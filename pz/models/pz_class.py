from collections import OrderedDict

from loguru import logger

from pz.utils import full_name_to_names


class PzClassGroup:
    groupId: int
    seniorName: str
    seniorDharmaName: str
    seniorStudentId: int

    def __init__(self, group_id: int, senior: str):
        real_name, dharma_name = full_name_to_names(senior)
        self.groupId = group_id
        self.seniorName = real_name
        self.seniorDharmaName = dharma_name
        self.seniorStudentId = 0

    def set_senior_id(self, student_id: int):
        self.seniorStudentId = student_id


class PzClass:
    pzClassName: str
    pzClassGroups: OrderedDict[int, PzClassGroup]

    def __init__(self, class_name: str):
        self.pzClassName = class_name
        self.pzClassGroups = OrderedDict()

    def add_class_group(self, group_id: int, senior: str):
        if group_id not in self.pzClassGroups:
            self.pzClassGroups[group_id] = PzClassGroup(group_id, senior)
        else:
            prev = self.pzClassGroups[group_id]
            if senior != prev.seniorName:
                logger.warning(
                    f'Warning: class:[{self.pzClassName}], group:[{group_id}], senior:[{senior} vs {prev.seniorName}]')
