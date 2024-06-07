import json


def static_init(args):
    pass


class MemberInAccessDB:
    ATTRIBUTES_MAP = {
        '學員編號': 'student_id',
        '姓名': 'real_name',
        '性別': 'gender',
        '出生日期': 'birthday',
        '緊急聯絡人': 'emergency_contact',
        '緊急聯絡人法名': 'emergency_contact_dharma_name',
        '緊急聯絡人稱謂': 'emergency_contact_relationship',
        '緊急聯絡人電話': 'emergency_contact_phone',
        '行動電話': 'mobile_phone',
        '住家電話': 'home_phone',
        '身分證字號': 'personal_id',
        '法名': 'dharma_name',
        '資料來源': 'source',
        '備註': 'remark',
    }
    initialized = False

    student_id: str
    real_name: str
    gender: str
    birthday: str
    emergency_contact: str
    emergency_contact_dharma_name: str
    emergency_contact_relationship: str
    emergency_contact_phone: str
    mobile_phone: str
    home_phone: str
    personal_id: str
    dharma_name: str
    source: str
    remark: str

    def __init__(self, mapping, data):
        # if not MemberInAccessDB.initialized:
        #     # Perform initialization logic here (only once)
        #     MemberInAccessDB.initialized = True
        #     print("Initializing...")
        #     for k, v in MemberInAccessDB.ATTRIBUTES_MAP.items():
        #         print(f'\'{v}\': \'{k}\',')
        for key, variable in MemberInAccessDB.ATTRIBUTES_MAP.items():
            if key in mapping:
                index = mapping.index(key)
                if index is not None:
                    self.__dict__[variable] = data[mapping.index(key)]

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=False)