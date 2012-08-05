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
        if self.context.entity:
            # context has an entity
            locations = self.tank.paths_from_entity(self.context.entity["type"],
                                                    self.context.entity["id"])
        elif self.context.project:
            # context has a project
            locations = self.tank.paths_from_entity(self.context.project["type"],
                                                    self.context.project["id"])
        else:
            # must have at least a project in the context to even start!
            raise tank.TankError("The nuke engine needs at least a project in the context "
                                 "in order to start! Your context: %s" % self.context)

        # make sure there are folders on disk
        if len(locations) == 0:
            raise tank.TankError("No folders on disk are associated with the current context. The Nuke "
                            "engine requires a context which exists on disk in order to run "
                            "correctly.")

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
