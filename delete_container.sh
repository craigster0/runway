# This script deletes a single container together with its profile and all its
# volumes without deleting its workspace.
#
# Please note this script doesn't delete any images.
#
# WARNING: We've recently detected some information is being kept after just
# deleting a single container, so use the following script at your own risk.
# Until further notice, if you want to re-create your container without
# deleting your workspace, we recommend you to run
# `vagrant destroy && vagrant up` from your runway directory (outside your VM).
# It's slower, but we know no data will be kept other than the workspace.

#
#Copyright (c) 2016-2021, NVIDIA CORPORATION.
#SPDX-License-Identifier: Apache-2.0

#!/bin/bash

if [ `id -u` -ne 0 ]; then
    echo 'Must be run as root'
    exit 1
fi

CNAME=$1
if [ -z "$CNAME" ];  then
    echo "Required container name variable is not specified"
    echo
    echo "usage: $0 <CONTAINER-NAME>"
    exit 1
fi

set -e
set -x

lxc delete $CNAME --force
lxc profile delete $CNAME-profile
lvremove --yes /dev/swift-runway-vg01/$CNAME-vol*
