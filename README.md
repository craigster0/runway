Runway
======

Runway is a project to help you take flight with OpenStack Swift. It sets up a
swift-all-in-one (SAIO) dev environment in an lxd container.

This project has three target use cases:
 - Developers looking to contribute code to any of the constituent projects
 - Developers looking for an API test target against which to write apps
 - Something easily consumable for CI to integrate into a QA process


Requirements
------------

In order to create a Runway container, you need a host that satisfies the
following requirements:

- Run on Ubuntu 18.04.
- Have an lvm volume group named `swift-runway-vg01`.
- LXD version 3.0 or higher is installed.
- Python 3

We anticipate that some developers' development environments won't meet these
requirements by default. Runway additionally provides an easy way to create a
VirtualBox VM that will meet them.

If you do want to create the containers inside the Runway-provided VM, your
development environment must satisfy these requirements:

- VirtualBox version 5.2.8 or higher is installed.
- Vagrant version 2.1.2 or higher is installed.
- Python 3


Manifests
---------

Runway is meant to be used to run OpenStack Swift, but besides that, not
everybody has the same needs. For instance, if you want to work on ProxyFS,
there are several additional repos that you will need to clone.  Runway uses
Manifest files to allow users to customize Runway for their needs.

You can read all the details on how to create a new manifest in
[the manifest readme file](https://github.com/swiftstack/runway/blob/master/README_MANIFEST.md),
but all most users will need to know is which manifest file to use.

You can create your own manifests, but we've provided some sample manifests in
the `manifests` directory that you can use:

- `default_manifest.cfg`: if you don't specify a manifest, this is the one that
will be used. It loads Swift, liberasurecode and python-swiftclient.
- `proxyfs_manifest.cfg`: in addition to everything included in the default
manifest, this manifest includes ProxyFS, swift3, and some settings optimized
for ProxyFS.
- `saio_manifest.cfg`: manifest for running Swift, optimized for SAIO
development, with 8 10GB drives.
- `tiny_manifest.cfg`: manifest for running Swift, optimized for an app test
target, with 1 1GB drive.


Get Runway
----------

All you need to do to get a copy of Runway is cloning the repo with Git. Open a
terminal, `cd` into the directory where you want to keep everything related to
Runway and run the following command:

```bash
git clone git@github.com:swiftstack/runway.git
```


Quick install
-------------

We provide a set of utilities that will get you up and running with almost no
work on your side. In this guide, we will use a VM as the host for all the
containers.

On the terminal run the following commands:

```bash
cd <your-runway-path>
bin/build_vm_and_container.py -m <path-to-manifest-file>
```
_NOTE: bin/build_vm_and_container.py will try to update your ubuntu/xenial64
box every time. If you don't want to update it, you can use the
`-u` / `--do_not_update_box` option and it will skip this step._

If everything goes as planned, `build_vm_and_container.py` should take quite
some time to finish (15-20 minutes).

There's a good chance your SCSI controller name is different than our default
one ("SCSI"). If `vagrant up` fails on your system because of your SCSI
controller name being different than our default, open your VirtualBox GUI,
select the "runway" VM, and go to Settings > Storage. Under "Storage Tree", you
should see an IDE controller and an SCSI controller. If you see something like
"Controller: SCSIController", then your controller name is "SCSIController".

If your SCSI controller was not properly set up during the first run, run the
following commands:

```bash
bin/cleanup_runway.sh
CONTROLLER_NAME=<your-controller-name> bin/build_vm_and_container.py -m <path-to-manifest-file>
```

### Specifying your container distro ###

When you build your VM and container, you have the option to specify what
distro will be used on your container:

```bash
cd <your-runway-path>
bin/build_vm_and_container.py -m <path-to-manifest-file> -d <distro>
```

The currently supported options are:
- `ss-centos7.5` (default): CentOS 7.5. A copy of LXD's
`images:centos/7/amd64`, hosted by SwiftStack, will be used. As opposite to
regular `images:centos/7/amd64`, this image will always be pinned to
CentOS 7.5.
- `rhel`: CentOS 7. LXD's `images:centos/7/amd64` image will be used. At the
time of this writing, it's CentOS 7.5, but it will most probably change once
new versions of the operating system are released.
- `ubuntu`: Ubuntu 16.04. LXD's `ubuntu:16.04` image will be used.


Using your container
--------------------

This is how you log into your new container:

```bash
bin/bash_on_current_container.sh
```


Startup script for ProxyFS containers
--------------------------------------

Once you're in the container, the first thing you'll probably want to do is
start Swift, ProxyFS, all of the related services and mount an SMB mount point
and/or an NFS mount point:

```bash
sudo start_and_mount_pfs
```

Running the command above without any extra arguments will mount an SMB mount
point at `/mnt/smb_proxyfs_mount` using protocol version `3.0` and an NFS mount
point at `/mnt/nfs_proxyfs_mount` using protocol version `3`.

If you only need one type of mount point or if you want a specific version of a
protocol, you can specify it when running the script. Here's a complete list
with all the options:

- `all` (default option): mount an SMB mount
point at `/mnt/smb_proxyfs_mount` using protocol version `3.0` and an NFS mount
point at `/mnt/nfs_proxyfs_mount` using protocol version `3`.
- `smb`/`smb3`: mount an SMB mount point at `/mnt/smb_proxyfs_mount` using
protocol version `3.0`.
- `smb1`: mount an SMB mount point at `/mnt/smb_proxyfs_mount` using protocol
version `1.0`.
- `smb2`: mount an SMB mount point at `/mnt/smb_proxyfs_mount` using protocol
version `2.1`.
- `nfs`: mount an NFS mount point at `/mnt/nfs_proxyfs_mount` using protocol
version `3`.

Usage example:

```bash
sudo start_and_mount_pfs smb2
```

_NOTE: running `start_and_mount_pfs` again will unmount all the mount points,
stop all the services in the appropriate order and then start and mount again._


Other handy commands to build and manage ProxyFS
------------------------------------------------

Unmount your mount points and stop all the services related to ProxyFS:

```bash
sudo unmount_and_stop_pfs
```

Re-build ProxyFS:

```bash
cdpfs
make
```

Install/re-build pfs_middleware. You will need it if you add new .py files to
the middleware:

```bash
cdpfs
cd pfs_middleware
python setup.py develop
```

Install/re-build meta_middleware. You will need it if you add new .py files to
the middleware:

```bash
cdpfs
cd meta_middleware
python setup.py develop
```


Update your components
----------------------

You could manually update all your components using Git, but the more
components you have the more tedious it gets. Runway provides a handy way to
update all the components on your manifest with a single command. Additionally,
it updates all your components' submodules in case they exist. From your runway
directory on your host, run:

```bash
bin/setup_guest_workspace.py -w <your-container-name>
```

In case the container you specify doesn't exist, the script will just create a
workspace in your `guest_workspaces` directory with all the components from the
default manifest.

Also, remember to periodically check for updates on Runway's code. From your
Runway directory, run:

```bash
git pull
```


Cleanup your environment
------------------------

At any given point, you might want to destroy your environment and re-create it
from scratch. The are 2 ways to do it:

**Delete all your containers and your VM, but keep your code/components:**

```bash
vagrant destroy
```

After this, you can re-create your environment just by running:

```bash
bin/build_vm_and_container.py -w <your-workspace-name>
```
_NOTE: Your container name will typically be something like `swift-runway-XXX`,
where `XXX` is a number between 001 and 999 (usually 001). To check your
container name, you can run `lxc list` inside your VM (second step in the list
above)._


**Delete all your containers, your VM and all your code/components:**

```bash
bin/cleanup_runway.sh
```
_**WARNING**: running the command above will delete all the code from all your
components in ALL your workspaces. Please, double-check you don't have any
unsaved/uncommitted work before your run it._

After this, you can re-create your environment by following all the steps in
section "Quick install".


How to use Runway without a VM
------------------------------

Use `bin/setup_guest_workspace.py` together with a manifest file (read
`README_MANIFEST.md` for further details) to get your components or manually
clone the appropriate code repos into `guest_workspaces/<your-workspace-name>`
directory by hand. Your workspace directory will be shared with your container.
This allows for easily having different versions of the source running
at the same time in different guest containers.

Start with `start.py`. A typical usage example would be:

```bash
start.py -d RHEL -v 1G
```

If you don't specify -d option, Ubuntu will be used by default. You can check
all the available options by running:

```bash
start.py -h
```

You can also run a streamlined version like this:

```bash
simple_start.py <path-to-manifest-file>
```


Clean everything up with `delete_all_runway_containers.py`. Because of the lvm
commands, these need to be run as root.

Project plans:
 - refactor to use many containers instead of an all-in-one container
 - allow the host to be something other than Ubuntu 16.04
