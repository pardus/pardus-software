#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import apt, apt_pkg


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

    def adv_size(self, app, packagenames):
        self.cache.clear()
        to_install = []
        to_delete = []
        recommends = []
        inst_recommends = True
        packagenames = packagenames.split(" ")
        ret = {"download_size": None, "freed_size": None, "install_size": None, "to_install": None, "to_delete": None}

        if "--no-install-recommends" in packagenames:
            inst_recommends = False
            packagenames.remove("--no-install-recommends")
        if "--no-install-suggests" in packagenames:
            inst_recommends = False
            packagenames.remove("--no-install-suggests")

        for packagename in packagenames:
            print(packagename)
            try:
                package = self.cache[packagename]
            except Exception as e:
                print("{}".format(e))
                return ret
            if package.is_installed:
                package.mark_delete(True, True)
            else:
                if inst_recommends:
                    package.mark_install(True, True)
                else:
                    package.mark_install(True, False)
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

        ret["download_size"] = self.beauty_size(download_size)
        ret["freed_size"] = self.beauty_size(freed_size)
        ret["install_size"] = self.beauty_size(install_size)
        ret["to_install"] = to_install
        ret["to_delete"] = to_delete

        # print("freed_size {}".format(ret["freed_size"]))
        # print("download_size {}".format(ret["download_size"]))
        # print("install_size {}".format(ret["install_size"]))
        # print("to_install {}".format(ret["to_install"]))
        # print("to_delete {}".format(ret["to_delete"]))

        return ret

    def beauty_size(self, size):
        # apt uses MB rather than MiB, so let's stay consistent
        if type(size) is int:
            size = size / 1000
            if size > 1000:
                size = "{:.1f} MB".format(float(size / 1000))
            else:
                size = "{:.1f} KB".format(float(size))
            return size
        return "size not found"

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
