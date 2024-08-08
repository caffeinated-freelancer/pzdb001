from loguru import logger

from pz.cloud.spreadsheet import SpreadsheetReadingService
from pz.config import PzProjectGoogleSpreadsheetConfig
from pz.models.google_member_relation import GoogleMemberRelation


class PzCloudSpreadsheetRelationsService:
    service: SpreadsheetReadingService

    def __init__(self, settings: PzProjectGoogleSpreadsheetConfig, secret_file: str):
        self.settings = settings
        self.service = SpreadsheetReadingService(settings, secret_file)

    def read_all(self) -> list[GoogleMemberRelation]:
        results = self.service.read_sheet(
            self.settings.sheet_name, GoogleMemberRelation.get_column_names(),
            header_row=self.settings.header_row, reverse_index=False)

        entries: list[GoogleMemberRelation] = []
        for result in results:
            model = GoogleMemberRelation([], raw_values=result)
            if model.realName is not None and len(model.realName) > 0:
                logger.trace(f'{result}')
                entries.append(model)
        return entries
