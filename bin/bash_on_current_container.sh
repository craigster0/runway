#!/bin/bash

# If a Runway container name is not provided, "CURRENT" will be used,
# and the system will try to guess what's the most recent container.
if [[ $# -gt 0 ]]; then
    RUNWAYCNAME="$1"
fi

if [[ $# -gt 1 ]]; then
    LOGINUSER="$2"
else
    LOGINUSER="swift"
fi

# run external to the runway host

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $SCRIPTDIR/lib/get_container_connection_options.sh

if [[ "$LOGINUSER" != "root" ]]; then
    ssh -t ${VAGRANTOPTIONS} ${RUNWAYHOST} lxc exec ${RUNWAYCNAME} -- sudo su - ${LOGINUSER}
else
    ssh -t ${VAGRANTOPTIONS} ${RUNWAYHOST} lxc exec ${RUNWAYCNAME} -- /bin/bash
fi
