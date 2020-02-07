import os
import re
from six.moves import configparser

from libs import colorprint
from libs.cli import run_command

RUNWAY_CONFIG_SECTION = "runway"
DOWNLOAD_LOG_FILE_NAME = "download.log"
RUNWAY_DEFAULTS = {
    "drive_size": "10G",
    "drive_count": 8,
    "swift": True,
}
BOOLEAN_RUNWAY_OPTIONS = {
    "debug",
    "no_install",
    "no_snapshot",
    "proxyfs",
    "tiny",
    "swift",
}
BOOLEAN_OPTIONS = {"local"}


class Manifest(object):
    sections = []
    components_options = {}
    runway_options = {}

    def __init__(self, config_file, workspace_dir):
        if not os.path.isfile(config_file):
            raise Exception(
                "Error: file {} does not " "exist.".format(config_file)
            )

        config = configparser.ConfigParser()
        config.read(config_file)
        for section in config.sections():
            section_options = self.get_config_options_for_section(
                config, section
            )
            self.validate_config_options_for_section(section_options, section)
            if section == RUNWAY_CONFIG_SECTION:
                self.runway_options = section_options
                self.set_default_runway_options()
            else:
                self.sections.append(section)
                self.components_options[section] = section_options

        self.workspace_dir = workspace_dir

    def set_default_runway_options(self):
        for key, value in RUNWAY_DEFAULTS.items():
            if key not in self.runway_options:
                self.runway_options[key] = value

    def retrieve_components(self):
        logfile_path = os.path.abspath(
            os.path.join(self.workspace_dir, DOWNLOAD_LOG_FILE_NAME)
        )
        for section in self.sections:
            colorprint.info("Getting {}...".format(section), logfile_path)
            section_options = self.components_options[section]
            dest_path = self.get_absolute_dest_path_for_section(section)
            component_exists = os.path.isdir(dest_path)

            # Run any needed command BEFORE cloning
            if not component_exists and "pre_cmd" in section_options:
                run_command(
                    section_options["pre_cmd"],
                    cwd=self.workspace_dir,
                    logfile_path=logfile_path,
                )

            if not section_options["local"]:
                if not component_exists:
                    self.git_clone_component(
                        section, logfile_path=logfile_path
                    )

                # Git checkout + pull in case "sha" or "tag" option is present
                # or if the component directory already existed.
                if (
                    component_exists
                    or "sha" in section_options
                    or "tag" in section_options
                ):
                    self.git_checkout_and_pull_component(
                        section, dest_path, logfile_path=logfile_path
                    )

                self.git_submodule_update(dest_path, logfile_path=logfile_path)
            else:
                if not component_exists:
                    colorprint.warning(
                        "Component '{}' has been marked as "
                        "local, but it doesn't exist. You'll "
                        "most probably want to add it before "
                        "doing anything else.".format(section),
                        logfile_path,
                    )
                else:
                    print("Component '{}' is locally managed.".format(section))

            # Run any needed command AFTER cloning
            if not component_exists and "post_cmd" in section_options:
                run_command(
                    section_options["post_cmd"],
                    cwd=self.workspace_dir,
                    logfile_path=logfile_path,
                )

            # Just print a new line to keep components' output separated
            print("")

    def get_repo_name_from_url(self, url):
        result = re.match("^.+\/(.+)\.git$", url)
        if result is None:
            raise Exception(
                "Couldn't get the name of the repo from url '{}'"
                ".".format(url)
            )
        return result.group(1)

    def get_config_options_for_section(self, config, section):
        config_options = {}

        if section == RUNWAY_CONFIG_SECTION:
            boolean_options_for_current_section = BOOLEAN_RUNWAY_OPTIONS
        else:
            boolean_options_for_current_section = BOOLEAN_OPTIONS

        for (key, value) in config.items(section):
            if key in boolean_options_for_current_section:
                try:
                    config_options[key] = config.getboolean(section, key)
                except ValueError:
                    raise Exception(
                        "Component '{}' has an invalid value for "
                        "boolean option '{}'.\nValid values for "
                        "'true' are: '1', 'yes', 'true', and 'on'."
                        "\nValid values for 'false' are: '0', 'no'"
                        ", 'false', and 'off'.\nThe values are "
                        "case insensitive.".format(section, key)
                    )
            else:
                config_options[key] = value

        for option in boolean_options_for_current_section:
            if option not in config_options:
                config_options[option] = RUNWAY_DEFAULTS.get(option, False)

        return config_options

    def validate_config_options_for_component_section(
        self, config_options, section
    ):
        if (
            sum(
                [
                    "branch" in config_options,
                    "sha" in config_options,
                    "tag" in config_options,
                ]
            )
            > 1
        ):
            raise Exception(
                "Invalid configuration for component '{}': you can"
                " only specify one of these options: branch, sha, "
                "tag.".format(section)
            )
        if config_options["local"] and "dest_path" not in config_options:
            raise Exception(
                "You need to specify a 'dest_path' for local "
                "component '{}'.".format(section)
            )
        if not config_options["local"] and "url" not in config_options:
            raise Exception(
                "URL not found in config for component '{}'"
                ".".format(section)
            )

    def validate_config_options_for_runway_section(self, config_options):
        # There's nothing to validate at the moment
        pass

    def validate_config_options_for_section(self, config_options, section):
        if section == RUNWAY_CONFIG_SECTION:
            self.validate_config_options_for_runway_section(config_options)
        else:
            self.validate_config_options_for_component_section(
                config_options, section
            )

    def get_absolute_dest_path_for_section(self, section):
        return os.path.join(
            self.workspace_dir,
            self.get_relative_dest_path_for_section(section),
        )

    def get_relative_dest_path_for_section(self, section):
        section_options = self.components_options[section]
        if "dest_path" in section_options:
            return section_options["dest_path"]
        else:
            return self.get_repo_name_from_url(section_options["url"])

    def git_clone_component(self, section, logfile_path=None):
        section_options = self.components_options[section]
        git_cmd = "git clone"
        if "branch" in section_options:
            git_cmd += " -b {}".format(section_options["branch"])
        git_cmd += " {}".format(section_options["url"])
        if "dest_path" in section_options:
            dest_path = os.path.join(
                self.workspace_dir, section_options["dest_path"]
            )
            git_cmd += " {}".format(dest_path)

        run_command(git_cmd, cwd=self.workspace_dir, logfile_path=logfile_path)

    def git_checkout_and_pull_component(
        self, section, dest_path, logfile_path=None
    ):
        run_command(
            "git fetch --all --tags", dest_path, logfile_path=logfile_path
        )

        section_options = self.components_options[section]
        git_cmd = "git checkout "
        if "tag" in section_options:
            git_cmd += "tags/{}".format(section_options["tag"])
        elif "sha" in section_options:
            git_cmd += section_options["sha"]
        elif "branch" in section_options:
            git_cmd += section_options["branch"]

        run_command(git_cmd, dest_path, logfile_path=logfile_path)
        if "branch" in section_options:
            run_command("git pull", dest_path, logfile_path=logfile_path)

    def git_submodule_update(self, dest_path, logfile_path=None):
        run_command(
            "git submodule update --init --recursive",
            dest_path,
            logfile_path=logfile_path,
        )

    # Getters for both runway's and components' options

    def get_config_options(self):
        return self.runway_options

    def get_config_option(self, option):
        if option in self.runway_options:
            return self.runway_options[option]
        else:
            return None

    def get_component_options(self, component):
        if component in self.components_options:
            return self.components_options[component]
        else:
            return None

    def get_component_option(self, component, option):
        if (
            component in self.components_options
            and option in self.components_options[component]
        ):
            return self.components_options[component][option]
        else:
            return None

    def get_components(self):
        return self.sections
