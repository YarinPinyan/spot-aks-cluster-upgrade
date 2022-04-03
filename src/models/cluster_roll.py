import sys
import json

sys.path.append("../")
from helpers.utils import Utils

utilities = Utils()
RollId = type(str)


class ClusterRoll:
    """
    # Arguments
    batch_size_percentage: int
    comment: str
    virtual_node_group_ids: List[str]
    """

    def __init__(self, batch_size_percentage=None, comment=None, virtual_node_group_ids=None):
        self.batch_size_percentage = batch_size_percentage
        self.comment = comment
        self.virtual_node_group_ids = virtual_node_group_ids

    def __nonzero__(self):
        return bool(self.virtual_node_group_ids and self.batch_size_percentage)

    def dict_to_json(self):
        converted, ret_val = {}, {}
        for k, v in vars(self).items():
            k = utilities.underscore_to_camel(k)
            if not k.startswith('_'):
                converted[k] = v

        ret_val['roll'] = converted
        return ret_val
