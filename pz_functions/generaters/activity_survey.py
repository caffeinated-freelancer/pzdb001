from typing import Any

from loguru import logger

from pz.config import PzProjectConfig, PzProjectExcelSpreadsheetConfig
from pz.models.activity_survey_model import ActivitySurveyModel
from pz.utils import excel_files_in_folder
from services.excel_template_service import ExcelTemplateService
from services.grand_member_service import PzGrandMemberService
from services.senior_deacon_service import SeniorDeaconService


def activity_survey(cfg: PzProjectConfig):
    activity_survey_config = cfg.excel.meditation_activity_survey

    member_service = PzGrandMemberService(cfg, from_access=False, from_google=False, all_via_access_db=False)

    deacon_service = SeniorDeaconService(cfg)

    all_members = member_service.fetch_all_class_members_with_details()

    # senior_service.

    folder = activity_survey_config.spreadsheet_folder

    logger.info(f'meditation activity survey folder: {folder}')

    for f in excel_files_in_folder(folder):
        spreadsheet = PzProjectExcelSpreadsheetConfig({
            'spreadsheet_file': f.filepath,
            'header_row': activity_survey_config.header_row,
            'header_on_blank_try': activity_survey_config.header_on_blank_try,
            'page_mode': activity_survey_config.page_mode,
        })

        logger.info(f'processing {f.filename}')

        template = ExcelTemplateService(ActivitySurveyModel({}),
                                        spreadsheet,
                                        f.filename, cfg.output_folder,
                                        f'[禪修活動調查]',
                                        debug=False)

        dharma_protector_header = "護法會"
        for header in template.get_headers():
            if dharma_protector_header in header:
                dharma_protector_header = header
                logger.info(f"護法會標題列: {dharma_protector_header}")

        template_sheet_name = "template"
        template.sheet_rename(template_sheet_name)
        template.set_template_sheet(template_sheet_name)

        max_page_entries = template.max_page_entries()

        first_sheet_name = None

        for class_name in cfg.meditation_class_names:
            class_members = []
            number = 0
            group_id = -1
            page_no = 0
            page_entries = 0

            for member in all_members:
                if member.class_name == class_name:
                    entry: dict[str, Any] = {}
                    # print(f'{member.class_name} {member.class_group} {member.student_id} {member.real_name} {member.dharma_name}')

                    if member.class_group != group_id:
                        if len(class_members) > 0:
                            number = 0
                            if page_no == 0:
                                template.duplicate_sheet(template_sheet_name, class_name)
                                if first_sheet_name is None:
                                    first_sheet_name = class_name
                            else:
                                template.duplicate_page(page_no)

                            supplier = (lambda y=x: x for x in class_members)
                            template.write_data(supplier, on_page=page_no, save=False)
                            page_no += 1

                        group_id = member.class_group
                        class_members.clear()
                        page_entries = 0
                    # else:

                    page_entries += 1

                    if page_entries > max_page_entries:
                        template.duplicate_page(page_no)
                        supplier = (lambda y=x: x for x in class_members)
                        template.write_data(supplier, on_page=page_no, save=False)
                        class_members.clear()
                        page_no += 1
                        page_entries = 1

                    number += 1
                    entry['No.'] = number
                    entry['姓名'] = member.real_name
                    entry['法名'] = member.dharma_name
                    entry['學員編號'] = member.student_id
                    entry['班級'] = class_name
                    entry['組別'] = member.class_group
                    entry['性別'] = member.gender
                    entry['groupId'] = member.class_group
                    entry['執事'] = deacon_service.find_deacon(class_name, member.class_group, member)

                    if member.have_detail:
                        entry[dharma_protector_header] = member.dharma_protection_position
                    else:
                        entry[dharma_protector_header] = None
                    class_members.append(entry)

        template.remove_sheet(template_sheet_name)
        template.set_active_sheet(first_sheet_name)

        template.save_as(f'{cfg.output_folder}/[禪修班活動調查]{f.filename}')
