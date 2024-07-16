import json

from loguru import logger

from pz.models.google_spreadsheet_model import GoogleSpreadSheetModelInterface
from pz.utils import full_name_to_real_name


class GoogleClassMemberModel(GoogleSpreadSheetModelInterface):
    SPREADSHEET_TITLE = '03-活動調查(所有學員)'
    VARIABLE_MAP: dict[str, str | list[str]] = {
        'sn': '總序',
        'studentId': '學員編號(公式)',
        'className': '班級',
        'classGroup': '組別',
        'fullName': '姓名',
        'dharmaName': '法名',
        'gender': '性別',
        'senior': '學長',
        'deacon': '執事',
        'nextClasses': ['上課班別', '第二班'],
    }
    # VARIABLE_LOCATIONS = [key for key in VARIABLE_MAP.keys()]

    sn: str
    studentId: str
    className: str
    classGroup: str
    fullName: str
    realName: str
    dharmaName: str
    gender: str
    senior: str
    deacon: str
    nextClasses: list[str]

    @classmethod
    def remap_variables(cls, new_mapping: dict[str, str | list[str]] | None):
        if new_mapping is not None:
            for key in cls.VARIABLE_MAP:
                if key in new_mapping:
                    cls.VARIABLE_MAP[key] = new_mapping[key]
            logger.info(f'update class variable: {cls.VARIABLE_MAP}')

    def __init__(self, values: list[str]):
        # person.__dict__["age"]

        # logger.error(f'values: {values}')
        # if len(values) > 0:
        #     raise Exception("oops")

        next_classes = []
        column_names = self.get_column_names()
        for i, value in enumerate(GoogleClassMemberModel.VARIABLE_MAP.keys()):
            if i < len(values):
                if value == 'nextClasses':
                    for nv in GoogleClassMemberModel.VARIABLE_MAP[value]:
                        ii = column_names.index(nv)
                        if ii < len(values) and values[ii] is not None:
                            next_classes.append(values[ii])
                    self.nextClasses = next_classes if len(next_classes) > 0 else None
                else:
                    self.__dict__[value] = values[i]
            else:
                self.__dict__[value] = None

        self.realName = full_name_to_real_name(self.fullName)

        if self.nextClasses is not None:
            logger.trace(f'{self.to_json()}')

    def new_instance(self, args: list[str]) -> 'GoogleClassMemberModel':
        return GoogleClassMemberModel(args)

    def __str__(self):
        return f'<\'{self.studentId}\',\'{self.fullName}\',\'{self.dharmaName}\',\'{self.className}\'>'

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=False)

    def get_spreadsheet_title(self) -> str:
        return GoogleClassMemberModel.SPREADSHEET_TITLE

    def get_column_names(self) -> list[str]:
        # print(PzMember.VARIABLE_MAP)
        # print(PzMember.VARIABLE_MAP.keys())
        # print(PzMember.VARIABLE_MAP.values())
        # return [x for k, x in self.VARIABLE_MAP.items()]
        # return GoogleClassMemberModel.VARIABLE_MAP.values()
        # logger.error(remap)
        columns: list[str] = []
        for k, v in self.VARIABLE_MAP.items():
            if isinstance(v, str):
                columns.append(v)
            elif isinstance(v, list):
                for e in v:
                    columns.append(e)
        #
        # logger.error(columns)
        return columns
