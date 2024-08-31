import os

from PyQt6.QtWidgets import QDialog, QLabel, QCheckBox, QComboBox

from ui.config_holder import ConfigHolder
from ui.dispatch_doc_dialog import DispatchDocDialog
from ui.senior_report_common import SeniorReportCommon
from ui.ui_commons import PzUiCommons
from ui.ui_utils import style101_dialog_layout


class SeniorContactDialog(QDialog):
    configHolder: ConfigHolder
    uiCommons: PzUiCommons
    dispatchDocDialog: DispatchDocDialog
    seniorReportCommon: SeniorReportCommon
    # fix_senior_checkbox_value: bool = False
    senior_checkbox: QCheckBox
    with_b_checkbox: QCheckBox
    with_q_checkbox: QCheckBox
    with_w_checkbox: QCheckBox
    willingness_combo: QComboBox

    def __init__(self, holder: ConfigHolder):
        self.configHolder = holder
        self.uiCommons = PzUiCommons(self, holder)
        super().__init__()

        self.dispatchDocDialog = DispatchDocDialog()
        self.seniorReportCommon = SeniorReportCommon(self, self.uiCommons, holder)

        self.setWindowTitle(f'[產出] 學長電聯表(自動分班)')

        self.resize(440, 250)

        file_name = os.path.basename(self.configHolder.get_config().excel.signup_next_info.spreadsheet_file)
        label = QLabel(f'Excel 檔: {file_name}')
        label.setFont(self.uiCommons.font10)
        self.senior_checkbox = QCheckBox("不要調整學長意願所屬班級 (可節省處理時間)")
        self.senior_checkbox.setFont(self.uiCommons.font12)
        self.senior_checkbox.setChecked(False)
        self.with_b_checkbox = QCheckBox("產出 A 表時, 參考 B 表")
        self.with_b_checkbox.setFont(self.uiCommons.font12)
        self.with_b_checkbox.setChecked(False)
        self.with_q_checkbox = QCheckBox("讀取意願調查表 （若不讀取意願調查表，新生部份資料將欠缺）")
        self.with_q_checkbox.setFont(self.uiCommons.font12)
        self.with_q_checkbox.setChecked(True)

        self.willingness_combo = QComboBox()
        self.willingness_combo.addItem("🚫 不要讀取升班調查表")
        self.willingness_combo.addItem("☁ 讀取 Google 升班調查表")
        self.willingness_combo.addItem("📊 讀取 Excel 升班調查表")
        self.willingness_combo.setCurrentIndex(1)
        self.willingness_combo.setFont(self.uiCommons.font12)
        self.willingness_combo.setFixedHeight(40)

        # self.with_w_checkbox = QCheckBox("讀取 Google 升班調查表")
        # self.with_w_checkbox.setFont(self.uiCommons.font12)
        # self.with_w_checkbox.setChecked(True)
        # self.with_w_checkbox = QCheckBox("讀取 Excel 升班調查表")
        # self.with_w_checkbox.setFont(self.uiCommons.font12)
        # self.with_w_checkbox.setChecked(True)

        # QRadioButton(self.with_wg_checkbox).setChecked(True)
        # QRadioButton(self.with_wg_checkbox).setChecked(True)
        # senior_checkbox.stateChanged.connect(self.senior_checkbox_state_changed)
        # self.fix_senior_checkbox_value = senior_checkbox.isChecked()

        buttons_and_functions = [
            [(f'Google {self.configHolder.get_config().semester} 學員同步', self.google_to_mysql)],
            [self.senior_checkbox],
            [self.with_b_checkbox],
            [self.with_q_checkbox],
            [self.willingness_combo],
            # [self.with_w_checkbox],
            [('進行 A 表及電聯表產生', self.run_senior_report)],
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

    # def run_senior_report_from_google(self):
    #     self.seniorReportCommon.run_senior_report_from_scratch(
    #         True, from_excel=False, close_widget=True,
    #         no_fix_senior=self.senior_checkbox.isChecked(),
    #         with_table_b=self.with_b_checkbox.isChecked(),
    #         with_questionnaire=self.with_q_checkbox.isChecked(),
    #         with_willingness=self.with_w_checkbox.isChecked())

    def run_senior_report(self):
        current_index = self.willingness_combo.currentIndex()

        if current_index == 1:
            willingness = True
            from_excel = False
        elif current_index == 2:
            willingness = True
            from_excel = True
        else:
            willingness = False
            from_excel = False

        self.seniorReportCommon.run_senior_report_from_scratch(
            True, from_excel=from_excel, close_widget=True,
            no_fix_senior=self.senior_checkbox.isChecked(),
            with_table_b=self.with_b_checkbox.isChecked(),
            with_questionnaire=self.with_q_checkbox.isChecked(),
            with_willingness=willingness)

    # def run_senior_report_from_excel(self):
    #     self.seniorReportCommon.run_senior_report_from_scratch(
    #         True, from_excel=True, close_widget=True,
    #         no_fix_senior=self.senior_checkbox.isChecked(),
    #         with_table_b=self.with_b_checkbox.isChecked(),
    #         with_questionnaire=self.with_q_checkbox.isChecked(),
    #         with_willingness=self.with_w_checkbox.isChecked())

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
