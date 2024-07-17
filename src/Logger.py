#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  5 08:58:53 2022

@author: fatih
"""

import logging
import sys
from pathlib import Path

import gi

gi.require_version("GLib", "2.0")
from gi.repository import GLib


class Logger(object):
    def __init__(self, name):

        logdir = Path.joinpath(Path(GLib.get_user_cache_dir()), Path("pardus-software"))
        if not Path(logdir).exists():
            logdir = Path.joinpath(Path(GLib.get_user_cache_dir()), Path("pardus/pardus-software"))
        logfile = Path.joinpath(logdir, "pardus-software.log")

        loglevel = logging.INFO  # Possible values are {DEBUG, INFO, WARN, ERROR, CRITICAL}

        if not Path.is_dir(Path(logdir)):
            Path(logdir).mkdir(parents=True, exist_ok=True)

        try:
            logging.basicConfig(level=loglevel,
                                format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
                                datefmt="%Y-%m-%d %H:%M:%S", encoding="utf-8",
                                handlers=[logging.FileHandler(logfile), logging.StreamHandler()]
                                )
        except Exception as e:
            print("{} - Logger will be use without utf-8 encoding".format(e))
            logging.basicConfig(level=loglevel,
                                format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
                                datefmt="%Y-%m-%d %H:%M:%S",
                                handlers=[logging.FileHandler(logfile), logging.StreamHandler()]
                                )

        self.logger = logging.getLogger(name)
        self.logger.info("Logger setup completed.")
        self.logger.info("{} is starting.".format(sys.argv[0]))

    def set_logger(self, type):
        self.logger = logging.getLogger(type)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)

    def exception(self, message):
        self.logger.exception(message)
