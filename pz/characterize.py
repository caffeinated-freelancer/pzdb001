import re
from math import floor


class CharacterizeCodec:
    @staticmethod
    def encoder(name) -> str | None:
        match = re.match(r'^0([23456789])(\d{3,4})(\d{4})$', name)

        if match:
            leading = int(match.group(1))
            first = int(match.group(2))
            second = int(match.group(3))
            second_char = chr(second + 0x4e00)

            if leading == 9:
                return chr(first + 0x4e00) + second_char
            elif leading in (2, 3, 4, 5, 6, 7, 8) and len(match.group(2)) == 3:
                return chr(10000 + leading * 1000 + first + 0x4e00) + second_char
            elif leading == 2:
                return chr(first + 0x20000) + second_char
            elif leading == 4 and len(match.group(2)) == 4:
                return chr(10000 + first + 0x20000) + second_char
        return None


    @staticmethod
    def decoder(name, hyphen: bool = False) -> str | None:
        if name is None:
            return None
        if len(name) != 2:
            return None

        first = ord(name[0])
        second = ord(name[1])
        second -= 0x4e00

        if 0x4e00 <= first <= 0x9fff:
            first -= 0x4e00
            leading = floor(first / 10000)
            first = first % 10000
            if leading == 0:
                if hyphen:
                    f1 = floor(first/100)
                    f2 = first % 100
                    return f"09{f1:0>2}-{f2:0>2}{second:0>4}"
                else:
                    return f"09{first:0>4}{second:0>4}"
            elif leading == 1:
                leading = floor(first / 1000)
                first = first % 1000
                if hyphen:
                    return f"0{leading}-{first:0>3}-{second:0>4}"
                else:
                    return f"0{leading}{first:0>3}{second:0>4}"
        elif 0x20000 <= first <= 0x2a6df:
            first -= 0x20000
            leading = floor(first / 10000)
            first = first % 10000
            if leading == 0:
                if hyphen:
                    return f"02-{first:0>4}-{second:0>4}"
                else:
                    return f"02{first:0>4}{second:0>4}"
            elif leading == 1:
                if hyphen:
                    return f"04-{first:0>4}-{second:0>4}"
                else:
                    return f"04{first:0>4}{second:0>4}"
        else:
            return hex(first)
