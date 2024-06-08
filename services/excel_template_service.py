import os

from pz.config import PzProjectExcelSpreadsheetConfig
from pz.models.excel_model import ExcelModelInterface
from services.excel_workbook_service import ExcelWorkbookService


class ExcelTemplateService:
    service: ExcelWorkbookService
    target_folder: str
    template_file: str
    destination_path: str
    headers: dict[str, int]
    header_row: int

    def __init__(self, model: ExcelModelInterface, template_spreadsheet: PzProjectExcelSpreadsheetConfig,
                 source_file_name: str, target_folder: str, debug: bool = False):
        if not os.path.exists(target_folder):
            raise FileNotFoundError(target_folder)

        self.template_file = template_spreadsheet.spreadsheet_file
        self.target_folder = target_folder

        # Define the source and destination paths
        self.destination_path = f'{target_folder}/output-{os.path.basename(source_file_name)}'

        # Copy the file
        # shutil.copyfile(template_file, destination_path)

        self.service = ExcelWorkbookService(model, self.template_file, header_at=template_spreadsheet.header_row,
                                            debug=debug)
        self.headers = self.service.get_headers()
        self.header_row = self.service.get_header_row()

    def get_headers(self) -> dict[str, int]:
        return self.headers

    def write_cell_at(self, row: int, column: int, value: str, font=None):
        self.service.write_cell(row, column, value, font=font)

    def write_cell(self, row: int, data: dict[str, str | int | None]):
        for column_name, index in self.headers.items():
            if column_name in data:
                self.write_cell_at(row, index, data[column_name])

    def write_data(self, callback):
        row_num = self.header_row + 1

        # fonts = [self.service.get_font(row_num, i) for i in range(1, len(self.headers), 1)]
        template_cells = [self.service.get_cell(row_num + 1, i) for i in range(1, len(self.headers) + 1, 1)]
        dimension = self.service.get_row_dimensions(row_num)

        for supplier in callback:
            datum = supplier()
            for column_name, index in self.headers.items():
                if column_name in datum:
                    self.service.write_cell(row_num, index, datum[column_name])
                    # print(index, len(template_cells))
                else:
                    self.service.write_cell(row_num, index, '')
                self.service.set_cell_properties(row_num, index, template_cells[index - 1])
            self.service.set_row_dimensions(row_num, dimension)
            row_num += 1

        self.service.save_as(self.destination_path)

    def save_as(self, file_name: str | None = None):
        if file_name is not None:
            self.service.save_as(file_name)
        else:
            self.service.save_as(self.destination_path)
