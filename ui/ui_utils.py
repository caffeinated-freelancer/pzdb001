from functools import partial
from typing import Callable

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLayout, QPushButton, QVBoxLayout, QGridLayout, QTextEdit, QDialog, QWidget

from ui.ui_commons import PzUiCommons


class PzUiButton():
    buttonText: str
    callback: Callable
    font: QFont | None
    buttonWidth: int
    buttonHeight: int

    def __init__(self, buttonText: str, callback: Callable, font: QFont | None = None, button_width: int = 0,
                 button_height: int = 0):
        self.buttonText = buttonText
        self.callback = callback
        self.font = font
        self.buttonWidth = button_width
        self.buttonHeight = button_height


def style101_button_creation(ui_commons: PzUiCommons,
                             buttons_and_functions: list[list[tuple[str, Callable] | QWidget | PzUiButton]],
                             button_font: QFont | None = None,
                             button_width: int = 280, button_height: int = 55) -> QGridLayout:
    button_map: dict[str, QPushButton] = {}
    buttons_layout = QGridLayout()

    if button_font is None:
        button_font = ui_commons.font14

    for row, keys in enumerate(buttons_and_functions):
        for col, k in enumerate(keys):
            if isinstance(k, tuple):
                key = k[0]
                func = k[1]
                button_map[key] = QPushButton(key)
                button_map[key].setFixedSize(button_width, button_height)
                button_map[key].setFont(button_font)
                if func is not None:
                    button_map[key].clicked.connect(partial(func))
                buttons_layout.addWidget(button_map[key], row, col)
            elif isinstance(k, QWidget):
                buttons_layout.addWidget(k, row, col)
            elif isinstance(k, PzUiButton):
                button_map[k.buttonText] = QPushButton(k.buttonText)
                if k.font is not None:
                    button_map[k.buttonText].setFont(k.font)
                else:
                    button_map[k.buttonText].setFont(button_font)
                button_map[k.buttonText].setFixedSize(
                    k.buttonWidth if k.buttonWidth > 0 else button_width,
                    k.buttonHeight if k.buttonHeight > 0 else button_height)
                button_map[k.buttonText].clicked.connect(partial(k.callback))
    return buttons_layout


def style101_dialog_layout(dialog: QDialog, ui_commons: PzUiCommons,
                           buttons_and_functions: list[list[tuple[str, Callable] | QWidget | PzUiButton]],
                           html: str | None = None,
                           button_font: QFont | None = None,
                           button_width: int = 280, button_height: int = 55) -> QLayout:
    layout = QVBoxLayout()

    buttons_layout = style101_button_creation(ui_commons, buttons_and_functions, button_font, button_width,
                                              button_height)

    # button_map: dict[str, QPushButton] = {}
    # buttons_layout = QGridLayout()
    #
    # if button_font is None:
    #     button_font = ui_commons.font14
    #
    # for row, keys in enumerate(buttons_and_functions):
    #     for col, k in enumerate(keys):
    #         if isinstance(k, tuple):
    #             key = k[0]
    #             func = k[1]
    #             button_map[key] = QPushButton(key)
    #             button_map[key].setFixedSize(button_width, button_height)
    #             button_map[key].setFont(button_font)
    #             if func is not None:
    #                 button_map[key].clicked.connect(partial(func))
    #             buttons_layout.addWidget(button_map[key], row, col)
    #         elif isinstance(k, QWidget):
    #             buttons_layout.addWidget(k, row, col)
    #         elif isinstance(k, PzUiButton):
    #             button_map[k.buttonText] = QPushButton(k.buttonText)
    #             if k.font is not None:
    #                 button_map[k.buttonText].setFont(k.font)
    #             else:
    #                 button_map[k.buttonText].setFont(button_font)
    #             button_map[k.buttonText].setFixedSize(
    #                 k.buttonWidth if k.buttonWidth > 0 else button_width,
    #                 k.buttonHeight if k.buttonHeight > 0 else button_height)
    #             button_map[k.buttonText].clicked.connect(partial(k.callback))

    layout.addLayout(buttons_layout)

    if html is not None:
        text_edit = QTextEdit()
        text_edit.setFont(ui_commons.font12)
        text_edit.setReadOnly(True)  # Optional: Make text non-editable
        text_edit.setHtml(html)
        layout.addWidget(text_edit)

    button = QPushButton("❎ 關閉")
    button.setFixedHeight(button_height)
    button.setFont(ui_commons.font12)
    button.clicked.connect(dialog.close)
    layout.addWidget(button)

    return layout
