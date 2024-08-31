import traceback

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QWidget, QProgressDialog
from loguru import logger

from pz.config import PzProjectConfig
from pz.models.general_processing_error import GeneralProcessingError
from pz_functions.generaters.senior import generate_senior_reports
from ui.config_holder import ConfigHolder
from ui.processing_done_dialog import ProcessingDoneDialog
from ui.ui_commons import PzUiCommons


class Worker(QThread):
    finished = pyqtSignal()
    config: PzProjectConfig
    from_scratch: bool
    from_excel: bool
    no_fix_senior: bool
    errors: list[GeneralProcessingError]
    exception: Exception | None
    with_table_b: bool
    with_questionnaire: bool
    with_willingness: bool

    def __init__(self, config: PzProjectConfig, from_scratch: bool, from_excel: bool, no_fix_senior: bool,
                 with_table_b: bool,
                 with_questionnaire: bool = True,
                 with_willingness: bool = True):
        super().__init__()
        self.config = config
        self.from_scratch = from_scratch
        self.from_excel = from_excel
        self.no_fix_senior = no_fix_senior
        self.with_table_b = with_table_b
        self.with_questionnaire = with_questionnaire
        self.with_willingness = with_willingness
        self.errors = []
        self.exception = None

    def run(self):
        try:
            self.errors = generate_senior_reports(
                self.config, self.from_scratch, from_excel=self.from_excel,
                no_fix_senior=self.no_fix_senior, with_table_b=self.with_table_b,
                with_questionnaire=self.with_questionnaire, with_willingness=self.with_willingness)
        except Exception as e:
            self.exception = e
            logger.error(e)
            stack_trace = traceback.format_exc()  # Get stack trace as string
            print(f"Exception occurred: {str(e)}")
            print(f"Stack Trace:\n{stack_trace}")
        finally:
            self.finished.emit()


class SeniorReportCommon:
    configHolder: ConfigHolder
    widget: QWidget
    uiCommons: PzUiCommons
    progress_dialog: QProgressDialog | None
    worker: Worker | None

    def __init__(self, widget: QWidget, ui_commons: PzUiCommons, holder: ConfigHolder) -> None:
        self.widget = widget
        self.uiCommons = ui_commons
        self.configHolder = holder
        self.progress_dialog = None
        self.worker = None

    def run_senior_report_from_scratch(self, from_scratch: bool, from_excel: bool,
                                       close_widget: bool = False,
                                       no_fix_senior: bool = False,
                                       with_table_b: bool = False,
                                       with_questionnaire: bool = True,
                                       with_willingness: bool = True) -> None:
        try:
            self.configHolder.get_config().make_sure_output_folder_exists()

            self.progress_dialog = QProgressDialog("編班及產生學長電聯表中, 請稍候", None, 0, 0)
            self.progress_dialog.setWindowTitle('產出學長電聯表及 A 表')
            self.progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
            self.progress_dialog.setFont(self.uiCommons.font16)
            # layout = QHBoxLayout()
            # layout.addWidget(self.progress_dialog)
            # layout.setStretchFactor(self.progress_dialog, 1)  # Make progress bar fill available space
            self.progress_dialog.show()

            self.worker = Worker(self.configHolder.get_config(), from_scratch, from_excel, no_fix_senior, with_table_b,
                                 with_questionnaire=with_questionnaire, with_willingness=with_willingness)
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
                logger.debug("close widget")
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
                try:
                    logger.warning(f'{len(errors)} errors occurred')
                    button = PzUiCommons.create_a_button(f'開啟程式產出資料夾')
                    button.clicked.connect(lambda: self.configHolder.get_config().explorer_output_folder())
                    dialog = ProcessingDoneDialog(
                        self.configHolder, '完成學長電聯表產出', ['等級', '警告訊息'], [
                            [x.level_name(), x.message] for x in errors
                        ], [[button]])
                    dialog.exec()
                except Exception as e:
                    stack_trace = traceback.format_exc()  # Get stack trace as string
                    print(f"Exception occurred: {str(e)}")
                    print(f"Stack Trace:\n{stack_trace}")

            else:
                self.configHolder.get_config().explorer_output_folder()
