#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import os
import subprocess
import sys
import pwd
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

    def remove(packages):
        packagelist = packages.split(" ")
        subprocess.call(["apt", "remove", "--purge", "-yq", "-o", "APT::Status-Fd=2"] + packagelist,
                        env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    def upgrade(packages):
        packagelist = packages.split(" ")
        subprocess.call(["apt", "install", "--upgrade", "-yq", "-o", "APT::Status-Fd=2"] + packagelist,
                        env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    def update():
        subprocess.call(["apt", "update", "-o", "APT::Status-Fd=2"],
                        env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

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

        if int(pid) < 100:
            print(f"kill func: cannot kill, pid: {pid}")
            return

        parent = psutil.Process(int(pid))

        parent_cmdline = "".join(parent.cmdline())
        if "pardus-software/src/Actions.py" not in parent_cmdline:
            print("kill func: not pardus-software process")
            return

        install_phase = any("dpkg" in child.exe() for child in parent.children(recursive=True))
        print(f"Install phase: {install_phase}")

        if install_phase:
            print("You can't cancel the operation because download completed and install in progress.")
            return

        kill_dic = {}
        for child in parent.children(recursive=True):
            try:
                child_name = child.name()
                child_pid = child.pid
                child_exe = child.exe()
                child_uid = child.uids().real
                child_user = pwd.getpwuid(child_uid).pw_name
                child_cmdline = " ".join(child.cmdline())
                print(f"Checking child: {child_name} PID={child_pid} exe={child_exe} user={child_user} cmdline={child_cmdline}")

                # apt child
                if child_name == "apt" and child_exe == "/usr/bin/apt" and "apt" in child_cmdline:
                    print(f"Adding apt child to kill list: {child_name} PID={child_pid}")
                    kill_dic[child_pid] = child_name

                # apt download child
                elif child_user == "_apt" and \
                     (child_exe.startswith("/usr/lib/apt/methods")) and \
                     (child_cmdline.startswith("/usr/lib/apt/methods")):
                    print(f"Adding apt download child to kill list: {child_name} PID={child_pid}")
                    kill_dic[child_pid] = child_name

            except Exception as e:
                print(f"Error reading child PID={child.pid}: {e}")
                continue

        if kill_dic:
            print("Download operation is cancelling")
            for child_pid, child_name in kill_dic.items():
                print(f"child killing: name: {child_name} - pid: {child_pid}")
                psutil.Process(child_pid).kill()
            print(f"parent killing name: {parent.name()} - pid: {parent.pid}")
            parent.kill()
        else:
            print("No apt/_apt download child found. Nothing to kill.")

    if len(sys.argv) > 1:
        if sys.argv[1] == "kill":
            kill(sys.argv[2])
            return
        if control_lock():
            if sys.argv[1] == "install":
                install(sys.argv[2])
            elif sys.argv[1] == "remove":
                remove(sys.argv[2])
            elif sys.argv[1] == "upgrade":
                upgrade(sys.argv[2])
            elif sys.argv[1] == "update":
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
