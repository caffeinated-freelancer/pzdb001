from pz.config import PzProjectConfig
from pz.models.general_processing_error import GeneralProcessingError
from pz.models.google_member_relation import GoogleMemberRelation
from pz.models.vertical_member_lookup_result import VerticalMemberLookupResult
from pz.vlookup_commons import vertical_member_lookup
from services.access_db_migration import AccessDBMigration
from services.grand_member_service import PzGrandMemberService
from services.member_merging_service import MemberMergingService
from services.mysql_import_and_fetching import MySqlImportAndFetchingService
from services.new_class_senior_service import NewClassSeniorService


def write_access_to_mysql(cfg: PzProjectConfig) -> int:
    """
        把 Access 資料庫的東西寫到 MySQL
    """
    merging_service = MemberMergingService(cfg.ms_access_db.db_file, cfg.ms_access_db.target_table)
    mysql_import_and_fetching = MySqlImportAndFetchingService(cfg)
    return mysql_import_and_fetching.access_db_member_to_mysql(merging_service)


def write_google_to_mysql(cfg: PzProjectConfig, check_formula: bool = False) -> int:
    """
        把 Google 資料的學員學長資料東西寫到 MySQL
    """
    mysql_import_and_fetching = MySqlImportAndFetchingService(cfg)
    return mysql_import_and_fetching.google_class_members_to_mysql(check_formula=check_formula)


def handle_lookup(gms: PzGrandMemberService, entry: GoogleMemberRelation) -> VerticalMemberLookupResult:
    student_id: int | None = None
    if entry.studentId is not None and entry.studentId.isdigit():
        student_id = int(entry.studentId)
    have_birthday_or_phone = False

    if entry.birthday is not None and entry.birthday.isdigit():
        have_birthday_or_phone = True
    if entry.phone is not None and entry.phone.isdigit():
        have_birthday_or_phone = True

    return vertical_member_lookup(gms, student_id, entry.fullName, entry.dharmaName, have_birthday_or_phone)


def write_google_relation_to_mysql(cfg: PzProjectConfig) -> tuple[int, list[GeneralProcessingError]]:
    gms = PzGrandMemberService(cfg, deacons=NewClassSeniorService.read_all_seniors(cfg))
    mysql_import_and_fetching = MySqlImportAndFetchingService(cfg)

    return mysql_import_and_fetching.google_relation_to_mysql(lambda x: handle_lookup(gms, x))


def migrate_access_table_to_mysql(cfg: PzProjectConfig) -> int:
    mig = AccessDBMigration(cfg)
    return mig.migrate()
