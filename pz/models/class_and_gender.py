import math

from loguru import logger

from pz.models.assigned_member import AssignedMember
from pz.models.auto_assignment_step import AutoAssignmentStepEnum
from pz.models.mix_member import MixMember
from pz.models.mysql_class_member_entity import MysqlClassMemberEntity
from pz.models.new_class_senior import NewClassSeniorModel


class PendingEntry:
    members: list[MixMember]
    description: str | None
    breakable: bool

    def __init__(self, members: list[MixMember], description: str | None, breakable: bool):
        self.members = members
        self.description = description
        self.breakable = breakable

    def len(self):
        return len(self.members)


class TriggerWaitingEntry:
    members: list[MixMember]
    description: str | None

    def __init__(self, members: list[MixMember], description: str | None):
        self.members = members
        self.description = description


class ClassAndGender:
    name: str
    gender: str
    groups: dict[int, NewClassSeniorModel]
    pending_list: list[PendingEntry]
    student_ids: set[int]
    all_followers_student_ids: set[int]
    already_assigned_students: dict[int, int]
    total_counter: int
    pending_counter: int
    avg: int
    pending_group_id: int
    followers: dict[int, list[MixMember]]
    looping_groups: list[list[MixMember]]
    willingness: dict[int, MixMember]
    introducers: dict[int, MysqlClassMemberEntity]
    on_assignment_triggers: dict[int, TriggerWaitingEntry]

    def __init__(self, name, gender):
        self.name = name
        self.gender = gender
        self.groups = {}
        self.pending_list = []
        self.followers = {}
        self.student_ids = set()
        self.all_followers_student_ids = set()
        self.already_assigned_students = {}
        self.total_counter = 0
        self.pending_counter = 0
        self.avg = 0
        self.pending_group_id = 0
        self.looping_groups = []
        self.willingness = {}
        self.introducers = {}
        self.on_assignment_triggers = {}

    def add_group(self, group_id: int, senior: NewClassSeniorModel):
        if group_id not in self.groups:
            self.groups[group_id] = senior
        else:
            logger.warning(f'班級/學長資料重覆: {group_id} at {self.name} / {self.gender}')

    def add_member_to(self, senior: NewClassSeniorModel, mix_member: MixMember, reason: str,
                      assignment: AutoAssignmentStepEnum, deacon: str = None, internal: bool = False,
                      non_follower_only: bool = False) -> bool:

        if non_follower_only and mix_member.get_unique_id() in self.all_followers_student_ids:
            logger.error(f'{self.name}/{self.gender} - {senior.fullName}/{senior.groupId} 忽略有介紹人的學員 {mix_member.get_full_name()}')
            return False
        mix_member.senior = senior

        if mix_member.get_student_id() is not None:
            if mix_member.get_student_id() in self.student_ids:
                if not internal:
                    logger.trace(
                        f'({reason}) 資料重覆: {mix_member.get_full_name()} {mix_member.get_student_id()} 已經存在 {senior.className} / {senior.gender}')
                    return False
            else:
                self.student_ids.add(mix_member.get_student_id())

        senior.members.append(AssignedMember(mix_member, deacon, reason, assignment))
        self.already_assigned_students[mix_member.get_student_id()] = senior.groupId

        if mix_member.get_unique_id() in self.on_assignment_triggers:
            triggered_data = self.on_assignment_triggers[mix_member.get_unique_id()]
            logger.info(
                f'{self.name}/{self.gender} - {mix_member.get_full_name()} 觸發 {[x.get_full_name() for x in triggered_data.members]} 分配至 {senior.fullName}/{senior.groupId}')
            for trigger_entry in triggered_data.members:
                self.add_member_to(senior, trigger_entry, triggered_data.description,
                                   AutoAssignmentStepEnum.INTRODUCER_FOLLOWING)

        logger.trace(
            f'adding {mix_member.get_full_name()}/{senior.fullName} at {senior.className}/{senior.groupId}/{senior.gender}')
        self.total_counter += 1
        return True

    # def min_member_first_assign(self, member: MixMember):
    #     groups = [x for x in self.groups.values()]
    #     senior_list = sorted(groups, key=new_class_senior_comparator)
    #
    #     self.add_member_to(senior_list[0], member)

    def add_to_pending(self, adding_members: list[MixMember], description: str | None = None, breakable: bool = True):
        members: list[MixMember] = []

        for member in adding_members:
            if member.get_student_id() is not None:
                if member.get_student_id() not in self.student_ids:
                    members.append(member)
                    self.student_ids.add(member.get_student_id())
                    self.total_counter += 1
                    self.pending_counter += 1
                else:
                    logger.trace(
                        f'(團體升班) 資料重覆: {member.get_full_name()}/{member.get_student_id()} 已經存在 {self.name} / {self.gender}')
            else:
                members.append(member)
                self.total_counter += 1
                self.pending_counter += 1

        self.pending_list.append(PendingEntry(members, description, breakable))

    def _assign_at(self, pending_group: list[MixMember], assigned_group_id: int, description: str | None = None):
        self.pending_group_id += 1
        for member in pending_group:
            assigned_group = self.groups[assigned_group_id]
            logger.trace(
                f'自動配置 {member.get_full_name()}/{member.get_senior()} 到 {assigned_group.fullName} {self.name}/{self.gender}/{assigned_group_id}')
            reason = f'自動配置 群:{self.pending_group_id}, 人數:{len(pending_group)}, 前學長:{member.get_senior()}'
            if member.classMember is None and member.questionnaireInfo is not None:
                reason = f'自動配置 禪修班意願調查, 介紹人: {member.questionnaireInfo.introducerName}'

            if description is not None and description != '':
                reason = description

            self.add_member_to(assigned_group, member, reason, AutoAssignmentStepEnum.AUTO_ASSIGNMENT, internal=True)

    def force_assigment_on_min_member(self, pending_entry: PendingEntry):
        assigned_group_id = -1
        min_member_count = self.avg + 1000
        for group_id in self.groups.keys():
            if len(self.groups[group_id].members) < min_member_count:
                assigned_group_id = group_id
                min_member_count = len(self.groups[group_id].members)
        self._assign_at(pending_entry.members, assigned_group_id, description=pending_entry.description)

    def _difference_assignment(self, pending_entry: PendingEntry, left_over: int) -> bool:
        pending_group = pending_entry.members

        number_of_members = len(pending_group)
        for group_id in self.groups.keys():
            group_member = len(self.groups[group_id].members)

            if (number_of_members >= 2 and self.avg <= number_of_members + group_member + left_over <= self.avg + 1 or
                    number_of_members + group_member + left_over == self.avg):
                logger.trace(f'{self.name}/{self.gender} : 配置人數為 {len(pending_group)} 至 {group_id} 群組 (滿)')
                logger.trace(
                    f'{self.name}/{self.gender}, group {group_id} / # {group_member}, add {number_of_members}, left over: {left_over}')
                logger.trace(f'{self.avg} <= {number_of_members} + {group_member} + {left_over} <= {self.avg} + 1')

                self._assign_at(pending_group, group_id, description=pending_entry.description)
                # for member in pending_group:
                #     assigned_group = self.groups[group_id]
                #     logger.trace(
                #         f'自動配置 {member.get_full_name()}/{member.get_senior()} 到 {assigned_group.fullName} {self.name}/{self.gender}/{group_id}')
                #     self.add_member_to(
                #         assigned_group, member,
                #         f'自動配置 群:{self.pending_group_id}, 人數:{len(pending_group)}, 前學長:{member.get_senior()}',
                #         internal=True)
                return True
        return False

    def _max_available(self):
        min_value = self.avg + 100

        for group_id in self.groups.keys():
            min_value = min(min_value, len(self.groups[group_id].members))
        return self.avg + 1 - min_value

    def _max_available_group(self) -> int:
        min_value = self.avg + 100
        found_group_id = -1
        for group_id in self.groups.keys():
            value = len(self.groups[group_id].members)
            if value < min_value:
                found_group_id = group_id
                min_value = value
        return found_group_id

    def _trigger_counter(self) -> int:
        counter = 0
        for t in self.on_assignment_triggers.values():
            counter += len(t.members)
        return counter

    def perform_auto_assignment(self) -> bool:
        self.avg = math.floor(self.total_counter + self._trigger_counter() / len(self.groups))

        pending_list: list[PendingEntry] = sorted(self.pending_list, key=lambda x: x.len(), reverse=True)
        pending_size_list = [x.len() for x in pending_list if x.len() > 0]
        logger.debug(
            f'{self.name}/{self.gender}: 組數: {len(self.groups)}, 總數: {self.total_counter}, 未編班: {self.pending_counter}, 平均: {self.avg}, 群: {len(pending_list)}')
        logger.debug(f'{self.name}/{self.gender}: {pending_size_list}')

        counter = 0

        while len(pending_list) > 0:
            pending_list = sorted(pending_list, key=lambda x: x.len(), reverse=True)
            logger.trace([x.len() for x in pending_list])

            max_count = pending_list[0].len()
            max_available = self._max_available()
            counter += 1

            if counter >= 3000:
                raise RuntimeError()

            if max_count > max_available:
                if pending_list[0].breakable:
                    middle = pending_list[0].len() // 2
                    logger.warning(
                        f'{self.name}/{self.gender} 人數: {max_count} 過多 ( > {max_available}), 需要拆班 at {middle}')
                    first = pending_list[0].members[:middle]
                    second = pending_list[0].members[middle:]
                    description = pending_list[0].description if pending_list[0].description is not None else ''
                    logger.debug(f'折成 {len(first)} and {len(second)}')
                    pending_list.pop(0)
                    pending_list.append(PendingEntry(first, f'[拆] {description}', True))
                    pending_list.append(PendingEntry(second, f'[拆] {description}', True))
                else:
                    self.force_assigment_on_min_member(pending_list.pop(0))
                    logger.warning(f'{self.name}/{self.gender} 人數: {max_count} 過多, 強制配置')
                continue

            found = False
            new_pending_list = []
            for x in pending_list:
                if max_count >= 3 and x.len() > 3 or max_count < 3:
                    if not found and self._difference_assignment(x, 0):
                        found = True
                        x = None
                elif max_count == 2:
                    if not found and self._difference_assignment(x, 0):
                        found = True
                        x = None
                if x is not None:
                    new_pending_list.append(x)
            if found:
                pending_list = sorted(new_pending_list, key=lambda x: x.len(), reverse=True)
                # logger.debug([len(x) for x in pending_list])
                continue

            if not found:
                assigned_group_id = self._max_available_group()
                entries = pending_list.pop(0)
                logger.trace(f'{self.name}/{self.gender} : 配置人數為 {entries.len()} 至 {assigned_group_id} 群組')
                self._assign_at(entries.members, self._max_available_group(), description=entries.description)
        logger.trace(f'solved, iteration {counter}')
        return True

    def follow(self, introducer: MysqlClassMemberEntity, mix_member: MixMember):
        student_id = introducer.student_id

        if student_id in self.followers:
            self.followers[student_id].append(mix_member)
            if student_id not in self.introducers:
                raise RuntimeError(f'介紹人 {introducer.real_name} 不存在')
        else:
            self.followers[student_id] = [mix_member]
            self.introducers[student_id] = introducer

        self.all_followers_student_ids.add(mix_member.get_unique_id())

        logger.debug(
            f'{self.name}/{self.gender}, followee: {introducer.real_name}/{introducer.student_id}, {len(self.followers)
            } {[f'{x.get_full_name()}/{x.get_unique_id()}' for x in self.followers[student_id]]}')

    def add_willingness(self, mix_member: MixMember):
        if mix_member.get_unique_id() not in self.willingness:
            self.willingness[mix_member.get_unique_id()] = mix_member

    def have_willingness(self, student_id: int) -> bool:
        logger.trace(f'{student_id} {"in" if student_id in self.willingness else "NOT in"} {self.name}/{self.gender}')
        return student_id in self.willingness

    def processing_followers(self):
        f_number = len(self.followers)
        logger.trace(f'{self.name}/{self.gender}, number of followee: {f_number}')
        if self._loop_detection():
            logger.info(
                f'{self.name}/{self.gender}, number of followee: {f_number} -> {len(self.followers)} (after loop removal)')

        self._find_a_chain_set()

    def _recursive_find(self, student_id: int, follower_list: list[int]) -> list[int] | None:
        logger.trace(f'{student_id} {follower_list}')
        if student_id in self.followers:
            for x in self.followers[student_id]:
                uid = x.get_unique_id()
                if uid in follower_list:
                    logger.warning(
                        f'{self.name}/{self.gender}: loop found {uid}, student id:{student_id}, list:{follower_list}')
                    return follower_list
                follower_list.append(uid)
                rc = self._recursive_find(uid, follower_list)
                if rc is not None:
                    return rc
                follower_list.pop()
        return None

    def _remove_from_follow_list(self, follow_list: list[int]) -> tuple[list[MixMember], int]:
        count = 0
        lopping_entries: list[MixMember] = []

        while len(follow_list) > 0:
            additional_list: list[int] = []

            for student_id in follow_list:
                if student_id in self.followers:
                    entries = self.followers.pop(student_id)
                    count += len(entries)
                    for entry in entries:
                        logger.trace(f'remove {entry.get_full_name()} ({entry.get_unique_id()})')
                        additional_list.append(entry.get_unique_id())
                        lopping_entries.append(entry)
                else:
                    logger.trace(f'{student_id} does not have a follower')
            follow_list = additional_list

        return lopping_entries, count
        # logger.warning(f'loop detected, {count} followers removed')
        # self.looping_groups.append(lopping_entries)

    def _loop_detection(self) -> bool:
        once_have_loop = False

        for entry in self.followers:
            logger.trace(f'{self.name}/{self.gender} : entry {entry}')

        while True:
            have_loop = False
            follow_list: list[int] | None = None

            for student_id in self.followers:
                follow_list = self._recursive_find(student_id, [student_id])
                if follow_list is not None:
                    have_loop = True
                    once_have_loop = True
                    break

            if have_loop:
                lopping_entries, count = self._remove_from_follow_list(follow_list)

                logger.warning(f'loop detected, {count} followers removed')
                self.looping_groups.append(lopping_entries)
                #
                # count = 0
                # lopping_entries: list[MixMember] = []
                #
                # while len(follow_list) > 0:
                #     additional_list: list[int] = []
                #
                #     for student_id in follow_list:
                #         if student_id in self.followers:
                #             entries = self.followers.pop(student_id)
                #             count += len(entries)
                #             for entry in entries:
                #                 logger.debug(f'remove {entry.get_full_name()} ({entry.get_unique_id()})')
                #                 additional_list.append(entry.get_unique_id())
                #                 lopping_entries.append(entry)
                #         else:
                #             logger.trace(f'{student_id} does not have a follower')
                #     follow_list = additional_list
                #
                # logger.warning(f'loop detected, {count} followers removed')
                # self.looping_groups.append(lopping_entries)
            else:
                break
        return once_have_loop

    def perform_follower_loop_assignment(self):
        logger.trace(f'{self.name}/{self.gender} : loop assignment')
        loop_index = 0
        for looping_entries in self.looping_groups:
            loop_index += 1
            logger.error(f'{self.name}/{self.gender} : looping group: {[x.get_full_name() for x in looping_entries]}')
            self.add_to_pending(looping_entries,
                                description=f'禪修班意願調查: {len(looping_entries)}人互為介紹人/被介紹人 ({self.name}/{self.gender}/{loop_index})')

    def _find_chain_root(self, student_id: int):
        for key, values in self.followers.items():
            if student_id in [x.get_unique_id() for x in values]:
                return self._find_chain_root(key)
        return student_id

    def _find_chain_follower(self, followee: int) -> list[int]:
        follower_list: list[int] = []

        if followee in self.followers:
            for follower in self.followers[followee]:
                follower_list.append(follower.get_unique_id())
                for entry in self._find_chain_follower(follower.get_unique_id()):
                    follower_list.append(entry)
        return follower_list

    def _find_a_chain_set(self):
        while True:
            found = False
            for student_id in self.followers:
                root_followee = self._find_chain_root(student_id)
                follow_list = self._find_chain_follower(root_followee)
                follow_list.insert(0, root_followee)

                introducer = self.introducers[root_followee] if root_followee in self.introducers else None

                if introducer is None:
                    raise RuntimeError(f'{self.name}/{self.gender} : {root_followee} 應該是個介紹人, 但不存在')

                logger.trace(f'{self.name}/{self.gender}: root:{root_followee}, list:{follow_list}')
                found = True

                lopping_entries, count = self._remove_from_follow_list(follow_list)

                if count == 0:
                    found = False
                else:
                    description = f'介紹鏈, 介紹人: {introducer.real_name}/{root_followee} - {count} 個被介紹人 {[
                        x.get_full_name() for x in lopping_entries]}'
                    self.on_assignment_triggers[root_followee] = TriggerWaitingEntry(lopping_entries, description)
                    logger.info(
                        f'{self.name}/{self.gender} {description}')
                    # self.looping_groups.append(lopping_entries)
                    break

            if not found:
                break

    def processing_unregistered_follower_chain(self):
        removing_entries: list[int] = []

        for student_id in self.on_assignment_triggers:
            entry = self.on_assignment_triggers[student_id]

            if student_id not in self.introducers:
                raise RuntimeError(f'無此介紹人 {student_id} not found')
            introducer = self.introducers[student_id]

            if not self.have_willingness(student_id):
                logger.error(f'{student_id} with his/her chain {len(entry.members)}')
            elif student_id in self.already_assigned_students:
                group_id = self.already_assigned_students[student_id]
                if group_id not in self.groups:
                    raise RuntimeError(f'{group_id} not found')
                senior = self.groups[group_id]

                description = f'介紹鏈, 介紹人: {introducer.real_name} - {len(entry.members)} 個被介紹人 {[
                    x.get_full_name() for x in entry.members]}'
                for m in entry.members:
                    self.add_member_to(senior, m, description, AutoAssignmentStepEnum.INTRODUCER_FOLLOWING)
                removing_entries.append(student_id)
                logger.warning(f'{self.name}/{self.gender} {description}')
            else:
                logger.info(f'{self.name}/{self.gender} {introducer.real_name}/{student_id} {[
                    x.get_full_name() for x in entry.members]}')

        if len(removing_entries) > 0:
            for student_id in removing_entries:
                del self.on_assignment_triggers[student_id]
