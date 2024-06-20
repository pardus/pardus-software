#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import gi

gi.require_version("GLib", "2.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GLib, GdkPixbuf, Gio
from Logger import Logger


class AppImage(object):
    def __init__(self):

        self.imgcache = {}
        self.Logger = Logger(__name__)

    def fetch(self, uri, fileuri, i):
        url = uri + fileuri
        img_file = Gio.File.new_for_uri(url)
        img_file.read_async(GLib.PRIORITY_LOW, None, self._open_stream, fileuri + i)

    def _open_stream(self, img_file, result, fileuri):
        try:
            stream = img_file.read_finish(result)
        except GLib.Error as error:
            self.Logger.warning("_open_stream Error: {}, {}".format(error.domain, error.message))
            self.Logger.exception("{}".format(error))
            self.Pixbuf(False, None, None)  # Send to MainWindow
            return False

        GdkPixbuf.Pixbuf.new_from_stream_async(stream, None, self._pixbuf_loaded, fileuri)

    def _pixbuf_loaded(self, stream, result, data):
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_stream_finish(result)
        except GLib.Error as error:
            self.Logger.warning("_pixbuf_loaded Error: {}, {}".format(error.domain, error.message))
            self.Logger.exception("{}".format(error))
            self.Pixbuf(False, None, None)  # Send to MainWindow
            return False

        stream.close_async(GLib.PRIORITY_LOW, None, self._close_stream, None)

        self.Pixbuf(True, pixbuf, data)  # Send to MainWindow

        self.imgcache[data] = pixbuf

    def _close_stream(self, stream, result, data):
        try:
            stream.close_finish(result)
        except GLib.Error as error:
            self.Logger.warning("Error: {}, {}".format(error.domain, error.message))
            self.Logger.exception("{}".format(error))
