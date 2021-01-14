#!/bin/bash

#
#Copyright (c) 2016-2021, NVIDIA CORPORATION.
#SPDX-License-Identifier: Apache-2.0

# run external to the runway host

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $SCRIPTDIR/lib/get_container_connection_options.sh

ssh ${VAGRANTOPTIONS} ${RUNWAYHOST} lxc stop ${RUNWAYCNAME} && echo "Done"
