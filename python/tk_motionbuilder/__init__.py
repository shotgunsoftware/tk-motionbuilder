"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

Callbacks to manage the engine when a new file is loaded in tank.

"""
import os
import sys
import traceback

#tank libs
import tank

# application libs
from pyfbsdk import FBMessageBox
from pyfbsdk import FBMenuManager

# local libs
from .menu_generation import MenuGenerator


def __show_tank_disabled_message(details):
    """
    Message when user clicks the tank is disabled menu
    """
    msg = ("Tank is currently disabled because the file you "
           "have opened is not recognized by Tank. Tank cannot "
           "determine which Context the currently open file belongs to. "
           "In order to enable the Tank functionality, try opening another "
           "file. <br><br><i>Details:</i> %s" % details)
    FBMessageBox( "Tank Error",  msg, "OK" )

def __create_tank_disabled_menu(details):
    """
    Creates a std "disabled" tank menu
    """
    menu_mgr = FBMenuManager()
    menu = menu_mgr.GetMenu("Tank")
    if not menu:
        menu_mgr.InsertBefore(None, "Help", "Tank")
        menu = menu_mgr.GetMenu("Tank")
    menu.InsertLast("Tank is disabled.", 1)

    def menu_event(control, event):
        __show_tank_disabled_message(details)
    menu.OnMenuActivate.Add(menu_event)


def __create_tank_error_menu():
    """
    Creates a std "error" tank menu and grabs the current context.
    Make sure that this is called from inside an except clause.
    """
    (exc_type, exc_value, exc_traceback) = sys.exc_info()
    message = ""
    message += "Message: There was a problem starting the Tank Engine.\n"
    message += "Please contact tanksupport@shotgunsoftware.com\n\n"
    message += "Exception: %s - %s\n" % (exc_type, exc_value)
    message += "Traceback (most recent call last):\n"
    message += "\n".join( traceback.format_tb(exc_traceback))

    menu_mgr = FBMenuManager()
    menu = menu_mgr.GetMenu("Tank")
    if not menu:
        menu_mgr.InsertBefore(None, "Help", "Tank")
        menu = menu_mgr.GetMenu("Tank")
    menu.InsertLast("[Tank Error - Click for details]", 1)

    def menu_event(control, event):
        FBMessageBox( "Tank Error",  message, "OK" )
    menu.OnMenuActivate.Add(menu_event)


def __engine_refresh(tk, new_context):
    """
    Checks the the tank engine should be
    """

    engine_name = os.environ.get("TANK_MOTIONBUILDER_ENGINE_INIT_NAME")

    curr_engine = tank.platform.current_engine()
    if curr_engine:
        # an old engine is running.
        if new_context == curr_engine.context:
            # no need to restart the engine!
            return
        else:
            # shut down the engine
            curr_engine.destroy()

    # try to create new engine
    try:
        tank.platform.start_engine(engine_name, tk, new_context)
    except tank.TankEngineInitError, e:
        # context was not sufficient! - disable tank!
        __create_tank_disabled_menu(e)


