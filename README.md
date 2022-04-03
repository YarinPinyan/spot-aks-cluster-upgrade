# spot-aks-cluster-upgrade

Provides a CLI and programmatic interface to Spot by NetApp Ocean API once an AKS cluster upgrade was performed in the AKS clusters which managed by Spot Ocean.

## Flow
In order to run, There is a programmatic CLI with the name of **init.sh**, and may run with the next command:
`sh init.sh`

The next usage screen will be on the stdout:
```bash Usage: ./init.sh Options:
        [-i, --ids]: If present, list the required virtual node group(s) to roll (vng-xxxxxxxx,...)
        [-p, --percentage]: If present, list the required percentage you want to roll the cluster. Integer 0-100
        [-d, --default]: If present, will roll with the default cluster roll (all cluster will be rolled, 20% per batch) - accepts true/1 in order to run.
```

# Scenarios
1. In order to deploy cluster with all VNGs, and 30% of the cluster will be rolled on each batch, run `sh init.sh -i ALL -p 30`
2. In order to deploy specific VNG, with 20% of the VNG on each batch, run `sh init.sh -i "vng-xxxxxxxx" -p 20`
