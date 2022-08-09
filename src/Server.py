#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

from pathlib import Path
from shutil import rmtree
from hashlib import md5
import tarfile, gi, json
from gi.repository import GLib, Gio, Soup

gi.require_version("GLib", "2.0")
gi.require_version("Soup", "2.4")


class Server(object):
    def __init__(self):
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

        userhome = str(Path.home())
        try:
            self.username = userhome.split("/")[-1]
        except:
            self.username = ""
        self.cachedir = userhome + "/.cache/pardus-software/"
        self.configdir = userhome + "/.config/pardus-software/"

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
        self.iconnames = ""
        self.badwords = []
        self.dailydowns = []
        self.osdowns = []
        self.appdowns = []
        self.oscolors = []
        self.appcolors = []
        self.aptuptime = 86400  # default control value is 1 day if server value is none

        self.gnomeratingserver = "https://odrs.gnome.org/1.0/reviews/api/ratings"
        self.gnomecommentserver = "https://odrs.gnome.org/1.0/reviews/api/fetch"

    def get(self, url, type):
        file = Gio.File.new_for_uri(url)
        file.load_contents_async(None, self._open_stream, type)

    def _open_stream(self, file, result, type):
        try:
            success, data, etag = file.load_contents_finish(result)
        except GLib.Error as error:
            self.error_message = error.message
            print(f"{type} _open_stream Error: {error.domain}, {error.message}")
            self.ServerAppsCB(False, response=None, type=type)
            return False
        if success:
            self.ServerAppsCB(True, json.loads(data), type)
        else:
            print(f"{type} is not success")
            self.ServerAppsCB(False, response=None, type=type)

    def getIcons(self, url, type, force_download=False, fromsettings=False):
        if not self.isExists(self.cachedir + type) or force_download:
            file = Gio.File.new_for_uri(url)
            file.load_contents_async(None, self._open_icon_stream, type, fromsettings)
        else:
            print(f"{type} already available")
            self.ServerIconsCB(True, type, fromsettings)

    def _open_icon_stream(self, file, result, type, fromsettings):
        try:
            success, data, etag = file.load_contents_finish(result)
        except GLib.Error as error:
            print(f"{type} _open_icon_stream Error: {error.domain}, {error.message}")
            self.ServerIconsCB(False, type, fromsettings)
            return False
        if success:
            if self.createDir(self.cachedir):
                with open(self.cachedir + type + self.serverarchive, "wb") as file:
                    file.write(data)
                if self.controlMD5(type):
                    if self.extractArchive(
                        self.cachedir + type + self.serverarchive, type
                    ):
                        self.ServerIconsCB(True, type, fromsettings)
                        return True
                    else:
                        print(f"{type} extract error")
                else:
                    print(f"md5 value is different (controlMD5) {type} ")
        else:
            print(f"{type} is not success")
        self.ServerIconsCB(False, type, fromsettings)

    # def getAppIcons(self, force_download=False):
    #     if not self.isExists(self.cachedir + self.serverappicons) or force_download:
    #         print("trying to downlad " + self.serverappicons)
    #         try:
    #             response = requests.get(self.serverurl + self.serverfiles + self.serverappicons + self.serverarchive)
    #         except:
    #             print(
    #                 "server error getting " + self.serverurl + self.serverfiles + self.serverappicons + self.serverarchive)
    #             return False
    #         if response.status_code == 200:
    #             if self.createDir(self.cachedir):
    #                 with open(self.cachedir + self.serverappicons + self.serverarchive, "wb") as file:
    #                     file.write(response.content)
    #                 if self.controlMD5(self.serverappicons):
    #                     if self.extractArchive(self.cachedir + self.serverappicons + self.serverarchive,
    #                                            self.serverappicons):
    #                         return True
    #                     else:
    #                         print("extract error")
    #                         return False
    #                 else:
    #                     print("md5 value is different (controlMD5)")
    #                     return False
    #             return False
    #         else:
    #             print("{} : {}".format("error getting app icons, status code", response.status_code))
    #             return False
    #     else:
    #         return True

    # def getCategoryIcons(self, force_download=False):
    #     if not self.isExists(self.cachedir + self.servercaticons) or force_download:
    #         print("trying to downlad " + self.servercaticons)
    #         try:
    #             response = requests.get(self.serverurl + self.serverfiles + self.servercaticons + self.serverarchive)
    #         except:
    #             print(
    #                 "server error getting " + self.serverurl + self.serverfiles + self.servercaticons + self.serverarchive)
    #             return False
    #         if response.status_code == 200:
    #             if self.createDir(self.cachedir):
    #                 with open(self.cachedir + self.servercaticons + self.serverarchive, "wb") as file:
    #                     file.write(response.content)
    #                 if self.controlMD5(self.servercaticons):
    #                     if self.extractArchive(self.cachedir + self.servercaticons + self.serverarchive,
    #                                            self.servercaticons):
    #                         return True
    #                     else:
    #                         print("extract error")
    #                         return False
    #                 else:
    #                     print("md5 value is different (controlMD5)")
    #                     return False
    #             return False
    #         else:
    #             print("{} : {}".format("error getting category icons, status code", response.status_code))
    #             return False
    #     else:
    #         return True

    def controlIcons(self):
        redown_app_icons = False
        redown_cat_icons = False
        if self.isExists(self.cachedir + self.serverappicons + self.serverarchive):
            localiconmd5 = md5(
                open(
                    self.cachedir + self.serverappicons + self.serverarchive, "rb"
                ).read()
            ).hexdigest()

            if self.servermd5["appicon"] and localiconmd5 != self.servermd5["appicon"]:
                print(
                    "md5 value of app icon is different so trying download new app icons from server"
                )

                redown_app_icons = True
        if self.isExists(self.cachedir + self.servercaticons + self.serverarchive):
            localiconmd5 = md5(
                open(
                    self.cachedir + self.servercaticons + self.serverarchive, "rb"
                ).read()
            ).hexdigest()

            if self.servermd5["caticon"] and localiconmd5 != self.servermd5["caticon"]:
                print(
                    "md5 value of cat icon is different so trying download new cat icons from server"
                )

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
            localiconmd5 = md5(
                open(self.cachedir + type + self.serverarchive, "rb").read()
            ).hexdigest()

            if self.servermd5[servertag] and localiconmd5 == self.servermd5[servertag]:
                return True
        return False

    # def getDefaultSettings(self):
    #     if not self.isExists(self.configdir):
    #         print("trying to get settings from server")
    #         try:
    #             response = requests.get(self.serverurl + self.serversettings)
    #         except:
    #             print("server error getting " + self.serverurl + self.serversettings)
    #             return False
    #         if response.status_code == 200:
    #             if self.createDir(self.configdir):
    #                 with open(self.configdir + self.settingsfile, "wb") as file:
    #                     file.write(response.content)
    #                     return True
    #         else:
    #             print("{} : {}".format("error getting settings, status code", response.status_code))
    #             return False
    #     else:
    #         return True

    def createDir(self, dir):
        try:
            Path(dir).mkdir(parents=True, exist_ok=True)
            return True
        except:
            print(f"mkdir error : {self.cachedir}")
            return False

    def extractArchive(self, archive, type):
        try:
            tar = tarfile.open(archive)
            if type == self.serverappicons:
                extractables = [
                    member
                    for member in tar.getmembers()
                    if member.name.startswith(self.serverappicons)
                    and member.name.endswith(self.servericonty)
                ]

            elif type == self.servercaticons:
                extractables = [
                    member
                    for member in tar.getmembers()
                    if member.name.startswith(self.servercaticons)
                    and member.name.endswith(self.servericonty)
                ]

            else:
                extractables = ""
            rmtree(self.cachedir + type, ignore_errors=True)
            try:
                icons = self.iconnames.split(",")
                for icon in icons:
                    rmtree(self.cachedir + type + "-" + icon, ignore_errors=True)
            except Exception as e:
                print(f"{e}")
            tar.extractall(members=extractables, path=self.cachedir)
            tar.close()
            return True
        except:
            print("tarfile error")
            return False

    def isExists(self, dir):
        if Path(dir).exists():
            print(f"{dir} exists")
            return True
        else:
            print(f"{dir} not exists")
            return False

    # def getGnomeRatings(self):
    #     try:
    #         request_gnome = requests.get(self.gnomeratingserver)
    #     except Exception as e:
    #         print(e)
    #         print("Connection problem on gnome odrs / ratings")
    #         self.gnomeconnection = False
    #
    #     if self.gnomeconnection:
    #         if request_gnome.status_code == 200:
    #             return request_gnome.json()
    #         return False
    #     return False

    def deleteCache(self):
        try:
            rmtree(self.cachedir)
            return True, ""
        except Exception as e:
            print(e)
            return False, str(e)
