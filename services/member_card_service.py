from loguru import logger

from pz.config import PzProjectConfig
from pz.ms_access.op import PzDbOperation


class MemberCardService:
    config: PzProjectConfig

    def __init__(self, cfg: PzProjectConfig):
        self.config = cfg

    def import_card_info_from_access(self):
        op = PzDbOperation(self.config.ms_access_db.db_file, self.config.ms_access_db.target_table)
        header, rows = op.read_all_from_table('card_electronic')
        student_id_index = header.index('StudentId')
        student_ids = [x[student_id_index] for x in rows]
        logger.debug(student_ids)
        logger.info(f'已發給電子福慧卡: {len(student_ids)}')
        header, rows = op.read_all_from_table('card_paper')
        student_id_index = header.index('StudentId')
        application_index = header.index('ApplicationDate')
        entries = [(x[student_id_index], x[application_index]) for x in rows]
        logger.debug(entries)
        logger.info(f'已申請紙本福慧卡: {len(student_ids)}')
