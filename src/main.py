#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import gi
from MainWindow import MainWindow

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="tr.org.pardus.software-center", **kwargs)
        self.window = None

    def do_activate(self):
        self.window = MainWindow(self)


if __name__ == "__main__":
    app = Application()
    app.run()
