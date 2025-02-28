import os

from pz.config import PzProjectConfig
from pz.models.qrcode_member_model import QRCodeMemberModel
from services.excel_workbook_service import ExcelWorkbookService
from services.qrcode_service import QRCodeService
from ui.general_ui_service import GeneralUiService


class QRCodeGeneratrUiService(GeneralUiService):
    config: PzProjectConfig
    excel_file: str
    def __init__(self, config: PzProjectConfig, excel_file: str):
        self.config = config
        self.excel_file = excel_file

    def perform_service(self):
        generate_qrcode(self.config, self.excel_file)

    def done(self):
        pass


def generate_qrcode(cfg: PzProjectConfig, excel_file: str):
    qrcode_service = QRCodeService(cfg)

    records_excel = ExcelWorkbookService(QRCodeMemberModel({}), excel_file, None,
                                         debug=False)

    raw_records: list[QRCodeMemberModel] = records_excel.read_all(required_attribute='studentId')

    for record in raw_records:
        if record.realName is not None and record.realName != '':
            class_folder = f'{cfg.output_folder}/{record.className}'
            if not os.path.exists(class_folder):
                os.makedirs(class_folder, exist_ok=True)
            group_folder = f'{class_folder}/{record.groupId}'
            if not os.path.exists(group_folder):
                os.makedirs(group_folder, exist_ok=True)

            png_file = f'{group_folder}/{record.realName}_{record.studentId}.png'
            dharma_name = None
            if record.dharmaName is not None and record.dharmaName != '':
                dharma_name = record.dharmaName.strip()
                if dharma_name != '':
                    png_file = f'{group_folder}/{record.realName}_{dharma_name}_{record.studentId}.png'
            qrcode_service.create_qrcode(str(record.studentId), record.realName.strip(), dharma_name, png_file)
