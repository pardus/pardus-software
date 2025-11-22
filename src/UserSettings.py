#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import configparser
from pathlib import Path

import distro
import gi

gi.require_version("GLib", "2.0")
from gi.repository import GLib
from Logger import Logger


class UserSettings(object):
    def __init__(self):
        self.userdistroid = distro.id()
        self.userdistroversion = distro.major_version().lower()
        self.usercodename = distro.codename().lower()
        if self.usercodename == "etap":
            self.usercodename = self.usercodename + self.userdistroversion
        self.userdistro = ", ".join(filter(bool, (distro.name(), distro.version(), distro.codename())))

        self.username = GLib.get_user_name()
        self.user_real_name = GLib.get_real_name()

        if self.user_real_name == "" or self.user_real_name == "Unknown":
            self.user_real_name = self.username


        self.cachedir = "{}/pardus/pardus-software/".format(GLib.get_user_cache_dir())
        self.configdir = "{}/pardus/pardus-software/".format(GLib.get_user_config_dir())

        self.apps_dir = self.cachedir + "apps/"
        self.cats_dir = self.cachedir + "cats/"
        self.home_dir = self.cachedir + "home/"
        self.icons_dir = self.cachedir + "icons/"
        self.images_dir = self.cachedir + "images/"
        self.app_icons_dir = self.icons_dir + "app-icons"
        self.cat_icons_dir = self.icons_dir + "cat-icons"
        self.slider_images_dir = self.images_dir + "slider-images"
        self.editor_images_dir = self.images_dir + "editor-images"

        self.icons_archive = "icons.tar.gz"
        self.images_archive = "images.tar.gz"
        self.apps_archive = "apps.tar.gz"
        self.cats_archive = "cats.tar.gz"
        self.home_archive = "home.tar.gz"
        self.apps_file = "apps.json"
        self.cats_file = "cats.json"
        self.home_file = "home.json"

        self.configfile = "settings.ini"
        self.config = configparser.ConfigParser()
        self.config_ea = None
        self.config_saa = None
        self.config_sgc = None
        self.config_udt = None
        self.config_aptup = None
        self.config_lastaptup = None
        self.config_forceaptuptime = None

        self.Logger = Logger(__name__)

    def createDefaultConfig(self, force=False):
        self.config['MAIN'] = {'Animations': 'yes',
                                  'OnlyAvailableApps': 'yes',
                                  'GnomeComments': 'yes',
                                  'DarkTheme': 'no',
                                  'AutoAptUpdate': 'yes',
                                  'LastAutoAptUpdate': '0',
                                  'ForceAutoAptUpdateTime': '0'}

        if not Path.is_file(Path(self.configdir + self.configfile)) or force:
            if self.createDir(self.configdir):
                with open(self.configdir + self.configfile, "w") as cf:
                    self.config.write(cf)

    def readConfig(self):
        try:
            self.Logger.info("in readconfig")
            self.config.read(self.configdir + self.configfile)
            self.config_ea = self.config.getboolean('MAIN', 'Animations')
            self.config_saa = self.config.getboolean('MAIN', 'OnlyAvailableApps')
            self.config_sgc = self.config.getboolean('MAIN', 'GnomeComments')
            self.config_udt = self.config.getboolean('MAIN', 'DarkTheme')
            self.config_aptup = self.config.getboolean('MAIN', 'AutoAptUpdate')
            self.config_lastaptup = self.config.getint('MAIN', 'LastAutoAptUpdate')
            self.config_forceaptuptime = self.config.getint('MAIN', 'ForceAutoAptUpdateTime')
        except Exception as e:
            self.Logger.warning("user config read error ! Trying create defaults")
            self.Logger.exception("{}".format(e))
            # if not read; try to create defaults
            self.config_ea = True
            self.config_saa = True
            self.config_sgc = True
            self.config_udt = False
            self.config_aptup = True
            self.config_lastaptup = 0
            self.config_forceaptuptime = 0
            try:
                self.createDefaultConfig(force=True)
            except Exception as e:
                self.Logger.warning("self.createDefaultConfig(force=True)")
                self.Logger.exception("{}".format(e))

    def writeConfig(self, **kwargs):
        """
        writeConfig(Animations=True)
        writeConfig(OnlyAvailableApps=True)
        writeConfig(DarkTheme=False)
        """

        current = {
            'Animations': self.config_ea,
            'OnlyAvailableApps': self.config_saa,
            'GnomeComments': self.config_sgc,
            'DarkTheme': self.config_udt,
            'AutoAptUpdate': self.config_aptup,
            'LastAutoAptUpdate': self.config_lastaptup,
            'ForceAutoAptUpdateTime': self.config_forceaptuptime
        }

        for key, value in kwargs.items():
            if key in current:
                current[key] = value
            else:
                self.Logger.warning(f"Unknown config key: {key}")

        self.config['MAIN'] = {
            'Animations': current['Animations'],
            'OnlyAvailableApps': current['OnlyAvailableApps'],
            'GnomeComments': current['GnomeComments'],
            'DarkTheme': current['DarkTheme'],
            'AutoAptUpdate': current['AutoAptUpdate'],
            'LastAutoAptUpdate': current['LastAutoAptUpdate'],
            'ForceAutoAptUpdateTime': current['ForceAutoAptUpdateTime']
        }

        config_path = self.configdir + self.configfile
        if self.createDir(self.configdir):
            try:
                with open(config_path, "w") as cf:
                    self.config.write(cf)
                    return True
            except Exception as e:
                self.Logger.exception(f"writeConfig error: {e}")
                return False
        return False

    def createDir(self, dir):
        try:
            Path(dir).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.Logger.warning("{} : {}".format("mkdir error", dir))
            self.Logger.exception("{}".format(e))
            return False
