import os.path
from pathlib import Path

from loguru import logger
from openpyxl.cell import Cell

from pz.config import PzProjectConfig
from pz.models.mysql_class_member_entity import MysqlClassMemberEntity
from pz.models.mysql_member_detail_entity import MysqlMemberDetailEntity
from pz.models.vlookup_model import VLookUpModel
from pz.utils import full_name_to_names, get_formatted_datetime
from services.excel_workbook_service import ExcelWorkbookService
from services.grand_member_service import PzGrandMemberService


class VLookUpGenerator:
    config: PzProjectConfig
    via_access_db: bool
    filename: str
    service: ExcelWorkbookService
    dataIndexes: dict[str, int]
    studentIdIndex: int
    realNameIndex: int
    dharmaNameIndex: int
    member_service: PzGrandMemberService

    def __init__(self, cfg: PzProjectConfig, filename: str, via_access: bool = False):
        self.config = cfg
        self.filename = filename
        self.via_access_db = via_access
        model = VLookUpModel({})
        self.service = ExcelWorkbookService(model, filename, header_at=1)
        self.member_service = PzGrandMemberService(
            cfg, from_access=False, from_google=False, all_via_access_db=via_access)

        self.dataIndexes: dict[str, int] = {}
        self.studentIdIndex = -1
        self.realNameIndex = -1
        self.dharmaNameIndex = -1

        for k, v in VLookUpModel.VARIABLE_MAP.items():
            if v in self.service.headers:
                i = self.service.headers[v]
                self.dataIndexes[k] = i - 1
                if k == 'studentId':
                    self.studentIdIndex = i - 1
                elif k == 'realName':
                    self.realNameIndex = i - 1
                elif k == 'dharmaName':
                    self.dharmaNameIndex = i - 1
        logger.debug(f'Data Indexes: {self.dataIndexes}')
        logger.debug(f'Student ID Index: {self.studentIdIndex}')
        logger.debug(f'Real Name Index: {self.realNameIndex}')
        logger.debug(f'Dharma Name Index: {self.dharmaNameIndex}')
        logger.debug(self.service.headers)
        logger.debug(self.dataIndexes)

    def perform_action(self, accumulate: list[list[str]], r: int, cells: list[Cell]) -> None:
        student_id = None
        full_name = None
        dharma_name = None

        if 0 <= self.studentIdIndex < len(cells):
            student_id = cells[self.studentIdIndex].value

        if 0 <= self.realNameIndex < len(cells):
            full_name = cells[self.realNameIndex].value

        if 0 <= self.dharmaNameIndex < len(cells):
            dharma_name = cells[self.dharmaNameIndex].value

        entity_tuple: tuple[MysqlMemberDetailEntity, MysqlClassMemberEntity] | None = None

        if student_id:
            if isinstance(student_id, str) and student_id.isdigit():
                student_id = int(student_id)

            if isinstance(student_id, int):
                logger.trace(f'lookup by student id: {student_id}')

                entity_tuple = self.member_service.find_one_grand_member_by_student_id(student_id)
                if entity_tuple is None or entity_tuple[1] is None:
                    return
            elif isinstance(student_id, str) and student_id.startswith('='):
                accumulate.append([f'第 {r} 列', '學員編號是公式, 請複製再貼上值'])
                return
        elif full_name:
            real_name, split_dharma_name = full_name_to_names(full_name)
            dharma_name = split_dharma_name if dharma_name is None else dharma_name

            if real_name.startswith('=') or dharma_name.startswith('='):
                accumulate.append([f'第 {r} 列', '姓名或法名是公式, 請複製再貼上值'])
            else:
                entity_tuple, warnings = self.member_service.find_one_class_member_by_names_with_warning(
                    real_name, dharma_name)
                if entity_tuple is None or entity_tuple[1] is None:
                    return
                logger.trace(f'lookup by name: {real_name} {dharma_name}')
                accumulate.extend([[f'第 {r} 列', w] for w in warnings])

        if entity_tuple is not None:
            entity = entity_tuple[1]
            detail = entity_tuple[0]

            for k, i in self.dataIndexes.items():
                if 0 <= i < len(cells):
                    value = cells[i].value
                    if value is None or isinstance(value, str) and len(value) == 0:
                        if k in VLookUpModel.TO_MYSQL_CLASS_MEMBER_MAP:
                            attr = VLookUpModel.TO_MYSQL_CLASS_MEMBER_MAP[k]
                            if attr in entity.__dict__:
                                cells[i].value = entity.__dict__[attr]
                        elif detail is not None:
                            if k in VLookUpModel.TO_MYSQL_MEMBER_DETAILS_MAP:
                                attr = VLookUpModel.TO_MYSQL_MEMBER_DETAILS_MAP[k]
                                if attr in detail.__dict__:
                                    cells[i].value = detail.__dict__[attr]
                            elif k in VLookUpModel.TO_MYSQL_MEMBER_WITH_FUNCTION_DETAILS_MAP:
                                attr, func = VLookUpModel.TO_MYSQL_MEMBER_WITH_FUNCTION_DETAILS_MAP[k]
                                # print(attr, func)
                                if attr in detail.__dict__:
                                    vv = func(detail.__dict__[attr])
                                    if vv is not None:
                                        cells[i].value = vv

    def lookup(self) -> list[list[str]]:
        warnings: list[list[str]] = []
        self.service.read_row_by_row(lambda r, cells: self.perform_action(warnings, r, cells))

        return warnings

    def save(self) -> str:
        file_dir = os.path.dirname(self.filename)
        _, extension = os.path.splitext(self.filename)
        formatted_date_time = get_formatted_datetime()

        filename = f'{file_dir}/{Path(self.filename).stem}-{formatted_date_time}{extension}'
        self.service.save_as(filename)
        return filename


def generate_lookup(cfg: PzProjectConfig, filename: str, via_access: bool = False) -> tuple[str, list[list[str]]]:
    logger.info(f'Generating lookup for {filename}')

    generator = VLookUpGenerator(cfg, filename, via_access=via_access)
    warnings = generator.lookup()
    return generator.save(), warnings
