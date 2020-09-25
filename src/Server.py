#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import requests


class Server(object):
    def __init__(self):
        server = "http://store.pardus.org.tr:5000/api/v1/apps/"

        appsrequest = requests.get(server)

        print("apps getted")

        print(appsrequest.status_code)

        app = appsrequest.json()["app-list"][0]["name"]

        print(app)
