import json
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from loguru import logger

# SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]
# SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/drive.file",
#           "https://www.googleapis.com/auth/spreadsheets"]
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


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
        header_row = 1 if self.frozenRowCount == 0 else self.frozenRowCount

        header_row = specify_header_row if specify_header_row is not None else header_row
        # self.service.fetch_range("03-活動調查(所有學員)!R1C1:R10C10")
        header_row_range = f"'{self.title}'!R{header_row}C1:R{header_row}C{self.columnCount}"
        # print(header_row_range)
        result = self.service.fetch_range(header_row_range)
        return result['values'][0], header_row


class GoogleSpreadsheetService:
    sheets: dict[str, dict[str, str | int | dict[str, int]]]
    spreadsheet_id: str

    def __init__(self, spreadsheet_id: str, secret_file: str) -> None:
        self.spreadsheet_id = spreadsheet_id
        credentials = service_account.Credentials.from_service_account_file(secret_file, scopes=SCOPES)
        service = build("sheets", "v4", credentials=credentials)

        # Call the Sheets API
        self.sheet = service.spreadsheets()

        result = self.sheet.get(spreadsheetId=spreadsheet_id,
                                fields="properties.title,sheets.properties").execute()

        self.sheets = {entry['properties']['title']: entry['properties'] for entry in result['sheets']}
        # print(self.sheets)

    def get_sheet_by_title(self, title: str) -> Spreadsheet | None:
        if title in self.sheets:
            return Spreadsheet(self, self.sheets[title])
        return None

    def fetch_range(self, sheet_range: str) -> dict[str, Any]:
        # print(sheet_range)
        return self.sheet.values().get(spreadsheetId=self.spreadsheet_id, range=sheet_range).execute()


class SpreadsheetReadingService:
    service: GoogleSpreadsheetService

    def __init__(self, spreadsheet_id: str, secret_file: str) -> None:
        self.service = GoogleSpreadsheetService(spreadsheet_id, secret_file)

    def read_sheet(self, title: str, col_names: list[str], header_row: int | None = None,
                   reverse_index: bool = False) -> list[list[Any]]:
        spreadsheet = self.service.get_sheet_by_title(title)

        if spreadsheet is not None:
            headers, h_row = spreadsheet.get_headers(header_row)

            logger.warning(f'headers: {headers}, {h_row}')
            # print(headers)
            # indexes = [headers.index(col_name) for col_name in col_names]
            if reverse_index:
                indexes = [len(headers) - 1 - headers[::-1].index(col_name) for col_name in col_names]
            else:
                indexes = [headers.index(col_name) for col_name in col_names]
            # my_list[::-1].index(element_to_find)
            # len(my_list) - 1 - last_occurrence_index

            starting_index = min(indexes)

            range = f"'{title}'!R{h_row + 1}C{starting_index + 1}:R{spreadsheet.rowCount}C{max(indexes) + 1}"
            # result = self.service.fetch_range(f"'{self.title}'!R{header_row}C1:R{header_row}C{self.columnCount}")
            # print(range)

            result = self.service.fetch_range(range)
            rows = []
            # print(indexes)
            # print(col_names)
            for row in result['values']:
                if row is not None and len(row) > 0:
                    entry = []
                    for i in indexes:
                        if i - starting_index < len(row):
                            entry.append(row[i - starting_index])
                        else:
                            entry.append(None)
                    # print(row)
                    # print(entry)
                    rows.append(entry)
            return rows
