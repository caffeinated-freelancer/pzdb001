import glob
import os
import re

from loguru import logger

from pz.config import PzProjectConfig
from pz.models.attend_record import AttendRecord
from pz.models.google_class_member import GoogleClassMemberModel
from services.excel_workbook_service import ExcelWorkbookService


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
        file_maps: dict[str, list[AttendRecordFileDetail]] = {}
        max_timestamp: int = 0
        target_key = ''

        for filename in files:
            f = os.path.basename(filename)
            if not f.startswith("~$"):
                detail = AttendRecordFileDetail(self.config, f)
                if detail.class_name is not None:
                    max_timestamp = max(max_timestamp, detail.timestamp)

                    if detail.timestamp == max_timestamp:
                        key = detail.map_key()
                        if key in file_maps:
                            if target_key != key:
                                logger.error(f'糟糕, key 對不上 {key} vs {target_key}')
                            else:
                                file_maps[key].append(detail)
                        else:
                            file_maps[key] = [detail]
                            target_key = key

        # logger.info(f'key: {target_key}, {len(file_maps[target_key])}')
        self.file_details = [detail for detail in file_maps[target_key]]

    def attend_record_to_google(self, record: AttendRecord) -> GoogleClassMemberModel:
        model = GoogleClassMemberModel([])

        for k, v in self.ATTEND_TO_GOOGLE_MAP.items():
            model.__dict__[v] = record.__dict__[k]

        model.realName = model.fullName

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
        for record in raw_records:
            if record.realName is None or record.realName.startswith('範例-'):
                continue
            record.className = detail.class_name
            model = self.attend_record_to_google(record)
            models.append(model)
            # print(model.to_json())

        return models

    def read_all(self) -> list[GoogleClassMemberModel]:
        class_members: dict[str, list[GoogleClassMemberModel]] = {}

        for detail in self.file_details:
            class_members[detail.class_name] = self._read_each_file(detail)

        models: list[GoogleClassMemberModel] = []
        for class_name in self.config.meditation_class_names:
            if class_name in class_members:
                models.extend(class_members[class_name])

        return models
