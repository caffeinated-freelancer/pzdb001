import json
from typing import Any

from pz.models.excel_creation_model import ExcelCreationModelInterface
from pz.models.mysql_member_detail_entity import MysqlMemberDetailEntity


class MemberDetailModel(ExcelCreationModelInterface):
    VARIABLE_MAP = {
        'student_id': '學員編號',
        'real_name': '姓名',
        'dharma_name': '法名',
        'gender': '性別',
        'birthday': '生日',
        'mobile_phone': '行動電話',
        'home_phone': '住家電話',
    }

    student_id: str
    real_name: str
    dharma_name: str
    gender: str
    birthday: str
    mobile_phone: str
    home_phone: str

    def __init__(self, values: dict[str, str], entity: MysqlMemberDetailEntity | None = None) -> None:
        if entity is None:
            for k, v in MemberDetailModel.VARIABLE_MAP.items():
                if v in values:
                    self.__dict__[k] = values[v]
        else:
            for k in MemberDetailModel.VARIABLE_MAP.keys():
                if k in entity.__dict__:
                    self.__dict__[k] = entity.__dict__[k]
                else:
                    self.__dict__[k] = None

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=False)

    def new_instance(self, args):
        return MemberDetailModel(args)

    def get_excel_headers(self) -> list[str]:
        return [x for _, x in self.VARIABLE_MAP.items()]

    def get_values_in_pecking_order(self) -> list[Any]:
        return [self.__dict__[x] for x, _ in self.VARIABLE_MAP.items()]

    def generate_query(self, table_name: str) -> tuple[str, list[str | int]]:
        ignored_tuple = ('id', 'student_id')
        variables = []
        params: list[str | int] = []
        have_data = False
        for k in MemberDetailModel.VARIABLE_MAP:
            if k in self.__dict__ and self.__dict__[k] is not None and self.__dict__[k] != '':
                v = self.__dict__[k]
                if isinstance(v, str):
                    v = v.strip()
                if k != '' and k not in ignored_tuple:
                    have_data = True
                variables.append(k)
                params.append(v)

        if not have_data:
            query = f"DELETE FROM {table_name} WHERE student_id = '{self.student_id}'"
            return query, []
        else:
            fields = ",".join([x for x in variables])
            placeholders = ",".join(["%s"] * len(variables))
            on_duplicate = ",".join([f'{x}=%s' for x in variables if x not in ignored_tuple])
            query = f'INSERT INTO {table_name} (id,{fields}) VALUES (%s,{placeholders}) ON DUPLICATE KEY UPDATE {on_duplicate}'
            params.insert(0, int(self.student_id))
            for x in variables:
                if x not in ignored_tuple:
                    params.append(self.__dict__[x])
            return query, params
