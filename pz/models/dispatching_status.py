import enum


class DispatchingStatus(enum.Enum):
    WAITING = enum.auto()
    FOLLOW = enum.auto()
    ASSIGNED = enum.auto()
