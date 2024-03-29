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
Callbacks to manage the engine when a new file is loaded in shotgun.

"""
import os
import sys
import traceback
import sgtk

# application libs
from pyfbsdk import FBMessageBox
from pyfbsdk import FBMenuManager

# local libs
from .menu_generation import MenuGenerator


def __show_sgtk_disabled_message(details):
    """
    Message when user clicks the shotgun is disabled menu
    """
    msg = (
        "PTR integration is currently disabled because the file you "
        "have opened is not recognized - PTR cannot "
        "determine which Context the currently open file belongs to. "
        "In order to enable the PTR functionality, try opening another "
        "file. <br><br><i>Details:</i> %s" % details
    )
    FBMessageBox("PTR Error", msg, "OK")


def __create_sgtk_disabled_menu(details):
    """
    Creates a std "disabled" Shotgun menu
    """
    menu_mgr = FBMenuManager()
    menu = menu_mgr.GetMenu("Flow Production Tracking")
    if not menu:
        menu_mgr.InsertBefore(None, "Help", "Flow Production Tracking")
        menu = menu_mgr.GetMenu("Flow Production Tracking")
    menu.InsertLast("Sgtk is disabled.", 1)

    def menu_event(control, event):
        __show_sgtk_disabled_message(details)

    menu.OnMenuActivate.Add(menu_event)


def __create_sgtk_error_menu():
    """
    Creates a std "error" shotgun menu and grabs the current context.
    Make sure that this is called from inside an except clause.
    """
    (exc_type, exc_value, exc_traceback) = sys.exc_info()
    message = ""
    message += "Message: There was a problem starting the Engine.\n"
    message += "Please contact %s\n\n" % sgtk.support_url
    message += "Exception: %s - %s\n" % (exc_type, exc_value)
    message += "Traceback (most recent call last):\n"
    message += "\n".join(traceback.format_tb(exc_traceback))

    menu_mgr = FBMenuManager()
    menu = menu_mgr.GetMenu("Flow Production Tracking")
    if not menu:
        menu_mgr.InsertBefore(None, "Help", "Flow Production Tracking")
        menu = menu_mgr.GetMenu("Flow Production Tracking")
    menu.InsertLast("[PTR Error - Click for details]", 1)

    def menu_event(control, event):
        FBMessageBox("PTR Error", message, "OK")

    menu.OnMenuActivate.Add(menu_event)


def __engine_refresh(tk, new_context):
    """
    Checks the the Shotgun engine should be
    """

    engine_name = os.environ.get("TANK_MOTIONBUILDER_ENGINE_INIT_NAME")

    curr_engine = sgtk.platform.current_engine()
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
        sgtk.platform.start_engine(engine_name, tk, new_context)
    except sgtk.TankEngineInitError as e:
        # context was not sufficient! - disable tank!
        __create_sgtk_disabled_menu(e)
