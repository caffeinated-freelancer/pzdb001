import os
import subprocess
from functools import partial

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QPushButton, QVBoxLayout, QGridLayout, QLabel, )
from loguru import logger

from pz.config import PzProjectConfig
from pz.utils import explorer_folder
from pz_functions.generaters.graduation import generate_graduation_reports
from pz_functions.generaters.introducer import generate_introducer_reports
from pz_functions.generaters.senior import generate_senior_reports
from pz_functions.importers.mysql_functions import write_access_to_mysql
from ui.dispatch_doc_dialog import DispatchDocDialog
from ui.senior_contact_dialog import SeniorContactDialog
from ui.ui_commons import PzUiCommons
from version import __version__

WINDOW_SIZE = 235
DISPLAY_HEIGHT = 35
BUTTON_SIZE = 120


class PyPzWindows(QMainWindow):
    config: PzProjectConfig
    dispatchDocDialog: DispatchDocDialog
    seniorContactDialog: SeniorContactDialog
    default_font: QFont
    uiCommons: PzUiCommons

    def __init__(self, cfg: PzProjectConfig):
        super().__init__()
        self.config = cfg
        self.uiCommons = PzUiCommons(self, self.config)
        self.setWindowTitle(f'普中資料管理程式 v{__version__}')
        self.default_font = QFont('Microsoft YaHei', 14)
        self.setFixedSize(620, 500)
        self.generalLayout = QVBoxLayout()

        centralWidget = QWidget(self)
        centralWidget.setLayout(self.generalLayout)
        self.setCentralWidget(centralWidget)
        self._createButtons()
        self.dispatchDocDialog = DispatchDocDialog()
        self.seniorContactDialog = SeniorContactDialog(cfg)
        self.show()
        self.activateWindow()

        # layout = QHBoxLayout()
        # #
        # button = QPushButton("產生結業報表")
        # button.clicked.connect(partial(generate_graduation_reports, cfg))
        #
        # layout.addWidget(button)
        # layout.addWidget(QPushButton("Center"))
        # layout.addWidget(QPushButton("Right"))
        # window.setLayout(layout)

    def do_nothing(self):
        os.startfile(self.config.output_folder)

    def open_folder(self):
        os.startfile(self.config.output_folder)

    def run_generate_graduation_reports(self):
        try:
            generate_graduation_reports(self.config)
            # os.startfile(self.config.output_folder)
        except Exception as e:
            self.uiCommons.show_error_dialog(e)

    def run_introducer_report(self):
        try:
            self.config.make_sure_output_folder_exists()
            self.config.explorer_output_folder()
            generate_introducer_reports(self.config)
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
        # try:
        #     self.config.make_sure_output_folder_exists()
        #     self.config.explorer_output_folder()
        #     generate_senior_reports(self.config, True)
        # except Exception as e:
        #     self.show_error_dialog(e)
        #     logger.error(e)
        self.seniorContactDialog.exec()

    def run_senior_report(self):
        try:
            self.config.make_sure_output_folder_exists()
            self.config.explorer_output_folder()
            generate_senior_reports(self.config, False)
        except Exception as e:
            self.uiCommons.show_error_dialog(e)
            logger.error(e)

    def show_dispatch_doc(self):
        # self.dispatchDocDialog.show()
        self.dispatchDocDialog.exec()

    def open_graduation_folder(self):
        explorer_folder(self.config.excel.graduation.records.spreadsheet_folder)

    def open_questionnaire_folder(self):
        explorer_folder(self.config.excel.questionnaire.spreadsheet_folder)

    def open_senior_folder(self):
        explorer_folder(os.path.dirname(self.config.excel.new_class_senior.spreadsheet_file))

    def open_template_folder(self):
        explorer_folder(self.config.template_folder)

    def open_output_folder(self):
        self.config.make_sure_output_folder_exists()
        explorer_folder(self.config.output_folder)

    def access_to_mysql(self):
        try:
            write_access_to_mysql(self.config)
        except Exception as e:
            self.uiCommons.show_error_dialog(e)
            logger.error(e)

    def google_to_mysql(self):
        self.uiCommons.google_to_mysql()
        # try:
        #     write_google_to_mysql(self.config)
        # except Exception as e:
        #     self.uiCommons.show_error_dialog(e)
        #     logger.error(e)

    def open_settings_in_notepad(self):
        # Open the file content (might launch in browser on some systems)
        subprocess.run(["notepad.exe", self.config.config_filename])
        # with open(self.config.config_filename, 'r') as file:
        #     content = file.read()
        #     webbrowser.open('data:text/plain;charset=utf-8,' + content)

    def _createButtons(self):
        self.buttonMap = {}
        buttonsLayout = QGridLayout()
        keyBoard = [
            [('[產出] 禪修班結業統計', self.run_generate_graduation_reports),
             ('上課記錄 資料夾', self.open_graduation_folder)],
            [('[產出] 介紹人電聯表', self.run_introducer_report), ('意願調查 資料夾', self.open_questionnaire_folder)],
            [('[產出] 學長電聯表(產生 A 表)', self.run_senior_report_from_scratch),
             ('學長電聯 資料夾', self.open_senior_folder)],
            [('[產出] 學長電聯表(讀 B 表)', self.run_senior_report), ('自動分班演算法說明', self.show_dispatch_doc)],
            [('Access -> MySQL', self.access_to_mysql),
             (f'Google 下載 {self.config.semester} 學員資料', self.google_to_mysql)],
            [('開啟程式設定檔', self.open_settings_in_notepad), ('輸出樣版 資料夾', self.open_template_folder)]
            # [('開課前電聯表', self.do_nothing), ],
            # [('關懷表', self.do_nothing), ],
        ]

        for row, keys in enumerate(keyBoard):
            for col, k in enumerate(keys):
                key = k[0]
                func = k[1]
                self.buttonMap[key] = QPushButton(key)
                self.buttonMap[key].setFixedSize(300, 60)
                self.buttonMap[key].setFont(self.uiCommons.font14)
                if func is not None:
                    # print(key)
                    self.buttonMap[key].clicked.connect(partial(func))
                buttonsLayout.addWidget(self.buttonMap[key], row, col)

        self.generalLayout.addLayout(buttonsLayout)

        # output_folder_button = QPushButton('輸出樣版資料夾')
        # output_folder_button.setFixedSize(500, 60)
        # output_folder_button.setFont(font)
        # # print(self.config.template_folder)
        # output_folder_button.clicked.connect(partial(explorer_folder, self.config.template_folder))
        # self.generalLayout.addWidget(output_folder_button)

        output_button_layout = QGridLayout()
        output_folder_button = QPushButton('程式輸出資料夾')
        output_folder_button.setFixedSize(500, 60)
        output_folder_button.setFont(self.uiCommons.font14)
        output_folder_button.clicked.connect(self.open_output_folder)
        output_button_layout.addWidget(output_folder_button)
        self.generalLayout.addLayout(output_button_layout)

        members = ['法世', '法和', '法華', '傳洵', '傳資']

        announce = QLabel(
            f'版權說明：本程式於 2024 年由普中精舍見聲法師帶領資料組{"、".join(members)} (按法名筆畫次序) 共同規劃需求；程式開發：劍青。')

        announce.setFont(self.uiCommons.font10)
        announce.setAlignment(Qt.AlignmentFlag.AlignLeft)
        announce.setWordWrap(True)
        announce.setStyleSheet("color: brown;")
        self.generalLayout.addWidget(announce)
