from pz.models.mysql_class_member_entity import MysqlClassMemberEntity


def class_name_ranking(name: str, is_senior: bool) -> int:
    second_word = name[1]
    # print(second_word, name, is_senior)
    if second_word == '初':
        return 1
    elif second_word == '中':
        return 2
    elif second_word == '高':
        return 3
    elif second_word == '研':
        return 4
    elif name[0] == '桃':
        return 5
    else:
        return 6 if is_senior else 0


def class_member_comparator(entity: MysqlClassMemberEntity):
    ranking = class_name_ranking(entity.class_name, entity.is_senior)
    return -ranking if entity.is_senior else ranking
