import glob
import os
import re
from typing import Any

from loguru import logger

from pz.config import PzProjectConfig, PzProjectExcelSpreadsheetConfig
from pz.models.general_processing_error import GeneralProcessingError
from pz.models.mix_member import MixMember
from pz.models.mysql_class_member_entity import MysqlClassMemberEntity
from pz.models.mysql_member_detail_entity import MysqlMemberDetailEntity
from pz.models.new_class_group_statistics import NewClassGroupStatistics
from pz.models.new_class_lineup import NewClassLineup
from pz.models.new_class_senior import NewClassSeniorModel
from pz.models.post_lineup_model import PostLineupModel
from pz.models.questionnaire_entry import QuestionnaireEntry
from pz.models.senior_contact_advanced import SeniorContactAdvanced
from pz.models.senior_contact_fundamental import SeniorContactFundamental
from pz.pz_commons import ACCEPTABLE_CLASS_NAMES, phone_number_normalize
from services.excel_creation_service import ExcelCreationService
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
    initial_errors: list[GeneralProcessingError]

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

        # FIXME
        # member_relation_service = MemberRelationService(config)
        # member_relation_service.load_relations(gender_care=True)

        self.initial_errors = self.new_senior_service.get_initial_errors()

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

    def get_initial_errors(self) -> list[GeneralProcessingError]:
        return self.initial_errors

    @staticmethod
    def class_gender_as_key(class_name: str, gender: str) -> str:
        return f'{class_name}-{gender}'

    def _auto_assignment(self,
                         spreadsheet_file: str, from_excel: bool = False,
                         no_fix_senior: bool = False,
                         with_table_b: bool = False,
                         with_questionnaire: bool = True,
                         with_willingness: bool = True) -> list[GeneralProcessingError]:
        errors: list[GeneralProcessingError] = []

        if with_willingness:
            # 預先處理, 記載每個學員的升班意願
            # 這裡不會把學員排進班級, 只是記載學員們的升班意願供後續查詢使用。
            err = self.signup_next_service.pre_processing(from_excel=from_excel)
            errors.extend(err)

            if not no_fix_senior:
                # 調整學長填寫升班意願的位置
                self.signup_next_service.fix_senior_willingness()

        if with_questionnaire:
            # 預先處理禪修班意願調查表, 包括讀取及連結介紹人的部份
            err, questionnaires_entries = self.questionnaire_service.pre_processing(spreadsheet_file)
            errors.extend(err)

        if with_table_b:
            # 要參考 B 表的話得先把 B 表讀進來, 排好編班
            self._read_predefined_information(with_table_b=True, questionnaires_entries=questionnaires_entries)

        if with_questionnaire:
            # 這部份會有部份滿足編組條件的學員先做分組處理
            # err = self.questionnaire_service.pre_processing(spreadsheet_file, from_scratch=True, with_table_b=with_table_b)
            err = self.questionnaire_service.pre_processing_non_member_classmate()
            errors.extend(err)

            err = self.questionnaire_service.pre_processing_assignment(with_table_b=with_table_b)
            errors.extend(err)

        # 部部份要檢查介紹人關係鏈或誰與誰同組的問題
        self.new_senior_service.perform_follower_loop_first()

        if with_willingness:
            # 處理所有升班調查的部份
            self.signup_next_service.processing_signups()

        if with_questionnaire:
            # 處理所有意願調查的部份
            self.questionnaire_service.assign_having_senior_questionnaire()
            # self.assign_having_senior_questionnaire(spreadsheet_file)

        if with_willingness:
            self.signup_next_service.add_to_pending_groups()

        self.new_senior_service.adding_unregistered_follower_chain()

        # 對所有的班級分配組別
        self.new_senior_service.perform_auto_assignment()

        return errors

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
        self.questionnaire_service.pre_processing(spreadsheet_file)
        self._read_predefined_information()
        self.new_senior_service.perform_table_b_auto_assignment()

    def processing_senior_report(self, spreadsheet_file: str,
                                 from_excel: bool = False, from_scratch: bool = True, no_fix_senior: bool = False,
                                 with_table_b: bool = False,
                                 with_questionnaire: bool = True,
                                 with_willingness: bool = True) -> list[GeneralProcessingError]:

        errors: list[GeneralProcessingError] = []

        if from_scratch:
            err = self._auto_assignment(spreadsheet_file, from_excel=from_excel, no_fix_senior=no_fix_senior,
                                        with_table_b=with_table_b,
                                        with_questionnaire=with_questionnaire,
                                        with_willingness=with_willingness)
            errors.extend(err)
        else:
            self._perform_final_report_processing(spreadsheet_file)

        for class_name in self.new_senior_service.all_classes:
            if class_name in ('日初', '夜初'):
                self._generate_fundamental_report(class_name, spreadsheet_file)
            else:
                self._generate_advanced_report(class_name, spreadsheet_file)

        return errors

    def _read_predefined_information(self, with_table_b: bool = False,
                                     questionnaires_entries: list[QuestionnaireEntry] | None = None):
        if self.from_scratch and not with_table_b:
            return

        spreadsheet = self.config.excel.new_class_predefined_info

        if not os.path.exists(spreadsheet.spreadsheet_file):
            logger.error(f'B 表檔案不存在: {spreadsheet.spreadsheet_file} ')
            return
        else:
            logger.error(f'讀取 B 表: {spreadsheet.spreadsheet_file} ')

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
                if isinstance(entry.studentId, str):
                    entry.studentId = int(entry.studentId)
                if isinstance(entry.groupId, str):
                    entry.groupId = int(entry.groupId)
                # print(f'{entry.studentId} {isinstance(entry.studentId, str)} {isinstance(entry.studentId, int)}')
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
                if (entry.phoneNumber is not None and
                        entry.gender in ('男', '女') and questionnaires_entries is not None):
                    for questionnaire in questionnaires_entries:
                        if (entry.realName == questionnaire.entry.fullName and
                                entry.gender == questionnaire.entry.gender and
                                entry.phoneNumber == questionnaire.entry.mobilePhone):
                            mix_member = questionnaire.member

                if mix_member is None:
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

            self.new_senior_service.add_table_b_member(entry.className, entry.gender, entry.groupId, entry,
                                                       with_table_b=with_table_b)

        logger.info(f'{counter} 位來自意願調查')

        # newbies = sorted(newbies, key=lambda x: x.realName)
        # for newbie in newbies:
        #     print(f'{newbie.realName} {newbie.className} {newbie.phoneNumber} {newbie.studentId} {newbie.lastSenior}')

    def generate_class_groups_statistics(self, filename: str):
        entries: list[NewClassGroupStatistics] = []
        for class_name in self.new_senior_service.all_classes:
            seniors = self.new_senior_service.all_classes[class_name]
            total = 0
            male = 0
            female = 0
            for senior in seniors:
                total += len(senior.members)
                if senior.gender == '女':
                    female += len(senior.members)
                else:
                    male += len(senior.members)

            for senior in seniors:
                if senior.gender == '女':
                    entries.append(NewClassGroupStatistics(senior, 0, female, total))
                else:
                    entries.append(NewClassGroupStatistics(senior, male, 0, total))

        service = ExcelCreationService(entries[0])

        data: list[list[Any]] = []
        for model in entries:
            data.append(model.get_values_in_pecking_order())

        os.path.basename(filename)

        full_file_path = f'{self.config.output_folder}/[班級分組人數概況表]-{os.path.basename(filename)}'

        supplier = (lambda y=x: x for x in data)
        service.write_data(supplier)

        service.save(full_file_path)

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

    def generate_post_lineup_from(self, filename: str, fullpath: str):
        for class_name in self.new_senior_service.all_classes:
            seniors = self.new_senior_service.all_classes[class_name]
            data = []

            for senior in seniors:
                group_sn = 0

                for assigned_member in senior.members:
                    if isinstance(assigned_member.member, MixMember):

                        member = assigned_member.member
                        group_sn += 1

                        phone_list = []
                        if member.questionnaireInfo is not None:
                            phone_list = [x for x in
                                          [member.questionnaireInfo.mobilePhone, member.questionnaireInfo.homePhone] if
                                          x is not None]
                        elif member.detail is not None:
                            detail = member.detail
                            phone_list = [x for x in [detail.mobile_phone, detail.home_phone] if x is not None]

                        datum: dict[str, str | int] = {
                            '組別': senior.groupId,
                            '組序': group_sn,
                            '學員編號': member.get_student_id() if member.get_student_id() is not None else '',
                            '班級': senior.className,
                            '班別': senior.className,
                            '學長': senior.fullName,
                            '姓名': member.get_full_name(),
                            '法名': member.get_dharma_name(),
                            '性別': member.get_gender(),
                            '學員電話行動&市話': "\n".join(phone_list),
                        }
                        data.append(datum)

            spreadsheet = PzProjectExcelSpreadsheetConfig({
                'spreadsheet_file': fullpath,
                'header_row': 2,
            })

            template = ExcelTemplateService(PostLineupModel({}),
                                            spreadsheet,
                                            filename,
                                            self.config.output_folder,
                                            f'{class_name}')

            sheet = template.get_sheet()

            for i in range(1, 3):
                title = sheet.cell(1, i).value
                if title is not None and isinstance(title, str) and '{class_name}' in title:
                    sheet.cell(1, i).value = title.replace('{class_name}', class_name)

            supplier = (lambda y=x: x for x in data)
            template.write_data(supplier, callback=lambda x, y, z: add_page_break(x, y))

    def generate_post_lineups(self):
        files = glob.glob(f'{self.config.excel.post_lineup_template_folder}/*.xlsx')

        for filename in files:
            f = os.path.basename(filename)
            if not f.startswith("~$"):
                try:
                    self.generate_post_lineup_from(f, filename)
                except Exception as e:
                    logger.exception(e)


def generate_senior_reports(cfg: PzProjectConfig,
                            from_scratch: bool, from_excel: bool | None = None,
                            no_fix_senior: bool = False,
                            with_table_b: bool = False,
                            with_questionnaire: bool = True,
                            with_willingness: bool = True) -> list[GeneralProcessingError]:
    if not from_scratch:
        if not os.path.exists(cfg.excel.new_class_predefined_info.spreadsheet_file):
            from_scratch = True

    logger.info(f'Spreadsheet: {cfg.excel.new_class_predefined_info.spreadsheet_file}')
    # logger.info(f'Post Lineup: {cfg.excel.post_lineup_template_folder}')

    generator = SeniorReportGenerator(cfg, from_scratch)
    errors = generator.get_initial_errors()

    from_excel = False if from_excel is None else from_excel

    if cfg.excel.questionnaire.spreadsheet_folder is not None and cfg.excel.questionnaire.spreadsheet_folder != '':
        files = glob.glob(f'{cfg.excel.questionnaire.spreadsheet_folder}/*.xlsx')

        file_counter = 0
        for filename in files:
            f = os.path.basename(filename)
            if not f.startswith("~$"):
                try:
                    file_counter += 1
                    err = generator.processing_senior_report(filename, from_excel=from_excel,
                                                             from_scratch=from_scratch, no_fix_senior=no_fix_senior,
                                                             with_table_b=with_table_b,
                                                             with_questionnaire=with_questionnaire,
                                                             with_willingness=with_willingness)
                    generator.generate_new_class_lineup(filename)
                    generator.generate_class_groups_statistics(filename)
                    generator.generate_post_lineups()
                    errors.extend(err)
                    return errors
                except Exception as e:
                    logger.error(f'{filename} - {e}')
                    raise e
        if file_counter == 0:
            if not with_questionnaire:
                filename = "沒有意願調查表.xlsx"
                err = generator.processing_senior_report(filename, from_excel=from_excel,
                                                         from_scratch=from_scratch, no_fix_senior=no_fix_senior,
                                                         with_table_b=with_table_b,
                                                         with_questionnaire=with_questionnaire,
                                                         with_willingness=with_willingness)
                generator.generate_new_class_lineup(filename)
                generator.generate_class_groups_statistics(filename)
                generator.generate_post_lineups()
                errors.extend(err)
                errors.append(GeneralProcessingError.error("注意! 沒有意願調查表將無法產出新生的基本資料。"))
            else:
                errors.append(GeneralProcessingError.error('沒有意願調查表'))

            return errors
    else:
        err = generator.processing_senior_report(cfg.excel.questionnaire.spreadsheet_file, from_excel=from_excel,
                                                 from_scratch=from_scratch, no_fix_senior=no_fix_senior,
                                                 with_table_b=with_table_b,
                                                 with_questionnaire=with_questionnaire,
                                                 with_willingness=with_willingness)
        generator.generate_new_class_lineup(cfg.excel.questionnaire.spreadsheet_file)
        generator.generate_class_groups_statistics(cfg.excel.questionnaire.spreadsheet_file)
        errors.extend(err)
        return errors
