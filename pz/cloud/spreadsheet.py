import json
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from loguru import logger

from pz.config import PzProjectGoogleSpreadsheetConfig

# SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]
# SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/drive.file",
#           "https://www.googleapis.com/auth/spreadsheets"]
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


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


class SpreadsheetReadingService:
    service: GoogleSpreadsheetService

    def __init__(self, settings: PzProjectGoogleSpreadsheetConfig, secret_file: str) -> None:
        self.service = GoogleSpreadsheetService(settings, secret_file)

    def read_sheet(self, title: str, col_names: list[str], header_row: int | None = None,
                   reverse_index: bool = False, read_formula: bool = False) -> list[list[SpreadsheetValueWithFormula]]:
        spreadsheet = self.service.get_sheet_by_title(title)

        if spreadsheet is not None:
            headers, h_row = spreadsheet.get_headers(header_row)

            logger.debug(f'headers: {header_row} {headers}, {h_row}')
            # print(headers)
            # indexes = [headers.index(col_name) for col_name in col_names]

            # for col_name in col_names:
            #     if
            if reverse_index:
                indexes = [len(headers) - 1 - headers[::-1].index(col_name) for col_name in col_names]
            else:
                indexes = [headers.index(col_name) for col_name in col_names]
            # my_list[::-1].index(element_to_find)
            # len(my_list) - 1 - last_occurrence_index

            starting_index = min(indexes)

            data_range = f"'{title}'!R{h_row + 1}C{starting_index + 1}:R{spreadsheet.rowCount}C{max(indexes) + 1}"
            logger.debug(f'range: {data_range}')
            # result = self.service.data_range(f"'{self.title}'!R{header_row}C1:R{header_row}C{self.columnCount}")
            # print(range)

            rows: list[list[SpreadsheetValueWithFormula]] = []

            if read_formula:
                results = self.service.fetch_range_with_formula(data_range)
                for row in results:
                    entry: list[SpreadsheetValueWithFormula] = []
                    for i in indexes:
                        if i - starting_index <= len(row):
                            entry.append(row[i - starting_index])

                    if len([x for x in entry if x.value is not None]) > 0:
                        logger.trace(f'{[x.value for x in entry]}')
                        rows.append(entry)
            else:
                result = self.service.fetch_range(data_range)
                for row in result['values']:
                    if row is not None and len(row) > 0:
                        entry = []
                        for i in indexes:
                            if i - starting_index < len(row):
                                entry.append(SpreadsheetValueWithFormula(row[i - starting_index], None))
                            else:
                                entry.append(SpreadsheetValueWithFormula(None, None))
                        rows.append(entry)
            return rows
