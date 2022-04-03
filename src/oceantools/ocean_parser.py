import argparse
import sys

sys.path.append("../")
from helpers.regex_factory import RegexFactory
from helpers.exception import SpotinstClientException
from models.cluster_roll import ClusterRoll


def get_parser() -> argparse.ArgumentParser:
    """
    Ocean argument parser for roll specification
    :return: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser("aksUpgradeParser")
    parser.add_argument("-i", "--ids",
                        help="The id(s) of the virtual node group to roll. for the whole cluster, provide "
                             "`ALL`")
    parser.add_argument("-p", "--percentage", help="The batch size percentage of each roll")
    args = parser.parse_args()

    return args


def validate_and_parse_args(args: argparse.PARSER) -> ClusterRoll:
    """
    Validates the argparsed from the cli and returns a ClusterRoll object
    :param args: args parsed by get_parser
    :return: ClusterRoll contains comment, virtualNodeGroupIds (optional) and batch percentage size
    """
    ret_val: ClusterRoll = ClusterRoll()
    vng_ids, batch_percentage = args.ids, args.percentage
    vng_removed: dict = {
        "count": 0,
        "removedIds": [],
        "originalIds": []
    }

    if vng_ids and batch_percentage:
        vng_ids = vng_ids.lower().replace("'","").replace('"',"")
        if not vng_ids.replace(" ", "").__contains__("all"):
            vng_ids = vng_ids.split(",")
            vng_removed["originalIds"].extend(vng_ids)
            for vng in vng_ids:
                if not RegexFactory().compile(regex_pattern=RegexFactory.SPOT_VNG_ID_REGEX, spot_id=vng):
                    vng_removed["count"] = vng_removed["count"] + 1
                    vng_removed["removedIds"].append(vng)
                    vng_ids.remove(vng)
                    print(
                        "ERROR: Couldn't roll VNG: `{0}`, the id is invalid and doesn't match the VNG regex of: `{1}`".format(
                            vng, RegexFactory.SPOT_VNG_ID_REGEX
                        ))

        if vng_ids:
            if isinstance(vng_ids, list):
                ret_val.virtual_node_group_ids = vng_ids
            else:
                del ret_val.virtual_node_group_ids

            batch_percentage = int(batch_percentage.replace(" ", ""))
            if 0 < batch_percentage <= 100:
                ret_val.comment = "Cluster roll to upgrade K8s version"
                ret_val.batch_size_percentage = batch_percentage
        else:
            if vng_removed["count"] > 0:
                raise SpotinstClientException(message="No virtual node group ids left after filtering problematic ids."
                                              " Input: {0}, Problematic vngs: {1}".format(vng_removed["originalIds"],
                                                                                          vng_removed["removedIds"]),
                                              response="ERROR")

    elif vng_ids:
        ret_val.virtual_node_group_ids = vng_ids
    elif batch_percentage:
        ret_val.batch_size_percentage = batch_percentage
    else:
        print("vng ids of `{0}` and batch percentage of `{1}` have not set to custom parameters. Roll config will be "
              "set as the default: Batch 20% and the whole cluster will be rolled.".format(vng_ids, batch_percentage))

    print("Roll config: {0}".format(ret_val.dict_to_json()))

    return ret_val
