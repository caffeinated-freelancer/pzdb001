from typing import Any

from pz.models.auto_assignment_step import AutoAssignmentStepEnum


class AssignedMember:
    member: 'MixMember'
    deacon: str
    reason: str
    assignment: AutoAssignmentStepEnum
    lineup: Any  # NewClassLineup
    info_b: str

    def __init__(self, mix_member: 'MixMember', deacon: str, reason: str, assignment: AutoAssignmentStepEnum,
                 lineup: Any, info_b: str) -> None:
        self.member = mix_member
        self.deacon = deacon
        self.reason = reason
        self.assignment = assignment
        self.lineup = lineup
        self.info_b = info_b
