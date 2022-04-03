import json
import sys

sys.path.append("../")
from helpers.utils import Utils

utilities = Utils()


class SpotOcean:
    """
    # Arguments
    ocean_id: str
    resource_group_name: str
    aks_cluster_name: str
    """

    def __init__(self,
                 ocean_id=None,
                 resource_group_name=None,
                 aks_cluster_name=None):
        self.ocean_id = ocean_id
        self.resource_group_name = resource_group_name
        self.aks_cluster_name = aks_cluster_name

    def __nonzero__(self):
        return bool(self.ocean_id and self.resource_group_name)

    def dict_to_json(self):
        """
        convert dict to json
        :return: dictionary converted to json
        """
        converted, ret_val = {}, {}
        for k, v in vars(self).items():
            k = utilities.underscore_to_camel(k)
            converted[k] = v

        ret_val['cluster'] = {'aks': converted}
        return ret_val
