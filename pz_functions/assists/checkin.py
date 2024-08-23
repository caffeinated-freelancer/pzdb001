from typing import Any

from pz.config import PzProjectConfig
from pz.models.class_member_for_checkin import ClassMemberForCheckinModel
from pz.utils import get_formatted_datetime
from services.excel_creation_service import ExcelCreationService
from services.mysql_import_and_fetching import MySqlImportAndFetchingService


def export_class_member_for_checkin_system(cfg: PzProjectConfig):
    fetcher = MySqlImportAndFetchingService(cfg)
    entities = fetcher.read_checkin_class_member_view()

    service = ExcelCreationService(ClassMemberForCheckinModel([], []))

    data: list[list[Any]] = []

    for entity in entities:
        # print(entity.to_json())
        data.append(entity.get_values_in_pecking_order())
        # print(model.to_json())

    supplier = (lambda y=x: x for x in data)
    service.write_data(supplier)

    formatted_date_time = get_formatted_datetime()

    file_name = f'報到系統用-班級學員_{formatted_date_time}.xlsx'
    full_path_name = f'{cfg.output_folder}/{file_name}'
    service.save(full_path_name)
    return full_path_name


def export_all_members_for_checkin_system(cfg: PzProjectConfig):
    fetcher = MySqlImportAndFetchingService(cfg)
    entities = fetcher.read_checkin_member_only_view()

    service = ExcelCreationService(ClassMemberForCheckinModel([], []))

    data: list[list[Any]] = []

    for entity in entities:
        # print(entity.to_json())
        data.append(entity.get_values_in_pecking_order())
        # print(model.to_json())

    supplier = (lambda y=x: x for x in data)
    service.write_data(supplier)

    formatted_date_time = get_formatted_datetime()

    file_name = f'報到系統用-學員_{formatted_date_time}.xlsx'
    full_path_name = f'{cfg.output_folder}/{file_name}'
    service.save(full_path_name)
    return full_path_name
