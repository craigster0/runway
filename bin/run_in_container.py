#!/usr/bin/env python3

import os
import subprocess
import sys

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
RUNWAY_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
BIN_DIR = os.path.abspath(os.path.join(RUNWAY_DIR, "bin"))


def run_in_container(container_name, user_command):
    """
    Function that runs a command inside a container. It's also meant for being
    imported, that's why we're returning an output + success tuple.
    :param container_name: str
    :param user_command: str
    :return: str, bool
    """
    cmd = (
        "OPTIONALRUNWAYCNAME=1 QUIET=1 source lib/get_container_connection_options.sh "
        "&& ssh -q -t ${{VAGRANTOPTIONS}} ${{RUNWAYHOST}} "
        "lxc exec {} -- {}".format(container_name, " ".join(user_command))
    )
    success = True
    try:
        cp = subprocess.run(
            cmd,
            shell=True,
            cwd=BIN_DIR,
            universal_newlines=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
        )
        output = cp.stdout.strip()
    except subprocess.CalledProcessError as e:
        output = e.output.strip()
        success = False
    return output, success


if __name__ == "__main__":
    usage = "Usage: {} container_name command".format(sys.argv[0])
    if len(sys.argv) < 3:
        print(usage)
        sys.exit(1)

    container_name = sys.argv[1]
    user_command = sys.argv[2:]

    output, success = run_in_container(container_name, user_command)
    print(output)
    if not success:
        sys.exit(1)
