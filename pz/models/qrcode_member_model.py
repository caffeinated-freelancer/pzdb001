import json

from pz.models.excel_model import ExcelModelInterface


class QRCodeMemberModel(ExcelModelInterface):
    VARIABLE_MAP = {
        'studentId': '學員編號',
        'className': '班級',
        'groupId': '組別',
        'realName': '姓名',
        'dharmaName': '法名',
    }

    studentId: str
    realName: str
    className: str
    dharmaName: str
    groupId: str

    def __init__(self, values: dict[str, str]):
        for k, v in QRCodeMemberModel.VARIABLE_MAP.items():
            # print(f'{k}: str')
            if v in values:
                # if values[v] is not None:
                self.__dict__[k] = values[v]
            else:
                self.__dict__[k] = None

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=False)

    def new_instance(self, args):
        return QRCodeMemberModel(args)
