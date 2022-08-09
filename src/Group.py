#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import subprocess
import sys


def main():
    def addtogroup(user):
        subprocess.call(["adduser", user, "pardus-software"])

    def delfromgroup(user):
        subprocess.call(["deluser", user, "pardus-software"])

    if len(sys.argv) > 1:
        if sys.argv[1] == "add":
            addtogroup(sys.argv[2])
        elif sys.argv[1] == "del":
            delfromgroup(sys.argv[2])
    else:
        print("no argument passed")


if __name__ == "__main__":
    main()
