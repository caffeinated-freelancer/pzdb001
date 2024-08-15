from PyQt6.QtWidgets import QDialog
from loguru import logger

from pz.config import PzProjectConfig
from pz_functions.exporters.member_to_access import member_to_access_db
from pz_functions.importers.mysql_functions import write_access_to_mysql, migrate_access_table_to_mysql
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
                # ('匯整 Access 基本資料', self.merge_access_database),
                ('🔜 [A->M] 匯入學員基本資料 (Details)', self.access_to_mysql),
            ],
            [
                ('🔜 [A->M] 匯入學員基本資料 (Basics)', self.migrate_access_table_to_mysql),
            ],
            [
                ('🔙 [M->A] 班級學員資料匯入 Access', self.member_to_access),
            ],
        ]

        self.resize(550, 600)

        layout = style101_dialog_layout(self, self.uiCommons, buttons_and_functions, html=f'''
    <h3>MS-Access 資料庫說明</h3>
    <ol>
    <li><font color="blue">[A-&gt;M]</font> 是指從 Access 匯入 MySQL, 而 <font color="blue">[M-&gt;A]</font> 則是由 MySQL 匯入 Access。</li>
    <li>MS-Access 資料庫是做為 Excel 快速匯入的一個暫用資料庫，因為 MS-Access 資料庫是單機模式，所以只是暫時借用。</li>
    <li>把班級學員資料匯入 Access 的目的是: 當電腦若不能連資料庫，則可自帶一份 MS-Access 單機處理。</li>
    <li>Details 是原本人工匯整多個殘破資料表而來，大部份的程式碼都是讀取這個表。</li>
    <li>Basics 來自資料源，它比 Details 更 detail，但程式並不支援它。目前的做法是在 Access 上，直接把 Basic 覆蓋 Details 
    來讓程式可以不必做太多的修改。</li>
    </ol>
            ''', button_width=500)
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

    def migrate_access_table_to_mysql(self):
        try:
            count = migrate_access_table_to_mysql(self.config)
            self.uiCommons.done()
            self.uiCommons.show_message_dialog(
                '資料表移轉', f'完成由 MS-Access 表匯入 {count} 筆資料到 MySQL')
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
