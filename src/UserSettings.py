#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

from pathlib import Path
import configparser


class UserSettings(object):
    def __init__(self):

        userhome = str(Path.home())
        self.configdir = userhome + "/.config/pardus-software/"
        self.configfile = "settings.ini"
        self.config = configparser.ConfigParser()
        self.config_usi = None
        self.config_anim = None

    def createDefaultConfig(self):
        self.config['DEFAULT'] = {'UseSystemIcons': 'no',
                                  'Animations': 'yes'}

        if not Path.is_file(Path(self.configdir + self.configfile)):
            if self.createDir(self.configdir):
                with open(self.configdir + self.configfile, "w") as cf:
                    self.config.write(cf)

    def readConfig(self):
        try:
            self.config.read(self.configdir + self.configfile)
            self.config_usi = self.config.getboolean('DEFAULT', 'UseSystemIcons')
            self.config_anim = self.config.getboolean('DEFAULT', 'Animations')
        except:
            print("user config read error !")
            # if not read; set defaults to true
            self.config_usi = True
            self.config_anim = True

    def writeConfig(self, sysicons, anims):
        self.config['DEFAULT'] = {'UseSystemIcons': sysicons,
                                  'Animations': anims}
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
