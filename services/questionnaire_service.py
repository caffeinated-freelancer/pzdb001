from loguru import logger

from pz.config import PzProjectConfig
from pz.models.auto_assignment_step import AutoAssignmentStepEnum
from pz.models.dispatching_status import DispatchingStatus
from pz.models.mix_member import MixMember
from pz.models.pz_questionnaire_info import PzQuestionnaireInfo
from pz.models.questionnaire_entry import QuestionnaireEntry
from pz.models.senior_report_error_model import SeniorReportError
from pz.pz_commons import phone_number_normalize
from pz.utils import full_name_to_names
from services.excel_workbook_service import ExcelWorkbookService
from services.grand_member_service import PzGrandMemberService
from services.new_class_senior_service import NewClassSeniorService
from services.prev_senior_service import PreviousSeniorService
from services.signup_next_info_service import SignupNextInfoService


class QuestionnaireService:
    config: PzProjectConfig
    member_service: PzGrandMemberService
    prev_senior_service: PreviousSeniorService
    new_senior_service: NewClassSeniorService
    signup_next_service: SignupNextInfoService
    all_questionnaires_entries: list[QuestionnaireEntry]
    questionnaire_dict: dict[str, QuestionnaireEntry]

    def __init__(self, config: PzProjectConfig, member_service: PzGrandMemberService,
                 prev_senior_service: PreviousSeniorService, new_senior_service: NewClassSeniorService,
                 signup_next_service: SignupNextInfoService):
        self.config = config
        self.member_service = member_service
        self.prev_senior_service = prev_senior_service
        self.new_senior_service = new_senior_service
        self.signup_next_service = signup_next_service
        self.all_questionnaires_entries = []
        self.questionnaire_dict: dict[str, QuestionnaireEntry] = {}

    @staticmethod
    def questionnaire_key(name: str, phone_number: str, gender: str) -> str:
        if phone_number is None:
            phone_number = 'None'
        return f'{name}_{phone_number_normalize(phone_number)}_{gender}'

    def get_questionnaire(self, name: str, phone_number: str, gender: str) -> QuestionnaireEntry | None:
        key = self.questionnaire_key(name, phone_number, gender)
        if key in self.questionnaire_dict:
            return self.questionnaire_dict[key]
        return None

    def save_questionnaire(self, questionnaire: QuestionnaireEntry) -> bool:
        key = self.questionnaire_key(questionnaire.entry.fullName, questionnaire.entry.mobilePhone,
                                     questionnaire.entry.gender)
        if key in self.questionnaire_dict:
            logger.warning(f'{questionnaire.entry.fullName} {questionnaire.entry.mobilePhone} 意願調查資料重複')
            return False
        self.questionnaire_dict[key] = questionnaire
        return True

    def pre_processing(self, spreadsheet_file: str, from_scratch: bool = True) -> list[SeniorReportError]:
        errors: list[SeniorReportError] = []
        self.all_questionnaires_entries = []

        service = ExcelWorkbookService(PzQuestionnaireInfo({}), spreadsheet_file,
                                       self.config.excel.questionnaire.sheet_name,
                                       header_at=self.config.excel.questionnaire.header_row,
                                       debug=False)
        entries: list[PzQuestionnaireInfo] = service.read_all(required_attribute='fullName')

        logger.debug(
            f'Assignment Step {AutoAssignmentStepEnum.INTRODUCER_AS_SENIOR} / {AutoAssignmentStepEnum.INTRODUCER_FOLLOWING}')
        for entry in entries:
            if entry.registerClass is not None and entry.registerClass != '':  # 所有有意願調查有指定班級的
                class_name = entry.registerClass.replace('班', '')
                entry.mobilePhone = phone_number_normalize(entry.mobilePhone)
                entry.mobilePhone2 = phone_number_normalize(entry.mobilePhone2)
                entry.registerClass = class_name

                name_tuple = full_name_to_names(entry.fullName)
                matched_members = self.member_service.find_relax_grand_member_by_pz_name(entry.fullName, debug=False)
                mix_member = None
                newbie = True

                for m in matched_members:
                    if m[0].birthday == entry.birthday and m[0].gender == entry.gender:
                        mix_member = MixMember(m[0], m[1], entry, None)
                        if m[1] is None:
                            logger.info(
                                f'舊生回歸: {name_tuple[0]} (學號: {mix_member.get_unique_id()}) -> 報名 {class_name}, 介紹人: {entry.introducerName})')
                        newbie = False
                    else:
                        logger.trace(
                            f'{name_tuple[0]} {entry.birthday} vs {m[0].birthday}, {entry.gender} vs {m[0].gender}')

                if mix_member is None:
                    # 新學員
                    mix_member = MixMember(None, None, entry, None)
                    logger.trace(
                        f'新生: [{name_tuple[0]}] ({mix_member.get_unique_id()}) added [{entry.birthday}]/[{entry.gender}] (matched:{len(matched_members)})')

                self.new_senior_service.add_willingness(class_name, mix_member)

                introducer = self.member_service.find_one_class_member_by_pz_name(entry.introducerName)

                self.all_questionnaires_entries.append(
                    QuestionnaireEntry(entry, mix_member, introducer, newbie, DispatchingStatus.WAITING))

        if not from_scratch:
            for questionnaire_entry in self.all_questionnaires_entries:
                self.save_questionnaire(questionnaire_entry)
            return errors

        for questionnaire_entry in self.all_questionnaires_entries:
            entry = questionnaire_entry.entry
            introducer = questionnaire_entry.introducer
            mix_member = questionnaire_entry.member

            if introducer is not None:
                if introducer.gender == entry.gender and introducer.student_id != mix_member.get_unique_id():
                    jobs = self.new_senior_service.get_senior_by_student_id(introducer.student_id)
                    for job in jobs:
                        if job.className == entry.registerClass and job.gender == entry.gender:
                            reason = f'意願調查: {entry.fullName}/{entry.gender} 加入介紹人 {job.fullName} {job.className}/{job.groupId}'
                            logger.debug(reason)
                            self.new_senior_service.add_member_to(
                                job, mix_member, reason, AutoAssignmentStepEnum.INTRODUCER_AS_SENIOR)
                            questionnaire_entry.dispatching_status = DispatchingStatus.ASSIGNED
                    if mix_member.senior is None:
                        # logger.warning(f'checking {mix_member.get_full_name()} on {entry.registerClass}')
                        if (self.signup_next_service.is_signup(introducer.student_id, entry.registerClass) or
                                self.new_senior_service.have_willingness_by_unique_id(
                                    entry.registerClass, entry.gender, introducer.student_id)):
                            logger.trace(
                                f'(follow {entry.registerClass}) {entry.fullName}/{mix_member.get_unique_id()} 跟介紹人 {introducer.real_name} 同班 {entry.registerClass}')
                            self.new_senior_service.follow(introducer, entry.registerClass,
                                                           mix_member)
                            # self.signup_next_service.follow(introducer.student_id, entry.registerClass,
                            #                                 mix_member)
                            questionnaire_entry.dispatching_status = DispatchingStatus.FOLLOW
                        else:
                            logger.trace(
                                f'[+] {entry.fullName} 介紹人 {introducer.real_name} 班級 {entry.registerClass}')
                    else:
                        logger.debug(
                            f'{entry.fullName}/{mix_member.get_unique_id()} 已經有學長 {mix_member.senior.fullName} at {entry.registerClass}')
        return errors

    def assign_having_senior_questionnaire(self):
        for questionnaires_entry in self.all_questionnaires_entries:
            entry = questionnaires_entry.entry

            mix_member = questionnaires_entry.member

            if questionnaires_entry.dispatching_status == DispatchingStatus.WAITING:
                if mix_member.classMember is not None:
                    prev_senior = mix_member.classMember.senior
                    senior_jobs = self.prev_senior_service.find_previous_senior(
                        mix_member.classMember.class_name, mix_member.classMember.class_group)

                    if len(senior_jobs) > 0:
                        for job in senior_jobs:
                            if job.fullName != prev_senior:
                                logger.warning(f'Warning: 學長姓名 從 {prev_senior} 變成 {job.fullName}')
                            else:
                                if job.className == entry.registerClass:
                                    reason = f'意願調查: {entry.fullName}/{entry.gender} 加入前學長 {job.fullName} {job.className}/{job.groupId}'
                                    logger.debug(reason)
                                    self.new_senior_service.add_member_to(
                                        job, mix_member, reason, AutoAssignmentStepEnum.PREVIOUS_SENIOR_FOLLOWING)
                                    questionnaires_entry.dispatching_status = DispatchingStatus.ASSIGNED
                    else:
                        logger.debug(f'之前的學長 {mix_member.classMember.senior} 沒有帶新班級')

                if mix_member.senior is None:  # 需要自動排的
                    self.new_senior_service.add_to_pending_assignment(entry.registerClass, mix_member)

        # for class_gender in class_members:
        #     # print(f'class: {class_gender}, member: {len(class_members[class_gender])}')
        #     for member in class_members[class_gender]:
        #         self.new_senior_service.min_member_first_assign(class_gender, member)

        # self.new_senior_service.find_by_class_gender(class_gender)
