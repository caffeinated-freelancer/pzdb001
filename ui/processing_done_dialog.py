from typing import Callable

from PyQt6.QtWidgets import QDialog, QWidget

from ui.config_holder import ConfigHolder
from ui.pz_table_widget import PzTableWidget
from ui.ui_commons import PzUiCommons
from ui.ui_utils import style101_dialog_layout, PzUiButton


class ProcessingDoneDialog(QDialog):
    configHolder: ConfigHolder

    def __init__(self, holder: ConfigHolder, title: str, headers: list[str], messages: list[list[str]],
                 widgets: list[list[QWidget]] | None, width: int = 550, height: int = 520):
        self.configHolder = holder
        self.uiCommons = PzUiCommons(self, holder)
        super().__init__()
        self.setWindowTitle(title)

        widget = PzTableWidget(headers, messages)

        buttons_and_functions: list[list[tuple[str, Callable] | QWidget | PzUiButton]] = [
            [widget],
        ]

        if widgets is not None:
            buttons_and_functions.extend(widgets)

        self.resize(width, height)

        layout = style101_dialog_layout(self, self.uiCommons, buttons_and_functions)
        self.setLayout(layout)
