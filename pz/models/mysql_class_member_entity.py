from typing import Any

from .google_class_member import GoogleClassMemberModel
from .json_class import JSONClass


class MysqlClassMemberEntity(JSONClass):
    id: int
    student_id: int
    class_name: str
    class_group: int
    senior: str
    real_name: str
    dharma_name: str
    deacon: str
    gender: str
    updated_at: str
    is_senior: bool

    VARIABLE_MAP = {
        'student_id': 'studentId',
        'class_name': 'className',
        'class_group': 'classGroup',
        'real_name': 'fullName',
        'dharma_name': 'dharmaName',
        'gender': 'gender',
        'senior': 'senior',
        'deacon': 'deacon',
    }

    @staticmethod
    def from_(data: Any) -> 'MysqlClassMemberEntity':
        pass

    def __init__(self, columns: list[str], values: list[Any],
                 google_member_detail: GoogleClassMemberModel | None = None) -> None:
        if google_member_detail is None:
            for i, column in enumerate(columns):
                if column == 'updated_at':
                    self.updated_at = values[i].strftime('%Y-%m-%d %H:%M:%S')
                elif column == 'id' or column in self.VARIABLE_MAP:
                    setattr(self, column, values[i])
        else:
            # print(google_member_detail.to_json())
            for member_variable, google_variable in self.VARIABLE_MAP.items():
                # print(member_variable, google_variable, google_member_detail.__dict__[google_variable])
                if member_variable in ['id', 'student_id', 'class_group']:
                    setattr(self, member_variable, int(google_member_detail.__dict__[google_variable]))
                else:
                    setattr(self, member_variable, google_member_detail.__dict__[google_variable])
            setattr(self, 'id', int(google_member_detail.studentId))
        self.is_senior = False
