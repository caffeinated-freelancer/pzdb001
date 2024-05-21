from pz.op import PzDbOperation

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # Replace with your actual database path
    db_path = r"C:/Users/Foveo/OneDrive/Documents/db0519.accdb"

    pzOperation = PzDbOperation(db_path, 'MemberData')

    relax = True

    pzOperation.clear_target_database()
    pzOperation.copy_from_001()
    pzOperation.copy_dharma_name_from_005()
    pzOperation.copy_members_only_in_005()
    pzOperation.copy_members_only_in_002()
    pzOperation.compare_update_from_data(True, relax, pzOperation.read_data_from_003)
    pzOperation.compare_update_from_data(True, relax, pzOperation.read_data_from_004)
    pzOperation.compare_update_from_006(True, relax)
