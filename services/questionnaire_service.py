import re

from loguru import logger

from pz.config import PzProjectConfig
from pz.models.auto_assignment_step import AutoAssignmentStepEnum
from pz.models.dispatching_status import DispatchingStatus
from pz.models.mix_member import MixMember
from pz.models.mysql_class_member_entity import MysqlClassMemberEntity
from pz.models.pz_questionnaire_info import PzQuestionnaireInfo
from pz.models.questionnaire_entry import QuestionnaireEntry
from pz.models.general_processing_error import GeneralProcessingError
from pz.pz_commons import phone_number_normalize
from pz.utils import full_name_to_names
from services.classmate_request_service import ClassmateRequestService
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
    non_member_classmates: dict[str, list[MixMember]]
    duplicate_detection_set: set[str]

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
        self.non_member_classmates: dict[str, list[MixMember]] = {}
        self.duplicate_detection_set: set[str] = set()

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

    @staticmethod
    def find_classmate_request(entry: PzQuestionnaireInfo) -> str | None:
        if entry.remark is not None and entry.remark is not None:
            remark = entry.remark
            if remark is not None and remark != '':
                matched = re.match(r'.*與(.{2,5})同組.*', remark)
                if matched:
                    logger.trace(f'{entry.fullName} 與 {matched.group(1)} 同組')
                    return matched.group(1)
        return None

    def check_duplication_and_save(self, entry: PzQuestionnaireInfo) -> bool:
        key = f'{entry.fullName}_{entry.mobilePhone}_{entry.gender}_{entry.registerClass}'
        if key in self.duplicate_detection_set:
            return True
        else:
            self.duplicate_detection_set.add(key)
            return False

    def pre_processing(self, spreadsheet_file: str) -> tuple[list[GeneralProcessingError], list[QuestionnaireEntry]]:
        errors: list[GeneralProcessingError] = []
        self.all_questionnaires_entries = []

        service = ExcelWorkbookService(PzQuestionnaireInfo({}), spreadsheet_file,
                                       self.config.excel.questionnaire.sheet_name,
                                       header_at=self.config.excel.questionnaire.header_row,
                                       debug=False)
        entries: list[PzQuestionnaireInfo] = service.read_all(required_attribute='fullName')
        logger.trace(f'{len(entries)} questionnaires in excel')

        self.non_member_classmates: dict[str, list[MixMember]] = {}

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

                if self.check_duplication_and_save(entry):
                    message = f'意願調查中, {entry.fullName}, 姓別: {entry.gender}, 班級: {entry.registerClass}, 行動電話 {entry.mobilePhone} 資料重複'
                    errors.append(GeneralProcessingError.warning(message))
                    logger.warning(message)
                    continue

                for m in matched_members:
                    if m[0] is not None and (m[0].birthday is None or m[0].gender is None):
                        if m[0].birthday is None:
                            message = f'意願調查中, {entry.fullName}/{entry.registerClass} 在基本資料中有同名, 但生日資料欠缺, 疑似學員編號為 {m[0].student_id}'
                        else:
                            message = f'意願調查中, {entry.fullName}/{entry.registerClass} 在基本資料中有同名, 但性別資料欠缺, 疑似學員編號為 {m[0].student_id}'
                        errors.append(GeneralProcessingError.warning(message))
                        logger.warning(message)
                    elif m[0].birthday == entry.birthday and m[0].gender == entry.gender:
                        mix_member = MixMember(m[0], m[1], entry, None)
                        if m[1] is None:
                            logger.debug(
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

                introducer: MysqlClassMemberEntity | None = None
                classmate = self.find_classmate_request(entry)

                if classmate is not None:
                    entry.classmate = classmate

                    introducer = self.member_service.find_one_class_member_by_pz_name(classmate)
                    logger.info(
                        f'{entry.fullName} 備註與 {classmate} 同組, {classmate} {"是" if introducer is not None else "不是"}學員, 介紹人 {entry.introducerName}')
                    if introducer is None:
                        if classmate in self.non_member_classmates:
                            self.non_member_classmates[classmate].append(mix_member)
                        else:
                            self.non_member_classmates[classmate] = [mix_member]

                if introducer is None:
                    introducer = self.member_service.find_one_class_member_by_pz_name(entry.introducerName)

                self.all_questionnaires_entries.append(
                    QuestionnaireEntry(entry, mix_member, introducer, classmate, newbie, DispatchingStatus.WAITING))

        # if not from_scratch:
        for questionnaire_entry in self.all_questionnaires_entries:
            self.save_questionnaire(questionnaire_entry)

        return errors, self.all_questionnaires_entries

    def pre_processing_non_member_classmate(self) -> list[GeneralProcessingError]:
        errors: list[GeneralProcessingError] = []

        ClassmateRequestService.initialize()
        # classmates_requests: list[NonMemberClassmateRequest] = []

        # def already_in_group(self, mix_member: MixMember):

        if len(self.non_member_classmates) > 0:
            non_same_class_followers: list[MixMember] = []
            have_followee: set[int] = set()

            for non_member_classmate, followers in self.non_member_classmates.items():
                for followee in self.all_questionnaires_entries:
                    if followee.entry.fullName == non_member_classmate:
                        for follower in followers:
                            if follower.questionnaireInfo.gender != followee.entry.gender:
                                non_same_class_followers.append(follower)
                                message = f'「{follower.questionnaireInfo.fullName}」想要跟「{followee.entry.fullName
                                }」同組, 但「{follower.questionnaireInfo.fullName}」是「{follower.questionnaireInfo.gender
                                }生」, 但「{followee.entry.fullName}」是「{followee.entry.gender}生」'
                                logger.warning(message)
                                errors.append(GeneralProcessingError.warning(message))
                            elif followee.entry.registerClass == follower.questionnaireInfo.registerClass:
                                ClassmateRequestService.add_request(followee, follower)
                                follower.questionnaireInfo.add_non_member_followee(followee)
                                followee.entry.add_non_member_follower(follower)
                                have_followee.add(follower.get_unique_id())
                            else:
                                non_same_class_followers.append(follower)
                                message = f'「{follower.questionnaireInfo.fullName}」想要跟「{followee.entry.fullName
                                }」同組, 但「{follower.questionnaireInfo.fullName}」上「{follower.questionnaireInfo.registerClass
                                }」但「{followee.entry.fullName}」上「{followee.entry.registerClass}」'
                                logger.warning(message)
                                errors.append(GeneralProcessingError.warning(message))

                # if len(non_same_class_followers) > 0:
                #     for follower in non_same_class_followers:
                #         message = f'{follower.questionnaireInfo.fullName} 與 {non_member_classmate} 同組, 但 {non_member_classmate
                #         } 不是學員, 且在禪修意願表沒有選修 {follower.questionnaireInfo.registerClass}。'
                #         errors.append(SeniorReportError.warning(message))
                #         logger.warning(message)

            for non_member_classmate, followers in self.non_member_classmates.items():
                for follower in followers:
                    if follower.get_unique_id() not in have_followee:
                        message = f'「{follower.questionnaireInfo.fullName}」與「{non_member_classmate
                        }」同組, 但在禪修意願表中, 沒有找到選修「{follower.questionnaireInfo.registerClass
                        }」且性別為「{follower.questionnaireInfo.gender}性」而姓名為「{non_member_classmate}」的人。'
                        errors.append(GeneralProcessingError.warning(message))
                        logger.warning(message)

        if ClassmateRequestService.count() > 0:
            for r in ClassmateRequestService.all_requests():
                message = f'「{r.follower.questionnaireInfo.fullName}」想與「{r.followee.entry.fullName}」同組, 但因程式尚不支援, 請記得手動檢查並調整。'
                errors.append(GeneralProcessingError.warning(message))

        return errors

    def pre_processing_assignment(self, with_table_b: bool = False) -> list[GeneralProcessingError]:
        errors: list[GeneralProcessingError] = []

        if with_table_b:
            questionnaires_entries = []

            for questionnaires_entry in self.all_questionnaires_entries:
                if questionnaires_entry.entry.registerClass != '兒童':
                    group_id = self.new_senior_service.already_assigned_group(questionnaires_entry.entry.registerClass,
                                                                              questionnaires_entry.member)
                    if group_id == -1:
                        questionnaires_entries.append(questionnaires_entry)
                        logger.info(
                            f'{questionnaires_entry.entry.fullName} not assigned')
                    else:
                        logger.debug(
                            f'{questionnaires_entry.entry.fullName} already assigned to {questionnaires_entry.entry.registerClass}{group_id}')
        else:
            questionnaires_entries = self.all_questionnaires_entries

        for questionnaire_entry in questionnaires_entries:
            entry = questionnaire_entry.entry
            introducer = questionnaire_entry.introducer
            mix_member = questionnaire_entry.member

            # self.find_relation_in_remark(questionnaire_entry)

            if entry.followee is not None:
                followee: QuestionnaireEntry = entry.followee
                logger.error(f'{entry.fullName} / {followee.entry.fullName}')
                self.new_senior_service.follow_non_member(followee.member, entry.registerClass, mix_member)
                questionnaire_entry.dispatching_status = DispatchingStatus.FOLLOW
            elif introducer is not None:
                if introducer.gender == entry.gender and introducer.student_id != mix_member.get_unique_id():
                    jobs = self.new_senior_service.get_senior_by_student_id(introducer.student_id)
                    for job in jobs:
                        if job.className == entry.registerClass and job.gender == entry.gender:
                            if entry.classmate is not None:
                                reason = f'意願調查: {entry.fullName}/{entry.gender} 加入介紹人 {job.fullName} {job.className}/{job.groupId} (與 {entry.classmate} 同組)'
                            else:
                                reason = f'意願調查: {entry.fullName}/{entry.gender} 加入介紹人 {job.fullName} {job.className}/{job.groupId}'
                            logger.debug(reason)
                            self.new_senior_service.add_member_to(
                                job, mix_member, reason, AutoAssignmentStepEnum.INTRODUCER_AS_SENIOR)
                            questionnaire_entry.dispatching_status = DispatchingStatus.ASSIGNED

                    if mix_member.senior is None:  # 還沒有配班級的
                        # logger.warning(f'checking {mix_member.get_full_name()} on {entry.registerClass}')
                        # 檢查介紹人是不是也有報班, 但這裡的介紹人必需是學員
                        if (self.signup_next_service.is_signup(introducer.student_id, entry.registerClass) or
                                self.new_senior_service.have_willingness_by_unique_id(
                                    entry.registerClass, entry.gender, introducer.student_id)):
                            logger.trace(
                                f'(follow {entry.registerClass}) {entry.fullName}/{mix_member.get_unique_id()} 跟介紹人 {introducer.real_name} 同班 {entry.registerClass}')
                            self.new_senior_service.follow(introducer, entry.registerClass, mix_member)
                            # self.signup_next_service.follow(introducer.student_id, entry.registerClass,
                            #                                 mix_member)
                            questionnaire_entry.dispatching_status = DispatchingStatus.FOLLOW
                        else:
                            logger.warning(
                                f'[+] {entry.fullName} 介紹人 {introducer.real_name} 班級 {entry.registerClass}')
                    else:
                        logger.debug(
                            f'{entry.fullName}/{mix_member.get_unique_id()} 已經有學長 {mix_member.senior.fullName} at {entry.registerClass}')
            elif entry.classmate is not None and entry.followee is not None:
                logger.error(f'「{entry.fullName}」 想要跟 「{entry.classmate}」 同班 ({entry.registerClass})')
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
