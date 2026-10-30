#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import os
import tempfile
import time
from hashlib import md5

import gi

gi.require_version("GLib", "2.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GLib, GdkPixbuf, Gio
from Logger import Logger


class AppImage(object):
    def __init__(self):

        self.Logger = Logger(__name__)
        self.cache_dir = "{}/pardus/pardus-software/screenshots/".format(GLib.get_user_cache_dir())
        self.cache_max_age = 30 * 24 * 60 * 60

    def cache_path(self, uri):
        return self.cache_dir + md5(uri.encode("utf-8")).hexdigest()

    def get_image(self, uri, app_name):
        cache_path = self.cache_path(uri)
        try:
            cached = time.time() - os.path.getmtime(cache_path) < self.cache_max_age
        except OSError:
            cached = False

        if cached:
            img_file = Gio.File.new_for_path(cache_path)
            img_file.read_async(GLib.PRIORITY_LOW, None, self._open_stream, uri, app_name, None)
        else:
            img_file = Gio.File.new_for_uri(uri)
            img_file.load_contents_async(None, self._downloaded, uri, app_name)

    def _downloaded(self, img_file, result, uri, app_name):
        try:
            success, data, etag = img_file.load_contents_finish(result)
        except GLib.Error as error:
            self.Logger.warning("_downloaded Error: {}, {}".format(error.domain, error.message))
            self.Logger.exception("{}".format(error))
            self.app_image_from_server(False)  # Send to MainWindow
            return False

        stream = Gio.MemoryInputStream.new_from_bytes(GLib.Bytes.new(data))
        GdkPixbuf.Pixbuf.new_from_stream_async(stream, None, self._pixbuf_loaded, uri, app_name, data)

    def _open_stream(self, img_file, result, uri, app_name, data):
        try:
            stream = img_file.read_finish(result)
        except GLib.Error as error:
            self.Logger.warning("_open_stream Error: {}, {}".format(error.domain, error.message))
            self.Logger.exception("{}".format(error))
            self.app_image_from_server(False)  # Send to MainWindow
            return False

        GdkPixbuf.Pixbuf.new_from_stream_async(stream, None, self._pixbuf_loaded, uri, app_name, data)

    def _pixbuf_loaded(self, stream, result, uri, app_name, data):
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_stream_finish(result)
        except GLib.Error as error:
            self.Logger.warning("_pixbuf_loaded Error: {}, {}".format(error.domain, error.message))
            self.Logger.exception("{}".format(error))
            if data is None:
                # a broken file in the cache, the next visit downloads it again
                self.remove_from_cache(uri)
            self.app_image_from_server(False)  # Send to MainWindow
            return False

        stream.close_async(GLib.PRIORITY_LOW, None, self._close_stream, None)

        # only an image that decoded goes to the cache
        if data is not None:
            self.save_to_cache(uri, data)

        self.app_image_from_server(True, pixbuf, uri, app_name)  # Send to MainWindow

    def save_to_cache(self, uri, data):
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            file_descriptor, temp_path = tempfile.mkstemp(dir=self.cache_dir)
            with os.fdopen(file_descriptor, "wb") as cache_file:
                cache_file.write(data)
            os.replace(temp_path, self.cache_path(uri))
        except OSError as error:
            self.Logger.warning("save_to_cache Error: {}".format(error))

    def remove_from_cache(self, uri):
        try:
            os.unlink(self.cache_path(uri))
        except OSError:
            pass

    def _close_stream(self, stream, result, data):
        try:
            stream.close_finish(result)
        except GLib.Error as error:
            self.Logger.warning("Error: {}, {}".format(error.domain, error.message))
            self.Logger.exception("{}".format(error))
