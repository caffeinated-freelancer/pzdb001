from pz.config import PzProjectConfig
from pz.models.mix_member import MixMember
from pz.models.signup_next_info import SignupNextInfoModel
from services.excel_workbook_service import ExcelWorkbookService
from services.grand_member_service import PzGrandMemberService
from services.new_class_senior_service import NewClassSeniorService
from services.prev_senior_service import PreviousSeniorService


class SignupNextInfoService:
    ACCEPTABLE_SIGNUP = (
        '日初', '日中', '日高', '日研',
        '夜初', '夜中', '夜高', '夜研',
    )
    config: PzProjectConfig
    member_service: PzGrandMemberService
    prev_senior_service: PreviousSeniorService
    new_class_senior_service: NewClassSeniorService

    def __init__(self, cfg: PzProjectConfig, member_service: PzGrandMemberService,
                 previous_senior_service: PreviousSeniorService, new_class_senior_service: NewClassSeniorService):
        self.config = cfg
        self.member_service = member_service
        self.prev_senior_service = previous_senior_service
        self.new_class_senior_service = new_class_senior_service

    def processing_signups(self) -> list[MixMember]:
        workbook = ExcelWorkbookService(SignupNextInfoModel({}), self.config.excel.signup_next_info.spreadsheet_file,
                                        header_at=self.config.excel.signup_next_info.header_row,
                                        debug=False)

        entries: list[SignupNextInfoModel] = workbook.read_all(required_attribute='fullName')

        print(f'{len(entries)} entries read from {self.config.excel.signup_next_info.spreadsheet_file}')

        signup_entries: list[MixMember] = []

        current_senior = ''
        senior_jobs = []

        debug = False

        for entry in entries:
            signups = set([x for x in [entry.signup1, entry.signup2, entry.signup3, entry.signup4] if
                           x is not None and x in self.ACCEPTABLE_SIGNUP])

            if len(signups) == 0:
                continue

            member_tuple = self.member_service.find_grand_member_by_student_id(entry.studentId)
            if member_tuple is None:
                print(f'Warning: {entry.studentId} / {entry.fullName} not found')
                continue

            mix_member = MixMember(member_tuple[0], member_tuple[1], None, entry)

            if entry.senior != current_senior:
                current_senior = entry.senior

                senior_jobs = self.prev_senior_service.find_previous_senior(entry.className, entry.groupId)
                if len(senior_jobs) > 0:
                    for job in senior_jobs:
                        if debug:
                            print(
                                f'senior {current_senior} service from {entry.className}/{entry.groupId} to {job.className}/{job.groupId}')
                elif current_senior is not None and current_senior != '':
                    if debug:
                        print(
                            f'senior {current_senior} service from {entry.className}/{entry.groupId} no longer exists')

            if len(senior_jobs) > 0:
                found = False
                for job in senior_jobs:
                    if job.className in signups:
                        self.new_class_senior_service.add_member_to(job, mix_member)
                        if debug:
                            print(
                                f'adding {entry.fullName}/{entry.senior} to {entry.className}/{entry.groupId} under {job.className}/{job.groupId}')
                        signups.remove(job.className)
                        found = True
                if not found:
                    if debug:
                        print(f'retain {entry.fullName}/{entry.senior} from {signups}')

            if len(signups) > 0:
                # current_senior = entry.senior
                entry.signups = signups
                signup_entries.append(mix_member)
            # senior_now = self.prev_senior_service.find_previous_senior(entry.className, entry.groupId)
            # if senior_now is not None:
            #     for signup in signups:
            #         if signup == senior_now.className:
            #             pass

        return signup_entries
