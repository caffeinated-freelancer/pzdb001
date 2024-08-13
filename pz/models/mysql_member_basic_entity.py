from typing import Callable

from .json_class import JSONClass


def mysql_schema_fine_tunner(creation_columns: list[str]):
    creation_columns.insert(0, "`id` int NOT NULL COMMENT 'Student ID'")
    creation_columns.append("`updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    creation_columns.append("PRIMARY KEY (`id`)\n")


class MysqlMemberBasicEntity(JSONClass):
    TABLE_NAME: str = 'member_basics'
    # MORE_TABLE_NAME: str = 'member_more_basics'
    PZ_MYSQL_COLUMN_NAMES: dict[str, str] = {
        '學員編號': 'student_id',
        '姓名': 'real_name',
        '法名': 'dharma_name',
        '性別': 'gender',
        '出生日期': 'birthday',
        '行動電話': 'mobile_phone',
        '住家電話': 'home_phone',
        'Email': 'email',
        '緊急聯絡人': 'emergency_contact',
        '緊急聯絡人法名': 'emergency_contact_dharma_name',
        '緊急聯絡人稱謂': 'emergency_contact_relationship',
        '緊急聯絡人電話': 'emergency_contact_phone',
        '身分證字號': 'personal_id',
        '護法會職稱': 'dharma_protection_position',
        # '中台信眾編號': 'ct_world_id',
        '家屬碼': 'family_code',
        '家屬碼ID': 'family_id',
        '家屬碼稱謂': 'family_code_name',
        '是否受三皈': 'threefold_refuge',
        # '受三皈依日期': 'threefold_refuge_date',
        '是否受五戒': 'five_precepts',
        # '受五戒日期': 'five_precepts_date',
        '是否受菩薩戒': 'bodhisattva_vow',
        # '受菩薩戒日期': 'bodhisattva_vow_date',
    }
    CT_WORLD_FIELD_NAME_MAP: dict[str, str] = {
        'student_id': '學員編號',
        'real_name': '姓名',
        'field3': '英文姓',
        'field4': '英文名',
        'gender': '性別',
        'field6': '年齡',
        'birthday': '出生日期',
        'mobile_phone': '行動電話',
        'home_phone': '住家電話',
        'email': 'Email',
        'field11': '公司名稱',
        'field12': '公司職稱',
        'field13': '公司電話',
        'field14': '學位',
        'field15': '畢業學校',
        'field16': '畢業學校系所',
        'field17': '國籍',
        'field18': '介紹人',
        'field19': '介紹人稱謂',
        'field20': '介紹人電話',
        'emergency_contact': '緊急聯絡人',
        'emergency_contact_dharma_name': '緊急聯絡人法名',
        'emergency_contact_relationship': '緊急聯絡人稱謂',
        'emergency_contact_phone': '緊急聯絡人電話',
        'field25': '防疫證書證號',
        'field26': '已上傳covid-19疫苗接種紀錄卡',
        'field27': '備註',
        'dharma_name': '法名',
        'field29': '皈依師德號',
        'personal_id': '身分證字號',
        'field31': '護照及其他證件號碼',
        'dharma_protection_position': '護法會職稱',
        'field33': '本山發心',
        'field34': '親眷發心稱謂',
        'family_code': '家屬碼',
        'field36': '新制最高禪修班別(學佛經歷)',
        'field37': '舊制最高禪修班別',
        'field38': '通訊(郵遞區號)',
        'field39': '通訊(國家)',
        'field40': '通訊(縣市)',
        'field41': '通訊(鄉鎮市區)',
        'field42': '通訊(街道門牌)',
        'field43': '學員狀態',
        'field44': '身心狀況',
        'field45': '心理正常',
        'field46': '生理正常',
        'field47': '心理狀態',
        'field48': '生理狀態',
        'field49': '專長',
        'field50': '身高(cm)',
        'field51': '體重(kg)',
        'field52': '是否具學界人士身分',
        'field53': '教職員工作單位',
        'field54': '教職員職稱',
        'field55': '是學生',
        'field56': '參加社團',
        'field57': '現任社團職稱',
        'field58': '曾任社團職稱',
        'field59': '目前就讀學校',
        'field60': '目前系所',
        'field61': '目前年級',
        'field62': '大專禪學會職稱',
        'field63': '可否寄通啟',
        'field64': '可否寄中台月刊',
        'field65': '可否寄簡訊',
        'field66': '可否寄email',
        'field67': '電話聯絡時段',
        'field68': '家長姓名',
        'field69': '家長聯絡電話',
        'field70': '家長職業',
        'field71': '小車車號',
        'field72': '已繳個資同意書',
        'ct_world_id': '中台信眾編號',
        'field74': '資料回山日',
        'threefold_refuge': '是否受三皈',
        'threefold_refuge_date': '受三皈依日期',
        'five_precepts': '是否受五戒',
        'five_preceptsDate': '受五戒日期',
        'bodhisattva_vow': '是否受菩薩戒',
        'bodhisattva_vow_date': '受菩薩戒日期',
        'field81': '打七次數',
        'field82': '護七次數',
        'field83': '護夏次數',
        'field84': '護戒次數',
        'field85': '是否圓滿福慧護照',
        'field86': '報名表個人註記1',
        'field87': '報名表個人註記2',
        'field88': '報名表個人註記3',
        'field89': '報名表個人註記4',
        'field90': '報名表個人註記5',
        'field91': '全名',
        'field92': '副名',
        'field93': '姓',
        'field94': '中間名',
        'field95': '名',
        'field96': '法名2',
        'field97': '皈依師德號2',
        'field98': '行動電話2',
        'field99': '住家電話2',
        'field100': 'Email2',
        'field101': '出生地(國家)',
        'field102': '出生地(省)',
        'field103': '出生地(縣市)',
        'field104': '籍貫(國家)',
        'field105': '籍貫(省)',
        'field106': '籍貫(縣市)',
        'field107': '永久地(國家)',
        'field108': '永久地(郵遞區號)',
        'field109': '永久地(縣市)',
        'field110': '永久地(鄉鎮市區)',
        'field111': '永久地(街道門牌)',
        'field112': '來精舍原因',
        'field113': '婚姻狀態',
        'field114': '緊急聯絡人2',
        'field115': '緊急聯絡人2 法名',
        'field116': '緊急聯絡人2 稱謂',
        'field117': '緊急聯絡人2 電話',
        'field118': '家長工作單位',
        'field119': '首次上課日期',
        'field120': '小車車號2',
        'field121': '機車車號',
        'field122': '欲發心組別',
        'family_id': '家屬碼ID',
        'family_code_name': '家屬碼稱謂',
        'field125': '個資同意書編號',
        'field126': '2012/10/01後到',
        'field127': 'Field127',
    }

    MYSQL_SCHEMA_FINE_TUNNER: Callable[[list[str]], None] = mysql_schema_fine_tunner

    id: int

    student_id: str
    real_name: str
    dharma_name: str
    gender: str
    birthday: str
    mobile_phone: str
    home_phone: str
    email: str
    emergency_contact: str
    emergency_contact_dharma_name: str
    emergency_contact_relationship: str
    personal_id: str
    dharma_protection_position: str
    ct_world_id: str
    family_code: str

    additional: dict[str, str]

    def __init__(self, params: dict[str, str]) -> None:
        for key, value in params.items():
            setattr(self, key, value)

        for v in self.PZ_MYSQL_COLUMN_NAMES.values():
            if v not in self.__dict__:
                self.__dict__[v] = None

        if self.student_id is not None:
            self.id = int(self.student_id)
        else:
            self.id = -1

    # @staticmethod
    # def member_more_basics_creation() -> list[str]:
    #     creation_columns: list[str] = [
    #         "`id` int NOT NULL COMMENT 'Student ID'",
    #         "`additional` JSON DEFAULT NULL COMMENT '額外資訊'",
    #         "`updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
    #         "PRIMARY KEY (`id`)\n",
    #     ]
    #     return creation_columns
