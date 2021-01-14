#!/usr/bin/env python3

#
#Copyright (c) 2016-2021, NVIDIA CORPORATION.
#SPDX-License-Identifier: Apache-2.0

# Install every component other than libec, swiftclient, and swift
# If a workspace is found, first we'll try to find an install command. If there
# isn't one, let's try to find a script named install.sh in the root of the
# component.
#
# If we're not using a manifest, stick to the old behavior: try to find a
# script named install.sh at the root of each top-level dir in the workspace.
#
# If any way to install is found, execute it inside the container.


import os
import sys
import subprocess

from libs import colorprint
from libs import workspaces
from libs.cli import run_command
from libs.manifest import Manifest


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
INSTALL_LOG_FILE_NAME = "install.log"


def exit_with_error(error_text, logfile_path):
    colorprint.error(error_text, logfile_path)
    sys.exit(1)


def get_manifest(workspace_name, logfile_path):
    if workspace_name is None:
        workspace_name = workspaces.get_last_workspace_name()
    if workspace_name is None:
        exit_with_error("No workspace found.", logfile_path)
    workspace_path = workspaces.get_workspace_path(workspace_name)
    manifest_path = workspaces.get_manifest_path(workspace_name)
    if not os.path.isfile(manifest_path):
        colorprint.warning("Error: could not find manifest at {}. While it's "
                           "not mandatory, it's highly recommended to use one."
                           " Read 'README_MANIFEST.md' for more "
                           "information.".format(manifest_path), logfile_path)
        return None
    else:
        try:
            return Manifest(manifest_path, workspace_path)
        except Exception as e:
            exit_with_error(e.message, logfile_path)


def get_install_commands(manifest, workspace_path, logfile_path):
    commands = []
    excluded_components = ['swift', 'python-swiftclient', 'liberasurecode']
    if manifest is not None:
        for component in manifest.get_components():
            if component not in excluded_components:
                dest_path = manifest.get_relative_dest_path_for_section(
                    component)
                install_cmd = manifest.get_component_option(component,
                                                            "install")
                if install_cmd is not None:
                    # We add the component to the excluded list to NOT check
                    # for the install.sh script in the next step.
                    excluded_components.append(component)
                    commands.append(os.path.join(dest_path, install_cmd))
                else:
                    install_sh_path = os.path.join(workspace_path, dest_path,
                                                   "install.sh")
                    if os.path.isfile(install_sh_path):
                        commands.append(os.path.join(dest_path, "install.sh"))

    else:
        for entry in os.scandir(workspace_path):
            if entry.is_dir() and entry.name not in excluded_components and \
                    os.path.isfile('{}/{}/install.sh'.format(workspace_path,
                                                             entry.name)):
                commands.append(os.path.join(entry.name, "install.sh"))
    return commands


if __name__ == "__main__":
    container_name = sys.argv[1]
    if len(sys.argv) > 2:
        workspace_name = sys.argv[2]
    else:
        workspace_name = container_name
    workspace_path = workspaces.get_workspace_path(workspace_name)
    logfile_path = os.path.abspath(os.path.join(workspace_path,
                                                INSTALL_LOG_FILE_NAME))
    manifest = get_manifest(workspace_name, logfile_path)

    install_commands = get_install_commands(manifest, workspace_path,
                                            logfile_path)

    for install_command in install_commands:
        cmd = 'lxc exec {} -- /bin/bash /home/swift/code/{}'.format(
            container_name, install_command)
        try:
            run_command(cmd, logfile_path=logfile_path)
        except Exception as e:
            colorprint.error(str(e), logfile_path)
            sys.exit(1)
