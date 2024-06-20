#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 23:59:23 2024

@author: fatih
"""
import os
import subprocess

from Logger import Logger


class Utils(object):
    def __init__(self):

        self.de_version_command = {"xfce": ["xfce4-session", "--version"],
                                   "gnome": ["gnome-shell", "--version"],
                                   "cinnamon": ["cinnamon", "--version"],
                                   "mate": ["mate-about", "--version"],
                                   "kde": ["plasmashell", "--version"],
                                   "lxqt": ["lxqt-about", "--version"],
                                   "budgie": ["budgie-desktop", "--version"]}

        self.Logger = Logger(__name__)

    def get_desktop_env(self):
        current_desktop = "{}".format(os.environ.get('XDG_CURRENT_DESKTOP'))
        return current_desktop

    def get_desktop_env_version(self, desktop):
        version = ""
        desktop = "{}".format(desktop.lower())
        try:
            if "xfce" in desktop:
                output = (subprocess.run(self.de_version_command["xfce"], shell=False, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)).stdout.decode().strip()
                for line in output.split("\n"):
                    if line.startswith("xfce4-session "):
                        version = line.split(" ")[-1].strip("()")
                        break

            elif "gnome" in desktop:
                output = (subprocess.run(self.de_version_command["gnome"], shell=False, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)).stdout.decode().strip()
                for line in output.split("\n"):
                    if "GNOME Shell" in line:
                        version = line.split(" ")[-1]

            elif "cinnamon" in desktop:
                output = (subprocess.run(self.de_version_command["cinnamon"], shell=False, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)).stdout.decode().strip()
                version = output.split(" ")[-1]

            elif "mate" in desktop:
                output = (subprocess.run(self.de_version_command["mate"], shell=False, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)).stdout.decode().strip()
                version = output.split(" ")[-1]

            elif "kde" in desktop:
                output = (subprocess.run(self.de_version_command["kde"], shell=False, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)).stdout.decode().strip()
                version = output.split(" ")[-1]

            elif "lxqt" in desktop:
                output = (subprocess.run(self.de_version_command["lxqt"], shell=False, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)).stdout.decode().strip()
                for line in output:
                    if "liblxqt" in line:
                        version = line.split()[1].strip()

            elif "budgie" in desktop:
                output = (subprocess.run(self.de_version_command["budgie"], shell=False, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)).stdout.decode().strip()
                version = output.split("\n")[0].strip().split(" ")[-1]
        except Exception as e:
            self.Logger.warning("Error on get_desktop_env_version")
            self.Logger.exception("{}".format(e))

        return version

    def get_session_type(self):
        session = "{}".format(os.environ.get('XDG_SESSION_TYPE')).capitalize()
        return session

    def get_path_size(self, path):
        total = 0
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += self.get_path_size(entry.path)
        return total
