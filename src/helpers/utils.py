import re
import requests
import json
import random
from time import sleep


def retry_with_backoff(retries=5, backoff_in_seconds=1):
    def rwb(f):
        def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    if x == retries:
                        raise
                    else:
                        print(
                            "Failed to execute function {0} at {1} attempt. Errors: {2}.\nretrying..".format(
                                f.__name__,
                                x, str(e)))
                        time_to_sleep = (backoff_in_seconds * 2 ** x +
                                         random.uniform(0, 1))
                        sleep(time_to_sleep)
                        x += 1

        return wrapper

    return rwb


class Utils:
    under_pat = re.compile(r'_([a-z])')

    def __init__(self):
        pass

    @staticmethod
    def is_json(myjson):
        try:
            out = json.loads(myjson)
        except ValueError as e:
            out = None
        finally:
            return out

    @staticmethod
    def get_random_between_ranges(n1: int, n2: int) -> int:
        return random.uniform(n1,n2)

    def underscore_to_camel(self, name):
        return self.under_pat.sub(lambda x: x.group(1).upper(), name)

    def fix_dict_to_spot_query_params(self, query_params: dict):
        ret_val: dict = {}
        for k, v in query_params.items():
            ret_val[self.underscore_to_camel(k)] = v
        return ret_val

    def check_and_return_if_request_items_are_iterable(self, request: requests.Response):
        ret_val: dict = None
        json_dict = self.is_json(request.text)
        if json_dict:
            if 'response' in json_dict:
                if 'items' in json_dict:
                    ret_val = json_dict['response']['items']

        return ret_val

    def convert_json(self, val, convert):
        new_json = {}
        if val is None:
            return val
        elif type(val) in (int, float, bool, "".__class__, u"".__class__):
            return val

        for k, v in list(val.items()):
            new_v = v
            if isinstance(v, dict):
                new_v = self.convert_json(v, convert)
            elif isinstance(v, list):
                new_v = list()
                for x in v:
                    new_v.append(self.convert_json(x, convert))
            new_json[convert(k)] = new_v
        return new_json