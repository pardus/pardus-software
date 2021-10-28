#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import gi, json

gi.require_version("GLib", "2.0")
gi.require_version('Soup', '2.4')
from gi.repository import GLib, Gio, Soup


class GnomeRatingServer(object):

    def __init__(self):

        pass

    def get(self):

        ratings_file = Gio.File.new_for_uri("https://odrs.gnome.org/1.0/reviews/api/ratings")
        ratings_file.load_contents_async(None, self._open_stream)

    def _open_stream(self, ratings_file, result):
        try:
            success, data, etag = ratings_file.load_contents_finish(result)
        except GLib.Error as error:
            print("GnomeRatingServer _open_stream Error: {}, {}".format(error.domain, error.message))
            self.gRatingServer(False, None)  # Send to MainWindow
            return False

        if success:
            try:
                self.gRatingServer(True, json.loads(data))
            except:
                self.gRatingServer(False, None)
        else:
            self.gRatingServer(False, None)
