#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import json
import tarfile
from hashlib import md5
from pathlib import Path
from shutil import rmtree

import gi

gi.require_version("GLib", "2.0")
gi.require_version('Soup', '2.4')
from gi.repository import GLib, Gio
from Logger import Logger


class Server(object):
    def __init__(self):
        self.Logger = Logger(__name__)
        self.serverurl = ""  # This is setting from MainWindow server func
        self.serverapps = "/api/v2/apps/"
        self.servercats = "/api/v2/cats/"
        self.serverhomepage = "/api/v2/homepage"
        self.serverstatistics = "/api/v2/statistics"
        self.serversendrate = "/api/v2/rate"
        self.serversenddownload = "/api/v2/download"
        self.serversendsuggestapp = "/api/v2/suggestapp"
        self.serverparduscomments = "/api/v2/parduscomments"
        self.serverfiles = "/files/"
        self.serverappicons = "appicons"
        self.servercaticons = "categoryicons"
        self.servericonty = ".svg"
        self.serverarchive = ".tar.gz"
        self.serversettings = "/api/v2/settings"
        self.settingsfile = "serversettings.ini"

        # The following cache and config assignments are for backward compatibility
        self.cachedir = "{}/pardus-software/".format(GLib.get_user_cache_dir())
        self.configdir = "{}/pardus-software/".format(GLib.get_user_config_dir())

        # The following cache and config assignments are for the new version
        if not Path(self.cachedir).exists():
            self.cachedir = "{}/pardus/pardus-software/".format(GLib.get_user_cache_dir())
        if not Path(self.configdir).exists():
            self.configdir = "{}/pardus/pardus-software/".format(GLib.get_user_config_dir())

        self.error_message = ""
        self.connection = False
        self.applist = []
        self.orgapplist = []
        self.catlist = []
        self.ediapplist = []
        self.mostdownapplist = []
        self.mostrateapplist = []
        self.lastaddedapplist = []
        self.totalstatistics = []
        self.servermd5 = []
        self.appversion = ""
        self.appversion_pardus21 = ""
        self.appversion_pardus23 = ""
        self.iconnames = ""
        self.badwords = []
        self.dailydowns = []
        self.osdowns = []
        self.appdowns = []
        self.oscolors = []
        self.appcolors = []
        self.osexplode = []
        self.aptuptime = 86400  # default control value is 1 day if server value is none

        self.gnomeratingserver = "https://odrs.gnome.org/1.0/reviews/api/ratings"
        self.gnomecommentserver = "https://odrs.gnome.org/1.0/reviews/api/fetch"

    def control_server(self, url):
        file = Gio.File.new_for_uri(url)
        file.load_contents_async(None, self._open_control_stream)

    def _open_control_stream(self, file, result):
        try:
            file.load_contents_finish(result)
        except GLib.Error as error:
            # if error.matches(Gio.tls_error_quark(),  Gio.TlsError.BAD_CERTIFICATE):
            if error.domain == GLib.quark_to_string(Gio.tls_error_quark()):
                self.Logger.warning("_open_control_stream Error: {}, {}".format(error.domain, error.message))
                self.Logger.exception("{}".format(error))
                self.ServerAppsControlCB(False)  # Send to MainWindow
                return False
        self.ServerAppsControlCB(True)  # Send to MainWindow

    def get(self, url, type):
        file = Gio.File.new_for_uri(url)
        file.load_contents_async(None, self._open_stream, type)

    def _open_stream(self, file, result, type):
        try:
            success, data, etag = file.load_contents_finish(result)
        except GLib.Error as error:
            self.error_message = error.message
            self.Logger.warning("{} _open_stream Error: {}, {}".format(type, error.domain, error.message))
            self.Logger.exception("{}".format(error))
            self.ServerAppsCB(False, response=None, type=type)  # Send to MainWindow
            return False

        if success:
            self.ServerAppsCB(True, json.loads(data), type)
        else:
            self.Logger.warning("{} is not success".format(type))
            self.ServerAppsCB(False, response=None, type=type)  # Send to MainWindow

    def getIcons(self, url, type, force_download=False, fromsettings=False):
        if not self.isExists(self.cachedir + type) or force_download:
            file = Gio.File.new_for_uri(url)
            file.load_contents_async(None, self._open_icon_stream, type, fromsettings)
        else:
            self.Logger.info("{} already available".format(type))
            self.ServerIconsCB(True, type, fromsettings)

    def _open_icon_stream(self, file, result, type, fromsettings):
        try:
            success, data, etag = file.load_contents_finish(result)
        except GLib.Error as error:
            self.Logger.warning("{} _open_icon_stream Error: {}, {}".format(type, error.domain, error.message))
            self.Logger.exception("{}".format(error))
            self.ServerIconsCB(False, type, fromsettings)
            return False

        if success:
            if self.createDir(self.cachedir):
                with open(self.cachedir + type + self.serverarchive, "wb") as file:
                    file.write(data)
                if self.controlMD5(type):
                    if self.extractArchive(self.cachedir + type + self.serverarchive, type):
                        self.ServerIconsCB(True, type, fromsettings)
                        return True
                    else:
                        self.Logger.warning("{} extract error".format(type))
                else:
                    self.Logger.warning("md5 value is different (controlMD5) {} ".format(type))
        else:
            self.Logger.warning("{} is not success".format(type))

        self.ServerIconsCB(False, type, fromsettings)

    def controlIcons(self):
        redown_app_icons = False
        redown_cat_icons = False
        if self.isExists(self.cachedir + self.serverappicons + self.serverarchive):
            localiconmd5 = md5(open(self.cachedir + self.serverappicons + self.serverarchive, "rb").read()).hexdigest()
            if self.servermd5["appicon"]:
                if localiconmd5 != self.servermd5["appicon"]:
                    self.Logger.info("md5 value of app icon is different so trying download new app icons from server")
                    redown_app_icons = True

        if self.isExists(self.cachedir + self.servercaticons + self.serverarchive):
            localiconmd5 = md5(open(self.cachedir + self.servercaticons + self.serverarchive, "rb").read()).hexdigest()
            if self.servermd5["caticon"]:
                if localiconmd5 != self.servermd5["caticon"]:
                    self.Logger.info("md5 value of cat icon is different so trying download new cat icons from server")
                    redown_cat_icons = True

        return redown_app_icons, redown_cat_icons

    def controlMD5(self, type):
        if type == self.serverappicons:
            servertag = "appicon"
        elif type == self.servercaticons:
            servertag = "caticon"
        else:
            return False

        if self.isExists(self.cachedir + type + self.serverarchive):
            localiconmd5 = md5(open(self.cachedir + type + self.serverarchive, "rb").read()).hexdigest()
            if self.servermd5[servertag]:
                if localiconmd5 == self.servermd5[servertag]:
                    return True
        return False

    def createDir(self, dir):
        try:
            Path(dir).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as error:
            self.Logger.warning("{} : {}".format("mkdir error", self.cachedir))
            self.Logger.exception("{}".format(error))
            return False

    def extractArchive(self, archive, type):
        try:
            tar = tarfile.open(archive)
            if type == self.serverappicons:
                extractables = [member for member in tar.getmembers() if
                                member.name.startswith(self.serverappicons) and member.name.endswith(self.servericonty)]
            elif type == self.servercaticons:
                extractables = [member for member in tar.getmembers() if
                                member.name.startswith(self.servercaticons) and member.name.endswith(self.servericonty)]
            else:
                extractables = ""
            rmtree(self.cachedir + type, ignore_errors=True)
            try:
                icons = self.iconnames.split(",")
                for icon in icons:
                    rmtree(self.cachedir + type + "-" + icon, ignore_errors=True)
            except Exception as e:
                self.Logger.exception("{}".format(e))
            tar.extractall(members=extractables, path=self.cachedir)
            tar.close()
            return True
        except:
            self.Logger.warning("tarfile error")
            return False

    def isExists(self, dir):
        if Path(dir).exists():
            self.Logger.info("{} exists".format(dir))
            return True
        else:
            self.Logger.info("{} not exists".format(dir))
            return False

    def deleteCache(self):
        try:
            rmtree(self.cachedir)
            self.cachedir = "{}/pardus/pardus-software/".format(GLib.get_user_cache_dir())
            self.createDir(self.cachedir)
            self.Logger.info("{} removed".format(self.cachedir))
            return True, ""
        except Exception as e:
            self.Logger.exception("{}".format(e))
            return False, str(e)
