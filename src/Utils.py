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
        self.de_version_command = {
            "xfce": ["xfce4-session", "--version"],
            "gnome": ["gnome-shell", "--version"],
            "cinnamon": ["cinnamon", "--version"],
            "mate": ["mate-about", "--version"],
            "kde": ["plasmashell", "--version"],
            "lxqt": ["lxqt-about", "--version"],
            "budgie": ["budgie-desktop", "--version"]
        }
        self.Logger = Logger(__name__)

    def get_desktop_env(self):
        return os.environ.get('XDG_CURRENT_DESKTOP', '')

    def get_desktop_env_version(self, desktop):
        desktop_key = next(
            (item for item in str(desktop).lower().split(":")
             if item in self.de_version_command),
            None
        )

        if not desktop_key:
            return ""

        try:
            result = subprocess.run(
                self.de_version_command[desktop_key],
                capture_output=True,
                text=True,
                check=False
            )

            output = result.stdout.strip()
            if not output:
                return ""

            if desktop_key == "xfce":
                for line in output.splitlines():
                    if line.startswith("xfce4-session "):
                        return line.split()[-1].strip("()")

            elif desktop_key == "gnome":
                for line in output.splitlines():
                    if "GNOME Shell" in line:
                        return line.split()[-1]

            elif desktop_key in ("cinnamon", "mate", "kde"):
                return output.split()[-1]

            elif desktop_key == "lxqt":
                for line in output.splitlines():
                    if "liblxqt" in line:
                        return line.split()[1].strip()

            elif desktop_key == "budgie":
                return output.splitlines()[0].strip().split()[-1]

        except Exception as e:
            self.Logger.warning("Error on get_desktop_env_version")
            self.Logger.exception("{}".format(e))

        return ""

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
