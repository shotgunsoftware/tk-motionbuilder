#
# Copyright (c) 2012 Shotgun Software, Inc
# ----------------------------------------------------
#

"""
A MotionBuilder engine for Tank.

"""

import os
import sys

# tank libs
import tank

# application libs
from pyfbsdk import FBMessageBox



# custom exception handler for motion builder
def tank_mobu_exception_trap(ex_cls, ex, tb):
    # careful about infinite loops here - 
    # MUST NOT RAISE EXCEPTIONS :)
    
    # assemble message
    error_message = "Could not format error message"
    try:
        import traceback
        tb_str = "\n".join(traceback.format_tb(tb))
        error_message = "A Python Exception was Caught!\n\nDetails: %s\nError Type: %s\n\nTraceback:\n%s" % (ex, ex_cls, tb_str)
    except:
        pass

    # now output it    
    try:
        from PySide import QtGui
        QtGui.QMessageBox.critical(None, "Python Exception Raised", error_message)
    except:
        try:
            print str(error_message)
        except:
            pass
        





class MotionBuilderEngine(tank.platform.Engine):
    
    def init_engine(self):
        self.log_debug("%s: Initializing..." % self)

        # now check that there is a location on disk which 
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
            raise tank.TankError("The Tank engine needs at least a project in the context "
                                 "in order to start! Your context: %s" % self.context)

        # make sure there are folders on disk
        if len(locations) == 0:
            raise tank.TankError("No folders on disk are associated with the current context. The "
                            "engine requires a context which exists on disk in order to run "
                            "correctly.")

        # import pyside QT UI libraries
        self._init_pyside()

        # motionbuilder doesn't have good exception handling, so install our own trap
        sys.excepthook = tank_mobu_exception_trap


    def _init_pyside(self):
        """
        Handles the pyside init
        """
        
        # first see if pyside is already present - in that case skip!
        try:
            from PySide import QtGui
        except:
            # fine, we don't expect pyside to be present just yet
            self.log_debug("PySide not detected - Tank will add it to the setup now...")
        else:
            # looks like pyside is already working! No need to do anything
            self.log_debug("PySide detected - Tank will use the existing version.")
            return
        
        if sys.platform == "win32":
            pyside_path = os.path.join(self.disk_location, "resources","pyside112_py26_qt470_win64", "python")
            sys.path.append(pyside_path)   
            dll_path = os.path.join(self.disk_location, "resources","pyside112_py26_qt470_win64", "lib")
            path = os.environ.get("PATH", "")
            path += ";%s" % dll_path
            os.environ["PATH"] = path
                     
        else:
            self.log_error("Unknown platform - cannot initialize PySide!")
        
        # now try to import it
        try:
            from PySide import QtCore
        except Exception, e:
            self.log_error("PySide could not be imported! Tank Apps using pyside will not "
                           "operate correctly! Error reported: %s" % e)
        else:
            self.log_debug("Adding support for various image formats via qplugins...")
            plugin_path = os.path.join(self.disk_location, "resources","pyside112_py26_qt470_win64", "qt_plugins")
            QtCore.QCoreApplication.addLibraryPath(plugin_path)


    def post_app_init(self):
        import tk_motionbuilder
        self._menu_generator = tk_motionbuilder.MenuGenerator(self)
        self._menu_generator.create_menu()

    def destroy_engine(self):
        self.log_debug('%s: Destroying...' % self)
        self._menu_generator.destroy_menu()

    def log_debug(self, msg):
        if self.get_setting("debug_logging", False):
            print msg

    def log_info(self, msg):
        print msg

    def log_error(self, msg):
        FBMessageBox( "Tank Error",  str(msg), "OK" )

    def log_warning(self, msg):
        print msg



