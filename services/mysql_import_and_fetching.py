import json
import re

from loguru import logger

from pz.cloud.spreadsheet_member_service import PzCloudSpreadsheetMemberService
from pz.config import PzProjectConfig, PzProjectGoogleSpreadsheetConfig
from pz.models.google_class_member import GoogleClassMemberModel
from pz.models.member_detail_model import MemberDetailModel
from pz.models.member_in_access import MemberInAccessDB
from pz.models.mysql_class_member_entity import MysqlClassMemberEntity
from pz.models.mysql_member_detail_entity import MysqlMemberDetailEntity
from pz.mysql.db import PzMysqlDatabase
from pz.utils import full_name_to_real_name
from services.member_merging_service import MemberMergingService


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

        self.db.perform_update('DROP TABLE IF EXISTS `member_details`')
        self.db.perform_update(query)

        cols, results = service.read_all()

        query = f'INSERT INTO `member_details` ({",".join(insert_columns)}) VALUES ({",".join(insert_values)})'
        # print(query)

        params = []
        for result in results:
            entry = MemberInAccessDB(cols, result)
            param = [int(entry.student_id)]
            for _, v in MemberInAccessDB.ATTRIBUTES_MAP.items():
                param.append(entry.__getattribute__(v))
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

    def _backup_table(self):
        number_of_backups = 3

        from_table = f'{self.current_table}_{number_of_backups + 1}'
        self._drop_table(from_table)

        for i in range(number_of_backups, 0, -1):
            try:
                to_table = from_table
                from_table = f'{self.current_table}_{i}'
                self._rename_table(from_table, to_table)
            except Exception as ignored:
                pass
        self._rename_table(self.current_table, from_table)

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

            self._backup_table()
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

    def read_google_class_members(self) -> list[MysqlClassMemberEntity]:
        cols, results = self.db.query(f'SELECT * FROM `{self.current_table}` ORDER BY class_name,class_group,id')
        entities = []
        for result in results:
            entity = MysqlClassMemberEntity(cols, result)
            entities.append(entity)
        return entities

    def read_member_details(self) -> list[MysqlMemberDetailEntity]:
        cols, results = self.db.query('SELECT * FROM `member_details`')
        entities = []
        for result in results:
            entity = MysqlMemberDetailEntity(cols, result)
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

