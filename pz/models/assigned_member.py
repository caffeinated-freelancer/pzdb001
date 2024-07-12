class AssignedMember:
    member: 'MixMember'
    deacon: str
    reason: str

    def __init__(self, mix_member: 'MixMember', deacon: str, reason: str):
        self.member = mix_member
        self.deacon = deacon
        self.reason = reason
