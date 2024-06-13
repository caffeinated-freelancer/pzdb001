import os
from functools import partial

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QPushButton, QVBoxLayout, QGridLayout,
)

from pz.config import PzProjectConfig
from pz.utils import explorer_folder
from pz_functions.generaters.graduation import generate_graduation_reports
from pz_functions.generaters.introducer import generate_introducer_reports

WINDOW_SIZE = 235
DISPLAY_HEIGHT = 35
BUTTON_SIZE = 120


class PyPzWindows(QMainWindow):
    config: PzProjectConfig

    def __init__(self, cfg: PzProjectConfig):
        super().__init__()
        self.config = cfg
        self.setWindowTitle("普中資料管理程式")
        self.setFixedSize(580, 400)
        self.generalLayout = QVBoxLayout()

        centralWidget = QWidget(self)
        centralWidget.setLayout(self.generalLayout)
        self.setCentralWidget(centralWidget)
        self._createButtons()

        # layout = QHBoxLayout()
        # #
        # button = QPushButton("產生結業報表")
        # button.clicked.connect(partial(generate_graduation_reports, cfg))
        #
        # layout.addWidget(button)
        # layout.addWidget(QPushButton("Center"))
        # layout.addWidget(QPushButton("Right"))
        # window.setLayout(layout)

    def do_nothing(self):
        os.startfile(self.config.output_folder)

    def open_folder(self):
        os.startfile(self.config.output_folder)

    def run_generate_graduation_reports(self):
        generate_graduation_reports(self.config)
        # os.startfile(self.config.output_folder)

    def run_introducer_report(self):
        self.config.make_sure_output_folder_exists()
        self.config.explorer_output_folder()
        generate_introducer_reports(self.config)

    def open_graduation_folder(self):
        explorer_folder(self.config.excel.graduation.records.spreadsheet_folder)

    def open_questionnaire_folder(self):
        explorer_folder(self.config.excel.questionnaire.spreadsheet_folder)

    def _createButtons(self):
        self.buttonMap = {}
        buttonsLayout = QGridLayout()
        keyBoard = [
            [('禪修班結業統計', self.run_generate_graduation_reports),
             ('上課記錄 資料夾', self.open_graduation_folder)],
            [('介紹人電聯表', self.run_introducer_report), ('意願調查 資料夾', self.open_questionnaire_folder)],
            [('學員電聯表', self.do_nothing), ],
            # [('開課前電聯表', self.do_nothing), ],
            # [('關懷表', self.do_nothing), ],
        ]

        font = QFont('Microsoft YaHei', 16)

        for row, keys in enumerate(keyBoard):
            for col, k in enumerate(keys):
                key = k[0]
                func = k[1]
                self.buttonMap[key] = QPushButton(key)
                self.buttonMap[key].setFixedSize(250, 60)
                self.buttonMap[key].setFont(font)
                if func is not None:
                    # print(key)
                    self.buttonMap[key].clicked.connect(partial(func))
                buttonsLayout.addWidget(self.buttonMap[key], row, col)

        self.generalLayout.addLayout(buttonsLayout)

        output_folder_button = QPushButton('輸出樣版資料夾')
        output_folder_button.setFixedSize(500, 60)
        output_folder_button.setFont(font)
        # print(self.config.template_folder)
        output_folder_button.clicked.connect(partial(explorer_folder, self.config.template_folder))
        self.generalLayout.addWidget(output_folder_button)

        output_folder_button = QPushButton('程式輸出資料夾')
        output_folder_button.setFixedSize(500, 60)
        output_folder_button.setFont(font)
        output_folder_button.clicked.connect(partial(explorer_folder, self.config.output_folder))
        self.generalLayout.addWidget(output_folder_button)
