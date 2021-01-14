#!/bin/bash

#
#Copyright (c) 2016-2021, NVIDIA CORPORATION.
#SPDX-License-Identifier: Apache-2.0

# run external to the runway host

if [ -z "$RUNWAYHOST" ]; then
    RUNWAYHOST=dev
fi

if [ -z "$RUNWAYCNAME" ]; then
    RUNWAYCNAME="CURRENT"
fi

BN=`basename $PWD`;
TARGET_DIR=/tmp/${RUNWAYCNAME}_${BN}/
exclude='--exclude=.git';
excludemsg='(excluding .git)';
if [[ $1 = "--with-git" ]]; then
    exclude='';
    excludemsg='(including .git)';
fi;
echo "rsyncing $PWD to dev box ($BN) $excludemsg";
# get it to /tmp on the runway host
#TODO: add in the necessary excludes (or maybe do that on the host side?)
rsync --progress -a --delete $exclude ./ $RUNWAYHOST:$TARGET_DIR
# now tell runway to move it to the right place
ssh $RUNWAYHOST -- '~/runway/bin/copy_code_to_container.sh' $TARGET_DIR $RUNWAYCNAME
