from pz.models.general_processing_error import GeneralProcessingError
from pz.models.mysql_class_member_entity import MysqlClassMemberEntity
from pz.models.mysql_member_detail_entity import MysqlMemberDetailEntity


class VerticalMemberLookupResult:
    detail: MysqlMemberDetailEntity | None
    classMember: MysqlClassMemberEntity | None
    error: GeneralProcessingError | None

    def __init__(self, detail: MysqlMemberDetailEntity | None, class_member: MysqlClassMemberEntity | None,
                 error: GeneralProcessingError | None = None) -> None:
        self.detail = detail
        self.classMember = class_member
        self.error = error

    def has_error(self) -> bool:
        return self.error is not None

    def get_real_name(self) -> str:
        if self.classMember is not None:
            return self.classMember.real_name
        elif self.detail is not None:
            return self.detail.real_name
        else:
            return ''

    def get_dharma_name(self) -> str:
        if self.classMember is not None:
            return self.classMember.dharma_name
        elif self.detail is not None:
            return self.detail.dharma_name
        else:
            return ''

    def get_student_id(self) -> int:
        if self.classMember is not None:
            return self.classMember.student_id
        elif self.detail is not None:
            return int(self.detail.student_id)
        return -1

    def is_member(self):
        return self.classMember is not None or self.detail is not None

    def get_gender(self) -> str:
        if self.classMember is not None:
            return self.classMember.gender
        elif self.detail is not None:
            return self.detail.gender
        else:
            return ''

    @staticmethod
    def with_error(message: str) -> 'VerticalMemberLookupResult':
        return VerticalMemberLookupResult(None, None, GeneralProcessingError.error(message))

    @staticmethod
    def with_warning(message: str) -> 'VerticalMemberLookupResult':
        return VerticalMemberLookupResult(None, None, GeneralProcessingError.warning(message))
