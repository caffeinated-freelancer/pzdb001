from typing import Any

from pz.config import PzProjectConfig
from pz.models.member_detail_model import MemberDetailModel
from pz.utils import get_formatted_datetime
from services.excel_creation_service import ExcelCreationService
from services.mysql_import_and_fetching import MySqlImportAndFetchingService


def export_member_details(cfg: PzProjectConfig) -> str:
    fetcher = MySqlImportAndFetchingService(cfg)
    details = fetcher.read_member_details()
    model = MemberDetailModel({})

    service = ExcelCreationService(model)

    data: list[list[Any]] = []

    for detail in details:
        model = MemberDetailModel({}, entity=detail)
        data.append(model.get_values_in_pecking_order())
        # print(model.to_json())

    supplier = (lambda y=x: x for x in data)
    service.write_data(supplier)

    formatted_date_time = get_formatted_datetime()

    file_name = f'報到系統用學員資料_{formatted_date_time}.xlsx'
    service.save(f'{cfg.output_folder}/{file_name}')
    return file_name
