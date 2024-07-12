from loguru import logger

from pz.config import PzProjectConfig
from pz.models.auto_assignment_step import AutoAssignmentStepEnum
from pz.models.mix_member import MixMember
from pz.models.new_class_senior import NewClassSeniorModel
from pz.models.signup_next_info import SignupNextInfoModel
from services.excel_workbook_service import ExcelWorkbookService
from services.grand_member_service import PzGrandMemberService
from services.new_class_senior_service import NewClassSeniorService
from services.prev_senior_service import PreviousSeniorService


class PendingGroup:
    className: str
    members: list[MixMember]

    def __init__(self, class_name: str):
        self.className = class_name
        self.members = []

    def add_member(self, mix_member: MixMember):
        self.members.append(mix_member)


class SignupMemberEntry:
    entry: SignupNextInfoModel
    member: MixMember
    signups: set[str]

    def __init__(self, entry: SignupNextInfoModel, member: MixMember, signups: set[str]):
        self.entry = entry
        self.member = member
        self.signups = signups


class SignupNextInfoService:
    ACCEPTABLE_SIGNUP = (
        '日初', '日中', '日高', '日研',
        '夜初', '夜中', '夜高', '夜研',
    )
    config: PzProjectConfig
    member_service: PzGrandMemberService
    prev_senior_service: PreviousSeniorService
    new_class_senior_service: NewClassSeniorService
    all_pending_groups: list[dict[str, PendingGroup]]
    signup_next_by_student_id: dict[int, dict[str, MixMember]]
    all_signup_entries: list[SignupMemberEntry]

    def __init__(self, cfg: PzProjectConfig, member_service: PzGrandMemberService,
                 previous_senior_service: PreviousSeniorService, new_class_senior_service: NewClassSeniorService):
        self.config = cfg
        self.member_service = member_service
        self.prev_senior_service = previous_senior_service
        self.new_class_senior_service = new_class_senior_service
        self.signup_next_by_student_id = {}
        self.all_pending_groups = []
        self.all_signup_entries = []

    def is_signup(self, student_id: int, class_name: str) -> bool:
        if student_id in self.signup_next_by_student_id:
            return class_name in self.signup_next_by_student_id[student_id]
        return False

    def pre_processing(self):
        workbook = ExcelWorkbookService(SignupNextInfoModel({}), self.config.excel.signup_next_info.spreadsheet_file,
                                        header_at=self.config.excel.signup_next_info.header_row,
                                        debug=False)

        entries: list[SignupNextInfoModel] = workbook.read_all(required_attribute='fullName')

        logger.info(f'{len(entries)} entries read from {self.config.excel.signup_next_info.spreadsheet_file}')

        self.all_signup_entries = []

        for entry in entries:
            signups = set([x for x in [entry.signup1, entry.signup2] if x is not None and x in self.ACCEPTABLE_SIGNUP])

            if len(signups) == 0:
                continue

            member_tuple = self.member_service.find_grand_member_by_student_id(entry.studentId, prefer=entry.className)

            if member_tuple is None:
                logger.warning(f'糟糕: {entry.studentId} / {entry.fullName} 不存在資料庫')
                continue

            # if member_tuple[1] is not None and member_tuple[1].class_name != entry.className:
            #     for m in member_tuples:
            #         if m[1] is not None and m[1].class_name == entry.className:
            #             member_tuple = m
            #             print(entry.className)
            #             print(member_tuple[1].to_json())
            #             break

            mix_member = MixMember(member_tuple[0], member_tuple[1], None, entry)

            if entry.studentId not in self.signup_next_by_student_id:
                self.signup_next_by_student_id[entry.studentId] = {}

            for signup in signups:
                self.signup_next_by_student_id[entry.studentId][signup] = mix_member
                self.new_class_senior_service.add_willingness(signup, mix_member)

            self.all_signup_entries.append(SignupMemberEntry(entry, mix_member, signups))

    def processing_signups(self):
        # workbook = ExcelWorkbookService(SignupNextInfoModel({}), self.config.excel.signup_next_info.spreadsheet_file,
        #                                 header_at=self.config.excel.signup_next_info.header_row,
        #                                 debug=False)
        #
        # entries: list[SignupNextInfoModel] = workbook.read_all(required_attribute='fullName')
        # entries = self.all_signup_entries

        # logger.info(f'{len(entries)} entries read from {self.config.excel.signup_next_info.spreadsheet_file}')

        current_senior = ''
        senior_jobs: list[NewClassSeniorModel] = []

        debug = False
        # pending_signups: dict[str, list[MixMember]] = {}
        pending_groups: dict[str, PendingGroup] = {}

        logger.warning(f'Assignment Step {AutoAssignmentStepEnum.CLASS_UPGRADE}')

        for signup_entry in self.all_signup_entries:
            entry = signup_entry.entry
            signups = signup_entry.signups
            mix_member = signup_entry.member

            # signups = set([x for x in [entry.signup1, entry.signup2] if x is not None and x in self.ACCEPTABLE_SIGNUP])
            #
            # if len(signups) == 0:
            #     continue
            #
            # member_tuple = self.member_service.find_grand_member_by_student_id(entry.studentId, prefer=entry.className)
            #
            # if member_tuple is None:
            #     logger.warning(f'糟糕: {entry.studentId} / {entry.fullName} 不存在資料庫')
            #     continue
            #
            # # if member_tuple[1] is not None and member_tuple[1].class_name != entry.className:
            # #     for m in member_tuples:
            # #         if m[1] is not None and m[1].class_name == entry.className:
            # #             member_tuple = m
            # #             print(entry.className)
            # #             print(member_tuple[1].to_json())
            # #             break
            #
            # mix_member = MixMember(member_tuple[0], member_tuple[1], None, entry)
            #
            # if entry.studentId not in self.signup_next_by_student_id:
            #     self.signup_next_by_student_id[entry.studentId] = set()
            #
            # for signup in signups:
            #     self.signup_next_by_student_id[entry.studentId].add(signup)

            if entry.senior != current_senior:
                # for signup, members in pending_signups.items():
                #     self.new_class_senior_service.add_to_pending_in_group(signup, members)
                # pending_signups = {}

                if len(pending_groups) > 0:
                    self.all_pending_groups.append(pending_groups)
                pending_groups = {}

                current_senior = entry.senior

                senior_jobs = self.prev_senior_service.find_previous_senior(entry.className, entry.groupId)
                if len(senior_jobs) > 0:
                    for job in senior_jobs:
                        logger.trace(
                            f'學長 {current_senior} 原班: {entry.className}/{entry.groupId}, 新班: {job.className}/{job.groupId}')
                elif current_senior is not None and current_senior != '':
                    logger.trace(
                        f'學長 {current_senior} 原班: {entry.className}/{entry.groupId}, 沒帶新班')

            if len(senior_jobs) > 0:
                found = False
                for job in senior_jobs:
                    if job.className in signups:
                        reason = f'升班調查 配置 ({entry.className}/{entry.groupId}) 至原學長 {job.fullName}, 班級 {job.className}/{job.groupId}'
                        self.new_class_senior_service.add_member_to(
                            job, mix_member, reason, AutoAssignmentStepEnum.PREVIOUS_SENIOR_FOLLOWING)
                        logger.trace(reason)
                        signups.remove(job.className)
                        found = True
                if not found:
                    if debug:
                        print(f'retain {entry.fullName}/{entry.senior} from {signups}')

            if len(signups) > 0:
                for signup in signups:

                    # if mix_member.classMember is not None and mix_member.classMember.class_name != signup:
                    #     member_tuple = member_tuples[0]
                    #     for m in member_tuples:
                    #         if m[1] is not None and m[1].class_name == entry.className:
                    #             member_tuple = m
                    #             print(signup)
                    #             print(mix_member.classMember.to_json())
                    #             print(member_tuple[1].to_json())
                    #             raise Exception
                    #             break
                    #
                    #     mix_member = MixMember(member_tuple[0], member_tuple[1], None, entry)

                    # if signup not in pending_signups:
                    #     pending_signups[signup] = [mix_member]
                    # else:
                    #     pending_signups[signup].append(mix_member)

                    if signup not in pending_groups:
                        pending_groups[signup] = PendingGroup(signup)

                    pending_groups[signup].add_member(mix_member)
                    # self.new_class_senior_service.add_to_pending_assignment(signup, mix_member)

                # current_senior = entry.senior
                # entry.signups = signups
                # signup_entries.append(mix_member)
            # senior_now = self.prev_senior_service.find_previous_senior(entry.className, entry.groupId)
            # if senior_now is not None:
            #     for signup in signups:
            #         if signup == senior_now.className:
            #             pass

        # for signup, members in pending_signups.items():
        #     self.new_class_senior_service.add_to_pending_in_group(signup, members)

        if len(pending_groups) > 0:
            self.all_pending_groups.append(pending_groups)

    def add_to_pending_groups(self):
        for entry in self.all_pending_groups:
            for signup, group in entry.items():
                self.new_class_senior_service.add_to_pending_in_group(signup, group.members)

    # def follow(self, student_id: int, class_name: str, mix_member: MixMember):
    #     if student_id in self.signup_next_by_student_id:
    #         if class_name in self.signup_next_by_student_id[student_id]:
    #             member = self.signup_next_by_student_id[student_id][class_name]
    #             logger.error(
    #                 f'{mix_member.get_full_name()} follow {student_id} ({member.get_full_name()}) at {class_name}')
    #         else:
    #             logger.error(f'{mix_member.get_full_name()} follow {student_id} at {class_name} but not found')
