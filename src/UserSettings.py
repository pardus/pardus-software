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
        self.user_distro_version = distro.major_version().lower()
        self.user_codename = distro.codename().lower()
        if self.user_codename == "etap":
            self.user_codename += self.user_distro_version
        self.user_distro = ", ".join(filter(bool, (distro.name(), distro.version(), distro.codename())))

        self.user_name = GLib.get_user_name()
        self.user_real_name = GLib.get_real_name()

        if not self.user_real_name or self.user_real_name == "Unknown":
            self.user_real_name = self.user_name

        self.cache_dir = "{}/pardus/pardus-software/".format(GLib.get_user_cache_dir())
        self.config_dir = "{}/pardus/pardus-software/".format(GLib.get_user_config_dir())

        self.apps_dir = self.cache_dir + "apps/"
        self.cats_dir = self.cache_dir + "cats/"
        self.home_dir = self.cache_dir + "home/"
        self.icons_dir = self.cache_dir + "icons/"
        self.images_dir = self.cache_dir + "images/"
        self.app_icons_dir = self.icons_dir + "app-icons"
        self.cat_icons_dir = self.icons_dir + "cat-icons"
        self.slider_images_dir = self.images_dir + "slider-images"
        self.editor_images_dir = self.images_dir + "editor-images"

        self.icons_archive = "icons.tar.gz"
        self.images_archive = "images.tar.gz"
        self.cats_archive = "cats.tar.gz"
        self.apps_archive = "apps.tar.gz"
        self.home_archive = "home.tar.gz"
        self.apps_file = "apps.json"
        self.cats_file = "cats.json"
        self.home_file = "home.json"

        self.configfile = "settings.ini"
        self.config = configparser.ConfigParser()
        self.config_animations = None
        self.config_only_available = None
        self.config_gnome_comments = None
        self.config_dark_theme = None
        self.config_auto_apt_update = None
        self.config_last_apt_update = None
        self.config_force_apt_update_time = None

        self.Logger = Logger(__name__)

    def create_default_config(self, force=False):
        self.config['MAIN'] = {
            'Animations': 'yes',
            'OnlyAvailableApps': 'yes',
            'GnomeComments': 'yes',
            'DarkTheme': 'no',
            'AutoAptUpdate': 'yes',
            'LastAutoAptUpdate': '0',
            'ForceAutoAptUpdateTime': '0'
        }

        if not Path.is_file(Path(self.config_dir + self.configfile)) or force:
            if self.create_dir(self.config_dir):
                with open(self.config_dir + self.configfile, "w") as cf:
                    self.config.write(cf)

    def read_config(self):
        try:
            self.Logger.info("in readconfig")
            self.config.read(self.config_dir + self.configfile)
            self.config_animations = self.config.getboolean('MAIN', 'Animations')
            self.config_only_available = self.config.getboolean('MAIN', 'OnlyAvailableApps')
            self.config_gnome_comments = self.config.getboolean('MAIN', 'GnomeComments')
            self.config_dark_theme = self.config.getboolean('MAIN', 'DarkTheme')
            self.config_auto_apt_update = self.config.getboolean('MAIN', 'AutoAptUpdate')
            self.config_last_apt_update = self.config.getint('MAIN', 'LastAutoAptUpdate')
            self.config_force_apt_update_time = self.config.getint('MAIN', 'ForceAutoAptUpdateTime')
        except Exception as e:
            self.Logger.warning("user config read error ! Trying create defaults")
            self.Logger.exception("{}".format(e))
            # if not read; try to create defaults
            self.config_animations = True
            self.config_only_available = True
            self.config_gnome_comments = True
            self.config_dark_theme = False
            self.config_auto_apt_update = True
            self.config_last_apt_update = 0
            self.config_force_apt_update_time = 0
            try:
                self.create_default_config(force=True)
            except Exception as e:
                self.Logger.warning("self.createDefaultConfig(force=True)")
                self.Logger.exception("{}".format(e))

    def write_config(self, **kwargs):
        """
        writeConfig(Animations=True)
        writeConfig(OnlyAvailableApps=True)
        writeConfig(DarkTheme=False)
        """

        current = {
            'Animations': self.config_animations,
            'OnlyAvailableApps': self.config_only_available,
            'GnomeComments': self.config_gnome_comments,
            'DarkTheme': self.config_dark_theme,
            'AutoAptUpdate': self.config_auto_apt_update,
            'LastAutoAptUpdate': self.config_last_apt_update,
            'ForceAutoAptUpdateTime': self.config_force_apt_update_time
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

        config_path = self.config_dir + self.configfile
        if self.create_dir(self.config_dir):
            try:
                with open(config_path, "w") as cf:
                    self.config.write(cf)
                    return True
            except Exception as e:
                self.Logger.exception(f"writeConfig error: {e}")
                return False
        return False

    def create_dir(self, dir):
        try:
            Path(dir).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.Logger.warning("{} : {}".format("mkdir error", dir))
            self.Logger.exception("{}".format(e))
            return False
