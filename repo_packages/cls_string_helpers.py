class StringHelpers:
    @staticmethod
    def is_null_or_empty(string):
        return string is None or string == ''

    @staticmethod
    def contains_alphabetic(text):
        return any(char.isalpha() for char in text)
