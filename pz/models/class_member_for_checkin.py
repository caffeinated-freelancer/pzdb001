import json
import re
from typing import Any

from pz.models.excel_creation_model import ExcelCreationModelInterface


class ClassMemberForCheckinModel(ExcelCreationModelInterface):
    VARIABLE_MAP = {
        'student_id': '學員編號',
        'real_name': '學員姓名',
        'dharma_name': '法名',
        'class_name': '班級',
        'class_group': '組別',
        'gender': '性別',
        'birthday': '生日末四碼',
        'mobile_phone': '電話末四碼',
    }

    student_id: str
    real_name: str
    dharma_name: str
    class_name: str
    class_group: str
    gender: str
    birthday: str
    mobile_phone: str

    def __init__(self, columns: list[str], values: list[Any]) -> None:
        for i, column in enumerate(columns):
            if column in self.VARIABLE_MAP:
                value = values[i]
                if value is None or value == '':
                    setattr(self, column, None)
                elif column == 'birthday':
                    matched = re.match(r'^\d{4}-(\d{2})-(\d{2})$', value)
                    if matched:
                        setattr(self, column, f'{matched.group(1)}{matched.group(2)}')
                    else:
                        setattr(self, column, None)
                elif column == 'mobile_phone':
                    matched = re.match(r'^\d{4}-\d{2}(\d{4})$', value)
                    if matched:
                        setattr(self, column, matched.group(1))
                    else:
                        setattr(self, column, None)
                else:
                    setattr(self, column, value)

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=False)

    def new_instance(self, args):
        return ClassMemberForCheckinModel([], [])

    def get_excel_headers(self) -> list[str]:
        return [x for _, x in self.VARIABLE_MAP.items()]

    def get_values_in_pecking_order(self) -> list[Any]:
        return [self.__dict__[x] for x, _ in self.VARIABLE_MAP.items()]
