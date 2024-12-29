import os
import subprocess
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QAction
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QPushButton, QVBoxLayout, QGridLayout, QLabel, QFileDialog, QProgressDialog, )
from loguru import logger

from pz.config import PzProjectConfig
from pz.utils import explorer_folder
from pz_functions.exporters.member_details_exporter import export_member_details
from pz_functions.generaters.activity_survey import activity_survey
from pz_functions.generaters.graduation import generate_graduation_reports
from pz_functions.generaters.introducer import generate_introducer_reports
from pz_functions.generaters.member_comparison import generate_member_comparison_table
from pz_functions.generaters.qrcode import QRCodeGeneratrUiService
from pz_functions.importers.mysql_functions import write_google_relation_to_mysql
from ui.access_db_dialog import AccessDatabaseDialog
from ui.checkin_system_dialog import CheckinSystemDialog
from ui.cloud_upload_dialog import CloudUploadDialog
from ui.config_holder import ConfigHolder
from ui.general_ui_worker import GeneralUiWorker
from ui.member_import_dialog import MemberImportDialog
from ui.pilgrimage_dialog import PilgrimageDialog
from ui.processing_done_dialog import ProcessingDoneDialog
from ui.senior_contact_dialog import SeniorContactDialog
from ui.senior_report_common import SeniorReportCommon
from ui.toolbox_dialog import ToolboxDialog
from ui.ui_commons import PzUiCommons
from ui.ui_utils import style101_button_creation
from ui.vlookup_dialog import VLookUpDialog
from version import __pz_version__

WINDOW_SIZE = 235
DISPLAY_HEIGHT = 35
BUTTON_SIZE = 120


class PyPzWindows(QMainWindow):
    configHolder: ConfigHolder
    # dispatchDocDialog: DispatchDocDialog
    seniorContactDialog: SeniorContactDialog
    memberImportDialog: MemberImportDialog
    vLookUpDialog: VLookUpDialog
    default_font: QFont
    uiCommons: PzUiCommons
    accessDatabaseDialog: AccessDatabaseDialog
    toolboxDialog: ToolboxDialog
    checkinSystemDialog: CheckinSystemDialog
    pilgrimageDialog: PilgrimageDialog
    seniorReportCommon: SeniorReportCommon
    pzCentralLayout: QVBoxLayout
    pzCentralWidget: QWidget
    cloudUploadDialog: CloudUploadDialog
    progressBar: QProgressDialog | None
    generalUiWorker: GeneralUiWorker | None

    def __init__(self, cfg: PzProjectConfig):
        super().__init__()
        self.configHolder = ConfigHolder(cfg)
        self.uiCommons = PzUiCommons(self, self.configHolder)
        self.setWindowTitle(f'普中資料管理程式 v{__pz_version__}')
        self.default_font = self.uiCommons.font14
        self.setFixedSize(880, 520)

        self.pzCentralLayout = QVBoxLayout()
        self.progressBar = None
        self.generalUiWorker = None

        # self.create_menu()
        # self.pzCentralWidget = QWidget(self)
        #
        # self.pzCentralWidget.setLayout(self.fullFunctionLayout)
        # self.pzCentralWidget.setLayout(self.simpleFunctionLayout)
        #
        # # self.setCentralWidget(self.fullFunctionWidget)
        # self.setCentralWidget(self.pzCentralWidget)

        self.change_to_simple_layout()

        # self.create_full_function_buttons()
        # self.create_simple_function_buttons()
        # self.dispatchDocDialog = DispatchDocDialog()
        # self.seniorContactDialog = SeniorContactDialog(self.configHolder)
        # self.show()
        # self.activateWindow()
        # self.memberImportDialog = MemberImportDialog(cfg)
        # self.vLookUpDialog = VLookUpDialog(cfg)
        # self.accessDatabaseDialog = AccessDatabaseDialog(cfg)
        # self.toolboxDialog = ToolboxDialog(cfg)
        # self.checkinSystemDialog = CheckinSystemDialog(cfg)
        # self.pilgrimageDialog = PilgrimageDialog(cfg)
        # self.seniorReportCommon = SeniorReportCommon(self, self.uiCommons, self.config)
        self.re_initialize()

        # layout = QHBoxLayout()
        # #
        # button = QPushButton("產生結業報表")
        # button.clicked.connect(partial(generate_graduation_reports, cfg))
        #
        # layout.addWidget(button)
        # layout.addWidget(QPushButton("Center"))
        # layout.addWidget(QPushButton("Right"))
        # window.setLayout(layout)
        # self.show()

    def re_initialize(self):
        self.seniorContactDialog = SeniorContactDialog(self.configHolder)
        self.activateWindow()
        self.memberImportDialog = MemberImportDialog(self.configHolder)
        self.vLookUpDialog = VLookUpDialog(self.configHolder)
        self.accessDatabaseDialog = AccessDatabaseDialog(self.configHolder)
        self.cloudUploadDialog = CloudUploadDialog(self.configHolder)
        self.toolboxDialog = ToolboxDialog(self.configHolder)
        self.checkinSystemDialog = CheckinSystemDialog(self.configHolder)
        self.pilgrimageDialog = PilgrimageDialog(self.configHolder)
        self.seniorReportCommon = SeniorReportCommon(self, self.uiCommons, self.configHolder)
        self.show()

    def create_menu(self):
        menubar = self.menuBar()

        # Create a file menu
        file_menu = menubar.addMenu('&F) 功能')

        # Add actions to the file menu
        new_action = QAction('&New', self)
        open_action = QAction('&Open', self)
        save_action = QAction('&Save', self)
        exit_action = QAction('&Exit', self)

        # Add actions to the file menu
        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

    def do_nothing(self):
        os.startfile(self.configHolder.get_config().output_folder)

    def open_folder(self):
        os.startfile(self.configHolder.get_config().output_folder)

    def run_generate_graduation_reports(self):
        try:
            generate_graduation_reports(self.configHolder.get_config())
            # os.startfile(self.config.output_folder)
            self.uiCommons.done()
        except Exception as e:
            self.uiCommons.show_error_dialog(e)

    def run_introducer_report(self):
        try:
            self.configHolder.get_config().make_sure_output_folder_exists()
            self.configHolder.get_config().explorer_output_folder()
            generate_introducer_reports(self.configHolder.get_config())
            self.uiCommons.done()
        except Exception as e:
            self.uiCommons.show_error_dialog(e)

    # def show_error_dialog(self, e: Exception):
    #     message_box = QMessageBox(self)  # Set parent for proper positioning
    #
    #     # Set message box options (type, text, buttons)
    #     message_box.setIcon(QMessageBox.Icon.Information)  # Optional: Set icon
    #     message_box.setWindowTitle("糟糕")
    #
    #     message_box.setFont(self.default_font)
    #     message_box.setText(str(e))
    #     stack_trace = traceback.format_exc()  # Get stack trace as string
    #     print(f"Exception occurred: {str(e)}")
    #     print(f"Stack Trace:\n{stack_trace}")
    #
    #     message_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    #
    #     # Show the dialog and get the user's choice (optional)
    #     self.show()
    #     self.raise_()
    #     self.activateWindow()
    #     message_box.show()
    #
    #     # if button_clicked == QMessageBox.StandardButton.Ok:
    #     #     print("User clicked OK!")
    #     # elif button_clicked == QMessageBox.StandardButton.Cancel:
    #     #     print("User clicked Cancel!")

    def run_senior_report_from_scratch(self):

        self.seniorContactDialog.exec()

    def run_senior_report(self):
        self.seniorReportCommon.run_senior_report_from_scratch(False, from_excel=False, close_widget=False)
        # try:
        #     self.config.make_sure_output_folder_exists()
        #     self.config.explorer_output_folder()
        #     generate_senior_reports(self.config, False, from_excel=False)
        #     self.uiCommons.done()
        # except Exception as e:
        #     self.uiCommons.show_error_dialog(e)
        #     logger.error(e)

    # def show_dispatch_doc(self):
    #     # self.dispatchDocDialog.show()
    #     self.dispatchDocDialog.exec()

    def open_graduation_folder(self):
        explorer_folder(self.configHolder.get_config().excel.graduation.records.spreadsheet_folder)

    def open_questionnaire_folder(self):
        explorer_folder(self.configHolder.get_config().excel.questionnaire.spreadsheet_folder)

    def open_senior_folder(self):
        explorer_folder(os.path.dirname(self.configHolder.get_config().excel.new_class_senior.spreadsheet_file))

    def open_template_folder(self):
        explorer_folder(self.configHolder.get_config().template_folder)

    def open_output_folder(self):
        self.configHolder.get_config().make_sure_output_folder_exists()
        explorer_folder(self.configHolder.get_config().output_folder)

    def open_activity_survey_folder(self):
        explorer_folder(self.configHolder.get_config().excel.meditation_activity_survey.spreadsheet_folder)

    # def access_to_mysql(self):
    #     try:
    #         write_access_to_mysql(self.config)
    #     except Exception as e:
    #         self.uiCommons.show_error_dialog(e)
    #         logger.error(e)

    def handle_ms_access(self):
        self.accessDatabaseDialog.exec()

    def handle_cloud_upload(self):
        self.cloudUploadDialog.exec()

    def google_to_mysql(self):
        self.uiCommons.google_to_mysql()
        # try:
        #     write_google_to_mysql(self.config)
        # except Exception as e:
        #     self.uiCommons.show_error_dialog(e)
        #     logger.error(e)

    def google_relations_to_mysql(self):
        try:
            records, errors = write_google_relation_to_mysql(self.configHolder.get_config())
            label = QLabel()
            label.setFont(self.uiCommons.font14)
            label.setText(f'{records} 筆親眷朋友關係資料匯入')

            if len(errors) > 0:
                dialog = ProcessingDoneDialog(
                    self.configHolder, '完親眷朋友關係匯到資料庫', ['等級', '警告訊息'], [
                        [x.level_name(), x.message] for x in errors
                    ], [[label]])
                dialog.exec()
            else:
                self.uiCommons.done()
                self.uiCommons.show_message_dialog('Google 匯出', f'{records} 筆資料由 Google 的親眷朋友關係匯到資料庫')
        except Exception as e:
            self.uiCommons.show_error_dialog(e)
            logger.error(e)

    def open_settings_in_notepad(self):
        # Open the file content (might launch in browser on some systems)
        subprocess.run(["notepad.exe", self.configHolder.get_config().config_filename])
        # with open(self.config.config_filename, 'r') as file:
        #     content = file.read()
        #     webbrowser.open('data:text/plain;charset=utf-8,' + content)

    def re_read_settings(self):
        v0 = self.configHolder.get_config().version
        config = PzProjectConfig.from_yaml(self.configHolder.get_config().config_filename)
        self.configHolder.set_config(config)
        logger.info(f'Configure file version {config.version} (from: {v0})')
        logger.trace(self.configHolder.get_config())

        logger.configure(
            handlers=[{"sink": sys.stderr, "level": config.logging.level}],
            # Change 'WARNING' to your desired level
        )
        logger.add(config.logging.log_file, level=config.logging.level, format=config.logging.format)

        # self.uiCommons.show_message_dialog('重新讀取設定檔', '設定檔重新讀取完成, 新的設定已生效。')
        self.uiCommons.show_message_dialog(
            '重新讀取設定檔',
            f'<p>設定檔讀取完成, 設定檔版本 {config.version}。</p><p>注意! 此功能尚在測試階段, 若有任何問題, 請重啟程式。</p>')

    def member_info_export(self):
        try:
            filename = export_member_details(self.configHolder.get_config())
            self.uiCommons.done()
            self.uiCommons.show_message_dialog('匯出學員基本資料', f'匯出至 {filename}')
        except Exception as e:
            self.uiCommons.show_error_dialog(e)
            logger.error(e)

    def member_info_import(self):
        # self.dispatchDocDialog.exec()
        self.memberImportDialog.exec()
        # try:
        #     member_details_update(self.config)
        #     self.uiCommons.done()
        # except Exception as e:
        #     self.uiCommons.show_error_dialog(e)
        #     logger.error(e)
        # self.uiCommons.show_message_dialog('匯入/更新學員基本資料', f'完成匯入/更新學員基本資料')

    def vlookup_by_name(self):
        # try:
        #     file_name, _ = QFileDialog.getOpenFileName(self, "開啟檔案", "", "Excel 檔案 (*.xlsx);; 所有檔案 (*)")
        #     if file_name:
        #         saved_file = generate_lookup(self.config, file_name)
        #         os.startfile(saved_file)
        # except Exception as e:
        #     self.uiCommons.show_error_dialog(e)
        #     logger.error(e)
        self.vLookUpDialog.exec()

    def member_difference_comparing(self):
        try:
            filename, headers, warnings = generate_member_comparison_table(self.configHolder.get_config())

            if filename is None:
                self.uiCommons.done()
                self.uiCommons.show_message_dialog('檢查學員資料差異', '太好了, Google 雲端跟個資的學員資料是一致的')
            else:
                if len(warnings) > 0:
                    logger.trace(warnings)
                    button = self.uiCommons.create_a_button(f'開啟差異檔 (Excel 格式)')
                    button.clicked.connect(lambda: os.startfile(filename))
                    dialog = ProcessingDoneDialog(
                        self.configHolder, 'Google 雲端 vs 個資學員資料',
                        headers, warnings, [[button]])
                    dialog.exec()
                else:
                    os.startfile(filename)
        except Exception as e:
            self.uiCommons.show_error_dialog(e)
            logger.error(e)

    def open_toolbox(self):
        # self.setCentralWidget(self.uiCommons.create_a_button("button"))
        self.toolboxDialog.exec()

    def open_checkin_system(self):
        self.checkinSystemDialog.exec()

    def open_pilgrimage_dialog(self):
        self.pilgrimageDialog.exec()

    def meditation_activity_survey(self):
        try:
            activity_survey(self.configHolder.get_config())
        except Exception as e:
            self.uiCommons.show_error_dialog(e)

    def change_to_full_layout(self):
        try:
            self.pzCentralLayout = QVBoxLayout()
            self.create_full_function_buttons()
            self.pzCentralWidget = QWidget(self)
            self.pzCentralWidget.setLayout(self.pzCentralLayout)
            self.setCentralWidget(self.pzCentralWidget)
        except Exception as e:
            self.uiCommons.show_error_dialog(e)

    def change_to_simple_layout(self):
        try:
            self.pzCentralLayout = QVBoxLayout()
            self.create_simple_function_buttons()
            self.pzCentralWidget = QWidget(self)
            self.pzCentralWidget.setLayout(self.pzCentralLayout)
            self.setCentralWidget(self.pzCentralWidget)
        except Exception as e:
            self.uiCommons.show_error_dialog(e)

    # def open_output_folder(self):
    #     os.startfile(self.configHolder.get_config().output_folder)

    def close_progress_bar(self):
        self.progressBar.close()
        self.progressBar = None
        self.open_output_folder()

    def show_qrcode_template(self):
        os.startfile(self.configHolder.get_config().qrcode.template_file)

    def generate_qrcode(self):
        try:
            file_name, _ = QFileDialog.getOpenFileName(self, "開啟檔案", "", "Excel 檔案 (*.xlsx);; 所有檔案 (*)")
            if file_name:
                svc = QRCodeGeneratrUiService(self.configHolder.get_config(), file_name)

                self.progressBar = QProgressDialog("QR Code 產生中", None, 0, 0)
                self.progressBar.setWindowTitle("產生 QR Code")
                self.progressBar.setFont(self.uiCommons.font16)
                self.progressBar.setWindowModality(Qt.WindowModality.ApplicationModal)
                self.progressBar.show()

                self.generalUiWorker = GeneralUiWorker(svc, self.progressBar)
                self.generalUiWorker.finished.connect(self.close_progress_bar)
                self.generalUiWorker.start()
                # generate_qrcode(self.configHolder.get_config(), file_name)
        except Exception as e:
            self.uiCommons.show_error_dialog(e)
            logger.error(e)

    def create_simple_function_buttons(self):
        buttons_and_functions = [
            [
                ('🔎 姓名 V 班級/組別🔸', self.vlookup_by_name),
                (f'🔄 Google {self.configHolder.get_config().semester} 學員同步', self.google_to_mysql),
            ],
            [
                (f'📝 禪修活動調查', self.meditation_activity_survey),
                ('📁 禪修活動資料夾', self.open_activity_survey_folder),
            ],
            [
                (f'💳 福慧卡製作', self.generate_qrcode),
                (f'🎨 福慧卡樣版', self.show_qrcode_template),
            ],
            [
                ('🔼 切換成完整版', self.change_to_full_layout),
                ('📁 程式輸出', self.open_output_folder),
            ],
        ]
        self.pzCentralLayout.addLayout(style101_button_creation(self.uiCommons, buttons_and_functions))

    def create_full_function_buttons(self):
        buttons_and_functions = [
            [
                ('📝 禪修班結業統計', self.run_generate_graduation_reports),
                ('📁 上課記錄', self.open_graduation_folder),
                ('🐞 檢查學員資料差異', self.member_difference_comparing),
            ],
            [
                ('📝 介紹人電聯表', self.run_introducer_report),
                ('📁 意願調查', self.open_questionnaire_folder),
                ('🔎 姓名 V 班級/組別🔸', self.vlookup_by_name),
            ],
            [
                ('📝 學長電聯表(產生 A 表)🔸', self.run_senior_report_from_scratch),
                ('📁 學長電聯', self.open_senior_folder),
                ('🚎 回山排車相關作業🔸', self.open_pilgrimage_dialog),
            ],
            # [('[產出] 學長電聯表(讀 B 表)', self.run_senior_report), ('自動分班演算法說明', self.show_dispatch_doc)],
            [
                ('📝 學長電聯表(讀 B 表)', self.run_senior_report),
                (f'🔄 Google {self.configHolder.get_config().semester} 學員同步', self.google_to_mysql),
                ('🔄 學員基本資料 匯入🔸', self.member_info_import),
            ],
            [
                ('🔙 切換成簡易版', self.change_to_simple_layout),
                ('📁 輸出樣版', self.open_template_folder),
                ('🔄 學員基本資料 匯出', self.member_info_export),
            ],
            [
                ('💾 MS Access 資料庫🔸', self.handle_ms_access),
                # FIXME
                # (f'🔄 Google 親眷朋友關係同步', self.google_relations_to_mysql),
                ('🌀 報到系統輔助🔸', self.open_checkin_system),
                ('🚀 雲端上傳同步🔸', self.handle_cloud_upload),
                # ('🌀 報到系統輔助🔸', self.open_checkin_system),
            ],
            [
                ('📖 開啟程式設定檔', self.open_settings_in_notepad),
                ('📤 重新載入程式設定檔', self.re_read_settings),
                ('🔧設計師的工具小品🔸', self.open_toolbox),
            ]
            # [('開課前電聯表', self.do_nothing), ],
            # [('關懷表', self.do_nothing), ],
        ]

        # for row, keys in enumerate(keyBoard):
        #     for col, k in enumerate(keys):
        #         key = k[0]
        #         func = k[1]
        #         self.buttonMap[key] = QPushButton(key)
        #         self.buttonMap[key].setFixedSize(280, 55)
        #         self.buttonMap[key].setFont(self.uiCommons.font14)
        #         if func is not None:
        #             # print(key)
        #             self.buttonMap[key].clicked.connect(partial(func))
        #         buttonsLayout.addWidget(self.buttonMap[key], row, col)

        self.pzCentralLayout.addLayout(style101_button_creation(self.uiCommons, buttons_and_functions))

        # output_folder_button = QPushButton('輸出樣版資料夾')
        # output_folder_button.setFixedSize(500, 60)
        # output_folder_button.setFont(font)
        # # print(self.config.template_folder)
        # output_folder_button.clicked.connect(partial(explorer_folder, self.config.template_folder))
        # self.generalLayout.addWidget(output_folder_button)

        output_button_layout = QGridLayout()
        output_folder_button = QPushButton('📁 程式輸出')
        output_folder_button.setFixedSize(500, 60)
        output_folder_button.setFont(self.uiCommons.font14)
        output_folder_button.clicked.connect(self.open_output_folder)
        output_button_layout.addWidget(output_folder_button)
        self.pzCentralLayout.addLayout(output_button_layout)

        # members = ['法世', '法和', '法華', '法喜', '傳洵', '傳資']
        #
        # announce = QLabel(
        #     f'版權說明：本程式於 2024 年由普中精舍見聲法師帶領資料組{"、".join(members)} (按法名筆畫次序) 共同規劃需求；程式開發：劍青。')
        #
        # announce.setFont(self.uiCommons.font10)
        # announce.setAlignment(Qt.AlignmentFlag.AlignLeft)
        # announce.setWordWrap(True)
        # announce.setStyleSheet("color: brown;")
        # self.pzCentralLayout.addWidget(announce)
