from pz.config import PzProjectConfig
from pz.models.mysql_member_relation_entity import MysqlMemberRelationEntity
from services.mysql_import_and_fetching import MySqlImportAndFetchingService


class MemberRelationService:
    config: PzProjectConfig

    def __init__(self, cfg: PzProjectConfig):
        self.config = cfg

    def load_relations(self, gender_care: bool = False):
        service = MySqlImportAndFetchingService(self.config)
        entries = service.read_member_relations()

        relations_by_key: dict[str, list[MysqlMemberRelationEntity]] = {}

        for entry in entries:
            for relation_key in entry.relationKeys:
                if relation_key in relations_by_key:
                    relations_by_key[relation_key].append(entry)
                else:
                    relations_by_key[relation_key] = [entry]
