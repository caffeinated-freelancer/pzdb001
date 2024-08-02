import enum
from enum import Enum


class SeniorReportErrorLevel(Enum):
    ERROR = enum.auto()
    WARNING = enum.auto()
    INFO = enum.auto()
    DEBUG = enum.auto()
    NONE = enum.auto()


class SeniorReportError:
    level: SeniorReportErrorLevel
    message: str

    def __init__(self, level: SeniorReportErrorLevel, message: str):
        self.level = level
        self.message = message

    def level_name(self):
        if self.level == SeniorReportErrorLevel.ERROR:
            return '錯誤'
        elif self.level == SeniorReportErrorLevel.WARNING:
            return '警告'
        elif self.level == SeniorReportErrorLevel.INFO:
            return 'INFO'
        elif self.level == SeniorReportErrorLevel.DEBUG:
            return 'DEBUG'
        else:
            return 'NONE'
    @staticmethod
    def warning(message: str) -> 'SeniorReportError':
        return SeniorReportError(SeniorReportErrorLevel.WARNING, message)

    @staticmethod
    def error(message: str) -> 'SeniorReportError':
        return SeniorReportError(SeniorReportErrorLevel.ERROR, message)
