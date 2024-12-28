from abc import ABC, abstractmethod


class GeneralUiService(ABC):
    @abstractmethod
    def perform_service(self):
        pass

    @abstractmethod
    def done(self):
        pass
