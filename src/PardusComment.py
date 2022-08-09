#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: fatih
"""

import gi, json
from gi.repository import GLib, Gio, Soup

gi.require_version("GLib", "2.0")
gi.require_version("Soup", "2.4")


class PardusComment(object):
    def __init__(self):

        self.session = Soup.Session(user_agent="application/json")

    def get(self, method, uri, dic, appname):
        # print("{} : {} {}".format(method, uri, dic))
        message = Soup.Message.new(method, uri)

        if method == "POST":
            message.set_request(
                "Content-type:application/json",
                Soup.MemoryUse.COPY,
                json.dumps(dic).encode("utf-8"),
            )

        message.request_headers.append("Content-type", "application/json")
        self.session.send_async(message, None, self.on_finished, message, appname)

    def on_finished(self, session, result, message, appname):
        try:
            input_stream = session.send_finish(result)
        except GLib.Error as error:
            print(f"PardusComment stream Error: {error.domain}, {error.message}")
            self.pComment(False, None)
            return False
        status_code = message.status_code
        print(f"pardus comments server status code : {status_code}")
        if input_stream:
            data_input_stream = Gio.DataInputStream.new(input_stream)
            lines = []
            while True:
                line, length = data_input_stream.read_line_utf8()
                if line is None:
                    print("Finished")
                    break
                else:
                    lines.append(line)
            if status_code == 200:
                content = "".join(lines)
                self.pComment(True, json.loads(content), appname)
            else:
                self.pComment(False, None)
        input_stream.close_async(GLib.PRIORITY_LOW, None, self._close_stream, None)

    def _close_stream(self, session, result, data):
        try:
            session.close_finish(result)
        except GLib.Error as error:
            print(f"PardusComments Close Error: {error.domain}, {error.message}")

    def control(self, uri):
        message = Soup.Message.new("POST", uri)
        message.request_headers.append("Content-type", "application/json")
        self.session.send_async(message, None, self.on_control_finished, message)

    def on_control_finished(self, session, result, message):
        if message.status_code == Soup.Status.SSL_FAILED:
            self.session.props.ssl_strict = False
        try:
            input_stream = session.send_finish(result)
        except GLib.Error:
            return False

        input_stream.close_async(
            GLib.PRIORITY_LOW, None, self._control_close_stream, None
        )

    def _control_close_stream(self, session, result, data):
        try:
            session.close_finish(result)
        except GLib.Error:
            pass
