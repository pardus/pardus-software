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
            os.makedirs("{}/{}/LC_MESSAGES".format(podir, po.split(".po")[0]), exist_ok=True)
            mo_file = "{}/{}/LC_MESSAGES/{}".format(podir, po.split(".po")[0], "pardus-software.mo")
            msgfmt_cmd = 'msgfmt {} -o {}'.format(podir + "/" + po, mo_file)
            subprocess.call(msgfmt_cmd, shell=True)
            mo.append(("/usr/share/locale/" + po.split(".po")[0] + "/LC_MESSAGES",
                       ["po/" + po.split(".po")[0] + "/LC_MESSAGES/pardus-software.mo"]))
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

data_files = [
                 ("/usr/bin", ["pardus-software"]),
                 ("/usr/share/applications",
                  ["tr.org.pardus.software.desktop",
                   "tr.org.pardus.software-open.desktop"]),
                 ("/usr/share/polkit-1/actions",
                  ["tr.org.pardus.pkexec.pardus-software.policy"]),
                 ("/usr/share/pardus/pardus-software/css",
                  ["css/all.css",
                   "css/base.css"]),
                 ("/usr/share/pardus/pardus-software/images",
                  ["images/rating.svg",
                   "images/rating-unrated.svg",
                   "images/rating-hover-empty.svg",
                   "images/rating-hover-full.svg",
                   "images/rating-0.svg",
                   "images/rating-0-3.svg",
                   "images/rating-0-5.svg",
                   "images/rating-0-8.svg",
                   "images/rating-1.svg"]),
                 ("/usr/share/pardus/pardus-software/ui",
                  ["ui/MainWindow.glade"]),
                 ("/usr/share/pardus/pardus-software/src",
                  ["src/Actions.py",
                   "src/AppDetail.py",
                   "src/AppImage.py",
                   "src/AppRequest.py",
                   "src/AutoAptUpdate.py",
                   "src/CellRendererButton.py",
                   "src/GnomeComment.py",
                   "src/GnomeRatingServer.py",
                   "src/Group.py",
                   "src/Main.py",
                   "src/MainWindow.py",
                   "src/Package.py",
                   "src/PardusComment.py",
                   "src/Server.py",
                   "src/SysActions.py",
                   "src/UserSettings.py",
                   "src/__version__"]),
                 ("/usr/share/icons/hicolor/scalable/apps/",
                  ["images/pardus-software.svg"]),
                 ("/usr/share/mime/packages/",
                  ["pardus-software.xml"]),
                 ("/var/lib/polkit-1/localauthority/50-local.d/",
                  ["pardus-software-group.pkla"]),
                 ("/etc/pardus/",
                  ["pardus-software.conf"])
             ] + create_mo_files()

setup(
    name="Pardus Software",
    version=version,
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
