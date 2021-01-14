#!/bin/bash

#
#Copyright (c) 2016-2021, NVIDIA CORPORATION.
#SPDX-License-Identifier: Apache-2.0

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

help() {
    echo "Description:"
    echo ""
    echo "  Build a VM and multiple containers of the same kind. The first"
    echo "  container will always be created from scratch, and the rest will "
    echo "  be created from an image based on the first one."
    echo ""
    echo "Flags:"
    echo ""
    echo "  -C, --container-count:  Mandatory. Number of containers that have"
    echo "                          to be created."
    echo "  -d, --distro:           Mandatory. Container distro."
    echo "  -h, --help:             Prints this message."
    echo "  -m, --manifest:         Path to the manifest file."
    echo "  -p, --container-prefix: Mandatory. string that will be used as the"
    echo "                          prefix for container names as well as for"
    echo "                          the workspace name unless -w is specified."
    echo "  -w, --workspace:        Workspace name (not path!). If specified,"
    echo "                          it will be used as a workspace name"
    echo "                          instead of using the container prefix."
    echo ""
    echo "  Any other argument will be passed directly to the start.py script"
    echo "  when creating the new containers (except for the first one)."
    echo "  Here's some flags you might be interested in:"
    echo ""
    echo "  -n, --no-install:  Installation of components will not be"
    echo "                     re-attempted. Keep in mind components will be"
    echo "                     installed when the first container is created,"
    echo "                     and the remaining containers are created from"
    echo "                     an image based on the first one. This option is"
    echo "                     highly recommended unless you want to do"
    echo "                     different things for each container when"
    echo "                     installing a component."
    echo "  -s, --no-snapshot: A snapshot will not be taken after each"
    echo "                     container is created (except for the first"
    echo "                     one). This option is highly recommended unless"
    echo "                     you specifically need to create the images."
}

ADDITIONALARGS=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -c|--container-name)
    echo "ERROR: you can't specify a container name when creating multiple containers at once."
    echo ""
    help
    exit 1
    ;;
    -C|--container-count)
    CONTAINER_COUNT="$2"
    if [[ "$CONTAINER_COUNT" -lt 2 ]]; then
        echo "ERROR: container count has to be 2 or greater"
        echo ""
        help
        exit 1
    fi
    shift # past argument
    shift # past value
    ;;
    -d|--distro)
    DISTRO="$2"
    shift # past argument
    shift # past value
    ;;
    -h|--help)
    help
    exit 0
    ;;
    -m|--manifest)
    MANIFEST="$2"
    shift # past argument
    shift # past value
    ;;
    -p|--container-prefix)
    CONTAINER_PREFIX="$2"
    shift # past argument
    shift # past value
    ;;
    -w|--workspace)
    WORKSPACE="$2"
    shift # past argument
    shift # past value
    ;;
    *)    # unknown option
    ADDITIONALARGS+=("$1") # save it in an array for later
    shift # past argument
    ;;
esac
done
set -- "${ADDITIONALARGS[@]}" # restore additional parameters

if [[ -z "$CONTAINER_COUNT" ]]; then
    echo "ERROR: -C / --container-count argument is mandatory"
    echo ""
    help
    exit 1
fi

if [[ -z "$CONTAINER_PREFIX" ]]; then
    echo "ERROR: -p / --container-prefix argument is mandatory"
    echo ""
    help
    exit 1
fi

if [[ -z "$DISTRO" ]]; then
    echo "ERROR: -d / --distro argument is mandatory"
    echo ""
    help
    exit 1
fi

if [[ -z "$WORKSPACE" ]] && [[ -z "$MANIFEST" ]]; then
    echo "ERROR: You have to specify at least one of -m / --manifest or -w / --workspace."
    echo ""
    help
    exit 1
fi

if [[ -z "$WORKSPACE" ]]; then
    WORKSPACE=$CONTAINER_PREFIX
fi

set -e

if [[ -n "$MANIFEST" ]]; then
    $SCRIPTDIR/build_vm_and_container.py --distro $DISTRO --manifest $MANIFEST --workspace $WORKSPACE --container-name ${CONTAINER_PREFIX}1
else
    $SCRIPTDIR/build_vm_and_container.py --distro $DISTRO --workspace $WORKSPACE --container-name ${CONTAINER_PREFIX}1
fi

for (( i=2; i<=$CONTAINER_COUNT; i++ )); do
    $SCRIPTDIR/create_container.sh --distro $DISTRO --workspace $WORKSPACE --container-name ${CONTAINER_PREFIX}${i} ${*}
done
