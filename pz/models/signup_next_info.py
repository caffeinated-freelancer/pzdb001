import json

from pz.models.excel_model import ExcelModelInterface


class SignupNextInfoModel(ExcelModelInterface):
    VARIABLE_MAP = {
        'studentId': '學員編號(公式)',
        'className': '班級',
        'senior': '學長',
        'groupId': '組別',
        'fullName': '姓名',
        'dharmaName': '法名',
        'signup1': '上課班別',
        'signup2': '學長發心班別',
        'signup3': '學長上課',
        'signup4': '發心上第二班禪修班',
    }

    studentId: int
    className: str
    senior: str
    groupId: int
    fullName: str
    dharmaName: str
    signup1: str
    signup2: str
    signup3: str
    signup4: str
    signups: set[str]

    def __init__(self, values: dict[str, str]):
        for k, v in SignupNextInfoModel.VARIABLE_MAP.items():
            if v in values:
                # if values[v] is not None:
                self.__dict__[k] = values[v]
        self.signups = set()

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=False)

    def new_instance(self, args):
        return SignupNextInfoModel(args)
