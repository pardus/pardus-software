#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import os
import threading
import netifaces
import psutil

import gi

gi.require_version("GLib", "2.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Notify", "0.7")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GLib, Gtk, GObject, Notify, GdkPixbuf, Gio, Gdk

from Package import Package
from Server import Server
# from CellRendererButton import CellRendererButton

from AppImage import AppImage
from AppDetail import AppDetail

from UserSettings import UserSettings


class MainWindow(object):
    def __init__(self, application):
        self.Application = application

        self.MainWindowUIFileName = os.path.dirname(os.path.abspath(__file__)) + "/../ui/MainWindow.glade"
        try:
            self.GtkBuilder = Gtk.Builder.new_from_file(self.MainWindowUIFileName)
            self.GtkBuilder.connect_signals(self)
        except GObject.GError:
            print("Error reading GUI file: " + self.MainWindowUIFileName)
            raise

        self.parduspixbuf = Gtk.IconTheme.new()
        self.parduspixbuf.set_custom_theme("pardus")

        try:
            self.missing_pixbuf = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", 96,
                                                                        Gtk.IconLookupFlags(16))
        except:
            self.missing_pixbuf = Gtk.IconTheme.get_default().load_icon("image-missing", 96,
                                                                        Gtk.IconLookupFlags(16))

        self.staron = GdkPixbuf.Pixbuf.new_from_file_at_size(
            os.path.dirname(os.path.abspath(__file__)) + "/../images/rating.svg", 24, 24)
        self.staroff = GdkPixbuf.Pixbuf.new_from_file_at_size(
            os.path.dirname(os.path.abspath(__file__)) + "/../images/rating-unrated.svg", 24, 24)

        self.isPardusSearching = False
        self.isRepoSearching = False

        self.RepoCategoryListBox = self.GtkBuilder.get_object("RepoCategoryListBox")

        self.HomeCategoryFlowBox = self.GtkBuilder.get_object("HomeCategoryFlowBox")
        """
        self.CategoryAllRow = Gtk.ListBoxRow.new()
        self.CategoryListBox.add(self.CategoryAllRow)

        grid = Gtk.Grid.new()
        self.CategoryAllRow.add(grid)

        icon = Gtk.Image.new_from_icon_name("applications-other",0)
        icon.set_pixel_size(48)
        
        text = Gtk.Label.new()
        text.set_text(" All")
        
        grid.add(icon)
        grid.attach(text, 1, 0, 3, 1)
        """
        # caticon = Gtk.Image.new_from_icon_name("applications-other",0)

        self.searchbar = self.GtkBuilder.get_object("searchbar")
        self.pardussearchbar = self.GtkBuilder.get_object("pardussearchbar")
        self.reposearchbar = self.GtkBuilder.get_object("reposearchbar")
        self.topsearchbutton = self.GtkBuilder.get_object("topsearchbutton")
        self.toprevealer = self.GtkBuilder.get_object("toprevealer")

        self.pardusicb = self.GtkBuilder.get_object("pardusicb")

        self.mainstack = self.GtkBuilder.get_object("mainstack")
        self.homestack = self.GtkBuilder.get_object("homestack")
        self.searchstack = self.GtkBuilder.get_object("searchstack")
        self.dIcon = self.GtkBuilder.get_object("dIcon")
        self.dName = self.GtkBuilder.get_object("dName")
        self.dActionButton = self.GtkBuilder.get_object("dActionButton")
        self.dDescriptionLabel = self.GtkBuilder.get_object("dDescriptionLabel")
        self.dSection = self.GtkBuilder.get_object("dSection")
        self.dMaintainer = self.GtkBuilder.get_object("dMaintainer")
        self.dVersion = self.GtkBuilder.get_object("dVersion")
        self.dSize = self.GtkBuilder.get_object("dSize")
        self.dComponent = self.GtkBuilder.get_object("dComponent")
        self.dType = self.GtkBuilder.get_object("dType")
        self.dCategory = self.GtkBuilder.get_object("dCategory")
        self.dLicense = self.GtkBuilder.get_object("dLicense")
        self.dCodename = self.GtkBuilder.get_object("dCodename")
        self.dWeb = self.GtkBuilder.get_object("dWeb")
        self.dMail = self.GtkBuilder.get_object("dMail")
        self.dtDownload = self.GtkBuilder.get_object("dtDownload")
        self.dtTotalRating = self.GtkBuilder.get_object("dtTotalRating")
        self.dtUserRating = self.GtkBuilder.get_object("dtUserRating")
        self.dtAverageRating = self.GtkBuilder.get_object("dtAverageRating")

        self.dtStar1 = self.GtkBuilder.get_object("dtStar1")
        self.dtStar2 = self.GtkBuilder.get_object("dtStar2")
        self.dtStar3 = self.GtkBuilder.get_object("dtStar3")
        self.dtStar4 = self.GtkBuilder.get_object("dtStar4")
        self.dtStar5 = self.GtkBuilder.get_object("dtStar5")

        self.dPardusRating = self.GtkBuilder.get_object("dPardusRating")
        self.dPardusBar1 = self.GtkBuilder.get_object("dPardusBar1")
        self.dPardusBar2 = self.GtkBuilder.get_object("dPardusBar2")
        self.dPardusBar3 = self.GtkBuilder.get_object("dPardusBar3")
        self.dPardusBar4 = self.GtkBuilder.get_object("dPardusBar4")
        self.dPardusBar5 = self.GtkBuilder.get_object("dPardusBar5")
        self.dPardusBarLabel1 = self.GtkBuilder.get_object("dPardusBarLabel1")
        self.dPardusBarLabel2 = self.GtkBuilder.get_object("dPardusBarLabel2")
        self.dPardusBarLabel3 = self.GtkBuilder.get_object("dPardusBarLabel3")
        self.dPardusBarLabel4 = self.GtkBuilder.get_object("dPardusBarLabel4")
        self.dPardusBarLabel5 = self.GtkBuilder.get_object("dPardusBarLabel5")

        self.dGnomeRating = self.GtkBuilder.get_object("dGnomeRating")
        self.dGnomeBar1 = self.GtkBuilder.get_object("dGnomeBar1")
        self.dGnomeBar2 = self.GtkBuilder.get_object("dGnomeBar2")
        self.dGnomeBar3 = self.GtkBuilder.get_object("dGnomeBar3")
        self.dGnomeBar4 = self.GtkBuilder.get_object("dGnomeBar4")
        self.dGnomeBar5 = self.GtkBuilder.get_object("dGnomeBar5")
        self.dGnomeBarLabel1 = self.GtkBuilder.get_object("dGnomeBarLabel1")
        self.dGnomeBarLabel2 = self.GtkBuilder.get_object("dGnomeBarLabel2")
        self.dGnomeBarLabel3 = self.GtkBuilder.get_object("dGnomeBarLabel3")
        self.dGnomeBarLabel4 = self.GtkBuilder.get_object("dGnomeBarLabel4")
        self.dGnomeBarLabel5 = self.GtkBuilder.get_object("dGnomeBarLabel5")

        self.raction = self.GtkBuilder.get_object("raction")
        self.rtitle = self.GtkBuilder.get_object("rtitle")
        self.rdetail = self.GtkBuilder.get_object("rdetail")
        self.rbotstack = self.GtkBuilder.get_object("rbotstack")

        self.topbutton1 = self.GtkBuilder.get_object("topbutton1")
        self.topbutton1.get_style_context().add_class("suggested-action")
        self.topbutton2 = self.GtkBuilder.get_object("topbutton2")

        self.splashspinner = self.GtkBuilder.get_object("splashspinner")
        self.splashbar = self.GtkBuilder.get_object("splashbar")
        self.splashlabel = self.GtkBuilder.get_object("splashlabel")
        self.splashbarstatus = True
        GLib.timeout_add(200, self.on_timeout, None)

        self.PardusAppsIconView = self.GtkBuilder.get_object("PardusAppsIconView")
        self.PardusAppsIconView.set_pixbuf_column(0)
        self.PardusAppsIconView.set_text_column(3)

        self.EditorAppsIconView = self.GtkBuilder.get_object("EditorAppsIconView")
        self.EditorAppsIconView.set_pixbuf_column(0)
        self.EditorAppsIconView.set_text_column(3)

        self.RepoAppsTreeView = self.GtkBuilder.get_object("RepoAppsTreeView")

        self.PardusAppListStore = self.GtkBuilder.get_object("PardusAppListStore")
        self.EditorListStore = self.GtkBuilder.get_object("EditorListStore")
        self.RepoAppListStore = self.GtkBuilder.get_object("RepoAppListStore")

        self.HeaderBarMenu = self.GtkBuilder.get_object("HeaderBarMenu")
        self.menu1 = self.GtkBuilder.get_object("menu1")
        self.menu1.set_use_stock(False)
        self.menu1.set_label("Preferences")
        self.menu1.set_image(Gtk.Image.new_from_icon_name('preferences-other-symbolic', Gtk.IconSize.BUTTON))
        self.menu2 = self.GtkBuilder.get_object("menu2")
        self.menu2.set_use_stock(False)
        self.menu2.set_label("Menu 2")
        self.menu2.set_image(Gtk.Image.new_from_icon_name('gtk-dialog-question', Gtk.IconSize.BUTTON))

        self.dialogpref = self.GtkBuilder.get_object("dialogpref")
        self.dpApply = self.GtkBuilder.get_object("dpApply")
        self.switchUSI = self.GtkBuilder.get_object("switchUSI")
        self.switchEA = self.GtkBuilder.get_object("switchEA")

        self.menubackbutton = self.GtkBuilder.get_object("menubackbutton")
        self.menubackbutton.set_sensitive(False)

        self.progresstextlabel = self.GtkBuilder.get_object("progresstextlabel")
        self.topspinner = self.GtkBuilder.get_object("topspinner")

        self.noserverlabel = self.GtkBuilder.get_object("noserverlabel")

        self.NavCategoryImage = self.GtkBuilder.get_object("NavCategoryImage")
        self.NavCategoryLabel = self.GtkBuilder.get_object("NavCategoryLabel")

        # self.editorapps = [{'name': '0ad', 'category': 'games', 'prettyname': '0 A.D.'},
        #                    {'name': 'akis', 'category': 'other', 'prettyname': 'Akis'},
        #                    {'name': 'alien-arena', 'category': 'games', 'prettyname': 'Alien Arena'}]
        #
        # for ediapp in self.editorapps:
        #     try:
        #         edipixbuf = Gtk.IconTheme.get_default().load_icon(ediapp['name'], 64, Gtk.IconLookupFlags(16))
        #         # pixbuf = self.appiconpixbuf.load_icon(app['name'], 64, 0)
        #     except:
        #         # pixbuf = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", 64, 0)
        #         try:
        #             edipixbuf = self.parduspixbuf.load_icon(ediapp['name'], 64, Gtk.IconLookupFlags(16))
        #         except:
        #             try:
        #                 edipixbuf = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", 64,
        #                                                                   Gtk.IconLookupFlags(16))
        #             except:
        #                 edipixbuf = Gtk.IconTheme.get_default().load_icon("image-missing", 64, Gtk.IconLookupFlags(16))
        #
        #     ediappname = ediapp['name']
        #     ediprettyname = ediapp['prettyname']
        #     edicategory = ediapp['category']
        #     edicategorynumber = self.get_category_number(ediapp['category'])
        #     self.EditorListStore.append([edipixbuf, ediappname, edicategorynumber, ediprettyname])

        self.PardusCurrentCategory = -1
        self.PardusCurrentCategoryString = "all"
        self.RepoCurrentCategory = "all"

        self.useDynamicListStore = False

        self.PardusCategoryFilter = self.GtkBuilder.get_object("PardusCategoryFilter")
        self.PardusCategoryFilter.set_visible_func(self.PardusCategoryFilterFunction)
        self.PardusCategoryFilter.refilter()

        # self.RepoCategoryFilter = self.GtkBuilder.get_object("RepoCategoryFilter")
        # self.RepoCategoryFilter.set_visible_func(self.RepoCategoryFilterFunction)
        # self.RepoCategoryFilter.refilter()

        self.dImage1 = self.GtkBuilder.get_object("dImage1")
        self.dImage2 = self.GtkBuilder.get_object("dImage2")
        self.pop1 = self.GtkBuilder.get_object("pop1")
        self.pop2 = self.GtkBuilder.get_object("pop2")
        self.pop1Image = self.GtkBuilder.get_object("pop1Image")
        self.pop2Image = self.GtkBuilder.get_object("pop2Image")
        self.pixbuf1 = None
        self.pixbuf2 = None
        self.getDisplay()

        self.mac = self.getMac()

        self.descSwBox = self.GtkBuilder.get_object("descSwBox")
        self.descSwBox.set_visible(False)

        self.descSw = self.GtkBuilder.get_object("descSw")

        self.MainWindow = self.GtkBuilder.get_object("MainWindow")
        self.MainWindow.set_application(application)
        self.mainstack.set_visible_child_name("page0")

        cssProvider = Gtk.CssProvider()
        cssProvider.load_from_path(os.path.dirname(os.path.abspath(__file__)) + "/../css/style.css")
        screen = Gdk.Screen.get_default()
        styleContext = Gtk.StyleContext()
        styleContext.add_provider_for_screen(screen, cssProvider,
                                             Gtk.STYLE_PROVIDER_PRIORITY_USER)
        # With the others GTK_STYLE_PROVIDER_PRIORITY values get the same result.

        self.MainWindow.show_all()

        p1 = threading.Thread(target=self.worker)
        p1.start()
        print("start done")

    def getMac(self):
        mac = ""
        try:
            AF_LINK = netifaces.AF_LINK
        except:
            AF_LINK = 17
        gateway_info = netifaces.gateways()
        default_gateways = gateway_info['default']
        for family in default_gateways:
            interface = default_gateways[family][1]  # 0 for gateway, 1 for interface
            mac = netifaces.ifaddresses(interface)[netifaces.AF_LINK][0]["addr"].upper()
            break
        if mac is None or mac == "":
            print("mac address can not get from netifaces, trying psutil")
            nics = psutil.net_if_addrs()
            nics.pop('lo')  # remove loopback
            for i in nics:
                for j in nics[i]:
                    if j.family == AF_LINK:
                        mac = j.address.upper()
                        break
                else:
                    continue
                break
        return mac

    def getDisplay(self):
        # defwindow = Gdk.get_default_root_window()
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        geometry = monitor.get_geometry()
        self.s_width = geometry.width
        self.s_height = geometry.height

    def worker(self):
        self.usersettings()
        self.package()
        self.appimage()
        self.appdetail()
        self.setRepoCategories()
        self.setRepoApps()
        self.server()
        self.gnomeRatings()
        self.setPardusCategories()
        self.setPardusApps()
        self.normalpage()

    def normalpage(self):
        # self.mainstack.set_visible_child_name("page1")
        self.mainstack.set_visible_child_name("page2")
        if self.Server.connection and self.Server.app_scode == 200 and self.Server.cat_scode == 200:
            self.homestack.set_visible_child_name("pardushome")
        else:
            self.homestack.set_visible_child_name("noserver")
            self.noserverlabel.set_markup(
                "<b>{}\n{} : {}\n{} : {}</b>".format("Could not connect to server.", "Error Code (app)",
                                                     self.Server.app_scode, "Error Code (cat)", self.Server.cat_scode))
        self.splashspinner.stop()
        self.splashbarstatus = False
        self.splashlabel.set_text("")
        print("page setted to normal")

    def package(self):
        # self.splashspinner.start()
        self.splashbar.pulse()
        self.splashlabel.set_markup("<b>Updating Cache</b>")
        self.Package = Package()

        print("package completed")

    def usersettings(self):
        self.UserSettings = UserSettings()
        self.UserSettings.createDefaultConfig()
        self.UserSettings.readConfig()

        print("{} {}".format("config_usi", self.UserSettings.config_usi))
        print("{} {}".format("config_anim", self.UserSettings.config_anim))

    def appimage(self):
        self.AppImage = AppImage()
        self.AppImage.Pixbuf = self.Pixbuf
        print("appimage completed")

    def appdetail(self):
        self.AppDetail = AppDetail()
        self.AppDetail.Detail = self.Detail
        print("appdetail completed")

    def on_dEventBox1_button_press_event(self, widget, event):
        print("here")
        self.pop1.show_all()
        self.pop1.popup()

    def on_dEventBox2_button_press_event(self, widget, event):
        print("here")
        self.pop2.show_all()
        self.pop2.popup()

    def on_dImage2_button_press_event(self, widget, event):
        print("image press")

    def setRepoCategories(self):
        self.splashlabel.set_markup("<b>Setting Repo Categories</b>")
        # for i in self.Package.sections:
        #     # row = Gtk.ListBoxRow.new()
        #     # self.RepoCategoryListBox.add(row)
        #     #
        #     label = Gtk.Label.new()
        #     label.set_text(" " + str(i["name"]).capitalize())
        #     label.set_property("xalign", 0)
        #
        #     row = Gtk.ListBoxRow()
        #     row.add(label)
        #
        #     self.RepoCategoryListBox.add(row)
        #
        # self.RepoCategoryListBox.show_all()
        print("Repo Categories setted")

    def setRepoApps(self):
        self.splashlabel.set_markup("<b>Setting Repo Apps</b>")
        print("Repo apps setting")
        # for app in self.Package.apps:
        #     appname = app['name']
        #     category = app['category']
        #     # categorynumber = self.get_repo_category_number(app["category"])
        #     installstatus = self.Package.isinstalled(appname)
        #     if installstatus:
        #         installtext = "Remove"
        #     else:
        #         installtext = "Install"
        #     self.RepoAppListStore.append([appname, category, 0, installstatus, installtext, self.Package.summary(appname)])

        renderer_toggle = Gtk.CellRendererToggle()
        renderer_toggle.connect("toggled", self.on_cell_toggled)
        column_toggle = Gtk.TreeViewColumn("Status", renderer_toggle, active=3)
        column_toggle.set_resizable(True)
        column_toggle.set_sort_column_id(3)
        self.RepoAppsTreeView.append_column(column_toggle)

        renderer = Gtk.CellRendererText()
        column_name = Gtk.TreeViewColumn("Name", renderer, text=0)
        column_name.set_resizable(True)
        column_name.set_sort_column_id(0)
        self.RepoAppsTreeView.append_column(column_name)

        renderer = Gtk.CellRendererText()
        column_cat = Gtk.TreeViewColumn("Section", renderer, text=1)
        column_cat.set_resizable(True)
        column_cat.set_sort_column_id(1)
        self.RepoAppsTreeView.append_column(column_cat)

        # renderer_btn = CellRendererButton()
        # renderer_btn.connect("clicked", self.on_cell_clicked)
        # column_btn = Gtk.TreeViewColumn("Action", renderer_btn, text=4)
        # column_btn.set_resizable(True)
        # column_btn.set_sort_column_id(4)
        # self.RepoAppsTreeView.append_column(column_btn)

        renderer = Gtk.CellRendererText()
        column_desc = Gtk.TreeViewColumn("Description", renderer, text=5)
        column_desc.set_resizable(True)
        column_desc.set_sort_column_id(5)
        self.RepoAppsTreeView.append_column(column_desc)

        self.RepoAppsTreeView.show_all()

        self.repoapps = self.Package.repoapps

        # if self.useDynamicListStore:
        #
        #     self.storedict = {}
        #
        #     for i in self.repoapps:
        #         self.storedict[i] = Gtk.ListStore(str, str, int, bool, str, str)
        #
        #     for i in self.storedict:
        #         for j in self.repoapps[i]:
        #             installstatus = self.Package.isinstalled(j["name"])
        #             if installstatus:
        #                 installtext = "Remove"
        #             else:
        #                 installtext = "Install"
        #             self.storedict[i].append(
        #                 [j["name"], j["category"], 0, installstatus, installtext, self.Package.summary(j["name"])])

    def on_cell_toggled(self, widget, path):
        # self.RepoAppListStore[path][3] = not self.RepoAppListStore[path][3]
        print("cell toggled")

    def on_cell_clicked(self, path, button):
        print("cell clicked")

    def server(self):
        self.splashbar.pulse()
        self.splashlabel.set_markup("<b>Getting applications from server</b>")
        self.Server = Server()
        print("{} {}".format("server connection", self.Server.connection))

    def gnomeRatings(self):
        self.splashlabel.set_markup("<b>Getting ratings from gnome odrs</b>")
        self.gnomeratings = self.Server.getGnomeRatings()
        if self.gnomeratings is not False:
            print("gnomeratings successful")

    def setPardusApps(self):
        if self.Server.connection:
            self.splashlabel.set_markup("<b>Setting applications</b>")

            if self.UserSettings.config_usi:
                print("User want to use system icons [app]")
                for app in self.Server.applist:
                    appicon = self.getSystemAppIcon(app["name"])
                    appname = app['name']
                    prettyname = app['prettyname']["en"]
                    category = ""
                    for i in app['category']:
                        category += i["en"] + ","
                    category = category.rstrip(",")
                    # print(appname + " : " + category)
                    categorynumber = self.get_category_number(category)
                    self.PardusAppListStore.append([appicon, appname, categorynumber, prettyname, category])
            else:
                print("User want to use server icons [app]")
                self.serverappicons = self.Server.getAppIcons()
                print("{} : {}".format("serverappicons", self.serverappicons))
                if self.serverappicons:
                    for app in self.Server.applist:
                        appicon = self.getServerAppIcon(app["name"])
                        appname = app['name']
                        prettyname = app['prettyname']["en"]
                        category = ""
                        for i in app['category']:
                            category += i["en"] + ","
                        category = category.rstrip(",")
                        # print(appname + " : " + category)
                        categorynumber = self.get_category_number(category)
                        self.PardusAppListStore.append([appicon, appname, categorynumber, prettyname, category])
                else:
                    print("user want to use server icons [app]; but serverappicons return as false")

    def setPardusCategories(self):
        if self.Server.connection:
            self.allcats = ["all"]
            for app in self.Server.catlist:
                self.allcats.append(app['en'])
            self.categories = sorted(list(set(self.allcats)))

            if self.UserSettings.config_usi:
                print("User want to use system icons [cat]")

                for cat in self.categories:
                    caticon = Gtk.Image.new()
                    caticon.set_from_pixbuf(self.getSystemCatIcon(cat))
                    label = Gtk.Label.new()
                    label_text = str(cat).capitalize()
                    label.set_text(" " + label_text)
                    box1 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
                    box1.pack_start(caticon, False, True, 0)
                    box1.pack_start(label, False, True, 0)
                    box1.set_name("homecats")
                    self.HomeCategoryFlowBox.add(box1)
            else:
                print("User want to use server icons [cat]")
                self.servercaticons = self.Server.getCategoryIcons()
                print("{} : {}".format("servercaticons", self.servercaticons))
                if self.servercaticons:
                    for cat in self.categories:
                        caticon = Gtk.Image.new()
                        caticon.set_from_pixbuf(self.getServerCatIcon(cat))
                        label = Gtk.Label.new()
                        label_text = str(cat).capitalize()
                        label.set_text(" " + label_text)
                        box1 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
                        box1.pack_start(caticon, False, True, 0)
                        box1.pack_start(label, False, True, 0)
                        box1.set_name("homecats")
                        self.HomeCategoryFlowBox.add(box1)
                else:
                    print("user want to use server icons [cat]; but servercaticons return as false")

            self.HomeCategoryFlowBox.show_all()

    def getSystemCatIcon(self, cat, size=48):
        try:
            caticon = Gtk.IconTheme.get_default().load_icon("applications-" + cat, size, Gtk.IconLookupFlags(16))
        except:
            if cat == "education":
                caticon = Gtk.IconTheme.get_default().load_icon("applications-science", size, Gtk.IconLookupFlags(16))
            elif cat == "all":
                caticon = Gtk.IconTheme.get_default().load_icon("applications-other", size, Gtk.IconLookupFlags(16))
            else:
                try:
                    caticon = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", size, Gtk.IconLookupFlags(16))
                except:
                    caticon = Gtk.IconTheme.get_default().load_icon("image-missing", size, Gtk.IconLookupFlags(16))
        return caticon

    def getServerCatIcon(self, cat, size=48):
        try:
            caticon = GdkPixbuf.Pixbuf.new_from_file_at_size(
                self.Server.cachedir + "categoryicons/applications-" + cat + ".svg", size, size)
        except:
            print("{} {}".format(cat, "category icon not found in server icons"))
            try:
                caticon = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", size, Gtk.IconLookupFlags(16))
            except:
                caticon = Gtk.IconTheme.get_default().load_icon("image-missing", size, Gtk.IconLookupFlags(16))
        return caticon

    def getSystemAppIcon(self, app, size=64):
        try:
            appicon = Gtk.IconTheme.get_default().load_icon(app, size, Gtk.IconLookupFlags(16))
        except:
            try:
                appicon = self.parduspixbuf.load_icon(app, size, Gtk.IconLookupFlags(16))
            except:
                try:
                    appicon = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", size, Gtk.IconLookupFlags(16))
                except:
                    appicon = Gtk.IconTheme.get_default().load_icon("image-missing", size, Gtk.IconLookupFlags(16))
        return appicon

    def getServerAppIcon(self, app, size=64):
        try:
            appicon = GdkPixbuf.Pixbuf.new_from_file_at_size(self.Server.cachedir + "appicons/" + app + ".svg", size,
                                                             size)
        except:
            try:
                appicon = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", size, Gtk.IconLookupFlags(16))
            except:
                appicon = Gtk.IconTheme.get_default().load_icon("image-missing", size, Gtk.IconLookupFlags(16))
        return appicon

    def on_timeout(self, user_data):
        if self.splashbarstatus:
            self.splashbar.pulse()
        else:
            self.splashbar.set_fraction(0)
        return True

    def get_category_number(self, thatcategory):
        listcat = list(thatcategory.split(","))
        lenlistcat = len(listcat)
        lencat = len(self.categories)
        for i in range(0, lencat):
            for j in range(0, lenlistcat):
                if self.categories[i] == listcat[j]:
                    return i

    def get_category_name(self, thatnumber):
        lencat = len(self.categories)
        for i in range(0, lencat):
            if thatnumber == i:
                return self.categories[i]

    def get_repo_category_number(self, thatcategory):
        repocatnumber = 404
        for i in self.Package.sections:
            if thatcategory == i["name"]:
                repocatnumber = i["number"]
        return repocatnumber

    def onDestroy(self, widget):
        self.MainWindow.destroy()

    def on_menubackbutton_clicked(self, widget):
        print("menuback")
        if self.homestack.get_visible_child_name() == "pardusapps":
            self.homestack.set_visible_child_name("pardushome")
            self.HomeCategoryFlowBox.unselect_all()
            self.EditorAppsIconView.unselect_all()
            self.menubackbutton.set_sensitive(False)
        elif self.homestack.get_visible_child_name() == "pardusappsdetail":
            self.homestack.set_visible_child_name("pardusapps")
            self.PardusAppsIconView.unselect_all()

    def on_PardusAppsIconView_selection_changed(self, iconview):

        self.menubackbutton.set_sensitive(True)

        self.descSw.set_state(False)

        selected_items = iconview.get_selected_items()

        if len(selected_items) == 1:
            treeiter = self.PardusCategoryFilter.get_iter(selected_items[0])
            self.appname = self.PardusCategoryFilter.get(treeiter, 1)[0]
            prettyname = self.PardusCategoryFilter.get(treeiter, 3)[0]
            print(selected_items[0])
            print(self.appname)

            self.homestack.set_visible_child_name("pardusappsdetail")

            if self.UserSettings.config_usi:
                pixbuf = self.getSystemAppIcon(self.appname, 128)
            else:
                pixbuf = self.getServerAppIcon(self.appname, 128)

            self.dIcon.set_from_pixbuf(pixbuf)

            self.description = ""
            for i in self.Server.applist:
                if i["name"] == self.appname:
                    self.description = i["description"]["en"]
                    self.section = i["section"][0]["en"]
                    self.maintainer_name = i["maintainer"][0]["name"]
                    self.maintainer_mail = i["maintainer"][0]["mail"]
                    self.maintainer_web = i["maintainer"][0]["website"]
                    self.category = i["category"][0]["en"].capitalize()
                    self.license = i["license"]
                    self.codenames = ", ".join(c["name"] for c in i["codename"])
                    self.gnomename = i["gnomename"]
                    self.screenshots = i["screenshots"]

            if self.gnomename != "" and self.gnomename is not None:
                try:
                    self.setGnomeRatings(self.gnomeratings[self.gnomename])
                except:
                    self.setGnomeRatings("")
                    print("{} {}".format(self.gnomename, "not found in gnomeratings"))
            else:
                self.setGnomeRatings("")

            if self.description.count("\n") > 5:
                self.s_description = "\n".join(self.description.splitlines()[0:5])
                self.descSwBox.set_visible(True)
                self.dDescriptionLabel.set_text(self.s_description)
            else:
                self.descSwBox.set_visible(False)
                self.dDescriptionLabel.set_text(self.description)

            self.dName.set_markup("<span font='23'><b>" + prettyname + "</b></span>")
            self.dSection.set_markup("<i>" + self.section + "</i>")
            self.dMaintainer.set_markup("<i>" + self.maintainer_name + "</i>")
            self.dCategory.set_markup(self.category)
            self.dLicense.set_markup(self.license)
            self.dCodename.set_markup(self.codenames)
            self.dMail.set_markup(
                "<a title='{}' href='mailto:{}'>{}</a>".format(self.maintainer_mail, self.maintainer_mail, "E-Mail"))
            self.dWeb.set_markup(
                "<a title='{}' href='{}'>{}</a>".format(self.maintainer_web, self.maintainer_web, "Website"))
            isinstalled = self.Package.isinstalled(self.appname)

            if isinstalled is not None:
                self.dActionButton.set_sensitive(True)

                version = self.Package.version(self.appname)
                size = self.Package.size(self.appname)
                component = self.Package.component(self.appname)
                if component == "non-free":
                    type = "Non-Free"
                else:
                    type = "Open Source"

                self.dVersion.set_markup(version)
                self.dSize.set_markup(size)
                self.dComponent.set_markup(component)
                self.dType.set_markup(type)

                if isinstalled:
                    if self.dActionButton.get_style_context().has_class("suggested-action"):
                        self.dActionButton.get_style_context().remove_class("suggested-action")
                    self.dActionButton.get_style_context().add_class("destructive-action")
                    self.dActionButton.set_label(" Uninstall")
                    self.dActionButton.set_image(Gtk.Image.new_from_stock("gtk-delete", Gtk.IconSize.BUTTON))
                else:
                    if self.dActionButton.get_style_context().has_class("destructive-action"):
                        self.dActionButton.get_style_context().remove_class("destructive-action")
                    self.dActionButton.get_style_context().add_class("suggested-action")
                    self.dActionButton.set_label(" Install")
                    self.dActionButton.set_image(Gtk.Image.new_from_stock("gtk-save", Gtk.IconSize.BUTTON))
            else:
                self.dActionButton.set_sensitive(False)
                if self.dActionButton.get_style_context().has_class("destructive-action"):
                    self.dActionButton.get_style_context().remove_class("destructive-action")
                if self.dActionButton.get_style_context().has_class("suggested-action"):
                    self.dActionButton.get_style_context().remove_class("suggested-action")

                self.dActionButton.set_label(" Not Found")
                self.dActionButton.set_image(Gtk.Image.new_from_stock("gtk-dialog-warning", Gtk.IconSize.BUTTON))

            self.pixbuf1 = None
            self.pixbuf2 = None

            if self.screenshots[0] + "#1" in self.AppImage.imgcache:
                print("image1 in cache")
                self.pixbuf1 = self.AppImage.imgcache[self.screenshots[0] + "#1"]
                self.resizeAppImage()
            else:
                self.pixbuf1 = None
                print("image1 not in cache")
                self.AppImage.fetch(self.Server.serverurl, self.screenshots[0], "#1")

            if self.screenshots[1] + "#2" in self.AppImage.imgcache:
                print("image2 in cache")
                self.pixbuf2 = self.AppImage.imgcache[self.screenshots[1] + "#2"]
                self.resizeAppImage()
            else:
                print("image2 not in cache")
                self.pixbuf2 = None
                self.AppImage.fetch(self.Server.serverurl, self.screenshots[1], "#2")

            dic = {"mac": self.mac, "app": self.appname}
            self.AppDetail.get("POST", self.Server.serverurl + "/api/v2/details", dic)

    def on_descSw_state_set(self, switch, state):
        print("switched {}".format(state))
        if state:
            self.dDescriptionLabel.set_text(self.description)
        else:
            self.dDescriptionLabel.set_text(self.s_description)

    def Detail(self, status, response):
        if status:
            print(response)
            self.dtDownload.set_markup(
                "{} {}".format(response["details"]["download"]["count"], "Download"))

            self.dtTotalRating.set_markup(
                "{} {}".format(response["details"]["rate"]["count"], "Ratings"))

            self.dtAverageRating.set_markup(
                "<big>{:.1f}</big>".format(float(response["details"]["rate"]["average"])))

            if response["details"]["rate"]["individual"] == 0:
                self.dtUserRating.set_markup(
                    "{} {}".format("Your Rate", "is None"))
            else:
                self.dtUserRating.set_markup(
                    "{} {}".format("Your Rate", response["details"]["rate"]["individual"]))

            self.setAppStar(response["details"]["rate"]["average"])

            self.setPardusRatings(response["details"]["rate"]["count"], response["details"]["rate"]["average"],
                                  response["details"]["rate"]["rates"]["1"], response["details"]["rate"]["rates"]["2"],
                                  response["details"]["rate"]["rates"]["3"], response["details"]["rate"]["rates"]["4"],
                                  response["details"]["rate"]["rates"]["5"])

    def setAppStar(self, average):
        average = int(average)

        if average == 0:
            self.dtStar1.set_from_pixbuf(self.staroff)
            self.dtStar2.set_from_pixbuf(self.staroff)
            self.dtStar3.set_from_pixbuf(self.staroff)
            self.dtStar4.set_from_pixbuf(self.staroff)
            self.dtStar5.set_from_pixbuf(self.staroff)
        elif average == 1:
            self.dtStar1.set_from_pixbuf(self.staron)
            self.dtStar2.set_from_pixbuf(self.staroff)
            self.dtStar3.set_from_pixbuf(self.staroff)
            self.dtStar4.set_from_pixbuf(self.staroff)
            self.dtStar5.set_from_pixbuf(self.staroff)
        elif average == 2:
            self.dtStar1.set_from_pixbuf(self.staron)
            self.dtStar2.set_from_pixbuf(self.staron)
            self.dtStar3.set_from_pixbuf(self.staroff)
            self.dtStar4.set_from_pixbuf(self.staroff)
            self.dtStar5.set_from_pixbuf(self.staroff)
        elif average == 3:
            self.dtStar1.set_from_pixbuf(self.staron)
            self.dtStar2.set_from_pixbuf(self.staron)
            self.dtStar3.set_from_pixbuf(self.staron)
            self.dtStar4.set_from_pixbuf(self.staroff)
            self.dtStar5.set_from_pixbuf(self.staroff)
        elif average == 4:
            self.dtStar1.set_from_pixbuf(self.staron)
            self.dtStar2.set_from_pixbuf(self.staron)
            self.dtStar3.set_from_pixbuf(self.staron)
            self.dtStar4.set_from_pixbuf(self.staron)
            self.dtStar5.set_from_pixbuf(self.staroff)
        elif average == 5:
            self.dtStar1.set_from_pixbuf(self.staron)
            self.dtStar2.set_from_pixbuf(self.staron)
            self.dtStar3.set_from_pixbuf(self.staron)
            self.dtStar4.set_from_pixbuf(self.staron)
            self.dtStar5.set_from_pixbuf(self.staron)
        else:
            print("star error")

    def setPardusRatings(self, tr, r, r1, r2, r3, r4, r5):
        self.dPardusRating.set_markup("<span font='21'><big><b>{:.1f}</b></big></span>".format(float(r)))
        self.dPardusBarLabel1.set_markup("{}".format(r1))
        self.dPardusBarLabel2.set_markup("{}".format(r2))
        self.dPardusBarLabel3.set_markup("{}".format(r3))
        self.dPardusBarLabel4.set_markup("{}".format(r4))
        self.dPardusBarLabel5.set_markup("{}".format(r5))

        if tr != 0:
            self.dPardusBar1.set_fraction(r1 / tr)
            self.dPardusBar2.set_fraction(r2 / tr)
            self.dPardusBar3.set_fraction(r3 / tr)
            self.dPardusBar4.set_fraction(r4 / tr)
            self.dPardusBar5.set_fraction(r5 / tr)
        else:
            self.dPardusBar1.set_fraction(0)
            self.dPardusBar2.set_fraction(0)
            self.dPardusBar3.set_fraction(0)
            self.dPardusBar4.set_fraction(0)
            self.dPardusBar5.set_fraction(0)

    def setGnomeRatings(self, gr):
        if gr != "":
            print(gr)

            average = (gr["star1"] * 1 + gr["star2"] * 2 + gr["star3"] * 3 + gr["star4"] * 4 + gr["star5"] * 5) / gr[
                "total"]

            self.dGnomeRating.set_markup("<span font='21'><big><b>{:.1f}</b></big></span>".format(float(average)))
            self.dGnomeBarLabel1.set_markup("{}".format(gr["star1"]))
            self.dGnomeBarLabel2.set_markup("{}".format(gr["star2"]))
            self.dGnomeBarLabel3.set_markup("{}".format(gr["star3"]))
            self.dGnomeBarLabel4.set_markup("{}".format(gr["star4"]))
            self.dGnomeBarLabel5.set_markup("{}".format(gr["star5"]))

            if gr["total"] != 0:
                self.dGnomeBar1.set_fraction(gr["star1"] / gr["total"])
                self.dGnomeBar2.set_fraction(gr["star2"] / gr["total"])
                self.dGnomeBar3.set_fraction(gr["star3"] / gr["total"])
                self.dGnomeBar4.set_fraction(gr["star4"] / gr["total"])
                self.dGnomeBar5.set_fraction(gr["star5"] / gr["total"])
            else:
                self.dGnomeBar1.set_fraction(0)
                self.dGnomeBar2.set_fraction(0)
                self.dGnomeBar3.set_fraction(0)
                self.dGnomeBar4.set_fraction(0)
                self.dGnomeBar5.set_fraction(0)
        else:
            self.dGnomeRating.set_markup("<span font='21'><big><b>{}</b></big></span>".format(0.0))
            self.dGnomeBarLabel1.set_markup("{}".format(0))
            self.dGnomeBarLabel2.set_markup("{}".format(0))
            self.dGnomeBarLabel3.set_markup("{}".format(0))
            self.dGnomeBarLabel4.set_markup("{}".format(0))
            self.dGnomeBarLabel5.set_markup("{}".format(0))
            self.dGnomeBar1.set_fraction(0)
            self.dGnomeBar2.set_fraction(0)
            self.dGnomeBar3.set_fraction(0)
            self.dGnomeBar4.set_fraction(0)
            self.dGnomeBar5.set_fraction(0)

    def on_test(self, widget, event):
        print("test")

    def Pixbuf(self, status, pixbuf, i):
        if status and i:
            i = i.split("#")[1]
            if i == "1":
                self.pixbuf1 = pixbuf
                self.resizeAppImage()
            if i == "2":
                self.pixbuf2 = pixbuf
                self.resizeAppImage()
        else:
            print("image not in cache")
            self.dImage1.set_from_pixbuf(self.missing_pixbuf)
            self.dImage2.set_from_pixbuf(self.missing_pixbuf)

            self.pop1Image.set_from_pixbuf(self.missing_pixbuf)
            self.pop2Image.set_from_pixbuf(self.missing_pixbuf)

    def on_PardusAppDetailBox_size_allocate(self, widget, allocated):

        # we are resizing app images when PardusAppsDetail size changed

        # self.resizeAppImage()

        self.resizePopImage()

    def resizeAppImage(self):
        allocation = self.MainWindow.get_allocation()
        w = allocation.width / 3.3  # this is for detail Image
        h = allocation.height / 3.3  # this is for detail Image

        pw = allocation.width / 1.3  # this is for popup Image
        ph = allocation.height / 1.3  # this is for popup Image

        if self.pixbuf1:
            pixbuf = self.pixbuf1.scale_simple(w, h, GdkPixbuf.InterpType.BILINEAR)
            self.dImage1.set_from_pixbuf(pixbuf)

            poppixbuf = self.pixbuf1.scale_simple(pw, ph, GdkPixbuf.InterpType.BILINEAR)
            self.pop1Image.set_from_pixbuf(poppixbuf)

        if self.pixbuf2:
            pixbuf = self.pixbuf2.scale_simple(w, h, GdkPixbuf.InterpType.BILINEAR)
            self.dImage2.set_from_pixbuf(pixbuf)

            poppixbuf = self.pixbuf2.scale_simple(pw, ph, GdkPixbuf.InterpType.BILINEAR)
            self.pop2Image.set_from_pixbuf(poppixbuf)

    def resizePopImage(self):
        # we are resizing only popup images because there is a bug others
        allocation = self.MainWindow.get_allocation()
        pw = allocation.width / 1.3  # this is for popup Image
        ph = allocation.height / 1.3  # this is for popup Image

        if self.pixbuf1:
            poppixbuf = self.pixbuf1.scale_simple(pw, ph, GdkPixbuf.InterpType.BILINEAR)
            self.pop1Image.set_from_pixbuf(poppixbuf)
        if self.pixbuf2:
            poppixbuf = self.pixbuf2.scale_simple(pw, ph, GdkPixbuf.InterpType.BILINEAR)
            self.pop2Image.set_from_pixbuf(poppixbuf)

    def on_EditorAppsIconView_selection_changed(self, iconview):

        self.menubackbutton.set_sensitive(True)

        selected_items = iconview.get_selected_items()

        if len(selected_items) == 1:
            treeiter = self.EditorListStore.get_iter(selected_items[0])
            self.appname = self.EditorListStore.get(treeiter, 1)[0]
            prettyname = self.EditorListStore.get(treeiter, 3)[0]
            print(selected_items[0])
            print(self.appname)

            self.homestack.set_visible_child_name("pardusappsdetail")

            try:
                pixbuf = Gtk.IconTheme.get_default().load_icon(self.appname, 96, Gtk.IconLookupFlags(16))
                # pixbuf = self.appiconpixbuf.load_icon(app['name'], 64, 0)
            except:
                # pixbuf = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", 64, 0)
                try:
                    pixbuf = self.parduspixbuf.load_icon(self.appname, 96, Gtk.IconLookupFlags(16))
                except:
                    try:
                        pixbuf = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", 96, Gtk.IconLookupFlags(16))
                    except:
                        pixbuf = Gtk.IconTheme.get_default().load_icon("image-missing", 96, Gtk.IconLookupFlags(16))

            self.dIcon.set_from_pixbuf(pixbuf)

            self.dName.set_markup("<b> " + prettyname + "</b>")

            self.dDescriptionLabel.set_text(self.Package.description(self.appname, True))

            if self.Package.isinstalled(self.appname):
                if self.dActionButton.get_style_context().has_class("suggested-action"):
                    self.dActionButton.get_style_context().remove_class("suggested-action")
                self.dActionButton.get_style_context().add_class("destructive-action")
                self.dActionButton.set_label(" Uninstall")
                self.dActionButton.set_image(Gtk.Image.new_from_stock("gtk-delete", Gtk.IconSize.BUTTON))
            else:
                if self.dActionButton.get_style_context().has_class("destructive-action"):
                    self.dActionButton.get_style_context().remove_class("destructive-action")
                self.dActionButton.get_style_context().add_class("suggested-action")
                self.dActionButton.set_label(" Install")
                self.dActionButton.set_image(Gtk.Image.new_from_stock("gtk-save", Gtk.IconSize.BUTTON))

            print(self.Package.isinstalled(self.appname))

            self.Package.missingdeps(self.appname)

    def PardusCategoryFilterFunction(self, model, iteration, data):
        search_entry_text = self.pardussearchbar.get_text()
        categorynumber = int(model[iteration][2])
        category = model[iteration][4]
        appname = model[iteration][1]
        showinstalled = self.pardusicb.get_active()

        if self.isPardusSearching:
            self.HomeCategoryFlowBox.unselect_all()
            if search_entry_text in appname:
                if self.pardusicb.get_active():
                    if self.Package.isinstalled(appname):
                        return True
                else:
                    return True
        else:
            if self.PardusCurrentCategoryString == "all":
                if self.pardusicb.get_active():
                    if self.Package.isinstalled(appname):
                        return True
                else:
                    return True
            else:
                if self.PardusCurrentCategoryString in category:
                    if self.pardusicb.get_active():
                        if self.Package.isinstalled(appname):
                            return True
                    else:
                        return True

    def on_pardusicb_toggled(self, button):
        self.PardusCategoryFilter.refilter()

    # def RepoCategoryFilterFunction(self, model, iteration, data):
    #     search_entry_text = self.reposearchbar.get_text()
    #     appname = model[iteration][0]
    #     categorynumber = int(model[iteration][2])
    #     category = model[iteration][1]
    #
    #     if self.isRepoSearching:
    #         self.RepoCategoryListBox.unselect_all()
    #         if search_entry_text in appname:
    #             return True
    #     else:
    #         if self.RepoCurrentCategory == "all":
    #             return True
    #         elif self.RepoCurrentCategory == "empty":
    #             return True
    #         else:
    #             return category == self.RepoCurrentCategory

    def on_HomeCategoryFlowBox_child_activated(self, flow_box, child):
        self.isPardusSearching = False
        self.mainstack.set_visible_child_name("page2")
        self.homestack.set_visible_child_name("pardusapps")
        self.menubackbutton.set_sensitive(True)
        self.PardusCurrentCategory = child.get_index()

        self.PardusCurrentCategoryString = self.get_category_name(self.PardusCurrentCategory)
        print("home category selected " + str(self.PardusCurrentCategory) + " " + self.PardusCurrentCategoryString)

        if self.UserSettings.config_usi:
            pixbuf = self.getSystemCatIcon(self.PardusCurrentCategoryString, 32)
        else:
            pixbuf = self.getServerCatIcon(self.PardusCurrentCategoryString, 32)

        self.NavCategoryImage.set_from_pixbuf(pixbuf)
        self.NavCategoryLabel.set_text(self.PardusCurrentCategoryString.capitalize())
        self.PardusCategoryFilter.refilter()

    def on_HomeCategoryFlowBox_selected_children_changed(self, flow_box):
        print("on_HomeCategoryFlowBox_selected_children_changed")
        self.isPardusSearching = False

    def on_RepoCategoryListBox_row_selected(self, listbox, row):
        # self.CurrentCategory = row.get_index()
        # self.CategoryFilter.refilter()
        # self.stack.set_visible_child_name("page0")
        self.isRepoSearching = False

    def on_RepoCategoryListBox_row_activated(self, listbox, row):
        self.isRepoSearching = False
        # self.RepoCurrentCategory = row.get_index()
        self.RepoCurrentCategory = row.get_child().get_text().lower().strip()
        print(row.get_child().get_text().lower().strip())

        if self.useDynamicListStore:

            if self.RepoCurrentCategory != "all":

                self.RepoAppsTreeView.set_model(self.storedict[self.RepoCurrentCategory])
                self.RepoAppsTreeView.show_all()

            else:
                self.RepoAppsTreeView.set_model(self.RepoAppListStore)
                self.RepoAppsTreeView.show_all()

        else:

            if self.RepoCurrentCategory != "all":

                self.store = Gtk.ListStore(str, str, int, bool, str, str)

                for i in self.repoapps[self.RepoCurrentCategory]:
                    installstatus = self.Package.isinstalled(i["name"])
                    if installstatus:
                        installtext = "Remove"
                    else:
                        installtext = "Install"
                    self.store.append(
                        [i["name"], i["category"], 0, installstatus, installtext, self.Package.summary(i["name"])])

                # print(self.repoapps[self.RepoCurrentCategory])

                self.RepoAppsTreeView.set_model(self.store)

                self.RepoAppsTreeView.show_all()

            else:
                self.RepoAppsTreeView.set_model(self.RepoAppListStore)
                self.RepoAppsTreeView.show_all()

        # self.RepoCategoryFilter.refilter()
        # print("category selected")

    def on_dActionButton_clicked(self, button):
        self.actionPackage()
        print("action " + self.appname)

    def on_topbutton1_clicked(self, button):
        if self.Server.connection and self.Server.app_scode == 200 and self.Server.cat_scode == 200:
            self.searchstack.set_visible_child_name("page0")
            self.homestack.set_visible_child_name("pardushome")
            self.HomeCategoryFlowBox.unselect_all()
            self.EditorAppsIconView.unselect_all()
            self.PardusAppsIconView.unselect_all()
        else:
            self.searchstack.set_visible_child_name("page2")
            self.homestack.set_visible_child_name("noserver")

        self.menubackbutton.set_sensitive(False)
        if self.topbutton2.get_style_context().has_class("suggested-action"):
            self.topbutton2.get_style_context().remove_class("suggested-action")
        if not self.topbutton1.get_style_context().has_class("suggested-action"):
            self.topbutton1.get_style_context().add_class("suggested-action")

    def on_topbutton2_clicked(self, button):
        self.searchstack.set_visible_child_name("page1")
        self.homestack.set_visible_child_name("repohome")
        self.menubackbutton.set_sensitive(False)
        if self.topbutton1.get_style_context().has_class("suggested-action"):
            self.topbutton1.get_style_context().remove_class("suggested-action")
        if not self.topbutton2.get_style_context().has_class("suggested-action"):
            self.topbutton2.get_style_context().add_class("suggested-action")

    def on_pardussearchbar_search_changed(self, entry_search):
        self.isPardusSearching = True
        self.homestack.set_visible_child_name("pardusapps")
        self.menubackbutton.set_sensitive(True)
        # self.SearchFilter.refilter()
        self.PardusCategoryFilter.refilter()

    def on_pardussearchbar_button_press_event(self, widget, click):
        self.homestack.set_visible_child_name("pardusapps")
        # self.SearchFilter.refilter()
        self.menubackbutton.set_sensitive(True)
        self.isPardusSearching = True
        print("on_searchbar_button_press_event")
        self.PardusCategoryFilter.refilter()

    def on_pardussearchbar_focus_in_event(self, widget, click):
        self.homestack.set_visible_child_name("pardusapps")
        self.menubackbutton.set_sensitive(True)
        print("on_searchbar_focus_in_event")
        self.isPardusSearching = True
        self.PardusAppsIconView.unselect_all()

        if self.UserSettings.config_usi:
            pixbuf = self.getSystemCatIcon("all", 32)
        else:
            pixbuf = self.getServerCatIcon("all", 32)

        self.NavCategoryImage.set_from_pixbuf(pixbuf)
        self.NavCategoryLabel.set_text("All")
        self.PardusCategoryFilter.refilter()

    def on_reposearchbar_search_changed(self, entry_search):
        print(entry_search.get_text())

        # searchstore = Gtk.ListStore(str, str)
        # for i in self.Package.apps:
        #     if entry_search.get_text() in i["name"]:
        #         searchstore.append([i["name"], i["category"]])
        #
        # self.RepoAppsTreeView.set_model(searchstore)
        # self.RepoAppsTreeView.show_all()

    def on_reposearchbar_button_press_event(self, widget, click):
        print("on_reposearchbar_button_press_event")

    def on_reposearchbar_focus_in_event(self, widget, click):
        print("on_reposearchbar_focus_in_event")
        # if self.reposearchbar.get_text() != "":
        #     self.RepoCategoryFilter.refilter()

    def on_reposearchbutton_clicked(self, button):
        # self.RepoCategoryListBox.unselect_all()
        self.isRepoSearching = True
        print("on_reposearchbutton_clicked")

        self.searchstore = Gtk.ListStore(str, str, int, bool, str, str)
        for i in self.Package.apps:
            if self.reposearchbar.get_text() in i["name"]:
                installstatus = self.Package.isinstalled(i["name"])
                if installstatus:
                    installtext = "Remove"
                else:
                    installtext = "Install"
                self.searchstore.append(
                    [i["name"], i["category"], 0, installstatus, installtext, self.Package.summary(i["name"])])

        self.RepoAppsTreeView.set_model(self.searchstore)
        self.RepoAppsTreeView.show_all()

    def on_RepoAppsTreeView_row_activated(self, tree_view, path, column):

        # if not self.isRepoSearching:
        #     if self.useDynamicListStore:
        #         if self.RepoCurrentCategory != "all":
        #             iter = self.storedict[self.RepoCurrentCategory].get_iter(path)
        #             value = self.storedict[self.RepoCurrentCategory].get_value(iter, 0)
        #         else:
        #             iter = self.RepoAppListStore.get_iter(path)
        #             value = self.RepoAppListStore.get_value(iter, 0)
        #     else:
        #         if self.RepoCurrentCategory != "all":
        #             iter = self.store.get_iter(path)
        #             value = self.store.get_value(iter, 0)
        #         else:
        #             iter = self.RepoAppListStore.get_iter(path)
        #             value = self.RepoAppListStore.get_value(iter, 0)
        # else:

        iter = self.searchstore.get_iter(path)
        value = self.searchstore.get_value(iter, 0)

        if self.Package.isinstalled(value):
            if self.raction.get_style_context().has_class("suggested-action"):
                self.raction.get_style_context().remove_class("suggested-action")
            self.raction.get_style_context().add_class("destructive-action")
            self.raction.set_label(" Uninstall")
            self.raction.set_image(Gtk.Image.new_from_stock("gtk-delete", Gtk.IconSize.BUTTON))
        else:
            if self.raction.get_style_context().has_class("destructive-action"):
                self.raction.get_style_context().remove_class("destructive-action")
            self.raction.get_style_context().add_class("suggested-action")
            self.raction.set_label(" Install")
            self.raction.set_image(Gtk.Image.new_from_stock("gtk-save", Gtk.IconSize.BUTTON))

        self.rbotstack.set_visible_child_name("page1")
        self.rtitle.set_text(self.Package.summary(value))
        self.rdetail.set_text(self.Package.description(value, False))

        print(value)

    def on_topsearchbutton_toggled(self, button):
        if self.topsearchbutton.get_active():
            self.toprevealer.set_reveal_child(True)
            if self.searchstack.get_visible_child_name() == "page0":
                self.pardussearchbar.grab_focus()
            elif self.searchstack.get_visible_child_name() == "page1":
                self.reposearchbar.grab_focus()
        else:
            self.toprevealer.set_reveal_child(False)

    def on_menu1_select(self, menu_item):
        self.UserSettings.readConfig()
        self.switchUSI.set_state(self.UserSettings.config_usi)
        self.switchEA.set_state(self.UserSettings.config_anim)
        self.dialogpref.run()
        self.dialogpref.hide()

    def on_dpApply_clicked(self, button):
        usi = self.switchUSI.get_state()
        ea = self.switchEA.get_state()
        print("USI : {}".format(usi))
        print("EA : {}".format(ea))

        if self.UserSettings.writeConfig(usi, ea):
            self.dpApply.set_sensitive(False)
            self.dpApply.set_label("Applied")
        else:
            self.dpApply.set_label("Error")


    def on_switchUSI_state_set(self, switch, state):
        self.dpApply.set_sensitive(True)
        self.dpApply.set_label("Apply")
        self.dpApply.set_image(Gtk.Image.new_from_stock("gtk-apply", Gtk.IconSize.BUTTON))


    def on_switchEA_state_set(self, switch, state):
        self.dpApply.set_sensitive(True)
        self.dpApply.set_label("Apply")
        self.dpApply.set_image(Gtk.Image.new_from_stock("gtk-apply", Gtk.IconSize.BUTTON))

    def actionPackage(self):

        self.topspinner.start()

        self.dActionButton.set_sensitive(False)

        self.dActionButton.set_image(Gtk.Image.new_from_stock("gtk-convert", Gtk.IconSize.BUTTON))

        self.actionedappname = self.appname

        self.isinstalled = self.Package.isinstalled(self.actionedappname)

        if self.isinstalled:
            self.dActionButton.set_label(" Removing")
            command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py", "remove",
                       self.actionedappname]
        else:
            self.dActionButton.set_label(" Installing")
            command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py", "install",
                       self.actionedappname]

        pid = self.startProcess(command)
        print(pid)

    def startProcess(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(params, flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_output=True, standard_error=True)
        GLib.io_add_watch(GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.onProcessStdout)
        GLib.io_add_watch(GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.onProcessStderr)
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, self.onProcessExit)

    def onProcessStdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False

        print(source.readline())
        return True

    def onProcessStderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False

        line = source.readline()

        print("error: " + line)

        if "dlstatus" in line:
            percent = line.split(":")[2].split(".")[0]
            if self.Package.missingdeps(self.actionedappname):
                print("Downloading dependencies " + percent + " %")
                self.progresstextlabel.set_text(
                    self.actionedappname + " | " + "Downloading dependencies : " + percent + " %")
            else:
                print("Controlling dependencies : " + percent + " %")
                self.progresstextlabel.set_text(
                    self.actionedappname + " | " + "Controlling dependencies : " + percent + " %")
        elif "pmstatus" in line:
            percent = line.split(":")[2].split(".")[0]
            print("Processing : " + percent)
            if self.isinstalled:
                self.progresstextlabel.set_text(self.actionedappname + " | " + "Removing" + ": " + percent + " %")
            else:
                self.progresstextlabel.set_text(self.actionedappname + " | " + "Installing" + ": " + percent + " %")
        return True

    def onProcessExit(self, pid, status):
        if status == 0:

            if self.isinstalled:
                self.progresstextlabel.set_text(self.actionedappname + " | Removed : 100 %")
            else:
                self.progresstextlabel.set_text(self.actionedappname + " | Installed : 100 %")
            self.Package.updatecache()
            self.controlView()
            self.notify()
        else:
            self.progresstextlabel.set_text(self.actionedappname + " | " + " Not Completed")
            self.controlView()

        self.dActionButton.set_sensitive(True)
        self.topspinner.stop()
        print(status)

    def controlView(self):
        selected_items = self.PardusAppsIconView.get_selected_items()
        print("selected_items " + str(selected_items))
        if len(selected_items) == 1:
            treeiter = self.PardusCategoryFilter.get_iter(selected_items[0])
            appname = self.PardusCategoryFilter.get(treeiter, 1)[0]
            prettyname = self.PardusCategoryFilter.get(treeiter, 3)[0]
            print("in controlView " + appname)
            if appname == self.actionedappname:
                try:
                    pixbuf = Gtk.IconTheme.get_default().load_icon(self.actionedappname, 96, Gtk.IconLookupFlags(16))
                except:
                    try:
                        pixbuf = self.parduspixbuf.load_icon(self.actionedappname, 96, Gtk.IconLookupFlags(16))
                    except:
                        try:
                            pixbuf = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", 96,
                                                                           Gtk.IconLookupFlags(16))
                        except:
                            pixbuf = Gtk.IconTheme.get_default().load_icon("image-missing", 96,
                                                                           Gtk.IconLookupFlags(16))

                self.dIcon.set_from_pixbuf(pixbuf)

                self.dName.set_markup("<b> " + prettyname + "</b>")

                if self.Package.isinstalled(self.actionedappname):
                    if self.dActionButton.get_style_context().has_class("suggested-action"):
                        self.dActionButton.get_style_context().remove_class("suggested-action")
                    self.dActionButton.get_style_context().add_class("destructive-action")
                    self.dActionButton.set_label(" Uninstall")
                    self.dActionButton.set_image(Gtk.Image.new_from_stock("gtk-delete", Gtk.IconSize.BUTTON))
                else:
                    if self.dActionButton.get_style_context().has_class("destructive-action"):
                        self.dActionButton.get_style_context().remove_class("destructive-action")
                    self.dActionButton.get_style_context().add_class("suggested-action")
                    self.dActionButton.set_label(" Install")
                    self.dActionButton.set_image(Gtk.Image.new_from_stock("gtk-save", Gtk.IconSize.BUTTON))

    def notify(self):

        if Notify.is_initted():
            Notify.uninit()

        Notify.init(self.actionedappname)
        if self.isinstalled:
            notification = Notify.Notification.new(self.actionedappname + " Removed")
        else:
            notification = Notify.Notification.new(self.actionedappname + " Installed")
        try:
            pixbuf = Gtk.IconTheme.get_default().load_icon(self.actionedappname, 96, Gtk.IconLookupFlags(16))
        except:
            try:
                pixbuf = self.parduspixbuf.load_icon(self.actionedappname, 96, Gtk.IconLookupFlags(16))
            except:
                try:
                    pixbuf = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", 96, Gtk.IconLookupFlags(16))
                except:
                    pixbuf = Gtk.IconTheme.get_default().load_icon("image-missing", 96, Gtk.IconLookupFlags(16))

        notification.set_icon_from_pixbuf(pixbuf)
        notification.show()
