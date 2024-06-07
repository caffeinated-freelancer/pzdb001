from collections import OrderedDict
from typing import Callable

from pz.cloud.spreadsheet_member_service import PzCloudSpreadsheetMemberService
from pz.comparators import class_member_comparator
from pz.config import PzProjectConfig, PzProjectGoogleSpreadsheetConfig
from pz.models.google_class_member import GoogleClassMemberModel
from pz.models.member_in_access import MemberInAccessDB
from pz.models.mysql_class_member_entity import MysqlClassMemberEntity
from pz.models.mysql_member_detail_entity import MysqlMemberDetailEntity
from pz.models.pz_class import PzClass
from pz.utils import full_name_to_names
from services.member_merging_service import MemberMergingService
from services.mysql_import_and_fetching import MySqlImportAndFetchingService


class PzGrandMemberService:
    config: PzProjectConfig
    mysql_service: MySqlImportAndFetchingService
    member_details_by_name: dict[str, list[MysqlMemberDetailEntity]]
    class_members_by_name: dict[str, list[MysqlClassMemberEntity]]
    all_classes: OrderedDict[str, PzClass]
    deacon_members_by_name: OrderedDict[str, list[MysqlClassMemberEntity]]
    senior_by_student_id: dict[int, MysqlClassMemberEntity]

    def __init__(self, config: PzProjectConfig, from_access: bool = False, from_google: bool = False):
        self.config = config

        self.mysql_service = MySqlImportAndFetchingService(self.config)

        if from_google:
            self.init_class_members(self.read_class_members_from_google)
        else:
            self.init_class_members(self.read_class_members_from_mysql)

        if from_access:
            self.init_member_details(self.read_member_details_from_access)
        else:
            self.init_member_details(self.read_member_details_from_mysql)

    def init_member_details(self, fetching_function: Callable[[], list[MysqlMemberDetailEntity]]):
        self.member_details_by_name = {}

        entities = fetching_function()

        for entity in entities:
            if entity.real_name in self.member_details_by_name:
                self.member_details_by_name[entity.real_name].append(entity)
            else:
                self.member_details_by_name[entity.real_name] = [entity]

    def init_class_members(self, fetching_function: Callable[[], list[MysqlClassMemberEntity]]):
        self.class_members_by_name = {}
        self.all_classes = OrderedDict()
        self.deacon_members_by_name = OrderedDict()
        self.senior_by_student_id = {}
        entities = fetching_function()

        for entity in entities:
            if entity.real_name in self.class_members_by_name:
                self.class_members_by_name[entity.real_name].append(entity)
            else:
                self.class_members_by_name[entity.real_name] = [entity]

            if entity.deacon is not None and entity.deacon != '':
                if entity.real_name not in self.deacon_members_by_name:
                    self.deacon_members_by_name[entity.real_name] = [entity]
                else:
                    self.deacon_members_by_name[entity.real_name].append(entity)

            if entity.class_name is not None:
                if entity.class_name not in self.all_classes:
                    self.all_classes[entity.class_name] = PzClass(entity.class_name)
                pz_class = self.all_classes[entity.class_name]
                pz_class.add_class_group(entity.class_group, entity.senior)

        for pz_class in self.all_classes.values():
            for group_id, pz_class_group in pz_class.pzClassGroups.items():
                if pz_class_group.seniorName in self.deacon_members_by_name:
                    for entity in self.deacon_members_by_name[pz_class_group.seniorName]:
                        if pz_class_group.seniorDharmaName != '' and pz_class_group.seniorDharmaName == entity.dharma_name:
                            pz_class_group.set_senior_id(entity.student_id)
                            self.senior_by_student_id[entity.student_id] = entity
                            entity.is_senior = True
                            break
                        elif pz_class.pzClassName == entity.class_name and group_id == entity.class_group:
                            pz_class_group.set_senior_id(entity.student_id)
                            self.senior_by_student_id[entity.student_id] = entity
                            entity.is_senior = True
                            break
        for pz_class in self.all_classes.values():
            for group_id, pz_class_group in pz_class.pzClassGroups.items():
                if pz_class_group.seniorStudentId == 0:
                    match_list = self.class_members_by_name.get(pz_class_group.seniorName)
                    if match_list is not None:
                        if len(match_list) == 1:
                            pz_class_group.set_senior_id(match_list[0].student_id)
                            self.senior_by_student_id[match_list[0].student_id] = match_list[0]
                            match_list[0].is_senior = True
                        elif len(match_list) > 1:
                            pz_class_group.set_senior_id(match_list[0].student_id)
                            self.senior_by_student_id[match_list[0].student_id] = match_list[0]
                            match_list[0].is_senior = True
                            print(
                                f'Warning! Senior {pz_class_group.seniorName} ({pz_class.pzClassName} / {group_id}) multiple match')
                    else:
                        print(
                            f'Warning! Senior {pz_class_group.seniorName} not found ({pz_class.pzClassName} / {group_id})')

    def find_member_details_by_name(self, name: str) -> list[MysqlMemberDetailEntity]:
        found = self.member_details_by_name.get(name)
        return found if found is not None else []

    def find_class_member_by_name(self, name: str) -> list[MysqlClassMemberEntity]:
        found = self.class_members_by_name.get(name)
        return found if found is not None else []

    def find_member_details_by_pz_name(self, full_name: str) -> list[MysqlMemberDetailEntity]:
        real_name, dharma_name = full_name_to_names(full_name)
        match_list = self.find_member_details_by_name(real_name)

        if len(match_list) > 1 and dharma_name != '':
            for member in match_list:
                if member.dharma_name == dharma_name:
                    return [member]
            return []

        return match_list

    def find_class_member_by_pz_name(self, full_name: str) -> list[MysqlClassMemberEntity]:
        real_name, dharma_name = full_name_to_names(full_name)
        match_list = self.find_class_member_by_name(real_name)

        if len(match_list) > 1 and dharma_name != '':
            for member in match_list:
                if member.dharma_name == dharma_name:
                    return [member]
            return []

        return match_list

    def find_grand_member_by_pz_name(self, full_name: str) -> list[
        tuple[MysqlMemberDetailEntity, MysqlClassMemberEntity]]:
        class_members = self.find_class_member_by_pz_name(full_name)
        member_details = self.find_member_details_by_pz_name(full_name)

        results = []
        for m1 in member_details:
            for m2 in class_members:
                if m1.id == m2.student_id:
                    results.append((m1, m2))

        # print(results)
        return results

    def find_one_class_member_by_pz_name(self, full_name: str) -> MysqlClassMemberEntity | None:
        results = [x[1] for x in self.find_grand_member_by_pz_name(full_name)]

        if len(results) == 1:
            return results[0]
        elif len(results) > 1:
            sorted_list = sorted(results, key=class_member_comparator)
            return sorted_list[0]
        else:
            return None

    def read_class_members_from_mysql(self) -> list[MysqlClassMemberEntity]:
        return self.mysql_service.read_google_class_members()

    def read_class_members_from_google(self) -> list[MysqlClassMemberEntity]:
        settings: PzProjectGoogleSpreadsheetConfig = self.config.google.spreadsheets.get('class_members')

        if settings is not None:
            service = PzCloudSpreadsheetMemberService(settings.spreadsheet_id, self.config.google.secret_file)
            results: list[GoogleClassMemberModel] = service.read_all(GoogleClassMemberModel([]))
            entities = []
            for result in results:
                entities.append(MysqlClassMemberEntity([], [], google_member_detail=result))
            return entities
        else:
            return []

    def read_member_details_from_mysql(self) -> list[MysqlMemberDetailEntity]:
        return self.mysql_service.read_member_details()

    def read_member_details_from_access(self) -> list[MysqlMemberDetailEntity]:
        service = MemberMergingService(self.config.ms_access_db.db_file, self.config.ms_access_db.target_table)
        cols, results = service.read_all()

        entities = []

        for result in results:
            entity = MysqlMemberDetailEntity.from_access_db(MemberInAccessDB(cols, result))
            entities.append(entity)

        return entities
