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

# tank libs
import tank

# application libs
from pyfbsdk import FBMessageBox
from pyfbsdk import FBSystem



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
        
        if self.context.project is None:
            # must have at least a project in the context to even start!
            raise tank.TankError("The Motionbuilder engine needs at least a project in the context "
                                 "in order to start! Your context: %s" % self.context)

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
            self.log_debug("PySide not detected - it will be added to the setup now...")
        else:
            # looks like pyside is already working! No need to do anything
            self.log_debug("PySide detected - the existing version will be used.")
            return

        pyside_folder = self.__get_pyside_folder();
        
        if sys.platform == "win32":
            pyside_path = os.path.join(self.disk_location, "resources", pyside_folder, "python")
            sys.path.append(pyside_path)   
            dll_path = os.path.join(self.disk_location, "resources", pyside_folder, "lib")
            path = os.environ.get("PATH", "")
            path += ";%s" % dll_path
            os.environ["PATH"] = path
                     
        else:
            self.log_error("Unknown platform - cannot initialize PySide!")
        
        # now try to import it
        try:
            from PySide import QtCore
        except Exception, e:
            self.log_error("PySide could not be imported! Apps using pyside will not "
                           "operate correctly! Error reported: %s" % e)
        else:
            self.log_debug("Adding support for various image formats via qplugins...")
            plugin_path = os.path.join(self.disk_location, "resources", pyside_folder, "qt_plugins")
            QtCore.QCoreApplication.addLibraryPath(plugin_path)
            
    def _get_dialog_parent(self):
        """
        Find the main Motionbuilder window/QWidget.  This
        will be used as the parent for all dialogs created
        by show_modal or show_dialog
        
        :returns: QWidget if found or None if not
        """
        from PySide import QtGui
        
        # get all top level windows:
        top_level_windows = QtGui.QApplication.topLevelWidgets()
        
        # from this list, find the main application window.
        for w in top_level_windows:
            if (type(w) == QtGui.QWidget        # window is always QWidget 
                and len(w.windowTitle()) > 0    # window always has a title/caption
                and w.parentWidget() == None):  # parent widget is always None
                return w
        
        return None

    def __get_pyside_folder(self):
        """
        Get the correct pyside folder name according to the 
        correct Motionbuilder version.

        :returns: String of the correct pyside distribution folder name (not the entire path)
        """
        version = FBSystem().Version
        folder = ''

        # MotionBuilder 2012 and 2013 use a qt compiled with vs2008 (even though mobu 2013 itself is compiled with 2010).
        # Use a dumpbin /headers on MoBu's qtcore4.dll to see which linker version was used, since versioning can
        # easily get confusing.
        if version < 14000:
            folder = "pyside112_py26_qt470_win64_vs2008"
        else:
            folder = "pyside112_py26_qt470_win64_vs2010"

        return folder

    def post_app_init(self):
        # default menu name is Shotgun but this can be overriden
        # in the configuration to be Sgtk in case of conflicts
        menu_name = "Shotgun"
        if self.get_setting("use_sgtk_as_menu_name", False):
            menu_name = "Sgtk"
            
        tk_motionbuilder = self.import_module("tk_motionbuilder")                
        self._menu_generator = tk_motionbuilder.MenuGenerator(self, menu_name)
        self._menu_generator.create_menu()

        try:
            self.log_user_attribute_metric("Motionbuilder version",
                str(FBSystem().Version))
        except:
            # ignore all errors. ex: using a core that doesn't support metrics
            pass

    def destroy_engine(self):
        self.log_debug('%s: Destroying...' % self)
        self._menu_generator.destroy_menu()

    def log_debug(self, msg):
        if self.get_setting("debug_logging", False):
            print msg

    def log_info(self, msg):
        msg = "Shotgun: %s" % msg
        print msg

    def log_error(self, msg):
        FBMessageBox( "Shotgun Error",  str(msg), "OK" )

    def log_warning(self, msg):
        msg = "Shotgun Warning: %s" % msg
        print msg



