#!/usr/bin/env python

import argparse
import datetime
import os
import sys
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '..')))

from libs import colorprint
from libs import workspaces
from libs.cli import run_command
from libs.manifest import Manifest

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
RUNWAY_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
BIN_DIR = os.path.abspath(os.path.join(RUNWAY_DIR, 'bin'))
SETUP_WORKSPACE_SCRIPT = 'setup_guest_workspace.py'
VAGRANT_BOX_NAME = "ubuntu/bionic64"
DEFAULT_CONTAINER_DISTRO = "ss-centos7.5"


def exit_on_error(error_text):
    colorprint.error(error_text)
    colorprint.error("\nIf you want to cleanup your runway installation, run "
                     "'{}'".format(os.path.join(RUNWAY_DIR, 'bin',
                                                'cleanup_runway.sh')))
    sys.exit(1)


def get_manifest(workspace_name):
    if workspace_name is None:
        exit_on_error("No workspace found.")
    workspace_path = workspaces.get_workspace_path(workspace_name)
    manifest_path = workspaces.get_manifest_path(workspace_name)
    try:
        return Manifest(manifest_path, workspace_path)
    except Exception as e:
        exit_on_error(e.message)


def vol_size_in_mebibytes(size_str):
    try:
        return int(size_str) / 1024 / 1024
    except Exception:
        pass

    if size_str.endswith("T"):
        return int(size_str[:-1]) * 1024 * 1024
    if size_str.endswith("G"):
        return int(size_str[:-1]) * 1024
    if size_str.endswith("M"):
        return int(size_str[:-1])
    if size_str.endswith("K"):
        return int(size_str[:-1]) / 1024
    if size_str.endswith("B"):
        return int(size_str[:-1]) / 1024 / 1024


def elapsed_time_string(sec_elapsed):
    rounded_seconds = int(round(sec_elapsed))
    h = int(rounded_seconds / (60 * 60))
    m = int((rounded_seconds % (60 * 60)) / 60)
    s = rounded_seconds % 60
    if h > 0:
        return "{} hour{}, {} minute{}, {} second{}".format(
            h, "" if h == 1 else "s",
            m, "" if m == 1 else "s",
            s, "" if s == 1 else "s")
    elif m > 0:
        return "{} minute{}, {} second{}".format(
            m, "" if m == 1 else "s",
            s, "" if s == 1 else "s")
    else:
        return "{} second{}".format(s, "" if s == 1 else "s")


if __name__ == "__main__":
    start_time = time.time()

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--container-name', default=None,
                        help="Container name. Default: the name of the "
                             "workspace")
    parser.add_argument('-d', '--distro', default=DEFAULT_CONTAINER_DISTRO,
                        help="Container distro (not the VM's). Default: "
                             "{}".format(DEFAULT_CONTAINER_DISTRO))
    parser.add_argument('-m', '--manifest', default=None,
                        help="Path to manifest file. Run '{}/{} -h' to check "
                             "the default manifest "
                             "file.".format(BIN_DIR, SETUP_WORKSPACE_SCRIPT))
    parser.add_argument('-w', '--workspace', default=None,
                        help="Workspace name")

    args = parser.parse_args()
    container_name = args.container_name
    distro = args.distro
    manifest_file = os.path.abspath(args.manifest) \
        if args.manifest is not None else None
    workspace_name = args.workspace

    # Setup workspace
    cmd = "./{}".format(SETUP_WORKSPACE_SCRIPT)
    if manifest_file is not None:
        cmd += " -m {}".format(manifest_file)
    if workspace_name is not None:
        cmd += " -w {}".format(workspace_name)
    run_command(cmd, cwd=BIN_DIR)

    # We need to know the number of drives and the drive size in order to
    # create a Virtual Disk large enough for 2 containers when creating the VM
    if workspace_name is None:
        workspace_name = workspaces.get_last_workspace_name()
        provided_workspace_name = False
    else:
        provided_workspace_name = True
    manifest = get_manifest(workspace_name)

    vol_size = manifest.get_config_option("drive_size")
    vol_count = int(manifest.get_config_option('drive_count'))

    # Vagrant up
    if os.environ.get('CONTROLLER_NAME') is None:
        colorprint.warning("WARNING: CONTROLLER_NAME env var hasn't been set. "
                           "If you fail to 'vagrant up' your VM, open "
                           "VirtualBox, check the name of your SCSI "
                           "Controller and provide it in the CONTROLLER_NAME "
                           "env var.")
    vagrant_env_vars = {
        'VOL_SIZE': "{}".format(vol_size_in_mebibytes(vol_size)),
        'VOL_COUNT': "{}".format(vol_count),
    }
    try:
        run_command("vagrant up", cwd=RUNWAY_DIR, env=vagrant_env_vars)
        colorprint.success("VM successfully created.")
        colorprint.info("VM needs to be rebooted before container creation.")
        run_command("vagrant reload", cwd=RUNWAY_DIR)
        colorprint.info("Creating container...")
        create_container_cmd = "./create_container.sh -d {}".format(distro)
        if container_name is not None:
            create_container_cmd += " --container-name {}".format(
                container_name)
        if provided_workspace_name:
            create_container_cmd += " --workspace {}".format(workspace_name)
        run_command(create_container_cmd, cwd=BIN_DIR)
    except Exception as e:
        exit_on_error(e.message)

    elapsed_time = time.time() - start_time

    # Log into our brand new container?
    colorprint.success(
        "Your new container is now up and running (after {})! If you want to "
        "log into it, just run the following command from the runway "
        "directory:\n\n"
        "\tbin/bash_on_current_container.sh {}".format(
            elapsed_time_string(elapsed_time),
            workspace_name if container_name is None else container_name))
