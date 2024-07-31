from pz.config import PzProjectConfig
from services.access_db_service import AccessDbService
from services.mysql_import_and_fetching import MySqlImportAndFetchingService


def member_to_access_db(cfg: PzProjectConfig) -> int:
    service = MySqlImportAndFetchingService(cfg)
    access_service = AccessDbService(cfg)
    service.read_google_class_members()

    return access_service.class_members_table_creation(service.read_google_class_members())

    # table_name = 'ClassMembers'
    # pz_db = PzDatabase(cfg.ms_access_db.db_file, debug=False)
    #
    # try:
    #     pz_db.perform_update(f'DROP TABLE {table_name}')
    # except Exception:
    #     pass
    #
    # pz_db.perform_update(f"""
    #     CREATE TABLE {table_name} (
    #         ID AUTOINCREMENT  PRIMARY KEY,
    #         StudentId INTEGER NOT NULL,
    #         ClassName TEXT(10) NOT NULL,
    #         ClassGroup INTEGER NOT NULL,
    #         Senior TEXT(10) NOT NULL,
    #         RealName TEXT(10) NOT NULL,
    #         DharmaName TEXT(2) NOT NULL,
    #         Deacon TEXT(10) NOT NULL,
    #         Gender TEXT(1) NOT NULL
    #     )
    # """)
    #
    # query = f'INSERT INTO {table_name} (StudentId,ClassName,ClassGroup,Senior,RealName,DharmaName,Deacon,Gender) VALUES (?,?,?,?,?,?,?,?)'
    # results = []
    #
    # for entity in service.read_google_class_members():
    #     results.append([
    #         entity.student_id,
    #         entity.class_name,
    #         entity.class_group,
    #         entity.senior,
    #         entity.real_name,
    #         entity.dharma_name,
    #         entity.deacon,
    #         entity.gender,
    #     ])
    #
    # supplier = (lambda y=x: x for x in results)
    # return pz_db.prepared_update(query, supplier)
