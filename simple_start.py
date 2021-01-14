#!/usr/bin/env python3

#
#Copyright (c) 2016-2021, NVIDIA CORPORATION.
#SPDX-License-Identifier: Apache-2.0

# simple start for setting up a new workspace and starting a guest
# All options come from the manifest; there are no options for this tool

import sys
import os
from shutil import copyfile

from libs.manifest import Manifest
from libs import workspaces
from libs import colorprint
from libs.cli import run_command
import setup_and_run_ansible_on_guest

if __name__ == '__main__':
    usage = '%s manifest_file' % sys.argv[0]

    try:
        manifest_path = os.path.abspath(sys.argv[1])
    except IndexError:
        print('Usage: %s' % usage)
        sys.exit(1)

    if os.geteuid() != 0:
        print("This script must be run as root.")
        sys.exit(1)

    RUNWAY_DIR = os.path.abspath(os.path.dirname(__file__))

    # need to parse the manifest file first to get the runway options (family)
    man = Manifest(manifest_path, None)

    # create workspace dir from runway_options['family']
    workspaces.WORKSPACE_PREFIX += '%s-' % man.runway_options['family']
    workspace_name = workspaces.get_new_workspace_name()
    workspace_path = workspaces.create_workspace_dir(workspace_name)
    man.workspace_dir = workspace_path

    # get manifest components into workspace
    man.retrieve_components()

    # get a copy of the manifest into the workspace directory
    copyfile(manifest_path, os.path.join(workspace_path, 'manifest.cfg'))

    # make guest etc etc
    container_name = workspace_name

    try:
        vol_size = man.get_config_option('drive_size')
        base_image = 'runway-base-%s' % man.get_config_option('family')
        debug = man.get_config_option('debug')
        debug_string = " --debug" if debug else ""
        vol_count = int(man.get_config_option('drive_count'))
        distro = man.runway_options.get('distro', 'ubuntu')
        tiny_deploy = man.get_config_option('tiny')
        no_install = tiny_deploy or \
            man.get_config_option('no_install')
        no_snap = no_install or \
            man.get_config_option('no_snapshot')

        # starting from a base image doesn't work if the base image
        # has fewer drives than the current manifest you're loading
        run_command("./make_base_container.py "
                    "{} {} {} {} {}".format(distro, container_name, vol_size,
                                              vol_count, base_image),
                    RUNWAY_DIR)

        setup_and_run_ansible_on_guest.setup_and_run_ansible(
            container_name, debug=debug, drive_count=vol_count,
            tiny_install=tiny_deploy)

        if not no_install:
            run_command("./generic_installer.py {}".format(container_name),
                        RUNWAY_DIR)
        if not no_snap:
            run_command("./snapshot_created_container.sh "
                        "{} {}{}".format(
                            container_name, base_image, debug_string),
                        RUNWAY_DIR)
    except Exception as e:
        colorprint.error(str(e))
        sys.exit(1)

    colorprint.success("Container '{}' successfully "
                       "created.\n".format(container_name))
