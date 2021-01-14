#!/bin/bash

#
#Copyright (c) 2016-2021, NVIDIA CORPORATION.
#SPDX-License-Identifier: Apache-2.0

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -m|--manifest)
    MANIFEST="$2"
    shift # past argument
    shift # past value
    ;;
    *)    # unknown option
    POSITIONAL+=("$1") # save it in an array for later
    shift # past argument
    ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ -n "$MANIFEST" ]; then
    $SCRIPTDIR/setup_guest_workspace.py -m "${MANIFEST}"
fi

# run external to the runway host
OPTIONALRUNWAYCNAME=1
source $SCRIPTDIR/lib/get_container_connection_options.sh

# Ideally we should get expected options from the manifest
# But for now, you must specify -d <DISTRO> -v <VOLSIZE> e.g., -d RHEL -v 1G
echo "Running in the Linux VM: sudo /vagrant/start.py ${*}"
ssh ${VAGRANTOPTIONS} ${RUNWAYHOST} sudo /vagrant/start.py ${*} && echo "Done"
