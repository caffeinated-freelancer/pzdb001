from abc import ABC, abstractmethod
from typing import Any


class GoogleSpreadSheetModelInterface(ABC):
    @abstractmethod
    def get_spreadsheet_title(self) -> str:
        pass

    @abstractmethod
    def get_column_names(self) -> list[str]:
        pass

    @abstractmethod
    def new_instance(self, args: list[Any]) -> 'GoogleSpreadSheetModelInterface':
        pass
