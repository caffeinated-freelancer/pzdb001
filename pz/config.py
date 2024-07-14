import json
import os
import re
from typing import Any, Callable

import yaml


class PzProjectConfigGlobal:
    config: 'PzProjectConfig' = None


class PzProjectBaseConfig:
    def __init__(self, variables: dict[str, Any],
                 sub_initializer: Callable[[str, dict[str, Any]], bool] | None = None) -> None:
        for variable, value in variables.items():
            if isinstance(value, str):
                if variable.endswith('_file') or variable.endswith('_folder'):
                    self.__setattr__(variable, PzProjectConfigGlobal.config.real_path(value))
                else:
                    self.__setattr__(variable, value)
            elif isinstance(value, int):
                self.__setattr__(variable, value)
            elif isinstance(value, dict):
                if sub_initializer is None or not sub_initializer(variable, value):
                    self.__setattr__(variable, value)

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=False)

    def __str__(self) -> str:
        return self.to_json()


class PzProjectLoggingConfig(PzProjectBaseConfig):
    level: str = 'INFO'
    format: str = '{time} - {level} - {message}'
    log_file: str

    def __init__(self, variables: dict[str, Any]) -> None:
        super().__init__(variables)


class PzProjectMySqlConfig(PzProjectBaseConfig):
    user: str
    password: str
    host: str
    database: str

    def __init__(self, variables: dict[str, Any]) -> None:
        super().__init__(variables)


class PzProjectMsAccessConfig(PzProjectBaseConfig):
    db_file: str
    target_table: str

    def __init__(self, variables: dict[str, Any]) -> None:
        super().__init__(variables)


class PzProjectGoogleSpreadsheetConfig(PzProjectBaseConfig):
    semester: str
    spreadsheet_id: str
    sheet_name: str
    fields_map: dict[str, str | list[str]] | None

    def __init__(self, variables: dict[str, Any]) -> None:
        self.fields_map = None
        super().__init__(variables, self.variable_initializer)

    def variable_initializer(self, variable: str, value: Any) -> bool:
        if variable == 'fields_map':
            if isinstance(value, dict):
                self.fields_map = value
            return True
        return False


class PzProjectGoogleConfig(PzProjectBaseConfig):
    secret_file: str
    spreadsheets: dict[str, PzProjectGoogleSpreadsheetConfig]

    def __init__(self, variables: dict[str, Any]) -> None:
        self.spreadsheets = {}
        super().__init__(variables, self.variable_initializer)

    def variable_initializer(self, variable: str, value: Any) -> bool:
        if variable == 'spreadsheets':
            if isinstance(value, dict):
                for name, settings in value.items():
                    if isinstance(settings, dict):
                        self.spreadsheets[name] = PzProjectGoogleSpreadsheetConfig(settings)
                return True
        return False


class PzProjectExcelSpreadsheetConfig(PzProjectBaseConfig):
    spreadsheet_file: str | None
    spreadsheet_folder: str | None
    sheet_name: str | None
    header_row: int | None
    ignore_parenthesis: bool
    data_skip_row: int
    insert_row_after: int
    additional_notes: dict[str, Any]

    def __init__(self, variables: dict[str, Any]) -> None:
        self.spreadsheet_file = None
        self.spreadsheet_folder = None
        self.additional_notes = {}
        self.ignore_parenthesis = False
        self.sheet_name = None
        self.header_row = None
        self.data_skip_row = 0
        self.insert_row_after = 0

        super().__init__(variables)
        if 'additional_notes' in variables and isinstance(variables['additional_notes'], dict):
            self.additional_notes = variables['additional_notes']

        if 'ignore_parenthesis' in variables and isinstance(variables['ignore_parenthesis'], bool):
            self.ignore_parenthesis = variables['ignore_parenthesis']


class PzProjectGraduationStandard:
    weeks: int
    expressions: list[str]

    def __init__(self, weeks: int, variables: list[str]) -> None:
        self.weeks = weeks
        self.expressions = []
        for variable in variables:
            self.expressions.append(variable)

    def calculate(self, counters: dict[str, int]) -> bool:
        graduate = True
        for expression in self.expressions:
            for key, value in counters.items():
                expression = expression.replace(key, str(value))
            graduate = graduate and eval(expression)
        return graduate


class PzProjectGraduationConfig(PzProjectBaseConfig):
    records: PzProjectExcelSpreadsheetConfig
    standards: PzProjectExcelSpreadsheetConfig
    template: PzProjectExcelSpreadsheetConfig
    graduation_standards: dict[int, PzProjectGraduationStandard]

    def __init__(self, variables: dict[str, Any]):
        self.graduation_standards = {}
        super().__init__(variables, self.variable_initializer)

    def variable_initializer(self, variable: str, value: Any) -> bool:
        if variable == 'records':
            self.records = PzProjectExcelSpreadsheetConfig(value)
        elif variable == 'standards':
            self.standards = PzProjectExcelSpreadsheetConfig(value)
        elif variable == 'template':
            self.template = PzProjectExcelSpreadsheetConfig(value)
        elif variable == 'graduation_standards':
            if isinstance(value, dict):
                for name, settings in value.items():
                    if re.match(r'\d+', name):
                        self.graduation_standards[int(name)] = PzProjectGraduationStandard(int(name), settings)
        else:
            return False
        return True

    def get_graduation_standard(self, week: int) -> PzProjectGraduationStandard | None:
        return self.graduation_standards[week] if week in self.graduation_standards else None


class PzProjectExcelConfig(PzProjectBaseConfig):
    questionnaire: PzProjectExcelSpreadsheetConfig
    new_class_lineup: PzProjectExcelSpreadsheetConfig
    templates: dict[str, PzProjectExcelSpreadsheetConfig]
    graduation: PzProjectGraduationConfig
    new_class_senior: PzProjectExcelSpreadsheetConfig
    signup_next_info: PzProjectExcelSpreadsheetConfig
    new_class_predefined_info: PzProjectExcelSpreadsheetConfig

    def __init__(self, variables: dict[str, Any]) -> None:
        self.templates = {}
        super().__init__(variables, self.variable_initializer)

    def variable_initializer(self, variable: str, value: Any) -> bool:
        if variable == 'graduation':
            self.graduation = PzProjectGraduationConfig(value)
        # elif variable == 'questionnaire':
        #     self.questionnaire = PzProjectExcelSpreadsheetConfig(value)
        # elif variable == 'new_class_lineup':
        #     self.new_class_lineup = PzProjectExcelSpreadsheetConfig(value)
        # elif variable == 'new_class_senior':
        #     self.new_class_senior = PzProjectExcelSpreadsheetConfig(value)
        elif variable in ('questionnaire', 'new_class_lineup', 'new_class_senior',
                          'signup_next_info', 'new_class_predefined_info'):
            self.__setattr__(variable, PzProjectExcelSpreadsheetConfig(value))
        elif variable == 'templates':
            if isinstance(value, dict):
                for k, v in value.items():
                    self.templates[k] = PzProjectExcelSpreadsheetConfig(v)
        else:
            return False
        return True


class PzProjectConfig(PzProjectBaseConfig):
    config_filename: str
    workspace: str
    template_folder: str
    output_folder: str
    mysql: PzProjectMySqlConfig
    ms_access_db: PzProjectMsAccessConfig
    google: PzProjectGoogleConfig
    excel: PzProjectExcelConfig
    semester: str
    previous_semester: str
    debug_text_file_output: str
    logging: PzProjectLoggingConfig

    def __init__(self, filename: str, variables: dict[str, Any]) -> None:
        self.config_filename = filename
        if 'workspace' in variables:
            self.workspace = self.real_path(variables['workspace'])
            variables.pop('workspace')
        else:
            self.workspace = self.real_path(r'{USERPROFILE}\Desktop')
            print(f'Warning! workspace path is {self.workspace}')

        if 'output_folder' in variables:
            self.output_folder = self.real_path(variables['output_folder'])
            variables.pop('output_folder')
        else:
            self.workspace = self.real_path(r'{USERPROFILE}\Desktop')
            print(f'Warning! output path is {self.output_folder}')

        for v in ['template_folder', 'debug_text_file_output']:
            if v in variables:
                self.__setattr__(v, self.real_path(variables[v]))
                variables.pop(v)

        # if 'template_folder' in variables:
        #     self.template_folder = self.real_path(variables['template_folder'])
        #     variables.pop('template_folder')
        #
        # if 'debug_text_file_output' in variables:
        #     self.debug_text_file_output = self.real_path(variables['debug_text_file_output'])
        #     variables.pop('debug_text_file_output')

        PzProjectConfigGlobal.config = self
        super().__init__(variables, self.variable_initializer)

    def variable_initializer(self, variable: str, value: Any) -> bool:
        if variable == 'mysql':
            self.mysql = PzProjectMySqlConfig(value)
        elif variable == 'ms_access_db':
            self.ms_access_db = PzProjectMsAccessConfig(value)
        elif variable == 'google':
            self.google = PzProjectGoogleConfig(value)
        elif variable == 'excel':
            self.excel = PzProjectExcelConfig(value)
        elif variable == 'logging':
            self.logging = PzProjectLoggingConfig(value)
        else:
            return False
        return True

    def make_sure_output_folder_exists(self):
        if not os.path.exists(self.output_folder):
            # Create the folder if it doesn't exist
            os.makedirs(self.output_folder)
            print(f"Folder '{self.output_folder}' created successfully!")

    def explorer_output_folder(self):
        os.startfile(self.output_folder)

    @classmethod
    def from_yaml(cls, filename) -> 'PzProjectConfig':
        with open(filename, 'r', encoding='utf-8') as file:
            config_data = yaml.safe_load(file)
            return cls(filename, config_data)

        # Validation and type conversion (replace with your logic)
        # server_data = config_data.get("server", {})
        # if not isinstance(server_data, dict):
        #     raise ValueError("Invalid server data format")
        # database_data = config_data.get("database", {})
        # if not isinstance(database_data, dict):
        #     raise ValueError("Invalid database data format")

        # Create the class object and assign validated values

    def real_path(self, file_path: str) -> str:
        matched = re.match(r'^(.*){([A-Z]+[_A-Z][A-Z]+)}(.*)', file_path)

        if matched:
            if 'WORKSPACE' == matched.group(2):
                # print(f'{matched.group(1)}{self.workspace}{matched.group(3)}')
                return f'{matched.group(1)}{self.workspace}{matched.group(3)}'
            elif 'TEMPLATE' == matched.group(2):
                return f'{matched.group(1)}{self.template_folder}{matched.group(3)}'
            elif 'OUTPUT_FOLDER' == matched.group(2):
                return f'{matched.group(1)}{self.output_folder}{matched.group(3)}'
            return self.real_path(f'{matched.group(1)}{os.getenv(matched.group(2))}{matched.group(3)}')

        matched = re.match(r'^[A-Za-z]:.*', file_path)
        if matched:
            return file_path
        elif file_path.startswith(r'\\'):
            return file_path
        else:
            return os.path.join(self.workspace, file_path)
