# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
A MotionBuilder engine for Shotgun.

"""

import os
import sys
import sgtk
import logging

# application libs
from pyfbsdk import FBMessageBox
from pyfbsdk import FBSystem


# custom exception handler for motion builder
def sgtk_mobu_exception_trap(ex_cls, ex, tb):
    # careful about infinite loops here -
    # MUST NOT RAISE EXCEPTIONS :)

    # assemble message
    error_message = "Could not format error message"
    try:
        import traceback

        tb_str = "\n".join(traceback.format_tb(tb))
        error_message = (
            "A Python Exception was Caught!\n\nDetails: %s\nError Type: %s\n\nTraceback:\n%s"
            % (ex, ex_cls, tb_str)
        )
    except Exception:
        pass

    # now output it
    try:
        from sgtk.util.qt_importer import QtImporter

        qt = QtImporter()
        qt.QtGui.QMessageBox.critical(None, "Python Exception Raised", error_message)
    except:
        try:
            print((str(error_message)))
        except:
            pass


class MotionBuilderEngine(sgtk.platform.Engine):
    @property
    def host_info(self):
        """
        :returns: A dictionary with information about the application hosting this engine.

        The returned dictionary is of the following form on success:

            {
                "name": "Motionbuilder",
                "version": "18000.0",
            }

        and of following form on an error preventing the version identification.

            {
                "name": "Motionbuilder",
                "version: "unknown"
            }
        """
        host_info = {"name": "Motionbuilder", "version": "unknown"}

        try:
            # NOTE: The 'Version' returns a double value
            # we really need the conversion to string.
            host_info["version"] = str(FBSystem().Version)
        except:
            # Fallback to initialized values above
            pass

        return host_info

    @property
    def context_change_allowed(self):
        """
        Whether the engine allows a context change without the need for a restart.
        """
        return True

    def init_engine(self):
        self.logger.debug("%s: Initializing..." % self)

        if self.context.project is None:
            # must have at least a project in the context to even start!
            raise sgtk.TankError(
                "The Motionbuilder engine needs at least a project in the context "
                "in order to start! Your context: %s" % self.context
            )

        # motionbuilder doesn't have good exception handling, so install our own trap
        sys.excepthook = sgtk_mobu_exception_trap

    def post_app_init(self):
        """
        Executes once all apps have been initialized
        """
        # Initialie the SG Toolkit style to the application.
        self._initialize_dark_look_and_feel()
        self._initialize_menu()

    def post_context_change(self, old_context, new_context):
        """
        Handles post-context-change requirements.

        :param old_context: The sgtk.context.Context being switched away from.
        :param new_context: The sgtk.context.Context being switched to.
        """
        self.logger.debug("tk-motionbuilder context changed to %s", str(new_context))
        self._menu_generator.destroy_menu()
        self._initialize_menu()

    def destroy_engine(self):
        """
        Uninitialize engine state
        """
        self.logger.debug("%s: Destroying..." % self)
        self._menu_generator.destroy_menu()

    def _initialize_dark_look_and_feel(self):
        """
        Override the base engine method.
        Apply specific styling for Mobu.
        """

        from sgtk.platform.qt import QtGui

        # Initialize the SG Toolkit style to the application.
        super()._initialize_dark_look_and_feel()

        # Apply Mobu specific styling
        app = QtGui.QApplication.instance()
        app_palette = app.palette()
        # The default placeholder text for Mobu is black, let's set it back to
        # the text color (as it was in Qt5), but with the current placeholder
        # text alpha value.
        new_placeholder_text_color = app_palette.text().color()
        placeholder_text_color = app_palette.placeholderText().color()
        new_placeholder_text_color.setAlpha(placeholder_text_color.alpha())
        app_palette.setColor(QtGui.QPalette.PlaceholderText, new_placeholder_text_color)
        # Set the palette back with the Mobu specific styling
        app.setPalette(app_palette)

    def _get_dialog_parent(self):
        """
        Find the main Motionbuilder window/QWidget.  This
        will be used as the parent for all dialogs created
        by show_modal or show_dialog

        :returns: QWidget if found or None if not
        """
        from sgtk.platform.qt import QtGui

        # get all top level windows:
        top_level_windows = QtGui.QApplication.topLevelWidgets()

        # from this list, find the main application window.
        for w in top_level_windows:
            if (
                type(w) == QtGui.QWidget
                and len(w.windowTitle()) > 0
                and w.parentWidget() is None
            ):
                return w

        return None

    def _initialize_menu(self):
        """
        Creates a new motionbuilder menu
        to reflect currently loaded apps.
        """
        tk_motionbuilder = self.import_module("tk_motionbuilder")
        self._menu_generator = tk_motionbuilder.MenuGenerator(
            self, "Flow Production Tracking"
        )
        self._menu_generator.create_menu()

    def _emit_log_message(self, handler, record):
        """
        Called by the engine to log messages in Mobu script editor.
        All log messages from the toolkit logging namespace will be passed to this method.
        :param handler: Log handler that this message was dispatched from.
                        Its default format is "[levelname basename] message".
        :type handler: :class:`~python.logging.LogHandler`
        :param record: Standard python logging record.
        :type record: :class:`~python.logging.LogRecord`
        """
        # Give a standard format to the message:
        #     Shotgun <basename>: <message>
        # where "basename" is the leaf part of the logging record name,
        # for example "tk-multi-shotgunpanel" or "qt_importer".
        if record.levelno < logging.INFO:
            formatter = logging.Formatter("Debug: PTR %(basename)s: %(message)s")
        else:
            formatter = logging.Formatter("PTR %(basename)s: %(message)s")

        msg = formatter.format(record)

        if record.levelno < logging.ERROR:
            print(msg)
        else:
            # for errors, pop up a modal msgbox
            FBMessageBox("PTR Error", str(msg), "OK")
