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
        # results = service.read_sheet(PzMember.get_spreadsheet_title(), PzMember.get_column_names(), reverse_index=False)
        #
        # self.memberMap = {}
        # self.memberByName = {}
        # self.classMap = {}
        # self.allMembers = []
        #
        # for result in results:
        #     member = PzMember(result)
        #     if member.studentId is None or len(member.studentId) != 9 or re.match(r'\d{5}0000', member.studentId):
        #         print(member.to_json())
        #         continue
        #
        #     self.allMembers.append(member)
        #
        #     if member.studentId not in self.memberMap:
        #         self.memberMap[member.studentId] = [member]
        #     else:
        #         entry = self.memberMap[member.studentId]
        #         if entry[0].realName != member.realName:
        #             print(f'duplicate student id: [{member.studentId}]: {entry[0].fullName} vs {member.fullName}')
        #         else:
        #             self.memberMap[member.studentId].append(member)
        #     if member.realName not in self.memberByName:
        #         self.memberByName[member.realName] = [member]
        #     else:
        #         entries = self.memberByName[member.realName]
        #         for entry in entries:
        #             if entry.studentId != member.studentId:
        #                 self.memberByName[member.realName].append(member)
        #
        #     if member.className not in self.classMap:
        #         self.classMap[member.className] = PzClass(member.className)
        #
        #     pz_class = self.classMap[member.className]
        #     pz_class.add_class_group(member.classGroup, member.senior)

    def check_senior(self):
        for k, pz_class in self.classMap.items():
            logger.trace(f'{k}')
            for group_id, pz_class_group in pz_class.pzClassGroups.items():
                if pz_class_group.seniorName not in self.memberByName:
                    logger.info(f'   >>> {pz_class_group.groupId} {pz_class_group.seniorName} (Not found)')
                else:
                    members = self.memberByName[pz_class_group.seniorName]
                    if len(members) > 1:
                        logger.info(f'   >>> {pz_class_group.groupId} {pz_class_group.seniorName} (Multiple match {len(members)})')
                    else:
                        logger.info(f'   >>> {pz_class_group.groupId} {pz_class_group.seniorName}')

    # def get_all_members(self) ->list[PzMember]:
    #     return self.allMembers
    def read_all(self, model: GoogleSpreadSheetModelInterface) -> list[
        GoogleSpreadSheetModelInterface]:

        for i, col in enumerate(model.get_column_names()):
            logger.trace(f'{i} - {col}')

        results = self.service.read_sheet(model.get_spreadsheet_title(),
                                          model.get_column_names(),
                                          header_row=self.settings.header_row,
                                          reverse_index=False)

        # logger.warning(f'{results}')
        entries: list[GoogleSpreadSheetModelInterface] = []
        for result in results:
            logger.trace(f'{result}')
            entries.append(GoogleClassMemberModel(result))
        return entries
