import sys
from getopt import getopt, GetoptError

from pz.cloud.spreadsheet_member_service import PzCloudSpreadsheetMemberService
from pz.config import PzProjectConfig
from pz.models.pz_questionnaire_info import PzQuestionnaireInfo
from pz_functions.generaters.introducer import generate_introducer_reports
from pz_functions.generaters.senior import generate_senior_reports
from pz_functions.importers.mysql_functions import write_data_to_mysql
from pz_functions.mergers.member_merging import member_data_merging
from services.excel_workbook_service import ExcelWorkbookService


def read_members_from_cloud(spreadsheet_id: str, secret_file: str):
    PzCloudSpreadsheetMemberService(spreadsheet_id, secret_file)


def read_new_members_from_excel(excel_file: str, sheet_name: str):
    service = ExcelWorkbookService(PzQuestionnaireInfo({}), excel_file, sheet_name, debug=True)
    service.read_all()


if __name__ == '__main__':
    short_opts = 'hvdc:'

    long_opts = [
        "help",
        "verbose",
        "debug",
        "config=",
        "write-to-mysql",
        "generate-introducer-reports",
        "generate-senior-reports"
    ]

    try:
        options, args = getopt(sys.argv[1:], short_opts, long_opts)
    except GetoptError as err:
        print(f"Error parsing options: {err}")
        sys.exit(2)

    config_file = 'C:/Applications/pzdb001/config.yaml'
    verbose = False
    debug = False
    write_data_to_mysql_flag = False
    generate_introducer_reports_flag = False
    generate_senior_reports_flag = False
    member_data_merging_flag = False

    for opt, arg in options:
        if opt in ("-h", "--help"):
            # Display help message
            print("Help message...")
            sys.exit()
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt in ("-d", "--debug"):
            debug = True
        elif opt in ("-c", "--config"):
            config_file = arg
        elif opt == "--write-to-mysql":
            write_data_to_mysql_flag = True
        elif opt == "--generate-introducer-reports":
            generate_introducer_reports_flag = True
        elif opt == "--generate-senior-reports":
            generate_senior_reports_flag = True
        else:
            print(f"Unknown option: {opt}")
            sys.exit(2)

    cfg = PzProjectConfig.from_yaml(config_file)

    if write_data_to_mysql_flag:
        write_data_to_mysql(cfg)
    elif generate_introducer_reports_flag:
        generate_introducer_reports(cfg)
    elif generate_senior_reports_flag:
        generate_senior_reports(cfg)
    elif member_data_merging_flag:
        member_data_merging(cfg.ms_access_db.db_file, cfg.ms_access_db.target_table)
        # read_merging_data(cfg.ms_access_db.db_file, cfg.ms_access_db.target_table)
