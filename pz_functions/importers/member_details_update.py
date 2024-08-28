import glob
import os
import re

from loguru import logger

from pz.config import PzProjectConfig
from pz.models.member_detail_model import MemberDetailModel
from services.excel_workbook_service import ExcelWorkbookService
from services.mysql_import_and_fetching import MySqlImportAndFetchingService


class ExcelUpdateFile:
    fullPathName: str
    basename: str
    dirname: str
    short_name: str

    def __init__(self, filename: str):
        self.fullPathName = filename
        self.basename = os.path.basename(filename)
        self.dirname = os.path.dirname(filename)
        matched = re.match(r'(.*).xlsx', self.basename)

        if matched:
            self.short_name = matched.group(1)


class ImportMemberDetailsUpdateService:
    config: PzProjectConfig
    mysql: MySqlImportAndFetchingService

    def __init__(self, config: PzProjectConfig):
        self.config = config
        self.mysql = MySqlImportAndFetchingService(self.config)

    def process(self, excel_file: ExcelUpdateFile):
        service = ExcelWorkbookService(MemberDetailModel({}), excel_file.fullPathName,
                                       header_at=self.config.excel.member_details_update.header_row)

        entries: list[MemberDetailModel] = service.read_all(required_attribute='student_id')

        records, count = self.mysql.import_and_update(entries)
        logger.info(f'{excel_file.basename} -  匯入 {records} 筆資料, {count} 筆更新')
        service.close()


def _processing_file(cfg: PzProjectConfig, ordered_files: list[ExcelUpdateFile]):
    service = ImportMemberDetailsUpdateService(cfg)

    for file in ordered_files:
        service.process(file)


def member_details_update(cfg: PzProjectConfig) -> bool:
    if cfg.excel.member_details_update.spreadsheet_folder is None:
        logger.error('設定檔需要進一步修正')
        return False

    folder = cfg.excel.member_details_update.spreadsheet_folder

    if not os.path.isdir(folder):
        os.makedirs(folder)

    files = glob.glob(f'{folder}/*.xlsx')
    all_files: list[ExcelUpdateFile] = []

    for filename in files:
        f = os.path.basename(filename)
        if not f.startswith("~$"):
            try:
                all_files.append(ExcelUpdateFile(filename))
            except Exception as e:
                logger.warning(f'{filename} - {e}')

    ordered_files = [x for x in sorted(all_files, key=lambda x: x.basename)]
    logger.trace([x.basename for x in ordered_files])

    _processing_file(cfg, ordered_files)

    # now = datetime.datetime.now()
    # formatted_date_time = now.strftime("%Y-%m-%d_%H-%M-%S")
    #
    # for file in ordered_files:
    #     processed_file_name = f'{file.short_name}_{formatted_date_time}_{processed_ending}.xlsx'
    #
    #     counter = 5
    #
    #     while counter > 0:
    #         try:
    #             os.rename(file.fullPathName, f'{file.dirname}/{processed_file_name}')
    #             logger.info(f'檔名變更為 {processed_file_name}')
    #             break
    #         except FileNotFoundError as e:
    #             logger.error(f'File not found. ({str(e)})')
    #             break
    #         except OSError as e:
    #             print(f"Error renaming file: {e}")
    #             time.sleep(3)
    #         finally:
    #             counter -= 1
