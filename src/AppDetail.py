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


class AppDetail(object):
    def __init__(self):

        self.session = Soup.Session(user_agent="application/json")

    def get(self, method, uri, dic, appname=""):
        # print("{} : {} {}".format(method, uri, dic))
        message = Soup.Message.new(method, uri)

        if method == "POST":
            message.set_request('Content-type:application/json', Soup.MemoryUse.COPY, json.dumps(dic).encode('utf-8'))

        message.request_headers.append('Content-type', 'application/json')
        self.session.send_async(message, None, self.on_finished, message, appname)

    def on_finished(self, session, result, message, appname):
        try:
            input_stream = session.send_finish(result)
        except GLib.Error as error:
            if message.status_code == Soup.Status.SSL_FAILED:
                self.session.props.ssl_strict = False
            print("AppDetail stream Error: {}, {}".format(error.domain, error.message))
            self.Detail(False, None)  # Send to MainWindow
            return False

        status_code = message.status_code
        # print(status_code)

        if input_stream:
            data_input_stream = Gio.DataInputStream.new(input_stream)
            line, length = data_input_stream.read_line_utf8()

            self.Detail(True, json.loads(line), appname)

        input_stream.close_async(GLib.PRIORITY_LOW, None, self._close_stream, None)

    def _close_stream(self, session, result, data):
        try:
            session.close_finish(result)
        except GLib.Error as error:
            print("AppDetail Close Error: {}, {}".format(error.domain, error.message))

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