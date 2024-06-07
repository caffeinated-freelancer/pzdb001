from abc import ABC, abstractmethod


class ExcelModelInterface(ABC):
    @abstractmethod
    def new_instance(self, args):
        pass
