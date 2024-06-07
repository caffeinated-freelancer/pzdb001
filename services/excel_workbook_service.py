from copy import copy
from typing import Any

import openpyxl
from openpyxl import Workbook
from openpyxl.cell import Cell
from openpyxl.styles import Font
from openpyxl.utils import coordinate_to_tuple
from openpyxl.worksheet.dimensions import RowDimension
from openpyxl.worksheet.worksheet import Worksheet

from pz.models.excel_model import ExcelModelInterface


class ExcelWorkbookService:
    headers: dict[str, int]
    model: ExcelModelInterface
    headers_rev: dict[Any, Any]
    max_column: int
    sheet: Worksheet | Any
    debug: bool
    wb: Workbook
    header_row: int

    def __init__(self, model: ExcelModelInterface, excel_file: str, sheet_name: str | None = None,
                 header_at: int | None = None, debug: bool = False) -> None:
        self.wb = openpyxl.load_workbook(excel_file)

        self.debug = debug
        self.model: ExcelModelInterface = model

        # print(self.wb.worksheets)
        # print(self.wb.sheetnames)
        self.sheet = self.wb[sheet_name] if sheet_name is not None else self.wb.active

        # self.sheet = self.wb.worksheets[sheet_name]

        self.header_row = 1

        if self.sheet.freeze_panes is not None:
            # print(self.sheet.freeze_panes)
            frozen_row, frozen_col = coordinate_to_tuple(self.sheet.freeze_panes)
            # print(frozen_row, frozen_col)
            self.header_row = frozen_row - 1

        if header_at is not None:
            self.header_row = header_at

        # print(self.header_row)

        self.headers = {}

        self.headers_rev = {}
        self.max_column = 0

        for colNum in range(1, self.sheet.max_column + 1, 1):
            cell = self.sheet.cell(self.header_row, colNum)
            value = cell.value
            if value is not None:
                if isinstance(value, str):
                    value = cell.value.replace('\r', '').replace('\n', '')
                # print("[", value, "]")
                self.headers[value] = colNum
                self.headers_rev[colNum] = value
                self.max_column = max(self.max_column, colNum)
                # print(value, max_column)

        self.max_column += 1

    def read_all(self, required_attribute: str | None = None) -> list[ExcelModelInterface]:
        if self.debug:
            print(self.headers)
        infos = []
        for rowNum in range(self.header_row + 1, self.sheet.max_row, 1):
            item = {}
            for colNum in range(1, self.max_column, 1):
                if colNum in self.headers_rev:
                    cell = self.sheet.cell(rowNum, colNum)
                    item[self.headers_rev[colNum]] = cell.value

                # print(cell.value, end='  ')
            # info = PzContactInfo(item)
            info = self.model.new_instance(item)

            if required_attribute is not None:
                if hasattr(info, required_attribute):
                    # print(info.to_json())
                    infos.append(info)
            else:
                infos.append(info)

        # if produceName in price_updates_dict:
        #     sheet.cell(rowNum, 2).value = price_updates_dict[produceName]
        #     sheet.cell(rowNum, 2).font = Font(color='FF0000')
        # 將結果另存新檔
        # wb.save('produceSales_update.xlsx')
        return infos

    def write_cell(self, row_num, col_num, value, color: str | None = None, font=None):
        current_font = self.sheet.cell(row_num, col_num).font
        self.sheet.cell(row_num, col_num).value = value

        if color is not None:
            # font.setColor(color)
            self.sheet.cell(row_num, col_num).font = Font(color=color, family=current_font.family,
                                                          size=current_font.size,
                                                          bold=current_font.bold, italic=current_font.italic,
                                                          underline=current_font.underline,
                                                          vertAlign=current_font.vertAlign,
                                                          outline=current_font.outline,
                                                          shadow=current_font.shadow, strike=current_font.strike,
                                                          charset=current_font.charset, condense=current_font.condense)
        elif font is not None:
            self.sheet.cell(row_num, col_num).font = font

    def get_font(self, row_num, col_num) -> Font:
        # col_num = col_num if col_num > 0 else 1
        font = self.sheet.cell(row_num, col_num).font

        # print(f'row:{row_num}, col:{col_num}, size:{font.size}')

        return Font(family=font.family, size=font.size,
                    bold=font.bold, italic=font.italic, underline=font.underline,
                    vertAlign=font.vertAlign, outline=font.outline,
                    shadow=font.shadow, strike=font.strike,
                    charset=font.charset, condense=font.condense)

    def get_cell(self, row_num, col_num) -> Cell:
        # col_num = col_num if col_num > 0 else 1
        return self.sheet.cell(row_num, col_num)

    def set_cell_properties(self, row_num, col_num, another_cell: Cell):
        cell = self.sheet.cell(row_num, col_num)

        cell.alignment = copy(another_cell.alignment)
        cell.font = copy(another_cell.font)
        cell.border = copy(another_cell.border)
        cell.fill = copy(another_cell.fill)

    def get_row_dimensions(self, row_num):
        return self.sheet.row_dimensions[row_num]

    def set_row_dimensions(self, row_num, value: RowDimension):
        self.sheet.row_dimensions[row_num].height = value.height
        # self.sheet.row_dimensions[row_num].alignment = value.alignment

    def get_headers(self) -> dict[str, int]:
        return self.headers

    def get_header_row(self) -> int:
        return self.header_row

    def save_as(self, filename: str):
        print(f'Save excel workbook as: {filename}')
        self.wb.save(filename)
