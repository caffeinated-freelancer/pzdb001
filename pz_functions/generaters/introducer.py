import functools
import glob
import os
from collections import OrderedDict
from typing import Any

from loguru import logger

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

    introducer_tag = '介紹人'
    gender = '性別'
    student_name_tag = '學員姓名'

    if introducer_tag in a and introducer_tag in b:
        try:
            if a[introducer_tag] != b[introducer_tag]:
                return -1 if a[introducer_tag] < b[introducer_tag] else 1
        except:
            pass
    elif introducer_tag in a:
        return -1
    elif introducer_tag in b:
        return 1
    else:
        logger.debug(f"{a[student_name_tag]} 跟 {b[introducer_tag]} 都沒有介紹人")

    if gender in a and gender in b:
        if a[gender] is not None and b[gender] is not None:
            if a[gender] != b[gender]:
                return -1 if a[gender] < b[gender] else 1

    if a[student_name_tag] != b[student_name_tag]:
        return -1 if a[student_name_tag] < b[student_name_tag] else 1
    return 0


def duplicate_header(datum, prev_datum) -> bool:
    if prev_datum is not None:
        if prev_datum['介紹人'] != datum['介紹人']:
            logger.trace(f'duplicate header {prev_datum['介紹人']} -> {datum['介紹人']}')
            return True
    return False


def generate_introducer_report(member_service: PzGrandMemberService, cfg: PzProjectConfig, spreadsheet_file: str):
    # member_service = PzGrandMemberService(cfg, from_access=False, from_google=False)

    # members = member_service.read_member_details_from_mysql()
    # for member in members:
    #     print(member)
    # entities = member_service.read_class_members_from_mysql()
    #
    # for entity in entities:
    #     print(entity)
    #
    notes = cfg.excel.questionnaire.additional_notes

    split_file = False
    if '按班級拆檔案' in notes and notes['按班級拆檔案']:
        split_file = True

    on_having_class_note = ''
    if '已有班級電聯註記' in notes:
        on_having_class_note = notes['已有班級電聯註記']

    service = ExcelWorkbookService(PzQuestionnaireInfo({}), spreadsheet_file,
                                   cfg.excel.questionnaire.sheet_name, header_at=cfg.excel.questionnaire.header_row,
                                   debug=True)
    entries: list[PzQuestionnaireInfo] = service.read_all(required_attribute='fullName')

    logger.info(f'{len(entries)} questionnaire entries found')

    # mapping = {'介紹人': 1, '班別': 2, '組別': 3, '學員姓名': 4, '性別': 5, '報名班別': 6, '茶會/上午': 7,
    #            '茶會/晚上': 8, '讀經班家長/關係': 9, '連絡電話': 10, '說明事項': 11, '2/22出席': 12, '2/29出席': 13,
    #            '電聯註記': 14}

    data = []

    classes_data: dict[str, list[dict[str, Any]]] = {}

    for entry in entries:
        if entry.fullName is None:
            continue

        if entry.cancel is not None and entry.cancel != '':
            continue

        phone_list = [entry.mobilePhone, entry.parentsPhone, entry.homePhone]
        logger.trace(phone_list)
        phones = list(OrderedDict.fromkeys(item for item in phone_list if item))
        logger.trace(phones)

        have_register_class = entry.registerClass is not None and entry.registerClass != ''

        # print(entry.to_json())
        datum: dict[str, str | int] = {
            '介紹人': entry.introducerName,
            '學員姓名': entry.fullName,
            '性別': entry.gender,
            '連絡電話': "\n".join(phones),
            '報名班別': entry.registerClass if have_register_class else '',
            '說明事項': entry.remark,
            '讀經班家長/關係': entry.parents if entry.parents is not None and have_register_class and entry.registerClass.startswith(
                '兒童') else '',
            '茶會/上午': 'V' if entry.tee == '上午' else '',
            '茶會/晚上': 'V' if entry.tee == '晚上' else '',
            '喫茶趣': entry.chaForTea if entry.chaForTea is not None else '',
        }
        introducer = member_service.find_one_class_member_by_pz_name(entry.introducerName)

        pz_class_name = ''

        if introducer is not None:
            datum['班別'] = introducer.class_name
            datum['組別'] = introducer.class_group
            pz_class_name = introducer.class_name
        else:
            datum['班別'] = ''
            datum['組別'] = ''

        if have_register_class and not entry.registerClass.startswith('兒童'):
            datum['電聯註記'] = on_having_class_note
        else:
            datum['電聯註記'] = ''

        if split_file:
            pz_class_name = '-' if pz_class_name == '' else pz_class_name
            if pz_class_name not in classes_data:
                classes_data[pz_class_name] = []

            classes_data[pz_class_name].append(datum)
        else:
            data.append(datum)

    if split_file:
        for pz_class_name in classes_data:
            class_data = classes_data[pz_class_name]

            sorted_list = sorted(class_data, key=functools.cmp_to_key(data_by_class_and_group))

            template_service = ExcelTemplateService(PzIntroducerContactForOutput({}), cfg.excel.templates['introducer'],
                                                    spreadsheet_file, cfg.output_folder,
                                                    f'[介紹人電聯表][{pz_class_name}]', debug=True)

            supplier = (lambda y=x: x for x in sorted_list)
            template_service.write_data(supplier, duplicate_callback=lambda x, y, z: duplicate_header(x, y))
    else:
        sorted_list = sorted(data, key=functools.cmp_to_key(data_by_class_and_group))

        template_service = ExcelTemplateService(PzIntroducerContactForOutput({}), cfg.excel.templates['introducer'],
                                                spreadsheet_file, cfg.output_folder, '[介紹人電聯表]', debug=True)

        supplier = (lambda y=x: x for x in sorted_list)
        template_service.write_data(supplier, duplicate_callback=lambda x, y, z: duplicate_header(x, y))


def generate_introducer_reports(cfg: PzProjectConfig):
    member_service = PzGrandMemberService(cfg, from_access=False, from_google=False)

    if cfg.excel.questionnaire.spreadsheet_folder is not None and cfg.excel.questionnaire.spreadsheet_folder != '':
        files = glob.glob(f'{cfg.excel.questionnaire.spreadsheet_folder}/*.xlsx')

        for filename in files:
            f = os.path.basename(filename)
            if not f.startswith("~$"):
                try:
                    generate_introducer_report(member_service, cfg, filename)
                except Exception as e:
                    logger.warning(f'{filename} - {e}')
                    logger.exception(e)
    else:
        generate_introducer_report(member_service, cfg, cfg.excel.questionnaire.spreadsheet_file)
