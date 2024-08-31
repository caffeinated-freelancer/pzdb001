import os
import time

from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import QDialog, QFileDialog, QProgressDialog
from loguru import logger

from pz.config import PzProjectConfig
from services.characterize_service import CharacterizeService
from services.file_transfer_service import FileTransferService
from ui.config_holder import ConfigHolder
from ui.ui_commons import PzUiCommons
from ui.ui_utils import style101_dialog_layout
from version import __pz_version__


# def receive_file_worker(rs232: Rs232Service, folder: str):
#     print("Starting thread...")
#     rs232.recv_file(folder)
#     print("Thread finished.")


class FileTransferWorker(QThread):
    finished = pyqtSignal()
    configHolder: ConfigHolder
    file_transfer_service: FileTransferService
    sending_file: str | None
    progress_bar: QProgressDialog

    def __init__(self, holder: ConfigHolder, service: FileTransferService, progress: QProgressDialog,
                 sending_file: str | None = None):
        super().__init__()
        self.configHolder = holder
        self.fileTransferService = service
        self.sending_file = sending_file
        self.progress_bar = progress

    def run(self):
        try:
            if self.sending_file is not None:
                self.fileTransferService.send_file(self.sending_file)
            else:
                self.fileTransferService.receive_file()

            time.sleep(2)
            prev_progress_value = -1

            while True:
                if self.fileTransferService.check_worker_thread_available():
                    break
                elif self.sending_file is not None:
                    progress_value = self.fileTransferService.get_progress()
                    if progress_value != prev_progress_value:
                        prev_progress_value = progress_value
                        self.progress_bar.setValue(self.fileTransferService.get_progress())
                time.sleep(0.5)
        except Exception as e:
            logger.error(e)
        finally:
            logger.info("file transfer finished")
            self.fileTransferService.close()
            self.finished.emit()


class ToolboxDialog(QDialog):
    configHolder: ConfigHolder
    uiCommons: PzUiCommons
    fileTransferService: FileTransferService | None
    progressBar: QProgressDialog | None

    def __init__(self, holder: ConfigHolder):
        self.configHolder = holder
        self.uiCommons = PzUiCommons(self, holder)
        self.fileTransferService = FileTransferService(self.configHolder)
        self.progressBar = None
        super().__init__()
        self.setWindowTitle(f'設計師的工具小品 v{__pz_version__}')

        buttons_and_functions = [
            [
                ('📳 行動電話編碼 🔒', self.encode_excel_file_mobile),
                ('📳 行動電話解碼 🔓', self.decode_excel_file_mobile),
            ],
            [
                ('☎ 住家電話編碼 🔒', self.encode_excel_file_home),
                ('☎ 住家電話解碼 🔓', self.decode_excel_file_home),
            ],
        ]

        enable_file_transfer = FileTransferService.check_com_port()

        if enable_file_transfer:
            buttons_and_functions.insert(0, [
                ('📨 檔案傳送', self.send_file),
                ('🎁 檔案接收', self.receive_file),
            ])

        self.resize(550, 400)

        layout = style101_dialog_layout(self, self.uiCommons, buttons_and_functions)
        self.setLayout(layout)

        # Connect button click to slot (method)

    def receive_file(self):
        # logger.info('receive_file')
        #
        # if self.fileTransferService.check_worker_thread_available():
        #     self.fileTransferService.receive_file()
        #     self.uiCommons.show_message_dialog('接收檔案', f'進入檔案接收模式, 請稍待')
        # else:
        #     self.uiCommons.show_message_dialog('接收檔案', f'有另一個檔案傳送接收的工作還在進行中, 請稍待')

        if self.fileTransferService.check_worker_thread_available():
            try:
                self.progressBar = QProgressDialog("檔案接收中", None, 0, 0)
                self.progressBar.setWindowTitle("接收檔案")
                self.progressBar.setFont(self.uiCommons.font16)
                self.progressBar.setWindowModality(Qt.WindowModality.NonModal)
                self.progressBar.show()

                self.worker = FileTransferWorker(self.configHolder.get_config(), self.fileTransferService, self.progressBar)
                self.worker.finished.connect(self.task_finished)
                self.worker.start()
                self.close()

                # self.fileTransferService.send_file(file_name)
                # self.uiCommons.show_message_dialog('傳送檔案', f'正在進入檔案傳送, 請稍待')
            except Exception as e:
                self.uiCommons.show_error_dialog(e)
                logger.exception(e)
        else:
            self.uiCommons.show_message_dialog('傳送檔案', f'有另一個檔案傳送接收的工作還在進行中, 請稍待')

    def send_file(self):
        if self.fileTransferService.check_worker_thread_available():
            try:
                file_name, _ = QFileDialog.getOpenFileName(self, "開啟檔案", "", "所有檔案 (*)")
                if file_name:
                    self.progressBar = QProgressDialog("檔案傳送中", None, 0, 100)
                    self.progressBar.setWindowModality(Qt.WindowModality.NonModal)
                    self.progressBar.setWindowTitle("傳送檔案")
                    self.progressBar.setFont(self.uiCommons.font16)
                    self.progressBar.show()

                    self.worker = FileTransferWorker(self.configHolder.get_config(), self.fileTransferService, self.progressBar,
                                                     sending_file=file_name)
                    self.worker.finished.connect(self.task_finished)
                    self.worker.start()
                    self.close()

                    # self.fileTransferService.send_file(file_name)
                    # self.uiCommons.show_message_dialog('傳送檔案', f'正在進入檔案傳送, 請稍待')
            except Exception as e:
                self.uiCommons.show_error_dialog(e)
                logger.exception(e)
        else:
            self.uiCommons.show_message_dialog('傳送檔案', f'有另一個檔案傳送接收的工作還在進行中, 請稍待')

    def task_finished(self):
        self.progressBar.close()
        self.fileTransferService.close()

    def characterize_excel_file(self, title: str, decode: bool, home_phone: bool):
        try:
            file_name, _ = QFileDialog.getOpenFileName(self, title, "", "Excel 檔案 (*.xlsx)")
            if file_name:
                saved = CharacterizeService.processing_file(file_name, decode, home_phone, True)
                os.startfile(saved)
        except Exception as e:
            self.uiCommons.show_error_dialog(e)
            logger.exception(e)

    def encode_excel_file_mobile(self):
        self.characterize_excel_file("開啟檔案 (行動電話編碼)", False, False)

    def decode_excel_file_mobile(self):
        self.characterize_excel_file("開啟檔案 (行動電話解碼)", True, False)

    def encode_excel_file_home(self):
        self.characterize_excel_file("開啟檔案 (住家電話編碼)", False, True)

    def decode_excel_file_home(self):
        self.characterize_excel_file("開啟檔案 (住家電話解碼)", True, True)
