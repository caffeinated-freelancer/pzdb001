from pz.config import PzProjectConfig
from services.member_card_service import MemberCardService


def import_member_card_from_access(cfg: PzProjectConfig):
    service = MemberCardService(cfg)
    service.import_card_info_from_access()
