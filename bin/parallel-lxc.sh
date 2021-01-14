#!/bin/bash

#
#Copyright (c) 2016-2021, NVIDIA CORPORATION.
#SPDX-License-Identifier: Apache-2.0

#set -x

help() {
    echo "Description:"
    echo ""
    echo "  Run a command on multiple LXC containers at once."
    echo ""
    echo "Flags:"
    echo ""
    echo "  --help:      Prints this message."
    echo "  -p, --push:  <src> <dest>. Push file located in <src> location to <dest> in container."
    echo "  -h, --hosts: Hosts file. Each line must contain a container name."
    echo "  -H, --host:  Additional host entry (container name). You can"
    echo "               specify more than one additional entry by passing the"
    echo "               -H / --host flag multiple times."
}

PUSH=false
POSITIONAL=()
CMDLINEHOSTS=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -p|--push)
    PUSH=true
    SRC="$2"
    DEST="$3"
    shift # past argument
    shift # past src
    shift # past dest
    ;;
    --help)
    help
    exit 0
    ;;
    -h|--hosts)
    HOSTSFILE="$2"
    shift # past argument
    shift # past value
    ;;
    -H|--host)
    CMDLINEHOSTS+=("$2")
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

CONTAINERS=()

if [[ -n "$HOSTSFILE" ]]; then
    while read -r line; do
        if [ -n "$line" ]; then
            # Doing this extra loop JIC several containers were found in a
            # single line
            for c in $line; do
                CONTAINERS+=("$c")
            done
        fi
    done <"$HOSTSFILE"
fi

if (( ${#CMDLINEHOSTS[@]} )); then
    for i in "${CMDLINEHOSTS[@]}"; do
        CONTAINERS+=("$i")
    done
fi

if [ ${#CONTAINERS[@]} -eq 0 ]; then
    echo "ERROR: you haven't specified any containers to run your command on."
    echo ""
    help
    exit 1
#else
#    echo "Container list: ${CONTAINERS[@]}"
fi

# run external to the runway host
OPTIONALRUNWAYCNAME=1
source $SCRIPTDIR/lib/get_container_connection_options.sh

for RUNWAYCNAME in "${CONTAINERS[@]}"; do
    echo ""
    if $PUSH
    then
        echo "===> Running PUSH '${SRC}' to '${RUNWAYCNAME}/${DEST}'"
        ssh -t ${VAGRANTOPTIONS} ${RUNWAYHOST} lxc file push ${SRC} ${RUNWAYCNAME}/${DEST}
        echo "===> End of PUSH '${SRC}' to '${RUNWAYCNAME}/${DEST}'"
    else
        echo "===> Running '${*}' on ${RUNWAYCNAME}"
        ssh -t ${VAGRANTOPTIONS} ${RUNWAYHOST} lxc exec ${RUNWAYCNAME} -- "${*}"
        echo "===> End of '${*}' on ${RUNWAYCNAME}"
    fi
done
