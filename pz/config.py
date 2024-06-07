import json
from typing import Any, Callable

import yaml


class PzProjectBaseConfig:
    def __init__(self, variables: dict[str, Any],
                 sub_initializer: Callable[[str, dict[str, Any]], bool] | None = None) -> None:
        for variable, value in variables.items():
            if isinstance(value, str) or isinstance(value, int):
                self.__setattr__(variable, value)
            elif isinstance(value, dict):
                if sub_initializer is None or not sub_initializer(variable, value):
                    self.__setattr__(variable, value)

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=False)

    def __str__(self) -> str:
        return self.to_json()


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

    def __init__(self, variables: dict[str, Any]) -> None:
        super().__init__(variables)


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
    spreadsheet_file: str
    sheet_name: str
    header_row: int

    def __init__(self, variables: dict[str, Any]) -> None:
        super().__init__(variables)


class PzProjectExcelConfig(PzProjectBaseConfig):
    questionnaire: PzProjectExcelSpreadsheetConfig
    new_class_lineup: PzProjectExcelSpreadsheetConfig
    templates: dict[str, PzProjectExcelSpreadsheetConfig]

    def __init__(self, variables: dict[str, Any]) -> None:
        self.templates = {}
        super().__init__(variables, self.variable_initializer)

    def variable_initializer(self, variable: str, value: Any) -> bool:
        if variable == 'questionnaire':
            self.questionnaire = PzProjectExcelSpreadsheetConfig(value)
        elif variable == 'new_class_lineup':
            self.new_class_lineup = PzProjectExcelSpreadsheetConfig(value)
        elif variable == 'templates':
            if isinstance(value, dict):
                for k, v in value.items():
                    self.templates[k] = PzProjectExcelSpreadsheetConfig(v)
        else:
            return False
        return True


class PzProjectConfig(PzProjectBaseConfig):
    ATTRIBUTES = [
        'access_db_filename',
        'access_db_target_table',
        'google_member_spreadsheet_id',
        'google_secret_file',
        'introducer_template_file',
        'output_folder',
        'introducer_input',
        'introducer_sheet_name',
    ]

    mysql: PzProjectMySqlConfig
    ms_access_db: PzProjectMsAccessConfig
    google: PzProjectGoogleConfig
    excel: PzProjectExcelConfig
    output_folder: str
    semester: str
    previous_semester: str

    def __init__(self, variables: dict[str, Any]) -> None:
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
        else:
            return False
        return True

    @classmethod
    def from_yaml(cls, filename) -> 'PzProjectConfig':
        with open(filename, 'r', encoding='utf-8') as file:
            config_data = yaml.safe_load(file)
            return cls(config_data)

        # Validation and type conversion (replace with your logic)
        # server_data = config_data.get("server", {})
        # if not isinstance(server_data, dict):
        #     raise ValueError("Invalid server data format")
        # database_data = config_data.get("database", {})
        # if not isinstance(database_data, dict):
        #     raise ValueError("Invalid database data format")

        # Create the class object and assign validated values
