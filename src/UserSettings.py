#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

from pathlib import Path
import configparser, distro


class UserSettings(object):
    def __init__(self):

        try:
            self.usercodename = distro.codename().lower()
        except:
            self.usercodename = ""
        userhome = str(Path.home())
        self.configdir = userhome + "/.config/pardus-software/"
        self.configfile = "settings.ini"
        self.config = configparser.ConfigParser()
        self.config_usi = None
        self.config_ea = None
        self.config_saa = None
        self.config_hera = None

    def createDefaultConfig(self, force=False):
        self.config['DEFAULT'] = {'UseServerIcons': 'yes',
                                  'Animations': 'yes',
                                  'ShowAvailableApps': 'yes',
                                  'HideExternalRepoApps': 'yes'}

        if not Path.is_file(Path(self.configdir + self.configfile)) or force:
            if self.createDir(self.configdir):
                with open(self.configdir + self.configfile, "w") as cf:
                    self.config.write(cf)

    def readConfig(self):
        try:
            print("in readconfig")
            self.config.read(self.configdir + self.configfile)
            self.config_usi = self.config.getboolean('DEFAULT', 'UseServerIcons')
            self.config_ea = self.config.getboolean('DEFAULT', 'Animations')
            self.config_saa = self.config.getboolean('DEFAULT', 'ShowAvailableApps')
            self.config_hera = self.config.getboolean('DEFAULT', 'HideExternalRepoApps')
        except:
            print("user config read error ! Trying create defaults")
            # if not read; try to create defaults
            self.config_usi = True
            self.config_ea = True
            self.config_saa = True
            self.config_hera = True
            try:
                self.createDefaultConfig(force=True)
            except Exception as e:
                print("self.createDefaultConfig(force=True) : {}".format(e))

    def writeConfig(self, srvicons, anims, avaiapps, extapps):
        self.config['DEFAULT'] = {'UseServerIcons': srvicons,
                                  'Animations': anims,
                                  'ShowAvailableApps': avaiapps,
                                  'HideExternalRepoApps': extapps}
        if self.createDir(self.configdir):
            with open(self.configdir + self.configfile, "w") as cf:
                self.config.write(cf)
                return True
        return False

    def createDir(self, dir):
        try:
            Path(dir).mkdir(parents=True, exist_ok=True)
            return True
        except:
            print("{} : {}".format("mkdir error", dir))
            return False
