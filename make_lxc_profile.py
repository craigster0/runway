#!/usr/bin/env python3

import subprocess
import shlex
import sys
import os.path


def undo_lv_and_exit(last_used_index, cname, volume_group):
    print(
        "There was an error trying to create logical volume "
        "'/dev/%s/%s-vol%s'. We'll now try to undo LV creation."
        % (volume_group, cname, last_used_index),
        file=sys.stderr,
    )
    for i in range(last_used_index + 1):
        lv_path = "/dev/%s/%s-vol%s" % (volume_group, cname, i)
        remove_command = "lvremove -y '%s'" % lv_path
        try:
            subprocess.run(
                shlex.split(remove_command), stdout=subprocess.PIPE, check=True
            )
            print(
                "Attempting to remove logical volume '%s'... " "Done!" % lv_path,
                file=sys.stderr,
            )
        except subprocess.CalledProcessError:
            if i == last_used_index:
                print(
                    "Attempting to remove logical volume '%s'... "
                    "Fail! This is the logical volume that just failed "
                    "being created, so it should be fine." % lv_path,
                    file=sys.stderr,
                )
            else:
                print(
                    "Attempting to remove logical volume '%s'... "
                    "Fail! You might have some leftover logical volumes. "
                    "You can check running 'lvdisplay'." % lv_path,
                    file=sys.stderr,
                )
    lxc_profile_name = "%s-profile" % cname
    try:
        subprocess.run(
            shlex.split("lxc profile delete %s" % lxc_profile_name),
            stdout=subprocess.PIPE,
            check=True,
        )
        print(
            "Attempting to delete lxc profile '%s'... Done!" % lxc_profile_name,
            file=sys.stderr,
        )
    except subprocess.CalledProcessError:
        print(
            "Attempting to delete lxc profile '%s'... Fail!" % lxc_profile_name,
            file=sys.stderr,
        )
    sys.exit(1)


CNAME = sys.argv[1]
VOLUME_GROUP = sys.argv[2]
try:
    DRIVE_SIZE = sys.argv[3]
except IndexError:
    DRIVE_SIZE = "10G"
try:
    DRIVE_COUNT = int(sys.argv[4])
except (IndexError, TypeError):
    DRIVE_COUNT = 8

dev_numbers = {}

single_drive_section = """
  disk%d:
    path: /dev/sd%s
    major: %s
    minor: %s
    type: unix-block
""".strip(
    "\n"
)

template_drive_sections = []

for i in range(DRIVE_COUNT):
    drive_letter = chr(ord("b") + i)
    create_command = "lvcreate -y --size %s --name '%s-vol%s' %s" % (
        DRIVE_SIZE,
        CNAME,
        i,
        VOLUME_GROUP,
    )
    try:
        print(
            "Running lvcreate on iteration #{}: {}".format(i, create_command),
            file=sys.stderr,
        )
        p = subprocess.run(
            shlex.split(create_command), stdout=subprocess.PIPE, check=True
        )
    except subprocess.CalledProcessError:
        undo_lv_and_exit(i, CNAME, VOLUME_GROUP)
    display_command = "lvdisplay '/dev/%s/%s-vol%s'" % (VOLUME_GROUP, CNAME, i)
    p = subprocess.run(shlex.split(display_command), stdout=subprocess.PIPE)
    for line in p.stdout.decode().split("\n"):
        if "Block device" in line:
            maj_min = line.split()[2].strip()
            major, minor = maj_min.split(":")
            drive = single_drive_section % (i, drive_letter, major, minor)
            template_drive_sections.append(drive)

path_to_repo = os.path.dirname(os.path.realpath(__file__))

template_vars = {}
template_vars.update(dev_numbers)
template_vars["drive_sections"] = "\n".join(template_drive_sections)

template_file = path_to_repo + "/container_base/swift-runway-v1.tmpl"
raw = open(template_file).read()
formatted = raw.format(name="%s-profile" % CNAME, **template_vars)
print(formatted)
