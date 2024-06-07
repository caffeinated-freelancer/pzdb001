import functools
from collections import OrderedDict
from typing import Any

from pz.config import PzProjectConfig
from pz.models.output_introducer_contact import PzIntroducerContactForOutput
from pz.models.pz_questionnaire_info import PzQuestionnaireInfo
from services.excel_template_service import ExcelTemplateService
from services.excel_workbook_service import ExcelWorkbookService
from services.grand_member_service import PzGrandMemberService


def class_name_to_integer(class_name: str) -> int:
    class_names = [
        '',
        '日初',
        '日中',
        '日高',
        '日研',
        '夜初',
        '夜中',
        '夜高',
        '夜研',
        '桃一',
        '桃二',
        '兒童',
    ]
    if class_name is None or len(class_name) < 2:
        return 0
    else:
        return class_names.index(class_name[:2])


def data_by_class_and_group(a: dict[str, Any], b: dict[str, Any]) -> int:
    class_name_a = class_name_to_integer(a['班別'])
    class_name_b = class_name_to_integer(b['班別'])
    group_id_a = int(a['組別']) if a['組別'] != '' else 0
    group_id_b = int(b['組別']) if b['組別'] != '' else 0

    if class_name_a != class_name_b:
        return class_name_a - class_name_b

    if group_id_a != group_id_b:
        return group_id_a - group_id_b

    if a['介紹人'] != b['介紹人']:
        return -1 if a['介紹人'] < b['介紹人'] else 1

    class_name_a = class_name_to_integer(a['報名班別'])
    class_name_b = class_name_to_integer(b['報名班別'])

    if class_name_a != class_name_b:
        return class_name_a - class_name_b

    if a['性別'] != b['性別']:
        return -1 if a['性別'] < b['性別'] else 1

    if a['學員姓名'] != b['學員姓名']:
        return -1 if a['學員姓名'] < b['學員姓名'] else 1
    return 0


def generate_introducer_reports(cfg: PzProjectConfig):
    member_service = PzGrandMemberService(cfg, from_access=False, from_google=False)

    # members = member_service.read_member_details_from_mysql()
    # for member in members:
    #     print(member)
    # entities = member_service.read_class_members_from_mysql()
    #
    # for entity in entities:
    #     print(entity)
    #
    service = ExcelWorkbookService(PzQuestionnaireInfo({}), cfg.excel.questionnaire.spreadsheet_file,
                                   cfg.excel.questionnaire.sheet_name, header_at=cfg.excel.questionnaire.header_row,
                                   debug=True)
    template_service = ExcelTemplateService(PzIntroducerContactForOutput({}), cfg.excel.templates['introducer'],
                                            cfg.output_folder, debug=True)

    print('--------- Template Headers -------')
    print(template_service.get_headers())
    print('----------------------------------')

    entries: list[PzQuestionnaireInfo] = service.read_all(required_attribute='fullName')

    # mapping = {'介紹人': 1, '班別': 2, '組別': 3, '學員姓名': 4, '性別': 5, '報名班別': 6, '茶會/上午': 7,
    #            '茶會/晚上': 8, '讀經班家長/關係': 9, '連絡電話': 10, '說明事項': 11, '2/22出席': 12, '2/29出席': 13,
    #            '電聯註記': 14}

    data = []

    for entry in entries:
        if entry.fullName is None:
            continue

        phone_list = [entry.mobilePhone, entry.parentsPhone, entry.homePhone]
        phones = list(OrderedDict.fromkeys(item for item in phone_list if item))

        # print(entry.to_json())
        datum: dict[str, str | int] = {
            '介紹人': entry.introducerName,
            '學員姓名': entry.fullName,
            '性別': entry.gender,
            '連絡電話': "\n".join(phones),
            '報名班別': entry.registerClass if entry.registerClass is not None else '',
            '說明事項': entry.remark,
            '讀經班家長/關係': entry.parents if entry.parents is not None and
                                                entry.registerClass is not None and
                                                entry.registerClass.startswith('兒童') else '',
            '茶會/上午': 'V' if entry.tee == '上午' else '',
            '茶會/晚上': 'V' if entry.tee == '晚上' else '',
        }
        introducer = member_service.find_one_class_member_by_pz_name(entry.introducerName)

        if introducer is not None:
            datum['班別'] = introducer.class_name
            datum['組別'] = introducer.class_group
        else:
            datum['班別'] = ''
            datum['組別'] = ''

        data.append(datum)

    sorted_list = sorted(data, key=functools.cmp_to_key(data_by_class_and_group))

    supplier = (lambda y=x: x for x in sorted_list)
    template_service.write_data(supplier)
