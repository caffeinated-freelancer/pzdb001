import json

from pz.models.excel_model import ExcelModelInterface


class GraduationStandards(ExcelModelInterface):
    VARIABLE_MAP = {
        'classNameInFile': '檔名班別',
        'className': '班別',
        'perfectAttendance': '全勤',
        'diligent': '勤學',
        'graduationMinimum': '結業',
        'graduationMakeupLimit': '補課上限',
        'graduationAbsentLimit': '缺席上限',
    }

    classNameInFile: str
    className: str
    perfectAttendance: int
    diligent: int
    graduationMinimum: int
    graduationMakeupLimit: int
    graduationAbsentLimit: int

    def __init__(self, values: dict[str, str]):
        for k, v in GraduationStandards.VARIABLE_MAP.items():
            # print(f'{k}: str')
            if v in values:
                # if values[v] is not None:
                self.__dict__[k] = values[v]

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=False)

    def new_instance(self, args):
        return GraduationStandards(args)
