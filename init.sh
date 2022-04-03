#!/usr/bin/env bash
#
# Copyright 2022 Spotinst LTD.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -e

# The working directory.
DEFAULT_WORK_DIR="$(dirname "$(mktemp -u)")"
DEFAULT_ROLL_CONFIG="-i ALL -p 20"
OCEAN_ROLL_CONFIG_TO_REPLACE="OCEAN_AKS_ROLL_CLUSTER_PREFERENCES"
ACD_IDENTIFIER_RANDOM_ID="RANDOM_ID"
GET_WAAGENT_DATA_JOB_NAME="get-waagent-data"
OCEAN_AKS_CLUSTER_UPGRADE_JOB_NAME="ocean-aks-cluster-upgrade"
AKS_CONNECTOR_LATEST_VERSION="AKS_CONNECTOR_LATEST_VERSION"
BASE_URL="https://spot-public-aks-scripts.s3.amazonaws.com/spot-aks-cluster-upgrade"
OLD_BASE_URL="https://spotinst-public.s3.amazonaws.com/integrations/kubernetes/aks/spot-aks-connector"
FILENAME="spot-aks-connector.yaml"

display_usage() {
        echo -e "\nUsage: $0 Options:\n\t[-i, --ids]: If present, list the required virtual node group(s) to roll (vng-xxxxxxxx,...)\n\t[-p, --percentage]: If present, list the required percentage you want to roll the cluster. Integer 0-100"
        echo -e "\t[-d, --default]: If present, will roll with the default cluster roll (all cluster will be rolled, 20% per batch) - accepts true/1 in order to run."
}

validate_args() {
        # if less than two arguments supplied, display usage
        if [  $# -le 1 ]
          then
            display_usage
            exit 1
        fi

        # check whether user had supplied -h or --help . If yes display usage
        if [[ ( $* == "--help") ||  $* == "-h" ]]
          then
            display_usage
            exit 0
        fi

        declare -A flags
        declare -A booleans
        args=()

        while [ "$1" ];
        do
            arg=$1
            if [ "${1:0:1}" == "-" ]
            then
              shift
              rev=$(echo "$arg" | rev)
              if [ -z "$1" ] || [ "${1:0:1}" == "-" ] || [ "${rev:0:1}" == ":" ]
              then
                bool=$(echo ${arg:1} | sed s/://g)
                booleans[$bool]=true
              else
                value=$1
                flags[${arg:1}]=$value
                shift
              fi
            else
              args+=("$arg")
              shift
            fi
        done

        if [[ ${flags["d"]} ||  ${flags["default"]} ]]; then
          echo -e "Rolling with the default spec"
          main $DEFAULT_ROLL_CONFIG

        else
          percentage=20
          if [[ ${flags["p"]} || ${flags["percentage"]} ]]; then
            percentage=${flags["percentage"]}
            if [[ ${flags["p"]} ]]; then
              percentage=${flags["p"]}
              fi
            if [[ ! $percentage -ge 1 && $percentage -le 100 ]]; then
                display_usage
                exit 0
            fi
          fi

          vng_ids="ALL"
          if [[ ${flags["i"]} || ${flags["ids"]} ]]; then
              vng_ids=${flags["i"]}
              if [[ ${flags["ids"]} ]]; then
                vng_ids=${flags["ids"]}
              fi
          fi

          if [[ ! -z $percentage && ! -z $vng_ids ]]; then
            roll_spec="-i $vng_ids -p $percentage"
            echo -e "Roll spec:\n\t[Ids]: $vng_ids\n\t[Percentage]: $percentage"
            main $roll_spec
          else
            echo -e "Roll spec is invalid\n\t[Ids]: $vng_ids\n\t[Percentage]: $percentage"
            display_usage
            exit 0
          fi
        fi
}

function log() {
        nanosec=$(date +%N)
        timestamp="$(date -u +"%Y-%m-%dT%H:%M:%S").${nanosec:0:3}Z"
        message="$*"
        echo -e "${timestamp} ${message}"
}

function download {
        in="$1"
	      out="$2"
        log "downloading"

        wget \
                 --retry-connrefused \
                 --tries=inf \
                 --timeout=30 \
                 --quiet \
		 -O "${out}" \
                 "${in}"
}

function render {
        base_folder="$1";
        file="$2";
        to_replace="$3"
        shift 3
        id="$@"
        log "rendering $to_replace"

        [ "$(uname)" = Linux ] && sed -i "s/${to_replace}/${id}/g" ${base_folder}/${file} || sed -i "" "s/${to_replace}/${id}/g" ${base_folder}/${file}

}

function delete_jobs {
  in="$@"

  for job in ${in}; do
    log "Deleting $job job"
    kubectl delete job $job -n kube-system || true
  done
}

function apply {
        in="$1"
        log "applying"

        kubectl apply -f "$1"
}

function main {
        # download the file
        download_in="${BASE_URL}/${FILENAME}"
        download_out="${DEFAULT_WORK_DIR}/${FILENAME}"
        roll_spec="$@"

        echo $download_in
        echo $download_out

        # delete existing job if exists
        delete_jobs $GET_WAAGENT_DATA_JOB_NAME $OCEAN_AKS_CLUSTER_UPGRADE_JOB_NAME

        echo $roll_spec
        download "${download_in}" "${download_out}"

        # insert the random id
        acd_identifier="acd-$(openssl rand -hex 4)"
        render "${DEFAULT_WORK_DIR}" "${FILENAME}" "$ACD_IDENTIFIER_RANDOM_ID" "$acd_identifier"

        # insert roll details
        render "${DEFAULT_WORK_DIR}" "${FILENAME}" "$OCEAN_ROLL_CONFIG_TO_REPLACE" $roll_spec

        # insert spot-aks-connector latest version
        latest_aks_connector_version=`curl -X GET "${OLD_BASE_URL}/${FILENAME}" | grep "spotinst/ocean-aks-connector" | awk '{print $2}' | cut -d ":" -f2`
        render "${DEFAULT_WORK_DIR}" "${FILENAME}" "$AKS_CONNECTOR_LATEST_VERSION" $latest_aks_connector_version

        # creating all resources
        apply "${DEFAULT_WORK_DIR}/${FILENAME}"

}

validate_args $@
