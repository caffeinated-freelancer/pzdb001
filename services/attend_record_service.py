import functools
import glob
import os
import re

from loguru import logger

from pz.comparators import google_class_member_comparator
from pz.config import PzProjectConfig
from pz.models.attend_record import AttendRecord
from pz.models.google_class_member import GoogleClassMemberModel
from services.excel_workbook_service import ExcelWorkbookService
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
        # full_path_name = f'{self.config.excel.graduation.records.spreadsheet_folder}/{detail.filename}'
        #
        # service = ExcelWorkbookService(AttendRecord({}), full_path_name, None,
        #                                header_at=self.config.excel.graduation.records.header_row,
        #                                ignore_parenthesis=self.config.excel.graduation.records.ignore_parenthesis,
        #                                print_header=False, debug=False)
        # raw_records: list[AttendRecord] = service.read_all(required_attribute='studentId')
        raw_records = self._read_each_file_as_attend_records(detail)

        # headers = records_excel.get_headers()

        models: list[GoogleClassMemberModel] = []
        pos = 0
        for record in raw_records:
            # if record.realName is None or record.realName.startswith('範例-'):
            #     continue
            record.className = detail.class_name
            pos += 1
            record.recordOrder = pos
            model = self.attend_record_to_google(record)
            models.append(model)
            # print(model.to_json())

        return models

    def _read_each_file_as_attend_records(self, detail: AttendRecordFileDetail) -> list[AttendRecord]:
        full_path_name = f'{self.config.excel.graduation.records.spreadsheet_folder}/{detail.filename}'

        service = ExcelWorkbookService(AttendRecord({}), full_path_name, None,
                                       header_at=self.config.excel.graduation.records.header_row,
                                       ignore_parenthesis=self.config.excel.graduation.records.ignore_parenthesis,
                                       print_header=False, debug=False)
        raw_records: list[AttendRecord] = service.read_all(required_attribute='studentId')
        records = [x for x in raw_records if x.realName is not None and not x.realName.startswith('範例-')]
        for record in records:
            record.className = detail.class_name
        return records
        # return  raw_records

    # @staticmethod
    # def senior_key(senior: NewClassSeniorModel) -> str:
    #     return f'{senior.className}_{senior.groupId}_{senior.fullName}_{senior.dharmaName}'

    def read_all_as_attend_records(self) -> list[AttendRecord]:
        records: list[AttendRecord] = []
        for detail in self.file_details:
            records.extend(self._read_each_file_as_attend_records(detail))
        return records

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

        attend_by_student_id: dict[str, list[GoogleClassMemberModel]] = {}

        logger.error(self.config.deacon_order)

        for model in models:
            model.deaconOrder = len(self.config.deacon_order) + 2
            model.isSenior = False
            model.notes = None

            key = f'{model.className}_{model.classGroup}_{model.fullName}_{model.dharmaName}'
            if key in deacon_service.senior_deacons:
                entry = deacon_service.senior_deacons.pop(key)

                my_deacon: str | None = None

                if entry.deacon is not None and entry.deacon != '':
                    my_deacon = entry.deacon
                elif entry.senior is not None and entry.senior != '':
                    my_deacon = entry.senior

                if my_deacon is not None:
                    model.deacon = my_deacon
                    model.isSenior = True
                    try:
                        model.deaconOrder = self.config.deacon_order.index(my_deacon)
                    except ValueError:
                        model.deaconOrder = len(self.config.deacon_order) + 1

            key = f'{model.className}_{model.classGroup}'
            if key in deacon_service.class_senior:
                model.senior = deacon_service.class_senior[key].fullName

            if model.studentId is not None and model.studentId != '':
                if model.studentId in attend_by_student_id:
                    attend_by_student_id[model.studentId].append(model)
                else:
                    attend_by_student_id[model.studentId] = [model]

        for student_id in attend_by_student_id:
            entries = attend_by_student_id[student_id]
            if len(entries) > 1:
                sorted_list = sorted(entries, key=functools.cmp_to_key(google_class_member_comparator))
                sorted_list[0].notes = '本班回報'
                for i in range(1, len(sorted_list)):
                    sorted_list[i].notes = f'上多班;請回報在{sorted_list[0].className}{sorted_list[0].classGroup}'
                logger.error(f'Student ID {student_id} has multiple attend records')
                for entry in sorted_list:
                    logger.warning(
                        f'{entry.className} {entry.classGroup} {entry.fullName} {entry.dharmaName} {entry.deacon} {entry.deaconOrder} {entry.notes}')

        attend_by_student_id.clear()

        # model.notes = ''

        # model.notes = '本班回報'
        # model.notes = '上多班;請回報在夜研5'

        logger.info(deacon_service.senior_deacons)

        for k in deacon_service.senior_deacons.keys():
            logger.warning(f'{k}: {deacon_service.senior_deacons[k].fullName} 學長沒有在上課記錄')

        sorted_list = sorted(models, key=functools.cmp_to_key(
            lambda a, b: trivial_comparator(a, b, self.config.meditation_class_names)))

        return sorted_list


def senior_first_comparator(a: GoogleClassMemberModel, b: GoogleClassMemberModel, class_names: list[str]) -> int:
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


def trivial_comparator(a: GoogleClassMemberModel, b: GoogleClassMemberModel, class_names: list[str]) -> int:
    if a.className == b.className:
        if a.classGroup == b.classGroup:
            if a.senior == a.fullName:
                return -1
            elif b.senior == b.fullName:
                return 1
            return a.recordOrder - b.recordOrder
        else:
            return int(a.classGroup) - int(b.classGroup)
    else:
        return class_names.index(a.className) - class_names.index(b.className)
