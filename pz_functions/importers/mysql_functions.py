from pz.config import PzProjectConfig
from services.member_merging_service import MemberMergingService
from services.mysql_import_and_fetching import MySqlImportAndFetchingService


def write_data_to_mysql(cfg: PzProjectConfig):
    """
        把 Access 資料庫的東西寫到 MySQL
    """
    merging_service = MemberMergingService(cfg.ms_access_db.db_file, cfg.ms_access_db.target_table)
    mysql_import_and_fetching = MySqlImportAndFetchingService(cfg)
    mysql_import_and_fetching.access_db_member_to_mysql(merging_service)
    mysql_import_and_fetching.google_class_members_to_mysql()
