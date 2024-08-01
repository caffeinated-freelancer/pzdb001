import os

from PyQt6.QtWidgets import QDialog, QFileDialog
from loguru import logger

from pz.config import PzProjectConfig
from services.characterize_service import CharacterizeService
from services.file_transfer_service import FileTransferService
from ui.ui_commons import PzUiCommons
from ui.ui_utils import style101_dialog_layout
from version import __pz_version__


# def receive_file_worker(rs232: Rs232Service, folder: str):
#     print("Starting thread...")
#     rs232.recv_file(folder)
#     print("Thread finished.")


class ToolboxDialog(QDialog):
    config: PzProjectConfig
    uiCommons: PzUiCommons
    fileTransferService: FileTransferService

    def __init__(self, cfg: PzProjectConfig):
        self.config = cfg
        self.uiCommons = PzUiCommons(self, self.config)
        self.fileTransferService = FileTransferService(self.config)
        super().__init__()
        self.setWindowTitle(f'設計師的工具小品 v{__pz_version__}')

        buttons_and_functions = [
            [
                ('檔案欄位編碼', self.encode_excel_file),
                ('檔案欄位解碼', self.decode_excel_file),
            ],
        ]

        enable_file_transfer = FileTransferService.check_com_port()

        if enable_file_transfer:
            buttons_and_functions.insert(0, [
                ('檔案傳送', self.send_file),
                ('檔案接收', self.receive_file),
            ])

        self.resize(550, 400)

        layout = style101_dialog_layout(self, self.uiCommons, buttons_and_functions)
        self.setLayout(layout)

        # Connect button click to slot (method)

    def receive_file(self):
        logger.info('receive_file')

        if self.fileTransferService.check_worker_thread_available():
            self.fileTransferService.receive_file()
            self.uiCommons.show_message_dialog('接收檔案', f'進入檔案接收模式, 請稍待')
        else:
            self.uiCommons.show_message_dialog('接收檔案', f'有另一個檔案傳送接收的工作還在進行中, 請稍待')

    def send_file(self):
        if self.fileTransferService.check_worker_thread_available():
            try:
                file_name, _ = QFileDialog.getOpenFileName(self, "開啟檔案", "", "所有檔案 (*)")
                if file_name:
                    self.fileTransferService.send_file(file_name)
                    self.uiCommons.show_message_dialog('傳送檔案', f'正在進入檔案傳送, 請稍待')
            except Exception as e:
                self.uiCommons.show_error_dialog(e)
                logger.exception(e)
        else:
            self.uiCommons.show_message_dialog('傳送檔案', f'有另一個檔案傳送接收的工作還在進行中, 請稍待')

    def characterize_excel_file(self, title: str, decode: bool):
        try:
            file_name, _ = QFileDialog.getOpenFileName(self, title, "", "Excel 檔案 (*.xlsx)")
            if file_name:
                saved = CharacterizeService.processing_file(file_name, decode, False, True)
                os.startfile(saved)
        except Exception as e:
            self.uiCommons.show_error_dialog(e)
            logger.exception(e)

    def encode_excel_file(self):
        self.characterize_excel_file("開啟檔案 (編碼)", False)

    def decode_excel_file(self):
        self.characterize_excel_file("開啟檔案 (解碼)", True)