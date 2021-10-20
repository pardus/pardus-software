#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import os
import subprocess
import sys
import apt_pkg


def main():
    def control_lock():
        apt_pkg.init_system()
        try:
            apt_pkg.pkgsystem_lock()
        except SystemError:
            return False
        apt_pkg.pkgsystem_unlock()
        return True

    def install(packages):
        packagelist = packages.split(" ")
        subprocess.call(["apt", "install", "-yq", "-o", "APT::Status-Fd=2"] + packagelist,
                        env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    def reinstall(debianpackage):
        subprocess.call(["apt", "install", "--reinstall", debianpackage, "-yq", "-o", "APT::Status-Fd=2"],
                        env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    def remove(packages):
        packagelist = packages.split(" ")
        subprocess.call(["apt", "remove", "--purge", "-yq", "-o", "APT::Status-Fd=2"] + packagelist,
                        env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    def downgrade(packagename):
        subprocess.call(["apt", "install", "--allow-downgrades", packagename, "-yq", "-o", "APT::Status-Fd=2"],
                        env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    def update():
        subprocess.call(["apt", "update", "-o", "APT::Status-Fd=2"],
                        env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    def removeresidual(packages):
        packagelist = packages.split(" ")
        subprocess.call(["apt", "remove", "--purge", "-yq", "-o", "APT::Status-Fd=2"] + packagelist,
                        env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    def removeauto():
        subprocess.call(["apt", "autoremove", "-yq", "-o", "APT::Status-Fd=2"],
                        env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    def externalrepo(keyfile, slistfile):
        subprocess.call(["apt-key", "add", keyfile])
        subprocess.call(["mv", slistfile, "/etc/apt/sources.list.d/"])

    if len(sys.argv) > 1:
        if control_lock():
            if sys.argv[1] == "install":
                install(sys.argv[2])
            elif sys.argv[1] == "remove":
                remove(sys.argv[2])
            elif sys.argv[1] == "reinstall":
                reinstall(sys.argv[2])
            elif sys.argv[1] == "downgrade":
                downgrade(sys.argv[2])
            elif sys.argv[1] == "update":
                update()
            elif sys.argv[1] == "removeresidual":
                print(sys.argv[2])
                removeresidual(sys.argv[2])
            elif sys.argv[1] == "removeauto":
                removeauto()
            elif sys.argv[1] == "externalrepo":
                externalrepo(sys.argv[2], sys.argv[3])
                update()
        else:
            print("lock error")
            sys.exit(1)
    else:
        print("no argument passed")


if __name__ == "__main__":
    main()
