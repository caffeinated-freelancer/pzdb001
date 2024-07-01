import json

from pz.models.excel_model import ExcelModelInterface


class SeniorContactAdvanced(ExcelModelInterface):
    VARIABLE_MAP = {
        'no': '組序',
        'className': '班別',
        'senior': '學長',
        'groupId': '組別',
        'realName': '姓名',
        'dharmaName': '法名',
        'phoneNumber': '學員電話行動&市話',
        'lastRecord': '上期班別/學長',
    }

    no: int
    className: str
    senior: str
    groupId: int
    realName: str
    dharmaName: str
    phoneNumber: str
    lastRecord: str

    def __init__(self, values: dict[str, str]):
        for k, v in SeniorContactAdvanced.VARIABLE_MAP.items():
            if v in values:
                # if values[v] is not None:
                self.__dict__[k] = values[v]

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=False)

    def new_instance(self, args):
        return SeniorContactAdvanced(args)

