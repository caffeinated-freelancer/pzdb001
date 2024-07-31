from functools import partial

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QDialog, QPushButton, QVBoxLayout, QTextEdit
from loguru import logger

from pz.config import PzProjectConfig
from pz.utils import explorer_folder
from pz_functions.importers.member_details_update import member_details_update
from ui.ui_commons import PzUiCommons
from version import __pz_version__


class MemberImportDialog(QDialog):
    config: PzProjectConfig
    uiCommons: PzUiCommons

    def __init__(self, cfg: PzProjectConfig):
        self.config = cfg
        self.uiCommons = PzUiCommons(self, self.config)
        super().__init__()
        self.setWindowTitle(f'學員基本資料匯入 v{__pz_version__}')

        self.resize(550, 600)

        # Create layout and widgets
        layout = QVBoxLayout()

        folder_button = QPushButton('學員資料更新資料夾')
        folder_button.setMinimumHeight(300)
        folder_button.setMinimumHeight(60)
        folder_button.setFont(self.uiCommons.font14)
        folder_button.clicked.connect(partial(self.open_member_import_folder))

        import_button = QPushButton('學員基本資料 匯入')
        import_button.setMinimumHeight(300)
        import_button.setMinimumHeight(60)
        import_button.setFont(self.uiCommons.font14)
        import_button.clicked.connect(partial(self.member_info_import))

        text_edit = QTextEdit()
        font = QFont('Microsoft YaHei', 12)
        text_edit.setFont(font)
        text_edit.setReadOnly(True)  # Optional: Make text non-editable
        text_edit.setHtml(f'''
    <h3>學員基本資料匯入/更新說明</h3>
    <ol>
    <li>匯入更新檔為 Excel 格式，內容<font color="red">不需要</font>包括所有的學員，只需要有<font color="blue">更新</font>的部份即可。</li>
    <li>匯入格式同匯出格式，因此可以先匯出以了解匯入格式。</li>
    <li>學員編號是主鍵，缺少學員編號的資料程式採不處理。</li>
    <li>系統採用<font color="blue">更新</font>的做法，除了學號以外，只有需要更新的欄位填入資料即可，未填的部份代表保留原資料不更新。</li>
    <li>請勿僅有學號而沒有任何其它的資料，如果這種情形的時候，代表想<font color="red">刪掉</font>這筆學號資料。</li>
    <li>此匯入/更新功能採用讀取資料夾中的所有檔案，依檔名依序執行。意指可以有多個更新檔，而前面檔更新的資料會被後面的更新檔複蓋。</li>
    <li>為了確保檔名被處理的次序，建議用　001, 002, 003, ..., 010, 011 這樣的檔名開頭，不要用 1, 2, 3, ..., 10, 11 的命名。</li>
    <li></li>
    </ol>
            ''')
        button = QPushButton("關閉")
        button.setFixedHeight(55)
        button.setFont(font)

        # Add widgets to layout and set layout
        # layout.addWidget(label)
        layout.addWidget(folder_button)
        layout.addWidget(import_button)
        layout.addWidget(text_edit)
        layout.addWidget(button)
        self.setLayout(layout)

        # Connect button click to slot (method)
        button.clicked.connect(self.close)

    def member_info_import(self):
        try:
            member_details_update(self.config)
            self.uiCommons.done()
            self.uiCommons.show_message_dialog('匯入/更新學員基本資料', f'完成匯入/更新學員基本資料')
            self.close()
        except Exception as e:
            self.uiCommons.show_error_dialog(e)
            logger.error(e)

    def open_member_import_folder(self):
        explorer_folder(self.config.excel.member_details_update.spreadsheet_folder)
