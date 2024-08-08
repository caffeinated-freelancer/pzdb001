import json
from typing import Any

from loguru import logger

from pz.cloud.spreadsheet import SpreadsheetValueWithFormula
from pz.models.google_spreadsheet_model import GoogleSpreadSheetModelInterface
from pz.utils import full_name_to_real_name


class GoogleMemberRelation(GoogleSpreadSheetModelInterface):
    SPREADSHEET_TITLE = '親眷朋友關係'
    VARIABLE_MAP: dict[str, str | list[str]] = {
        'fullName': '姓名',
        'dharmaName': '法名',
        'gender': '性別',
        'studentId': '學員編號',
        'birthday': '生日末四碼',
        'phone': '行動電話末四碼',
        'relationKeys': ['關係代碼1', '關係代碼2', '關係代碼3', '關係代碼4', '關係代碼5', '關係代碼6'],
    }
    # VARIABLE_LOCATIONS = [key for key in VARIABLE_MAP.keys()]

    fullName: str
    dharmaName: str
    gender: str
    studentId: str
    birthday: str
    phone: str
    relationKeys: list[str] | None = None

    realName: str

    @classmethod
    def remap_variables(cls, new_mapping: dict[str, str | list[str]] | None):
        if new_mapping is not None:
            for key in cls.VARIABLE_MAP:
                if key in new_mapping:
                    cls.VARIABLE_MAP[key] = new_mapping[key]
            logger.info(f'更新讀取 Google 親眷朋友關係的欄位名稱: {cls.VARIABLE_MAP}')

    def __init__(self, values: list[str], raw_values: list[SpreadsheetValueWithFormula] | None = None):
        if raw_values is not None:
            values = [x.value for x in raw_values]

        relation_keys = []
        column_names = self.get_column_names()

        for i, value in enumerate(GoogleMemberRelation.VARIABLE_MAP.keys()):
            if i < len(values):
                if value == 'relationKeys':
                    for nv in GoogleMemberRelation.VARIABLE_MAP[value]:
                        ii = column_names.index(nv)
                        if ii < len(values) and values[ii] is not None and values[ii] != '':
                            relation_keys.append(values[ii])
                    self.relationKeys = relation_keys if len(relation_keys) > 0 else None
                elif value == 'studentId':
                    self.__dict__[value] = values[i]
                else:
                    self.__dict__[value] = values[i]
            else:
                self.__dict__[value] = None

        self.realName = full_name_to_real_name(self.fullName)

        # if self.relationKeys is not None:
        #     logger.trace(f'{self.to_json()}')

    def get_spreadsheet_title(self) -> str:
        return self.SPREADSHEET_TITLE

    @classmethod
    def get_column_names(cls) -> list[str]:
        columns: list[str] = []
        for k, v in cls.VARIABLE_MAP.items():
            if isinstance(v, str):
                columns.append(v)
            elif isinstance(v, list):
                for e in v:
                    columns.append(e)
        #
        # logger.error(columns)
        return columns

    def new_instance(self, args: list[Any]) -> 'GoogleSpreadSheetModelInterface':
        pass

    def __str__(self):
        return f'<\'{self.studentId}\',\'{self.fullName}\',\'{self.dharmaName}\'>'

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=False)
