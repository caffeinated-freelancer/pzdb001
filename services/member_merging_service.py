import pyodbc

from pz.ms_access.op import PzDbOperation


class MemberMergingService:
    pzOperation: PzDbOperation
    target_table: str
    db_path: str

    def __init__(self, db_path: str, target_table: str):
        self.db_path = db_path
        self.target_table = target_table
        self.pzOperation = PzDbOperation(self.db_path, self.target_table)

    def reemerging(self, relax: bool = True):
        self.pzOperation.clear_target_database()  # 清空資料庫

        self.pzOperation.copy_members_only_in_002()  # 複製僅在 002 上有的資料 (上課記錄)
        self.pzOperation.copy_members_only_in_005()  # 複製僅在 005 上有的資料 (112-2 禪修班)
        self.pzOperation.copy_member_only_in_001()  # 複製 001 的資料 (去年見羨法師提供的資料)
        self.pzOperation.copy_members_only_in_007()  # 複製僅在 002 上有的資料 (5/19 報到系統累積的資料)

        self.pzOperation.copy_dharma_name_from_002()  # 複製 002 的法名
        self.pzOperation.copy_dharma_name_from_005()  # 複製 005 的法名
        self.pzOperation.copy_dharma_name_from_007()  # 複製 007 的法名

        # 補資料: 003, 004, 006 缺學號, 所以用姓名比對補 [身分證字號], [出生日期]
        self.pzOperation.compare_update_pid_and_birthday(True, relax, '003 - 保險資料',
                                                         self.pzOperation.read_and_index_by_name_from_003)
        self.pzOperation.compare_update_pid_and_birthday(True, relax, '004 - 保險資料',
                                                         self.pzOperation.read_and_index_by_name_from_004)

        # 普高的身分證號資料有問題
        self.pzOperation.compare_update_pid_and_birthday(True, relax, '006 - 普高資料',
                                                         self.pzOperation.read_and_index_by_name_from_006)

        self.pzOperation.compare_update_contact_info_from_001()

        self.pzOperation.compare_update_personal_phone_from_001()
        self.pzOperation.compare_update_personal_phone_from_005()

        self.pzOperation.compare_update_contact_info_from_006()
        self.pzOperation.compare_update_personal_phone_from_006()
        # pzOperation.compare_update_pid_and_birthday_from_006(True, relax)

        self.pzOperation.set_null_for_blank_pid_and_dharma_name_in_target()

    def comparing(self):
        self.pzOperation.pid_and_gender_checker()
        self.pzOperation.target_personal_id_checker()
        self.pzOperation.check_pid_unique_in_target()

        self.pzOperation.compare_with_008_more_data()
        self.pzOperation.compare_with_008_less_data()
        self.pzOperation.compare_with_008_different_data()

    def read_all(self) -> tuple[list[str], list[pyodbc.Row]]:
        return self.pzOperation.read_all_from_target()
