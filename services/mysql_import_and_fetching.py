from pz.cloud.spreadsheet_member_service import PzCloudSpreadsheetMemberService
from pz.config import PzProjectConfig, PzProjectGoogleSpreadsheetConfig
from pz.models.google_class_member import GoogleClassMemberModel
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

    def __init__(self, config: PzProjectConfig):
        self.config = config
        self.db = PzMysqlDatabase(config.mysql)
        self.current_table = f'class_members_{self.config.semester}'

    def access_db_member_to_mysql(self, service: MemberMergingService):
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

        print(f'>>> {len(params)} records inserted')

    def google_class_members_to_mysql(self):
        settings: PzProjectGoogleSpreadsheetConfig = self.config.google.spreadsheets.get('class_members')

        if settings is not None:
            service = PzCloudSpreadsheetMemberService(settings.spreadsheet_id, self.config.google.secret_file)

            query = (f'''
CREATE TABLE `{self.current_table}` (
  `id` int NOT NULL AUTO_INCREMENT,
  `student_id` int NOT NULL COMMENT '學員編號',
  `class_name` varchar(5) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '班級',
  `class_group` int NOT NULL COMMENT '組別',
  `senior` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '學長',
  `real_name` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '姓名',
  `dharma_name` varchar(2) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '法名',
  `deacon` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '執事',
  `gender` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '性別',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `student_id` (`student_id`,`class_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
            ''')

            self.db.perform_update(f'DROP TABLE IF EXISTS `{self.current_table}`')
            self.db.perform_update(query)

            columns_insert = ','.join([f'`{k}`' for k in MysqlClassMemberEntity.VARIABLE_MAP.keys()])
            values_insert = ','.join(['%s' for _ in MysqlClassMemberEntity.VARIABLE_MAP.keys()])
            query = f'INSERT INTO `{self.current_table}` ({columns_insert}) VALUES ({values_insert})'
            print(query)

            members: list[GoogleClassMemberModel] = service.read_all(GoogleClassMemberModel([]))
            params = []
            for member in members:
                param = []
                for k, v in MysqlClassMemberEntity.VARIABLE_MAP.items():
                    if k == 'id' or k == 'student_id' or k == 'class_group':
                        param.append(int(member.__getattribute__(v)))
                    elif k == 'real_name':
                        param.append(full_name_to_real_name(member.__getattribute__(v)))
                    else:
                        param.append(member.__getattribute__(v))
                params.append(tuple(param))

            supplier = (lambda y=x: x for x in params)
            self.db.prepared_update(query, supplier)

            print(f'>>> {len(params)} records inserted')

    def read_google_class_members(self) -> list[MysqlClassMemberEntity]:
        cols, results = self.db.query(f'SELECT * FROM `{self.current_table}`')
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
