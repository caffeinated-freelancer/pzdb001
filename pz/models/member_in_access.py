import json

from pz.models.mysql_member_basic_entity import MysqlMemberBasicEntity


def static_init(args):
    pass


class MemberInAccessDB:
    ATTRIBUTES_MAP = MysqlMemberBasicEntity.PZ_MYSQL_COLUMN_NAMES
    initialized = False

    student_id: str
    real_name: str
    dharma_name: str
    gender: str
    birthday: str
    mobile_phone: str
    home_phone: str
    email: str
    emergency_contact: str
    emergency_contact_dharma_name: str
    emergency_contact_relationship: str
    emergency_contact_phone: str
    personal_id: str
    dharma_protection_position: str
    family_code: str
    family_id: str
    family_code_name: str
    threefold_refuge: str
    five_precepts: str
    bodhisattva_vow: str

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
