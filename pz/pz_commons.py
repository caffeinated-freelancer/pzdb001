import re

ACCEPTABLE_CLASS_NAMES = (
    '日初', '日中', '日高', '日研',
    '夜初', '夜中', '夜高', '夜研',
)


def phone_number_normalize(phone_number: str | None) -> str | None:
    if phone_number is None:
        return None

    matched = re.match(r'^(09\d{2})-(\d{3})-(\d{3})$', phone_number)
    if matched:
        return f'{matched.group(1)}-{matched.group(2)}{matched.group(3)}'

    matched = re.match(r'^(09\d{2})(\d{3})(\d{3})$', phone_number)
    if matched:
        return f'{matched.group(1)}-{matched.group(2)}{matched.group(3)}'

    return phone_number
