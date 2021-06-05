#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import requests
from pathlib import Path
import tarfile
from shutil import rmtree


class Server(object):
    def __init__(self):
        self.serverurl = "http://store.pardus.org.tr"
        self.serverapps = "/api/v2/apps/"
        self.servercats = "/api/v2/cats/"
        self.serverhomepage = "/api/v2/homepage"
        self.serversendrate = "/api/v2/rate"
        self.serversenddownload = "/api/v2/download"
        self.serverfiles = "/files/"
        self.serverappicons = "appicons"
        self.servercaticons = "categoryicons"
        self.serverarchive = ".tar.gz"
        self.serversettings = "/api/v2/settings"
        self.settingsfile = "serversettings.ini"

        userhome = str(Path.home())
        self.cachedir = userhome + "/.cache/pardus-software/"
        self.configdir = userhome + "/.config/pardus-software/"

        self.connection = True
        self.app_scode = 0
        self.cat_scode = 0
        self.applist = []
        self.catlist = []
        self.ediapplist = []

        self.gnomeratingserver = "https://odrs.gnome.org/1.0/reviews/api/ratings"
        self.gnomecommentserver = "https://odrs.gnome.org/1.0/reviews/api/fetch"
        self.gnomeconnection = True

        try:
            request_app = requests.get(self.serverurl + self.serverapps)
        except Exception as e:
            print(e)
            print("Connection problem on serverapps")
            self.connection = False

        try:
            request_cat = requests.get(self.serverurl + self.servercats)
        except Exception as e:
            print(e)
            print("Connection problem on servercats")
            self.connection = False

        try:
            request_home = requests.get(self.serverurl + self.serverhomepage)
        except Exception as e:
            print(e)
            print("Connection problem on servercats")
            self.connection = False

        if self.connection:
            self.app_scode = request_app.status_code
            self.cat_scode = request_cat.status_code
            self.home_scode = request_home.status_code
            if self.app_scode == 200 and self.cat_scode == 200 and self.home_scode == 200:
                print("Connection successful")
                self.applist = request_app.json()["app-list"]
                self.applist = sorted(self.applist, key=lambda x: x["name"])
                self.catlist = request_cat.json()["cat-list"]
                self.ediapplist = request_home.json()["editor-apps"]
            else:
                self.connection = False

    def getAppIcons(self):
        if not self.isExists(self.cachedir + self.serverappicons):
            print("trying to downlad " + self.serverappicons)
            try:
                response = requests.get(self.serverurl + self.serverfiles + self.serverappicons + self.serverarchive)
            except:
                print(
                    "server error getting " + self.serverurl + self.serverfiles + self.serverappicons + self.serverarchive)
                return False
            if response.status_code == 200:
                if self.createDir(self.cachedir):
                    with open(self.cachedir + self.serverappicons + self.serverarchive, "wb") as file:
                        file.write(response.content)
                    if self.extractArchive(self.cachedir + self.serverappicons + self.serverarchive,
                                           self.serverappicons):
                        return True
                return False
            else:
                print("{} : {}".format("error getting app icons, status code", response.status_code))
                return False
        else:
            return True

    def getCategoryIcons(self):
        if not self.isExists(self.cachedir + self.servercaticons):
            print("trying to downlad " + self.servercaticons)
            try:
                response = requests.get(self.serverurl + self.serverfiles + self.servercaticons + self.serverarchive)
            except:
                print(
                    "server error getting " + self.serverurl + self.serverfiles + self.servercaticons + self.serverarchive)
                return False
            if response.status_code == 200:
                if self.createDir(self.cachedir):
                    with open(self.cachedir + self.servercaticons + self.serverarchive, "wb") as file:
                        file.write(response.content)
                    if self.extractArchive(self.cachedir + self.servercaticons + self.serverarchive,
                                           self.servercaticons):
                        return True
                return False
            else:
                print("{} : {}".format("error getting category icons, status code", response.status_code))
                return False
        else:
            return True

    def getDefaultSettings(self):
        if not self.isExists(self.configdir):
            print("trying to get settings from server")
            try:
                response = requests.get(self.serverurl + self.serversettings)
            except:
                print("server error getting " + self.serverurl + self.serversettings)
                return False
            if response.status_code == 200:
                if self.createDir(self.configdir):
                    with open(self.configdir + self.settingsfile, "wb") as file:
                        file.write(response.content)
                        return True
            else:
                print("{} : {}".format("error getting settings, status code", response.status_code))
                return False
        else:
            return True

    def createDir(self, dir):
        try:
            Path(dir).mkdir(parents=True, exist_ok=True)
            return True
        except:
            print("{} : {}".format("mkdir error", self.cachedir))
            return False

    def extractArchive(self, archive, type):
        if not Path(self.cachedir + type).exists():
            try:
                tar = tarfile.open(archive)
                tar.extractall(path=self.cachedir)
                tar.close()
                return True
            except:
                print("tarfile error")
                return False
        return True

    def isExists(self, dir):
        if Path(dir).exists():
            print(dir + " folder exists")
            return True
        else:
            print(dir + " folder not exists")
            return False

    def getGnomeRatings(self):
        try:
            request_gnome = requests.get(self.gnomeratingserver)
        except Exception as e:
            print(e)
            print("Connection problem on gnome odrs / ratings")
            self.gnomeconnection = False

        if self.gnomeconnection:
            if request_gnome.status_code == 200:
                return request_gnome.json()
            return False
        return False

    def deleteCache(self):
        try:
            rmtree(self.cachedir)
            return True, ""
        except Exception as e:
            print(str(e))
            return False, str(e)
