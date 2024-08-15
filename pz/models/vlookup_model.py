import json

from pz.models.excel_model import ExcelModelInterface


class VLookUpModel(ExcelModelInterface):
    VARIABLE_MAP = {
        'studentId': '學員編號',
        'className': '班級',
        'groupId': '組別',
        'senior': '學長',
        'realName': '姓名',
        'dharmaName': '法名',
        'gender': '性別',

        'mobilePhone': '行動電話',
        'homePhone': '住家電話',
        # 'personalId': '身分證字號',
        'birthday': '出生日期',
        'dharmaProtectionPosition': '護法會職稱',
    }

    TO_MYSQL_CLASS_MEMBER_MAP = {
        'studentId': 'student_id',
        'className': 'class_name',
        'groupId': 'class_group',
        'realName': 'real_name',
        'dharmaName': 'dharma_name',
        'gender': 'gender',
        'senior': 'senior',
    }

    TO_MYSQL_MEMBER_DETAILS_MAP = {
        'mobilePhone': 'mobile_phone',
        'homePhone': 'home_phone',
        # 'personalId': 'class_group',
        'birthday': 'birthday',
        'dharmaProtectionPosition': 'dharma_protection_position',
    }

    studentId: str | None
    className: str | None
    groupId: str | None
    senior: str | None
    realName: str | None
    dharmaName: str | None
    gender: str | None

    mobilePhone: str | None
    homePhone: str | None
    birthday: str | None
    dharmaProtectionPosition: str | None

    # personalId: str | None

    def __init__(self, values: dict[str, str]):
        for k, v in VLookUpModel.VARIABLE_MAP.items():
            if v in values:
                # if values[v] is not None:
                self.__dict__[k] = values[v]
            else:
                self.__dict__[k] = None

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=False)

    def new_instance(self, args):
        return VLookUpModel(args)
