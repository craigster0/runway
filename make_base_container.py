#!/usr/bin/env python3

import argparse
import os
import random
import requests
import sys
import tempfile
import uuid

from libs import colorprint
from libs.cli import run_command

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
# assume well-known lvm volume group on host
#   ...later we'll figure out how to make this dynamic
VG_NAME = "swift-runway-vg01"
SWIFTSTACK_IMAGES_PREFIX = "ss-"
SWIFTSTACK_IMAGES_BASE_URL = "https://tellus.swiftstack.com/v1/AUTH_runway/lxd-images"
BACKUP_SWIFTSTACK_IMAGES_BASE_URL = (
    "https://cloud.swiftstack.com/v1/AUTH_runway/lxd-images"
)
IMAGE_MANIFEST_OBJECT_NAME = "manifest.json"
UNIFIED_TARBALL_TYPE = "unified"
SPLIT_TARBALL_TYPE = "split"
TARBALL_TYPES = [UNIFIED_TARBALL_TYPE, SPLIT_TARBALL_TYPE]


def exit_with_error(error_text):
    colorprint.error(error_text)
    sys.exit(1)


def get_default_image(distro):
    if distro.lower() == "rhel":
        return "images:centos/7/amd64"
    else:
        return "ubuntu:16.04"


def is_swiftstack_hosted_image(base_image):
    return base_image.lower().startswith(SWIFTSTACK_IMAGES_PREFIX)


def get_image_manifest(swift_container_name, use_backup_url=False):
    if use_backup_url:
        base_url = BACKUP_SWIFTSTACK_IMAGES_BASE_URL
    else:
        base_url = SWIFTSTACK_IMAGES_BASE_URL

    manifest_obj_url = "{}/{}/{}".format(
        base_url, swift_container_name, IMAGE_MANIFEST_OBJECT_NAME
    )

    try:
        r = requests.get(manifest_obj_url)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        if not use_backup_url:
            print(
                "Could not download container image manifest from its "
                "primary location. Retrying with backup location..."
            )
            return get_image_manifest(swift_container_name, True)
        else:
            raise Exception(
                "Could not download container image manifest from "
                "'{}'.\n{}".format(manifest_obj_url, e)
            )


def is_image_already_imported(fingerprint):
    try:
        run_command("lxc image info {} >/dev/null 2>&1".format(fingerprint), shell=True)
    except Exception:
        return False
    return True


def delete_image_with_alias(alias):
    try:
        run_command("lxc image delete {}".format(alias))
    except Exception:
        pass


def download_unified_image_file(manifest, use_backup_url=False):
    if use_backup_url:
        base_url = BACKUP_SWIFTSTACK_IMAGES_BASE_URL
    else:
        base_url = SWIFTSTACK_IMAGES_BASE_URL

    tarball_url = "{}/{}".format(base_url, manifest["tarball-object"])

    try:
        r = requests.get(tarball_url, stream=True)
        r.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=False) as f:
            file_path = f.name
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
    except Exception as e:
        if not use_backup_url:
            print(
                "Could not download unified image from its primary "
                "location. Retrying with backup location..."
            )
            return download_unified_image_file(manifest, True)
        else:
            raise Exception(
                "Could not download file from '{}': {}".format(tarball_url, e)
            )

    return file_path


def import_unified_image(manifest, alias):
    tarball_path = download_unified_image_file(manifest)
    # There might be an older image with the same alias
    delete_image_with_alias(alias)
    run_command("lxc image import {} --alias {}".format(tarball_path, alias))
    os.unlink(tarball_path)


def download_split_image_files(manifest, use_backup_url=False):
    if use_backup_url:
        base_url = BACKUP_SWIFTSTACK_IMAGES_BASE_URL
    else:
        base_url = SWIFTSTACK_IMAGES_BASE_URL

    metadata_tarball_url = "{}/{}".format(base_url, manifest["metadata-object"])
    rootfs_tarball_url = "{}/{}".format(base_url, manifest["rootfs-object"])
    file_paths = []

    for url in [metadata_tarball_url, rootfs_tarball_url]:
        try:
            r = requests.get(url, stream=True)
            r.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False) as f:
                file_paths.append(f.name)
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
        except Exception as e:
            if not use_backup_url:
                print(
                    "Could not download split image from its primary "
                    "location. Retrying with backup location..."
                )
                return download_split_image_files(manifest, True)
            else:
                raise Exception(
                    "Could not download file from '{}': {}".format(url, e)
                )

    return tuple(file_paths)


def import_split_image(manifest, alias):
    metadata_tarball_path, rootfs_tarball_path = download_split_image_files(manifest)
    # There might be an older image with the same alias
    delete_image_with_alias(alias)
    run_command(
        "lxc image import {} {} --alias {}".format(
            metadata_tarball_path, rootfs_tarball_path, alias
        )
    )
    os.unlink(metadata_tarball_path)
    os.unlink(rootfs_tarball_path)


def import_image(manifest, alias):
    """
    There are 2 possible image formats: unified and split. We support both.

    For unified format, the manifest will look like this:

    {
        "tarball_type": "unified",
        "fingerprint": "629d2c18b7bb0b52b80dfe62ae309937123d05b563ef057233e7802c9e18c018",
        "tarball-object": "centos7.5/629d2c18b7bb0b52b80dfe62ae309937123d05b563ef057233e7802c9e18c018.tar.gz"
    }

    For split format, the manifest will look like this:

    {
        "tarball_type": "split",
        "fingerprint": "22abbefe0c68943f264a7139c7a699a0b2adfbcf46fc661d2e89b1232301a5de",
        "metadata-object": "centos7.5/meta-22abbefe0c68943f264a7139c7a699a0b2adfbcf46fc661d2e89b1232301a5de.tar.xz",
        "rootfs-object": "centos7.5/22abbefe0c68943f264a7139c7a699a0b2adfbcf46fc661d2e89b1232301a5de.squashfs"
    }
    """

    if manifest["tarball_type"] not in TARBALL_TYPES:
        raise Exception("Invalid tarball type: {}".format(manifest["tarball_type"]))
    elif manifest["tarball_type"] == UNIFIED_TARBALL_TYPE:
        import_unified_image(manifest, alias)
    elif manifest["tarball_type"] == SPLIT_TARBALL_TYPE:
        import_split_image(manifest, alias)
    else:
        raise Exception(
            "Tarball type '{}' is valid, but a method to import "
            "it has not been implemented yet."
        )


def import_image_if_needed(base_image):
    if not is_swiftstack_hosted_image(base_image):
        raise Exception("{} is not an image hosted by SwiftStack".format(base_image))

    swift_container_name = base_image[len(SWIFTSTACK_IMAGES_PREFIX) :]
    manifest = get_image_manifest(swift_container_name)
    if not is_image_already_imported(manifest["fingerprint"]):
        print("Importing image '{}'...".format(base_image))
        import_image(manifest, base_image)
    else:
        print("Image '{}' is already imported".format(base_image))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("distro", type=str, help="Container distro")
    parser.add_argument("cname", metavar="containername", help="Container name")
    parser.add_argument("volsize", help="Volume size")
    parser.add_argument("volcount", type=int, help="Volume count")
    parser.add_argument(
        "baseimage",
        nargs="?",
        help="Base image. Defaults: 'images:centos/7/amd64' "
        "for RHEL distro, 'ubuntu:16.04' otherwise",
    )

    args = parser.parse_args()
    distro = args.distro
    container_name = args.cname
    base_image = args.baseimage
    volume_size = args.volsize
    volume_count = args.volcount

    if is_swiftstack_hosted_image(distro):
        import_image_if_needed(distro)
        default_image = distro
    else:
        default_image = get_default_image(distro)

    if base_image is None:
        base_image = default_image

    try:
        # make a container profile that maps 8 block devices to the guest
        rand_file_name = str(uuid.UUID(int=random.getrandbits(128)))
        run_command(
            "./make_lxc_profile.py {} {} {} {} > "
            "/tmp/{}".format(
                container_name, VG_NAME, volume_size, volume_count, rand_file_name
            ),
            cwd=SCRIPT_DIR,
            shell=True,
        )
        run_command("lxc profile create {}-profile".format(container_name))
        run_command(
            "cat /tmp/{} | lxc profile edit {}-profile".format(
                rand_file_name, container_name
            ),
            cwd=SCRIPT_DIR,
            shell=True,
        )

        # launch the new container
        print("Trying to launch container from base image {}".format(base_image))
        run_command(
            "lxc launch {} {} -p {}-profile || "
            "lxc launch {} {} -p {}-profile".format(
                base_image,
                container_name,
                container_name,
                default_image,
                container_name,
                container_name,
            ),
            shell=True,
        )
    except Exception as e:
        exit_with_error(str(e))
