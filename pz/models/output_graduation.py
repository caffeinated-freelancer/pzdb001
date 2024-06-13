import json

from pz.models.excel_model import ExcelModelInterface


class PzGraduationForOutput(ExcelModelInterface):
    VARIABLE_MAP = {
        'introducer': '介紹人',
        'pzClass': '班別',
        'group': '組別',
        'fullName': '學員姓名',
        'gender': '性別',
        'registerClass': '報名班別',
        'morningTee': '茶會/上午',
        'afternoonTee': '茶會/晚上',
        'relationship': '讀經班家長/關係',
        'contactPhone': '連絡電話',
        'description': '說明事項',
        'attendAt22': '2/22出席',
        'attendAt29': '2/29出席',
        'contactRemark': '電聯註記',
    }
    introducer: str
    pzClass: str
    group: str
    fullName: str
    gender: str
    registerClass: str
    morningTee: str
    afternoonTee: str
    relationship: str
    contactPhone: str
    description: str
    attendAt22: str
    attendAt29: str
    contactRemark: str

    def __init__(self, values: dict[str, str]):
        for k, v in PzGraduationForOutput.VARIABLE_MAP.items():
            if v in values:
                if values[v] is not None:
                    self.__dict__[k] = values[v]

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=False)

    def new_instance(self, args):
        return PzGraduationForOutput(args)
