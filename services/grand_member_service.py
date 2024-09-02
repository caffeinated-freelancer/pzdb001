import functools
from collections import OrderedDict
from typing import Callable

from loguru import logger

from pz.cloud.spreadsheet_member_service import PzCloudSpreadsheetMemberService
from pz.comparators import deacon_based_class_member_comparator, deacon_based_class_member_comparator_for_tuple
from pz.config import PzProjectConfig, PzProjectGoogleSpreadsheetConfig
from pz.models.google_class_member import GoogleClassMemberModel
from pz.models.member_in_access import MemberInAccessDB
from pz.models.mysql_class_member_entity import MysqlClassMemberEntity
from pz.models.mysql_member_detail_entity import MysqlMemberDetailEntity
from pz.models.pz_class import PzClass
from pz.utils import full_name_to_names, names_to_pz_full_name
from services.access_db_service import AccessDbService
from services.member_merging_service import MemberMergingService
from services.mysql_import_and_fetching import MySqlImportAndFetchingService


class PzGrandMemberService:
    config: PzProjectConfig
    mysql_service: MySqlImportAndFetchingService | None
    member_details_by_name: dict[str, list[MysqlMemberDetailEntity]]
    member_details_by_student_id: dict[int, MysqlMemberDetailEntity]
    class_members_by_name: dict[str, list[MysqlClassMemberEntity]]
    class_members_by_student_id: dict[int, list[MysqlClassMemberEntity]]
    all_classes: OrderedDict[str, PzClass]
    deacon_members_by_name: OrderedDict[str, list[MysqlClassMemberEntity]]
    senior_by_student_id: dict[int, MysqlClassMemberEntity]
    senior_by_class_and_group: dict[str, MysqlClassMemberEntity]
    all_seniors: list[MysqlClassMemberEntity]
    all_class_members: list[MysqlClassMemberEntity]

    def __init__(self, config: PzProjectConfig, from_access: bool = False, from_google: bool = False,
                 all_via_access_db: bool = False):
        self.config = config

        if all_via_access_db:
            self.mysql_service = None
        else:
            self.mysql_service = MySqlImportAndFetchingService(self.config)

        self.senior_by_class_and_group = {}

        if from_google:
            self.init_class_members(self.read_class_members_from_google)
        elif all_via_access_db:
            self.init_class_members(self.read_class_members_from_access)
        else:
            self.init_class_members(self.read_class_members_from_mysql)

        if from_access or all_via_access_db:
            self.init_member_details(self.read_member_details_from_access)
        else:
            self.init_member_details(self.read_member_details_from_mysql)

    def init_member_details(self, fetching_function: Callable[[], list[MysqlMemberDetailEntity]]):
        self.member_details_by_name = {}
        self.member_details_by_student_id = {}

        entities = fetching_function()

        for entity in entities:
            if entity.real_name in self.member_details_by_name:
                self.member_details_by_name[entity.real_name].append(entity)
            else:
                self.member_details_by_name[entity.real_name] = [entity]

            try:
                self.member_details_by_student_id[int(entity.student_id)] = entity
            except:
                pass

    def init_class_members(self, fetching_function: Callable[[], list[MysqlClassMemberEntity]]):
        self.class_members_by_name = {}
        self.all_classes = OrderedDict()
        self.deacon_members_by_name = OrderedDict()
        self.senior_by_student_id = {}
        self.class_members_by_student_id = {}
        self.all_class_members = fetching_function()

        for entity in self.all_class_members:
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

            if entity.student_id in self.class_members_by_student_id:
                self.class_members_by_student_id[entity.student_id].append(entity)
                # print(f'{entity.student_id} {entity.class_name} {entity.senior}')
            else:
                self.class_members_by_student_id[entity.student_id] = [entity]

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
                            logger.warning(
                                f'Warning! Senior {pz_class_group.seniorName} ({pz_class.pzClassName} / {group_id}) multiple match')
                    else:
                        logger.warning(
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

    def find_relax_grand_member_by_pz_name(self, full_name: str, debug: bool = False) -> list[
        tuple[MysqlMemberDetailEntity, MysqlClassMemberEntity]]:
        class_members = self.find_class_member_by_pz_name(full_name)
        member_details = self.find_member_details_by_pz_name(full_name)

        results = []

        if len(class_members) == 0 and len(member_details) == 0:
            pass
        elif len(member_details) != 0:
            for member_detail in member_details:
                results.append((member_detail, None))
        else:
            for m1 in member_details:
                if debug:
                    logger.warning(f'{m1.to_json()}')
                for m2 in class_members:
                    if debug:
                        logger.warning(f'{m2.to_json()}')
                    if m1.id == m2.student_id:
                        results.append((m1, m2))
        return results

    def find_grand_member_by_pz_name(self, full_name: str, debug: bool = False) -> list[
        tuple[MysqlMemberDetailEntity, MysqlClassMemberEntity]]:
        class_members = self.find_class_member_by_pz_name(full_name)
        member_details = self.find_member_details_by_pz_name(full_name)

        results = []

        if len(member_details) == 0 and len(class_members) > 0:
            for m2 in class_members:
                results.append((None, m2))
        else:
            for m1 in member_details:
                if debug:
                    logger.warning(f'{m1.to_json()}')
                for m2 in class_members:
                    if debug:
                        logger.warning(f'{m2.to_json()}')
                    if m1.id == m2.student_id:
                        results.append((m1, m2))
            if len(results) == 0 and len(class_members) > 0:
                for m2 in class_members:
                    results.append((None, m2))

        # print(results)
        return results

    def find_grand_member_by_pz_name_and_dharma_name(self, full_name: str, dharma_name: str | None, gender: str) -> \
            tuple[MysqlMemberDetailEntity, MysqlClassMemberEntity] | None:
        results = self.find_grand_member_by_pz_name(full_name)
        for result in results:
            if result[0] is not None and result[0].dharma_name == dharma_name and result[0].gender == gender:
                return result

        return None

    def find_class_member_by_student_id(self, student_id: int) -> list[MysqlClassMemberEntity] | None:
        if student_id in self.class_members_by_student_id:
            return self.class_members_by_student_id[student_id]
        return None

    def find_member_details_by_student_id(self, student_id: int) -> MysqlMemberDetailEntity | None:
        if student_id in self.member_details_by_student_id:
            return self.member_details_by_student_id[student_id]
        return None

    def find_grand_member_by_student_id(self, student_id: int, prefer: str = None) -> tuple[
                                                                                          MysqlMemberDetailEntity, MysqlClassMemberEntity] | None:
        class_members = self.find_class_member_by_student_id(student_id)
        member_details = self.find_member_details_by_student_id(student_id)

        if class_members is not None or member_details is not None:
            class_member = class_members[0] if class_members is not None else None
            if prefer is not None and class_members is not None:
                for m in class_members:
                    if m.class_name == prefer:
                        return member_details, m
                logger.warning(f'{student_id} / {class_member.real_name}: {prefer} not found')
            return member_details, class_member
        return None

    def find_all_grand_member_by_student_id(self, student_id: int) -> list[
        tuple[MysqlMemberDetailEntity, MysqlClassMemberEntity]]:
        class_members = self.find_class_member_by_student_id(student_id)

        if class_members is None or len(class_members) == 1:
            result = self.find_grand_member_by_student_id(student_id)
            return [result] if result is not None else []

        member_details = self.find_member_details_by_student_id(student_id)

        results = []
        for class_member in class_members:
            results.append((member_details, class_member))

        # if len(results) > 0:
        #     print(f'{results[0][1].class_name} vs {results[1][1].class_name}')

        return results

    @staticmethod
    def perform_find_one(results: list[MysqlClassMemberEntity],
                         dharma_name: str | None = None) -> MysqlClassMemberEntity | None:
        if results is None:
            return None

        if dharma_name is not None and dharma_name != '':
            results = [x for x in results if x.dharma_name == dharma_name]

        if len(results) == 1:
            return results[0]
        elif len(results) > 1:
            student_ids: dict[int, MysqlClassMemberEntity] = {}

            for result in results:
                if result.student_id not in student_ids:
                    student_ids[result.student_id] = result
            if len(student_ids) > 1:
                logger.warning(f'注意! {results[0].real_name} 有 {len(student_ids)
                } 個學員符合: {[f'{x.student_id}/{x.dharma_name if x.dharma_name is not None else ''
                }/{x.class_name}/{x.class_group}' for x in student_ids.values()]}')
            # sorted_list = sorted(results, key=class_member_comparator)
            sorted_list = sorted(results, key=functools.cmp_to_key(deacon_based_class_member_comparator))
            return sorted_list[0]
        else:
            return None

    @staticmethod
    def perform_find_grand_one(
            results: list[tuple[MysqlMemberDetailEntity, MysqlClassMemberEntity]],
            dharma_name: str | None = None) -> tuple[MysqlMemberDetailEntity, MysqlClassMemberEntity] | None:
        if results is None:
            return None

        if dharma_name is not None and dharma_name != '':
            results = [x for x in results if x[1].dharma_name == dharma_name]

        if len(results) == 1:
            return results[0]
        elif len(results) > 1:
            student_ids: dict[int, tuple[MysqlMemberDetailEntity, MysqlClassMemberEntity]] = {}

            for result in results:
                if result[1].student_id not in student_ids:
                    student_ids[result[1].student_id] = result
            if len(student_ids) > 1:
                logger.warning(f'注意! {results[0][1].real_name} 有 {len(student_ids)
                } 個學員符合: {[f'{x[1].student_id}/{x[1].dharma_name if x[1].dharma_name is not None else ''
                }/{x[1].class_name}/{x[1].class_group}' for x in student_ids.values()]}')
            # sorted_list = sorted(results, key=class_member_comparator)
            sorted_list = sorted(results, key=functools.cmp_to_key(deacon_based_class_member_comparator_for_tuple))
            return sorted_list[0]
        else:
            return None

    def find_one_class_member_by_pz_name(self, full_name: str, debug: bool = False) -> MysqlClassMemberEntity | None:
        _, dharma_name = full_name_to_names(full_name)
        results = [x[1] for x in self.find_grand_member_by_pz_name(full_name, debug=debug)]
        if debug:
            logger.warning(f'{full_name}: {results}')
        return self.perform_find_one(results, dharma_name=dharma_name)
        #
        # if len(results) == 1:
        #     return results[0]
        # elif len(results) > 1:
        #     # sorted_list = sorted(results, key=class_member_comparator)
        #     sorted_list = sorted(results, key=functools.cmp_to_key(deacon_based_class_member_comparator))
        #     return sorted_list[0]
        # else:
        #     return None

    def find_one_class_member_by_names(self, real_name: str, dharma_name: str | None,
                                       debug: bool = False) -> MysqlClassMemberEntity | None:
        full_name = names_to_pz_full_name(real_name, dharma_name)
        if debug:
            logger.warning(f'{full_name}')
        return self.find_one_class_member_by_pz_name(full_name, debug=debug)

    def find_one_class_member_by_names_with_warning(
            self, real_name: str, dharma_name: str | None,
            debug: bool = False) -> tuple[tuple[MysqlMemberDetailEntity, MysqlClassMemberEntity] | None, list[str]]:
        full_name = names_to_pz_full_name(real_name, dharma_name)
        if debug:
            logger.warning(f'{full_name}')

        # results = [x[1] for x in self.find_grand_member_by_pz_name(full_name, debug=debug)]
        results: list[tuple[MysqlMemberDetailEntity, MysqlClassMemberEntity]] = self.find_grand_member_by_pz_name(
            full_name, debug=debug)

        warnings: list[str] = []

        have_reduced = False
        while len(results) > 1:
            student_ids: set[int] = set()
            for r in results:
                student_ids.add(r[1].student_id)

            if len(student_ids) > 1:
                if not have_reduced and (dharma_name is None or dharma_name == ''):
                    new_results = [x for x in results if x[1].dharma_name is None or x[1].dharma_name == '']
                    if len(new_results) != len(results) and len(new_results) > 0:
                        have_reduced = True
                        warnings.append(
                            f'{full_name} 同名同姓有 {len(results)} 人, 因沒有設定法名, 所以選取沒有法名的 {[f'{x[1].student_id}/{x[1].dharma_name}/{x[1].class_name}/{x[1].class_group}' for x in results]}')
                        logger.warning(
                            f'reduce: {full_name}: {[f'{x[1].student_id}/{x[1].real_name}/{x[1].dharma_name}/{x[1].class_name}' for x in results]}')
                        results = new_results
                        continue
                logger.warning(
                    f'{full_name}: {[f'{x[1].student_id}/{x[1].real_name}/{x[1].dharma_name}/{x[1].class_name}' for x in results]}')
                warnings.append(
                    f'{full_name} 同名同姓有 {len(results)} 人, 系統挑選的不一定是正確的, 試著指定法名 {[f'{x[1].student_id}/{x[1].dharma_name}/{x[1].class_name}/{x[1].class_group}' for x in results]}')
            break

        return self.perform_find_grand_one(results, dharma_name=dharma_name), warnings

    def find_one_class_member_by_student_id(self, student_id: int) -> MysqlClassMemberEntity | None:
        results = self.find_class_member_by_student_id(student_id)
        return self.perform_find_one(results)

    def find_one_grand_member_by_student_id(
            self, student_id: int) -> tuple[MysqlMemberDetailEntity, MysqlClassMemberEntity] | None:
        results = self.find_all_grand_member_by_student_id(student_id)
        if results is not None:
            return self.perform_find_grand_one(results)
        return None

    def read_class_members_from_mysql(self) -> list[MysqlClassMemberEntity]:
        return self.mysql_service.read_google_class_members()

    def read_class_members_from_google(self) -> list[MysqlClassMemberEntity]:
        settings: PzProjectGoogleSpreadsheetConfig = self.config.google.spreadsheets.get('class_members')

        GoogleClassMemberModel.remap_variables(settings.fields_map)

        if settings is not None:
            service = PzCloudSpreadsheetMemberService(settings, self.config.google.secret_file)
            results: list[GoogleClassMemberModel] = service.read_all(GoogleClassMemberModel([]), settings.sheet_name)
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

    def read_class_members_from_access(self) -> list[MysqlClassMemberEntity]:
        service = AccessDbService(self.config)
        return service.read_all_members_as_mysql()

    @staticmethod
    def class_group_as_key(class_name: str, class_group: int):
        return f'{class_name}_{class_group}'

    def _read_senior_into_cache(self):
        if len(self.senior_by_class_and_group) == 0:
            self.all_seniors = self.mysql_service.read_current_seniors()

            for senior in self.all_seniors:
                key = self.class_group_as_key(senior.class_name, senior.class_group)

                self.senior_by_class_and_group[key] = senior

    def read_all_seniors(self) -> list[MysqlClassMemberEntity]:
        self._read_senior_into_cache()
        return self.all_seniors

    def fetch_all_class_members(self) -> list[MysqlClassMemberEntity]:
        return self.all_class_members
