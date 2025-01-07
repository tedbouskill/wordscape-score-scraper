import re

class StringHelpers:
    @staticmethod
    def is_null_or_empty(string: str) -> bool:
        return string is None or string == ''

    @staticmethod
    def contains_alphabetic(text: str) -> bool:
        return any(char.isalpha() for char in text)

    @staticmethod
    def is_all_uppercase(text: str) -> bool:
        return bool(re.match(r'^[A-Z]+$', text.replace(" ", "")))

    @staticmethod
    def is_all_numeric(text: str) -> bool:
        return bool(re.match(r'^\d+$', text))

    @staticmethod
    def convert_to_integer(text: str) -> int:
        try:
            return int(text)
        except ValueError:
            print(f"Cannot convert '{text}' to an integer.")
            return None


