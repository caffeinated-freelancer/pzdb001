from PyQt6.QtWidgets import QDialog, QFileDialog
from loguru import logger

from pz.config import PzProjectConfig
from services.file_transfer_service import FileTransferService
from services.rs232 import Rs232Service
from ui.ui_commons import PzUiCommons
from ui.ui_utils import style101_dialog_layout
from version import __pz_version__


def receive_file_worker(rs232: Rs232Service, folder: str):
    print("Starting thread...")
    rs232.recv_file(folder)
    print("Thread finished.")


class ToolboxDialog(QDialog):
    config: PzProjectConfig
    uiCommons: PzUiCommons

    def __init__(self, cfg: PzProjectConfig):
        self.config = cfg
        self.uiCommons = PzUiCommons(self, self.config)
        self.fileTransferService = FileTransferService(self.config)
        super().__init__()
        self.setWindowTitle(f'設計師的工具小品 v{__pz_version__}')

        buttons_and_functions = [
            [
                ('檔案欄位編碼', self.dummy),
                ('檔案欄位解碼', self.dummy),
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

    def dummy(self):
        pass

    def receive_file(self):
        logger.info('receive_file')
        self.fileTransferService.receive_file()

    def send_file(self):
        try:
            file_name, _ = QFileDialog.getOpenFileName(self, "開啟檔案", "", "所有檔案 (*)")
            if file_name:
                self.fileTransferService.send_file(file_name)
        except Exception as e:
            self.uiCommons.show_error_dialog(e)
            logger.error(e)
