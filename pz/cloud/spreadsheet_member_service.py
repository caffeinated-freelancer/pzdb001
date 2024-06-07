from pz.cloud.spreadsheet import SpreadsheetReadingService
from pz.models.google_class_member import GoogleClassMemberModel
from pz.models.google_spreadsheet_model import GoogleSpreadSheetModelInterface
from pz.models.pz_class import PzClass


class PzCloudSpreadsheetMemberService:
    service: SpreadsheetReadingService
    classMap: dict[str, PzClass]
    memberByName: dict[str, list[GoogleClassMemberModel]]
    memberMap: dict[str, list[GoogleClassMemberModel]]
    allMembers: list[GoogleClassMemberModel]

    def __init__(self, spreadsheet_id: str, secret_file: str):
        # PzMember.get_column_names()
        self.service = SpreadsheetReadingService(spreadsheet_id, secret_file)
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
            print(k)
            for group_id, pz_class_group in pz_class.pzClassGroups.items():
                if pz_class_group.seniorName not in self.memberByName:
                    print("   >>>", pz_class_group.groupId, pz_class_group.seniorName, " (Not found)")
                else:
                    members = self.memberByName[pz_class_group.seniorName]
                    if len(members) > 1:
                        print("   >>>", pz_class_group.groupId, pz_class_group.seniorName,
                              f' (Multiple match {len(members)})')
                    else:
                        print("   >>>", pz_class_group.groupId, pz_class_group.seniorName)

    # def get_all_members(self) ->list[PzMember]:
    #     return self.allMembers
    def read_all(self, model: GoogleSpreadSheetModelInterface) -> list[GoogleSpreadSheetModelInterface]:
        results = self.service.read_sheet(model.get_spreadsheet_title(), model.get_column_names(), reverse_index=False)
        entries = []
        for result in results:
            entries.append(GoogleClassMemberModel(result))
        return entries
