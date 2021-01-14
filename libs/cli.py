#
#Copyright (c) 2016-2021, NVIDIA CORPORATION.
#SPDX-License-Identifier: Apache-2.0

import datetime
import os
import re
import shlex
import subprocess
import sys
from subprocess import CalledProcessError


def extract_env_vars(cmd):
    env_vars = {}
    matches = re.split("(\S+=\S+) ", cmd)
    remaining_matches = list(matches)
    for match in matches:
        stripped_match = match.strip()
        if stripped_match != "":
            if match.find(" ") > -1 or match.find("=") < 0:
                break
            else:
                split_match = stripped_match.split("=")
                env_vars[split_match[0]] = split_match[1]
        remaining_matches.pop(0)
    remainder = "".join(remaining_matches)
    return env_vars if len(env_vars) > 0 else None, remainder


def native_string(s):
    if sys.version_info[0] < 3:
        return s
    return s.decode("utf-8")


def print_and_log(text, logfile_path):
    print(text)
    log(text, logfile_path)


def log(text, logfile_path):
    if logfile_path is not None:
        with open(logfile_path, "a") as logfile:
            logfile.write(
                "[{}] {}\n".format(
                    datetime.datetime.now().strftime("%F %H:%M:%S"), text
                )
            )


def print_remaining_process_output(p, logfile_path=None):
    remaining_output = native_string(p.stdout.read()).strip()
    if remaining_output != "":
        print_and_log(native_string(p.stdout.read()), logfile_path)


def run_command(cmd, cwd=None, logfile_path=None, shell=False, env=None):
    # TODO: when a script uses run_command to call another script that also
    # uses run_command, weird output formatting is shown. Fix it!
    # Eg: bin/build_vm_and_container.py calling start.py
    envs_for_popen = os.environ.copy()
    if env is not None:
        envs_for_popen.update(env)
    if cwd is not None:
        print_and_log("$ cd {}".format(cwd), logfile_path)
    env_vars, stripped_cmd = None, cmd  # extract_env_vars(cmd)
    if env_vars is not None:
        envs_for_popen.update(env_vars)
    if shell:
        parsed_cmd = stripped_cmd
    else:
        parsed_cmd = shlex.split(stripped_cmd)
    print_and_log("$ {}".format(parsed_cmd), logfile_path)
    p = None
    try:
        p = subprocess.Popen(
            parsed_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=cwd,
            env=envs_for_popen,
            bufsize=1,
            shell=shell,
        )
        while p.poll() is None:
            # This blocks until it receives a newline:
            line = native_string(p.stdout.readline())
            print_and_log(line.rstrip(), logfile_path)
        print_remaining_process_output(p, logfile_path=logfile_path)
        exit_code = p.wait()
        if exit_code != 0:
            raise LoggedException(
                "Command '{}' responded with a non-zero exit status ({}).\n"
                "An error for this command might have been printed above "
                "these lines. Please read the output in order to check what "
                "went wrong.".format(parsed_cmd, exit_code),
                logfile_path,
            )
    except CalledProcessError as e:
        if p:
            print_remaining_process_output(p, logfile_path=logfile_path)
        raise LoggedException(
            "Error running '{}':\n{}\n{}".format(parsed_cmd, e.output, str(e)),
            logfile_path,
        )
    except LoggedException:
        if p:
            print_remaining_process_output(p, logfile_path=logfile_path)
        raise
    except Exception as e:
        if p:
            print_remaining_process_output(p, logfile_path=logfile_path)
        raise LoggedException(
            "Error running '{}':\n{}".format(cmd, str(e)), logfile_path
        )


class LoggedException(Exception):
    def __init__(self, message, logfile_path, *args, **kwargs):
        super(LoggedException, self).__init__(message, *args, **kwargs)
        log(str(self), logfile_path)
