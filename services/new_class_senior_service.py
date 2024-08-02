from loguru import logger

from debugging.check import debug_on_student_id
from pz.config import PzProjectConfig
from pz.models.auto_assignment_step import AutoAssignmentStepEnum
from pz.models.class_and_gender import ClassAndGender
from pz.models.mix_member import MixMember
from pz.models.mysql_class_member_entity import MysqlClassMemberEntity
from pz.models.new_class_lineup import NewClassLineup
from pz.models.new_class_senior import NewClassSeniorModel
from pz.models.senior_report_error_model import SeniorReportError
from pz.models.signup_next_info import SignupNextInfoModel
from services.excel_workbook_service import ExcelWorkbookService
from services.grand_member_service import PzGrandMemberService


class NewClassSeniorService:
    config: PzProjectConfig
    senior_by_class_gender: dict[str, ClassAndGender]
    senior_by_class_group: dict[str, NewClassSeniorModel]
    senior_by_student_id: dict[int, list[NewClassSeniorModel]]
    all_classes: dict[str, list[NewClassSeniorModel]]
    member_service: PzGrandMemberService
    initial_errors: list[SeniorReportError]

    def __init__(self, cfg: PzProjectConfig, member_service: PzGrandMemberService):
        self.config = cfg

        new_class_seniors = self._read_all()
        self.senior_by_class_gender = {}
        self.senior_by_class_group = {}
        self.senior_by_student_id = {}
        self.all_classes = {}
        self.member_service = member_service

        logger.info(f'新班學長: {len(new_class_seniors)} 筆資料')
        self.initial_errors = self._init_new_classes_by_senior(new_class_seniors)
        err = self._add_new_default_member(new_class_seniors)
        self.initial_errors.extend(err)

    def _init_new_classes_by_senior(self, new_class_seniors: list[NewClassSeniorModel]) -> list[SeniorReportError]:
        errors: list[SeniorReportError] = []
        group_id_assignment: dict[str, int] = {}

        for senior in new_class_seniors:
            if senior.senior != '學長' or senior.fullName is None or senior.fullName == '':
                continue

            if senior.className in self.all_classes:
                self.all_classes[senior.className].append(senior)
            else:
                self.all_classes[senior.className] = [senior]

            senior_infos = self.member_service.find_grand_member_by_pz_name_and_dharma_name(senior.fullName,
                                                                                            senior.dharmaName,
                                                                                            senior.gender)
            if senior_infos is None or senior_infos[0] is None:
                message = f'糟糕: 學長 {senior.fullName} / {senior.deacon} 在後端資料庫中找不到'
                logger.warning(message)
                errors.append(SeniorReportError.warning(message))
                continue

            senior.studentId = int(senior_infos[0].student_id)
            if senior.studentId in self.senior_by_student_id:
                self.senior_by_student_id[senior.studentId].append(senior)
            else:
                self.senior_by_student_id[senior.studentId] = [senior]

            if senior.groupId is None:
                if senior.className in group_id_assignment:
                    senior.groupId = group_id_assignment[senior.className] + 1
                else:
                    senior.groupId = 101
                    message = f'班級 {senior.className} / {senior.gender} / {senior.fullName} 沒有組別'
                    logger.warning(message)
                    errors.append(SeniorReportError.warning(message))
                group_id_assignment[senior.className] = senior.groupId
            else:
                key = self.key_of_senior_by_group_id(senior.className, senior.groupId)
                if key in self.senior_by_class_group:
                    message = f'班級 {senior.className}, 組別 {senior.groupId} 重覆'
                    logger.warning(message)
                    errors.append(SeniorReportError.warning(message))
                else:
                    self.senior_by_class_group[key] = senior

            key = self.key_of_senior(senior.className, senior.gender)

            if key not in self.senior_by_class_gender:
                self.senior_by_class_gender[key] = ClassAndGender(senior.className, senior.gender)

            self.senior_by_class_gender[key].add_group(senior.groupId, senior)

        for clazz in self.all_classes:
            self.all_classes[clazz].sort(key=lambda x: x.groupId)
        return errors

    def _add_new_default_member(self, new_class_seniors: list[NewClassSeniorModel]) -> list[SeniorReportError]:
        errors: list[SeniorReportError] = []
        logger.debug(f'Assignment Step {AutoAssignmentStepEnum.PREDEFINED_SENIOR}')
        for entry in new_class_seniors:
            member_tuple = self.member_service.find_grand_member_by_pz_name_and_dharma_name(
                entry.fullName, entry.dharmaName, entry.gender)

            if member_tuple is None:
                message = f'學長 姓名：{entry.fullName}，法名：{entry.dharmaName if entry is not None else ''}，姓別：{entry.gender} 在資料庫中找不到'
                logger.warning(message)
                errors.append(SeniorReportError.warning(message))
                continue

            signup_next = SignupNextInfoModel({})

            if member_tuple[1] is not None:
                signup_next.studentId = member_tuple[1].student_id
                signup_next.className = member_tuple[1].class_name
                signup_next.groupId = member_tuple[1].class_group
                signup_next.senior = member_tuple[1].senior
            elif member_tuple[0] is not None:
                signup_next.studentId = int(member_tuple[0].student_id)
                signup_next.className = ''
                signup_next.senior = ''

            signup_next.gender = entry.gender
            signup_next.fullName = entry.fullName
            signup_next.dharmaName = entry.dharmaName
            signup_next.signup1 = entry.className

            mix_member = MixMember(member_tuple[0], member_tuple[1], None, signup_next)

            key = self.key_of_senior_by_group_id(entry.className, entry.groupId)
            if key in self.senior_by_class_group:
                logger.trace(
                    f'學長 {mix_member.get_full_name()} 預先排進班級 {entry.className} / {entry.groupId} / {entry.gender}')
                self.add_member_to(self.senior_by_class_group[key], mix_member, '學長預排',
                                   AutoAssignmentStepEnum.PREDEFINED_SENIOR, deacon=entry.deacon)
            else:
                logger.warning(f'Warning: {entry.className} / {entry.groupId} not found')
        return errors

    def get_initial_errors(self):
        return self.initial_errors

    @staticmethod
    def key_of_senior(class_name: str, gender: str):
        return f'{class_name}-{gender}'

    @staticmethod
    def key_of_senior_by_group_id(class_name: str, group_id: int):
        return f'{class_name}-{group_id}'

    def _read_all(self) -> list[NewClassSeniorModel]:
        workbook = ExcelWorkbookService(NewClassSeniorModel({}), self.config.excel.new_class_senior.spreadsheet_file,
                                        header_at=self.config.excel.new_class_senior.header_row,
                                        sheet_name=self.config.excel.new_class_senior.sheet_name,
                                        debug=False)

        entries: list[NewClassSeniorModel] = workbook.read_all(required_attribute='fullName')
        return entries

    def add_member(self, mix_member: MixMember):
        key = self.key_of_senior(mix_member.questionnaireInfo.registerClass, mix_member.questionnaireInfo.gender)
        if key not in self.senior_by_class_gender:
            logger.warning(
                f'Warning: {mix_member.questionnaireInfo.registerClass} {mix_member.questionnaireInfo.gender} did not have a senior')
        else:
            classes = self.senior_by_class_gender[key]
            if mix_member.classMember is not None:
                pass
        pass

    def get_senior_by_student_id(self, student_id: int) -> list[NewClassSeniorModel]:
        if student_id in self.senior_by_student_id:
            return self.senior_by_student_id[student_id]
        return []

    def add_member_to(self, senior: NewClassSeniorModel, mix_member: MixMember, reason: str,
                      step: AutoAssignmentStepEnum, deacon: str = None, non_follower_only: bool = False):
        key = self.key_of_senior(senior.className, senior.gender)
        debug = debug_on_student_id(mix_member.get_student_id())
        if key in self.senior_by_class_gender:
            self.add_willingness(senior.className, mix_member)
            if debug:
                logger.error(f'add_member {mix_member.get_full_name()} to {senior.fullName}')
            self.senior_by_class_gender[key].add_member_to(senior, mix_member, reason, step, deacon=deacon,
                                                           non_follower_only=non_follower_only)
        else:
            logger.error(f'錯誤!! {senior.className} {senior.gender} 班級不存在')

        # mix_member.senior = senior
        # for m in senior.members:
        #     if isinstance(m, MixMember):
        #         if m.get_student_id() is not None and mix_member.get_student_id() is not None:
        #             if m.get_student_id() == mix_member.get_student_id():
        #                 logger.warning(
        #                     f'ignore duplicate {m.get_student_id()} {m.get_full_name()} on {senior.className}')
        #                 return
        # senior.members.append(mix_member)
        # logger.trace(
        #     f'adding {mix_member.get_full_name()}/{senior.fullName} at {senior.className}/{senior.groupId}/{senior.gender}')

    # def find_by_class_gender(self, class_gender_key: str):
    #     if class_gender_key in self.senior_by_class_gender:
    #         logger.info(f'{class_gender_key}: {entry.fullName}, current-member: {len(entry.members)}')
    #     else:
    #         logger.warning(f'{class_gender_key}: not found')

    # def min_member_first_assign(self, class_gender_key: str, member: MixMember):
    #     if class_gender_key in self.senior_by_class_gender:
    #         # senior_list = [x for x in self.senior_by_class_gender[class_gender_key]]
    #         #
    #         # senior_list.sort()
    #         # senior_list = sorted(self.senior_by_class_gender[class_gender_key], key=new_class_senior_comparator)
    #         #
    #         # self.add_member_to(senior_list[0], member)
    #         self.senior_by_class_gender[class_gender_key].min_member_first_assign(member)
    #     else:
    #         logger.warning(f'糟糕! {class_gender_key} 找不到')

    def add_to_pending_assignment(self, signup_class: str, mix_member: MixMember):
        class_gender_key = self.key_of_senior(signup_class, mix_member.get_gender())

        if class_gender_key in self.senior_by_class_gender:
            self.senior_by_class_gender[class_gender_key].add_to_pending([mix_member])
        elif signup_class != '兒童':
            logger.warning(f'糟糕! {class_gender_key} 找不到')

    def add_to_pending_in_group(self, signup_class: str, pending_list: list[MixMember]):
        if len(pending_list) > 0:
            class_gender_key = self.key_of_senior(signup_class, pending_list[0].get_gender())

            if class_gender_key in self.senior_by_class_gender:
                self.senior_by_class_gender[class_gender_key].add_to_pending(pending_list)
            else:
                logger.warning(f'糟糕! {class_gender_key} 找不到')

    def perform_auto_assignment(self):  # 對所有的班級分配組別
        # for class_and_gender in self.senior_by_class_gender.values():
        #     class_and_gender.processing_followers()
        #     class_and_gender.perform_follower_loop_assignment()

        for class_and_gender in self.senior_by_class_gender.values():
            if not class_and_gender.perform_auto_assignment():
                logger.error(f'演算法無去處理 {class_and_gender.name} / {class_and_gender.gender}')

    def perform_table_b_auto_assignment(self):  # 對所有的班級分配組別
        for class_and_gender in self.senior_by_class_gender.values():
            class_and_gender.perform_table_b_auto_assignment()

    def add_willingness(self, class_name: str, mix_member: MixMember):
        class_and_gender = self.key_of_senior(class_name, mix_member.get_gender())

        if class_and_gender in self.senior_by_class_gender:
            self.senior_by_class_gender[class_and_gender].add_willingness(mix_member)

    def have_willingness(self, class_name: str, mix_member: MixMember) -> bool:
        class_and_gender = self.key_of_senior(class_name, mix_member.get_gender())
        if class_and_gender in self.senior_by_class_gender:
            logger.warning(f'checking {mix_member.get_full_name()} on {class_name}')
            return self.senior_by_class_gender[class_and_gender].have_willingness(mix_member.get_unique_id())
        return False

    def have_willingness_by_unique_id(self, class_name: str, gender: str, unique_id: int) -> bool:
        class_and_gender = self.key_of_senior(class_name, gender)
        if class_and_gender in self.senior_by_class_gender:
            return self.senior_by_class_gender[class_and_gender].have_willingness(unique_id)
        return False

    def follow(self, introducer: MysqlClassMemberEntity, class_name: str, mix_member: MixMember):
        class_and_gender = self.key_of_senior(class_name, mix_member.get_gender())

        if class_and_gender in self.senior_by_class_gender:
            senior = self.senior_by_class_gender[class_and_gender]
            senior.add_willingness(mix_member)
            senior.follow(introducer, mix_member)

        #
        #
        # if student_id in self.signup_next_by_student_id:
        #     if class_name in self.signup_next_by_student_id[student_id]:
        #         member = self.signup_next_by_student_id[student_id][class_name]
        #         logger.error(
        #             f'{mix_member.get_full_name()} follow {student_id} ({member.get_full_name()}) at {class_name}')
        #     else:
        #         logger.error(f'{mix_member.get_full_name()} follow {student_id} at {class_name} but not found')

    def perform_follower_loop_first(self):
        # for class_and_gender in self.senior_by_class_gender.keys():
        #     self.senior_by_class_gender[class_and_gender].perform_follower_loop_assignment()
        for class_and_gender in self.senior_by_class_gender.values():
            class_and_gender.processing_followers()
            class_and_gender.perform_follower_loop_assignment()

    def adding_unregistered_follower_chain(self):
        for class_and_gender in self.senior_by_class_gender.values():
            class_and_gender.processing_unregistered_follower_chain()

    def add_table_b_member(self, class_name: str, gender: str, group_id: int | None, entry: NewClassLineup):
        key = self.key_of_senior(class_name, gender)

        if key not in self.senior_by_class_gender:
            error_message = f'找不到 {class_name}/{gender} 的資料'
            logger.error(error_message)
            raise RuntimeError(error_message)
        else:
            self.senior_by_class_gender[key].add_table_b_assignment(group_id, entry)
