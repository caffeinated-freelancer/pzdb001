import json
import re
from typing import Callable

from loguru import logger

from pz.cloud.spreadsheet_member_service import PzCloudSpreadsheetMemberService
from pz.cloud.spreadsheet_relations_service import PzCloudSpreadsheetRelationsService
from pz.config import PzProjectConfig, PzProjectGoogleSpreadsheetConfig
from pz.models.general_processing_error import GeneralProcessingError
from pz.models.google_class_member import GoogleClassMemberModel
from pz.models.google_member_relation import GoogleMemberRelation
from pz.models.member_detail_model import MemberDetailModel
from pz.models.member_in_access import MemberInAccessDB
from pz.models.mysql_class_member_entity import MysqlClassMemberEntity
from pz.models.mysql_member_detail_entity import MysqlMemberDetailEntity
from pz.models.mysql_member_relation_entity import MysqlMemberRelationEntity
from pz.models.vertical_member_lookup_result import VerticalMemberLookupResult
from pz.mysql.db import PzMysqlDatabase
from pz.utils import full_name_to_real_name, simple_phone_number_normalization
from services.member_merging_service import MemberMergingService


class MySqlEntityHelper:
    clazz: type

    def __init__(self, clazz: type):
        self.clazz = clazz

    def write(self, entity):
        pass


class MySqlImportAndFetchingService:
    config: PzProjectConfig
    db: PzMysqlDatabase
    current_table: str
    previous_table: str

    def __init__(self, config: PzProjectConfig):
        self.config = config
        self.db = PzMysqlDatabase(config.mysql)
        self.current_table = f'class_members_{self.config.semester}'
        self.previous_table = f'class_members_{self.config.previous_semester}'

    def access_db_member_to_mysql(self, service: MemberMergingService) -> int:
        # cols, results = service.read_all()

        columns = []
        insert_columns = ['`id`']
        insert_values = ['%s']
        for k, v in MemberInAccessDB.ATTRIBUTES_MAP.items():
            columns.append(f'`{v}` VARCHAR(255) COMMENT \'{k}\',')
            insert_columns.append(f'`{v}`')
            insert_values.append('%s')

        query = (f'''
            CREATE TABLE IF NOT EXISTS `member_details` (
                id INT NOT NULL COMMENT 'Student ID',
                {"\n".join(columns)}
                PRIMARY KEY (`student_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                 ''')

        self._drop_table('member_details')

        self.db.perform_update(query)

        cols, results = service.read_all()

        query = f'INSERT INTO `member_details` ({",".join(insert_columns)}) VALUES ({",".join(insert_values)})'
        # print(query)

        params = []
        for result in results:
            entry = MemberInAccessDB(cols, result)
            param = [int(entry.student_id)]
            for _, v in MemberInAccessDB.ATTRIBUTES_MAP.items():
                value = entry.__getattribute__(v)
                if v.endswith('_phone'):
                    value = simple_phone_number_normalization(value)

                param.append(value)
            # print(param)
            params.append(tuple(param))

        supplier = (lambda y=x: x for x in params)
        self.db.prepared_update(query, supplier)

        logger.info(f'>>> {len(params)} 筆資料匯入')
        return len(params)

    def _drop_table(self, table_name: str):
        try:
            self.db.perform_update(f'DROP TABLE IF EXISTS `{table_name}`')
        except Exception as ignored:
            pass

    def _rename_table(self, from_name: str, to_name: str):
        try:
            self.db.perform_update(f'ALTER TABLE `{from_name}` RENAME TO `{to_name}`')
        except Exception as ignored:
            pass

    def _backup_table(self, current_table: str):
        number_of_backups = 3

        from_table = f'{current_table}_{number_of_backups + 1}'
        self._drop_table(from_table)

        for i in range(number_of_backups, 0, -1):
            try:
                to_table = from_table
                from_table = f'{current_table}_{i}'
                self._rename_table(from_table, to_table)
            except Exception as ignored:
                pass
        self._rename_table(current_table, from_table)

    def google_class_members_to_mysql(self, check_formula: bool = False) -> int:
        settings: PzProjectGoogleSpreadsheetConfig = self.config.google.spreadsheets.get('class_members')

        if settings is not None:

            GoogleClassMemberModel.remap_variables(settings.fields_map)
            service = PzCloudSpreadsheetMemberService(settings, self.config.google.secret_file)

            query = (f'''
CREATE TABLE `{self.current_table}`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `student_id` int NOT NULL COMMENT '學員編號',
  `class_name` varchar(5) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '班級',
  `class_group` int NOT NULL COMMENT '組別',
  `senior` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '學長',
  `real_name` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '姓名',
  `dharma_name` varchar(2) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '法名',
  `deacon` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '執事',
  `gender` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '性別',
  `next_classes` json DEFAULT NULL COMMENT '升班調查',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `student_id` (`student_id`,`class_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
            ''')

            self._backup_table(self.current_table)
            self.db.perform_update(query)

            columns_insert = ','.join([f'`{k}`' for k in MysqlClassMemberEntity.VARIABLE_MAP.keys()])
            values_insert = ','.join(['%s' for _ in MysqlClassMemberEntity.VARIABLE_MAP.keys()])
            query = f'INSERT INTO `{self.current_table}` ({columns_insert}) VALUES ({values_insert})'
            logger.info(f'Query: {query}')

            members: list[GoogleClassMemberModel] = service.read_all(
                GoogleClassMemberModel([]), check_formula=check_formula)
            params = []
            for member in members:
                param = []
                have_error = False
                for k, v in MysqlClassMemberEntity.VARIABLE_MAP.items():
                    value = member.__getattribute__(v)

                    if k == 'student_id' and (value is None or not value.isdigit()):
                        param.append(value)
                        have_error = True
                    elif k == 'id' or k == 'student_id' or k == 'class_group':
                        try:
                            param.append(int(value))
                        except ValueError as e:
                            logger.trace(f'k:[{k}], value:[{value}], error:{e}')
                            param.append(value)
                            have_error = True
                        except TypeError as e:
                            logger.trace(f'k:[{k}], value:[{value}], error:{e}')
                            param.append(value)
                            have_error = True
                    elif k == 'real_name':
                        param.append(full_name_to_real_name(value))
                    elif k == 'next_classes':
                        if isinstance(value, list) and len(value) > 0:
                            param.append(json.dumps(value))
                        # elif isinstance(value, str):
                        #     param.append(value)
                        else:
                            param.append(None)
                    else:
                        param.append(value)
                if have_error:
                    logger.warning(f'Error: {param}')
                else:
                    params.append(tuple(param))

            supplier = (lambda y=x: x for x in params)
            self.db.prepared_update(query, supplier)

            logger.info(f'>>> {len(params)} 筆資料匯入')
            return len(params)

    # def google_relationships_to_mysql(self):
    #     settings: PzProjectGoogleSpreadsheetConfig = self.config.google.spreadsheets.get('relationships')

    def read_google_class_members(self) -> list[MysqlClassMemberEntity]:
        cols, results = self.db.query(f'SELECT * FROM `{self.current_table}` ORDER BY class_name,class_group,id')
        entities = []
        for result in results:
            entity = MysqlClassMemberEntity(cols, result)
            entities.append(entity)
        return entities

    def read_member_details(self) -> list[MysqlMemberDetailEntity]:
        table_name = 'member_details'
        cols, results = self.db.query(f'SELECT * FROM `{table_name}`')
        entities = []
        for result in results:
            entity = MysqlMemberDetailEntity(cols, result)
            entities.append(entity)
        return entities

    def read_member_relations(self) -> list[MysqlMemberRelationEntity]:
        table_name = 'member_relationships'
        cols, results = self.db.query(f'SELECT * FROM `{table_name}`')
        entities = []
        for result in results:
            entity = MysqlMemberRelationEntity(cols, result)
            entities.append(entity)
        return entities

    def _read_seniors_from_table(self, table: str) -> list[MysqlClassMemberEntity]:
        cols, results = self.db.query(f'''
         SELECT * FROM `{table}` WHERE real_name in (
         SELECT DISTINCT(senior) FROM `{table}`) 
         AND real_name=senior AND deacon !=''
         ORDER BY class_name,class_group;
        ''')
        entities = []
        for result in results:
            entity = MysqlClassMemberEntity(cols, result)
            entities.append(entity)
        return entities

    def read_current_seniors(self) -> list[MysqlClassMemberEntity]:
        return self._read_seniors_from_table(self.current_table)

    def read_previous_seniors(self) -> list[MysqlClassMemberEntity]:
        return self._read_seniors_from_table(self.current_table)

    def read_and_update_details(self, entry: MemberDetailModel) -> int:
        query, params = entry.generate_query('member_details')
        # print(query, params)

        try:
            supplier = (lambda y=x: x for x in [params])
            affected_row = self.db.prepared_update(query, supplier)
            return 1 if affected_row > 0 else 0
        except Exception as e:
            logger.error(f'Error: {e}')
            return -1

    def import_and_update(self, entries: list[MemberDetailModel]) -> tuple[int, int]:
        count = 0
        records = 0
        for entry in entries:
            if entry.student_id is not None:
                records += 1
                if re.match(r'\d{9}', str(entry.student_id)):
                    affected_rows = self.read_and_update_details(entry)
                    if affected_rows > 0:
                        logger.info(f'學員: {entry.real_name}, 學號: {entry.student_id} 資料更新')
                        count += affected_rows
                else:
                    logger.warning(f'student_id:{entry.student_id}')
        return records, count

    def google_relation_to_mysql(self, lookup: Callable[[GoogleMemberRelation], VerticalMemberLookupResult]) -> tuple[
        int, list[GeneralProcessingError]]:
        settings: PzProjectGoogleSpreadsheetConfig = self.config.google.spreadsheets.get('relationships')

        relation_table_name = 'member_relationships'

        if settings is not None:
            if settings.fields_map is not None:
                GoogleMemberRelation.remap_variables(settings.fields_map)

            service = PzCloudSpreadsheetRelationsService(settings, self.config.google.secret_file)

            query = (f'''
CREATE TABLE `{relation_table_name}`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `real_name` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '姓名',
  `dharma_name` varchar(2) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '法名',
  `gender` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '性別',
  `student_id` int NULL COMMENT '學員編號',
  `birthday` int NULL COMMENT '生日四碼',
  `phone` int NULL COMMENT '電話末四碼',
  `relation_keys` json DEFAULT NULL COMMENT '親眷朋友關係',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `student_id` (`student_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
            ''')

            self._backup_table(relation_table_name)
            # self._drop_table(relation_table_name)
            self.db.perform_update(query)

            columns_insert = ','.join([f'`{k}`' for k in MysqlMemberRelationEntity.VARIABLE_MAP.keys()])
            values_insert = ','.join(['%s' for _ in MysqlMemberRelationEntity.VARIABLE_MAP.keys()])
            query = f'INSERT INTO `{relation_table_name}` ({columns_insert}) VALUES ({values_insert})'
            logger.info(f'Query: {query}')

            errors: list[GeneralProcessingError] = []
            members: list[GoogleMemberRelation] = service.read_all()
            params = []
            for member in members:
                v_look_result = lookup(member)

                if v_look_result.has_error():
                    errors.append(v_look_result.error)
                    continue

                if v_look_result.is_member():
                    # member.dharmaName = v_look_result.get_dharma_name()
                    member.gender = v_look_result.get_gender()

                    if member.studentId is None or member.studentId == '':
                        member.studentId = str(v_look_result.get_student_id())
                        errors.append(
                            GeneralProcessingError.info(f'{v_look_result.get_real_name()} 的學號為 {member.studentId}'))

                    if member.fullName is None or member.fullName == '':
                        member.fullName = member.realName = v_look_result.get_real_name()
                        errors.append(
                            GeneralProcessingError.info(
                                f'學員編號 {v_look_result.get_student_id()} 的姓名為 {v_look_result.get_real_name()}'))
                    else:
                        real_name = full_name_to_real_name(member.fullName)
                        if real_name != v_look_result.get_real_name():
                            errors.append(GeneralProcessingError.error(
                                f'學員編號 {v_look_result.get_student_id()} 的姓名為 {v_look_result.get_real_name()} 不是 {real_name}'))

                    if member.dharmaName is None or member.dharmaName == '':
                        if v_look_result.get_dharma_name() is not None and v_look_result.get_dharma_name() != '':
                            member.dharmaName = v_look_result.get_dharma_name()
                            errors.append(GeneralProcessingError.info(
                                f'學員  {v_look_result.get_real_name()}/{v_look_result.get_student_id()} 的法名為 {v_look_result.get_dharma_name()}'))
                    elif v_look_result.get_dharma_name() is not None and v_look_result.get_dharma_name() != '':
                        if member.dharmaName != v_look_result.get_dharma_name():
                            member.dharmaName = v_look_result.get_dharma_name()
                            errors.append(GeneralProcessingError.info(
                                f'學員  {v_look_result.get_real_name()}/{v_look_result.get_student_id()} 的法名為 {v_look_result.get_dharma_name()} 不是 {member.dharmaName}'))

                param = []
                have_name = False
                have_relation = False
                # logger.trace(member.to_json())

                for k, v in MysqlMemberRelationEntity.VARIABLE_MAP.items():
                    value = member.__getattribute__(v)
                    logger.trace(f'{k} -> {v} [{value}]')

                    if k in ('student_id', 'phone', 'birthday'):
                        if value is None or not value.isdigit():
                            param.append(None)
                        else:
                            int_value = int(value)
                            if k in ('phone', 'birthday'):
                                int_value = int_value % 10000
                            param.append(int_value)
                    elif k == 'real_name':
                        have_name = True
                        param.append(full_name_to_real_name(value))
                    elif k == 'relation_keys':
                        if isinstance(value, list) and len(value) > 0:
                            have_relation = True
                            param.append(json.dumps(value))
                    else:
                        param.append(value)

                if have_name and have_relation:
                    params.append(tuple(param))
                else:
                    logger.warning(f'Error: {have_name} {have_relation} {param}')

            supplier = (lambda y=x: x for x in params)
            self.db.prepared_update(query, supplier)

            logger.info(f'>>> {len(params)} 筆資料匯入')
            return len(params), errors

    def drop_and_create_table(self, table_name: str, creation_query: str):
        self._drop_table(table_name)
        self.db.perform_update(creation_query)

    @staticmethod
    def mysql_creation_query(table_name: str, columns_in_mysql: list[str]) -> str:
        return f"CREATE TABLE {table_name} ({', \n'.join(columns_in_mysql)}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci"
