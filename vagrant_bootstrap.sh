#!/bin/bash

set -e

pvcreate /dev/sdc -y
vgcreate swift-runway-vg01 /dev/sdc -y

apt-get update

lxd init --auto
usermod -G lxd vagrant
lxc list > /dev/null
sudo -H -u ubuntu bash -c 'lxc list > /dev/null'
sudo -H -u vagrant bash -c 'lxc list > /dev/null'
apt-get install linux-generic -y

# Prepare the system to enable core dumps in the container, although core
# dumps will not be enabled by default
sysctl kernel.core_uses_pid=0
sysctl kernel.core_pattern=/tmp/%e-%t-%s-%p.core
