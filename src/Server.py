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
        self.serverurl = "http://192.168.1.13"
        self.serverapi = "/api/v2/apps/"
        self.serverfiles = "/files/"
        self.serverappicons = "appicons"
        self.servercaticons = "categoryicons"
        self.serverarchive = ".tar.gz"

        userhome = str(Path.home())
        self.cachedir = userhome + "/.cache/pardus-software-center/"

        self.connection = True
        self.scode = 0
        self.applist = []

        try:
            request = requests.get(self.serverurl + self.serverapi)
        except Exception as e:
            print(e)
            print("Connection problem")
            self.connection = False

        if self.connection:
            self.scode = request.status_code
            if self.scode == 200:
                print("Connection successful")
                self.applist = request.json()["app-list"]
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
