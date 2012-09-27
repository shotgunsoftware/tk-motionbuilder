"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

Menu handling for Nuke

"""
import os
import sys
import platform
import webbrowser
import unicodedata

from pyfbsdk import FBMenuManager
from pyfbsdk import FBGenericMenu

class MenuGenerator(object):
    """
    Menu generation functionality for Nuke
    """

    def __init__(self, engine):
        self._engine = engine
        self._dialogs = []
        self.__menu_index = 1
        self._callbacks = {}

    ##########################################################################################
    # public methods

    def create_menu(self):
        """
        Render the entire Tank menu.
        """
        # create main menu
        menu_mgr = FBMenuManager()
        self._menu_handle = menu_mgr.GetMenu("Tank")
        if not self._menu_handle:
            menu_mgr.InsertBefore(None, "Help", "Tank")
            self._menu_handle = menu_mgr.GetMenu("Tank")
        #self._menu_handle.clearMenu()
        self._menu_handle.OnMenuActivate.Add(self.__menu_event)
        # now add the context item on top of the main menu
        self._context_menu = self._add_context_menu()
        #self._menu_handle.addSeparator()

        # now add favourites
        for fav in self._engine.get_setting("menu_favourites"):
            app_instance_name = fav["app_instance"]
            menu_name = fav["name"]

            # scan through all menu items
            for (cmd_name, cmd_details) in self._engine.commands.items():
                cmd = AppCommand(cmd_name, cmd_details)
                if cmd.get_app_instance_name() == app_instance_name and cmd.name == menu_name:
                    # found our match!
                    self.__menu_index += 1
                    cmd.add_command_to_menu(self._menu_handle, self.__menu_index)
                    # mark as a favourite item
                    cmd.favourite = True            
                    

        #self._menu_handle.addSeparator()

        # now go through all of the menu items.
        # separate them out into various sections
        commands_by_app = {}

        context_menu_index = 103
        for (cmd_name, cmd_details) in self._engine.commands.items():
            cmd = AppCommand(cmd_name, cmd_details)

            if cmd.get_type() == "context_menu":
                # context menu!
                context_menu_index += 1
                cmd.add_command_to_menu(self._context_menu, context_menu_index)
                self._add_event_callback(cmd.name, cmd.callback)
            else:
                # normal menu
                app_name = cmd.get_app_name()
                if app_name is None:
                    # un-parented app
                    app_name = "Other Items"
                if not app_name in commands_by_app:
                    commands_by_app[app_name] = []
                commands_by_app[app_name].append(cmd)

        # now add all apps to main menu
        self._add_app_menu(commands_by_app)

    def destroy_menu(self):
        item = self._menu_handle.GetFirstItem()
        while item:
            next_item = self._menu_handle.GetNextItem(item)
            self._menu_handle.DeleteItem(item)
            item = next_item
        self.__menu_index = 1
        self._callbacks = {}

    ##########################################################################################
    # context menu and UI

    def _add_context_menu(self):
        """
        Adds a context menu which displays the current context
        """

        ctx = self._engine.context
        if ctx.entity is None:
            # project-only!
            ctx_name = "%s" % ctx.project["name"]

        elif ctx.step is None and ctx.task is None:
            # entity only
            # e.g. Shot ABC_123
            ctx_name = "%s %s" % (ctx.entity["type"], ctx.entity["name"])

        else:
            # we have either step or task
            task_step = None
            if ctx.step:
                task_step = ctx.step.get("name")
            if ctx.task:
                task_step = ctx.task.get("name")

            # e.g. [Lighting, Shot ABC_123]
            ctx_name = "%s, %s %s" % (task_step, ctx.entity["type"], ctx.entity["name"])

        # create the menu object
        ctx_menu = FBGenericMenu()

        ctx_menu.InsertLast("Jump to Shotgun", self.__menu_index * 100 + 2)
        self._add_event_callback("Jump to Shotgun", self._jump_to_sg)

        ctx_menu.InsertLast("Jump to File System", self.__menu_index * 100 + 3)
        self._add_event_callback("Jump to File System", self._jump_to_fs)

        ctx_menu.OnMenuActivate.Add(self.__menu_event)

        self._menu_handle.InsertFirst(ctx_name, self.__menu_index, ctx_menu)
        self.__menu_index += 1
        return ctx_menu

    def _add_event_callback(self, event_name, callback):
        """
        Creates a mapping between the menu item name and the callback that should be
        run when it is clicked.
        """
        self._callbacks[event_name] = callback

    def _jump_to_sg(self):
        if self._engine.context.entity is None:
            # project-only!
            url = "%s/detail/%s/%d" % (self._engine.shotgun.base_url,
                                       "Project",
                                       self._engine.context.project["id"])
        else:
            # entity-based
            url = "%s/detail/%s/%d" % (self._engine.shotgun.base_url,
                                       self._engine.context.entity["type"],
                                       self._engine.context.entity["id"])

        # deal with fucked up nuke unicode handling
        if url.__class__ == unicode:
            url = unicodedata.normalize('NFKD', url).encode('ascii', 'ignore')
        webbrowser.open(url)

    def _jump_to_fs(self):
        """
        Jump from context to FS
        """
        if self._engine.context.entity:
            paths = self._engine.tank.paths_from_entity(self._engine.context.entity["type"],
                                                     self._engine.context.entity["id"])
        else:
            paths = self._engine.tank.paths_from_entity(self._engine.context.project["type"],
                                                     self._engine.context.project["id"])

        # launch one window for each location on disk
        # todo: can we do this in a more elegant way?
        for disk_location in paths:

            # get the setting
            system = platform.system()

            # run the app
            if system == "Linux":
                cmd = 'xdg-open "%s"' % disk_location
            elif system == "Darwin":
                cmd = 'open "%s"' % disk_location
            elif system == "Windows":
                cmd = 'cmd.exe /C start "Folder" "%s"' % disk_location
            else:
                raise Exception("Platform '%s' is not supported." % system)

            exit_code = os.system(cmd)
            if exit_code != 0:
                self._engine.log_error("Failed to launch '%s'!" % cmd)

    ##########################################################################################
    # app menus

    def _add_app_menu(self, commands_by_app):
        """
        Add all apps to the main menu, process them one by one.
        """

        for i, app_name in enumerate(sorted(commands_by_app.keys())):
            if len(commands_by_app[app_name]) > 1:
                # more than one menu entry fort his app
                # make a sub menu and put all items in the sub menu
                #app_menu = self._menu_handle.InsertLast(app_name, tank_index + i)
                app_menu = FBGenericMenu()
                self.__menu_index += 1
                menu_id = self.__menu_index * 100
                for j, cmd in enumerate(commands_by_app[app_name]):
                    cmd.add_command_to_menu(app_menu, menu_id + j + 1)
                    self._add_event_callback(cmd.name, cmd.callback)
                app_menu.OnMenuActivate.Add(self.__menu_event)
                self._menu_handle.InsertLast(app_name, menu_id, app_menu)
            else:
                # this app only has a single entry.
                # display that on the menu
                # todo: Should this be labelled with the name of the app
                # or the name of the menu item? Not sure.
                cmd_obj = commands_by_app[app_name][0]
                if not cmd_obj.favourite:
                    self.__menu_index += 1
                    cmd_obj.add_command_to_menu(self._menu_handle, self.__menu_index)
                    self._add_event_callback(cmd_obj.name, cmd_obj.callback)

    ##########################################################################################
    # private methods

    def __menu_event(self, control, event):
        """
        Handles menu events.
        """
        callback = self._callbacks.get(event.Name)
        if callback:
            callback()

class AppCommand(object):
    """
    Wraps around a single command that you get from engine.commands
    """

    def __init__(self, name, command_dict):
        self.name = name
        self.properties = command_dict["properties"]
        self.callback = command_dict["callback"]
        self.favourite = False

    def get_app_name(self):
        """
        Returns the name of the app that this command belongs to
        """
        if "app" in self.properties:
            return self.properties["app"].display_name
        return None

    def get_app_instance_name(self):
        """
        Returns the name of the app instance, as defined in the environment.
        Returns None if not found.
        """
        if "app" not in self.properties:
            return None

        app_instance = self.properties["app"]
        engine = app_instance.engine

        for (app_instance_name, app_instance_obj) in engine.apps.items():
            if app_instance_obj == app_instance:
                # found our app!
                return app_instance_name

        return None

    def get_documentation_url_str(self):
        """
        Returns the documentation as a str
        """
        if "app" in self.properties:
            app = self.properties["app"]
            doc_url = app.documentation_url
            # deal with nuke's inability to handle unicode. #fail
            if doc_url.__class__ == unicode:
                doc_url = unicodedata.normalize('NFKD', doc_url).encode('ascii', 'ignore')
            return doc_url

        return None

    def get_type(self):
        """
        returns the command type. Returns node, custom_pane or default
        """
        return self.properties.get("type", "default")

    def add_command_to_menu(self, menu, index):
        """
        Adds an app command to the menu
        """
        # std shotgun menu
        menu.InsertLast(self.name, index)
