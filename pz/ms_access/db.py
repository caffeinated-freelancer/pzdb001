from typing import Any, Callable

import pyodbc
from loguru import logger


class PzAccessDbStructure:
    column_index: int
    column_name: str
    type_code: type
    display_size: int | None
    internal_size: int
    precision: int
    scale: int
    nullable: bool

    def __init__(self, column_index, column: tuple[str, Any, int, int, int, int, bool]):
        self.column_index = column_index
        self.column_name = column[0]
        if isinstance(column[1], type):
            self.type_code = column[1].__name__
        else:
            self.type_code = column[1]
        self.display_size = column[2]
        self.internal_size = column[3]
        self.precision = column[4]
        self.scale = column[5]
        self.nullable = column[6]


class PzAccessDbMySqlCreator:
    mapping: dict[str, str]

    def __init__(self, mapping: dict[str, str]):
        self.mapping = mapping

    def mysql_have_mapping(self, db_struct: PzAccessDbStructure) -> bool:
        if db_struct.column_name in self.mapping:
            return True
        else:
            return False

    def _mysql_field_name(self, db_struct: PzAccessDbStructure) -> str:
        if db_struct.column_name in self.mapping:
            return f'`{self.mapping[db_struct.column_name]}`'
        return f'`field{db_struct.column_index}`'

    @staticmethod
    def _mysql_datatype(db_struct: PzAccessDbStructure) -> str:
        if isinstance(db_struct.type_code, str):
            return f'VARCHAR({db_struct.precision}) COLLATE utf8mb4_general_ci'
        elif isinstance(db_struct.type_code, int):
            return f'INTEGER({db_struct.precision})'
        else:
            logger.warning(f'mysql_datatype: {db_struct.type_code}')
            return f'VARCHAR({db_struct.precision}) COLLATE utf8mb4_general_ci'

    @staticmethod
    def _mysql_nullable(db_struct: PzAccessDbStructure) -> str:
        if db_struct.nullable:
            return 'NULL'
        else:
            return 'NOT NULL'

    def to_mysql(self, db_struct: PzAccessDbStructure) -> str:
        return f"{self._mysql_field_name(db_struct)} {self._mysql_datatype(db_struct)} {self._mysql_nullable(db_struct)} COMMENT '{db_struct.column_name}'"


class PzDatabase:
    conn_str: str
    connection: pyodbc.connect
    debug: bool = False

    def __init__(self, db_path: str, debug: bool = False):
        self.conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path}"
        self.connection = pyodbc.connect(self.conn_str)
        self.debug = debug

    def __del__(self):
        # body of destructor
        self.connection.close()
        logger.debug("Connection closed")

    # def copy_table_structure(self, original_table_name: str, new_table_name: str):
    #     # query = f"CREATE TABLE {new_table_name} LIKE {original_table_name}"
    #     # self.perform_update(query)
    #
    #     cursor = self.connection.cursor()
    #
    #     # Sample SELECT query to get column information (modify as needed)
    #     sql_query = f"""
    #     SELECT COLUMN_NAME, DATA_TYPE
    #     FROM INFORMATION_SCHEMA.COLUMNS
    #     WHERE TABLE_NAME = '{original_table_name}'
    #     """
    #
    #     # Execute the query
    #     cursor.execute(sql_query)
    #
    #     # Get column information (assuming two columns)
    #     column_names = [row[0] for row in cursor.fetchall()]
    #     column_types = [row[1] for row in cursor.fetchall()]
    #
    #     print(column_names)
    #     print(column_types)

    def perform_update(self, query: str) -> int:
        cursor = self.connection.cursor()

        if self.debug:
            logger.debug(f"Update Query: {query}")

        cursor.execute(query)
        affected_rows = cursor.rowcount
        if self.debug:
            logger.debug('affected rows: ', affected_rows)

        self.connection.commit()
        cursor.close()
        return affected_rows

    def prepared_update(self, query: str, callback) -> int:
        logger.debug(f"Update Query (prepared statement): {query}")

        cursor = self.connection.cursor()
        counter = 0

        for supplier in callback:
            params = supplier()
            logger.trace(params)
            try:
                cursor.execute(query, params)
                counter += 1
            except pyodbc.IntegrityError:
                logger.warning("Integrity Error", params)
            # print(params)

        self.connection.commit()

        affected_rows = cursor.rowcount

        logger.debug(f'{counter} record(s) updated successfully!')
        cursor.close()
        return counter

    def get_column_names(self, query: str) -> list[str]:
        cursor = self.connection.cursor()
        cursor.execute(query)
        des = [col[0] for col in cursor.description]
        cursor.close()
        return des

    def query(self, query: str) -> tuple[list[str], list[pyodbc.Row]]:
        cursor = self.connection.cursor()
        cursor.execute(query)
        column_names = [col[0] for col in cursor.description]
        all_rows = cursor.fetchall()
        cursor.close()

        return column_names, all_rows

    def print_query(self, query: str):
        print(query)
        cursor = self.connection.cursor()
        cursor.execute(query)

        # print(cursor.description)

        # column_names = [col.name for col in cursor.description]
        column_names = [col[0] for col in cursor.description]

        # Fetch results (can be a loop for many rows)
        # row = cursor.fetchone()
        #
        # # Print the first row (or loop through all rows)
        # if row:
        #     print(row)  # This will be a tuple containing column values
        # else:
        #     print("No data found")

        all_rows = cursor.fetchall()

        for row in all_rows:
            # Access column values using index or column names (refer to cursor.description)
            # print(f"ID: {row[0]} | Name: {row[1]} (assuming ID and Name are first two columns)")
            print(row)
            # Process each row as needed

        # Close the cursor and connection
        cursor.close()
        print(column_names)

    def table_structure(self, table_name: str) -> list[PzAccessDbStructure]:
        cursor = self.connection.cursor()
        query = f"SELECT * FROM {table_name} WHERE 1=0"  # Returns no data, but allows to get column info
        cursor.execute(query)

        # Fetch the column information
        # columns = [(column.column_name, column.type_name, column.column_size) for column in cursor.description]

        # Print the table structure
        fields: list[PzAccessDbStructure] = []
        i = 0
        for column in cursor.description:
            i += 1
            fields.append(PzAccessDbStructure(i, column))
        return fields

    def table_to_mysql_table_creation_query(
            self, access_table_name: str, mysql_table_name: str, column_name_mapping: dict[str, str],
            fine_tunner: Callable[[list[str]], None]) -> str:
        columns = self.table_structure(access_table_name)
        creator = PzAccessDbMySqlCreator(column_name_mapping)

        columns_in_mysql = [creator.to_mysql(x) for x in columns if creator.mysql_have_mapping(x)]
        fine_tunner(columns_in_mysql)

        return self.mysql_creation_query(mysql_table_name, columns_in_mysql)

    @staticmethod
    def mysql_creation_query(table_name: str, columns_in_mysql: list[str]) -> str:
        return f"CREATE TABLE {table_name} ({', \n'.join(columns_in_mysql)}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci"
