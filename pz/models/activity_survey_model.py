from pz.models.excel_model import ExcelModelInterface


class ActivitySurveyModel(ExcelModelInterface):
    VARIABLE_MAP: dict[str, str] = {
        'no': 'No.',
        'realName': '姓名',
        'deacon': '執事',
        'dharmaName': '法名',
        'gender': '性別',
        'className': '班級',
        'groupId': '組別',
        'dharmaProtector': '護法會',
        'notes': '調查備註',
    }

    no: int
    realName: str
    deacon: str
    dharmaName: str
    gender: str
    groupId: int
    dharmaProtector: str
    notes: str

    def __init__(self, values: dict[str, str]):
        super().__init__()
        for k, v in ActivitySurveyModel.VARIABLE_MAP.items():
            if v in values:
                self.__dict__[k] = values[v]

    def new_instance(self, args):
        pass
