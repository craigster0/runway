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
echo 'kernel.core_uses_pid=0' >> /etc/sysctl.conf
echo 'kernel.core_pattern=/tmp/%e-%t-%s-%p.core' >> /etc/sysctl.conf
sysctl --system

# It looks like there's been a bug in Ubuntu since (at least) 2006 that prevents
# from properly loading the above settings, so we have to reload them at start up
# https://bugs.launchpad.net/ubuntu/+source/procps/+bug/50093
cat > /etc/cron.d/reload-sysctl << EOF
SHELL=/bin/bash
@reboot root /bin/sleep 5 && /sbin/sysctl --system
EOF
