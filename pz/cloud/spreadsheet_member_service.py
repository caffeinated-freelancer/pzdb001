from loguru import logger

from pz.cloud.spreadsheet import SpreadsheetReadingService
from pz.config import PzProjectGoogleSpreadsheetConfig
from pz.models.google_class_member import GoogleClassMemberModel
from pz.models.google_spreadsheet_model import GoogleSpreadSheetModelInterface
from pz.models.pz_class import PzClass


class PzCloudSpreadsheetMemberService:
    service: SpreadsheetReadingService
    classMap: dict[str, PzClass]
    memberByName: dict[str, list[GoogleClassMemberModel]]
    memberMap: dict[str, list[GoogleClassMemberModel]]
    allMembers: list[GoogleClassMemberModel]
    settings: PzProjectGoogleSpreadsheetConfig

    def __init__(self, settings: PzProjectGoogleSpreadsheetConfig, secret_file: str):
        self.settings = settings
        # PzMember.get_column_names()
        self.service = SpreadsheetReadingService(settings, secret_file)

    def check_senior(self):
        for k, pz_class in self.classMap.items():
            logger.trace(f'{k}')
            for group_id, pz_class_group in pz_class.pzClassGroups.items():
                if pz_class_group.seniorName not in self.memberByName:
                    logger.info(f'   >>> {pz_class_group.groupId} {pz_class_group.seniorName} (Not found)')
                else:
                    members = self.memberByName[pz_class_group.seniorName]
                    if len(members) > 1:
                        logger.info(
                            f'   >>> {pz_class_group.groupId} {pz_class_group.seniorName} (Multiple match {len(members)})')
                    else:
                        logger.info(f'   >>> {pz_class_group.groupId} {pz_class_group.seniorName}')

    # def get_all_members(self) ->list[PzMember]:
    #     return self.allMembers
    def read_all(self, model: GoogleSpreadSheetModelInterface, spreadsheet_title: str, check_formula: bool = False) -> list[
        GoogleSpreadSheetModelInterface]:

        for i, col in enumerate(model.get_column_names()):
            logger.trace(f'{i} - {col}')

        results = self.service.read_sheet(
            spreadsheet_title, model.get_column_names(),
            header_row=self.settings.header_row, read_formula=check_formula, reverse_index=False)

        # logger.warning(f'{results}')
        entries: list[GoogleSpreadSheetModelInterface] = []
        for result in results:
            model = GoogleClassMemberModel([], raw_values=result)
            if model.realName is not None and len(model.realName) > 0:
                logger.trace(f'{result}')
                entries.append(model)
        return entries

    def clear_all(self, model: GoogleSpreadSheetModelInterface):
        self.service.clear_sheet_data(
            self.settings.sheet_name, model.get_column_names(),
            header_row=self.settings.header_row)

    def write_data(self, models: list[GoogleSpreadSheetModelInterface]):
        if len(models) > 0:

            data = []
            for model in models:
                entry = []
                for column_name in model.get_variable_names():
                    entry.append(model.__dict__[column_name])
                data.append(entry)

            self.service.write_data(
                self.settings.sheet_name, models[0].get_column_names(),
                data,
                header_row=self.settings.header_row)
