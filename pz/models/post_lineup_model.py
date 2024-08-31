import json

from pz.models.excel_model import ExcelModelInterface


class PostLineupModel(ExcelModelInterface):
    VARIABLE_MAP = {
        'groupId': '組別',
        'groupNo': '組序',
        'realName': '姓名',
    }

    groupId: str
    groupNo: str
    realName: str

    def __init__(self, values: dict[str, str]):
        for k, v in PostLineupModel.VARIABLE_MAP.items():
            if v in values:
                # if values[v] is not None:
                self.__dict__[k] = values[v]

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=False)

    def new_instance(self, args):
        return PostLineupModel(args)
