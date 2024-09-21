from pz.config import PzProjectConfig
from pz.models.mysql_class_member_entity import MysqlClassMemberEntity
from pz.models.new_class_senior import NewClassSeniorModel
from services.new_class_senior_service import NewClassSeniorService


class SeniorDeaconService:
    senior_deacons: dict[str, NewClassSeniorModel]
    class_senior: dict[str, NewClassSeniorModel]

    def __init__(self, cfg: PzProjectConfig):
        self.senior_deacons: dict[str, NewClassSeniorModel] = {}
        self.class_senior: dict[str, NewClassSeniorModel] = {}

        for senior in NewClassSeniorService.read_all_seniors(cfg):
            self.senior_deacons[self.senior_key(senior)] = senior
            if senior.senior is not None and senior.senior == '學長':
                self.class_senior[f'{senior.className}_{senior.groupId}'] = senior

    @staticmethod
    def senior_key(senior: NewClassSeniorModel) -> str:
        return f'{senior.className}_{senior.groupId}_{senior.fullName}_{senior.dharmaName}'

    def find_deacon(self, class_name: str, group_id: int, member: MysqlClassMemberEntity) -> str | None:
        key = f'{class_name}_{group_id}_{member.real_name}_{member.dharma_name}'

        if key in self.senior_deacons:
            entry = self.senior_deacons[key]
            if entry.deacon is not None and entry.deacon != '':
                return entry.deacon
            else:
                return entry.senior
        return None
