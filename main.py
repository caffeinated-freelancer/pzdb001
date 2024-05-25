from pz.op import PzDbOperation

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # Replace with your actual database path
    db_path = r"C:/Users/Foveo/OneDrive/Documents/db0519.accdb"

    pzOperation = PzDbOperation(db_path, 'MemberData')

    relax = True
    rewrite = True

    if rewrite:
        pzOperation.clear_target_database()  # 清空資料庫

        pzOperation.copy_members_only_in_002()  # 複製僅在 002 上有的資料 (上課記錄)
        pzOperation.copy_members_only_in_005()  # 複製僅在 005 上有的資料 (112-2 禪修班)
        pzOperation.copy_member_only_in_001()  # 複製 001 的資料 (去年見羨法師提供的資料)
        pzOperation.copy_members_only_in_007()  # 複製僅在 002 上有的資料 (5/19 報到系統累積的資料)

        pzOperation.copy_dharma_name_from_002()  # 複製 002 的法名
        pzOperation.copy_dharma_name_from_005()  # 複製 005 的法名
        pzOperation.copy_dharma_name_from_007()  # 複製 007 的法名

        # 補資料: 003, 004, 006 缺學號, 所以用姓名比對補 [身分證字號], [出生日期]
        pzOperation.compare_update_pid_and_birthday(True, relax, '003 - 保險資料',
                                                    pzOperation.read_and_index_by_name_from_003)
        pzOperation.compare_update_pid_and_birthday(True, relax, '004 - 保險資料',
                                                    pzOperation.read_and_index_by_name_from_004)

        # 普高的身分證號資料有問題
        pzOperation.compare_update_pid_and_birthday(True, relax, '006 - 普高資料',
                                                    pzOperation.read_and_index_by_name_from_006)

        pzOperation.compare_update_contact_info_from_001()
        pzOperation.compare_update_personal_phone_from_001()
        # pzOperation.compare_update_pid_and_birthday_from_006(True, relax)

        pzOperation.set_null_for_blank_pid_and_dharma_name_in_target()

    pzOperation.pid_and_gender_checker()
    pzOperation.target_personal_id_checker()
    pzOperation.check_pid_unique_in_target()

    pzOperation.compare_with_008_more_data()
    pzOperation.compare_with_008_less_data()
    pzOperation.compare_with_008_different_data()
    # pzOperation.read_data_from_006()

    # pzOperation.compare_update_contact_info_from_001()
