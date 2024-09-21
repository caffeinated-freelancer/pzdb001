from pz.models.mysql_class_member_entity import MysqlClassMemberEntity
from pz.models.mysql_member_detail_entity import MysqlMemberDetailEntity


class MemberWithDetail(MysqlClassMemberEntity):
    birthday: str
    mobile_phone: str
    home_phone: str
    email: str
    emergency_contact: str
    emergency_contact_dharma_name: str
    emergency_contact_relationship: str
    emergency_contact_phone: str
    personal_id: str
    dharma_protection_position: str
    # ct_world_id: str
    family_code: str
    family_id: str
    family_code_name: str
    threefold_refuge: str
    five_precepts: str
    bodhisattva_vow: str
    have_detail: bool

    def __init__(self, member: MysqlClassMemberEntity, detail: MysqlMemberDetailEntity):
        super().__init__([], [], another_entity=member)

        if detail is not None:
            self.have_detail = True
            self.birthday = detail.birthday
            self.mobile_phone = detail.mobile_phone
            self.email = detail.email
            self.emergency_contact = detail.emergency_contact
            self.emergency_contact_dharma_name = detail.emergency_contact_dharma_name
            self.emergency_contact_relationship = detail.emergency_contact_relationship
            self.emergency_contact_phone = detail.emergency_contact_phone
            self.personal_id = detail.personal_id
            self.dharma_protection_position = detail.dharma_protection_position
            self.family_code = detail.family_code
            self.family_id = detail.family_id
            self.family_code_name = detail.family_code_name
            self.threefold_refuge = detail.threefold_refuge
            self.five_precepts = detail.five_precepts
            self.bodhisattva_vow = detail.bodhisattva_vow
        else:
            self.have_detail = False
