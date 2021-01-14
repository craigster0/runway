#!/bin/bash

#
#Copyright (c) 2016-2021, NVIDIA CORPORATION.
#SPDX-License-Identifier: Apache-2.0

# run external to the runway host

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $SCRIPTDIR/../..
eval RUNWAYDIR=`pwd`

if [ -z "$RUNWAYHOST" ]; then
    if vagrant ssh-config >/dev/null 2>&1; then
        if [ -z "$QUIET" ]; then
            echo "Connecting to Vagrant VM..."
        fi
        # We currently don't support multiple Vagrant hosts, but if we want to (some day), we just need to populate
        # this variable:
        VAGRANTHOST=""
        VAGRANTOPTIONS=`vagrant ssh-config $VAGRANTHOST | sed '/^[[:space:]]*$/d' |  awk 'NR>1 {print " -o "$1"="$2}'`
        RUNWAYHOST=localhost
    else
        RUNWAYHOST=dev
    fi
fi

if [ -z "$VAGRANTOPTIONS" ] && [ -z "$QUIET" ]; then
    echo "Connecting to $RUNWAYHOST..."
fi

if [ -z "$RUNWAYCNAME" ]; then
    RUNWAYCNAME="CURRENT"
fi

if [ $RUNWAYCNAME == "CURRENT" ]; then
    # get the last container in the list
    RUNWAYCNAME=`ssh ${VAGRANTOPTIONS} ${RUNWAYHOST} lxc list | grep swift-runway | cut -d '|' -f2 | awk '{$1=$1;print}' | tail -1`
fi

# If $OPTIONALRUNWAYCNAME is set, it means we don't require a container name
if [ -z $RUNWAYCNAME ] && [ -z $OPTIONALRUNWAYCNAME ]; then
    # no currently running containers
    echo "No runway guest containers found. Exiting."
    exit 1
fi

# Example of how to use vars we just got:
# ssh -t ${VAGRANTOPTIONS} ${RUNWAYHOST} lxc exec ${RUNWAYCNAME} -- 'sudo su - swift'
