import json
from typing import Any

from .google_member_relation import GoogleMemberRelation
from .json_class import JSONClass


class MysqlMemberRelationEntity(JSONClass):
    id: int
    student_id: int | None
    real_name: str
    dharma_name: str | None
    gender: str | None
    birthday: int | None
    phone: int | None
    relation_keys: str
    updated_at: str

    relationKeys: list[str]

    VARIABLE_MAP = {
        'real_name': 'fullName',
        'dharma_name': 'dharmaName',
        'gender': 'gender',
        'student_id': 'studentId',
        'birthday': 'birthday',
        'phone': 'phone',
        'relation_keys': 'relationKeys',
    }

    @staticmethod
    def from_(data: Any) -> 'MysqlMemberRelationEntity':
        pass

    def __init__(self, columns: list[str], values: list[Any],
                 entry: GoogleMemberRelation | None = None) -> None:

        if entry is None:
            for i, column in enumerate(columns):
                if column == 'updated_at':
                    self.updated_at = values[i].strftime('%Y-%m-%d %H:%M:%S')
                elif column == 'relation_keys':
                    if values[i] is not None and values[i] != '':
                        self.relation_keys = values[i]
                        self.relationKeys = json.loads(values[i])
                    else:
                        self.relation_keys = ''
                        self.relationKeys = []
                elif column == 'id' or column in self.VARIABLE_MAP:
                    setattr(self, column, values[i])

            # logger.warning(f'<< {self.next_classes} {self.to_json()}')
        else:
            # print(google_member_detail.to_json())
            for member_variable, google_variable in self.VARIABLE_MAP.items():
                # print(member_variable, google_variable, google_member_detail.__dict__[google_variable])
                if member_variable in ['id', 'student_id', 'birthday', 'phone']:
                    if google_variable is not None:
                        setattr(self, member_variable, int(entry.__dict__[google_variable]))
                    else:
                        setattr(self, member_variable, None)
                elif member_variable == 'relation_keys':
                    v = entry.__dict__[google_variable]
                    if v is not None:
                        setattr(self, member_variable, json.dumps(v))
                    else:
                        setattr(self, member_variable, None)
                else:
                    setattr(self, member_variable, entry.__dict__[google_variable])
            setattr(self, 'id', int(entry.studentId))
            # logger.warning(f'>> {self.to_json()}')
