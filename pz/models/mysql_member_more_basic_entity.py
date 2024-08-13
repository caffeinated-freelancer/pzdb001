from datetime import datetime

from .json_class import JSONClass


class MysqlMemberMoreBasicEntity(JSONClass):
    TABLE_NAME: str = 'member_more_basics'
    id: int
    additional: dict[str, str]
    updated_at: datetime

    def __init__(self, entity_id: int, additional: dict[str, str]) -> None:
        self.id = entity_id
        self.additional = additional

    @staticmethod
    def member_more_basics_creation() -> list[str]:
        creation_columns: list[str] = [
            "`id` int NOT NULL COMMENT 'Student ID'",
            "`additional` JSON DEFAULT NULL COMMENT '額外資訊'",
            "`updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
            "PRIMARY KEY (`id`)\n",
        ]
        return creation_columns
