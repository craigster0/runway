#!/usr/bin/env python3

import json
import os
import subprocess
import sys

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
RUNWAY_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
BIN_DIR = os.path.abspath(os.path.join(RUNWAY_DIR, "bin"))
VALID_FORMATS = {None, "json", "csv"}


def clean_output(output):
    lines = output.split("\r\n")
    containers = []
    container_info = ""
    for line in lines:
        if not line:
            continue
        clean_line = line.split(" ")[0]
        if "," in clean_line:
            if container_info:
                containers.append(container_info)
            container_info = clean_line.replace('"', "")
        else:
            container_info += ",{}".format(clean_line.replace('"', ""))
    if container_info:
        containers.append(container_info)

    return "\n".join(containers)


def parse_output(output):
    containers_info = []
    for cont in output.split():
        container_info = {}
        split_info = cont.split(",")
        container_info["name"] = split_info.pop(0)
        container_info["ip_addresses"] = split_info
        containers_info.append(container_info)
    return containers_info


usage = "Usage: {} container_name [--csv|--json]".format(sys.argv[0])
try:
    container_name = sys.argv[1]
except IndexError:
    print(usage)
    sys.exit(1)

try:
    format = sys.argv[2]
    if not format.startswith("--"):
        print(usage)
        sys.exit(1)
    format = format.replace("--", "")
except IndexError:
    format = None

if format not in VALID_FORMATS:
    print("Error: Invalid format")
    print(usage)
    sys.exit(1)

cmd = (
    "OPTIONALRUNWAYCNAME=1 QUIET=1 source lib/get_container_connection_options.sh "
    "&& ssh -q -t ${{VAGRANTOPTIONS}} ${{RUNWAYHOST}} lxc list {} -c n4 --format "
    "csv".format(container_name)
)
output = subprocess.check_output(cmd, shell=True, cwd=BIN_DIR, universal_newlines=True)
csv_data = clean_output(output)

if format is None or format == "csv":
    print(csv_data)
else:
    parsed_data = parse_output(csv_data)
    if format == "json":
        print(json.dumps(parsed_data))
    else:
        # We should never get here!
        # We'll leave it here to make it clear where to generate other output
        # formats if that's ever done.
        pass
