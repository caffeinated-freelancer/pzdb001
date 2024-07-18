import re
from collections import OrderedDict
from copy import copy
from typing import Any

import openpyxl
from loguru import logger
from openpyxl import Workbook
from openpyxl.cell import Cell
from openpyxl.styles import Font
from openpyxl.utils import coordinate_to_tuple, get_column_letter
from openpyxl.worksheet.dimensions import RowDimension, ColumnDimension
from openpyxl.worksheet.pagebreak import Break
from openpyxl.worksheet.worksheet import Worksheet

from pz.models.excel_model import ExcelModelInterface


class PzCellProperties:
    def __init__(self, another_cell: Cell):
        self.alignment = copy(another_cell.alignment)
        self.font = copy(another_cell.font)
        self.border = copy(another_cell.border)
        self.fill = copy(another_cell.fill)


class ExcelWorkbookService:
    headers: OrderedDict[str, int]
    model: ExcelModelInterface
    headers_rev: dict[Any, Any]
    max_column: int
    sheet: Worksheet | Any
    debug: bool
    wb: Workbook
    header_row: int
    ignore_parenthesis: bool
    print_header: bool

    def __init__(self, model: ExcelModelInterface, excel_file: str, sheet_name: str | None = None,
                 header_at: int | None = None, ignore_parenthesis: bool = False, debug: bool = False,
                 print_header: bool = False) -> None:
        self.ignore_parenthesis = ignore_parenthesis
        self.print_header = print_header

        self.wb = openpyxl.load_workbook(excel_file)

        self.debug = debug
        self.model: ExcelModelInterface = model

        # if debug:
        #     print(self.wb.worksheets)
        #     print(self.wb.sheetnames)
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

        # for column in range(1, self.sheet.max_column):
        #     letter = get_column_letter(column)
        #
        #     print(f'{letter}: {self.sheet.column_dimensions[letter].width}')

        logger.debug(f'{excel_file}: {self.wb.sheetnames}/row:{self.header_row} - {self.wb.worksheets}')

        self.rehash_header()

    def __del__(self):
        self.wb.close()

    def rehash_header(self):
        self.headers = OrderedDict()

        self.headers_rev = {}
        self.max_column = 0

        for colNum in range(1, self.sheet.max_column + 1, 1):
            cell = self.sheet.cell(self.header_row, colNum)
            value = cell.value
            if value is not None:
                if isinstance(value, str):
                    value = cell.value.replace('\r', '').replace('\n', '')
                # print("[", value, "]")
                if self.ignore_parenthesis:
                    matched = re.match(r'^\s*(.*\S)\s*\(.*', value)
                    if matched:
                        value = matched.group(1)
                self.headers[value] = colNum
                if isinstance(value, str):
                    self.headers_rev[colNum] = value.strip()
                else:
                    self.headers_rev[colNum] = value
                self.max_column = max(self.max_column, colNum)
                # print(value, max_column)

        self.max_column += 1

        if self.print_header:
            print(f'Header row at: {self.header_row}')
            for header in self.headers:
                # print(header, self.headers[header])
                print(f'\'\': \'{header}\',')

    def add_page_break(self, row: int):
        self.sheet.row_breaks.append(Break(id=row))

    def read_all(self, required_attribute: str | None = None) -> list[ExcelModelInterface]:
        if self.debug:
            logger.debug(self.headers)
        infos = []
        for rowNum in range(self.header_row + 1, self.sheet.max_row + 1, 1):
            item = {}
            for colNum in range(1, self.max_column, 1):
                if colNum in self.headers_rev:
                    cell = self.sheet.cell(rowNum, colNum)
                    value = cell.value
                    if isinstance(value, str):
                        item[self.headers_rev[colNum]] = value.strip()
                    else:
                        item[self.headers_rev[colNum]] = value

                # print(cell.value, end='  ')
            # info = PzContactInfo(item)
            info = self.model.new_instance(item)

            if required_attribute is not None:
                if hasattr(info, required_attribute) and info.__dict__.get(required_attribute) is not None:
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
        cell = self.sheet.cell(row_num, col_num)

        if color is not None:
            current_font = cell.font
            # print(f'set color as {color}')
            # font.setColor(color)
            cell.font = Font(color=color, family=current_font.family,
                             size=current_font.size,
                             bold=current_font.bold, italic=current_font.italic,
                             underline=current_font.underline,
                             vertAlign=current_font.vertAlign,
                             outline=current_font.outline,
                             shadow=current_font.shadow, strike=current_font.strike,
                             charset=current_font.charset, condense=current_font.condense)
        elif font is not None:
            cell.font = font

        cell.value = value

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

    def set_cell_properties_from_pz_cell(self, row_num, col_num, pz_cell: PzCellProperties):
        cell = self.sheet.cell(row_num, col_num)

        cell.alignment = copy(pz_cell.alignment)
        cell.font = copy(pz_cell.font)
        cell.border = copy(pz_cell.border)
        cell.fill = copy(pz_cell.fill)

    def get_row_dimensions(self, row_num) -> RowDimension:
        return self.sheet.row_dimensions[row_num]

    def set_row_dimensions(self, row_num, value: RowDimension):
        self.sheet.row_dimensions[row_num].height = value.height
        # self.sheet.row_dimensions[row_num].alignment = value.alignment

    def get_column_dimension(self, col_num) -> ColumnDimension:
        column_a_width = self.sheet.column_dimensions[col_num].width
        if column_a_width is None:
            logger.debug(f"Column {col_num} width is not set explicitly.")
        else:
            logger.debug(f"Column {col_num} width: {column_a_width}")
        logger.debug(f'get column dimension for {col_num}, width: {self.sheet.column_dimensions[col_num].width}')
        return self.sheet.column_dimensions[col_num]

    def set_column_dimension(self, col_num, value: ColumnDimension):
        self.sheet.column_dimensions[col_num].width = value.width
        pass

    def set_column_width(self, col_num, width: float):
        self.sheet.column_dimensions[get_column_letter(col_num)].width = width

    def get_headers(self) -> dict[str, int]:
        return self.headers

    def get_header_row(self) -> int:
        return self.header_row

    def max_column(self) -> int:
        return self.max_column

    def max_row(self) -> int:
        return self.sheet.max_row

    def save_as(self, filename: str):
        logger.info(f'Save excel workbook as: {filename}')
        self.wb.save(filename)
