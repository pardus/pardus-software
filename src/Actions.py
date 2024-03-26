#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import os
import subprocess
import sys

import apt
import apt_pkg
import psutil


def main():
    def control_lock():
        apt_pkg.init_system()
        try:
            apt_pkg.pkgsystem_lock()
        except SystemError as e:
            print(e, file=sys.stderr)
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

    def enable_i386_install(packages):
        print("pardus-software-i386-start", file=sys.stderr)
        subprocess.call(["dpkg", "--add-architecture", "i386"])
        try:
            cache = apt.Cache()
            cache.update()
            cache.open()
        except Exception as e:
            print(str(e))
            print("{}".format(e), file=sys.stderr)
            update()
        install(packages)

    def kill(pid):
        print("kill function working for: {} pid".format(pid))
        kill_dic = {}
        parent = psutil.Process(int(pid))
        for child in parent.children(recursive=True):
            kill_dic[child.name()] = child.pid

        keys = kill_dic.keys()
        if "dpkg" in keys or "dpkg-deb" in keys:
            print("You can't cancel the operation because download completed and install in progress.")
        elif "http" in keys or "https" in keys:
            print("download operation is cancelling")
            for child_name, child_pid in kill_dic.items():
                print("child killing!!! name: {} - pid: {}".format(child_name, child_pid))
                psutil.Process(child_pid).kill()
            print("parent killing!!! name: {} - pid: {}".format(parent.name(), parent.pid))
            parent.kill()
        else:
            print("There is something wrong.")
            for child_name, child_pid in kill_dic.items():
                print("child, name: {} - pid: {}".format(child_name, child_pid))

    if len(sys.argv) > 1:
        if sys.argv[1] == "kill":
            kill(sys.argv[2])
            return
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
            elif sys.argv[1] == "enablei386andinstall":
                enable_i386_install(sys.argv[2])
        else:
            print("lock error")
            sys.exit(1)
    else:
        print("no argument passed")


if __name__ == "__main__":
    main()
