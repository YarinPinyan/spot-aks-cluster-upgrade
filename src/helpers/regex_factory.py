import re


class RegexFactory(object):
    SPOT_VNG_ID_REGEX: str = "^\s*((vng)-[^\W_]{8})\s*$"  # noqa 605

    @staticmethod
    def compile(spot_id: str, regex_pattern: str) -> bool:
        """
        Validates if the spot it matches the given regex pattern
        :param spot_id:
        :param regex_pattern: the pattern to compare
        :return: True if matches the regex, False otherwise
        """
        ret_val: bool = False
        if re.match(regex_pattern, spot_id):
            ret_val = True
        return ret_val
