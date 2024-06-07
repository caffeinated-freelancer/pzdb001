from services.member_merging_service import MemberMergingService


def member_data_merging(access_database: str, member_data_table: str):
    service = MemberMergingService(access_database, member_data_table)

    service.reemerging()
    service.comparing()


def read_merging_data(database_file: str, table_name: str):
    service = MemberMergingService(database_file, table_name)
    cols, results = service.read_all()
    print(cols)
    print(results)
