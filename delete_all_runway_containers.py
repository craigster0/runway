#!/usr/bin/env python3

"""
do lxc list --format=json swift-runway
...and delete them


while it would be cool if this worked, it doesn't and the docs are bad
https://linuxcontainers.org/lxc/documentation/#python
import lxc
for defined in (True, False):
    for active in (True, False):
        x = lxc.list_containers(active=active, defined=defined)
        print(x, f"=> lxc.list_containers(active={active}, defined={defined})")
"""

import argparse
import glob
import json
import os
import re
import shlex
import shutil
import subprocess
import sys


def parse_profiles_list(cli_output):
    profiles = []
    lines = cli_output.split("\n")
    for line in lines:
        result = re.match("(^\|\s{1}|^)([\w-]+)", line)
        if result is not None:
            profiles.append(result.group(2))
    return profiles


if os.geteuid() != 0:
    print("must be run as root")
    sys.exit(1)

DEFAULT_PREFIX = "swift-runway-"
parser = argparse.ArgumentParser()
parser.add_argument(
    "-a", "--all", action="store_true", default=False, help="Delete everything"
)

parser.add_argument(
    "-p",
    "--prefix",
    default=None,
    help=f"Prefix to look for when deleting. Default: '{DEFAULT_PREFIX}'",
)

args = parser.parse_args()

delete_everything = args.all
prefix = args.prefix
if prefix is None:
    prefix_was_provided = False
    prefix = DEFAULT_PREFIX
else:
    prefix_was_provided = True

VOLUME_GROUP = "swift-runway-vg01"

list_command = "lxc list --format=json"
p = subprocess.run(shlex.split(list_command), stdout=subprocess.PIPE)

containers = json.loads(p.stdout.decode())
to_delete = [x["name"] for x in containers if x["name"].startswith(prefix)]

if to_delete:
    delete_command = f"lxc delete --force {' '.join(to_delete)}"
    print(delete_command)
    p = subprocess.run(shlex.split(delete_command))
    print(f"{len(to_delete)} containers deleted")
else:
    print("No containers to delete")

# delete associated lvm volumes
try:

    if prefix_was_provided:
        lvlist = glob.glob(f"/dev/{VOLUME_GROUP}/{prefix}*")
    else:
        # We'll delete all the lvm volumes if a prefix was not provided
        lvlist = glob.glob(f"/dev/{VOLUME_GROUP}/*")
except FileNotFoundError:
    print("No volumes to delete")
else:
    num_deleted = 0
    for logical_volume in lvlist:
        delete_command = f"lvremove -f {logical_volume}"
        print(delete_command)
        try:
            p = subprocess.run(
                shlex.split(delete_command),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                check=True,
            )
        except subprocess.CalledProcessError as err:
            print(
                f"Error deleting {logical_volume}:\n{err.stderr.rstrip()}",
                file=sys.stderr,
            )
        else:
            num_deleted += 1
    else:
        print(f"{num_deleted} volumes deleted")

# delete associated lxc profiles
profile_list_command = "lxc profile list"
p = subprocess.run(shlex.split(profile_list_command), stdout=subprocess.PIPE)
to_delete = []
for line in p.stdout.decode().split("\n"):
    parts = line.split("|")
    try:
        profile_name = parts[1].strip()
        if profile_name.startswith(prefix):
            to_delete.append(profile_name)
    except IndexError:
        pass
if to_delete:
    for profile in to_delete:
        delete_command = f"lxc profile delete {profile}"
        print(delete_command)
        p = subprocess.run(shlex.split(delete_command))
    print(f"{len(to_delete)} profiles deleted")
else:
    print("No profiles to delete")

# delete container working spaces
for entry_name in os.listdir("guest_workspaces"):
    entry_path = os.path.join("guest_workspaces", entry_name)
    if entry_name == "README" or not os.path.isdir(entry_path):
        continue
    print(entry_path)
    shutil.rmtree(entry_path)

# delete snapshotted container images
images_to_delete = []
image_list_command = 'lxc image list description="Created by swift runway"'
p = subprocess.run(shlex.split(image_list_command), stdout=subprocess.PIPE)
for line in p.stdout.decode().split("\n"):
    if "Created by swift runway" in line:
        parts = line.split("|")
        fingerprint = parts[2].strip()
        alias = parts[1].strip()
        # If we're not deleting everything, we ONLY delete images whose alias
        # starts with the given prefix.
        if delete_everything or (alias != "" and alias.startswith(prefix)):
            images_to_delete.append(fingerprint)
if images_to_delete:
    print(f"Deleting {len(images_to_delete)} images")
    image_delete_command = f"lxc image delete {' '.join(images_to_delete)}"
    print(image_delete_command)
    p = subprocess.run(shlex.split(image_delete_command))
else:
    print("No images to delete")
