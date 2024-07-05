import json

from pz.models.excel_model import ExcelModelInterface


class PzQuestionnaireInfo(ExcelModelInterface):
    VARIABLE_MAP = {
        'no': 'NO',
        'fullName': '姓名',
        'gender': '性別',
        'birthday': '出生日期',
        'reason': '來精舍原因',
        'tee': '茶會',
        'chaForTea': '喫茶趣',
        'registerClass': '報班',
        # 'registerClass': '報名班別',
        'personalId': '身分證字號',
        'mobilePhone': '行動電話',
        'mobilePhone2': '行動電話2',
        'homePhone': '住家電話',
        'homePhone2': '住家電話2',
        'contactName': '緊急聯絡人',
        'contactDharmaName': '緊急聯絡人法名',
        'contactRelationship': '緊急聯絡人稱謂',
        'contactPhone': '緊急聯絡人電話',
        'familyCode': '家屬碼',
        'familyId': '家屬碼ID',
        'familyTitle': '家屬碼稱謂',
        'introducerTitle': '介紹人稱謂',
        'introducerPhone': '介紹人電話',
        'introducerName': '介紹人',
        'introducerClass': '介紹人班級',
        'introducerClassGroup': '介紹人組別',
        'parents': '家長姓名',
        'parentsPhone': '家長聯絡電話',
        'bookkeepingDate': '資料組登陸日期',
        'remark': '備註',
    }

    no: str
    fullName: str
    gender: str
    birthday: str
    reason: str
    tee: str
    chaForTea: str
    registerClass: str
    personalId: str
    mobilePhone: str
    mobilePhone2: str
    homePhone: str
    homePhone2: str
    contactName: str
    contactDharmaName: str
    contactRelationship: str
    contactPhone: str
    familyCode: str
    familyId: str
    familyTitle: str
    introducerTitle: str
    introducerPhone: str
    introducerName: str
    introducerClass: str
    introducerClassGroup: str
    parents: str
    parentsPhone: str
    bookkeepingDate: str
    remark: str

    def __init__(self, values: dict[str, str]):
        for k, v in PzQuestionnaireInfo.VARIABLE_MAP.items():
            if v in values:
                # if values[v] is not None:
                self.__dict__[k] = values[v]

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=False)

    def new_instance(self, args):
        return PzQuestionnaireInfo(args)
