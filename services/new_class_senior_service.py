from loguru import logger

from pz.comparators import new_class_senior_comparator
from pz.config import PzProjectConfig
from pz.models.mix_member import MixMember
from pz.models.new_class_senior import NewClassSeniorModel
from services.excel_workbook_service import ExcelWorkbookService
from services.grand_member_service import PzGrandMemberService


class NewClassSeniorService:
    config: PzProjectConfig
    senior_by_class_gender: dict[str, list[NewClassSeniorModel]]
    senior_by_student_id: dict[int, list[NewClassSeniorModel]]
    all_classes: dict[str, list[NewClassSeniorModel]]

    def __init__(self, cfg: PzProjectConfig, member_service: PzGrandMemberService):
        self.config = cfg

        new_class_seniors = self._read_all()
        group_id_assignment: dict[str, int] = {}
        self.senior_by_class_gender = {}
        self.senior_by_student_id = {}
        self.all_classes = {}

        for senior in new_class_seniors:
            if senior.className in self.all_classes:
                self.all_classes[senior.className].append(senior)
            else:
                self.all_classes[senior.className] = [senior]

            senior_infos = member_service.find_grand_member_by_pz_name_and_dharma_name(senior.fullName,
                                                                                       senior.dharmaName,
                                                                                       senior.gender)

            if senior_infos is None or senior_infos[0] is None:
                print(f'Warning: senior {senior.fullName} not found')
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
                group_id_assignment[senior.className] = senior.groupId
            key = self.key_of_senior(senior.className, senior.gender)

            if key in self.senior_by_class_gender:
                self.senior_by_class_gender[key].append(senior)
            else:
                self.senior_by_class_gender[key] = [senior]

        for clazz in self.all_classes:
            self.all_classes[clazz].sort(key=lambda x: x.groupId)

    @staticmethod
    def key_of_senior(class_name: str, gender: str):
        return f'{class_name}-{gender}'

    def _read_all(self) -> list[NewClassSeniorModel]:
        workbook = ExcelWorkbookService(NewClassSeniorModel({}), self.config.excel.new_class_senior.spreadsheet_file,
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

    def add_member_to(self, senior: NewClassSeniorModel, mix_member: MixMember):
        mix_member.senior = senior
        for m in senior.members:
            if isinstance(m, MixMember):
                if m.get_student_id() is not None and mix_member.get_student_id() is not None:
                    if m.get_student_id() == mix_member.get_student_id():
                        logger.warning(
                            f'ignore duplicate {m.get_student_id()} {m.get_full_name()} on {senior.className}')
                        return
        senior.members.append(mix_member)
        logger.debug(
            f'adding {mix_member.get_full_name()}/{senior.fullName} at {senior.className}/{senior.groupId}/{senior.gender}')

    def find_by_class_gender(self, class_gender_key: str):
        if class_gender_key in self.senior_by_class_gender:
            for entry in self.senior_by_class_gender[class_gender_key]:
                logger.info(f'{class_gender_key}: {entry.fullName}, current-member: {len(entry.members)}')
        else:
            logger.warning(f'{class_gender_key}: not found')

    def min_member_first_assign(self, class_gender_key: str, member: MixMember):
        if class_gender_key in self.senior_by_class_gender:
            # senior_list = [x for x in self.senior_by_class_gender[class_gender_key]]
            #
            # senior_list.sort()
            senior_list = sorted(self.senior_by_class_gender[class_gender_key], key=new_class_senior_comparator)

            self.add_member_to(senior_list[0], member)
        else:
            logger.warning(f'{class_gender_key}: not found')
