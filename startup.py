# Copyright (c) 2024 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os

import sgtk
import sgtk.platform
import sgtk.platform.framework


class EngineConfigurationError(sgtk.TankError):
    pass


class MotionBuilderLauncher(sgtk.platform.SoftwareLauncher):

    # Named regex strings to insert into the executable template paths when
    # matching against supplied versions and products. Similar to the glob
    # strings, these allow us to alter the regex matching for any of the
    # variable components of the path in one place
    COMPONENT_REGEX_LOOKUP = {
        "version": "[\d.]+",
        "version_back": "[\d.]+",  # backreference to ensure same version
    }

    # This dictionary defines a list of executable template strings for each
    # of the supported operating systems. The templates are used for both
    # globbing and regex matches by replacing the named format placeholders
    # with an appropriate glob or regex string. As Adobe adds modifies the
    # install path on a given OS for a new release, a new template will need
    # to be added here.
    #
    EXECUTABLE_MATCH_TEMPLATES = [
        {
            # C:\Program Files\Autodesk\MotionBuilder 2020\bin\x64\motionbuilder.exe
            "win32": "C:/Program Files/Autodesk/MotionBuilder {version}/bin/x64/motionbuilder.exe",
        },
    ]

    @property
    def minimum_supported_version(self):
        """
        The minimum software version that is supported by the launcher.
        """
        return "2022"

    def prepare_launch(self, exec_path, args, file_to_open=None):
        """
        Prepares an environment to launch MotionBuilder so that will automatically
        load Toolkit after startup.

        :param str exec_path: Path to Maya executable to launch.
        :param str args: Command line arguments as strings.
        :param str file_to_open: (optional) Full path name of a file to open on launch.
        :returns: :class:`sgtk.platform.LaunchInformation` instance
        """

        # determine all environment variables
        required_env = {}

        self.logger.debug(
            "Preparing Maya Launch via Toolkit Classic methodology ..."
        )
        required_env["SGTK_ENGINE"] = self.engine_name
        required_env["SGTK_CONTEXT"] = sgtk.context.serialize(self.context)

        if file_to_open:
            # Add the file name to open to the launch environment
            required_env["SGTK_FILE_TO_OPEN"] = file_to_open

        return sgtk.platform.LaunchInformation(exec_path, args, required_env)

    def scan_software(self):
        """
        Scan the filesystem for all MotionBuilder executables.

        :return: A list of :class:`sgtk.platform.SoftwareVersion` objects.
        """

        self.logger.debug("Scanning for MotionBuilder executables...")

        # use the bundled icon
        icon_path = os.path.join(self.disk_location, "icon_256.png")
        self.logger.debug("Using icon path: %s" % (icon_path,))

        platform = (
            "win32"
            if sgtk.util.is_windows()
            else None
        )

        if platform is None:
            self.logger.debug("MotionBuilder not supported on this platform.")
            return []

        all_sw_versions = []

        for match_template_set in self.EXECUTABLE_MATCH_TEMPLATES:
            for executable_path, tokens in self._glob_and_match(
                match_template_set[platform], self.COMPONENT_REGEX_LOOKUP
            ):
                self.logger.debug(
                    "Processing %s with tokens %s", executable_path, tokens
                )
                # extract the components (default to None if not included). but
                # version is in all templates, so should be there.
                executable_version = tokens.get("version")

                sw_version = sgtk.platform.SoftwareVersion(
                    executable_version, "MotionBuilder", executable_path, icon_path
                )
                supported, reason = self._is_supported(sw_version)
                if supported:
                    all_sw_versions.append(sw_version)
                else:
                    self.logger.debug(reason)

        return all_sw_versions
