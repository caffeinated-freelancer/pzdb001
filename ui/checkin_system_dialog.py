import os

from PyQt6.QtWidgets import QDialog
from loguru import logger

from pz.config import PzProjectConfig
from pz_functions.assists.checkin import export_all_members_for_checkin_system, export_class_member_for_checkin_system
from ui.config_holder import ConfigHolder
from ui.ui_commons import PzUiCommons
from ui.ui_utils import style101_dialog_layout


class CheckinSystemDialog(QDialog):
    configHolder: ConfigHolder
    config: PzProjectConfig
    uiCommons: PzUiCommons

    def __init__(self, holder: ConfigHolder):
        super().__init__()
        self.configHolder = holder
        self.config = holder.get_config()
        self.uiCommons = PzUiCommons(self, holder)

        self.setWindowTitle(f'報到系統資料處理')

        buttons_and_functions = [
            [
                ('報到系統用班級學員資料匯出', self.checkin_system_class_member_export),
            ], [
                ('報到系統用學員(全部)資料匯出', self.checkin_system_all_members_export),
            ], [
                ('福慧出坡簽到資料匯出', self.uiCommons.under_construction),
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

    def checkin_system_class_member_export(self):
        try:
            saved_file = export_class_member_for_checkin_system(self.config)
            os.startfile(saved_file)
        except Exception as e:
            self.uiCommons.show_error_dialog(e)
            logger.error(e)

    def checkin_system_all_members_export(self):
        try:
            saved_file = export_all_members_for_checkin_system(self.config)
            os.startfile(saved_file)
        except Exception as e:
            self.uiCommons.show_error_dialog(e)
            logger.error(e)
