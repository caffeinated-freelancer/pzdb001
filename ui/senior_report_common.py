import traceback

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QWidget, QProgressDialog
from loguru import logger

from pz.config import PzProjectConfig
from pz.models.senior_report_error_model import SeniorReportError
from pz_functions.generaters.senior import generate_senior_reports
from ui.processing_done_dialog import ProcessingDoneDialog
from ui.ui_commons import PzUiCommons


class Worker(QThread):
    finished = pyqtSignal()
    config: PzProjectConfig
    from_scratch: bool
    from_excel: bool
    no_fix_senior: bool
    errors: list[SeniorReportError]
    exception: Exception | None

    def __init__(self, config: PzProjectConfig, from_scratch: bool, from_excel: bool, no_fix_senior: bool,
                 with_table_b: bool):
        super().__init__()
        self.config = config
        self.from_scratch = from_scratch
        self.from_excel = from_excel
        self.no_fix_senior = no_fix_senior
        self.with_table_b = with_table_b
        self.errors = []
        self.exception = None

    def run(self):
        try:
            self.errors = generate_senior_reports(
                self.config, self.from_scratch, from_excel=self.from_excel,
                no_fix_senior=self.no_fix_senior, with_table_b=self.with_table_b)
        except Exception as e:
            self.exception = e
            logger.error(e)
            stack_trace = traceback.format_exc()  # Get stack trace as string
            print(f"Exception occurred: {str(e)}")
            print(f"Stack Trace:\n{stack_trace}")
        finally:
            self.finished.emit()


class SeniorReportCommon:
    widget: QWidget
    config: PzProjectConfig
    uiCommons: PzUiCommons
    progress_dialog: QProgressDialog | None
    worker: Worker | None

    def __init__(self, widget: QWidget, ui_commons: PzUiCommons, cfg: PzProjectConfig) -> None:
        self.widget = widget
        self.uiCommons = ui_commons
        self.config = cfg
        self.progress_dialog = None
        self.worker = None

    def run_senior_report_from_scratch(self, from_scratch: bool, from_excel: bool,
                                       close_widget: bool = False,
                                       no_fix_senior: bool = False,
                                       with_table_b: bool = False) -> None:
        try:
            self.config.make_sure_output_folder_exists()

            self.progress_dialog = QProgressDialog("編班及產生學長電聯表中, 請稍候", None, 0, 0)
            self.progress_dialog.setWindowTitle('產出學長電聯表及 A 表')
            self.progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
            self.progress_dialog.setFont(self.uiCommons.font16)
            # layout = QHBoxLayout()
            # layout.addWidget(self.progress_dialog)
            # layout.setStretchFactor(self.progress_dialog, 1)  # Make progress bar fill available space
            self.progress_dialog.show()

            self.worker = Worker(self.config, from_scratch, from_excel, no_fix_senior, with_table_b)
            self.worker.finished.connect(self.task_finished)
            self.worker.start()

            # errors = generate_senior_reports(self.config, from_scratch, from_excel=from_excel)
            # self.uiCommons.done()
            #
            # if len(errors) > 0:
            #     logger.warning(f'{len(errors)} errors occurred')
            #     button = PzUiCommons.create_a_button(f'開啟程式產出資料夾')
            #     button.clicked.connect(lambda: self.config.explorer_output_folder())
            #     dialog = ProcessingDoneDialog(
            #         self.config, '完成學長電聯表產出', ['等級', '警告訊息'], [
            #             [x.level_name(), x.message] for x in errors
            #         ], [[button]])
            #     dialog.exec()
            # else:
            #     self.config.explorer_output_folder()

        except Exception as e:
            self.uiCommons.show_error_dialog(e)
            logger.error(e)
        finally:
            if close_widget:
                self.widget.close()

    def task_finished(self):
        self.uiCommons.done()

        self.progress_dialog.setValue(100)
        self.progress_dialog.close()

        if self.worker.exception is not None:
            self.uiCommons.show_error_dialog(self.worker.exception)
        else:
            errors = self.worker.errors

            # self.widget.killTimer(self.widget.progress_timer)
            # logger.warning(f'{len(errors)} errors occurred')

            if len(errors) > 0:
                logger.warning(f'{len(errors)} errors occurred')
                button = PzUiCommons.create_a_button(f'開啟程式產出資料夾')
                button.clicked.connect(lambda: self.config.explorer_output_folder())
                dialog = ProcessingDoneDialog(
                    self.config, '完成學長電聯表產出', ['等級', '警告訊息'], [
                        [x.level_name(), x.message] for x in errors
                    ], [[button]])
                dialog.exec()
            else:
                self.config.explorer_output_folder()
