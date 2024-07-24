from pz.models.mix_member import MixMember
from pz.models.mysql_class_member_entity import MysqlClassMemberEntity
from pz.models.pz_questionnaire_info import PzQuestionnaireInfo
from pz.models.dispatching_status import DispatchingStatus


class QuestionnaireEntry:
    entry: PzQuestionnaireInfo
    member: MixMember
    introducer: MysqlClassMemberEntity | None
    newbie: bool
    dispatching_status: DispatchingStatus

    def __init__(self, entry: PzQuestionnaireInfo, member: MixMember, introducer: MysqlClassMemberEntity | None,
                 newbie: bool, dispatching_status: DispatchingStatus):
        self.entry = entry
        self.member = member
        self.introducer = introducer
        self.newbie = newbie
        self.dispatching_status = dispatching_status
