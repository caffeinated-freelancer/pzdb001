import glob
import os
import re
from typing import Any

from loguru import logger

from pz.config import PzProjectConfig
from pz.models.mix_member import MixMember
from pz.models.mysql_class_member_entity import MysqlClassMemberEntity
from pz.models.mysql_member_detail_entity import MysqlMemberDetailEntity
from pz.models.new_class_lineup import NewClassLineup
from pz.models.new_class_senior import NewClassSeniorModel
from pz.models.senior_contact_advanced import SeniorContactAdvanced
from pz.models.senior_contact_fundamental import SeniorContactFundamental
from pz.pz_commons import ACCEPTABLE_CLASS_NAMES, phone_number_normalize
from services.excel_template_service import ExcelTemplateService
from services.excel_workbook_service import ExcelWorkbookService
from services.grand_member_service import PzGrandMemberService
from services.new_class_senior_service import NewClassSeniorService
from services.prev_senior_service import PreviousSeniorService
from services.questionnaire_service import QuestionnaireService
from services.signup_next_info_service import SignupNextInfoService, SignupMemberEntry


def add_page_break(datum, prev_datum) -> tuple[Any, bool]:
    if prev_datum is not None:
        if prev_datum['組別'] != datum['組別']:
            # print("send page break")
            return datum, True
    return datum, False


class SeniorReportGenerator:
    config: PzProjectConfig
    from_scratch: bool
    member_service: PzGrandMemberService
    new_senior_service: NewClassSeniorService
    signup_next_service: SignupNextInfoService
    prev_senior_service: PreviousSeniorService
    questionnaire_service: QuestionnaireService

    # prev_class_senior_map: dict[str, NewClassSeniorModel]  # 舊的班級學長到哪了

    def __init__(self, config: PzProjectConfig, from_scratch: bool):
        self.config = config
        self.from_scratch = from_scratch

        self.member_service = PzGrandMemberService(config, from_access=False, from_google=False)
        self.new_senior_service = NewClassSeniorService(config, self.member_service)
        self.prev_senior_service = PreviousSeniorService(self.member_service, self.new_senior_service)
        self.signup_next_service = SignupNextInfoService(config, self.member_service, self.prev_senior_service,
                                                         self.new_senior_service)
        self.questionnaire_service = QuestionnaireService(config, self.member_service, self.prev_senior_service,
                                                          self.new_senior_service, self.signup_next_service)

        self.fp = None

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

    def _auto_assignment(self, spreadsheet_file: str, from_excel: bool = False):
        # 預先處理, 記載每個學員的升班意願
        self.signup_next_service.pre_processing(from_excel=from_excel)

        self.signup_next_service.fix_senior_willingness()

        # 預先處理禪修班意願調查表, 包括讀取及連結介紹人的部份
        self.questionnaire_service.pre_processing(spreadsheet_file, from_scratch=True)

        self.new_senior_service.perform_follower_loop_first()

        # 處理所有升班調查的部份
        self.signup_next_service.processing_signups()

        # 處理所有意願調查的部份
        self.questionnaire_service.assign_having_senior_questionnaire()
        # self.assign_having_senior_questionnaire(spreadsheet_file)

        self.signup_next_service.add_to_pending_groups()

        self.new_senior_service.adding_unregistered_follower_chain()

        # 對所有的班級分配組別
        self.new_senior_service.perform_auto_assignment()

    # def pre_processing_questionnaire(self, spreadsheet_file: str):
    #     pass

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

            group_sn = 0
            for assigned_member in senior.members:
                member = assigned_member.member
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

            group_sn = 0
            for assigned_member in senior.members:
                member = assigned_member.member
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

    def _perform_final_report_processing(self, spreadsheet_file: str):
        self.signup_next_service.pre_processing(from_excel=False, for_table_b=True)
        self.questionnaire_service.pre_processing(spreadsheet_file, from_scratch=False)
        self._read_predefined_information()
        self.new_senior_service.perform_table_b_auto_assignment()

    def processing_senior_report(self, spreadsheet_file: str, from_excel: bool = False, from_scratch: bool = True):
        if from_scratch:
            self._auto_assignment(spreadsheet_file, from_excel=from_excel)
        else:
            self._perform_final_report_processing(spreadsheet_file)

        for class_name in self.new_senior_service.all_classes:
            if class_name in ('日初', '夜初'):
                self._generate_fundamental_report(class_name, spreadsheet_file)
            else:
                self._generate_advanced_report(class_name, spreadsheet_file)

    def _read_predefined_information(self):
        if self.from_scratch:
            return

        spreadsheet = self.config.excel.new_class_predefined_info

        service = ExcelWorkbookService(NewClassLineup({}), spreadsheet.spreadsheet_file,
                                       sheet_name=spreadsheet.sheet_name,
                                       header_at=spreadsheet.header_row)
        entries: list[NewClassLineup] = service.read_all(required_attribute='realName')
        counter = 0
        newbies: list[NewClassLineup] = []
        for entry in entries:
            entry.phoneNumber = phone_number_normalize(entry.phoneNumber)

            if entry.className is None or entry.realName is None:
                logger.error(f'資料有問題 {entry}')
                continue
            elif entry.className not in ACCEPTABLE_CLASS_NAMES:
                logger.error(f'{entry.realName}: [{entry.className}] 需有班級名稱或名稱錯誤')
                continue

            latest_class = latest_senior = None
            mix_member: MixMember | None = None
            signup_entry: SignupMemberEntry | None = None

            if entry.lastSenior is not None and re.match(r'.*/.*', entry.lastSenior):
                latest_class, latest_senior = entry.lastSenior.split('/', 2)

            if entry.studentId is not None:
                signup_entry = self.signup_next_service.find_by_student_id_for_table_b(entry.studentId)

                if signup_entry is None:
                    member_tuple = self.member_service.find_grand_member_by_student_id(entry.studentId,
                                                                                       prefer=latest_class)
                    if member_tuple is None:
                        logger.error(f'學員編號 {entry.studentId} 查不到資料')
                        continue
                    mix_member = MixMember(member_tuple[0], member_tuple[1], None, None)
                else:
                    mix_member = signup_entry.member
            else:
                member_tuple = self.member_service.find_grand_member_by_pz_name_and_dharma_name(
                    entry.realName, entry.dharmaName, entry.gender)

                if member_tuple is None:
                    if entry.gender not in ('男', '女'):
                        logger.error(
                            f'姓名: {entry.realName}, 法名: {entry.dharmaName}, 沒有學號或非學員時, 性別資料是必要')
                        continue
                    if entry.phoneNumber is None or entry.phoneNumber == '':
                        logger.warning(
                            f'姓名: {entry.realName}, 法名: {entry.dharmaName}, 性別: {entry.gender} 在資料中找不到, 但同時缺少行動電話資料')
                else:
                    if member_tuple[1] is not None:
                        signup_entry = self.signup_next_service.find_by_student_id_for_table_b(
                            member_tuple[1].student_id)
                    elif member_tuple[0] is not None:
                        signup_entry = self.signup_next_service.find_by_student_id_for_table_b(
                            int(member_tuple[0].student_id))

                    if signup_entry is not None:
                        mix_member = signup_entry.member
                    else:
                        mix_member = MixMember(member_tuple[0], member_tuple[1], None, None)

            if mix_member is None or entry.studentId is None or entry.phoneNumber is not None or entry.lastSenior is None:  # 意願調查
                questionnaire = self.questionnaire_service.get_questionnaire(entry.realName, entry.phoneNumber,
                                                                             entry.gender)
                if questionnaire is None:
                    logger.warning(
                        f'姓名: {entry.realName}, 電話: {entry.phoneNumber} 並沒有在禪修班意願調查表中, B 表中的新成員請先登錄在禪修班意願調查中')
                    if mix_member is None:
                        mix_member = MixMember(None, None, None, None, new_class_line_up=entry)
                else:
                    if mix_member is None:
                        mix_member = questionnaire.member
                    else:
                        mix_member.questionnaireInfo = questionnaire.entry
                    entry.questionnaireEntry = questionnaire

                newbies.append(entry)
                counter += 1

            if mix_member is None:
                logger.error(f'程式內部錯誤, 無法對 {entry.realName} 產生學員資料結構')
                continue
            elif mix_member.get_full_name() == '':
                logger.error(f'程式內部錯誤, 無法對 {entry.realName} 產生有效的學員資料結構')
                continue

            entry.mixMember = mix_member

            self.new_senior_service.add_table_b_member(entry.className, entry.gender, entry.groupId, entry)

        logger.info(f'{counter} 位來自意願調查')

        # newbies = sorted(newbies, key=lambda x: x.realName)
        # for newbie in newbies:
        #     print(f'{newbie.realName} {newbie.className} {newbie.phoneNumber} {newbie.studentId} {newbie.lastSenior}')

    def generate_new_class_lineup(self, filename: str):
        template_key = 'new_class_lineup'

        if template_key not in self.config.excel.templates:
            logger.error(f'輸出樣版未設定 {template_key}')
        else:
            template_file = self.config.excel.templates['new_class_lineup']
            data = []
            grand_total = 0

            for class_name in self.new_senior_service.all_classes:
                seniors = self.new_senior_service.all_classes[class_name]

                for senior in seniors:
                    group_sn = 0

                    for assigned_member in senior.members:
                        member = assigned_member.member
                        group_sn += 1
                        grand_total += 1

                        phone = ''
                        if member.questionnaireInfo is not None:
                            phone = member.questionnaireInfo.mobilePhone

                        datum: dict[str, str | int] = {
                            '總序': grand_total,
                            '序': group_sn,
                            '學員編號': member.get_student_id() if member.get_student_id() is not None else '',
                            '班級': senior.className,
                            '學長': senior.fullName,
                            '姓名': member.get_full_name(),
                            '法名': member.get_dharma_name(),
                            '性別': member.get_gender(),
                            '執事': assigned_member.deacon if assigned_member.deacon is not None else '',
                            '組別': senior.groupId,
                            '行動電話': phone,
                            '上期學長': member.get_last_record(),
                            '備註': assigned_member.reason if assigned_member.reason is not None else '',
                            'B 表處理備註': assigned_member.info_b
                        }
                        data.append(datum)

            template = ExcelTemplateService(NewClassLineup({}),
                                            template_file,
                                            filename, self.config.output_folder,
                                            f'[新編班資料]')
            supplier = (lambda y=x: x for x in data)
            template.write_data(supplier)


def generate_senior_reports(cfg: PzProjectConfig, from_scratch: bool, from_excel: bool | None = None):
    if not from_scratch:
        if not os.path.exists(cfg.excel.new_class_predefined_info.spreadsheet_file):
            from_scratch = True

    generator = SeniorReportGenerator(cfg, from_scratch)

    from_excel = False if from_excel is None else from_excel

    if cfg.excel.questionnaire.spreadsheet_folder is not None and cfg.excel.questionnaire.spreadsheet_folder != '':
        files = glob.glob(f'{cfg.excel.questionnaire.spreadsheet_folder}/*.xlsx')

        for filename in files:
            generator.processing_senior_report(filename, from_excel=from_excel, from_scratch=from_scratch)
            generator.generate_new_class_lineup(filename)
    else:
        generator.processing_senior_report(cfg.excel.questionnaire.spreadsheet_file, from_excel=from_excel,
                                           from_scratch=from_scratch)
        generator.generate_new_class_lineup(cfg.excel.questionnaire.spreadsheet_file)
