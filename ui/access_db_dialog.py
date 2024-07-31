from PyQt6.QtWidgets import QDialog
from loguru import logger

from pz.config import PzProjectConfig
from pz_functions.exporters.member_to_access import member_to_access_db
from pz_functions.importers.mysql_functions import write_access_to_mysql
from pz_functions.mergers.member_merging import member_data_merging
from ui.ui_commons import PzUiCommons
from ui.ui_utils import style101_dialog_layout
from version import __pz_version__


class AccessDatabaseDialog(QDialog):
    config: PzProjectConfig
    uiCommons: PzUiCommons

    def __init__(self, cfg: PzProjectConfig):
        self.config = cfg
        self.uiCommons = PzUiCommons(self, self.config)
        super().__init__()
        self.setWindowTitle(f'MS-Access 資料庫 v{__pz_version__}')

        buttons_and_functions = [
            [
                ('匯整 Access 學員資料', self.merge_access_database),
                ('匯入 Access 學員資料', self.access_to_mysql),
            ],
            [
                ('學員資料匯入 Access', self.member_to_access),
            ],
        ]

        self.resize(550, 400)

        layout = style101_dialog_layout(self, self.uiCommons, buttons_and_functions, html=f'''
    <h3>MS-Access 資料庫說明</h3>
    <ol>
    <li>MS-Access 資料庫是做為 Excel 快速匯入的一個暫用資料庫，因為 MS-Access 資料庫是單機模式，所以只是暫時借用。</li>
    <li>個資電腦因為不能連精舍資料庫，如果個資電腦有支援使用 MS-Access 的話，我們仍會使用 MS-Access 來輔助處理資料。</li>
    </ol>
            ''')
        self.setLayout(layout)

        # Connect button click to slot (method)

    def access_to_mysql(self):
        try:
            write_access_to_mysql(self.config)
            self.uiCommons.done()
            self.uiCommons.show_message_dialog(
                '學員基本資料匯入', '完成匯入： 學員基本資料 由 MS-Access 資料庫匯入 MySQL 資料庫')
        except Exception as e:
            self.uiCommons.show_error_dialog(e)
            logger.error(e)

    def merge_access_database(self):
        try:
            member_data_merging(self.config.ms_access_db.db_file, self.config.ms_access_db.target_table)
            self.uiCommons.done()
            self.uiCommons.show_message_dialog(
                '資料匯整', f'資料匯整完成, 匯整至 {self.config.ms_access_db.target_table} 資料表')
        except Exception as e:
            self.uiCommons.show_error_dialog(e)
            logger.error(e)

    def member_to_access(self):
        try:
            records = member_to_access_db(self.config)
            self.uiCommons.done()
            self.uiCommons.show_message_dialog(
                '學員資料匯入 Access', f'{records} 筆學員資料匯入 MS-Access 資料庫')
        except Exception as e:
            self.uiCommons.show_error_dialog(e)
            logger.error(e)
