import os

from PyQt6.QtWidgets import QDialog, QLabel, QCheckBox
from loguru import logger

from pz.config import PzProjectConfig
from ui.dispatch_doc_dialog import DispatchDocDialog
from ui.senior_report_common import SeniorReportCommon
from ui.ui_commons import PzUiCommons
from ui.ui_utils import style101_dialog_layout


class SeniorContactDialog(QDialog):
    config: PzProjectConfig
    uiCommons: PzUiCommons
    dispatchDocDialog: DispatchDocDialog
    seniorReportCommon: SeniorReportCommon
    # fix_senior_checkbox_value: bool = False
    senior_checkbox: QCheckBox

    def __init__(self, cfg: PzProjectConfig):
        self.config = cfg
        self.uiCommons = PzUiCommons(self, self.config)
        super().__init__()

        self.dispatchDocDialog = DispatchDocDialog()
        self.seniorReportCommon = SeniorReportCommon(self, self.uiCommons, self.config)

        self.setWindowTitle(f'[產出] 學長電聯表(自動分班)')

        self.resize(400, 250)

        file_name = os.path.basename(cfg.excel.signup_next_info.spreadsheet_file)
        label = QLabel(f'Excel 檔: {file_name}')
        label.setFont(self.uiCommons.font10)
        self.senior_checkbox = QCheckBox("不要調整學長意願所屬班級 (可節省處理時間)")
        self.senior_checkbox.setFont(self.uiCommons.font10)
        self.senior_checkbox.setChecked(True)
        # senior_checkbox.stateChanged.connect(self.senior_checkbox_state_changed)
        # self.fix_senior_checkbox_value = senior_checkbox.isChecked()


        buttons_and_functions = [
            [(f'Google 下載 {self.config.semester} 學員資料', self.google_to_mysql)],
            [self.senior_checkbox],
            [('讀取 Google 上的升班調查', self.run_senior_report_from_google)],
            [('讀取升班調查 Excel 檔', self.run_senior_report_from_excel)],
            [label],
            [('自動分班演算法說明', self.show_dispatch_doc)],
        ]

        layout = style101_dialog_layout(self, self.uiCommons, buttons_and_functions,
                                        button_width=360, button_height=60)
        self.setLayout(layout)

    # def senior_checkbox_state_changed(self, state):
    #     # print(f'state: {state} {Qt.CheckState.Checked.value} {Qt.CheckState.Unchecked.value}')
    #     if state == Qt.CheckState.Checked.value:
    #         print("Checkbox is checked")
    #     else:
    #         print("Checkbox is unchecked")

    def show_dispatch_doc(self):
        # self.dispatchDocDialog.show()
        self.dispatchDocDialog.exec()

    #
    def google_to_mysql(self):
        self.uiCommons.google_to_mysql(check_formula=True)

    #     try:
    #         write_google_to_mysql(self.config)
    #     except Exception as e:
    #         self.uiCommons.show_error_dialog(e)
    #         logger.error(e)

    def run_senior_report_from_google(self):
        logger.info(f'{self.senior_checkbox.isChecked()}')
        self.seniorReportCommon.run_senior_report_from_scratch(
            True, from_excel=False, close_widget=True, no_fix_senior=self.senior_checkbox.isChecked())

    def run_senior_report_from_excel(self):
        self.seniorReportCommon.run_senior_report_from_scratch(
            True, from_excel=True, close_widget=True, no_fix_senior=self.senior_checkbox.isChecked())

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

    # if button_clicked == QMessageBox.StandardButton.Ok:
    #     print("User clicked OK!")
    # elif button_clicked == QMessageBox.StandardButton.Cancel:
    #     print("User clicked Cancel!")
