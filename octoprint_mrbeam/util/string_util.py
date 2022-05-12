import re


def separate_camelcase_words(string, separator=' '):
    if string is None:
        return ''
    return remove_extra_spaces(re.sub(r"(\w)([A-Z])", r"\1" + separator + r"\2", string))


def remove_extra_spaces(string):
    return re.sub(' +', ' ', string).strip()
