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
                size = "not found"
        if type(size) is int:
            size = size / 1024
            print(size)
            if size > 1024:
                size = "{:.2f} MB".format(float(size / 1024))
            else:
                size = "{:.2f} KB".format(float(size))
        return size

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
