import traceback

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QMessageBox, QWidget
from loguru import logger

from pz.config import PzProjectConfig
from pz_functions.generaters.senior import generate_senior_reports
from pz_functions.importers.mysql_functions import write_google_to_mysql


class PzUiCommons:
    widget: QWidget
    config: PzProjectConfig
    font10: QFont
    font14: QFont

    def __init__(self, widget: QWidget, cfg: PzProjectConfig) -> None:
        self.widget = widget
        self.config = cfg

        self.font14 = QFont('Microsoft YaHei', 14)
        self.font10 = QFont('Microsoft YaHei', 10)

    def show_error_dialog(self, e: Exception):
        message_box = QMessageBox(self.widget)  # Set parent for proper positioning

        # Set message box options (type, text, buttons)
        message_box.setIcon(QMessageBox.Icon.Information)  # Optional: Set icon
        message_box.setWindowTitle("糟糕")

        message_box.setFont(self.font14)
        message_box.setText(str(e))
        stack_trace = traceback.format_exc()  # Get stack trace as string
        print(f"Exception occurred: {str(e)}")
        print(f"Stack Trace:\n{stack_trace}")

        message_box.setStandardButtons(QMessageBox.StandardButton.Ok)

        # Show the dialog and get the user's choice (optional)
        self.widget.show()
        self.widget.raise_()
        self.widget.activateWindow()
        message_box.show()

    def show_message_dialog(self, title: str, message: str):
        message_box = QMessageBox(self.widget)  # Set parent for proper positioning

        # Set message box options (type, text, buttons)
        message_box.setIcon(QMessageBox.Icon.Information)  # Optional: Set icon
        message_box.setWindowTitle(title)

        message_box.setFont(self.font14)
        message_box.setText(message)

        message_box.setStandardButtons(QMessageBox.StandardButton.Ok)

        # Show the dialog and get the user's choice (optional)
        self.widget.show()
        self.widget.raise_()
        self.widget.activateWindow()
        message_box.show()

    def run_senior_report_from_scratch(self, from_excel: bool):
        try:
            self.config.make_sure_output_folder_exists()
            self.config.explorer_output_folder()
            generate_senior_reports(self.config, True, from_excel=from_excel)
            self.done()
        except Exception as e:
            self.show_error_dialog(e)
            logger.error(e)
        finally:
            self.widget.close()

    def google_to_mysql(self, check_formula: bool = False):
        try:
            records = write_google_to_mysql(self.config, check_formula=check_formula)
            self.done()
            self.show_message_dialog('Google 匯出', f'{records} 筆資料由 Google 的班級及升班資料匯到資料庫')
        except Exception as e:
            self.show_error_dialog(e)
            logger.error(e)

    @staticmethod
    def done():
        logger.info(f'##### 完成 #####')
