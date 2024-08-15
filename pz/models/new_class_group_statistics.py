from typing import Any

from pz.models.excel_creation_model import ExcelCreationModelInterface
from pz.models.new_class_senior import NewClassSeniorModel


class NewClassGroupStatistics(ExcelCreationModelInterface):
    VARIABLE_MAP = {
        'serialNo': '總序',
        'className': '班級',
        'groupId': '組別',
        'fullName': '學長姓名',
        'dharmaName': '法名',
        'gender': '性別',
        'numberOfMembers': '分組人數',
        'numberOfMale': '男學員人數',
        'numberOfFemale': '女學員人數',
        'numberOfClassMembers': '班級人數',
    }
    serialNo: int
    className: str
    groupId: int
    fullName: str
    dharmaName: str
    gender: str
    numberOfMembers: int
    numberOfMale: int
    numberOfFemale: int
    numberOfClassMembers: int

    def __init__(self, senior: NewClassSeniorModel, male: int, female: int, total: int) -> None:
        self.serialNo = senior.serialNo
        self.className = senior.className
        self.groupId = senior.groupId
        self.fullName = senior.fullName
        self.dharmaName = senior.dharmaName
        self.gender = senior.gender
        self.numberOfMembers = len(senior.members)
        self.numberOfMale = male
        self.numberOfFemale = female
        self.numberOfClassMembers = total

    def get_excel_headers(self) -> list[str]:
        return [x for _, x in NewClassGroupStatistics.VARIABLE_MAP.items()]

    def get_values_in_pecking_order(self) -> list[Any]:
        return [self.__dict__[x] for x, _ in NewClassGroupStatistics.VARIABLE_MAP.items()]

    def new_instance(self, args):
        pass
