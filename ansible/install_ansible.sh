#!/bin/bash

# if --debug is given in the list of arguments
if [[ " $* " =~ " --debug " ]]; then
    set -x
fi

set +e

echo "Waiting on networking..."
for i in {1..20}; do
    ping -c 1 archive.ubuntu.com
    if [ $? -ne 0 ]; then
        sleep 5
    else
        break
    fi
done
echo "Done!"

distro="RHEL"
installer=`type -P yum`

if [ -z "$installer" ]; then
  installer=`which apt-get`
  distro="Debian"
fi

if [ $distro = "RHEL" ]; then
  $installer install -y epel-release
fi

if [ -z "$installer" ]; then
  echo "Unknown or unsupported distro"
  exit 1
fi

# the update step is needed to make sure package sources are available
$installer update -y

PACKAGELIST="python-pip build-essential gcc libssl-dev python-dev libffi-dev"
if [ $distro = "RHEL" ]; then
  PACKAGELIST="python-pip gcc openssl-devel python-devel libffi-devel libsodium"
fi

$installer install -y $PACKAGELIST

pip install --upgrade pip==9.0.3
pip install ansible
