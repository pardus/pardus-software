#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: fatih
"""

import json

import gi

gi.require_version("GLib", "2.0")
gi.require_version('Soup', '2.4')
from gi.repository import GLib, Gio, Soup
from Logger import Logger


class GnomeComment(object):
    def __init__(self):

        self.session = Soup.Session(user_agent="application/json")
        self.Logger = Logger(__name__)

    def get(self, method, uri, dic, appname, lang):
        # self.Logger.info("{} : {} {}".format(method, uri, dic))
        message = Soup.Message.new(method, uri)

        if method == "POST":
            message.set_request('Content-type:application/json', Soup.MemoryUse.COPY, json.dumps(dic).encode('utf-8'))

        message.request_headers.append('Content-type', 'application/json')
        self.session.send_async(message, None, self.on_finished, message, appname, lang)

    def on_finished(self, session, result, message, appname, lang):
        try:
            input_stream = session.send_finish(result)
        except GLib.Error as error:
            self.Logger.warning("GnomeComment stream Error: {}, {}".format(error.domain, error.message))
            self.Logger.exception("{}".format(error))
            self.gComment(False, None)  # Send to MainWindow
            return False

        status_code = message.status_code
        self.Logger.info("gnome comments server status code : {}, lang : {}".format(status_code, lang))

        if input_stream:
            data_input_stream = Gio.DataInputStream.new(input_stream)
            lines = list()
            while True:
                line, length = data_input_stream.read_line_utf8()
                if line is None:
                    self.Logger.info("Finished")
                    break
                else:
                    lines.append(line)
            content = "".join(lines)
            if status_code == 200:
                self.gComment(True, json.loads(content), appname, lang)
            else:
                self.gComment(False, None)
        input_stream.close_async(GLib.PRIORITY_LOW, None, self._close_stream, None)

    def _close_stream(self, session, result, data):
        try:
            session.close_finish(result)
        except GLib.Error as error:
            self.Logger.warning("GnomeComments Close Error: {}, {}".format(error.domain, error.message))
            self.Logger.exception("{}".format(error))
