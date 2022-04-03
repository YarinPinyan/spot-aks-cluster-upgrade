import os
from helpers.exception import SpotinstClientException
from helpers.constants import Constants


class Session:
    """
    # Arguments
    spot_token: str
    spot_account_id: str
    spot_controller_cluster_identifier: str
    spot_acd_identifier: str
    """
    _BASE_LOAD_DEPENDENCIES_EXCEPTION_MESSAGE: str = "Couldn't load environment variable `{0}`. Please fix that in " \
                                                     "order to proceed "

    def __init__(self, spot_token: str = None, spot_account: str = None, spot_cluster_identifier: str = None,
                 spot_acd_identifier: str = None):
        self.spot_token = os.environ.get(Constants.SPOT_TOKEN) if spot_token is None else spot_token
        self.spot_account_id = os.environ.get(Constants.SPOT_ACCOUNT) if spot_account is None else spot_account
        self.spot_controller_cluster_identifier = os.environ.get(Constants.CLUSTER_IDENTIFIER) if \
            spot_cluster_identifier is None else spot_cluster_identifier
        self.spot_acd_identifier = os.environ.get(Constants.SPOT_ACD_IDENTIFIER) if \
            spot_acd_identifier is None else spot_acd_identifier
        self.validate_session()

        self.headers = {
            'Authorization': 'Bearer ' + self.spot_token,
            'Content-Type': 'application/json',
        }

    def validate_session(self, ):
        """
        Raise exception if an os environment was missing
        :return: Nothing
        """
        for key, val in vars(self).items():
            if not val:
                raise SpotinstClientException(
                    message=self._BASE_LOAD_DEPENDENCIES_EXCEPTION_MESSAGE.format(key.upper()),
                    response="ERROR")