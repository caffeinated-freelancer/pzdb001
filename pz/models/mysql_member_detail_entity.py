from typing import Any

from .json_class import JSONClass
from .member_in_access import MemberInAccessDB


class MysqlMemberDetailEntity(JSONClass):
    id: int
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

    @staticmethod
    def from_access_db(model: MemberInAccessDB) -> 'MysqlMemberDetailEntity':
        return MysqlMemberDetailEntity([], [], model)

    def __init__(self, columns: list[str], values: list[Any], model: MemberInAccessDB | None = None) -> None:
        if model is None:
            for i, column in enumerate(columns):
                setattr(self, column, values[i])
        else:
            for member_variable in MemberInAccessDB.ATTRIBUTES_MAP.values():
                setattr(self, member_variable, model.__dict__[member_variable])
            setattr(self, 'id', int(model.student_id))
