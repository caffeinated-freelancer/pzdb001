import json

from pz.models.google_spreadsheet_model import GoogleSpreadSheetModelInterface
from pz.utils import full_name_to_real_name


class GoogleClassMemberModel(GoogleSpreadSheetModelInterface):
    SPREADSHEET_TITLE = '03-活動調查(所有學員)'
    VARIABLE_MAP: dict[str, str | list[str]] = {
        'sn': '總序',
        'studentId': '學員編號\n(公式)',
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

    def __init__(self, values: list[str], remap: dict[str, str | list[str]] | None = None):
        # person.__dict__["age"]
        for i, value in enumerate(GoogleClassMemberModel.VARIABLE_MAP.keys()):
            if i < len(values):
                self.__dict__[value] = values[i]
            else:
                self.__dict__[value] = None

        self.realName = full_name_to_real_name(self.fullName)

    def new_instance(self, args: list[str], remap: dict[str, str | list[str]] | None = None) -> 'GoogleClassMemberModel':
        return GoogleClassMemberModel(args, remap)

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
        return GoogleClassMemberModel.VARIABLE_MAP.values()
