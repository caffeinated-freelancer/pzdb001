from abc import abstractmethod
from typing import Any

from pz.models.excel_model import ExcelModelInterface


class ExcelCreationModelInterface(ExcelModelInterface):
    @abstractmethod
    def get_excel_headers(self) -> list[str]:
        pass

    @abstractmethod
    def get_values_in_pecking_order(self) -> list[Any]:
        pass
