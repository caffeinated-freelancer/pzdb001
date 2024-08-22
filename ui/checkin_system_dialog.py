import os

from PyQt6.QtWidgets import QDialog
from loguru import logger

from pz.config import PzProjectConfig
from pz_functions.assists.checkin import export_member_for_checkin_system
from ui.ui_commons import PzUiCommons
from ui.ui_utils import style101_dialog_layout


class CheckinSystemDialog(QDialog):
    config: PzProjectConfig
    uiCommons: PzUiCommons

    def __init__(self, cfg: PzProjectConfig):
        super().__init__()
        self.config = cfg
        self.uiCommons = PzUiCommons(self, self.config)

        self.setWindowTitle(f'報到系統資料處理')

        buttons_and_functions = [
            [
                ('報到系統用學員資料匯出', self.checkin_system_member_export),
            ], [
                ('福慧出坡簽到資料匯出', self.uiCommons.under_construction),
            ], [
                ('福慧出坡補簽到記錄', self.uiCommons.under_construction),
            ],
        ]

        self.resize(550, 400)

        layout = style101_dialog_layout(self, self.uiCommons, buttons_and_functions, html=f'''
            <h3>報到系統資料處理</h3>
            <ol>
            <li>本系統提供部份報到系統後端輔助功能。</li>
            </ol>
                    ''')
        self.setLayout(layout)

    def checkin_system_member_export(self):
        try:
            saved_file = export_member_for_checkin_system(self.config)
            os.startfile(saved_file)
        except Exception as e:
            self.uiCommons.show_error_dialog(e)
            logger.error(e)
