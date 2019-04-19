#!/usr/bin/env python

import os
import subprocess
import sys

from shutil import copy

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
RUNWAY_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
BIN_DIR = os.path.abspath(os.path.join(RUNWAY_DIR, 'bin'))
TMP_FILES_DIR = os.path.abspath(os.path.join(RUNWAY_DIR, 'tmpfiles'))


def _make_tmp_dir():
    try:
        os.mkdir(TMP_FILES_DIR)
    except OSError:
        # Directory already exists. That's fine.
        pass


def _make_tmp_copy(src):
    _make_tmp_dir()
    copy(src, TMP_FILES_DIR)


def _delete_tmp_copy(src):
    os.remove(os.path.join(TMP_FILES_DIR, src))


def push_into_container(container_name, src, dest):
    """
    Function that pushes a file into a container. It's also meant for being
    imported, that's why we're returning an output + success tuple.
    :param container_name: str
    :param src: str
    :param dest: str
    :return: str, bool
    """
    _make_tmp_copy(src)
    cmd = "OPTIONALRUNWAYCNAME=1 QUIET=1 source " \
          "lib/get_container_connection_options.sh && ssh -q -t " \
          "${VAGRANTOPTIONS} ${RUNWAYHOST} lxc file push /vagrant/tmpfiles" \
          "/%s %s%s" % (src, container_name, dest)
    success = True
    try:
        output = subprocess.check_output(cmd, shell=True, cwd=BIN_DIR)
    except subprocess.CalledProcessError as e:
        output = e.output
        output += "\nPushing the file `{}` into the `{}` container failed." \
                  "\n".format(src, container_name)
        output += e.message
        success = False
    _delete_tmp_copy(src)
    return output, success


if __name__ == "__main__":
    usage = 'Usage: %s container_name source_file destination_file' \
            % sys.argv[0]
    if len(sys.argv) != 4:
        print(usage)
        sys.exit(1)

    container_name = sys.argv[1]
    src = sys.argv[2]
    dest = sys.argv[3]

    if not dest.startswith("/"):
        print("Destination path must be an absolute path.")
        sys.exit(1)

    output, success = push_into_container(container_name, src, dest)
    print(output)
    if not success:
        sys.exit(1)
