#
# Copyright (c) 2012 Shotgun Software, Inc
# ----------------------------------------------------
#

"""
A MotionBuilder engine for Tank.

"""

# tank libs
import tank

# application libs
from PyQt4 import QtGui
from pyfbsdk import FBMenuManager


CONSOLE_OUTPUT_WIDTH = 120

class MotionBuilderEngine(tank.platform.Engine):
    def init_engine(self):
        self.log_debug("%s: Initializing..." % self)

        # now check that there is a location on disk which corresponds to the context
        # for the MotionBuilder engine (because it for example sets the MotionBuilder project)
        if len(self.context.entity_locations) == 0:
            raise tank.TankError("No folders on disk are associated with the current context. The MotionBuilder "
                "engine requires a context which exists on disk in order to run correctly.")

        menu_mgr = FBMenuManager()
        menu = menu_mgr.GetMenu("Tank")
        if not menu:
            menu_mgr.InsertBefore(None, "Help", "Tank")

    def destroy_engine(self):
        self.log_debug('%s: Destroying...' % self)

    def log_debug(self, msg):
        print msg

    def log_info(self, msg):
        print msg

    def log_error(self, msg):
        QtGui.QMessageBox.critical(None, "Tank Error", str(msg))

    def log_warning(self, msg):
        print msg
