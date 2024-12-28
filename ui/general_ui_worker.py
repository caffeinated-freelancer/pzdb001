from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QProgressDialog
from loguru import logger

from ui.config_holder import ConfigHolder
from ui.general_ui_service import GeneralUiService


class GeneralUiWorker(QThread):
    finished = pyqtSignal()
    progress_bar: QProgressDialog
    service: GeneralUiService

    def __init__(self, service: GeneralUiService, progress: QProgressDialog):
        super().__init__()
        self.service = service
        self.progress_bar = progress

    def run(self):
        try:
            logger.info("General UI worker started")
            self.service.perform_service()
            self.progress_bar.setValue(100)
            logger.info("General UI worker done")
        except Exception as e:
            logger.error(e)
        finally:
            self.service.done()
            self.finished.emit()
