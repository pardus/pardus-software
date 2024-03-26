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


class PardusComment(object):
    def __init__(self):

        self.session = Soup.Session(user_agent="application/json")
        self.Logger = Logger(__name__)

    def get(self, method, uri, dic, appname):
        # self.Logger.info("{} : {} {}".format(method, uri, dic))
        message = Soup.Message.new(method, uri)

        if method == "POST":
            message.set_request('Content-type:application/json', Soup.MemoryUse.COPY, json.dumps(dic).encode('utf-8'))

        message.request_headers.append('Content-type', 'application/json')
        self.session.send_async(message, None, self.on_finished, message, appname)

    def on_finished(self, session, result, message, appname):
        try:
            input_stream = session.send_finish(result)
        except GLib.Error as error:
            self.Logger.warning("PardusComment stream Error: {}, {}".format(error.domain, error.message))
            self.pComment(False, None)  # Send to MainWindow
            return False

        status_code = message.status_code
        self.Logger.info("pardus comments server status code : {}".format(status_code))

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
                self.pComment(True, json.loads(content), appname)
            else:
                self.pComment(False, None)
        input_stream.close_async(GLib.PRIORITY_LOW, None, self._close_stream, None)

    def _close_stream(self, session, result, data):
        try:
            session.close_finish(result)
        except GLib.Error as error:
            self.Logger.warning("PardusComments Close Error: {}, {}".format(error.domain, error.message))
            self.Logger.exception("{}".format(error))

    def control(self, uri):
        message = Soup.Message.new("POST", uri)
        message.request_headers.append('Content-type', 'application/json')
        self.session.send_async(message, None, self.on_control_finished, message)

    def on_control_finished(self, session, result, message):
        if message.status_code == Soup.Status.SSL_FAILED:
            self.session.props.ssl_strict = False
        try:
            input_stream = session.send_finish(result)
        except GLib.Error:
            return False

        input_stream.close_async(GLib.PRIORITY_LOW, None, self._control_close_stream, None)

    def _control_close_stream(self, session, result, data):
        try:
            session.close_finish(result)
        except GLib.Error:
            pass
