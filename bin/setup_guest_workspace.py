#!/usr/bin/env python3

import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from libs import colorprint
from libs.workspaces import create_workspace_dir, MANIFEST_COPY_NAME
from libs.manifest import Manifest
from shutil import copyfile

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
RUNWAY_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
MANIFESTS_DIR_NAME = "manifests"
MANIFESTS_DIR = os.path.join(RUNWAY_DIR, MANIFESTS_DIR_NAME, "templates")
DEFAULT_MANIFEST_NAME = "default_manifest.cfg"
DEFAULT_MANIFEST_PATH = os.path.join(MANIFESTS_DIR, DEFAULT_MANIFEST_NAME)


def exit_with_error(error_text):
    colorprint.error(error_text)
    colorprint.error(
        "\nIf you want to cleanup your runway installation, run "
        "'{}'".format(os.path.join(RUNWAY_DIR, "bin", "cleanup_runway.sh"))
    )
    sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m",
        "--manifest",
        default=DEFAULT_MANIFEST_PATH,
        help="Path to manifest file. Default: '{}'".format(DEFAULT_MANIFEST_PATH),
    )
    parser.add_argument("-w", "--workspace", default=None, help="Workspace name")

    args = parser.parse_args()
    manifest_file = os.path.abspath(args.manifest)
    workspace_name = args.workspace

    # Create new workspace directory
    try:
        new_workspace_path = create_workspace_dir(workspace_name)
    except Exception as e:
        exit_with_error(e.message)

    colorprint.info(
        "\nRetrieving components into workspace at '{}'..."
        "\n".format(new_workspace_path)
    )

    # Copy manifest into workspace
    manifest_copy_path = os.path.join(new_workspace_path, MANIFEST_COPY_NAME)
    if not os.path.isfile(manifest_copy_path):
        copyfile(manifest_file, manifest_copy_path)

    # Retrieve contents
    try:
        current_manifest = Manifest(manifest_copy_path, new_workspace_path)
        current_manifest.retrieve_components()
    except Exception as e:
        exit_with_error(e.message)

    colorprint.success(
        "Guest workspace successfully set up at " "'{}'.".format(new_workspace_path)
    )
