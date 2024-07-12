import json

from pz.models.assigned_member import AssignedMember
from pz.models.excel_model import ExcelModelInterface


class NewClassSeniorModel(ExcelModelInterface):
    VARIABLE_MAP = {
        'serialNo': '總序',
        'className': '班級',
        'groupId': '組別',
        'fullName': '姓名',
        'senior': '學長',
        'deacon': '執事',
        'dharmaName': '法名',
        'gender': '性別',
    }
    serialNo: int
    className: str
    groupId: int
    fullName: str
    senior: str
    deacon: str
    dharmaName: str
    gender: str

    studentId: int
    members: list[AssignedMember]

    def __init__(self, values: dict[str, str]):
        for k, v in NewClassSeniorModel.VARIABLE_MAP.items():
            if v in values:
                if v == 'serialNo':
                    self.__dict__[k] = int(values[v])
                elif v == 'groupId':
                    if values[v] is not None and len(values[v]) > 0:
                        self.__dict__[k] = int(values[v])
                    else:
                        self.__dict__[k] = -1
                else:
                    self.__dict__[k] = values[v]
        self.studentId = 0
        self.members = []

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=False)

    def new_instance(self, args):
        return NewClassSeniorModel(args)
