#!/bin/bash

#
#Copyright (c) 2016-2021, NVIDIA CORPORATION.
#SPDX-License-Identifier: Apache-2.0

set -e

CNAME=$1
if [ -z "$CNAME" ]; then
  echo "usage: $0 <container-name> [BASEIMAGE name] [--debug] [--delete-container]"
  exit 1
fi
shift

BASEIMAGE=$1
if [ -z "$BASEIMAGE" ]; then
  BASEIMAGE=runway-base
fi

DEBUG=''
# if --debug is given in the list of arguments
if [[ " $* " =~ " --debug " ]]; then
    set -x
    DEBUG="--debug"
fi

lxc exec $CNAME -- shutdown -h now
lxc stop $CNAME || true
echo "Trying to delete old image..."
lxc image alias delete $BASEIMAGE || true
lxc image delete $BASEIMAGE || true
lxc publish -f $CNAME --alias $BASEIMAGE description="Created by swift runway"
if [[ " $* " =~ " --delete-container " ]]; then
    lxc delete $CNAME
else
    lxc start $CNAME
    lxc exec $CNAME -- mount -a
fi
