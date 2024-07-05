import glob
from typing import Any

from loguru import logger

from pz.config import PzProjectConfig
from pz.models.mix_member import MixMember
from pz.models.mysql_class_member_entity import MysqlClassMemberEntity
from pz.models.mysql_member_detail_entity import MysqlMemberDetailEntity
from pz.models.new_class_senior import NewClassSeniorModel
from pz.models.pz_questionnaire_info import PzQuestionnaireInfo
from pz.models.senior_contact_advanced import SeniorContactAdvanced
from pz.models.senior_contact_fundamental import SeniorContactFundamental
from pz.utils import full_name_to_names
from services.excel_template_service import ExcelTemplateService
from services.excel_workbook_service import ExcelWorkbookService
from services.grand_member_service import PzGrandMemberService
from services.new_class_senior_service import NewClassSeniorService
from services.prev_senior_service import PreviousSeniorService
from services.signup_next_info_service import SignupNextInfoService


def add_page_break(datum, prev_datum) -> tuple[Any, bool]:
    if prev_datum is not None:
        if prev_datum['組別'] != datum['組別']:
            # print("send page break")
            return datum, True
    return datum, False


class SeniorReportGenerator:
    config: PzProjectConfig
    member_service: PzGrandMemberService
    new_senior_service: NewClassSeniorService
    signup_next_service: SignupNextInfoService
    prev_senior_service: PreviousSeniorService

    # prev_class_senior_map: dict[str, NewClassSeniorModel]  # 舊的班級學長到哪了

    def __init__(self, config: PzProjectConfig):
        self.config = config

        self.member_service = PzGrandMemberService(config, from_access=False, from_google=False)
        self.new_senior_service = NewClassSeniorService(config, self.member_service)
        self.prev_senior_service = PreviousSeniorService(self.member_service, self.new_senior_service)
        self.signup_next_service = SignupNextInfoService(config, self.member_service, self.prev_senior_service,
                                                         self.new_senior_service)

        if config.debug_text_file_output is not None:
            self.fp = open(config.debug_text_file_output, "w", encoding="utf-8")

        # prev_seniors = self.member_service.read_all_seniors()
        # self.prev_class_senior_map = {}

        # # 先前的學長是否還繼續當學長
        # for senior in prev_seniors:
        #     model = self.new_senior_service.get_senior_by_student_id(senior.student_id)
        #     if model is not None:
        #         self.prev_class_senior_map[self.class_group_as_key(senior.class_name, senior.class_group)] = model
        #         # print(f'{senior.student_id} {senior.real_name} serve as new senior at {model.className} {model.groupId} (from {senior.class_name} {senior.class_group})')

    # @staticmethod
    # def class_group_as_key(class_name: str, group_id: int) -> str:
    #     return f'{class_name}-{group_id}'

    def __del__(self):
        if self.fp is not None:
            self.fp.close()

    @staticmethod
    def class_gender_as_key(class_name: str, gender: str) -> str:
        return f'{class_name}-{gender}'

    def auto_assignment(self, spreadsheet_file: str):
        class_members: dict[str, list[MixMember]] = {}

        self.assign_having_senior_signup_next(class_members)
        self.assign_having_senior_questionnaire(spreadsheet_file, class_members)

        for class_gender in class_members:
            # print(f'class: {class_gender}, member: {len(class_members[class_gender])}')
            for member in class_members[class_gender]:
                self.new_senior_service.min_member_first_assign(class_gender, member)

    def assign_having_senior_signup_next(self, class_members: dict[str, list[MixMember]]):
        unassigned_signups = self.signup_next_service.processing_signups()

        for signup in unassigned_signups:
            for entry in signup.signupNextInfo.signups:
                if signup.classMember is not None:
                    key = self.class_gender_as_key(entry, signup.classMember.gender)
                    if key in class_members:
                        class_members[key].append(signup)
                    else:
                        class_members[key] = [signup]

    def assign_having_senior_questionnaire(self, spreadsheet_file: str, class_members: dict[str, list[MixMember]]):
        service = ExcelWorkbookService(PzQuestionnaireInfo({}), spreadsheet_file,
                                       self.config.excel.questionnaire.sheet_name,
                                       header_at=self.config.excel.questionnaire.header_row,
                                       debug=False)
        entries: list[PzQuestionnaireInfo] = service.read_all(required_attribute='fullName')

        for entry in entries:
            if entry.registerClass is not None and entry.registerClass != '':  # 所有有意願調查有指定班級的
                class_name = entry.registerClass.replace('班', '')
                entry.registerClass = class_name

                name_tuple = full_name_to_names(entry.fullName)
                matched_members = self.member_service.find_grand_member_by_pz_name(name_tuple[0])
                mix_member = None

                for m in matched_members:
                    if m[0].birthday == entry.birthday and m[0].gender == entry.gender:
                        mix_member = MixMember(m[0], m[1], entry, None)
                        if m[1] is not None:
                            prev_senior = m[1].senior
                            senior_jobs = self.prev_senior_service.find_previous_senior(m[1].class_name,
                                                                                        m[1].class_group)

                            if len(senior_jobs) > 0:
                                for job in senior_jobs:
                                    if job.fullName != prev_senior:
                                        logger.warning(f'Warning: 學長姓名 from {prev_senior} to {job.fullName}')
                                    else:
                                        if job.className == entry.registerClass:
                                            logger.info(
                                                f'{entry.fullName} {entry.registerClass} 加入前學長 {job.fullName} {job.className} 班級')
                                            self.new_senior_service.add_member_to(job, mix_member)
                                        # else:
                                        #     print(
                                        #         f'{entry.fullName} {entry.registerClass} : 前學長 {job.fullName} at {job.className}')
                            else:
                                logger.info(f'之前的學長 {m[1].senior} 沒有帶新班級')

                if mix_member is None:
                    mix_member = MixMember(None, None, entry, None)

                if mix_member.senior is None:  # 需要自動排的
                    key = self.class_gender_as_key(class_name, entry.gender)

                    if key in class_members:
                        class_members[key].append(mix_member)
                    else:
                        class_members[key] = [mix_member]

        # for class_gender in class_members:
        #     # print(f'class: {class_gender}, member: {len(class_members[class_gender])}')
        #     for member in class_members[class_gender]:
        #         self.new_senior_service.min_member_first_assign(class_gender, member)

        # self.new_senior_service.find_by_class_gender(class_gender)

    @staticmethod
    def _take_introducer_info_from(m: tuple[MysqlMemberDetailEntity, MysqlClassMemberEntity]) -> tuple[str, str]:
        introducer_class = ''
        introducer_phone = ''
        if m[1] is not None:
            introducer_class = f'{m[1].class_name}/{m[1].class_group}'
        if m[0] is not None:
            introducer_phones = []
            if m[0].mobile_phone is not None and m[0].mobile_phone != '':
                introducer_phones.append(m[0].mobile_phone)
            if m[0].home_phone is not None and m[0].home_phone != '':
                introducer_phones.append(m[0].home_phone)
            introducer_phone = '\n'.join(introducer_phones)
        return introducer_class, introducer_phone

    def _print_data_as_text(self, senior: NewClassSeniorModel, member: MixMember, sn: int, gt: int):
        if self.fp is not None:
            self.fp.write(
                f"{gt:{3}} {sn:{2}} {senior.className} {senior.groupId} {senior.gender} {senior.fullName} - {member.get_full_name()} {member.get_student_id()}\r\n")

    def _take_introducer_info(self, introducer_name: str) -> tuple[str, str]:
        if introducer_name is None or introducer_name == '':
            return '', ''

        m_list = self.member_service.find_grand_member_by_pz_name(introducer_name)

        if len(m_list) == 1:
            return self._take_introducer_info_from(m_list[0])
        elif len(m_list) > 1:
            for m in m_list:
                if m[0] is not None and m[1] is not None:
                    return self._take_introducer_info_from(m)
            for m in m_list:
                if m[0] is not None:
                    return self._take_introducer_info_from(m)

        return '', ''

    def _generate_fundamental_report(self, class_name: str, spreadsheet_file: str):
        seniors = self.new_senior_service.all_classes[class_name]
        # print(f'class: {class_name} {len(seniors)}')

        data = []

        grand_total = 0
        for senior in seniors:
            # print(f'[{__name__}] senior: {senior.className} {senior.groupId} - {senior.fullName} ({senior.gender})')

            members = senior.members
            group_sn = 0
            for member in members:
                if isinstance(member, MixMember):
                    group_sn += 1
                    grand_total += 1

                    (introducer_class, introducer_phone) = self._take_introducer_info(
                        member.questionnaireInfo.introducerName) if member.questionnaireInfo is not None else ('', '')

                    datum: dict[str, str | int] = {
                        '組序': group_sn,
                        '姓名': member.get_full_name(),
                        '班別': senior.className,
                        '學長': senior.fullName,
                        '組別': senior.groupId,
                        '法名': member.get_dharma_name(),
                        '學員電話行動&市話': member.get_phone(),
                        '介紹人': member.get_introducer_name(),
                        '介紹人班別/組別': introducer_class,
                        '介紹人電話行動&市話': introducer_phone,
                        '報名時備註': member.get_remark(),
                        '茶會': member.get_tee(),
                        '喫茶趣': member.get_cha_for_tea(),
                    }
                    data.append(datum)

                    self._print_data_as_text(senior, member, group_sn, grand_total)

        template = ExcelTemplateService(SeniorContactFundamental({}),
                                        self.config.excel.templates['fundamental_contact'],
                                        spreadsheet_file, self.config.output_folder,
                                        f'[初級班電聯表][{class_name}]',
                                        debug=False)
        supplier = (lambda y=x: x for x in data)
        template.write_data(supplier, callback=lambda x, y, z: add_page_break(x, y))

    def _generate_advanced_report(self, class_name: str, spreadsheet_file: str):
        seniors = self.new_senior_service.all_classes[class_name]
        # print(f'class: {class_name} {len(seniors)}')

        data = []
        grand_total = 0

        for senior in seniors:
            # print(f'senior: {senior.className} {senior.groupId} - {senior.fullName} ({senior.gender})')

            members = senior.members
            group_sn = 0
            for member in members:
                if isinstance(member, MixMember):
                    group_sn += 1
                    grand_total += 1

                    datum: dict[str, str | int] = {
                        '組序': group_sn,
                        '姓名': member.get_full_name(),
                        '班別': senior.className,
                        '學長': senior.fullName,
                        '組別': senior.groupId,
                        '法名': member.get_dharma_name(),
                        '學員電話行動&市話': member.get_phone(),
                        '上期班別/學長': member.get_last_record(),
                        '喫茶趣': member.get_cha_for_tea(),
                    }
                    data.append(datum)

                    self._print_data_as_text(senior, member, group_sn, grand_total)

        template = ExcelTemplateService(SeniorContactAdvanced({}),
                                        self.config.excel.templates['advanced_contact'],
                                        spreadsheet_file, self.config.output_folder,
                                        f'[學長電聯表][{class_name}]',
                                        debug=False)
        sheet = template.get_sheet()

        title = sheet.cell(1, 1).value
        if title is not None and isinstance(title, str):
            sheet.cell(1, 1).value = title.replace('{class_name}', class_name)
        supplier = (lambda y=x: x for x in data)
        # template.write_data(supplier)
        template.write_data(supplier, callback=lambda x, y, z: add_page_break(x, y))

    def reading_report(self, spreadsheet_file: str):
        self.auto_assignment(spreadsheet_file)

        for class_name in self.new_senior_service.all_classes:
            if class_name in ('日初', '夜初'):
                self._generate_fundamental_report(class_name, spreadsheet_file)
            else:
                self._generate_advanced_report(class_name, spreadsheet_file)


def generate_senior_reports(cfg: PzProjectConfig):
    generator = SeniorReportGenerator(cfg)

    if cfg.excel.questionnaire.spreadsheet_folder is not None and cfg.excel.questionnaire.spreadsheet_folder != '':
        files = glob.glob(f'{cfg.excel.questionnaire.spreadsheet_folder}/*.xlsx')

        for filename in files:
            generator.reading_report(filename)
    else:
        generator.reading_report(cfg.excel.questionnaire.spreadsheet_file)
