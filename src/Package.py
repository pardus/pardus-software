#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import apt


class Package(object):
    def __init__(self):
        # self.updatecache()

        """
        self.MainWindowUIFileName = "SplashScreen.glade"
        try:
            self.GtkBuilder = Gtk.Builder.new_from_file(self.MainWindowUIFileName)
            self.GtkBuilder.connect_signals(self)
        except GObject.GError:
            print(_("Error reading GUI file: ") + self.MainWindowUIFileName)
            raise

        self.splashwindow = self.GtkBuilder.get_object("splashwindow")

        self.splashwindow.set_auto_startup_notification(False)
        
        p = threading.Thread(target=self.updatecache)
        p.start()
        p.join()
        
        self.splashwindow.show_all()
        """
        self.cache = apt.Cache()
        self.cache.open()
        print("cache updated")

        self.apps = []
        self.secs = []
        self.sections = []
        for mypkg in self.cache:
            name = mypkg.name
            try:
                section = mypkg.candidate.section.lower()
            except:
                section = mypkg.versions[0].section.lower()
            self.apps.append({"name": name, "category": section})
            self.secs.append(section)

        self.uniqsections = sorted(list(set(self.secs)))

        lencat = len(self.uniqsections)

        self.sections.append({"name": "all", "number": 0})
        for i in range(0, lencat):
            self.sections.append({"name": self.uniqsections[i], "number": i + 1})

        self.repoapps = {}

        lenuniqsec = len(self.uniqsections)
        lenapss = len(self.apps)

        for i in range(0, lenuniqsec):
            temp = []
            for j in range(0, lenapss):
                if self.uniqsections[i] == self.apps[j]["category"]:
                    temp.append({"name": self.apps[j]["name"], "category": self.apps[j]["category"]})
            self.repoapps[self.uniqsections[i]] = temp

        # p = threading.Thread(target=self.updatecache)
        # p.start()

    """
    def updatecache(self):
        self.cache = apt.Cache()
        self.cache.open()
        time.sleep(1)
        print("cache updated")
        # self.splashwindow.close()
    """

    """
    def onDestroy(self, widget):
        print("splashwindow destroyed")
        self.splashwindow.destroy()
    """

    def updatecache(self):
        self.cache = apt.Cache()
        self.cache.open()
        print("cache re-updated")

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
        package = self.cache[packagename]
        try:
            summ = package.candidate.summary
        except:
            try:
                summ = package.versions[0].summary
            except:
                summ = "Summary is not found"
        return summ
