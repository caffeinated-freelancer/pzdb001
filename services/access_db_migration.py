import json

from loguru import logger

from pz.config import PzProjectConfig
from pz.models.mysql_member_basic_entity import MysqlMemberBasicEntity
from pz.models.mysql_member_more_basic_entity import MysqlMemberMoreBasicEntity
from pz.ms_access.db import PzDatabase
from pz.mysql.db import PzMysqlDatabase
from services.mysql_import_and_fetching import MySqlImportAndFetchingService


class AccessDBMigration:
    config: PzProjectConfig
    pzDb: PzDatabase
    db: PzMysqlDatabase
    dbFile: str

    def __init__(self, cfg: PzProjectConfig, db_file: str | None = None) -> None:
        self.config = cfg
        if db_file is None:
            self.dbFile = cfg.ms_access_db.db_file
        else:
            self.dbFile = db_file
        self.pzDb = PzDatabase(self.dbFile)
        self.db = PzMysqlDatabase(cfg.mysql)

    def insert_into_basic(self, entities: list[MysqlMemberBasicEntity]):
        columns = [f'`{k}`' for k in MysqlMemberBasicEntity.PZ_MYSQL_COLUMN_NAMES.values()]
        columns.insert(0, '`id`')
        columns_insert = ','.join(columns)

        values_insert = ','.join(['%s'] * len(columns))
        query = f'INSERT INTO `{MysqlMemberBasicEntity.TABLE_NAME}` ({columns_insert}) VALUES ({values_insert})'

        params = []
        for entity in entities:
            param = [entity.id]
            for k in MysqlMemberBasicEntity.PZ_MYSQL_COLUMN_NAMES.values():
                param.append(entity.__dict__[k])
            params.append(tuple(param))

        supplier = (lambda y=x: x for x in params)
        self.db.prepared_update(query, supplier)

    def insert_into_more_basic(self, entities: list[MysqlMemberMoreBasicEntity]):
        columns = ["`id`", "`additional`"]
        columns_insert = ','.join(columns)

        values_insert = ','.join(['%s'] * len(columns))
        query = f'INSERT INTO `{MysqlMemberMoreBasicEntity.TABLE_NAME}` ({columns_insert}) VALUES ({values_insert})'

        params = []
        for entity in entities:
            params.append((entity.id, json.dumps(entity.additional,
                                                 default=lambda o: o.to_dict(),
                                                 sort_keys=True, ensure_ascii=False)))

        supplier = (lambda y=x: x for x in params)
        self.db.prepared_update(query, supplier)

    def migrate(self) -> int:
        # self.pzDb.get_all_tables()
        # self.pzDb.table_structure('MemberBasic')

        access_table_name = 'MemberBasic'
        mysql_table_name = MysqlMemberBasicEntity.TABLE_NAME

        query = self.pzDb.table_to_mysql_table_creation_query(
            access_table_name, mysql_table_name,
            MysqlMemberBasicEntity.PZ_MYSQL_COLUMN_NAMES,
            MysqlMemberBasicEntity.MYSQL_SCHEMA_FINE_TUNNER)
        logger.info(query)
        mysql_service = MySqlImportAndFetchingService(self.config)

        mysql_service.drop_and_create_table(mysql_table_name, query)

        more_basics = MysqlMemberMoreBasicEntity.TABLE_NAME
        query = mysql_service.mysql_creation_query(more_basics,
                                                   MysqlMemberMoreBasicEntity.member_more_basics_creation())
        mysql_service.drop_and_create_table(more_basics, query)

        headers, rows = self.pzDb.query(f'SELECT * FROM {access_table_name}')

        attributes: list[tuple[str, int]] = []
        more_attributes: list[tuple[str, int]] = []
        for i, header in enumerate(headers):
            if header in MysqlMemberBasicEntity.PZ_MYSQL_COLUMN_NAMES:
                attributes.append((MysqlMemberBasicEntity.PZ_MYSQL_COLUMN_NAMES[header], i))
            else:
                more_attributes.append((header, i))

        basic_entities = []
        more_entities = []

        for row in rows:
            params: dict[str, str] = {}
            more_params: dict[str, str] = {}

            for attribute in attributes:
                params[attribute[0]] = row[attribute[1]]

            for more_attribute in more_attributes:
                if row[more_attribute[1]] is not None and row[more_attribute[1]] != '':
                    more_params[more_attribute[0]] = row[more_attribute[1]]

            basic_entity = MysqlMemberBasicEntity(params)

            if basic_entity.id != -1:
                more_entity = MysqlMemberMoreBasicEntity(basic_entity.id, more_params)

                basic_entities.append(basic_entity)
                more_entities.append(more_entity)
                # print(basic_entity.to_json())
                # print(more_entity.to_json())

        self.insert_into_basic(basic_entities)
        self.insert_into_more_basic(more_entities)

        logger.info(f'>>> {len(basic_entities)} 筆資料匯入')
        return len(basic_entities)
