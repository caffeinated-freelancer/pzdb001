from PyQt6.QtWidgets import QDialog
from loguru import logger

from pz.utils import explorer_folder
from pz_functions.exporters.attend_to_class import from_attend_records_to_class
from ui.config_holder import ConfigHolder
from ui.ui_commons import PzUiCommons
from ui.ui_utils import style101_dialog_layout
from version import __pz_version__


class CloudUploadDialog(QDialog):
    configHolder: ConfigHolder
    uiCommons: PzUiCommons

    def __init__(self, holder: ConfigHolder):
        self.configHolder = holder
        self.uiCommons = PzUiCommons(self, holder)
        super().__init__()
        self.setWindowTitle(f'雲端資料上傳 v{__pz_version__}')

        buttons_and_functions = [
            [
                # ('匯整 Access 基本資料', self.merge_access_database),
                ('🔜 上課記錄轉成 Google 雲端學員資料', self.upload_to_google),
            ],
            [
                ('📁 上課記錄', self.open_graduation_folder),
            ],
        ]

        self.resize(550, 400)

        layout = style101_dialog_layout(self, self.uiCommons, buttons_and_functions, html=f'''
    <h3>功能說明</h3>
    <ol>
    <li>依照上課記錄，可以轉成班級學員資料。</li>
    <li>「上課記錄轉成 Google 雲端學員資料」的功能是把這些記錄自動更新 Google 
    雲端的「學長調查」試算表。不過系統不會更新正式版的那份「學長調查」試算表，而是在另一個長得很像的表上。</li>
    </ol>
            ''', button_width=500)
        self.setLayout(layout)

        # Connect button click to slot (method)

    def open_graduation_folder(self):
        explorer_folder(self.configHolder.get_config().excel.graduation.records.spreadsheet_folder)

    def upload_to_google(self):
        try:
            from_attend_records_to_class(self.configHolder.get_config())
        except Exception as e:
            self.uiCommons.show_error_dialog(e)
            logger.error(e)
        finally:
            logger.debug("uploaded")
