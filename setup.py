#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from setuptools import setup, find_packages, os

changelog = "debian/changelog"
if os.path.exists(changelog):
    head = open(changelog).readline()
    try:
        version = head.split("(")[1].split(")")[0]
    except:
        print("debian/changelog format is wrong for get version")
        version = ""
    f = open("src/__version__", "w")
    f.write(version)
    f.close()

data_files = [
    ("/usr/bin", ["pardus-software"]),
    ("/usr/share/applications", ["tr.org.pardus.software.desktop", "tr.org.pardus.software-open.desktop"]),
    ("/usr/share/locale/tr/LC_MESSAGES", ["po/tr/LC_MESSAGES/pardus-software.mo"]),
    ("/usr/share/polkit-1/actions", ["tr.org.pardus.pkexec.pardus-software.policy"]),
    ("/usr/share/pardus/pardus-software/css", ["css/style.css"]),
    ("/usr/share/pardus/pardus-software/images",
     ["images/rating.svg", "images/rating-unrated.svg", "images/rating-hover.svg",
      "images/rating-unrated-hover.svg"]),
    ("/usr/share/pardus/pardus-software/ui", ["ui/MainWindow.glade"]),
    ("/usr/share/pardus/pardus-software/src",
     ["src/Actions.py", "src/AppDetail.py", "src/AppImage.py", "src/AppRequest.py", "src/AutoAptUpdate.py",
      "src/CellRendererButton.py", "src/GnomeComment.py", "src/GnomeRatingServer.py", "src/main.py",
      "src/MainWindow.py", "src/Package.py", "src/Server.py", "src/SysActions.py", "src/UserSettings.py",
      "src/__version__"]),
    ("/usr/share/icons/hicolor/scalable/apps/", ["images/pardus-software.svg"]),
    ("/usr/share/mime/packages/", ["pardus-software.xml"])
]

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
