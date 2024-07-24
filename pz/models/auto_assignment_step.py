import enum


class AutoAssignmentStepEnum(enum.Enum):
    PREDEFINED_SENIOR = enum.auto()  # 學長預排
    INTRODUCER_AS_SENIOR = enum.auto()  # 介紹人是學長
    INTRODUCER_FOLLOWING = enum.auto()  # 跟介紹人同班
    PREVIOUS_SENIOR_FOLLOWING = enum.auto()  # 跟隨以前的學長
    CLASSMATE_FOLLOWING = enum.auto()
    CLASS_UPGRADE = enum.auto()
    AUTO_ASSIGNMENT = enum.auto()
    TABLE_B_ASSIGNMENT = enum.auto()
    TABLE_B_ALGORITHM = enum.auto()
