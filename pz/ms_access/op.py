import re
from typing import List, Any, Callable

import pyodbc

from pz.ms_access.db import PzDatabase
from pz.utils import personal_id_verification, normalize_phone_number


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
            if x[1] is None:
                x[1] = "-"
            else:
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

    @staticmethod
    def sanitize_006_personal_id(personal_id: str) -> str | None:
        if personal_id[0] in 'AB' and personal_id[2] == '0':
            if personal_id[1] == '1':
                pid = int(personal_id[1:4])
            elif personal_id[1] == '2':
                pid = int(personal_id[1:5])
            else:
                pid = 0
            if 104 <= pid <= 108 or 2015 <= pid <= 2019:
                return None

        if personal_id_verification(personal_id):
            return personal_id
        return None

    def clear_target_database(self):
        print('[*] 清空資料庫')
        self.pzDb.perform_update(f'DELETE FROM {self.target_table}')

    def update_data_come_from(self, come_from: str):
        data = "'" + come_from + "'"
        self.pzDb.perform_update(
            f'UPDATE {self.target_table} SET [資料來源] = {data} WHERE IsNull([資料來源])')

    def copy_member_only_in_001(self):
        print('[*] 從 001 複製初始學員資料')
        # column_names = self.pzDb.get_column_names(f'SELECT * FROM member001')
        #
        # # pz_database.print_query("SELECT * FROM member001")
        # inserted_column = ",".join([f"[{col}]" for col in column_names])
        # # pz_database.perform_update(f"INSERT INTO MemberData ({inserted_column},身分證字號,法名) SELECT *,NULL as 身分證字號,NULL as 法名 FROM member001")
        # rows = self.pzDb.perform_update(
        #     f'INSERT INTO {self.target_table} ({inserted_column}) SELECT {inserted_column} FROM member001')
        # self.update_data_come_from('001 - 初始資料')
        # print(f'>>> {rows} record(s) copied')
        # print()

        column_names = self.pzDb.get_column_names(f'SELECT * FROM member001')

        # pz_database.print_query("SELECT * FROM member001")
        inserted_column = ",".join([f"[{col}]" for col in column_names])
        selected_column = ",".join([f"m.[{col}]" for col in column_names])
        # pz_database.perform_update(f"INSERT INTO MemberData ({inserted_column},身分證字號,法名) SELECT *,NULL as 身分證字號,NULL as 法名 FROM member001")
        rows = self.pzDb.perform_update(f'''
            INSERT INTO {self.target_table} ({inserted_column}) SELECT {selected_column} FROM member001 m
            LEFT JOIN {self.target_table} ON m.學員編號 = {self.target_table}.學員編號
            WHERE {self.target_table}.學員編號 IS NULL
            ''')
        self.update_data_come_from('001 - 去年資料')
        print(f'>>> {rows} record(s) copied')
        print()

    def query_and_insert_missing_data(self, query: str, data_come_from: str) -> int:
        cols, results = self.pzDb.query(query)

        result_list = PzDbOperation.fix_chinese_name_in_results(results)

        supplier = (lambda y=x: x for x in result_list)

        query = f'INSERT INTO {self.target_table} ({",".join(cols)}) VALUES ({",".join(["?"] * len(cols))})'

        self.pzDb.prepared_update(query, supplier)
        self.update_data_come_from(data_come_from)

        return len(result_list)

    def copy_dharma_name(self, query: str) -> int:
        _, results = self.pzDb.query(query)
        supplier = (lambda y=x: x for x in results)
        self.pzDb.prepared_update(f'UPDATE [{self.target_table}] SET [法名] = ? WHERE [學員編號] = ?', supplier)
        return len(results)

    def copy_dharma_name_from_002(self):
        print('[*] 從 (002 - 上課記錄) 複製法名')
        rows = self.copy_dharma_name(f'''
            SELECT member002.法名, {self.target_table}.學員編號
            FROM {self.target_table} INNER JOIN member002 ON member002.學員編號 = {self.target_table}.學員編號
            WHERE Not IsNull([member002.法名]) AND IsNull([{self.target_table}.法名]) AND Len(Trim([member002.法名])) > 0
            ''')
        print(f'>>> {rows} record(s) updated')
        print()

    def copy_dharma_name_from_005(self):
        print('[*] 從 (005 - 112-2 禪修班) 複製法名')
        rows = self.copy_dharma_name(f'''
            SELECT member005.法名, {self.target_table}.學員編號
            FROM {self.target_table} INNER JOIN member005 ON member005.學員編號 = {self.target_table}.學員編號
            WHERE Not IsNull([member005.法名]) AND IsNull([{self.target_table}.法名]) AND Len(Trim([member005.法名])) > 0
            ''')
        print(f'>>> {rows} record(s) updated')
        print()

    def copy_dharma_name_from_007(self):
        print('[*] 從 (007 - 報到系統) 複製法名')
        rows = self.copy_dharma_name(f'''
            SELECT member007.法名, {self.target_table}.學員編號
            FROM {self.target_table} INNER JOIN member007 ON member007.學員編號 = {self.target_table}.學員編號
            WHERE Not IsNull([member007.法名]) AND IsNull([{self.target_table}.法名]) AND Len(Trim([member007.法名])) > 0
            ''')
        print(f'>>> {rows} record(s) updated')
        print()

    def copy_members_only_in_005(self):
        print('[*] 從 (005 - 112-2 禪修班) 匯入未匯入的學員資料')
        rows = self.query_and_insert_missing_data(f'''
            SELECT member005.學員編號, member005.學員姓名 AS 姓名, member005.法名, member005.手機 AS 行動電話, member005.住宅 AS 住家電話
            FROM member005 LEFT JOIN {self.target_table} ON member005.學員編號 = {self.target_table}.學員編號
            WHERE (((member005.學員編號) Not In ('缺生日','沒有生日','缺性別') And (member005.學員編號) Is Not Null) And ((Len(member005.學員編號))=9) And (({self.target_table}.學員編號) Is Null));
        ''', '005 - 112-2 禪修班')
        print(f'>>> {rows} record(s) copied')
        print()

    def copy_members_only_in_002(self):
        print('[*] 從 (002 - 上課記錄) 匯入未匯入的學員資料')
        rows = self.query_and_insert_missing_data(f'''
            SELECT m.學員編號, m.姓名, m.法名, m.性別 FROM member002 m
            LEFT JOIN {self.target_table} ON m.學員編號 = {self.target_table}.學員編號
            WHERE {self.target_table}.學員編號 IS NULL;
        ''', '002 - 上課記錄')
        print(f'>>> {rows} record(s) copied')
        print()

    def fix_member_name_from_002(self):
        pass

    def copy_members_only_in_007(self):
        print('[*] 從 (007 - 報到系統) 匯入未匯入的學員資料')
        rows = self.query_and_insert_missing_data(f'''
            SELECT m.學員編號, m.姓名, m.法名, m.性別 FROM member007 m
            LEFT JOIN {self.target_table} ON m.學員編號 = {self.target_table}.學員編號
            WHERE {self.target_table}.學員編號 IS NULL;
        ''', '007 - 報到系統')
        print(f'>>> {rows} record(s) copied')
        print()

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
            if x[2] is not None and len(x[2]) != 0 and not personal_id_verification(x[2]):
                print(x[2], "pid error for", x)

        return cols, data

    def read_and_index_by_name_from_003(self) -> tuple[list[str], dict[str, list[list[Any]]]]:
        return self.index_by_first_column(
            'SELECT 姓名, 性別, 身分證字號, 出生日期 FROM member003 WHERE 身分證字號 IS NOT NULL', None)

    def read_and_index_by_name_from_004(self) -> tuple[list[str], dict[str, list[list[Any]]]]:
        return self.index_by_first_column(
            'SELECT 姓名, 性別, 身分證字號, 出生日期 FROM member004 WHERE 身分證字號 IS NOT NULL', None)

    def read_and_index_by_name_from_006(self) -> tuple[list[str], dict[str, list[list[Any]]]]:
        return self.index_by_first_column(
            'SELECT 姓名, 性別, 身份証號 AS 身分證字號, 出生日 AS 出生日期 FROM member006 WHERE 身份証號 IS NOT NULL',
            lambda x: [x[0], x[1], self.sanitize_006_personal_id(x[2]), self.normalize_birthday(x[3])])

    def read_data_from_006(self):
        cols, results = self.pzDb.query(f'''
            SELECT t.[學員編號],t.[出生日期],t.[行動電話],t.[住家電話],t.[身分證字號],
                m.[身份証號], m.[姓名], m.[法名], m.[性別], m.[出生日], m.[地址], m.[住宅電], m.[公司電],
                m.[行動], m.[緊急連絡人], m.[連絡人關係], m.[連絡人電話], m.[家屬碼], m.[介紹人/關係]
                FROM member006 m INNER JOIN {self.target_table} t ON m.[姓名] = t.[姓名]
                WHERE Not IsNull(m.[出生日]) ORDER BY m.[身份証號]
        ''')

        counter = 0
        error_counter = 0
        pass_counter = 0
        pid_errors = {}
        for result in results:
            if result[cols.index('出生日期')] is not None:
                if self.normalize_birthday(result[cols.index('出生日')]) == result[cols.index('出生日期')]:
                    if result[cols.index('身分證字號')] is None:
                        problem_pid = result[cols.index('身份証號')]

                        if personal_id_verification(problem_pid):
                            # print(result)
                            counter += 1
                        elif problem_pid[0] in 'AB' and problem_pid[1] in '12' and problem_pid[2] == '0':
                            short_pid = problem_pid[1:7]
                            # print(result[cols.index('身份証號')], 'incorrect (006)')
                            # print(short_pid)
                            if short_pid not in pid_errors:
                                pid_errors[short_pid] = []
                            pid_errors[short_pid].append(problem_pid)
                    else:
                        if personal_id_verification(result[cols.index('身分證字號')]):
                            # print(result[cols.index('身分證字號')], f'incorrect ({self.target_table})')
                            pass_counter += 1
                        else:
                            print(result[cols.index('身分證字號')])
                            personal_id_verification(result[cols.index('身分證字號')], True)
                            error_counter += 1
        print(counter, "records found")
        print(error_counter, "record(s) error in personal id")
        print(pass_counter, "record(s) ok in personal id")
        for i, pid_error in enumerate(pid_errors):
            print(pid_error, len(pid_errors[pid_error]))
            # print(pid_errors[pid_error])

    def read_target_db(self, column_names: list[str]) -> tuple[list[str], dict[str, list[list[Any]]]]:
        return self.index_by_first_column(f'SELECT {",".join(column_names)} FROM {self.target_table}', None)

    def compare_update_pid_and_birthday(self, write_back: bool, relax: bool, note: str, callback):
        print(f'[*] 合併身分證字號及生日資訊 (來源: {note})')
        cols, data = callback()
        cols.append("學員編號")
        _, target = self.read_target_db(cols)

        confidence = []
        relax_entries = []
        # possible = []
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
                                confidence.append((entry[1], entry[2], f'{note} (姓名+生日)', target_entry[4]))
                        elif target_entry[3] is None and entry[3] is not None:  # 缺出生日期資訊
                            if len(target[e]) == 1 and len(data[e]) == 1:
                                if target_entry[1] is not None and target_entry[1] != entry[1]:
                                    print("Warning! ", entry, target_entry)
                                else:
                                    # print("Unique Match: ", entry, target_entry)
                                    # possible.append((entry[1], entry[2], entry[3], f'{note} (唯一姓名)', target_entry[4]))
                                    relax_entries.append(
                                        (entry[1], entry[2], entry[3], f'{note} (唯一姓名)', target_entry[4]))
                            elif len(target[e]) == 1:
                                if target_entry[1] is not None and target_entry[1] != entry[1]:
                                    print("Warning! ", entry, target_entry)
                                else:
                                    print("Multiple Match: ", entry, target_entry)
                                    multiple_ids = ", ".join([m[2] if m[2] is not None else '' for m in data[e]])
                                    multiple_match.append((entry[1], multiple_ids, target_entry[4]))

        # print(confidence)
        print(f'>>> {len(confidence)} confidence record(s) found ({note})')
        print(f'>>> {len(relax_entries)} relax record(s) found ({note})')
        print(f'>>> {len(multiple_match)} multiple matching record(s) found ({note})')

        if write_back:
            if len(confidence) > 0:
                supplier = (lambda y=x: x for x in confidence)

                self.pzDb.prepared_update(
                    f'UPDATE {self.target_table} SET [性別] = ?, [身分證字號] = ?, [備註] = ? WHERE [學員編號] = ?',
                    supplier)

            if relax and len(relax_entries) > 0:
                supplier = (lambda y=x: x for x in relax_entries)

                self.pzDb.prepared_update(
                    f'UPDATE {self.target_table} SET [性別] = ?, [身分證字號] = ?, [出生日期] = ?, [備註] =?    WHERE [學員編號] = ?',
                    supplier)

            # if len(possible) > 0:
            #     supplier = (lambda y=x: x for x in possible)
            #
            #     self.pzDb.prepared_update(
            #         f'UPDATE {self.target_table} SET [性別] = ?, [鬆散身分證字號] = ?, [鬆散出生日期] = ?, [備註] =?  WHERE [學員編號] = ?',
            #         supplier)

        # def compare_update_pid_and_birthday_from_006(self, write_back: bool, relax: bool):
        #     self.compare_update_pid_and_birthday(write_back, relax, self.read_data_from_006)
        print()

    def compare_update_contact_info_from_001(self):
        print(f'[*] 合併聯絡人資料 (來源: 001 - 去年資料)')
        cols, results = self.pzDb.query(f'''
            SELECT m.[緊急聯絡人], m.[緊急聯絡人法名], m.[緊急聯絡人稱謂], m.[緊急聯絡人電話],m.[學員編號] FROM member001 m
            INNER JOIN {self.target_table} t ON m.[學員編號] = t.[學員編號] AND m.[姓名] = t.[姓名]
            WHERE IsNull(t.[緊急聯絡人]) AND Not IsNull(m.[緊急聯絡人])
        ''')

        updated_cols = [f'[{c}]=?' for c in cols[:len(cols) - 1]]
        supplier = (lambda y=x: x for x in results)
        self.pzDb.prepared_update(f'UPDATE [{self.target_table}] SET {', '.join(updated_cols)} WHERE [學員編號] = ?',
                                  supplier)
        print(f'>>> {len(results)} records updated')
        print()

    def compare_and_update_personal_phone_number(self, query: str):
        cols, results = self.pzDb.query(query)

        cols = cols[:len(cols) - 1]

        params = []
        valid = [False, False, False, False]
        for result in results:
            for i in range(4):
                result[i], valid[i] = normalize_phone_number(result[i])

            param = [None, None, result[4]]
            modified = False

            if result[0] is not None:
                if result[2] is not None:
                    if valid[2]:
                        param[0] = result[2]
                    elif valid[0]:
                        param[0] = result[0]
                        modified = True
                else:
                    param[0] = result[0]
                    modified = True
            else:
                param[0] = result[2]

            if result[1] is not None:
                if result[3] is not None:
                    if valid[3]:
                        param[1] = result[3]
                    elif valid[1]:
                        param[1] = result[1]
                        modified = True
                else:
                    param[1] = result[1]
                    modified = True
            else:
                param[1] = result[3]

            if modified:
                params.append(tuple(param))

            # value = 0
            # value |= 1 if result[0] is not None else 0  # new value store in 0 and 1
            # value |= 2 if result[1] is not None else 0
            # value |= 4 if result[2] is not None else 0  # origin value store in 2 and 3
            # value |= 8 if result[3] is not None else 0
            #
            # if 1 <= value <= 3:
            #     params.append((result[0], result[1], result[4]))
            # elif 5 <= value <= 7:
            #     if value != 6 and result[0] != result[2]:
            #         print(result[4], result[5], " (mobile):", result[0], "vs", result[2], "(in-db)")
            #         if valid[2] and not valid[0]:
            #             params.append((result[2], result[1], result[4]))
            #     if value == 6 or value == 7:
            #         params.append((result[2], result[1], result[4]))
            # elif 9 <= value <= 11:
            #     if value != 9 and result[1] != result[3]:
            #         print(result[4], result[5], " (home):", result[1], "vs", result[3], "(in-db)")
            #     params.append((result[0], result[3], result[4]))
            # else:
            #     if (value & 1) == 1 and result[0] != result[2]:
            #         print(result[4], result[5], " (mobile):", result[0], "vs", result[2], "(in-db)")
            #     if (value & 2) == 2 and result[1] != result[3]:
            #         print(result[4], result[5], " (home):", result[1], "vs", result[3], "(in-db)")

        updated_cols = [f'[{c}]=?' for c in cols[:2]]
        # print(params)
        # print(updated_cols)
        supplier = (lambda y=x: x for x in params)
        self.pzDb.prepared_update(f'UPDATE [{self.target_table}] SET {', '.join(updated_cols)} WHERE [學員編號] = ?',
                                  supplier)
        print(f'>>> {len(params)} record(s) updated, {len(results)} joined record(s)')
        print()

    def compare_update_personal_phone_from_005(self):
        print(f'[*] 合併個人電話資料 (來源: 005 - 112-2 禪修班)')

        self.compare_and_update_personal_phone_number(f'''
                    SELECT m.[手機] AS 行動電話, m.[住宅] AS 住家電話, t.[行動電話], t.[住家電話], m.[學員編號], t.[姓名] FROM member005 m
                    INNER JOIN {self.target_table} t ON m.[學員編號] = t.[學員編號] AND m.[學員姓名] = t.[姓名]
                ''')

    def compare_update_personal_phone_from_001(self):
        print(f'[*] 合併個人電話資料 (來源: 001 - 去年資料)')

        self.compare_and_update_personal_phone_number(f'''
            SELECT m.[行動電話], m.[住家電話], t.[行動電話], t.[住家電話], m.[學員編號], t.[姓名] FROM member001 m
            INNER JOIN {self.target_table} t ON m.[學員編號] = t.[學員編號] AND m.[姓名] = t.[姓名]
        ''')

    def compare_update_personal_phone_from_006(self):
        # 006 - 普高資料
        print(f'[*] 合併個人電話資料 (來源: 006 - 普高資料)')
        self.compare_and_update_personal_phone_number(f'''
                    SELECT m.[行動] AS 行動電話, m.[住宅電] AS 住家電話, t.[行動電話], t.[住家電話], m.[學員編號], t.[姓名] FROM member006 m
                    INNER JOIN {self.target_table} t ON m.[身份証號] = t.[身分證字號] AND m.[姓名] = t.[姓名]
                ''')

    def compare_update_contact_info_from_006(self):
        # 006 - 普高資料
        # cols = self.pzDb.get_column_names('select * from member006')
        # 'ID', '身份証號', '中台編號', '學員編號', '姓名', 'Field5', '法名', 'Field7', '新增月刊', '新增通啟', '性別', '現齡', '出生日', '地址', '住宅電', '公司電', '行動', '畢校&科系', '工作&職稱', '介紹人', 'E-mail', '特殊專長', '身心狀況', '出生地', '備註', '精舍信眾編號', '緊急連絡人', '連絡人關係', '連絡人電話', '家屬碼', '介紹人/關係', '建檔日期', '受戒別', '發心項目', '親眷關係', '護法會職稱', '班別', '組別']

        print(f'[*] 合併聯絡人資料 (來源: 006 - 普高資料)')
        # SELECT m.[緊急聯絡人], m.[連絡人關係], m.[連絡人電話], m.[學員編號] FROM member006 m
        cols, results = self.pzDb.query(f'''
                    SELECT m.[緊急連絡人] AS 緊急聯絡人, m.[連絡人關係] AS 緊急聯絡人稱謂, m.[連絡人電話] AS 緊急聯絡人電話, m.[學員編號] FROM member006 m
                    INNER JOIN {self.target_table} t ON m.[學員編號] = t.[學員編號] AND m.[姓名] = t.[姓名]
                    WHERE IsNull(t.[緊急聯絡人]) AND Not IsNull(m.[緊急連絡人])
                ''')
        #
        # updated_cols = [f'[{c}]=?' for c in cols[:len(cols) - 1]]
        # supplier = (lambda x=x: x for x in results)
        # self.pzDb.prepared_update(f'UPDATE [{self.target_table}] SET {', '.join(updated_cols)} WHERE [學員編號] = ?',
        #                           supplier)
        print(f'>>> {len(results)} new record(s) found')
        print()

    def set_null_for_blank_pid_and_dharma_name_in_target(self):
        self.pzDb.perform_update(
            f'UPDATE {self.target_table} SET [身分證字號]=NULL WHERE Not IsNull([身分證字號]) AND Len(Trim([身分證字號])) = 0')
        self.pzDb.perform_update(
            f'UPDATE {self.target_table} SET [法名]=NULL WHERE Not IsNull([法名]) AND Len(Trim([法名])) = 0')

    def check_pid_unique_in_target(self):
        print(f'[*] 檢查身分證字號的唯一性')
        _, results = self.pzDb.query(f'''
            SELECT [身分證字號], COUNT(*) FROM {self.target_table}
            WHERE Not IsNull([身分證字號]) GROUP BY [身分證字號] HAVING COUNT(*) > 1 
        ''')

        duplicated_pids = ["'" + x[0] + "'" for x in results]

        if len(duplicated_pids) > 0:
            cols, results = self.pzDb.query(f'''
                SELECT * FROM {self.target_table} 
                WHERE [身分證字號] in ({",".join(duplicated_pids)}) 
                ORDER BY [身分證字號],[學員編號]
            ''')

            # print(cols)

            last_pid = None
            for result in results:
                current_pid = result[cols.index('身分證字號')]

                if last_pid != current_pid:
                    last_pid = current_pid
                    print('>>>', current_pid)
                print('  ', (result[cols.index('學員編號')],
                             result[cols.index('姓名')],
                             result[cols.index('資料來源')],
                             result[cols.index('法名')],
                             result[cols.index('出生日期')],
                             result[cols.index('行動電話')],
                             result[cols.index('住家電話')],
                             result[cols.index('緊急聯絡人')],
                             result[cols.index('備註')]))
        print()

    def target_personal_id_checker(self):
        print(f'[*] 身分證字號檢查是否符合規則檢查')
        _, results = self.pzDb.query(f'''
            SELECT [學員編號],[身分證字號],[姓名],[性別] FROM {self.target_table} WHERE Not IsNull([身分證字號])
        ''')

        error_count = 0
        for result in results:
            if not personal_id_verification(result[1]):
                error_count += 1
                print(result)

        print(f'>>> {error_count} 筆錯誤')
        print()

    def pid_and_gender_checker(self):
        print('[*] 性別身分證字號合理性檢查')
        _, results = self.pzDb.query(f'''
            SELECT [學員編號],[身分證字號],[姓名],[性別], [資料來源], [備註] FROM {self.target_table}
            WHERE (Mid([身分證字號], 2, 1)='1' AND [性別] = '女') OR (Mid([身分證字號], 2, 1)='2' AND [性別] = '男')
        ''')
        error_count = 0
        for result in results:
            print(result)
            error_count += 1
        print(f'>>> {error_count} 筆錯誤')
        print()

    def compare_with_008_more_data(self):
        print('[*] 與 008 比較 - 額外資料')
        _, results = self.pzDb.query(f'''
                    SELECT t.[學員編號],t.[身分證字號],t.[姓名],t.[性別],t.[資料來源],t.[備註] FROM {self.target_table} t
                    LEFT JOIN member008 m ON t.[學員編號] = m.[學員編號]
                    WHERE IsNull(m.[學員編號])
                ''')
        for result in results:
            print("  ", result)
        print(f'>>> 多 {len(results)} 筆')
        print()

    def compare_with_008_less_data(self):
        print('[*] 與 008 比較 - 短少資料')
        _, results = self.pzDb.query(f'''
                    SELECT m.[學員編號],m.[身分證字號],m.[姓名],m.[性別] FROM member008 m 
                    LEFT JOIN {self.target_table} t
                    ON t.[學員編號] = m.[學員編號]
                    WHERE IsNull(t.[學員編號])
                ''')
        for result in results:
            print("  ", result)
        print(f'>>> 少 {len(results)} 筆')
        print()

    def compare_with_008_different_data(self):
        print('[*] 與 008 比較 - 不同資料')
        cols, results = self.pzDb.query(f'''
                    SELECT t.[學員編號],t.[身分證字號],m.[身分證字號],t.[姓名],m.[姓名],t.[出生日期],m.[出生日期],t.[性別],m.[性別],t.[資料來源],t.[備註] FROM {self.target_table} t
                    INNER JOIN member008 m ON t.[學員編號] = m.[學員編號]
                    WHERE t.[身分證字號] <> m.[身分證字號]
                    OR t.[姓名] <> m.[姓名]
                    OR t.[性別] <> m.[性別]
                ''')
        # --                     OR t.[出生日期] <> m.[出生日期]
        for result in results:
            if result[1] != result[2]:
                # print("  ", result[0], "(", result[1], "vs", result[2], ")", "(", result[3], ",", result[4], ")", "(", result[5], ",", result[6], ") [", result[cols.index("資料來源")], "]")
                print("  ", result[0], "(", result[1], "vs", result[2], ")", "(", result[3], ",", result[4], ")")
            elif result[3] != result[4]:
                # print("  ", result[0], "(", result[1], ",", result[2], ")", "(", result[3], "vs", result[4], ")", "(", result[5], ",", result[6], ") [", result[cols.index("資料來源")], "]")
                print("  ", result[0], "(", result[1], ",", result[2], ")", "(", result[3], "vs", result[4], ")")
            elif result[7] != result[8]:
                print("  ", result[0], result[1], result[3], "(", result[7], "vs", result[8], ")")
            else:
                # print("  ", result[0], "(", result[1], ",", result[2], ")", "(", result[3], ",", result[4], ")", "(", result[5], "vs", result[6], ") [", result[cols.index("資料來源")], "]")
                print("  ", result[0], "(", result[1], ",", result[2], ")", "(", result[3], ",", result[4], ")", "(",
                      result[5], "vs", result[6], ") [", result[cols.index("資料來源")], "]")
        print(f'>>> 不同 {len(results)} 筆')
        print()

    def read_all_from_target(self) -> tuple[list[str], list[pyodbc.Row]]:
        return self.pzDb.query(f'SELECT * FROM {self.target_table}')
