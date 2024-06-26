from pz.models.mysql_class_member_entity import MysqlClassMemberEntity
from pz.models.mysql_member_detail_entity import MysqlMemberDetailEntity
from pz.models.new_class_senior import NewClassSeniorModel
from pz.models.pz_questionnaire_info import PzQuestionnaireInfo
from pz.models.signup_next_info import SignupNextInfoModel


class MixMember:
    detail: MysqlMemberDetailEntity | None
    classMember: MysqlClassMemberEntity | None
    questionnaireInfo: PzQuestionnaireInfo | None
    signupNextInfo: SignupNextInfoModel | None
    senior: NewClassSeniorModel | None

    def __init__(self, detail: MysqlMemberDetailEntity | None, class_member: MysqlClassMemberEntity | None,
                 questionnaire: PzQuestionnaireInfo | None, signup_next: SignupNextInfoModel | None):
        self.detail = detail
        self.classMember = class_member
        self.questionnaireInfo = questionnaire
        self.signupNextInfo = signup_next
        self.senior = None

    def is_new_student(self):
        return self.detail is None

    def get_student_id(self) -> int | None:
        if self.detail is not None:
            return int(self.detail.student_id)
        elif self.classMember is not None:
            return self.classMember.student_id
        elif self.signupNextInfo is not None:
            return self.signupNextInfo.studentId
        return None

    def get_full_name(self) -> str:
        if self.questionnaireInfo is not None:
            return self.questionnaireInfo.fullName
        elif self.classMember is not None:
            return self.classMember.real_name
        else:
            return ''

    def get_dharma_name(self) -> str:
        if self.detail is not None:
            return self.detail.dharma_name
        elif self.classMember is not None:
            return self.classMember.dharma_name
        else:
            return ''

    def get_introducer_name(self) -> str:
        if self.questionnaireInfo is not None:
            return self.questionnaireInfo.introducerName
        else:
            return ''

    def get_remark(self) -> str:
        if self.questionnaireInfo is not None:
            return self.questionnaireInfo.remark
        elif self.signupNextInfo is not None:
            return f"{self.signupNextInfo.className}/{self.signupNextInfo.senior}"
        else:
            return ''

    def get_tee(self) -> str:
        if self.questionnaireInfo is not None:
            return self.questionnaireInfo.tee
        elif self.signupNextInfo is not None:
            return '上期學員'
        else:
            return ''

    def get_phone(self) -> str:
        if self.questionnaireInfo is not None:
            phone = str(self.questionnaireInfo.mobilePhone)
            if self.questionnaireInfo.homePhone is not None:
                phone += '\n' + self.questionnaireInfo.homePhone
            return phone
        elif self.detail is not None:
            phone = self.detail.mobile_phone if self.detail.mobile_phone is not None else ''
            if self.detail.home_phone is not None:
                if phone == '':
                    phone = self.detail.home_phone
                else:
                    phone += '\n' + self.detail.home_phone
            return phone
        else:
            return ''

    def get_last_record(self) -> str:
        last_record = ''
        if self.classMember is not None:
            last_record = f'{self.classMember.class_name}/{self.classMember.senior}'
        return last_record

    '''
                        phone = member.questionnaireInfo.mobilePhone
                    if member.questionnaireInfo.homePhone is not None:
                        phone += '\n' + member.questionnaireInfo.homePhone
                    last_record = ''
                    if member.classMember is not None:
                        last_record = f'{member.classMember.class_name}/{member.classMember.senior}'

                    datum: dict[str, str | int] = {
                        '組序': group_sn,
                        '姓名': member.questionnaireInfo.fullName,
                        '班別': senior.className,
                        '學長': senior.fullName,
                        '組別': senior.groupId,
                        '法名': member.detail.dharma_name if member.detail is not None else '',
                        '學員電話行動&市話': phone,
                        '上期班別/學長': last_record,
                    }
    '''
