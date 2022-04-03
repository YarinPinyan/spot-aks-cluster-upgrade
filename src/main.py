from helpers.utils import Utils, retry_with_backoff
from helpers.constants import Constants
from helpers.exception import SpotinstClientException
from models.spot_ocean import SpotOcean
from models.ocean import Ocean
from models.cluster_roll import ClusterRoll, RollId
from oceantools.ocean_parser import get_parser, validate_and_parse_args
from session import Session
from time import sleep
from datetime import datetime
import json
import argparse
import requests


def get_ocean_details(spotinst_session: Session) -> SpotOcean:
    """
    Gets the details of the ocean cluster associated with the k8s cluster
    :param spotinst_session: session initialized with env variables to roll the cluster
    :return: SpotOcean object model representing the Ocean cluster that will be rolled
    """
    ret_val: SpotOcean = SpotOcean()

    print("Trying to get Ocean data from Spot API")

    r = requests.get(url=Constants.BASE_OCEAN_AKS_API_URL,
                     headers=spotinst_session.headers,
                     params={"accountId": spotinst_session.spot_account_id})
    if r.status_code != 200:
        raise SpotinstClientException("Couldn't get ocean id from spot API. Errors: {0} ".format(r.text),
                                      response="ERROR")

    ocean_clusters = json.loads(r.text)
    if ocean_clusters:
        if 'response' in ocean_clusters:
            ocean_clusters = ocean_clusters.get('response').get('items')
            for cluster in ocean_clusters:
                if spotinst_session.spot_controller_cluster_identifier == cluster['controllerClusterId']:
                    ret_val.ocean_id = cluster['id']
                    ret_val.resource_group_name = cluster['aks']['resourceGroupName']
                    ret_val.aks_cluster_name = cluster['aks']['name']
                    break

    if ret_val is None:
        raise SpotinstClientException("Couldn't find cluster with id: `{0}` in account: `{1}`".format(
            spotinst_session.spot_controller_cluster_identifier,
            spotinst_session.spot_account_id),
            response="ERROR")
    else:
        print("Ocean details: {0}".format(ret_val.dict_to_json()))

    return ret_val


@retry_with_backoff(retries=8)
def import_acd_to_ocean(ocean: SpotOcean, spotinst_session: Session) -> requests.Response:
    """
    Importing the new azure cluster data to Ocean (with POST)
    :param ocean: the Ocean cluster associated with the k8s cluster
    :param spotinst_session: session initialized with env variables to roll the cluster
    :return: request.Response holding the response output, may raise exception and retry with backoff if failed
    """
    print("Importing Azure Cluster Data to Ocean.")

    params = {
        'accountId': spotinst_session.spot_account_id,
    }

    json_data = {
        'cluster': {
            'aks': {
                'name': ocean.aks_cluster_name,
                'resourceGroupName': ocean.resource_group_name,
            },
        },
    }

    response = requests.post(
        'https://api.spotinst.io/ocean/azure/k8s/cluster/aks/import/{0}'.format(spotinst_session.spot_acd_identifier),
        headers=spotinst_session.headers,
        params=params, json=json_data)
    if not response.status_code == 200:
        raise Exception(response.json())

    return response


@retry_with_backoff(retries=8)
def update_ocean_cluster(spotinst_session: Session, ocean: SpotOcean, cluster_data: str):
    """
    Update ocean cluster data with fixed configuration
    :param spotinst_session: session initialized with env variables to roll the cluster
    :param ocean: the Ocean cluster associated with the k8s cluster
    :param cluster_data: the cluster data retrieved after the import acd
    :return: None, updates API only with PUT
    """
    ret_val: bool = True

    print("Updating Ocean AKS SaaS with the new cluster data.")

    headers = {
        'Authorization': 'Bearer ' + spotinst_session.spot_token,
        'Content-Type': 'application/json',
    }

    params = {
        'accountId': spotinst_session.spot_account_id,
    }
    response = requests.put('{0}/{1}'.format(Constants.BASE_OCEAN_AKS_API_URL, ocean.ocean_id), headers=headers,
                            params=params,
                            data=cluster_data)
    if not response.status_code == 200:
        raise Exception(json.loads(response.text)['response'])


def fix_cluster_data(cluster_data: requests.Response) -> str:
    """
    Fix the cluster data in order to apply for Spot API
    :param cluster_data: Ocean cluster data, str
    :return: None if the cluster data is not a valid json string else str
    """

    if Utils.is_json(cluster_data.text):
        cluster_data = json.loads(cluster_data.text)['response']['items'][0]
        del cluster_data['cluster']['aks']
        del cluster_data['cluster']['virtualNodeGroupTemplate']['launchSpecification']['resourceGroupName']
        ret_val = json.dumps(cluster_data)
    else:
        raise SpotinstClientException(
            "Retrieved cluster data is not a valid json. cluster data: {0}".format(cluster_data.text))

    return ret_val


def get_running_cluster_roll(spotinst_session: Session, ocean: SpotOcean) -> RollId:
    """

    :param spotinst_session:
    :param ocean:
    :return:
    """
    ret_val: RollId = None
    params = {
        'accountId': spotinst_session.spot_account_id,
    }
    response = requests.get('https://api.spotinst.io/ocean/azure/k8s/cluster/{0}/roll'.format(ocean.ocean_id),
                            headers=spotinst_session.headers,
                            params=params)
    if response.status_code == 200:
        rolls = response.json()['response'].get('items')
        for roll in rolls:
            if roll['status'] == Constants.ROLL_IN_PROGRESS:
                ret_val = roll['id']
                print("Found an existing roll in progress.\n\tId: {0}\n\tProgress: {1}\n\tCreated At: {2}".format(
                    roll['id'],
                    roll['progress'],
                    roll['createdAt']))
                break
    else:
        raise Exception(response.json()['response'])

    return ret_val


@retry_with_backoff(retries=8)
def initiate_cluster_roll(spotinst_session: Session, cluster_roll: ClusterRoll, ocean: SpotOcean) -> RollId:
    """
    Initiates Ocean cluster roll based on the roll spec defined in the init.sh script
    :param spotinst_session: session initialized with env variables to roll the cluster
    :param cluster_roll: Ocean Cluster roll object with roll specification
    :param ocean: the Ocean cluster associated with the k8s cluster
    :return:
    """
    ret_val: RollId = None

    print("Initiating cluster roll with the following specs: {0}".format(cluster_roll.dict_to_json()))
    params = {
        'accountId': spotinst_session.spot_account_id,
    }

    response = requests.post('https://api.spotinst.io/ocean/azure/k8s/cluster/{0}/roll'.format(ocean.ocean_id),
                             headers=spotinst_session.headers,
                             params=params, json=cluster_roll.dict_to_json())
    if not response.status_code == 200:
        errors = response.json()['response'].get('errors')
        if errors:
            code = errors[0].get('code')
            if code == Constants.CLUSTER_ROLL_ALREADY_IN_PROGRESS:
                ret_val = get_running_cluster_roll(spotinst_session=spotinst_session, ocean=ocean)
            elif code == Constants.CLUSTER_HAS_NO_ACTIVE_INSTANCES:
                print("Couldn't roll the cluster {0}, Reason: {1}. Exiting the process".format(ocean.ocean_id,Constants.CLUSTER_HAS_NO_ACTIVE_INSTANCES))
                exit(1)
            else:
                print("Found an unknown status of: {0} when trying to initiate cluster roll. Exiting the process".format(code))
                exit(1)
        else:
            raise Exception(json.loads(response.text)['response'])
    else:
        ret_val: RollId = json.loads(response.text)['response']['items'][0]['id']

    return ret_val


@retry_with_backoff(retries=5, backoff_in_seconds=0.6)
def display_cluster_roll_progress(cluster_roll: ClusterRoll, ocean: SpotOcean, spotinst_session: Session):
    """
    Displaying the cluster roll progress
    :param spotinst_session: session initialized with env variables to roll the cluster
    :param cluster_roll: Ocean Cluster roll object with roll specification
    :param ocean: the Ocean cluster associated with the k8s cluster
    :return: None
    """
    should_display: bool = True
    params = {
        'accountId': spotinst_session.spot_account_id,
    }
    init_time: datetime = datetime.now()
    should_update_date: bool = True

    while should_display:
        r = requests.get(
            url="https://api.spotinst.io/ocean/azure/k8s/cluster/{0}/roll/{1}".format(ocean.ocean_id, cluster_roll.id),
            headers=spotinst_session.headers,
            params=params)

        cluster_roll_progress = json.loads(r.text)['response']['items']
        if cluster_roll_progress:
            cluster_roll_progress = cluster_roll_progress[0]
            if cluster_roll_progress['status'] == Constants.ROLL_IN_PROGRESS:
                if should_update_date:
                    init_time = datetime.strptime(cluster_roll_progress['createdAt'],'%Y-%m-%dT%H:%M:%S.%fZ')
                    should_update_date = False

                print("------------- Cluster roll progress -------------")
                print('Current batch: {0}, Num of batches: {1}'.format(cluster_roll_progress['currentBatch'],
                                                                       cluster_roll_progress['numOfBatches']))
                print("Cluster roll percentage: {0}\n{1}".format(cluster_roll_progress['progress']['value'], "-" * 50))
                sleep(Utils.get_random_between_ranges(2, 10))
                print("------------- Detailed status -------------")
                print(cluster_roll_progress['progress']['detailedStatus'])
            else:
                print("Cluster roll status {0} is different than in progress status. Will finish the process.".format(cluster_roll_progress['status']))
        else:
            print("Couldn't find cluster roll data, exiting the process.\n{0}".format("-" * 50))
            exit(1)


        time_passed_since_roll_begin = ((datetime.now() - init_time).total_seconds() / 60)
        print("Time passed since the roll begin: {0} minutes\n{1}".format(
            time_passed_since_roll_begin, "-" * 50))
        should_display = cluster_roll_progress['progress']['value'] != 100.0 and time_passed_since_roll_begin < 30
        sleep(Utils.get_random_between_ranges(10, 60))


def main():
    spotinst_session = Session()
    cluster_roll_data: ClusterRoll = validate_and_parse_args(args=get_parser())
    ocean: SpotOcean = get_ocean_details(spotinst_session=spotinst_session)
    existing_cluster_roll = get_running_cluster_roll(spotinst_session=spotinst_session, ocean=ocean)
    if not existing_cluster_roll:
        cluster_data = import_acd_to_ocean(spotinst_session=spotinst_session, ocean=ocean)
        cluster_data = fix_cluster_data(cluster_data)
        update_ocean_cluster(spotinst_session=spotinst_session, ocean=ocean, cluster_data=cluster_data)
        cluster_roll_id = initiate_cluster_roll(spotinst_session=spotinst_session, ocean=ocean,
                                                cluster_roll=cluster_roll_data)

        cluster_roll_data.__setattr__('id', cluster_roll_id)

    else:
        cluster_roll_data.__setattr__('id', existing_cluster_roll)
        display_cluster_roll_progress(cluster_roll=cluster_roll_data,
                                      spotinst_session=spotinst_session,
                                      ocean=ocean)
    exit(1)


if __name__ == '__main__':
    main()