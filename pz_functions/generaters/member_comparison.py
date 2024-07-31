import enum
import glob
import re
from enum import Enum
from typing import Any

from loguru import logger

from pz.config import PzProjectConfig
from pz.models.attend_record import AttendRecord
from pz.models.excel_creation_model import ExcelCreationModelInterface
from pz.models.mysql_class_member_entity import MysqlClassMemberEntity
from pz.utils import get_formatted_datetime
from services.excel_creation_service import ExcelCreationService
from services.excel_workbook_service import ExcelWorkbookService
from services.grand_member_service import PzGrandMemberService


class DifferenceRecordType(Enum):
    DIFFERENT = enum.auto()
    HAS_MORE = enum.auto()
    HAS_LESS = enum.auto()
    NO_DIFFERENCE = enum.auto()


class DifferenceRecord(ExcelCreationModelInterface):
    className: str
    groupId: int
    differentType: DifferenceRecordType
    studentId: int
    realName: str
    gender: str
    dharmaName: str
    differentText: str
    description: str

    VARIABLE_MAP = {
        'className': '班級',
        'groupId': '組別',
        'realName': '姓名',
        'dharmaName': '法名',
        'studentId': '學員編號',
        'gender': '性別',
        'differentText': '狀況',
        'description': '差異說明',
    }

    def __init__(self, class_name: str, group_id: int, entity: MysqlClassMemberEntity | None = None,
                 record: AttendRecord | None = None,
                 differences: list[str] | None = None):
        self.className = class_name
        self.groupId = group_id
        self.description = ''

        if entity is None and record is None:
            self.differentType = DifferenceRecordType.NO_DIFFERENCE
        elif entity is None and record is not None:
            self.differentType = DifferenceRecordType.HAS_LESS
            self.differentText = '欠缺'
            self.studentId = int(record.studentId)
            self.realName = record.realName
            self.dharmaName = record.dharmaName if record.dharmaName is not None else ''
            self.gender = record.gender
            self.description = f'僅在個資系統上  {class_name}/{group_id}  有此資料 (以學號為依據)'
        elif entity is not None:
            self.studentId = entity.student_id
            self.realName = entity.real_name
            self.gender = entity.gender
            self.dharmaName = entity.dharma_name if entity.dharma_name is not None else ''

            if record is None:
                self.differentType = DifferenceRecordType.HAS_MORE
                self.differentText = '多餘'
                self.description = f'個資系統上 {class_name}/{group_id} 並沒有此資料 (以學號為依據)'
            else:
                self.differentType = DifferenceRecordType.DIFFERENT
                self.differentText = '不同'
                self.description = ", ".join(differences)

    @staticmethod
    def only_in_google(entity: MysqlClassMemberEntity) -> 'DifferenceRecord':
        return DifferenceRecord(entity.class_name, entity.class_group, entity=entity)

    @staticmethod
    def not_in_google(class_name: str, group_id: int, record: AttendRecord) -> 'DifferenceRecord':
        return DifferenceRecord(class_name, group_id, record=record)

    @staticmethod
    def has_difference(record: AttendRecord, entity: MysqlClassMemberEntity) -> 'DifferenceRecord':
        e_dharma_name = entity.dharma_name if entity.dharma_name is not None else ''
        r_dharma_name = record.dharmaName if record.dharmaName is not None else ''
        class_name = entity.class_name
        group_id = entity.class_group

        differences: list[str] = []

        if entity.real_name != record.realName:
            logger.warning(
                f'{class_name}/{group_id}, 學號: {entity.student_id}, 姓名不同 Google: {entity.real_name} <-> 個資:{record.realName}')
            differences.append(f'個資上的姓名為: [{record.realName}], 法名: [{record.dharmaName if record.dharmaName is not None else ''}]')
        if e_dharma_name != r_dharma_name:
            if r_dharma_name != '':
                differences.append(f'個資上的法名為: [{r_dharma_name}]')
            else:
                differences.append(f'個資上並沒有法名')
            logger.warning(
                f'{class_name}/{group_id}, 學號: {entity.student_id}／{record.realName}, 法名不同 Google: [{e_dharma_name}] <-> 個資: [{r_dharma_name}]')
        if entity.gender != record.gender:
            differences.append(f'姓別: [{entity.gender}] vs [{record.gender}] (@個資)')
            logger.warning(f'{entity.gender} vs {record.gender}')

        if len(differences) == 0:
            return DifferenceRecord(class_name, group_id)
        else:
            return DifferenceRecord(class_name, group_id, entity=entity, record=record, differences=differences)

    def get_excel_headers(self) -> list[str]:
        return [x for _, x in self.VARIABLE_MAP.items()]

    def get_values_in_pecking_order(self) -> list[Any]:
        return [self.__dict__[x] for x, _ in self.VARIABLE_MAP.items()]

    def new_instance(self, args):
        pass


def generate_member_comparison_table(cfg: PzProjectConfig) -> tuple[
    str | None, list[str] | None, list[list[Any]] | None]:
    graduation_cfg = cfg.excel.graduation
    spreadsheet_cfg = graduation_cfg.records
    # print(graduation_cfg)
    cfg.make_sure_output_folder_exists()

    member_service = PzGrandMemberService(cfg, from_access=False, from_google=False)

    all_class_members = member_service.fetch_all_class_members()

    files = glob.glob(f'{graduation_cfg.records.spreadsheet_folder}/*.xlsx')
    processed_classes: set[str] = set()

    difference_records: list[DifferenceRecord] = []

    for filename in files:
        matched = re.match(r'^(.*)_(.{2}).?_上課.*', filename)

        if matched:
            class_name = matched.group(2)
            if class_name in processed_classes:
                logger.warning(f'{class_name} 已經處理過了')
                continue
            processed_classes.add(class_name)

            member_in_class_group: dict[int, dict[int, MysqlClassMemberEntity]] = {}
            for m in all_class_members:
                if m.class_name == class_name:
                    if m.class_group not in member_in_class_group:
                        member_in_class_group[m.class_group] = {}
                    member_in_class_group[m.class_group][m.student_id] = m

            records_excel = ExcelWorkbookService(AttendRecord({}), filename, None,
                                                 header_at=spreadsheet_cfg.header_row,
                                                 ignore_parenthesis=spreadsheet_cfg.ignore_parenthesis,
                                                 print_header=False,
                                                 debug=False)
            row_records: list[AttendRecord] = records_excel.read_all(required_attribute='studentId')

            for record in row_records:
                if record.realName.startswith('範例-'):
                    continue
                student_id = int(record.studentId)
                group_id = int(record.groupName)

                if group_id not in member_in_class_group:
                    logger.warning(f'Google 資料缺少 {class_name} {group_id} 群組')
                elif student_id not in member_in_class_group[group_id]:
                    difference_records.append(DifferenceRecord.not_in_google(class_name, group_id, record))
                    logger.warning(
                        f'Google 資料缺少 {class_name} {group_id} {record.realName}/{record.dharmaName}/{record.studentId}')
                else:
                    entry = member_in_class_group[group_id][student_id]

                    difference = DifferenceRecord.has_difference(record, entry)

                    if difference.differentType != DifferenceRecordType.NO_DIFFERENCE:
                        difference_records.append(difference)

                    del member_in_class_group[group_id][student_id]

            for group_id in member_in_class_group:
                for student_id in member_in_class_group[group_id]:
                    entry = member_in_class_group[group_id][student_id]
                    difference_records.append(DifferenceRecord.only_in_google(entry))
                    logger.warning(f'{class_name}/{group_id}/{student_id}/{entry.real_name} 僅在 Google 學員')

    if len(difference_records) > 0:
        model = DifferenceRecord('', 0)

        service = ExcelCreationService(model)

        data: list[list[Any]] = []
        for model in difference_records:
            data.append(model.get_values_in_pecking_order())

        supplier = (lambda y=x: x for x in data)
        service.write_data(supplier)

        formatted_date_time = get_formatted_datetime()

        file_name = f'Google 學員資料差異_{formatted_date_time}.xlsx'
        full_file_path = f'{cfg.output_folder}/{file_name}'
        service.save(full_file_path)
        # os.startfile(full_file_path)
        return full_file_path, model.get_excel_headers(), data
    return None, None, None
