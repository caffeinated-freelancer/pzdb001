import json
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from loguru import logger

from pz.config import PzProjectGoogleSpreadsheetConfig
from pz.utils import safe_index

# SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]
# SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/drive.file",
#           "https://www.googleapis.com/auth/spreadsheets"]
# SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class SpreadsheetValueData:
    value: Any
    unformatted_value: Any

    def __init__(self, value, unformatted_value):
        self.value = value
        self.unformatted_value = unformatted_value


class SpreadsheetValueWithFormula:
    value: Any
    formula: Any

    def __init__(self, value, formula):
        self.value = value
        self.formula = formula

    def __str__(self):
        return f"{self.value} {self.formula}"


class Spreadsheet:
    sheetId: int
    title: str
    index: int
    sheetType: str
    rowCount: int
    columnCount: int
    frozenRowCount: int
    frozenColumnCount: int
    service: 'GoogleSpreadsheetService'

    # 'gridProperties': {'rowCount': 782, 'columnCount': 24, 'frozenRowCount': 2, 'frozenColumnCount': 10}}

    def __init__(self, service: 'GoogleSpreadsheetService', properties: dict[str, str | int | dict[str, int]]):
        self.service = service
        self.sheetId = properties['sheetId']
        self.title = properties['title']
        self.index = properties['index']
        self.sheetType = properties['sheetType']
        grid_properties = properties['gridProperties']
        self.rowCount = grid_properties['rowCount']
        self.columnCount = grid_properties['columnCount']
        self.frozenRowCount = grid_properties['frozenRowCount'] if 'frozenRowCount' in grid_properties else 0
        self.frozenColumnCount = grid_properties['frozenColumnCount'] if 'frozenColumnCount' in grid_properties else 0

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def get_headers(self, specify_header_row: int | None = None) -> tuple[list[str], int]:
        logger.debug(f'frozenRowCount: {self.frozenRowCount}')
        header_row = 1 if self.frozenRowCount == 0 else self.frozenRowCount

        header_row = specify_header_row if specify_header_row is not None else header_row
        # self.service.fetch_range("03-活動調查(所有學員)!R1C1:R10C10")
        header_row_range = f"'{self.title}'!R{header_row}C1:R{header_row}C{self.columnCount}"
        # print(header_row_range)
        result = self.service.fetch_range(header_row_range)
        # logger.debug(f'{result['values'][0]}')
        headers = [v.replace('\n', '') for v in result['values'][0]]
        logger.trace(f'{headers}')

        return headers, header_row


class GoogleSpreadsheetService:
    sheets: dict[str, dict[str, str | int | dict[str, int]]]
    spreadsheet_id: str

    def __init__(self, settings: PzProjectGoogleSpreadsheetConfig, secret_file: str) -> None:
        self.spreadsheet_id = settings.spreadsheet_id
        credentials = service_account.Credentials.from_service_account_file(secret_file, scopes=SCOPES)
        service = build("sheets", "v4", credentials=credentials)

        # Call the Sheets API
        self.sheet = service.spreadsheets()

        result = self.sheet.get(spreadsheetId=self.spreadsheet_id,
                                fields="properties.title,sheets.properties").execute()

        self.sheets = {entry['properties']['title']: entry['properties'] for entry in result['sheets']}
        # print(self.sheets)

    def get_sheet_by_title(self, title: str) -> Spreadsheet | None:
        if title in self.sheets:
            return Spreadsheet(self, self.sheets[title])
        return None

    def fetch_range_with_formula(self, sheet_range: str) -> list[list[SpreadsheetValueWithFormula]]:
        result = self.sheet.get(spreadsheetId=self.spreadsheet_id, ranges=sheet_range, includeGridData=True).execute()
        sheets = result.get('sheets', [])

        result_list: list[list[SpreadsheetValueWithFormula]] = []
        for sheet in sheets:
            data = sheet.get('data', [])
            for row_idx, row_data in enumerate(data[0].get('rowData', [])):
                row_list: list[SpreadsheetValueWithFormula] = []
                for col_idx, cell_data in enumerate(row_data.get('values', [])):
                    formula = cell_data.get('userEnteredValue', {}).get('formulaValue')
                    value = cell_data.get('formattedValue')
                    # if value is not None:
                    row_list.append(SpreadsheetValueWithFormula(value, formula))
                    # if formula:
                    #     print(f'Cell {cell_address} - Value: {value}, Formula: {formula}')
                    # elif value is not None:
                    #     print(f'Cell {cell_address} - Value: {value}')
                result_list.append(row_list)

        return result_list

    def fetch_range_with_unformatted_value(self, sheet_range: str) -> list[SpreadsheetValueData]:
        # print(sheet_range)
        formatted_values_request = self.sheet.values().get(
            spreadsheetId=self.spreadsheet_id, range=sheet_range, valueRenderOption='FORMATTED_VALUE'
        )
        formatted_values_response = formatted_values_request.execute()
        formatted_values = formatted_values_response.get('values', [])

        unformatted_values_request = self.sheet.values().get(
            spreadsheetId=self.spreadsheet_id, range=sheet_range, valueRenderOption='UNFORMATTED_VALUE'
        )
        unformatted_values_response = unformatted_values_request.execute()
        unformatted_values = unformatted_values_response.get('values', [])

        data: list[SpreadsheetValueData] = []
        for i in range(len(formatted_values)):
            data.append(SpreadsheetValueData(formatted_values[i], unformatted_values[i]))
        return data

    def fetch_range(self, sheet_range: str) -> dict[str, Any]:
        return self.sheet.values().get(spreadsheetId=self.spreadsheet_id, range=sheet_range).execute()

    def store_range(self, sheet_range: str, values: list[list[Any]]) -> None:
        """
        :param sheet_range:
        :param values:
        :return:

        values = [
            [
                # Cell values ...
            ],
            # Additional rows ...
        ]
        """
        result = (self.sheet.values().update(spreadsheetId=self.spreadsheet_id,
                                             range=sheet_range,
                                             valueInputOption='USER_ENTERED',
                                             body={"values": values}).execute())
        logger.info(f"{result.get('updatedCells')} cells updated.")


class SpreadsheetRangeInfo:
    title: str
    data_range: str
    indexes: list[int]
    starting_row: int
    starting_index: int
    number_of_rows: int
    number_of_columns: int

    def __init__(self, spreadsheet: Spreadsheet, title: str, col_names: list[str], header_row: int | None = None,
                 reverse_index: bool = False):
        self.title = title
        headers, h_row = spreadsheet.get_headers(header_row)
        logger.debug(f'headers: {header_row} {headers}, {h_row}')
        # print(headers)
        # indexes = [headers.index(col_name) for col_name in col_names]

        # for col_name in col_names:
        #     if
        if reverse_index:
            self.indexes = [len(headers) - 1 - headers[::-1].index(col_name) for col_name in col_names]
        else:
            self.indexes = [safe_index(headers, col_name, -1) for col_name in col_names]
            # self.indexes = [x for x in [safe_index(headers, col_name, -1) for col_name in col_names] if x >= 0]
        # my_list[::-1].index(element_to_find)
        # len(my_list) - 1 - last_occurrence_index
        logger.info(headers)

        self.starting_row = h_row + 1
        self.ending_row = spreadsheet.rowCount - 1
        self.starting_index = min([x for x in [safe_index(headers, col_name, -1) for col_name in col_names] if x >= 0])

        self.number_of_rows = spreadsheet.rowCount - self.starting_row
        self.number_of_columns = max(self.indexes) - self.starting_index + 1

        self.data_range = f"'{title}'!R{h_row + 1}C{self.starting_index + 1}:R{spreadsheet.rowCount}C{max(self.indexes) + 1}"

    def re_calculate_range(self, count: int) -> str:
        return f"'{self.title}'!R{self.starting_row}C{self.starting_index + 1}:R{count + self.starting_row }C{max(self.indexes) + 1}"


class SpreadsheetReadingService:
    service: GoogleSpreadsheetService

    def __init__(self, settings: PzProjectGoogleSpreadsheetConfig, secret_file: str) -> None:
        self.service = GoogleSpreadsheetService(settings, secret_file)

    # def _calculate_range(self, title: str, col_names: list[str], header_row: int | None = None,
    #                      reverse_index: bool = False) -> tuple[Spreadsheet | None, str, list[int]]:
    #     spreadsheet = self.service.get_sheet_by_title(title)
    #
    #     if spreadsheet is not None:
    #         headers, h_row = spreadsheet.get_headers(header_row)
    #         logger.debug(f'headers: {header_row} {headers}, {h_row}')
    #         # print(headers)
    #         # indexes = [headers.index(col_name) for col_name in col_names]
    #
    #         # for col_name in col_names:
    #         #     if
    #         if reverse_index:
    #             indexes = [len(headers) - 1 - headers[::-1].index(col_name) for col_name in col_names]
    #         else:
    #             indexes = [x for x in [safe_index(headers, col_name, -1) for col_name in col_names] if x >= 0]
    #         # my_list[::-1].index(element_to_find)
    #         # len(my_list) - 1 - last_occurrence_index
    #
    #         starting_index = min(indexes)
    #
    #         data_range = f"'{title}'!R{h_row + 1}C{starting_index + 1}:R{spreadsheet.rowCount}C{max(indexes) + 1}"
    #         return spreadsheet, data_range, indexes
    #     return None, "", []

    def read_sheet(self, title: str, col_names: list[str], header_row: int | None = None,
                   reverse_index: bool = False, read_formula: bool = False) -> list[list[SpreadsheetValueWithFormula]]:

        # spreadsheet, data_range, indexes = self._calculate_range(title, col_names, header_row=header_row,
        #                                                          reverse_index=reverse_index)

        spreadsheet = self.service.get_sheet_by_title(title)

        if spreadsheet is None:
            logger.error(f'{title} not found')
        else:
            range_info = SpreadsheetRangeInfo(spreadsheet, title, col_names, header_row=header_row,
                                              reverse_index=reverse_index)
            # headers, h_row = spreadsheet.get_headers(header_row)
            #
            # logger.debug(f'headers: {header_row} {headers}, {h_row}')
            # print(headers)
            # indexes = [headers.index(col_name) for col_name in col_names]

            # for col_name in col_names:
            #     if
            # if reverse_index:
            #     indexes = [len(headers) - 1 - headers[::-1].index(col_name) for col_name in col_names]
            # else:
            #     indexes = [x for x in [safe_index(headers, col_name, -1) for col_name in col_names] if x >= 0]
            # my_list[::-1].index(element_to_find)
            # len(my_list) - 1 - last_occurrence_index

            # starting_index = min(indexes)
            #
            # data_range = f"'{title}'!R{h_row + 1}C{starting_index + 1}:R{spreadsheet.rowCount}C{max(indexes) + 1}"
            # logger.debug(f'range: {data_range}')
            # result = self.service.data_range(f"'{self.title}'!R{header_row}C1:R{header_row}C{self.columnCount}")
            # print(range)

            indexes = range_info.indexes
            data_range = range_info.data_range
            starting_index = range_info.starting_index

            rows: list[list[SpreadsheetValueWithFormula]] = []

            if read_formula:
                results = self.service.fetch_range_with_formula(data_range)
                for row in results:
                    entry: list[SpreadsheetValueWithFormula] = []
                    for i in indexes:
                        if i >= 0 and i - starting_index <= len(row):
                            entry.append(row[i - starting_index])

                    if len([x for x in entry if x.value is not None]) > 0:
                        logger.trace(f'{[x.value for x in entry]}')
                        rows.append(entry)
            else:
                result = self.service.fetch_range(data_range)
                if 'values' in result:
                    for row in result['values']:
                        if row is not None and len(row) > 0:
                            entry = []
                            for i in indexes:
                                if i >= 0 and i - starting_index < len(row):
                                    entry.append(SpreadsheetValueWithFormula(row[i - starting_index], None))
                                else:
                                    entry.append(SpreadsheetValueWithFormula(None, None))
                            rows.append(entry)
            return rows

    def clear_sheet_data(self, title: str, col_names: list[str], header_row: int | None = None):
        spreadsheet = self.service.get_sheet_by_title(title)

        if spreadsheet is not None:
            info = SpreadsheetRangeInfo(spreadsheet, title, col_names, header_row=header_row)
            logger.debug(f'range: {info.data_range} ({info.number_of_rows}, {info.number_of_columns})')

            data = []
            for r in range(0, info.number_of_rows):
                entry = []
                for c in range(0, info.number_of_columns):
                    entry.append('')
                data.append(entry)
            self.service.store_range(info.data_range, data)

    def write_data(self, title: str, col_names: list[str], values: list[list[Any]], header_row: int | None = None):
        if len(values) > 0:
            spreadsheet = self.service.get_sheet_by_title(title)

            if spreadsheet is not None:
                info = SpreadsheetRangeInfo(spreadsheet, title, col_names, header_row=header_row)
                logger.trace(f'range: {info.data_range} ({info.number_of_rows}, {info.number_of_columns})')
                logger.trace(f'indexes: {info.indexes}')
                logger.trace(f'first: {values[0]}')

                data = []
                for value in values:
                    entry = [''] * info.number_of_columns
                    for i, v in enumerate(info.indexes):
                        try:
                            entry[v] = value[i]
                        except IndexError:
                            pass
                    # print(entry)
                    data.append(entry)

                r = info.re_calculate_range(len(values))

                # data = []
                # for r in range(0, len(values)):
                #     entry = []
                #     for c in range(0, info.number_of_columns):
                #         entry.append('')
                #     data.append(entry)
                self.service.store_range(r, data)
