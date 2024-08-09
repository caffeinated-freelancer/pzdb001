import enum
from enum import Enum


class GeneralProcessingErrorLevel(Enum):
    ERROR = enum.auto()
    WARNING = enum.auto()
    INFO = enum.auto()
    DEBUG = enum.auto()
    NONE = enum.auto()


class GeneralProcessingError:
    level: GeneralProcessingErrorLevel
    message: str

    def __init__(self, level: GeneralProcessingErrorLevel, message: str):
        self.level = level
        self.message = message

    def level_name(self):
        if self.level == GeneralProcessingErrorLevel.ERROR:
            return '錯誤'
        elif self.level == GeneralProcessingErrorLevel.WARNING:
            return '警告'
        elif self.level == GeneralProcessingErrorLevel.INFO:
            return '告知'
        elif self.level == GeneralProcessingErrorLevel.DEBUG:
            return 'DEBUG'
        else:
            return 'NONE'
    @staticmethod
    def warning(message: str) -> 'GeneralProcessingError':
        return GeneralProcessingError(GeneralProcessingErrorLevel.WARNING, message)

    @staticmethod
    def info(message: str) -> 'GeneralProcessingError':
        return GeneralProcessingError(GeneralProcessingErrorLevel.INFO, message)
    @staticmethod
    def error(message: str) -> 'GeneralProcessingError':
        return GeneralProcessingError(GeneralProcessingErrorLevel.ERROR, message)
