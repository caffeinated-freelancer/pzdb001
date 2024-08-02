from PyQt6.QtWidgets import QDialog

from pz.config import PzProjectConfig
from ui.ui_commons import PzUiCommons
from ui.ui_utils import style101_dialog_layout


class PilgrimageDialog(QDialog):
    config: PzProjectConfig
    uiCommons: PzUiCommons

    def __init__(self, cfg: PzProjectConfig):
        super().__init__()
        self.config = cfg
        self.uiCommons = PzUiCommons(self, self.config)

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
