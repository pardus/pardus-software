#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import requests


class Server(object):
    def __init__(self):
        serverurl = "http://192.168.1.13"
        server = serverurl + "/api/v2/apps/"
        self.connection = True
        self.scode = 0
        self.applist = []
        try:
            request = requests.get(server)
        except Exception as e:
            print(e)
            print("Connection problem")
            self.connection = False

        if self.connection:
            self.scode = request.status_code
            if self.scode == 200:
                print("Connection successful")
                self.applist = request.json()["app-list"]
            else:
                self.connection = False
