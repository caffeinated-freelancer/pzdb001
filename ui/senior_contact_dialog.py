import os
from functools import partial

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel

from pz.config import PzProjectConfig
from ui.ui_commons import PzUiCommons


class SeniorContactDialog(QDialog):
    config: PzProjectConfig
    uiCommons: PzUiCommons

    def __init__(self, cfg: PzProjectConfig):
        self.config = cfg
        self.uiCommons = PzUiCommons(self, self.config)
        super().__init__()
        self.setWindowTitle(f'[產出] 學長電聯表(自動分班)')

        self.resize(400, 250)

        # Create layout and widgets
        layout = QVBoxLayout()
        self.setLayout(layout)

        button_sync = QPushButton(f'Google 下載 {self.config.semester} 學員資料')
        button_sync.setMinimumHeight(300)
        button_sync.setMinimumHeight(60)
        button_sync.setFont(self.uiCommons.font14)
        button_sync.clicked.connect(partial(self.google_to_mysql))

        button1 = QPushButton('讀取 Google 上的升班調查')
        button1.setMinimumHeight(300)
        button1.setMinimumHeight(60)
        button1.setFont(self.uiCommons.font14)
        button1.clicked.connect(partial(self.run_senior_report_from_google))

        file_name = os.path.basename(cfg.excel.signup_next_info.spreadsheet_file)
        label = QLabel(f'Excel 檔: {file_name}')
        label.setFont(self.uiCommons.font10)

        button2 = QPushButton(f'讀取升班調查 Excel 檔')
        button2.setMinimumHeight(300)
        button2.setMinimumHeight(60)
        button2.setFont(self.uiCommons.font14)
        button2.clicked.connect(partial(self.run_senior_report_from_excel))

        close_button = QPushButton("關閉")
        close_button.setFont(self.uiCommons.font10)
        close_button.setMinimumHeight(300)
        close_button.setMinimumHeight(60)

        layout.addWidget(button_sync)
        layout.addWidget(button1)
        layout.addWidget(button2)
        layout.addWidget(label)
        layout.addWidget(close_button)

        close_button.clicked.connect(self.close)

    # def run_senior_report_from_scratch(self, from_excel: bool):
    #     try:
    #         self.config.make_sure_output_folder_exists()
    #         self.config.explorer_output_folder()
    #         generate_senior_reports(self.config, True, from_excel=from_excel)
    #     except Exception as e:
    #         self.uiCommons.show_error_dialog(e)
    #         logger.error(e)
    #     finally:
    #         self.close()
    #
    def google_to_mysql(self):
        self.uiCommons.google_to_mysql()
    #     try:
    #         write_google_to_mysql(self.config)
    #     except Exception as e:
    #         self.uiCommons.show_error_dialog(e)
    #         logger.error(e)

    def run_senior_report_from_google(self):
        self.uiCommons.run_senior_report_from_scratch(from_excel=False)

    def run_senior_report_from_excel(self):
        self.uiCommons.run_senior_report_from_scratch(from_excel=True)

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
