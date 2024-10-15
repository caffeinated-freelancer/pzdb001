from pz.models.mysql_class_member_entity import MysqlClassMemberEntity
from pz.models.mysql_member_detail_entity import MysqlMemberDetailEntity
from pz.models.new_class_senior import NewClassSeniorModel
from pz.utils import logical_xor


def class_name_ranking(name: str, is_senior: bool) -> int:
    second_word = name[1]
    # print(second_word, name, is_senior)
    if second_word == '初':
        return 2
    elif second_word == '中':
        return 3
    elif second_word == '高':
        return 4
    elif second_word == '研':
        return 5
    elif name[0] == '桃':
        # logger.error(f'{name}')
        return 1
    else:
        return 6 if is_senior else 0


def class_member_comparator(entity: MysqlClassMemberEntity, is_senior: bool):
    ranking = class_name_ranking(entity.class_name, is_senior)
    return -ranking if is_senior else ranking


def deacon_based_class_member_comparator(a: MysqlClassMemberEntity, b: MysqlClassMemberEntity) -> int:
    if not logical_xor(a.some_kind_of_senior, b.some_kind_of_senior):
        return class_member_comparator(a, a.some_kind_of_senior) - class_member_comparator(b, b.some_kind_of_senior)
    elif a.some_kind_of_senior:
        return -1
    elif b.some_kind_of_senior:
        return 1
    return 0


def deacon_based_class_member_comparator_for_vlookup_tuple(
        a: tuple[MysqlMemberDetailEntity, MysqlClassMemberEntity],
        b: tuple[MysqlMemberDetailEntity, MysqlClassMemberEntity]) -> int:
    if a[1].special_deacon is not None and b[1].special_deacon is not None:
        if a[1].special_deacon.order != b[1].special_deacon.order:
            return a[1].special_deacon.order - b[1].special_deacon.order
        return class_member_comparator(b[1], True) - class_member_comparator(a[1], True)
    elif a[1].special_deacon is not None:
        return -1
    elif b[1].special_deacon is not None:
        return 1

    return class_member_comparator(b[1], False) - class_member_comparator(a[1], False)


def new_class_senior_comparator(model: NewClassSeniorModel):
    if model.groupId is not None:
        return len(model.members) * 1000 + model.groupId
    else:
        return len(model.members) * 1000 + 999
