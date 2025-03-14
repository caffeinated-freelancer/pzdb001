import glob
import os
import re
from typing import Any

from loguru import logger

from pz.config import PzProjectConfig, PzProjectExcelSpreadsheetConfig
from pz.models.attend_record import AttendRecord
from pz.models.output_graduation import PzGraduationForOutput
from pz.models.text_with_properties import TextWithProperties
from services.attend_record_service import AttendRecordFileDetail
from services.excel_template_service import ExcelTemplateService
from services.excel_workbook_service import ExcelWorkbookService


def add_page_break(datum, prev_datum) -> tuple[Any, bool]:
    if prev_datum is not None:
        if prev_datum['組別'] != datum['組別']:
            # print("send page break")
            return datum, True
    return datum, False


def generate_graduation_report(cfg: PzProjectConfig, spreadsheet_cfg: PzProjectExcelSpreadsheetConfig,
                               detail: AttendRecordFileDetail, filename: str):
    if detail.class_name is None:
        logger.warning(f'{detail.filename} 檔名需按標準命名 精舍名_班級名_上課...')
    else:
        class_name = detail.class_name
        # print(class_name)

        # if class_name not in standards:
        #     print(f'{class_name} 班級沒有設定好結業標準, 程式無法處理')
        #     return

        # standard = standards[class_name]

        records_excel = ExcelWorkbookService(AttendRecord({}), filename, None,
                                             header_at=spreadsheet_cfg.header_row,
                                             ignore_parenthesis=spreadsheet_cfg.ignore_parenthesis, print_header=False,
                                             debug=False)
        headers = records_excel.get_headers()

        days = [x for x in headers.keys() if re.match(r'\d{1,2}/\d{1,2}', x)]
        # print(days)
        # print(standard.to_json())

        template_service = ExcelTemplateService(PzGraduationForOutput({}),
                                                cfg.excel.graduation.template,
                                                detail.filename,
                                                cfg.output_folder,
                                                f'[結業統計表][{class_name}]',
                                                debug=False)

        template_columns = [x for x in template_service.get_headers().keys() if isinstance(x, int)]
        sheet = template_service.get_sheet()

        title = sheet.cell(1, 1).value
        if title is not None and isinstance(title, str):
            sheet.cell(1, 1).value = title.replace('{class_name}', class_name)

        if len(days) > len(template_columns):
            index = template_service.get_headers().get(max(template_columns))
            amount = len(days) - len(template_columns)

            template_index = template_service.get_headers().get(min(template_columns))

            template_service.insert_columns(template_index, index + 1, amount)
            value = max(template_columns)
            row = template_service.header_row

            for i in range(0, amount, 1):
                column = index + i + 1
                sheet.cell(row, column).value = value + i + 1

            template_service.rehash_header()

        # print(template_service.get_headers())
        # print(headers)

        template_header = template_service.get_headers()
        # print(template_header)
        date2index: dict[str, int] = {}

        for i, day in enumerate(days):
            idx = i + 1
            if idx in template_header:
                sheet.cell(template_service.header_row + 1, template_header[idx]).value = day
                date2index[day] = idx

        raw_records: list[AttendRecord] = records_excel.read_all(required_attribute='studentId')
        data = []
        vacations: dict[str, int] = {}
        blank_days: dict[str, int] = {}
        last_group = -1
        group_serial_no = 0
        records: list[AttendRecord] = []

        for record in raw_records:
            if record.realName.startswith('範例-'):
                continue
            records.append(record)

            for day in days:
                if day in date2index:
                    if day in record.records:
                        value = record.records[day]
                        if value is None or value == '':
                            if day in blank_days:
                                blank_days[day] += 1
                            else:
                                blank_days[day] = 1
                        elif value == 'F':
                            if day in vacations:
                                vacations[day] += 1
                            else:
                                vacations[day] = 1

        vacation_days = set()
        no_data_days = set()

        for day, count in vacations.items():
            if count * 3 >= len(records) * 2:
                vacation_days.add(day)
                logger.info(f'{count} against {len(records)} - add {day} as vacation ({detail.filename})')

        for day, count in blank_days.items():
            if count * 3 >= len(records) * 2:
                no_data_days.add(day)
                # print(f'add {day} as no data ({filename})')

        days_left = len(no_data_days)
        logger.info(f'{len(vacation_days)} vacation, {days_left} day(s) without data')

        for record in records:
            current_group_number = int(record.groupName)

            if current_group_number != last_group:
                group_serial_no = 1
                last_group = current_group_number
            else:
                group_serial_no += 1

            attend_counters: dict[str, int] = {
                'V': 0,  # 出席
                'O': 0,  # 請假
                'A': 0,  # 晚到(曠課)
                'X': 0,  # 中輟
                'D': 0,  # 日補
                'N': 0,  # 夜捕
                'W': 0,  # 公假
                'F': 0,  # 放香
                'M': 0,  # 補課
                'L': 0,  # 遲到
                'E': 0,  # 早退
                'ML': 0, # 靜坐補課 [當出席]
                'LL': 0, # 靜坐遲到
                'S1': 0, # 特殊 1 (回山護持本山各類禪七活動) [當補課]
                '_': 0,  # 空白/無資料
            }

            datum: dict[str | int, str | int | TextWithProperties | dict[str, int]] = {
                '學員編號': record.studentId,
                '姓名': record.realName,
                '法名': record.dharmaName,
                '性別': record.gender,
                '班別': class_name,
                '組別': record.groupName,
                '組號': current_group_number,
                '序號': group_serial_no,
                '執事': '',
            }
            # print(record.realName)
            for day in days:
                if day in date2index:
                    if day in record.records:
                        value = record.records[day]
                        datum[date2index[day]] = value
                        if value is None or value == '':
                            if day not in no_data_days:
                                attend_counters['_'] += 1
                        elif value in attend_counters:
                            if day not in no_data_days:
                                attend_counters[value] += 1

                                if value == 'F':
                                    if day not in vacation_days:
                                        logger.warning(
                                            f'糟糕! {day} 大部份的學員*不是是放香*, 但 {record.realName} 卻能放香')
                                else:
                                    if day in vacation_days:
                                        logger.warning(
                                            f'糟糕! {day} 大部份的學員是放香, 但 {record.realName} 是 {value}')
                            else:
                                logger.warning(
                                    f'{record.realName} / {class_name} 在 {day} 的記錄為 {value}, 但大部份的學員都還沒有記錄影(時間未到)')
                    else:
                        datum[date2index[day]] = ''
            # '出席V': 31, '遲到L': 32, '補課M': 33, '請假O': 34, '放香F': 35, '曠課A': 36, '全勤': 37, '勤學': 38, '結業': 39
            datum['出席V'] = attend_counters['V'] + attend_counters['ML']
            datum['遲到L'] = attend_counters['L']
            datum['靜坐遲到LL'] = attend_counters['LL']
            datum['補課M'] = attend_counters['M']
            datum['請假O'] = attend_counters['O']
            datum['放香F'] = attend_counters['F']
            datum['曠課A'] = attend_counters['A']
            datum['counters'] = attend_counters
            data.append(datum)

        number_of_weeks = len(days) - len(vacation_days)
        graduation_standard = cfg.excel.graduation.graduation_standards.get(number_of_weeks)

        notes = cfg.excel.graduation.template.additional_notes

        graduation_warning_tag = '結業預警'
        graduation_warning = 'H'

        if graduation_warning_tag in notes:
            graduation_warning = notes[graduation_warning_tag]

        for datum in data:
            attend_counters = datum['counters']
            # print(f'{len(days)} - {len(vacations)} = {len(days) - len(vacations)}, weeks: {weeks}')
            graduated = False

            if days_left > 0 and graduation_standard is not None:
                if graduation_standard.calculate(attend_counters):
                    datum['結業'] = notes['圓滿結業'] if '圓滿結業' in notes else 'V'
                else:
                    saved = attend_counters
                    attend_counters['V'] += days_left
                    if graduation_standard.calculate(attend_counters):
                        datum['結業'] = notes['結業在即'] if '結業在即' in notes else 'K'
                    else:
                        attend_counters = saved

                        make_up = attend_counters['O'] + attend_counters['A'] + attend_counters['_'] + attend_counters['LL']
                        m_org = attend_counters['M']
                        attend_counters['M'] += make_up
                        attend_counters['A'] = 0
                        attend_counters['O'] = 0
                        attend_counters['_'] = 0
                        attend_counters['LL'] = 0
                        if graduation_standard.calculate(attend_counters):
                            for i in range(1, make_up + 1):
                                attend_counters['M'] = m_org + i
                                attend_counters['O'] = make_up - i
                                if graduation_standard.calculate(attend_counters):
                                    m = graduation_warning.replace("{{m}}", str(i))
                                    datum['結業'] = TextWithProperties(m, {'color': 'FF0000'})
                                    break
                        else:
                            text = notes['缺課過多'] if '缺課過多' in notes else ''
                            datum['結業'] = TextWithProperties(text, {'color': 'FF0000'})
                    attend_counters = saved
            else:
                if graduation_standard is not None:
                    if graduation_standard.calculate(attend_counters):
                        datum['結業'] = 'V'
                        graduated = True

                if attend_counters['V'] == number_of_weeks:
                    datum['全勤'] = notes['全勤'] if '全勤' in notes else '全勤'
                elif not graduated and attend_counters['V'] + attend_counters['L'] + attend_counters[
                    'M'] == number_of_weeks:
                    datum['勤學'] = notes['勤學'] if '勤學' in notes else '勤學'

        supplier = (lambda y=x: x for x in data)
        template_service.write_data(supplier, callback=lambda x, y, z: add_page_break(x, y))


def generate_graduation_reports(cfg: PzProjectConfig):
    graduation_cfg = cfg.excel.graduation
    # print(graduation_cfg)
    cfg.make_sure_output_folder_exists()
    cfg.explorer_output_folder()

    # standards_excel = ExcelWorkbookService(GraduationStandards({}), graduation_cfg.standards.spreadsheet_file,
    #                                        None, debug=True)
    #
    # all_standards: list[GraduationStandards] = standards_excel.read_all('className')
    # standards: dict[str, GraduationStandards] = {}
    #
    # for standard in all_standards:
    #     key = standard.classNameInFile if standard.classNameInFile is not None and standard.classNameInFile != '' else standard.className
    #     standards[key] = standard

    files = glob.glob(f'{graduation_cfg.records.spreadsheet_folder}/*.xlsx')

    for filename in files:
        f = os.path.basename(filename)
        if not f.startswith("~$"):
            detail = AttendRecordFileDetail(cfg, f)

            try:
                generate_graduation_report(cfg, graduation_cfg.records, detail, filename)
            except Exception as e:
                logger.warning(f'{filename} - {e}')
        # break
