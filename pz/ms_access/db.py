import pyodbc
from loguru import logger


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
        if self.debug:
            logger.debug(f"Update Query (prepared statement): {query}")

        cursor = self.connection.cursor()
        counter = 0

        for supplier in callback:
            params = supplier()
            # print(params)
            try:
                cursor.execute(query, params)
                counter += 1
            except pyodbc.IntegrityError:
                logger.warning("Integrity Error", params)
            # print(params)

        self.connection.commit()

        affected_rows = cursor.rowcount

        if self.debug:
            logger.debug(f'{counter} record(s) updated successfully!')
        cursor.close()
        return affected_rows

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
