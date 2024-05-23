import re


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
