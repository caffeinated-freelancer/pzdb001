from pz.models.new_class_senior import NewClassSeniorModel
from services.grand_member_service import PzGrandMemberService
from services.new_class_senior_service import NewClassSeniorService


class PreviousSeniorService:
    member_service: PzGrandMemberService
    new_senior_service: NewClassSeniorService
    prev_class_senior_map: dict[str, list[NewClassSeniorModel]]  # 舊的班級學長到哪了

    def __init__(self, member_service: PzGrandMemberService, new_senior_service: NewClassSeniorService):
        self.member_service = member_service
        self.new_senior_service = new_senior_service

        prev_seniors = self.member_service.read_all_seniors()
        self.prev_class_senior_map = {}

        # 先前的學長是否還繼續當學長
        for senior in prev_seniors:
            models = self.new_senior_service.get_senior_by_student_id(senior.student_id)
            self.prev_class_senior_map[self.class_group_as_key(senior.class_name, senior.class_group)] = models

    @staticmethod
    def class_group_as_key(class_name: str, group_id: int) -> str:
        return f'{class_name}-{group_id}'

    def find_previous_senior(self, class_name: str, group_id: int) -> list[NewClassSeniorModel]:
        key = self.class_group_as_key(class_name, group_id)

        if key in self.prev_class_senior_map:
            return self.prev_class_senior_map[key]
        return []
