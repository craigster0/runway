#!/usr/bin/env python3

#
#Copyright (c) 2016-2021, NVIDIA CORPORATION.
#SPDX-License-Identifier: Apache-2.0

import sys
import json

from libs.cli import run_command


def setup_and_run_ansible(cname, debug=False, no_install=False, drive_count=1,
                          tiny_install=False, swift=True, proxyfs=False,
                          workspace_name=None):
    if not workspace_name:
        workspace_name = cname
    if not no_install:
        # get all the guest-executed stuff pushed over
        # lxc file push ./ansible/ $CNAME/root/
        # unfortunately, lxc doesn't support directly pushing a whole directory
        # https://github.com/lxc/lxd/issues/1218
        cmd = 'tar cf - ansible | lxc exec %s -- tar xf - -C /root/' % cname
        run_command(cmd, cwd=sys.path[0], shell=True)

        # install ansible
        cmd = 'lxc exec %s -- /bin/bash /root/ansible/install_ansible.sh%s' \
              % (cname, (' --debug' if debug else ''))
        run_command(cmd)

    def available_mounts():
        total = 0
        for j in range(1, 80):  # drives per server (an arbitrary big number)
            i = 1
            for i in range(1, 5):  # servers per guest
                total += 1
                if total > 8:
                    return
                yield '/srv/%d/node/d%d' % (i, total)

    extra_vars = {'no_install': no_install, 'tiny_install': tiny_install,
                  'proxyfs': proxyfs}
    drive_list = []
    all_mounts = available_mounts()
    for i in range(drive_count):
        drive_letter = 'sd%c' % chr(ord('b') + i)
        mount_point = next(all_mounts)
        x = {'drive_letter': drive_letter,
             'mount_point': mount_point,
            }
        drive_list.append(x)
    extra_vars['drive_list'] = drive_list
    extra_vars = json.dumps(extra_vars)

    # run bootstrap playbook
    # see http://docs.ansible.com/ansible/latest/playbooks_variables.html#passing-variables-on-the-command-line
    # for passing in a list of drives
    cmd = 'lxc exec %s -- ansible-playbook -i "localhost," -c local ' \
          '--extra-vars \'%s\' /root/ansible/bootstrap.yaml' % (cname, extra_vars)
    run_command(cmd, shell=True)

    # create shared code folder
    cmd = 'lxc config device add %(cname)s sharedcomponents disk ' \
          'path=/home/swift/code source=%(dir)s/guest_workspaces/%(workspace)s' \
          % {'cname': cname, 'dir': sys.path[0], 'workspace': workspace_name}
    run_command(cmd, cwd=sys.path[0])

    # install
    if not no_install:
        if swift:
            cmd = 'lxc exec %s -- ansible-playbook -i "localhost," -c local --extra-vars \'%s\' ' \
                  '/root/ansible/master_playbook.yaml' % (cname, extra_vars)
            run_command(cmd)


def main():
    cname = sys.argv[1]
    debug = '--debug' in sys.argv
    no_install = '--no-install' in sys.argv

    # TODO
    # We never call this script directly, we just import and call
    # setup_and_run_ansible function. We should clean this up. Otherwise, we
    # need to accept "tiny_mode", "proxyfs" and also (list of drives or number
    # of drives)

    setup_and_run_ansible(cname, debug=debug, no_install=no_install)

if __name__ == '__main__':
    main()
