import glob
import os
from six.moves import xrange

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
RUNWAY_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
WORKSPACE_DIR = os.path.join(RUNWAY_DIR, "guest_workspaces")
MAXIMUM_WORKSPACE_COUNT = 999
WORKSPACE_PREFIX = "swift-runway-"
MANIFEST_COPY_NAME = "manifest.cfg"


def get_maximum_workspace_index_length():
    return len(str(MAXIMUM_WORKSPACE_COUNT))


def get_last_workspace_name():
    wildcard_expression = os.path.join(WORKSPACE_DIR, "{}".format(WORKSPACE_PREFIX))
    for i in xrange(get_maximum_workspace_index_length()):
        wildcard_expression += "[0-9]"
    current_workspaces = sorted(
        [os.path.basename(name) for name in glob.glob(wildcard_expression)],
        reverse=True,
    )
    if len(current_workspaces) == 0:
        return None
    return current_workspaces[0]


def get_last_workspace_index():
    last_workspace_name = get_last_workspace_name()
    if last_workspace_name is None:
        return None
    last_index = int(last_workspace_name[len(WORKSPACE_PREFIX) :])
    return last_index


def get_new_workspace_name():
    last_index = get_last_workspace_index()
    if last_index is None:
        new_index = 1
    elif last_index < MAXIMUM_WORKSPACE_COUNT:
        new_index = last_index + 1
    else:
        raise Exception(
            "You have reached the maximum workspace index "
            "({}).".format(MAXIMUM_WORKSPACE_COUNT)
        )
    return "{}{:03d}".format(WORKSPACE_PREFIX, new_index)


def create_workspace_dir(workspace_name=None):
    if workspace_name is None:
        # Get name for our new workspace
        user_provided_workspace = False
        workspace_name = get_new_workspace_name()
    else:
        user_provided_workspace = True

    new_workspace_path = os.path.join(WORKSPACE_DIR, workspace_name)
    try:
        os.mkdir(new_workspace_path)
    except OSError as e:
        # If the user provided the workspace name, he might be trying to update
        # it, so it's fine if we get error 17 (File exists).
        if not user_provided_workspace or e.errno != 17:
            raise Exception(
                "Could not create directory '{}': [Errno {}] "
                "{}".format(new_workspace_path, e.errno, e.strerror)
            )

    return new_workspace_path


def get_workspace_path(workspace_name):
    return os.path.abspath(os.path.join(WORKSPACE_DIR, workspace_name))


def get_manifest_path(workspace_name):
    workspace_path = get_workspace_path(workspace_name)
    return os.path.abspath(os.path.join(workspace_path, MANIFEST_COPY_NAME))
