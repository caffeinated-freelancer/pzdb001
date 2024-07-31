import os

from PyQt6.QtWidgets import QDialog, QFileDialog
from loguru import logger

from pz.config import PzProjectConfig
from pz_functions.generaters.generate_lookup import generate_lookup
from ui.processing_done_dialog import ProcessingDoneDialog
from ui.ui_commons import PzUiCommons
from ui.ui_utils import style101_dialog_layout
from version import __pz_version__


class VLookUpDialog(QDialog):
    config: PzProjectConfig
    uiCommons: PzUiCommons

    def __init__(self, cfg: PzProjectConfig):
        self.config = cfg
        self.uiCommons = PzUiCommons(self, self.config)
        super().__init__()
        self.setWindowTitle(f'姓名 V 班級/組別 v{__pz_version__}')

        buttons_and_functions = [
            [('開啟 Excel 檔 (一般電腦用)', self.vlookup_by_name)],
            [('開啟 Excel 檔 (個資電腦用)', self.vlookup_by_name_using_access)],
        ]

        self.resize(550, 620)

        layout = style101_dialog_layout(self, self.uiCommons, buttons_and_functions, button_width=500, html=f'''
    <h3>姓名 V 班級/組別</h3>
    <ol>
<li>支援的欄位名稱 (個資系統標準命名):
<ul>
<li>學員編號 : 可做為查詢或回填 (以姓名回填學員編號)</li>
<li>姓名 : 可做為查詢或回填 (以學員編號回填姓名)</li>
<li>法名 : 輔助姓名查詢用, 或回填</li>
<li>班級 : 空白時回填</li>
<li>組別 : 空白時回填</li>
<li>學長 : 空白時回填</li>
<li>性別 : 空白時回填</li>
<li>出生日期 : 空白時回填</li>
<li>行動電話 : 空白時回填</li>
<li>住家電話 : 空白時回填</li>
</ul></li>
<li>以姓名 vlookup 時, 可在必要時加法名輔助, 加法名輔助的方式有兩種:
<ul>
<li>僅用姓名欄, 格式如: 孫行者(悟空), 請用半形括號。</li>
<li>用姓名欄跟法名欄</li>
</ul>
<li>會產生一新的檔案，放置於原始檔相同目錄，並以原檔名加上日期做識別。</li>
    </ol>
            ''')
        self.setLayout(layout)

    def vlookup_by_name(self):
        self.perform_vlookup_by_name(False)

    def vlookup_by_name_using_access(self):
        self.perform_vlookup_by_name(True)

    def perform_vlookup_by_name(self, via_access: bool):
        try:
            file_name, _ = QFileDialog.getOpenFileName(self, "開啟檔案", "", "Excel 檔案 (*.xlsx);; 所有檔案 (*)")
            if file_name:
                saved_file, warnings = generate_lookup(self.config, file_name, via_access=via_access)
                self.close()

                if len(warnings) > 0:
                    logger.warning(warnings)
                    button = self.uiCommons.create_a_button(f'開啟產出的 Excel 檔')
                    button.clicked.connect(lambda: os.startfile(saved_file))
                    dialog = ProcessingDoneDialog(self.config, '完成 Vlookup',
                                                  ['位置', '警告訊息'], warnings, [[button]])
                    dialog.exec()
                else:
                    os.startfile(saved_file)
        except Exception as e:
            self.uiCommons.show_error_dialog(e)
            logger.error(e)
