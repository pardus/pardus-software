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
        # self.servercats = "/api/v2/cats/"
        self.serverhomepage = "/api/v3/homepage"
        self.serversendrate = "/api/v2/rate"
        self.serversenddownload = "/api/v2/download"
        # self.serversendsuggestapp = "/api/v3/suggestapp"
        self.serverparduscomments = "/api/v2/parduscomments"
        self.serverfiles = "/files/"
        self.server_apps_archive = "apps.tar.gz"
        self.server_icons_archive = "icons.tar.gz"
        self.server_images_archive = "images.tar.gz"
        self.server_cats_archive = "cats.tar.gz"
        self.server_home_archive = "home.tar.gz"

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
        self.trendapplist = []
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

    # def control_server(self, url):
    #     file = Gio.File.new_for_uri(url)
    #     file.load_contents_async(None, self._open_control_stream)
    #
    # def _open_control_stream(self, file, result):
    #     try:
    #         file.load_contents_finish(result)
    #     except GLib.Error as error:
    #         # if error.matches(Gio.tls_error_quark(),  Gio.TlsError.BAD_CERTIFICATE):
    #         if error.domain == GLib.quark_to_string(Gio.tls_error_quark()):
    #             self.Logger.warning("_open_control_stream Error: {}, {}".format(error.domain, error.message))
    #             self.Logger.exception("{}".format(error))
    #             self.ServerAppsURLControlCB(False)  # Send to MainWindow
    #             return False
    #     self.ServerAppsURLControlCB(True)  # Send to MainWindow

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

    def get_file(self, url, download_location, server_md5, type="", save_file=True):
        file = Gio.File.new_for_uri(url)
        file.load_contents_async(None, self._open_file_stream, download_location, server_md5, type, save_file)

    def _open_file_stream(self, file, result, download_location, server_md5, type, save_file=True):
        try:
            success, data, etag = file.load_contents_finish(result)
        except GLib.Error as error:
            print()
            self.error_message = "{} : {}".format(error, type)
            self.Logger.warning("{} _open_file_stream Error: {}, {}".format(type, error.domain, error.message))
            self.Logger.exception("{}".format(error))
            self.ServerFilesCB(False)
            return False

        if save_file:
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
        else:
            self.ServerFilesCB(True, type=type, response=json.loads(data))

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

    def delete_cache(self):
        try:
            rmtree(self.cachedir)
            self.cachedir = "{}/pardus/pardus-software/".format(GLib.get_user_cache_dir())
            Path(self.cachedir).mkdir(parents=True, exist_ok=True)
            self.Logger.info("{} removed".format(self.cachedir))
            return True, ""
        except Exception as e:
            self.Logger.exception("{}".format(e))
            return False, str(e)
