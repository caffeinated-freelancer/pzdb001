from loguru import logger

from pz.models.vertical_member_lookup_result import VerticalMemberLookupResult
from pz.utils import full_name_to_names
from services.grand_member_service import PzGrandMemberService


def vertical_member_lookup(member_service: PzGrandMemberService,
           student_id: int | None, full_name: str | None, dharma_name: str | None = None,
           have_phone_or_birthday: bool = False) -> 'VerticalMemberLookupResult':
    if student_id is not None:
        entity_tuple = member_service.find_one_grand_member_by_student_id(student_id)
        if entity_tuple is None:
            return VerticalMemberLookupResult.with_error(f'學員編號 {student_id} 不存在')

        return VerticalMemberLookupResult(entity_tuple[0], entity_tuple[1])
    elif full_name is not None and full_name != '':
        real_name, split_dharma_name = full_name_to_names(full_name)
        if dharma_name is None:
            dharma_name = split_dharma_name

        entity_tuple, warnings = member_service.find_one_class_member_by_names_with_warning(
            real_name, dharma_name)
        if entity_tuple is None:
            if dharma_name is not None and dharma_name != '':
                return VerticalMemberLookupResult.with_error(f'學員 {full_name}/{dharma_name} 不存在')
            elif not have_phone_or_birthday:
                return VerticalMemberLookupResult.with_error(f'學員 {full_name}/{dharma_name} 不存在')
            return VerticalMemberLookupResult(None, None)
        else:
            return VerticalMemberLookupResult(entity_tuple[0], entity_tuple[1])
    return VerticalMemberLookupResult.with_error(f'無效記錄! 缺學員編號與姓名')
