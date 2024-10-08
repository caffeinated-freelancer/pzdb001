from PyQt6.QtWidgets import QDialog

from pz.config import PzProjectConfig
from ui.config_holder import ConfigHolder
from ui.ui_commons import PzUiCommons
from ui.ui_utils import style101_dialog_layout


class PilgrimageDialog(QDialog):
    configHolder: ConfigHolder
    config: PzProjectConfig
    uiCommons: PzUiCommons

    def __init__(self, holder: ConfigHolder):
        super().__init__()
        self.configHolder = holder
        self.config = holder.get_config()
        self.uiCommons = PzUiCommons(self, holder)

        self.setWindowTitle(f'回山排車相關作業')

        buttons_and_functions = [
            [
                ('回山相關作業 1', self.uiCommons.under_construction),
                ('回山相關作業 2', self.uiCommons.under_construction)
            ],
        ]

        self.resize(550, 400)

        layout = style101_dialog_layout(self, self.uiCommons, buttons_and_functions)
        self.setLayout(layout)
