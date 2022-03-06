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


class AppRequest(object):
    def __init__(self):

        self.session = Soup.Session(user_agent="application/json")

    def send(self, method, uri, dic):
        # print("{} : {} {}".format(method, uri, dic))
        message = Soup.Message.new(method, uri)

        if method == "POST":
            message.set_request('Content-type:application/json', Soup.MemoryUse.COPY, json.dumps(dic).encode('utf-8'))

        message.request_headers.append('Content-type', 'application/json')
        self.session.send_async(message, None, self.on_finished, message)

    def on_finished(self, session, result, message):
        try:
            input_stream = session.send_finish(result)
        except GLib.Error as error:
            print("AppRequest stream Error: {}, {}".format(error.domain, error.message))
            self.Request(False, None)  # Send to MainWindow
            return False

        status_code = message.status_code
        # print(status_code)

        if input_stream:
            data_input_stream = Gio.DataInputStream.new(input_stream)
            line, length = data_input_stream.read_line_utf8()

            self.Request(True, json.loads(line))

        input_stream.close_async(GLib.PRIORITY_LOW, None, self._close_stream, None)

    def _close_stream(self, session, result, data):
        try:
            session.close_finish(result)
        except GLib.Error as error:
            print("AppRequest Close Error: {}, {}".format(error.domain, error.message))
