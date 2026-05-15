#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import subprocess

from setuptools import setup, find_packages


def create_mo_files():
    podir = "po"
    mo = []
    for po in os.listdir(podir):
        if po.endswith(".po"):
            lang = po[:-3]
            local_dir = os.path.join(podir, lang, "LC_MESSAGES")
            os.makedirs(local_dir, exist_ok=True)
            mo_file = os.path.join(local_dir, "pardus-software.mo")
            subprocess.call(["msgfmt", os.path.join(podir, po), "-o", mo_file])
            mo.append((f"/usr/share/locale/{lang}/LC_MESSAGES", [mo_file]))
    return mo


changelog = "debian/changelog"
version = "0.1.0"
if os.path.exists(changelog):
    head = open(changelog).readline()
    try:
        version = head.split("(")[1].split(")")[0]
    except:
        print("debian/changelog format is wrong for get version")
    f = open("src/__version__", "w")
    f.write(version)
    f.close()

def pythonic_version(version):
    return (version
        .replace("~alpha", "a")
        .replace("~beta", "b")
        .replace("~rc", "rc")
        .replace("~dev", ".dev")
    )

data_files = [
                 ("/usr/bin", ["pardus-software"]),
                 ("/usr/share/applications",
                  ["tr.org.pardus.software.desktop",
                   "tr.org.pardus.software-open.desktop"]),
                 ("/usr/share/polkit-1/actions",
                  ["tr.org.pardus.pkexec.pardus-software.policy"]),
                 ("/usr/share/pardus/pardus-software/css",
                  ["css/adwaita.css",
                   "css/base.css"]),
                 ("/usr/share/pardus/pardus-software/ui",
                  ["ui/MainWindow.glade"]),
                 ("/usr/share/pardus/pardus-software/src",
                  ["src/Actions.py",
                   "src/AppDetail.py",
                   "src/AppImage.py",
                   "src/AppRequest.py",
                   "src/AutoAptUpdate.py",
                   "src/GnomeComment.py",
                   "src/GnomeRatingServer.py",
                   "src/Group.py",
                   "src/Logger.py",
                   "src/Main.py",
                   "src/MainWindow.py",
                   "src/Package.py",
                   "src/PardusComment.py",
                   "src/Server.py",
                   "src/SysActions.py",
                   "src/UserSettings.py",
                   "src/Utils.py",
                   "src/__version__"]),
                 ("/usr/share/icons/hicolor/scalable/apps/",
                  ["images/pardus-software.svg"]),
                 ("/usr/share/mime/packages/",
                  ["pardus-software.xml"]),
                 ("/usr/share/polkit-1/rules.d/",
                  ["pardus-software-group.rules"]),
                 ("/etc/pardus/",
                  ["pardus-software.conf"])
             ] + create_mo_files()

setup(
    name="Pardus Software",
    version=pythonic_version(version),
    packages=find_packages(),
    scripts=["pardus-software"],
    install_requires=["PyGObject"],
    data_files=data_files,
    author="Fatih Altun",
    author_email="fatih.altun@pardus.org.tr",
    description="Pardus Software Center",
    license="GPLv3",
    keywords="software center",
    url="https://www.pardus.org.tr",
)
