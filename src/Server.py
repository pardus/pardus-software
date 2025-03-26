#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import json
import os.path
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
        self.serverhash = "/api/v3/hash"
        self.serverapps = "/api/v3/apps/"
        self.serverapps_v2 = "/api/v2/apps/"
        self.servercats = "/api/v2/cats/"
        self.serverhomepage = "/api/v2/homepage"
        self.serverstatistics = "/api/v2/statistics"
        self.serversendrate = "/api/v2/rate"
        self.serversenddownload = "/api/v2/download"
        self.serversendsuggestapp = "/api/v2/suggestapp"
        self.serverparduscomments = "/api/v2/parduscomments"
        self.serverfiles = "/files/"
        # self.serverappicons = "appicons"
        # self.servercaticons = "categoryicons"
        self.server_apps_archive = "apps.tar.gz"
        self.server_icons_archive = "icons.tar.gz"
        self.server_images_archive = "images.tar.gz"
        self.server_cats_archive = "cats.tar.gz"
        self.server_home_archive = "home.tar.gz"
        # self.servericonty = ".svg"
        # self.serverarchive = ".tar.gz"
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

        self.icons_dir = self.cachedir + "icons/"
        self.app_icons_dir = self.icons_dir + "app-icons"
        self.cat_icons_dir = self.icons_dir + "cat-icons"

        self.error_message = ""
        self.connection = False
        self.applist = []
        self.orgapplist = []
        self.catlist = []
        self.ediapplist = []
        self.sliderapplist = []
        self.mostdownapplist = []
        self.popularapplist = []
        self.lastaddedapplist = []
        self.totalstatistics = []
        self.servermd5 = {}
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

        self.old_server_tried = False

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
                self.ServerAppsURLControlCB(False)  # Send to MainWindow
                return False
        self.ServerAppsURLControlCB(True)  # Send to MainWindow

    def get_hashes(self, url):
        file = Gio.File.new_for_uri(url)
        file.load_contents_async(None, self._open_hashes_stream)

    def _open_hashes_stream(self, file, result):
        try:
            success, data, etag = file.load_contents_finish(result)
        except GLib.Error as error:
            self.error_message = error
            self.Logger.warning("_open_hashes_stream Error: {}, {}".format(error.domain, error.message))
            self.Logger.exception("{}".format(error))
            self.ServerHashesCB(False)
            return False

        if success:
            self.ServerHashesCB(True, json.loads(data))
        else:
            self.Logger.warning("_open_hashes_stream is not success")
            self.ServerHashesCB(False)  # Send to MainWindow

    def get(self, url, type):
        file = Gio.File.new_for_uri(url)
        file.load_contents_async(None, self._open_stream, type)

    def _open_stream(self, file, result, type):
        try:
            success, data, etag = file.load_contents_finish(result)
        except GLib.Error as error:
            # if error.domain == GLib.quark_to_string(Gio.io_error_quark()):
            if error.matches(Gio.io_error_quark(), Gio.IOErrorEnum.NOT_FOUND):
                if not self.old_server_tried and type == "apps":
                    self.Logger.warning("_open_stream: trying old server apps url")
                    self.get(self.serverurl + self.serverapps_v2, type)
                    self.old_server_tried = True
                    return
                else:
                    self.Logger.warning("{} is not success from old server apps too".format(type))
                    self.ServerAppsCB(False, response=None, type=type)  # Send to MainWindow
                    return False
            else:
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

    def get_file(self, url, download_location, server_md5, type=""):
        file = Gio.File.new_for_uri(url)
        file.load_contents_async(None, self._open_file_stream, download_location, server_md5, type)

    def _open_file_stream(self, file, result, download_location, server_md5, type):
        try:
            success, data, etag = file.load_contents_finish(result)
        except GLib.Error as error:
            print()
            self.error_message = "{} : {}".format(error, type)
            self.Logger.warning("{} _open_file_stream Error: {}, {}".format(type, error.domain, error.message))
            self.Logger.exception("{}".format(error))
            self.ServerFilesCB(False)
            return False

        try:
            Path(os.path.dirname(download_location)).mkdir(parents=True, exist_ok=True)
            with open(download_location, "wb") as file:
                file.write(data)
        except Exception as e:
            self.error_message = "{}".format(e)
            self.Logger.warning("_open_file_stream Error: {}".format(e))
            self.Logger.exception("{}".format(e))
            self.ServerFilesCB(False)
            return False

        if md5(open(download_location, "rb").read()).hexdigest() == server_md5:
            if self.extract_archive(download_location):
                self.ServerFilesCB(True, type=type)
            else:
                self.error_message = "{} extract error".format(type)
                self.Logger.warning("{} extract error".format(type))
                self.ServerFilesCB(False)
        else:
            self.error_message = "{} file downloaded but md5 is different!".format(download_location)
            self.Logger.warning("{} file downloaded but md5 is different!".format(download_location))
            self.ServerFilesCB(False)

    def get_icons(self, url, filename, force_download=False, fromsettings=False):
        if not self.isExists(self.icons_dir + filename) or force_download:
            file = Gio.File.new_for_uri(url)
            file.load_contents_async(None, self._open_icon_stream, filename, fromsettings)
        else:
            self.Logger.info("{} already available".format(filename))
            if not self.isExists(self.app_icons_dir) or not self.isExists(self.cat_icons_dir):
                self.extract_icons(self.icons_dir + filename)
            self.ServerIconsCB(True, fromsettings)

    def _open_icon_stream(self, file, result, filename, fromsettings):
        try:
            success, data, etag = file.load_contents_finish(result)
        except GLib.Error as error:
            self.Logger.warning("{} _open_icon_stream Error: {}, {}".format(filename, error.domain, error.message))
            self.Logger.exception("{}".format(error))
            self.ServerIconsCB(False, fromsettings)
            return False

        if success:
            if self.createDir(self.icons_dir):
                with open(self.icons_dir + filename , "wb") as file:
                    file.write(data)
                if self.control_icons_md5(filename):
                    if self.extract_icons(self.icons_dir + filename):
                        self.ServerIconsCB(True, fromsettings)
                        return True
                    else:
                        self.Logger.warning("{} extract error".format(filename))
                else:
                    self.Logger.warning("md5 value is different (controlMD5) {} ".format(filename))
        else:
            self.Logger.warning("{} is not success".format(filename))

        self.ServerIconsCB(False, fromsettings)

    def control_icons(self):
        redown_icons = False
        if self.isExists(self.icons_dir + self.server_icons_archive):
            localiconmd5 = md5(open(self.icons_dir + self.server_icons_archive, "rb").read()).hexdigest()
            if "icons" in self.servermd5.keys() and self.servermd5["icons"]:
                if localiconmd5 != self.servermd5["icons"]:
                    self.Logger.info("md5 value of icons are different so trying download new icons from server")
                    redown_icons = True
        return redown_icons

    def control_icons_md5(self, filename):
        if self.isExists(self.icons_dir + filename):
            localiconmd5 = md5(open(self.icons_dir + filename, "rb").read()).hexdigest()
            if self.servermd5["icons"]:
                if localiconmd5 == self.servermd5["icons"]:
                    return True
        return False

    def extract_icons(self, archive):
        try:
            rmtree(self.app_icons_dir, ignore_errors=True)
            rmtree(self.cat_icons_dir, ignore_errors=True)
            tar = tarfile.open(archive)
            extractables = [member for member in tar.getmembers() if member.name.endswith(".svg")]
            tar.extractall(members=extractables, path=self.icons_dir)
            tar.close()
            return True
        except Exception as error:
            self.Logger.warning("{} : {}".format("extract error", self.cachedir))
            self.Logger.exception("{}".format(error))
            return False

    def extract_archive(self, archive):
        def remove_subdirectories_and_files(directory, excepted_file):
            for root, dirs, files in os.walk(directory, topdown=False):
                for file in files:
                    file_path = os.path.join(root, file)
                    if file_path != excepted_file:
                        os.remove(file_path)
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    rmtree(dir_path, ignore_errors=True)
        try:
            remove_subdirectories_and_files(os.path.dirname(archive), excepted_file=archive)
            tar = tarfile.open(archive)
            extractables = [member for member in tar.getmembers() if member.name.endswith(".svg") or member.name.endswith(".png") or member.name.endswith(".json")]
            tar.extractall(members=extractables, path=os.path.dirname(archive))
            tar.close()
            return True
        except Exception as error:
            self.Logger.warning("{} : {}".format("extract error", self.cachedir))
            self.Logger.exception("{}".format(error))
            return False

    def createDir(self, dir):
        try:
            Path(dir).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as error:
            self.Logger.warning("{} : {}".format("mkdir error", self.cachedir))
            self.Logger.exception("{}".format(error))
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
