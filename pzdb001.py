import os
import sys
from getopt import getopt, GetoptError
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
)
from loguru import logger

from pz.config import PzProjectConfig
from pz.models.pz_questionnaire_info import PzQuestionnaireInfo
from pz_functions.exporters.member_details_exporter import export_member_details
from pz_functions.generaters.graduation import generate_graduation_reports
from pz_functions.generaters.introducer import generate_introducer_reports
from pz_functions.generaters.member_comparison import generate_member_comparison_table
from pz_functions.generaters.senior import generate_senior_reports
from pz_functions.importers.member_card import import_member_card_from_access
from pz_functions.importers.member_details_update import member_details_update
from pz_functions.importers.mysql_functions import write_access_to_mysql, write_google_to_mysql
from pz_functions.mergers.member_merging import member_data_merging
from services.excel_workbook_service import ExcelWorkbookService
from ui.windows_gui import PyPzWindows


# def read_members_from_cloud(spreadsheet_id: str, secret_file: str):
#     PzCloudSpreadsheetMemberService(spreadsheet_id, secret_file)


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
        "card-record-to-mysql",
        "generate-introducer-reports",
        "generate-senior-reports",
        "generate-graduation-reports",
        "generate-member-comparison",
        "access-to-mysql",
        "google-to-mysql",
        "generate-predefined-senior-reports",
        "export-details",
        "import-details",
    ]

    try:
        options, args = getopt(sys.argv[1:], short_opts, long_opts)
    except GetoptError as err:
        print(f"Error parsing options: {err}")
        sys.exit(2)

    default_config_file = r'config.yaml'

    default_config_files: list[str] = [
        r'config.yaml',
        r'C:\Applications\pzdb001\config.yaml',
        r'\\NS-Puzhong2\資料組\禪修程式檔\config.yaml'
    ]

    # get_usb_info()

    for cfg_file in default_config_files:
        if Path(cfg_file).exists():
            default_config_file = cfg_file
            break

    # if not Path(default_config_file).exists():
    #     if Path('config.yaml').exists():
    #         default_config_file=Path('config.yaml').absolute()
    #     else:
    #         default_config_file = r'\\NS-Puzhong2\資料組\禪修程式檔\config.yaml'

    # config_file = os.getenv('PZDB_CONFIG', r'\\NS-Puzhong2\資料組\禪修程式檔\config.yaml')
    config_file = os.getenv('PZDB_CONFIG', default_config_file)

    logger.info(f'read config file from: {config_file}')
    verbose = False
    debug = False
    write_access_to_mysql_flag = False
    write_google_to_mysql_flag = False
    generate_introducer_reports_flag = False
    generate_senior_reports_flag = False
    generate_predefined_senior_reports_flag = False
    generate_graduation_reports_flag = False
    member_data_merging_flag = False
    export_details_flag = False
    import_details_flag = False
    card_record_to_mysql_flag = False
    generate_member_comparison_flag = False

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
        elif opt == "--access-to-mysql":
            write_access_to_mysql_flag = True
        elif opt == "--google-to-mysql":
            write_google_to_mysql_flag = True
        elif opt == "--generate-introducer-reports":
            generate_introducer_reports_flag = True
        elif opt == "--generate-senior-reports":
            generate_senior_reports_flag = True
        elif opt == "--generate-graduation-reports":
            generate_graduation_reports_flag = True
        elif opt == "--generate-predefined-senior-reports":
            generate_predefined_senior_reports_flag = True
        elif opt == "--export-details":
            export_details_flag = True
        elif opt == "--import-details":
            import_details_flag = True
        elif opt == "--card-record-to-mysql":
            card_record_to_mysql_flag = True
        else:
            print(f"Unknown option: {opt}")
            sys.exit(2)

    cfg = PzProjectConfig.from_yaml(config_file)

    cfg.make_sure_output_folder_exists()
    logger.configure(
        handlers=[{"sink": sys.stderr, "level": cfg.logging.level}],  # Change 'WARNING' to your desired level
    )
    logger.add(cfg.logging.log_file, level=cfg.logging.level, format=cfg.logging.format)

    if write_access_to_mysql_flag:
        logger.info("Writing MS Access to MySQL database ...")
        write_access_to_mysql(cfg)
    elif write_google_to_mysql_flag:
        logger.info("Writing Google spreadsheet to MySQL database ...")
        write_google_to_mysql(cfg)
    elif generate_introducer_reports_flag:
        logger.info("Generating introducer reports ...")
        generate_introducer_reports(cfg)
    elif generate_senior_reports_flag:
        logger.info("Generating senior reports ...  (from scratch)")
        generate_senior_reports(cfg, True)
    elif generate_predefined_senior_reports_flag:
        logger.info("Generating graduation reports ... (from predefined)")
        generate_senior_reports(cfg, False)
    elif generate_member_comparison_flag:
        logger.info("Generating member comparison ...")
        generate_member_comparison_table(cfg)
    elif member_data_merging_flag:
        logger.info("Merging member data ...")
        member_data_merging(cfg.ms_access_db.db_file, cfg.ms_access_db.target_table)
        # read_merging_data(cfg.ms_access_db.db_file, cfg.ms_access_db.target_table)
    elif generate_graduation_reports_flag:
        logger.info("Generating graduation reports ... (from scratch)")
        generate_graduation_reports(cfg)
    elif export_details_flag:
        logger.info("Exporting details ...")
        export_member_details(cfg)
    elif import_details_flag:
        logger.info("Importing details ...")
        member_details_update(cfg)
    elif card_record_to_mysql_flag:
        logger.info("Merging card records to MySQL database ...")
        import_member_card_from_access(cfg)
    else:
        app = QApplication([])
        # window = QWidget()
        # window.setWindowTitle("普中資料管理程式")
        # window.setGeometry(100, 100, 580, 680)
        #
        # layout = QHBoxLayout()
        #
        # button = QPushButton("產生結業報表")
        # button.clicked.connect(partial(generate_graduation_reports, cfg))
        #
        # layout.addWidget(button)
        # layout.addWidget(QPushButton("Center"))
        # layout.addWidget(QPushButton("Right"))
        # window.setLayout(layout)
        #
        # window.show()
        # sys.exit(app.exec())

        window = PyPzWindows(cfg)
        window.show()
        sys.exit(app.exec())
