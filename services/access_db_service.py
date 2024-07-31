from typing import Any

from loguru import logger

from pz.config import PzProjectConfig
from pz.models.mysql_class_member_entity import MysqlClassMemberEntity
from pz.ms_access.db import PzDatabase


class AccessDbService:
    config: PzProjectConfig
    pzDb: PzDatabase
    CLASS_MEMBER_TABLE = 'ClassMembers'

    def __init__(self, cfg: PzProjectConfig):
        self.config = cfg
        self.pzDb = PzDatabase(cfg.ms_access_db.db_file)

    def class_members_table_creation(self, entries: list[MysqlClassMemberEntity]) -> int:
        table_name = 'ClassMembers'

        try:
            self.pzDb.perform_update(f'DROP TABLE {self.CLASS_MEMBER_TABLE}')
            logger.debug('dropping table')
        except Exception:
            logger.debug('failed to drop table')

        variable_names: list[str] = []
        column_names: list[str] = []
        table_creation_columns: list[str] = ['ID AUTOINCREMENT  PRIMARY KEY']

        for k, v in MysqlClassMemberEntity.ACCESS_DB_MAP.items():
            variable_names.append(k)
            column_names.append(v[0])
            table_creation_columns.append(f'{v[0]} {v[1]} NOT NULL')

        creation_query = f'CREATE TABLE {self.CLASS_MEMBER_TABLE} ({",".join(table_creation_columns)})'

        self.pzDb.perform_update(creation_query)
        self.pzDb.perform_update(f'CREATE INDEX idx_StudentId ON {self.CLASS_MEMBER_TABLE} (StudentId)')

        query = f'INSERT INTO {table_name} ({",".join(column_names)}) VALUES ({",".join(["?"] * len(column_names))})'
        results = []

        for entity in entries:
            params = []
            for v in variable_names:
                params.append(entity.__dict__[v])
            results.append(tuple(params))

        supplier = (lambda y=x: x for x in results)
        return self.pzDb.prepared_update(query, supplier)

    def read_all_members_as_mysql(self) -> list[MysqlClassMemberEntity]:
        reversed_map: dict[str, str] = {}

        for k, v in MysqlClassMemberEntity.ACCESS_DB_MAP.items():
            reversed_map[v[0]] = k

        query = f'SELECT * FROM {self.CLASS_MEMBER_TABLE} ORDER BY ClassName,ClassGroup,ID'

        headers, rows = self.pzDb.query(query)
        logger.debug(headers)
        columns: list[str] = []
        indexes: list[int] = []

        for i, header in enumerate(headers):
            if header in reversed_map:
                columns.append(reversed_map[header])
                indexes.append(i)

        results: list[MysqlClassMemberEntity] = []
        for row in rows:
            values: list[Any] = []
            for i in indexes:
                values.append(row[i])
            results.append(MysqlClassMemberEntity(columns, values))

        return results
