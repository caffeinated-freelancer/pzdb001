import glob
import re
from typing import Any

from pz.config import PzProjectConfig, PzProjectExcelSpreadsheetConfig
from pz.models.attend_record import AttendRecord
from pz.models.graduation_standards import GraduationStandards
from pz.models.output_graduation import PzGraduationForOutput
from services.excel_template_service import ExcelTemplateService
from services.excel_workbook_service import ExcelWorkbookService


def add_page_break(datum, prev_datum) -> tuple[Any, bool]:
    if prev_datum is not None:
        if prev_datum['組別'] != datum['組別']:
            # print("send page break")
            return datum, True
    return datum, False


def generate_graduation_report(cfg: PzProjectConfig, standards: dict[str, GraduationStandards],
                               spreadsheet_cfg: PzProjectExcelSpreadsheetConfig, filename: str):
    matched = re.match(r'^(.*)_(.*)_上課.*', filename)
    if matched:
        class_name = matched.group(2)
        # print(class_name)

        if class_name not in standards:
            print(f'{class_name} 班級沒有設定好結業標準, 程式無法處理')
            return

        standard = standards[class_name]

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
                                                filename,
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
            template_service.insert_columns(index + 1, amount)
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
                print(f'{count} against {len(records)} - add {day} as vacation ({filename})')

        for day, count in blank_days.items():
            if count * 3 >= len(records) * 2:
                no_data_days.add(day)
                # print(f'add {day} as no data ({filename})')

        days_left = len(no_data_days)
        print(f'{len(vacation_days)} vacation, {days_left} day(s) without data')

        for record in records:
            if record.groupNumber != last_group:
                group_serial_no = 1
                last_group = record.groupNumber
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
                '_': 0,  # 空白/無資料
            }

            datum: dict[str | int, str | int | dict[str, int]] = {
                '學員編號': record.studentId,
                '姓名': record.realName,
                '法名': record.dharmaName,
                '性別': record.gender,
                '班別': standard.className,
                '組別': record.groupName,
                '組號': record.groupNumber,
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
                                        print(f'Warning! {day} (should not be F for {record.realName}) )')
                                else:
                                    if day in vacation_days:
                                        print(f'Warning! {day} (should be F for {record.realName})')
                            else:
                                print(
                                    f'Warning! {day} (got {value}, should be blank for {record.realName} / {class_name}) )')
                    else:
                        datum[date2index[day]] = ''
            # '出席V': 31, '遲到L': 32, '補課M': 33, '請假O': 34, '放香F': 35, '曠課A': 36, '全勤': 37, '勤學': 38, '結業': 39
            datum['出席V'] = attend_counters['V']
            datum['遲到L'] = attend_counters['L']
            datum['補課M'] = attend_counters['M']
            datum['請假O'] = attend_counters['O']
            datum['放香F'] = attend_counters['F']
            datum['曠課A'] = attend_counters['A']
            datum['counters'] = attend_counters
            data.append(datum)

        number_of_weeks = len(days) - len(vacation_days)
        graduation_standard = cfg.excel.graduation.graduation_standards.get(number_of_weeks)

        for datum in data:
            attend_counters = datum['counters']
            # print(f'{len(days)} - {len(vacations)} = {len(days) - len(vacations)}, weeks: {weeks}')
            graduated = False

            if days_left > 0 and graduation_standard is not None:
                if graduation_standard.calculate(attend_counters):
                    datum['結業'] = 'V'
                else:
                    attend_counters['V'] += days_left
                    if not graduation_standard.calculate(attend_counters):
                        datum['結業'] = 'X'
                    attend_counters['V'] -= days_left
            else:
                if graduation_standard is not None:
                    if graduation_standard.calculate(attend_counters):
                        datum['結業'] = 'V'
                        graduated = True

                if attend_counters['V'] == number_of_weeks:
                    datum['全勤'] = '全勤'
                elif not graduated and attend_counters['V'] + attend_counters['L'] + attend_counters[
                    'M'] == number_of_weeks:
                    datum['勤學'] = '勤學'

        supplier = (lambda y=x: x for x in data)
        template_service.write_data(supplier, callback=lambda x, y: add_page_break(x, y))
    else:
        print(f'{filename} 檔名需按標準命名 精舍名_班級名_上課...')


def generate_graduation_reports(cfg: PzProjectConfig):
    graduation_cfg = cfg.excel.graduation
    # print(graduation_cfg)
    cfg.make_sure_output_folder_exists()
    cfg.explorer_output_folder()

    standards_excel = ExcelWorkbookService(GraduationStandards({}), graduation_cfg.standards.spreadsheet_file,
                                           None, debug=True)

    all_standards: list[GraduationStandards] = standards_excel.read_all('className')
    standards: dict[str, GraduationStandards] = {}

    for standard in all_standards:
        key = standard.classNameInFile if standard.classNameInFile is not None and standard.classNameInFile != '' else standard.className
        standards[key] = standard

    files = glob.glob(f'{graduation_cfg.records.spreadsheet_folder}/*.xlsx')

    for filename in files:
        generate_graduation_report(cfg, standards, graduation_cfg.records, filename)
        # break
