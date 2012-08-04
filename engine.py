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
from pyfbsdk import FBMessageBox


CONSOLE_OUTPUT_WIDTH = 120

class MotionBuilderEngine(tank.platform.Engine):
    def init_engine(self):
        self.log_debug("%s: Initializing..." % self)

        # now check that there is a location on disk which corresponds to the context
        # for the MotionBuilder engine (because it for example sets the MotionBuilder project)
        if len(self.context.entity_locations) == 0:
            raise tank.TankError("No folders on disk are associated with the current context. The MotionBuilder "
                "engine requires a context which exists on disk in order to run correctly.")

        import tk_motionbuilder
        self._menu_generator = tk_motionbuilder.MenuGenerator(self)
        self._menu_generator.create_menu()

    def destroy_engine(self):
        self.log_debug('%s: Destroying...' % self)
        self._menu_generator.destroy_menu()

    def log_debug(self, msg):
        print msg

    def log_info(self, msg):
        print msg

    def log_error(self, msg):
        FBMessageBox( "Tank Error",  str(msg), "OK" )

    def log_warning(self, msg):
        print msg
