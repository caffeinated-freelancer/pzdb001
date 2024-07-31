from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout
from loguru import logger

from ui.ui_commons import PzUiCommons


class PzTableWidget(QWidget):
    def __init__(self, headers: list[str], data: list[list[Any]]):
        super().__init__()

        self.table = QTableWidget()
        self.table.setColumnCount(len(headers))
        self.table.setRowCount(len(data))
        self.table.setFont(PzUiCommons.font14)
        self.table.setHorizontalHeaderLabels(headers)

        logger.trace(f'columns: {len(headers)}, row: {len(data)}')

        # Populate table with data
        for row in range(len(data)):
            logger.trace(f'{row} in range({len(headers)})')
            row_data = data[row]
            logger.trace(row_data)
            for column in range(len(headers)):
                if column < len(row_data):
                    item = QTableWidgetItem(str(row_data[column]))
                else:
                    item = QTableWidgetItem('')
                item.setFont(PzUiCommons.font14)
                item.setTextAlignment(Qt.AlignmentFlag.AlignTop)
                self.table.setItem(row, column, item)

        # self.table.setMinimumWidth(300)
        self.table.resizeColumnsToContents()

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)

    # def resizeEvent(self, event):
    #     new_width = self.width()
    #     new_height = self.height()
    #     logger.trace(f"Widget resized to: {new_width} x {new_height}")
    #     # self.table.resizeColumnsToContents()
    #     self.table.resizeColumnToContents(new_width)
