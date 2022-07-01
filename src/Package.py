#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import apt, apt_pkg
import time, os, locale, subprocess, re
from gi.repository import Gio

class Package(object):
    def __init__(self):

        # self.updatecache()

        self.apps = []
        self.secs = []
        self.sections = []

        # self.uniqsections = sorted(list(set(self.secs)))
        #
        # lencat = len(self.uniqsections)
        #
        # self.sections.append({"name": "all", "number": 0})
        # for i in range(0, lencat):
        #     self.sections.append({"name": self.uniqsections[i], "number": i + 1})
        #
        # self.repoapps = {}
        #
        # lenuniqsec = len(self.uniqsections)
        # lenapss = len(self.apps)
        #
        # for i in range(0, lenuniqsec):
        #     temp = []
        #     for j in range(0, lenapss):
        #         if self.uniqsections[i] == self.apps[j]["category"]:
        #             temp.append({"name": self.apps[j]["name"], "category": self.apps[j]["category"]})
        #     self.repoapps[self.uniqsections[i]] = temp

    def updatecache(self):
        try:
            self.cache = apt.Cache()
            self.cache.open()
        except:
            return False
        if self.cache.broken_count > 0:
            return False
        return True

    def getApps(self):
        for mypkg in self.cache:
            name = mypkg.name
            try:
                section = mypkg.candidate.section.lower()
            except:
                section = mypkg.versions[0].section.lower()
            self.apps.append({"name": name, "category": section})
            # self.secs.append(section)

    def controlPackageCache(self, packagename):
        try:
            self.cache[packagename]
        except:
            return False
        return True

    def isinstalled(self, packagename):
        try:
            package = self.cache[packagename]
        except:
            return None
        if package.is_installed:
            return True
        else:
            return False

    def missingdeps(self, packagename):
        package = self.cache[packagename]
        for rd in package.candidate.get_dependencies("Depends"):
            if not rd.installed_target_versions:
                return True
                break
        return False

    # print(package.versions[0].get_dependencies("Depends"))

    def description(self, packagename, israw):
        try:
            package = self.cache[packagename]
        except:
            return ""
        try:
            if israw:
                desc = package.candidate.raw_description.replace("\n", "")
            else:
                desc = package.candidate.raw_description
        except:
            try:
                if israw:
                    desc = package.versions[0].raw_description.replace("\n", "")
                else:
                    desc = package.versions[0].raw_description
            except:
                desc = "Description is not found"
        return desc

    def adv_description(self, packagename):
        try:
            long_desc = ""
            raw_desc = self.description(packagename, False).split("\n")
            # append a newline to the summary in the first line
            summary = raw_desc[0]
            raw_desc[0] = ""
            long_desc = "%s\n" % summary
            for line in raw_desc:
                tmp = line.strip()
                if tmp == ".":
                    long_desc += "\n"
                else:
                    long_desc += tmp + "\n"
            # print long_desc
            # do some regular expression magic on the description
            # Add a newline before each bullet
            p = re.compile(r'^(\s|\t)*(\*|0|-)', re.MULTILINE)
            long_desc = p.sub('\n*', long_desc)
            # replace all newlines by spaces
            p = re.compile(r'\n', re.MULTILINE)
            long_desc = p.sub(" ", long_desc)
            # replace all multiple spaces by
            # newlines
            p = re.compile(r'\s\s+', re.MULTILINE)
            long_desc = p.sub("\n", long_desc)
            long_desc = long_desc.rstrip("\n")
            # print(summary)
            # print(long_desc)
            return long_desc
        except:
            return self.description(packagename, False)

    def summary(self, packagename):
        # Return the short description (one line summary)
        try:
            package = self.cache[packagename]
        except:
            return ""
        try:
            summ = package.candidate.summary
        except:
            try:
                summ = package.versions[0].summary
            except:
                summ = "Summary is not found"
        return summ

    def version(self, packagename):
        package = self.cache[packagename]
        try:
            version = package.candidate.version
        except:
            try:
                version = package.versions[0].version
            except:
                version = "not found"
        return version

    def installedVersion(self, packagename):
        try:
            package = self.cache[packagename]
        except:
            return None
        try:
            version = package.installed.version
        except:
            version = None
        return version

    def size(self, packagename):
        package = self.cache[packagename]
        try:
            size = package.candidate.size
        except:
            try:
                size = package.versions[0].size
            except:
                size = ""
        return self.beauty_size(size)

    def required_changes(self, packagenames, sleep=True):
        if sleep:
            time.sleep(0.25)
        self.cache.clear()
        to_install = []
        to_delete = []
        broken = []
        inst_recommends = True
        packagenames = packagenames.split(" ")
        ret = {"download_size": None, "freed_size": None, "install_size": None, "to_install": None, "to_delete": None,
               "broken": None}

        if "--no-install-recommends" in packagenames:
            inst_recommends = False
            packagenames.remove("--no-install-recommends")
        if "--no-install-suggests" in packagenames:
            # inst_recommends = False
            packagenames.remove("--no-install-suggests")

        for packagename in packagenames:
            # print(packagename)
            try:
                package = self.cache[packagename]
            except Exception as e:
                print("{}".format(e))
                return ret
            try:
                if package.is_installed:
                    package.mark_delete(True, True)
                else:
                    if inst_recommends:
                        package.mark_install(True, True)
                    else:
                        package.mark_install(True, False)
            except:
                if packagename not in broken:
                    broken.append(packagename)
            changes = self.cache.get_changes()
            for package in changes:
                if package.marked_install:
                    if package.name not in to_install:
                        to_install.append(package.name)
                elif package.marked_delete:
                    if package.name not in to_delete:
                        to_delete.append(package.name)

        download_size = self.cache.required_download
        space = self.cache.required_space
        if space < 0:
            freed_size = space * -1
            install_size = 0
        else:
            freed_size = 0
            install_size = space

        ret["download_size"] = download_size
        ret["freed_size"] = freed_size
        ret["install_size"] = install_size
        ret["to_install"] = to_install
        ret["to_delete"] = to_delete
        ret["broken"] = broken

        # print("freed_size {}".format(ret["freed_size"]))
        # print("download_size {}".format(ret["download_size"]))
        # print("install_size {}".format(ret["install_size"]))
        # print("to_install {}".format(ret["to_install"]))
        # print("to_delete {}".format(ret["to_delete"]))

        return ret

    def myapps_remove_details(self, desktopname):
        # self.updatecache()
        try:
            process = subprocess.run(["dpkg", "-S", desktopname], stdout=subprocess.PIPE)
            output = process.stdout.decode("utf-8")
            package = output[:output.find(":")].split(",")[0]
            if package:
                return True, self.required_changes(package, sleep=False), package
            else:
                # try get package name from basename
                process = subprocess.run(["dpkg", "-S", os.path.basename(desktopname)], stdout=subprocess.PIPE)
                output = process.stdout.decode("utf-8")
                package = output[:output.find(":")].split(",")[0]
                if package:
                    return True, self.required_changes(package, sleep=False), package
                else:
                    return False, None, ""
        except Exception as e:
            print("Error on myapps_remove_details: {}".format(e))
            return False, None, ""

    def get_appname_from_desktopfile(self, desktopname):
        try:
            process = subprocess.run(["dpkg", "-S", desktopname], stdout=subprocess.PIPE)
            output = process.stdout.decode("utf-8")
            package = output[:output.find(":")].split(",")[0]
            if package:
                return True, package
            else:
                # try get package name from basename
                process = subprocess.run(["dpkg", "-S", os.path.basename(desktopname)], stdout=subprocess.PIPE)
                output = process.stdout.decode("utf-8")
                package = output[:output.find(":")].split(",")[0]
                if package:
                    return True, package
                else:
                    return False, ""
        except Exception as e:
            print("Error on get_appname_from_desktopfile: {}".format(e))
            return False, ""

    def beauty_size(self, size):
        # apt uses MB rather than MiB, so let's stay consistent
        if type(size) is int:
            size = size / 1000
            if size > 1000000:
                size = "{:.1f} GB".format(float(size / 1000000))
            elif size > 1000:
                size = "{:.1f} MB".format(float(size / 1000))
            else:
                size = "{:.1f} KB".format(float(size))
            return size
        return "size not found"

    # old function
    # def installed_packages(self, lang="en"):
    #
    #     # apt list --installed   || very slow method
    #     # applist = []
    #     # for mypkg in self.cache:
    #     #     if self.cache[mypkg.name].is_installed:
    #     #         applist.append({"name": mypkg.name, "size": self.installed_size(mypkg.name), "summary": self.summary(mypkg.name)})
    #
    #     # apps that have desktop file in /usr/share/applications/  | slow method
    #     # dloc = "/usr/share/applications/"
    #     # desktop_dir = os.listdir(dloc)
    #     # desktop_list = []
    #     # applist = []
    #     # for desktop in desktop_dir:
    #     #     if desktop.endswith(".desktop") and "NoDisplay=true" not in open(os.path.join(dloc, desktop), "r").read():
    #     #         desktop_list.append(desktop)
    #     # for desktop in desktop_list:
    #     #     process = subprocess.run(["dpkg", "-S", desktop], stdout=subprocess.PIPE)
    #     #     output = process.stdout.decode("utf-8")
    #     #     app = output[:output.find(":")].split(",")[0]
    #     #     applist.append({"name": app, "size": self.installed_size(app), "summary": self.summary(app)})
    #     # applist = sorted(dict((v['name'], v) for v in applist).values(), key=lambda x: x["name"])
    #
    #
    #     # parse desktop file in /usr/share/applications/  | normal method
    #     applist = []
    #     dloc = "/usr/share/applications/"
    #     desktop_listdir = os.listdir(dloc)
    #     for desktop in desktop_listdir:
    #         if desktop.endswith(".desktop"):
    #             desktop_read = open(os.path.join(dloc, desktop), "r").read()
    #             if "NoDisplay=true" not in desktop_read:
    #                 name = ""
    #                 icon = ""
    #                 comment = ""
    #                 name_tr = ""
    #                 comment_tr = ""
    #                 mainentry = ""
    #                 if "Name=" in desktop_read:
    #                     for line in desktop_read.splitlines():
    #                         if line.startswith("["):
    #                             mainentry = line.strip()[1:-1]
    #                         if line.startswith("Name=") and mainentry == "Desktop Entry":
    #                             name = line.split("Name=")[1].strip()
    #                             break
    #                 if "Icon=" in desktop_read:
    #                     for line in desktop_read.splitlines():
    #                         if line.startswith("["):
    #                             mainentry = line.strip()[1:-1]
    #                         if line.startswith("Icon=") and mainentry == "Desktop Entry":
    #                             icon = line.split("Icon=")[1].strip()
    #                             break
    #                 if "Comment=" in desktop_read:
    #                     for line in desktop_read.splitlines():
    #                         if line.startswith("["):
    #                             mainentry = line.strip()[1:-1]
    #                         if line.startswith("Comment=") and mainentry == "Desktop Entry":
    #                             comment = line.split("Comment=")[1].strip()
    #                             break
    #                 else:
    #                     comment = name
    #
    #                 if lang == "tr":
    #                     if "Name[tr]=" in desktop_read:
    #                         for line in desktop_read.splitlines():
    #                             if line.startswith("["):
    #                                 mainentry = line.strip()[1:-1]
    #                             if line.startswith("Name[tr]=") and mainentry == "Desktop Entry":
    #                                 name_tr = line.split("Name[tr]=")[1].strip()
    #                                 print("{} {}".format(mainentry, name_tr))
    #                                 break
    #                     if "Comment[tr]=" in desktop_read:
    #                         for line in desktop_read.splitlines():
    #                             if line.startswith("["):
    #                                 mainentry = line.strip()[1:-1]
    #                             if line.startswith("Comment[tr]=") and mainentry == "Desktop Entry":
    #                                 comment_tr = line.split("Comment[tr]=")[1].strip()
    #                                 break
    #                     if name_tr == "":
    #                         name_tr = name
    #                     if comment_tr == "":
    #                         comment_tr = comment
    #
    #                 applist.append({"name": name_tr if lang == "tr" else name,
    #                                 "comment": comment_tr if lang == "tr" else comment,
    #                                 "desktop": os.path.join(dloc, desktop), "icon": icon})
    #     applist = sorted(dict((v['name'], v) for v in applist).values(), key=lambda x: locale.strxfrm(x["name"]))
    #
    #     return applist

    # old function
    # def parse_desktopfile(self, desktop, lang):
    #     dloc = "/usr/share/applications/"
    #     if os.path.isfile(os.path.join(dloc, desktop)):
    #         desktop_read = open(os.path.join(dloc, desktop), "r").read()
    #         name = ""
    #         icon = ""
    #         comment = ""
    #         name_tr = ""
    #         comment_tr = ""
    #         mainentry = ""
    #         if "Name=" in desktop_read:
    #             for line in desktop_read.splitlines():
    #                 if line.startswith("["):
    #                     mainentry = line.strip()[1:-1]
    #                 if line.startswith("Name=") and mainentry == "Desktop Entry":
    #                     name = line.split("Name=")[1].strip()
    #                     break
    #         if "Icon=" in desktop_read:
    #             for line in desktop_read.splitlines():
    #                 if line.startswith("["):
    #                     mainentry = line.strip()[1:-1]
    #                 if line.startswith("Icon=") and mainentry == "Desktop Entry":
    #                     icon = line.split("Icon=")[1].strip()
    #                     break
    #         if "Comment=" in desktop_read:
    #             for line in desktop_read.splitlines():
    #                 if line.startswith("["):
    #                     mainentry = line.strip()[1:-1]
    #                 if line.startswith("Comment=") and mainentry == "Desktop Entry":
    #                     comment = line.split("Comment=")[1].strip()
    #                     break
    #         else:
    #             comment = name
    #
    #         if lang == "tr":
    #             if "Name[tr]=" in desktop_read:
    #                 for line in desktop_read.splitlines():
    #                     if line.startswith("["):
    #                         mainentry = line.strip()[1:-1]
    #                     if line.startswith("Name[tr]=") and mainentry == "Desktop Entry":
    #                         name_tr = line.split("Name[tr]=")[1].strip()
    #                         print("{} {}".format(mainentry, name_tr))
    #                         break
    #             if "Comment[tr]=" in desktop_read:
    #                 for line in desktop_read.splitlines():
    #                     if line.startswith("["):
    #                         mainentry = line.strip()[1:-1]
    #                     if line.startswith("Comment[tr]=") and mainentry == "Desktop Entry":
    #                         comment_tr = line.split("Comment[tr]=")[1].strip()
    #                         break
    #             if name_tr == "":
    #                 name_tr = name
    #             if comment_tr == "":
    #                 comment_tr = comment
    #
    #         return {"name": name_tr if lang == "tr" else name, "comment": comment_tr if lang == "tr" else comment,
    #                         "desktop": os.path.join(dloc, desktop), "icon": icon}
    #
    #     else:
    #         print("{} file not exists on {} location".format(desktop, dloc))
    #         return None

    def get_installed_apps(self):
        apps = []
        for app in Gio.DesktopAppInfo.get_all():

            id = app.get_id()
            name = app.get_name()
            executable = app.get_executable()
            nodisplay = app.get_nodisplay()
            icon = app.get_string('Icon')
            description = app.get_description() or app.get_generic_name() or app.get_name()
            filename = app.get_filename()

            if os.path.dirname(filename) == "/usr/share/applications" and executable and not nodisplay:
                apps.append({"id": id, "name": name, "icon": icon, "description": description, "filename": filename})

        apps = sorted(dict((v['name'], v) for v in apps).values(), key=lambda x: locale.strxfrm(x["name"]))

        return apps

    def parse_desktopfile(self, desktopfilename):
        try:
            app = Gio.DesktopAppInfo.new(desktopfilename)
            if app:
                id = app.get_id()
                name = app.get_name()
                # executable = app.get_executable()
                # nodisplay = app.get_nodisplay()
                icon = app.get_string('Icon')
                description = app.get_description() or app.get_generic_name() or app.get_name()
                filename = app.get_filename()
                print(filename)
                if os.path.dirname(filename) == "/usr/share/applications":
                    return True, {"id": id, "name": name, "icon": icon, "description": description, "filename": filename}
                else:
                    return False, {"id": id, "name": name, "icon": icon, "description": description, "filename": filename}
            else:
                print("parse_desktopfile: {} app not exists".format(desktopfilename))
                return False, None
        except Exception as e:
            print("{}".format(e))
            print("parse_desktopfile: {} app not exists".format(desktopfilename))
            return False, None

    def origins(self, packagename):
        package = self.cache[packagename]
        try:
            component = package.candidate.origins[0]
        except:
            try:
                component = package.versions[0].origins[0]
            except:
                component = None
        return component

    def residual(self):
        residual = []
        try:
            for pkg in self.cache:
                if self.cache[pkg.name].has_config_files and not self.cache[pkg.name].is_installed:
                    residual.append(pkg.name)
        except Exception as e:
            print("Package residual Error: {}".format(e))

        return residual

    def autoremovable(self):
        autoremovable = []
        try:
            for pkg in self.cache:
                if self.cache[pkg.name].is_auto_removable:
                    autoremovable.append(pkg.name)
        except Exception as e:
            print("Package autoremovable Error: {}".format(e))
        return autoremovable

    def upgradable(self):
        upgradable = []
        try:
            for pkg in self.cache:
                if self.cache[pkg.name].is_upgradable:
                    upgradable.append(pkg.name)
        except Exception as e:
            print("Package upgradable Error: {}".format(e))
        return upgradable

    def versionCompare(self, version1, version2):
        vc = apt_pkg.version_compare(version1, version2)
        if vc > 0:
            print("user version: {} > server version: {}".format(version1, version2))
        elif vc == 0:
            print("user version: {} == server version: {}".format(version1, version2))
        elif vc < 0:
            print("user version: {} < server version: {}".format(version1, version2))
        return vc
