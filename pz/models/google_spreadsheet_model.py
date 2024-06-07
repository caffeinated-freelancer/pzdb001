from abc import ABC, abstractmethod


class GoogleSpreadSheetModelInterface(ABC):
    @abstractmethod
    def get_spreadsheet_title(self) -> str:
        pass

    @abstractmethod
    def get_column_names(self) -> list[str]:
        pass

    @abstractmethod
    def new_instance(self, args) -> 'GoogleSpreadSheetModelInterface':
        pass
