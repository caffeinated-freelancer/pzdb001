import functools
import glob
import os
import re

from loguru import logger

from pz.config import PzProjectConfig
from pz.models.attend_record import AttendRecord
from pz.models.google_class_member import GoogleClassMemberModel
from pz.models.new_class_senior import NewClassSeniorModel
from services.excel_workbook_service import ExcelWorkbookService
from services.new_class_senior_service import NewClassSeniorService
from services.senior_deacon_service import SeniorDeaconService


def simplify_class_name(config: PzProjectConfig, full_class_name: str) -> str | None:
    matched_classes = [x for x in config.meditation_class_names if x in full_class_name]
    if len(matched_classes) == 1:
        return matched_classes[0]
    elif len(matched_classes) == 0:
        logger.error(f'{full_class_name}: no matched classes found')
    else:
        logger.error(f'{full_class_name}: multiple matched classes found')
    return None


class AttendRecordFileDetail:
    filename: str
    class_name: str | None
    meditation_center: str | None
    person: str | None
    timestamp: int

    def __init__(self, config: PzProjectConfig, filename: str):
        self.filename = filename
        matched = re.match(r'^(.*)_(.*)_上課紀錄_(.*)_(\d{10})(\d+).xlsx$', filename)

        if matched:
            self.meditation_center = matched.group(1)
            self.class_name = simplify_class_name(config, matched.group(2))
            self.person = matched.group(3)
            self.timestamp = int(matched.group(4))
        else:
            self.meditation_center = None
            self.class_name = None
            self.person = None
            self.timestamp = 0

    def map_key(self):
        return f'{self.meditation_center}_{self.person}_{self.timestamp}'


class AttendRecordAsClassMemberService:
    ATTEND_TO_GOOGLE_MAP = {
        'studentId': 'studentId',
        'realName': 'fullName',
        'dharmaName': 'dharmaName',
        'gender': 'gender',
        'groupName': 'classGroup',
        'groupNumber': 'sn',
        'className': 'className',
    }

    config: PzProjectConfig
    file_details: list[AttendRecordFileDetail]

    def __init__(self, cfg: PzProjectConfig):
        self.config = cfg

        files = glob.glob(f'{cfg.excel.graduation.records.spreadsheet_folder}/*.xlsx')

        class_file_map: dict[str, AttendRecordFileDetail] = {}

        for filename in files:
            f = os.path.basename(filename)
            if not f.startswith("~$"):
                detail = AttendRecordFileDetail(self.config, f)
                if detail.class_name is not None:
                    if detail.class_name not in cfg.meditation_class_names:
                        logger.warning(f'班級名稱 {detail.class_name}: 設定檔中, 未設定')
                        continue

                    if detail.class_name not in class_file_map:
                        class_file_map[detail.class_name] = detail
                    elif class_file_map[detail.class_name].timestamp < detail.timestamp:
                        class_file_map[detail.class_name] = detail

        # logger.info(f'key: {target_key}, {len(file_maps[target_key])}')
        self.file_details = [class_file_map[x] for x in cfg.meditation_class_names if x in class_file_map]
        # self.file_details = [detail for detail in file_maps[target_key]]

    def attend_record_to_google(self, record: AttendRecord) -> GoogleClassMemberModel:
        model = GoogleClassMemberModel([])

        for k, v in self.ATTEND_TO_GOOGLE_MAP.items():
            model.__dict__[v] = record.__dict__[k]

        model.realName = model.fullName
        model.recordOrder = record.recordOrder

        return model

    def _read_each_file(self, detail: AttendRecordFileDetail) -> list[GoogleClassMemberModel]:
        full_path_name = f'{self.config.excel.graduation.records.spreadsheet_folder}/{detail.filename}'

        service = ExcelWorkbookService(AttendRecord({}), full_path_name, None,
                                       header_at=self.config.excel.graduation.records.header_row,
                                       ignore_parenthesis=self.config.excel.graduation.records.ignore_parenthesis,
                                       print_header=False, debug=False)
        raw_records: list[AttendRecord] = service.read_all(required_attribute='studentId')

        # headers = records_excel.get_headers()

        models: list[GoogleClassMemberModel] = []
        pos = 0
        for record in raw_records:
            if record.realName is None or record.realName.startswith('範例-'):
                continue
            record.className = detail.class_name
            pos += 1
            record.recordOrder = pos
            model = self.attend_record_to_google(record)
            models.append(model)
            # print(model.to_json())

        return models

    # @staticmethod
    # def senior_key(senior: NewClassSeniorModel) -> str:
    #     return f'{senior.className}_{senior.groupId}_{senior.fullName}_{senior.dharmaName}'

    def read_all(self) -> list[GoogleClassMemberModel]:
        # senior_deacons: dict[str, NewClassSeniorModel] = {}
        # class_senior: dict[str, NewClassSeniorModel] = {}
        #
        # for senior in NewClassSeniorService.read_all_seniors(self.config):
        #     senior_deacons[self.senior_key(senior)] = senior
        #     if senior.senior is not None and senior.senior == '學長':
        #         class_senior[f'{senior.className}_{senior.groupId}'] = senior

        deacon_service = SeniorDeaconService(self.config)

        class_members: dict[str, list[GoogleClassMemberModel]] = {}

        for detail in self.file_details:
            class_members[detail.class_name] = self._read_each_file(detail)

        models: list[GoogleClassMemberModel] = []
        for class_name in self.config.meditation_class_names:
            if class_name in class_members:
                models.extend(class_members[class_name])

        for model in models:
            key = f'{model.className}_{model.classGroup}_{model.fullName}_{model.dharmaName}'
            if key in deacon_service.senior_deacons:
                entry = deacon_service.senior_deacons.pop(key)
                if entry.deacon is not None and entry.deacon != '':
                    model.deacon = entry.deacon
                elif entry.senior is not None and entry.senior != '':
                    model.deacon = entry.senior

            key = f'{model.className}_{model.classGroup}'
            if key in deacon_service.class_senior:
                model.senior = deacon_service.class_senior[key].fullName

        for k, v in deacon_service.senior_deacons:
            logger.warning(f'{k}: {v.fullName}')

        sorted_list = sorted(models, key=functools.cmp_to_key(
            lambda a, b: comparator(a, b, self.config.meditation_class_names)))

        return sorted_list


def comparator(a: GoogleClassMemberModel, b: GoogleClassMemberModel, class_names: list[str]) -> int:
    if a.className == b.className:
        if a.classGroup == b.classGroup:
            if a.senior == a.fullName:
                return -1
            elif b.senior == b.fullName:
                return 1
            elif a.deacon is not None and a.deacon != '':
                if b.deacon is not None and b.deacon != '':
                    pass
                else:
                    return -1
            elif b.deacon is not None and b.deacon != '':
                return 1
            return a.recordOrder - b.recordOrder
        else:
            return int(a.classGroup) - int(b.classGroup)
    else:
        return class_names.index(a.className) - class_names.index(b.className)
