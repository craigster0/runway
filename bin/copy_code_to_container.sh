#!/bin/bash

#
#Copyright (c) 2016-2021, NVIDIA CORPORATION.
#SPDX-License-Identifier: Apache-2.0

# this runs on the host and is called by a remote machine, given the name of
# the code directory and the container to put it in

SRC=$1
CNAME=$2

base=`basename $SRC`
base_no_prefix=`echo ${base} | sed "s/${CNAME}_//g"`

if [ $CNAME == "CURRENT" ]; then
    # get the last container in the list
    CNAME=`lxc list | grep swift-runway | cut -d '|' -f2 | awk '{$1=$1;print}' | tail -1`
fi

if [ -z $CNAME ]; then
    # no currently running containers
    echo "No runway guest containers found. Exiting."
    exit 1
fi

cd `dirname $SRC`
tar cf - $base | lxc exec $CNAME -- tar xf - -C /home/swift/code/
lxc exec $CNAME -- rsync -a --delete /home/swift/code/${base}/ /home/swift/code/${base_no_prefix}/
lxc exec $CNAME -- rm -rf /home/swift/code/${base}/
