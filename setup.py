#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from setuptools import setup, find_packages
import os, subprocess


def create_mo_files():
    podir = "po"
    mo = []
    for po in os.listdir(podir):
        if po.endswith(".po"):
            os.makedirs(f'{podir}/{po.split(".po")[0]}/LC_MESSAGES', exist_ok=True)
            mo_file = f'{podir}/{po.split(".po")[0]}/LC_MESSAGES/pardus-software.mo'
            msgfmt_cmd = f"msgfmt {podir}/{po} -o {mo_file}"
            subprocess.call(msgfmt_cmd, shell=True)
            mo.append(
                (
                    "/usr/share/locale/" + po.split(".po")[0] + "/LC_MESSAGES",
                    ["po/" + po.split(".po")[0] + "/LC_MESSAGES/pardus-software.mo"],
                )
            )
    return mo


changelog = "debian/changelog"
if os.path.exists(changelog):
    head = open(changelog).readline()
    try:
        version = head.split("(")[1].split(")")[0]
    except:
        print("debian/changelog format is wrong for get version")
        version = ""
    with open("src/__version__", "w") as f:
        f.write(version)
data_files = [
    ("/usr/bin", ["pardus-software"]),
    (
        "/usr/share/applications",
        ["tr.org.pardus.software.desktop", "tr.org.pardus.software-open.desktop"],
    ),
    ("/usr/share/polkit-1/actions", ["tr.org.pardus.pkexec.pardus-software.policy"]),
    ("/usr/share/pardus/pardus-software/css", ["css/style.css"]),
    (
        "/usr/share/pardus/pardus-software/images",
        [
            "images/rating.svg",
            "images/rating-unrated.svg",
            "images/rating-hover.svg",
            "images/rating-unrated-hover.svg",
        ],
    ),
    ("/usr/share/pardus/pardus-software/ui", ["ui/MainWindow.glade"]),
    (
        "/usr/share/pardus/pardus-software/src",
        [
            "src/Actions.py",
            "src/AppDetail.py",
            "src/AppImage.py",
            "src/AppRequest.py",
            "src/AutoAptUpdate.py",
            "src/CellRendererButton.py",
            "src/GnomeComment.py",
            "src/GnomeRatingServer.py",
            "src/Group.py",
            "src/main.py",
            "src/MainWindow.py",
            "src/Package.py",
            "src/PardusComment.py",
            "src/Server.py",
            "src/SysActions.py",
            "src/UserSettings.py",
            "src/__version__",
        ],
    ),
    ("/usr/share/icons/hicolor/scalable/apps/", ["images/pardus-software.svg"]),
    ("/usr/share/mime/packages/", ["pardus-software.xml"]),
    ("/var/lib/polkit-1/localauthority/50-local.d/", ["pardus-software-group.pkla"]),
    ("/etc/pardus/", ["pardus-software.conf"]),
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
