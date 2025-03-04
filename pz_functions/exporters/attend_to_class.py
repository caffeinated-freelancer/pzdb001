from pz.cloud.spreadsheet_member_service import PzCloudSpreadsheetMemberService
from pz.config import PzProjectConfig, PzProjectGoogleSpreadsheetConfig
from pz.models.google_class_member import GoogleClassMemberModel
from services.attend_record_service import AttendRecordAsClassMemberService
from services.grand_member_service import PzGrandMemberService


def remap_if_possible(cfg: PzProjectConfig):
    settings: PzProjectGoogleSpreadsheetConfig = cfg.google.spreadsheets.get('class_members')

    if settings is not None:
        GoogleClassMemberModel.remap_variables(settings.fields_map)


def from_attend_records_to_class(cfg: PzProjectConfig):
    service = AttendRecordAsClassMemberService(cfg)
    # grand_member_service = PzGrandMemberService(cfg)
    # senior_service = NewClassSeniorService(cfg, grand_member_service)
    models = service.read_all()

    # senior_service.

    # for model in models:
    #     # print(
    #     #     f'{model.className} {model.classGroup} {model.sn} {model.studentId} {model.realName} {model.dharmaName} {model.gender}')
    #     print(
    #         f'{model.className} {model.classGroup} {model.sn} {model.studentId} {model.realName} {model.deacon} {model.senior}')

    if len(models) > 0:
        remap_if_possible(cfg)

        settings: PzProjectGoogleSpreadsheetConfig = cfg.google.spreadsheets.get('class_members_for_upload')

        if settings is not None:
            gservice = PzCloudSpreadsheetMemberService(settings, cfg.google.secret_file)
            gservice.clear_all(models[0])
            # results: list[GoogleClassMemberModel] = gservice.read_all(GoogleClassMemberModel([]))

            current_group = ''
            group_sn = 0
            for i in range(0, len(models)):
                models[i].sn = str(i + 1)

                if current_group != models[i].className:
                    group_sn = 0
                    current_group = models[i].className

                group_sn += 1
                models[i].groupSn = str(group_sn)

            gservice.write_data(models)
            # for result in results:
            #     print(result.to_json())
