#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import requests
from pathlib import Path
import tarfile


class Server(object):
    def __init__(self):
        self.serverurl = "http://192.168.1.28:8000"
        self.serverapps = "/api/v2/apps/"
        self.servercats = "/api/v2/cats/"
        self.serverfiles = "/files/"
        self.serverappicons = "appicons"
        self.servercaticons = "categoryicons"
        self.serverarchive = ".tar.gz"

        userhome = str(Path.home())
        self.cachedir = userhome + "/.cache/pardus-software-center/"

        self.connection = True
        self.app_scode = 0
        self.cat_scode = 0
        self.applist = []
        self.catlist = []

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

        if self.connection:
            self.app_scode = request_app.status_code
            self.cat_scode = request_cat.status_code
            if self.app_scode == 200 and self.cat_scode == 200:
                print("Connection successful")
                self.applist = request_app.json()["app-list"]
                self.applist = sorted(self.applist, key=lambda x: x["name"])
                self.catlist = request_cat.json()["cat-list"]
            else:
                self.connection = False

    def getAppIcons(self):
        if not self.isCacheFiles(self.serverappicons):
            print("trying to downlad " + self.serverappicons)
            try:
                response = requests.get(self.serverurl + self.serverfiles + self.serverappicons + self.serverarchive)
            except:
                print(
                    "server error getting " + self.serverurl + self.serverfiles + self.serverappicons + self.serverarchive)
                return False
            if response.status_code == 200:
                if self.createCacheDir():
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
        if not self.isCacheFiles(self.servercaticons):
            print("trying to downlad " + self.servercaticons)
            try:
                response = requests.get(self.serverurl + self.serverfiles + self.servercaticons + self.serverarchive)
            except:
                print(
                    "server error getting " + self.serverurl + self.serverfiles + self.servercaticons + self.serverarchive)
                return False
            if response.status_code == 200:
                if self.createCacheDir():
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

    def createCacheDir(self):
        try:
            Path(self.cachedir).mkdir(parents=True, exist_ok=True)
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

    def isCacheFiles(self, type):
        if Path(self.cachedir + type).exists():
            print(self.cachedir + type + " folder exists")
            return True
        else:
            print(self.cachedir + type + " folder not exists")
            return False
