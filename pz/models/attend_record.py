import json
import re

from pz.models.excel_model import ExcelModelInterface


class AttendRecord(ExcelModelInterface):
    VARIABLE_MAP = {
        'studentId': '學員編號',
        'realName': '姓名',
        'dharmaName': '法名',
        'gender': '性別',
        'groupName': '組別',
        'groupNumber': '組號',
    }

    studentId: str
    realName: str
    dharmaName: str
    gender: str
    groupName: str
    groupNumber: str
    records: dict[str, str | None]

    # transit
    className: str
    recordOrder: int

    def __init__(self, values: dict[str, str]):
        for k, v in AttendRecord.VARIABLE_MAP.items():
            # print(f'{k}: str')
            if v in values:
                # if values[v] is not None:
                self.__dict__[k] = values[v]

        self.records = {}

        for k, v in values.items():
            if k not in AttendRecord.VARIABLE_MAP.values():
                matched = re.match(r'^(\d{1,2})/(\d{1,2})$', k)
                if matched:
                    self.records[k] = v

        self.recordOrder = 0

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=False)

    def new_instance(self, args):
        return AttendRecord(args)
