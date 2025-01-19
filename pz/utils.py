import datetime
import glob
import os
import re


class PzFile:
    filepath: str
    filename: str

    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)


def personal_id_verification(id_number: str, debug: bool = False) -> bool:
    letters = 'ABCDEFGHJKLMNPQRSTUVXYWZIO'
    letter_values = {letter: (i // 10 + 1, i % 10) for i, letter in enumerate(letters)}

    if not re.match(r"[A-Z]\d{9}", id_number):
        if re.match(r"[A-Z][A-Z]\d{8}", id_number):
            id_number = id_number[0] + chr(ord('0') + letter_values[id_number[1]][1]) + id_number[2:]
        else:
            return False

    # print(letter_values)

    first_letter = id_number[0]
    if first_letter not in letter_values:
        return False

    first_letter_value = letter_values[first_letter]
    numeric_id = [first_letter_value[0], first_letter_value[1]] + [int(digit) for digit in id_number[1:]]

    weights = [1, 9, 8, 7, 6, 5, 4, 3, 2, 1, 1]
    total = sum(n * w for n, w in zip(numeric_id, weights))
    if debug:
        print(id_number, numeric_id, weights, total)

    return total % 10 == 0


def full_name_to_real_name(name: str) -> str:
    if name is not None:
        match = re.match(r'(.*)\s*\(.*', name)
        if match:
            return match.group(1)
    return name


def full_name_to_names(name: str) -> tuple[str, str]:
    if name is not None:
        matched = re.match(r'(.*)\s*\((.*)\)', name)

        if matched:
            return matched.group(1), matched.group(2)

    return name, ""


def names_to_pz_full_name(real_name: str, dharma_name: str | None) -> str:
    full_name = real_name
    if dharma_name is not None and dharma_name != "":
        full_name = f'{real_name}({dharma_name})'
    return full_name


def logical_xor(a: bool, b: bool) -> bool:
    return (a or b) and not (a and b)


def get_formatted_datetime() -> str:
    now = datetime.datetime.now()
    formatted_date_time = now.strftime("%Y-%m-%d_%H-%M-%S")
    return formatted_date_time


def format_phone_number(phone_number: int) -> str:
    phone_number_str = str(phone_number)

    if len(phone_number_str) != 9:
        return phone_number_str
    return f"0{phone_number_str[:3]}-{phone_number_str[3:]}"


def normalize_phone_number(phone_number: str) -> tuple[str | None, bool]:
    if phone_number is None:
        return None, False

    phone_number = phone_number.strip()

    if phone_number == '' or phone_number == '-':
        return None, False

    if phone_number in ['未提供', '無', '勿打宅電', '海外居士', '沒電話']:
        return phone_number, False

    if re.match(r'09\d{2}-\d{6}', phone_number):
        return phone_number, True
    elif re.match(r'0\d{2,3}-\d{7,84}', phone_number):
        return phone_number, True

    match = re.match(r'(09\d{2})(\d{6})', phone_number)
    if match:
        return f'{match.group(1)}-{match.group(2)}', True

    match = re.match(r'(\d{2,3})\s*-\s*(\d{6,7})', phone_number)
    if match:
        return f'{match.group(1)}-{match.group(2)}', True

    match = re.match(r'(09\d{2})-(\d{3})-(\d{3})', phone_number)
    if match:
        return f'{match.group(1)}-{match.group(2)}{match.group(3)}', True

    match = re.match(r'(09\d{2})-(\d{2})(\d{6})', phone_number)
    if match:
        return f'{match.group(1)}{match.group(2)}-{match.group(3)}', True

    match = re.match(r'(0[234567])(\d{7,8})', phone_number)
    if match:
        return f'{match.group(1)}-{match.group(2)}', True

    match = re.match(r'(0[234567])\s*-+\s*(\d{7})', phone_number)
    if match:
        return f'{match.group(1)}-{match.group(2)}', True

    # print(phone_number)
    return phone_number, False


def simple_phone_number_normalization(phone_number: str | None) -> str | None:
    normalization_phone_number, _ = normalize_phone_number(phone_number)
    return normalization_phone_number


def tuple_to_coordinate(row, col):
    """Converts a (row, column) tuple to its corresponding Excel coordinate,
       supporting columns beyond XFD (maximum column)."""
    if not isinstance(row, int) or not isinstance(col, int):
        raise ValueError("Row and column must be integers.")
    if row <= 0 or col <= 0:
        raise ValueError("Row and column must be positive integers.")

    base_letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    second_letters = base_letters * 26  # Double the alphabet for columns beyond Z

    col_letter = ""
    # Handle columns up to 'Z' (base_letters)
    while col > len(base_letters):
        col, remainder = divmod(col - 1, len(base_letters))
        col_letter = base_letters[remainder] + col_letter

    # Handle columns beyond 'Z' (second_letters)
    while col > 0:
        col, remainder = divmod(col - 1, 26)
        col_letter = second_letters[remainder] + col_letter

    # Combine and return the Excel coordinate
    return col_letter + str(row)


# # Example usage with a column larger than 26
# row = 7
# col = 32  # Corresponds to "AD"

def explorer_folder(folder: str):
    os.startfile(folder)


def safe_index(target_list: list, looking_for: str, default_value: int) -> int:
    try:
        return target_list.index(looking_for)
    except ValueError:
        return default_value


def excel_files_in_folder(folder: str) -> list[PzFile]:
    files = glob.glob(f'{folder}/*.xlsx')

    excel_files = []

    for file in files:
        pz_file = PzFile(file)
        if not pz_file.filename.startswith("~$"):
            excel_files.append(pz_file)

    return excel_files
