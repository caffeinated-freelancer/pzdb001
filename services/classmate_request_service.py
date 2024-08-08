from pz.models.mix_member import MixMember
from pz.models.pz_questionnaire_info import PzQuestionnaireInfo
from pz.models.questionnaire_entry import QuestionnaireEntry


class NonMemberClassmateRequest:
    followee: QuestionnaireEntry
    follower: MixMember

    def __init__(self, followee: QuestionnaireEntry, follower: MixMember):
        self.followee = followee
        self.follower = follower


class ClassmateRequestService:
    requests: list[NonMemberClassmateRequest] = []

    @classmethod
    def initialize(cls):
        cls.requests = []

    @classmethod
    def add_request(cls, followee: QuestionnaireEntry, follower: MixMember):
        cls.requests.append(NonMemberClassmateRequest(followee, follower))

    @classmethod
    def count(cls):
        return len(cls.requests)

    @classmethod
    def all_requests(cls):
        return cls.requests
