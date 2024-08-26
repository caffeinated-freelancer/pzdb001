from typing import Callable, Any

from loguru import logger

from debugging.check import debug_on_student_id
from pz.config import PzProjectConfig
from pz.models.auto_assignment_step import AutoAssignmentStepEnum
from pz.models.mix_member import MixMember
from pz.models.new_class_senior import NewClassSeniorModel
from pz.models.general_processing_error import GeneralProcessingError
from pz.models.signup_next_info import SignupNextInfoModel
from pz.pz_commons import ACCEPTABLE_CLASS_NAMES
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

    def get_student_id(self) -> int | None:
        return self.member.get_student_id()

    def get_full_name(self) -> str:
        return self.member.get_full_name()

    def get_current_class_name(self) -> str:
        if self.member.classMember is not None:
            return self.member.classMember.class_name
        else:
            return ''


class SignupNextInfoService:
    config: PzProjectConfig
    member_service: PzGrandMemberService
    prev_senior_service: PreviousSeniorService
    new_class_senior_service: NewClassSeniorService
    all_pending_groups: list[dict[str, PendingGroup]]
    signup_next_by_student_id: dict[int, dict[str, MixMember]]
    all_signup_entries: list[SignupMemberEntry]
    signup_entry_by_student_id: dict[int, SignupMemberEntry]  # for Table B

    def __init__(self, cfg: PzProjectConfig, member_service: PzGrandMemberService,
                 previous_senior_service: PreviousSeniorService, new_class_senior_service: NewClassSeniorService):
        self.config = cfg
        self.member_service = member_service
        self.prev_senior_service = previous_senior_service
        self.new_class_senior_service = new_class_senior_service
        self.signup_next_by_student_id = {}
        self.all_pending_groups = []
        self.all_signup_entries = []
        self.signup_entry_by_student_id = {}  # for Table B

    def is_signup(self, student_id: int, class_name: str) -> bool:
        if student_id in self.signup_next_by_student_id:
            return class_name in self.signup_next_by_student_id[student_id]
        return False

    def db_as_signup_next(self) -> list[SignupNextInfoModel]:
        entries: list[SignupNextInfoModel] = []
        for member in self.member_service.all_class_members:
            entry = SignupNextInfoModel({})
            entry.studentId = member.student_id
            entry.fullName = member.real_name
            entry.dharmaName = member.dharma_name
            entry.className = member.class_name
            entry.groupId = member.class_group
            entry.senior = member.senior
            entry.signups = set()

            if member.signupClasses is not None and len(member.signupClasses) > 0:
                entry.signups = set([x for x in member.signupClasses if x in ACCEPTABLE_CLASS_NAMES])
                logger.trace(f'{entry.fullName} - {entry.signups} {member.signupClasses}')
            entries.append(entry)
        return entries

    def pre_processing(self, from_excel: bool = False, for_table_b: bool = False) -> list[GeneralProcessingError]:
        """
        讀取昇班調查, 主要目的在記載學員的昇班意願, 而不在處理分班分組。
        :param from_excel: 資料讀取自 Excel 而不是 Google 上的昇班調查
        :param for_table_b: Table B 是有預設分組的表。
        :return: 錯誤清單
        """
        errors: list[GeneralProcessingError] = []

        if from_excel:
            workbook = ExcelWorkbookService(SignupNextInfoModel({}),
                                            self.config.excel.signup_next_info.spreadsheet_file,
                                            header_at=self.config.excel.signup_next_info.header_row,
                                            debug=False)

            entries: list[SignupNextInfoModel] = workbook.read_all(required_attribute='fullName')

            logger.info(
                f'升班調查 {len(entries)} 筆資料, 資料來源 {self.config.excel.signup_next_info.spreadsheet_file}')
        else:
            entries: list[SignupNextInfoModel] = self.db_as_signup_next()
            logger.info(f'升班調查 {len(entries)} 筆資料, 資料來自 Google 試算表下到資料庫中的快取')

        self.all_signup_entries = []

        for entry in entries:
            if from_excel:
                signups = set(
                    [x for x in [entry.signup1, entry.signup2] if x is not None and x in ACCEPTABLE_CLASS_NAMES])
            else:
                signups = set(entry.signups)

            if len(signups) == 0 and not for_table_b:
                continue

            member_tuple = self.member_service.find_grand_member_by_student_id(entry.studentId, prefer=entry.className)

            if member_tuple is None:
                error_message = f'糟糕: {entry.studentId} / {entry.fullName} 不存在資料庫'
                logger.error(error_message)
                errors.append(GeneralProcessingError.error(error_message))
                continue

            mix_member = MixMember(member_tuple[0], member_tuple[1], None, entry)

            if entry.studentId not in self.signup_next_by_student_id:
                self.signup_next_by_student_id[entry.studentId] = {}

            for signup in signups:
                self.signup_next_by_student_id[entry.studentId][signup] = mix_member
                self.new_class_senior_service.add_willingness(signup, mix_member)

            signup_member_entry = SignupMemberEntry(entry, mix_member, signups)

            self.signup_entry_by_student_id[entry.studentId] = signup_member_entry

            self.all_signup_entries.append(signup_member_entry)
            if debug_on_student_id(entry.studentId):
                logger.error(
                    f'{signup_member_entry.get_full_name()} add to all_signup_entries {signup_member_entry.signups}')

        return errors

    def processing_signups(self):
        current_senior = ''
        senior_jobs: list[NewClassSeniorModel] = []

        debug = False
        # pending_signups: dict[str, list[MixMember]] = {}
        pending_groups: dict[str, PendingGroup] = {}

        logger.debug(f'Assignment Step {AutoAssignmentStepEnum.CLASS_UPGRADE}')

        for signup_entry in self.all_signup_entries:
            entry = signup_entry.entry
            signups = signup_entry.signups
            mix_member = signup_entry.member

            logger_trace: Callable[[Any], None] = lambda x: logger.trace(x)

            debug = debug_on_student_id(entry.studentId)
            if debug:
                logger_trace = lambda x: logger.error(x)

            if debug:
                logger.error(f'{entry.fullName} {entry.studentId} {entry.className} {entry.signups} {signups}')

            if entry.senior != current_senior:
                if len(pending_groups) > 0:
                    self.all_pending_groups.append(pending_groups)
                pending_groups = {}

                current_senior = entry.senior

                senior_jobs = self.prev_senior_service.find_previous_senior(entry.className, entry.groupId)
                if len(senior_jobs) > 0:
                    for job in senior_jobs:
                        logger_trace(
                            f'學長 {current_senior} 原班: {entry.className}/{entry.groupId}, 新班: {job.className}/{job.groupId}')
                elif current_senior is not None and current_senior != '':
                    logger_trace(
                        f'學長 {current_senior} 原班: {entry.className}/{entry.groupId}, 沒帶新班')

            if len(senior_jobs) > 0:
                found = False
                for job in senior_jobs:
                    if job.className in signups:
                        reason = f'升班調查 {entry.fullName} 配置 ({entry.className}/{entry.groupId}) 至原學長 {job.fullName}, 班級 {job.className}/{job.groupId}'
                        self.new_class_senior_service.add_member_to(
                            job, mix_member, reason, AutoAssignmentStepEnum.PREVIOUS_SENIOR_FOLLOWING,
                            non_follower_only=True)
                        logger_trace(reason)
                        signups.remove(job.className)
                        found = True
                if not found:
                    logger_trace(f'retain {entry.fullName}/{entry.senior} from {signups}')

            if len(signups) > 0:
                for signup in signups:
                    if signup not in pending_groups:
                        pending_groups[signup] = PendingGroup(signup)
                    pending_groups[signup].add_member(mix_member)

        if len(pending_groups) > 0:
            self.all_pending_groups.append(pending_groups)

    def add_to_pending_groups(self):
        for entry in self.all_pending_groups:
            for signup, group in entry.items():
                self.new_class_senior_service.add_to_pending_in_group(signup, group.members)

    def _find_me_at_other_places(self, entry: SignupMemberEntry) -> list[SignupMemberEntry]:
        # FIXME: 學長的升班意願填寫位置
        # 先找學長目前的所有班級及學長
        other_places: list[SignupMemberEntry] = []

        for e in self.all_signup_entries:
            if entry.member.classMember is not None:
                if entry.member.get_student_id() == e.member.get_student_id() and entry.member.classMember.class_name != e.member.classMember.class_name:
                    other_places.append(e)
        return other_places

    def _fix_senior_willingness_location(self, entry: SignupMemberEntry,
                                         other_places: list[SignupMemberEntry]):
        logger.debug(
            f'學長升班調整: {entry.member.get_full_name()} {entry.member.classMember.class_name}, 升班意願: {entry.signups}, 本期上課:{[
                x.member.classMember.class_name for x in other_places
            ]}')

        all_signups = set()
        all_signups.update(entry.signups)

        current_entries: list[SignupMemberEntry] = [entry]

        for other in other_places:
            if len(other.signups) > 0:
                logger.debug(f'(其它) 目前班別 {other.member.classMember.class_name}, 升班意願: {other.signups}')
                all_signups.update(other.signups)
            current_entries.append(other)

        student_id = entry.get_student_id()

        if student_id is None:
            raise Exception(f'糟糕, 竟然不知道學長的學號: {entry.get_full_name()}')
        if entry.member.classMember is None:
            raise Exception(f'糟糕, 竟然沒有班級: {entry.get_full_name()}')

        # jobs = self.new_class_senior_service.get_senior_by_student_id(student_id)
        #
        # for job in jobs:
        #     if job.className in all_signups:
        #         logger.debug(f'{entry.get_full_name()}: remove {job.className}')
        #         all_signups.remove(job.className)

        if len(all_signups) > 0:
            changed_signup = set()

            for signup in all_signups:
                for e in current_entries:
                    if signup == e.get_current_class_name():
                        changed_signup.add(signup)

            logger.info(f'{entry.get_full_name()}: 升班意願: {all_signups}, 現況: {[
                x.get_current_class_name() for x in current_entries
            ]}, {[
                x.member.classMember.senior for x in current_entries
            ]}, {[
                x.signups for x in current_entries
            ]}')

            if len(changed_signup) > 0:
                have_changed = False
                for signup in all_signups:
                    if signup in changed_signup:
                        for e in current_entries:
                            if signup == e.get_current_class_name():
                                if signup not in e.signups:
                                    e.signups.add(signup)
                                    logger.info(
                                        f'{entry.get_full_name()}: 增加意願 {signup} 在 {e.get_current_class_name()}/{e.member.classMember.senior} 填寫的資料')
                                    have_changed = True
                            elif signup in e.signups:
                                e.signups.remove(signup)
                                logger.info(
                                    f'{entry.get_full_name()}: 刪除意願 {signup} 在 {e.get_current_class_name()}/{e.member.classMember.senior} 填寫的資料')
                                have_changed = True
                if have_changed:
                    logger.info(f'{entry.get_full_name()}: 升班意願: {all_signups}, 調整後: {[
                        x.get_current_class_name() for x in current_entries
                    ]}, {[
                        x.member.classMember.senior for x in current_entries
                    ]}, {[
                        x.signups for x in current_entries
                    ]}')

    def fix_senior_willingness(self):
        for entry in self.all_signup_entries:
            if entry.member.classMember is not None:
                if entry.member.classMember.senior == entry.member.get_full_name():
                    if len(entry.signups) > 0:
                        other_places: list[SignupMemberEntry] = self._find_me_at_other_places(entry)
                        if len(other_places) > 0:
                            self._fix_senior_willingness_location(entry, other_places)

    def find_by_student_id_for_table_b(self, student_id: int) -> SignupMemberEntry | None:
        if student_id in self.signup_entry_by_student_id:
            return self.signup_entry_by_student_id[student_id]
        return None
