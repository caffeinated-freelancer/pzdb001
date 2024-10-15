import json
from typing import Any

from .google_class_member import GoogleClassMemberModel
from .json_class import JSONClass
from .special_deacon import SpecialDeacon


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
    next_classes: str
    updated_at: str

    is_senior: bool
    some_kind_of_senior: bool
    special_deacon: SpecialDeacon | None
    signupClasses: list[str]

    VARIABLE_MAP = {
        'student_id': 'studentId',
        'class_name': 'className',
        'class_group': 'classGroup',
        'real_name': 'fullName',
        'dharma_name': 'dharmaName',
        'gender': 'gender',
        'next_classes': 'nextClasses',
        'senior': 'senior',
        'deacon': 'deacon',
    }

    ACCESS_DB_MAP: dict[str, tuple[str, str]] = {
        'student_id': ('StudentId', 'INTEGER'),
        'class_name': ('ClassName', 'TEXT(10)'),
        'class_group': ('ClassGroup', 'INTEGER'),
        'real_name': ('RealName', 'TEXT(10)'),
        'dharma_name': ('DharmaName', 'TEXT(10)'),
        'gender': ('Gender', 'TEXT(1)'),
        'senior': ('Senior', 'TEXT(10)'),
        'deacon': ('Deacon', 'TEXT(20)'),
    }

    @staticmethod
    def from_(data: Any) -> 'MysqlClassMemberEntity':
        pass

    def __init__(self, columns: list[str], values: list[Any],
                 google_member_detail: GoogleClassMemberModel | None = None,
                 another_entity: 'MysqlClassMemberEntity' = None) -> None:
        self.is_senior = False
        self.special_deacon = None

        if another_entity is not None:
            for k, v in another_entity.__dict__.items():
                setattr(self, k, v)
        elif google_member_detail is None:
            for i, column in enumerate(columns):
                if column == 'updated_at':
                    self.updated_at = values[i].strftime('%Y-%m-%d %H:%M:%S')
                elif column == 'next_classes':
                    if values[i] is not None and values[i] != '':
                        self.next_classes = values[i]
                        self.signupClasses = json.loads(values[i])
                    else:
                        self.next_classes = ''
                        self.signupClasses = []
                elif column == 'id' or column in self.VARIABLE_MAP:
                    setattr(self, column, values[i])

            # logger.warning(f'<< {self.next_classes} {self.to_json()}')
        else:
            # print(google_member_detail.to_json())
            for member_variable, google_variable in self.VARIABLE_MAP.items():
                # print(member_variable, google_variable, google_member_detail.__dict__[google_variable])
                if member_variable in ['id', 'student_id', 'class_group']:
                    setattr(self, member_variable, int(google_member_detail.__dict__[google_variable]))
                elif member_variable == 'next_classes':
                    v = google_member_detail.__dict__[google_variable]
                    if v is not None:
                        setattr(self, member_variable, json.dumps(v))
                    else:
                        setattr(self, member_variable, None)
                else:
                    setattr(self, member_variable, google_member_detail.__dict__[google_variable])
            setattr(self, 'id', int(google_member_detail.studentId))
            # logger.warning(f'>> {self.to_json()}')

        self.some_kind_of_senior = self.deacon is not None and self.deacon != ''
