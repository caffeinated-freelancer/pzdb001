import re
from typing import List, Any, Callable

import pyodbc

from pz.db import PzDatabase


class PzDbOperation:
    pzDb: PzDatabase
    target_table: str

    def __init__(self, db_path: str, target_table: str):
        self.pzDb = PzDatabase(db_path)
        self.target_table = target_table

    @staticmethod
    def fix_chinese_name(name: str) -> str:
        pattern = r'^(?P<real>.*\S)\s*\(.*$'
        match = re.match(pattern, name)
        if match:
            return match.group('real')
        else:
            return name

    @staticmethod
    def row_to_list(rows: List[pyodbc.Row]) -> list[list[Any]]:
        converter = lambda x: list(x)
        return [converter(x) for x in rows]

    @staticmethod
    def fix_chinese_name_in_results(results: list[pyodbc.Row]) -> list[list[Any]]:
        result_list = PzDbOperation.row_to_list(results)

        for x in result_list:
            x[1] = PzDbOperation.fix_chinese_name(x[1])

        return result_list

    @staticmethod
    def normalize_birthday(birthday: str | None) -> str | None:
        if birthday is not None:
            pattern = r'^(?P<y>\d{1,3})\.(?P<m>\d{2})\.(?P<d>\d{2})$'
            match = re.match(pattern, birthday)
            if match:
                return f'{int(match.group('y')) + 1911}-{match.group('m')}-{match.group('d')}'
        return birthday

    def clear_target_database(self):
        self.pzDb.perform_update(f'DELETE FROM {self.target_table}')

    def copy_from_001(self):
        column_names = self.pzDb.get_column_names("SELECT * FROM member001")
        # pz_database.print_query("SELECT * FROM member001")
        inserted_column = ",".join([f"[{col}]" for col in column_names])
        # pz_database.perform_update(f"INSERT INTO MemberData ({inserted_column},身分證字號,法名) SELECT *,NULL as 身分證字號,NULL as 法名 FROM member001")
        self.pzDb.perform_update(
            f'INSERT INTO {self.target_table} ({inserted_column}) SELECT {inserted_column} FROM member001')

    def query_and_insert_missing_data(self, query: str):
        cols, results = self.pzDb.query(query)

        result_list = PzDbOperation.fix_chinese_name_in_results(results)

        supplier = (lambda x=x: x for x in result_list)

        query = f'INSERT INTO {self.target_table} ({",".join(cols)}) VALUES ({",".join(["?"] * len(cols))})'
        self.pzDb.prepared_update(query, supplier)

    def copy_dharma_name_from_005(self):
        cols, results = self.pzDb.query(f'''
            SELECT member005.法名, {self.target_table}.學員編號
            FROM {self.target_table} INNER JOIN member005 ON member005.學員編號 = {self.target_table}.學員編號
            WHERE member005.法名 IS NOT NULL
            ''')

        # data = dict((y, x) for x, y in results)
        # print(data)

        supplier = (lambda x=x: x for x in results)

        self.pzDb.prepared_update(f'UPDATE {self.target_table} SET 法名 = ? WHERE 學員編號 = ?', supplier)

    def copy_members_only_in_005(self):
        self.query_and_insert_missing_data(f'''
            SELECT member005.學員編號, member005.學員姓名 AS 姓名, member005.法名, member005.手機 AS 行動電話, member005.住宅 AS 住家電話
            FROM member005 LEFT JOIN {self.target_table} ON member005.學員編號 = {self.target_table}.學員編號
            WHERE (((member005.學員編號) Not In ('缺生日','沒有生日','缺性別') And (member005.學員編號) Is Not Null) And ((Len(member005.學員編號))=9) And (({self.target_table}.學員編號) Is Null));
        ''')

    def copy_members_only_in_002(self):
        self.query_and_insert_missing_data(f'''
            SELECT m.學員編號, m.姓名, m.法名, m.性別 FROM member002 m
            LEFT JOIN {self.target_table} ON m.學員編號 = {self.target_table}.學員編號
            WHERE {self.target_table}.學員編號 IS NULL;
        ''')

    def index_by_first_column(self, query: str, manipulator: Callable[[list[str]], list[str]] | None) -> tuple[
        list[str], dict[str, list[list[Any]]]]:
        cols, results = self.pzDb.query(query)
        result_list = PzDbOperation.row_to_list(results)

        if manipulator is not None and callable(manipulator):
            converted = []
            for x in result_list:
                converted.append(manipulator(x))
            result_list = converted

        # data = dict((entry[0], entry) for entry in result_list)
        data = {}
        for x in result_list:
            if x[0] in data:
                data[x[0]].append(x)
            else:
                data[x[0]] = [x]

        return cols, data

    def read_data_from_003(self) -> tuple[list[str], dict[str, list[list[Any]]]]:
        return self.index_by_first_column(
            'SELECT 姓名, 性別, 身分證字號, 出生日期 FROM member003 WHERE 身分證字號 IS NOT NULL', None)

    def read_data_from_004(self) -> tuple[list[str], dict[str, list[list[Any]]]]:
        return self.index_by_first_column(
            'SELECT 姓名, 性別, 身分證字號, 出生日期 FROM member004 WHERE 身分證字號 IS NOT NULL', None)

    def read_data_from_006(self) -> tuple[list[str], dict[str, list[list[Any]]]]:
        return self.index_by_first_column(
            'SELECT 姓名, 性別, 身份証號 AS 身分證字號, 出生日 AS 出生日期 FROM member006 WHERE 身份証號 IS NOT NULL',
            lambda x: [x[0], x[1], x[2], self.normalize_birthday(x[3])])

    def read_target_db(self, column_names: list[str]) -> tuple[list[str], dict[str, list[list[Any]]]]:
        return self.index_by_first_column(f'SELECT {",".join(column_names)} FROM {self.target_table}', None)

    def compare_update_from_data(self, write_back: bool, relax: bool, callback):
        cols, data = callback()
        cols.append("學員編號")
        _, target = self.read_target_db(cols)

        confidence = []
        relax_entries = []
        possible = []
        multiple_match = []

        for e in data:
            if e in target:
                for entry in data[e]:
                    for target_entry in target[e]:
                        if target_entry[3] is not None and target_entry[3] == entry[3]:  # 出生日期相符
                            if target_entry[1] is not None and target_entry[1] != entry[1]:
                                print("Warning! ", entry, target_entry)
                            elif target_entry[2] is not None:
                                pass
                            else:
                                # print(entry)
                                confidence.append((entry[1], entry[2], target_entry[4]))
                        elif target_entry[3] is None and entry[3] is not None:  # 缺出生日期資訊
                            if len(target[e]) == 1 and len(data[e]) == 1:
                                if target_entry[1] is not None and target_entry[1] != entry[1]:
                                    print("Warning! ", entry, target_entry)
                                else:
                                    # print("Unique Match: ", entry, target_entry)
                                    possible.append((entry[1], entry[2], entry[3], target_entry[4]))
                                    relax_entries.append((entry[1], entry[2], entry[3], target_entry[4]))
                            elif len(target[e]) == 1:
                                if target_entry[1] is not None and target_entry[1] != entry[1]:
                                    print("Warning! ", entry, target_entry)
                                else:
                                    print("Multiple Match: ", entry, target_entry)
                                    multiple_ids = ", ".join([m[2] for m in data[e]])
                                    multiple_match.append((entry[1], multiple_ids, target_entry[4]))

        # print(confidence)
        print(f'{len(confidence)} confidence record(s) found')
        print(f'{len(possible)} relax record(s) found')
        print(f'{len(multiple_match)} multiple matching record(s) found')

        if write_back:
            if len(confidence) > 0:
                supplier = (lambda x=x: x for x in confidence)

                self.pzDb.prepared_update(
                    f'UPDATE {self.target_table} SET [性別] = ?, [身分證字號] = ? WHERE [學員編號] = ?', supplier)

            if relax and len(relax_entries) > 0:
                supplier = (lambda x=x: x for x in relax_entries)

                self.pzDb.prepared_update(
                    f'UPDATE {self.target_table} SET [性別] = ?, [身分證字號] = ?, [出生日期] = ?  WHERE [學員編號] = ?',
                    supplier)

            if len(possible) > 0:
                supplier = (lambda x=x: x for x in possible)

                self.pzDb.prepared_update(
                    f'UPDATE {self.target_table} SET [性別] = ?, [鬆散身分證字號] = ?, [鬆散出生日期] = ?  WHERE [學員編號] = ?',
                    supplier)

    def compare_update_from_006(self, write_back: bool, relax: bool):
        self.compare_update_from_data(write_back, relax, self.read_data_from_006)
