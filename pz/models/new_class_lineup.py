import json

from pz.models.excel_model import ExcelModelInterface
from services.questionnaire_service import QuestionnaireEntry


class NewClassLineup(ExcelModelInterface):
    VARIABLE_MAP = {
        'sn': '總序',
        'no': '序',
        'studentId': '學員編號',
        'className': '班級',
        'senior': '學長',
        'groupId': '組別',
        'realName': '姓名',
        'deacon': '執事',
        'dharmaName': '法名',
        'gender': '性別',
        'phoneNumber': '行動電話',
        'lastSenior': '上期學長',
        'automationInfo': '自動編班資訊',
    }

    sn: int
    no: int
    studentId: int | None
    className: str
    senior: str
    groupId: int
    realName: str
    deacon: str
    dharmaName: str
    phoneNumber: str | None
    lastSenior: str | None
    automationInfo: str
    # transit
    questionnaireEntry: QuestionnaireEntry

    def __init__(self, values: dict[str, str]):
        for k, v in NewClassLineup.VARIABLE_MAP.items():
            if v in values:
                # if values[v] is not None:
                self.__dict__[k] = values[v]

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=False)

    def new_instance(self, args):
        return NewClassLineup(args)
