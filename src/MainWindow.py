#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import os
import subprocess
import threading
import netifaces
import psutil
from datetime import datetime
import gi, sys

import locale
from locale import gettext as _
from locale import getlocale

locale.bindtextdomain('pardus-software', '/usr/share/locale')
locale.textdomain('pardus-software')

gi.require_version("GLib", "2.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Notify", "0.7")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GLib, Gtk, GObject, Notify, GdkPixbuf, Gio, Gdk

from Package import Package
from Server import Server
from GnomeRatingServer import GnomeRatingServer
# from CellRendererButton import CellRendererButton

from AppImage import AppImage
from AppDetail import AppDetail
from AppRequest import AppRequest
from GnomeComment import GnomeComment

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

        self.locale = self.getLocale()
        print(self.locale)

        self.parduspixbuf = Gtk.IconTheme.new()
        self.parduspixbuf.set_custom_theme("pardus")

        self.error = False
        self.dpkglockerror = False
        self.dpkgconferror = False

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

        self.staronhover = GdkPixbuf.Pixbuf.new_from_file_at_size(
            os.path.dirname(os.path.abspath(__file__)) + "/../images/rating-hover.svg", 24, 24)
        self.staroffhover = GdkPixbuf.Pixbuf.new_from_file_at_size(
            os.path.dirname(os.path.abspath(__file__)) + "/../images/rating-unrated-hover.svg", 24, 24)

        self.cstaron = GdkPixbuf.Pixbuf.new_from_file_at_size(
            os.path.dirname(os.path.abspath(__file__)) + "/../images/rating.svg", 16, 16)
        self.cstaroff = GdkPixbuf.Pixbuf.new_from_file_at_size(
            os.path.dirname(os.path.abspath(__file__)) + "/../images/rating-unrated.svg", 16, 16)

        self.gcstaron = GdkPixbuf.Pixbuf.new_from_file_at_size(
            os.path.dirname(os.path.abspath(__file__)) + "/../images/rating.svg", 16, 16)
        self.gcstaroff = GdkPixbuf.Pixbuf.new_from_file_at_size(
            os.path.dirname(os.path.abspath(__file__)) + "/../images/rating-unrated.svg", 16, 16)

        self.wpcstaron = GdkPixbuf.Pixbuf.new_from_file_at_size(
            os.path.dirname(os.path.abspath(__file__)) + "/../images/rating.svg", 38, 38)
        self.wpcstaroff = GdkPixbuf.Pixbuf.new_from_file_at_size(
            os.path.dirname(os.path.abspath(__file__)) + "/../images/rating-unrated.svg", 38, 38)

        self.isPardusSearching = False
        self.isRepoSearching = False

        self.RepoCategoryListBox = self.GtkBuilder.get_object("RepoCategoryListBox")

        self.HomeCategoryFlowBox = self.GtkBuilder.get_object("HomeCategoryFlowBox")
        self.MostDownFlowBox = self.GtkBuilder.get_object("MostDownFlowBox")
        self.MostRateFlowBox = self.GtkBuilder.get_object("MostRateFlowBox")

        self.hometotaldc = self.GtkBuilder.get_object("hometotaldc")
        self.hometotalrc = self.GtkBuilder.get_object("hometotalrc")
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
        self.bottomrevealer = self.GtkBuilder.get_object("bottomrevealer")

        self.bottomerrorlabel = self.GtkBuilder.get_object("bottomerrorlabel")
        self.bottomerrorbutton = self.GtkBuilder.get_object("bottomerrorbutton")

        self.pardusicb = self.GtkBuilder.get_object("pardusicb")
        self.sortPardusAppsCombo = self.GtkBuilder.get_object("sortPardusAppsCombo")

        self.mainstack = self.GtkBuilder.get_object("mainstack")
        self.homestack = self.GtkBuilder.get_object("homestack")
        self.searchstack = self.GtkBuilder.get_object("searchstack")
        self.bottomstack = self.GtkBuilder.get_object("bottomstack")
        self.commentstack = self.GtkBuilder.get_object("commentstack")
        self.dIcon = self.GtkBuilder.get_object("dIcon")
        self.dName = self.GtkBuilder.get_object("dName")
        self.dActionButton = self.GtkBuilder.get_object("dActionButton")
        self.dOpenButton = self.GtkBuilder.get_object("dOpenButton")
        # self.dOpenButton.get_style_context().add_class("circular")
        self.dDisclaimerButton = self.GtkBuilder.get_object("dDisclaimerButton")
        self.DisclaimerPopover = self.GtkBuilder.get_object("DisclaimerPopover")
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

        self.wpcStar1 = self.GtkBuilder.get_object("wpcStar1")
        self.wpcStar2 = self.GtkBuilder.get_object("wpcStar2")
        self.wpcStar3 = self.GtkBuilder.get_object("wpcStar3")
        self.wpcStar4 = self.GtkBuilder.get_object("wpcStar4")
        self.wpcStar5 = self.GtkBuilder.get_object("wpcStar5")
        self.wpcStarLabel = self.GtkBuilder.get_object("wpcStarLabel")
        self.wpcComment = self.GtkBuilder.get_object("wpcComment")
        self.wpcAuthor = self.GtkBuilder.get_object("wpcAuthor")
        self.wpcSendButton = self.GtkBuilder.get_object("wpcSendButton")
        self.wpcgetnameLabel = self.GtkBuilder.get_object("wpcgetnameLabel")
        self.wpcgetcommentLabel = self.GtkBuilder.get_object("wpcgetcommentLabel")
        self.wpcresultLabel = self.GtkBuilder.get_object("wpcresultLabel")
        self.wpcformcontrolLabel = self.GtkBuilder.get_object("wpcformcontrolLabel")
        self.editCommentButton = self.GtkBuilder.get_object("editCommentButton")

        self.wpcstar = 0

        self.raction = self.GtkBuilder.get_object("raction")
        self.rtitle = self.GtkBuilder.get_object("rtitle")
        self.rdetail = self.GtkBuilder.get_object("rdetail")
        self.rbotstack = self.GtkBuilder.get_object("rbotstack")

        self.topbutton1 = self.GtkBuilder.get_object("topbutton1")
        self.topbutton1.get_style_context().add_class("suggested-action")
        self.topbutton2 = self.GtkBuilder.get_object("topbutton2")
        self.queuebutton = self.GtkBuilder.get_object("queuebutton")

        self.splashspinner = self.GtkBuilder.get_object("splashspinner")
        self.splashbar = self.GtkBuilder.get_object("splashbar")
        self.splashlabel = self.GtkBuilder.get_object("splashlabel")
        self.splashbarstatus = True
        # GLib.timeout_add(200, self.on_timeout, None)

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

        self.HeaderBarMenuButton = self.GtkBuilder.get_object("HeaderBarMenuButton")
        self.PopoverMenu = self.GtkBuilder.get_object("PopoverMenu")

        self.aboutdialog = self.GtkBuilder.get_object("aboutdialog")
        self.aboutdialog.set_program_name(_("Pardus Software Center"))

        self.switchUSI = self.GtkBuilder.get_object("switchUSI")
        self.switchEA = self.GtkBuilder.get_object("switchEA")
        self.preflabel = self.GtkBuilder.get_object("preflabel")
        self.prefapplybutton = self.GtkBuilder.get_object("prefapplybutton")
        self.prefcachebutton = self.GtkBuilder.get_object("prefcachebutton")

        self.menubackbutton = self.GtkBuilder.get_object("menubackbutton")

        self.updatecontrolbutton = self.GtkBuilder.get_object("updatecontrolbutton")
        self.updatetextview = self.GtkBuilder.get_object("updatetextview")
        self.updatespinner = self.GtkBuilder.get_object("updatespinner")

        self.updateerrorlabel = self.GtkBuilder.get_object("updateerrorlabel")

        self.residualtextview = self.GtkBuilder.get_object("residualtextview")
        self.removabletextview = self.GtkBuilder.get_object("removabletextview")
        self.upgradabletextview = self.GtkBuilder.get_object("upgradabletextview")

        self.updatestack = self.GtkBuilder.get_object("updatestack")
        self.updatestack.set_visible_child_name("empty")

        self.upgradebutton = self.GtkBuilder.get_object("upgradebutton")
        self.autoremovebutton = self.GtkBuilder.get_object("autoremovebutton")
        self.residualbutton = self.GtkBuilder.get_object("residualbutton")

        self.upgradablebox = self.GtkBuilder.get_object("upgradablebox")
        self.removablebox = self.GtkBuilder.get_object("removablebox")
        self.residualbox = self.GtkBuilder.get_object("residualbox")

        self.progresstextlabel = self.GtkBuilder.get_object("progresstextlabel")
        self.topspinner = self.GtkBuilder.get_object("topspinner")

        self.noserverlabel = self.GtkBuilder.get_object("noserverlabel")

        self.NavCategoryImage = self.GtkBuilder.get_object("NavCategoryImage")
        self.NavCategoryLabel = self.GtkBuilder.get_object("NavCategoryLabel")

        self.menu_suggestapp = self.GtkBuilder.get_object("menu_suggestapp")

        self.SuggestAppName = self.GtkBuilder.get_object("SuggestAppName")
        self.SuggestCat = self.GtkBuilder.get_object("SuggestCat")
        self.SuggestDescTR = self.GtkBuilder.get_object("SuggestDescTR")
        self.SuggestDescEN = self.GtkBuilder.get_object("SuggestDescEN")
        self.SuggestLicense = self.GtkBuilder.get_object("SuggestLicense")
        self.SuggestCopyright = self.GtkBuilder.get_object("SuggestCopyright")
        self.SuggestWeb = self.GtkBuilder.get_object("SuggestWeb")
        self.SuggestIconChooser = self.GtkBuilder.get_object("SuggestIconChooser")
        self.SuggestInRepo = self.GtkBuilder.get_object("SuggestInRepo")

        self.SuggestName = self.GtkBuilder.get_object("SuggestName")
        self.SuggestMail = self.GtkBuilder.get_object("SuggestMail")

        self.SuggestInfoLabel = self.GtkBuilder.get_object("SuggestInfoLabel")
        self.SuggestSend = self.GtkBuilder.get_object("SuggestSend")

        self.SuggestStack = self.GtkBuilder.get_object("SuggestStack")

        self.SuggestScroll = self.GtkBuilder.get_object("SuggestScroll")
        self.PardusAppDetailScroll = self.GtkBuilder.get_object("PardusAppDetailScroll")

        self.PardusCurrentCategory = -1
        if self.locale == "tr":
            self.PardusCurrentCategoryString = "tümü"
            self.RepoCurrentCategory = "tümü"
        else:
            self.PardusCurrentCategoryString = "all"
            self.RepoCurrentCategory = "all"

        self.useDynamicListStore = False
        self.repoappname = ""
        self.repoappclicked = False

        self.PardusCategoryFilter = self.GtkBuilder.get_object("PardusCategoryFilter")
        self.PardusCategoryFilter.set_visible_func(self.PardusCategoryFilterFunction)
        self.PardusCategoryFilter.refilter()

        # self.RepoCategoryFilter = self.GtkBuilder.get_object("RepoCategoryFilter")
        # self.RepoCategoryFilter.set_visible_func(self.RepoCategoryFilterFunction)
        # self.RepoCategoryFilter.refilter()

        self.dImage1 = self.GtkBuilder.get_object("dImage1")
        self.dImage2 = self.GtkBuilder.get_object("dImage2")
        self.ImagePopover = self.GtkBuilder.get_object("ImagePopover")
        self.ImagePopoverStack = self.GtkBuilder.get_object("ImagePopoverStack")
        self.pop1Image = self.GtkBuilder.get_object("pop1Image")
        self.pop2Image = self.GtkBuilder.get_object("pop2Image")
        self.pixbuf1 = None
        self.pixbuf2 = None
        self.imgLabel = self.GtkBuilder.get_object("imgLabel")
        # self.getDisplay()

        self.mac = self.getMac()

        self.descSwBox = self.GtkBuilder.get_object("descSwBox")
        self.descSwBox.set_visible(False)
        self.descSw = self.GtkBuilder.get_object("descSw")

        self.MainWindow = self.GtkBuilder.get_object("MainWindow")
        self.MainWindow.set_application(application)

        self.mainstack.set_visible_child_name("splash")

        self.HeaderBarMenuButton.set_sensitive(False)
        self.menubackbutton.set_sensitive(False)
        self.topbutton1.set_sensitive(False)
        self.topbutton2.set_sensitive(False)
        self.topsearchbutton.set_sensitive(False)

        self.queue = []
        self.inprogress = False

        self.serverappicons = False
        self.servercaticons = False

        self.frommostapps = False
        self.fromrepoapps = False
        self.fromdetails = False

        self.mostappname = None
        self.detailsappname = None

        self.statusoftopsearch = self.topsearchbutton.get_active()

        self.errormessage = ""

        self.updateclicked = False

        self.desktop_file = ""

        self.rate_average = 0
        self.rate_individual = _("is None")
        self.rate_author = ""
        self.rate_comment = ""

        self.imgfullscreen = False

        self.imgfullscreen_count = 0

        # cssProvider = Gtk.CssProvider()
        # cssProvider.load_from_path(os.path.dirname(os.path.abspath(__file__)) + "/../css/style.css")
        # screen = Gdk.Screen.get_default()
        # styleContext = Gtk.StyleContext()
        # styleContext.add_provider_for_screen(screen, cssProvider,
        #                                      Gtk.STYLE_PROVIDER_PRIORITY_USER)
        # # With the others GTK_STYLE_PROVIDER_PRIORITY values get the same result.

        self.PardusCommentListBox = self.GtkBuilder.get_object("PardusCommentListBox")
        self.GnomeCommentListBox = self.GtkBuilder.get_object("GnomeCommentListBox")
        self.QueueListBox = self.GtkBuilder.get_object("QueueListBox")

        # Set version
        # If not getted from __version__ file then accept version in MainWindow.glade file
        try:
            version = open(os.path.dirname(os.path.abspath(__file__)) + "/__version__").readline()
            self.aboutdialog.set_version(version)
        except:
            pass

        self.MainWindow.show_all()

        p1 = threading.Thread(target=self.worker)
        p1.daemon = True
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

    def getLocale(self):
        try:
            locale = getlocale()[0].split("_")[0]
            if locale != "tr" and locale != "en":
                locale = "en"
        except Exception as e:
            print(str(e))
            locale = "en"
        return locale

    def getDisplay(self):
        # defwindow = Gdk.get_default_root_window()
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        geometry = monitor.get_geometry()
        self.s_width = geometry.width
        self.s_height = geometry.height

    def worker(self):
        self.usersettings()
        self.setAnimations()
        self.package()
        self.appimage()
        self.appdetail()
        self.apprequest()
        # self.setRepoCategories()
        self.server()
        self.getIcons()
        self.controlIcons()
        self.normalpage()
        GLib.idle_add(self.gnomeComments)
        GLib.idle_add(self.setPardusCategories)
        GLib.idle_add(self.setPardusApps)
        GLib.idle_add(self.setEditorApps)
        GLib.idle_add(self.setMostApps)
        GLib.idle_add(self.setRepoApps)
        GLib.idle_add(self.gnomeRatings)
        GLib.idle_add(self.controlArgs)

    def controlArgs(self):
        if "details" in self.Application.args.keys():
            app = self.Application.args["details"]
            if app.endswith(".pardusapp"):
                app = app.split("/")[-1].split(".pardusapp")[0]
            try:
                for apps in self.Server.applist:
                    if app == apps["name"] or app == apps["desktop"].split(".desktop")[0] or app == \
                            apps["gnomename"].split(".desktop")[0]:
                        app = apps["name"]  # if the name is coming from desktop then set it to app name
                        self.fromdetails = True
                        self.detailsappname = app
                        GLib.idle_add(self.on_PardusAppsIconView_selection_changed, app)
            except Exception as e:
                print(str(e))

    def normalpage(self):
        self.mainstack.set_visible_child_name("home")
        if self.Server.connection and self.Server.app_scode == 200 and self.Server.cat_scode == 200:
            self.homestack.set_visible_child_name("pardushome")
        else:
            self.homestack.set_visible_child_name("noserver")
            self.noserverlabel.set_markup(
                "<b>{}\n{} : {}\n{} : {}</b>".format(_("Could not connect to server."), _("Error Code (app)"),
                                                     self.Server.app_scode, _("Error Code (cat)"),
                                                     self.Server.cat_scode))
        self.splashspinner.stop()
        # self.splashbarstatus = False
        self.splashlabel.set_text("")

        # self.HeaderBarMenuButton.set_visible(True)
        # self.menubackbutton.set_visible(True)
        # self.topbutton1.set_visible(True)
        # self.topbutton2.set_visible(True)
        # self.topsearchbutton.set_visible(True)

        GLib.idle_add(self.HeaderBarMenuButton.set_sensitive, True)
        GLib.idle_add(self.topbutton1.set_sensitive, True)
        GLib.idle_add(self.topbutton2.set_sensitive, True)
        GLib.idle_add(self.topsearchbutton.set_sensitive, True)

        if not self.Server.connection:
            GLib.idle_add(self.menu_suggestapp.set_sensitive, False)

        print("page setted to normal")

    def package(self):
        # self.splashspinner.start()
        # self.splashbar.pulse()
        self.splashlabel.set_markup("<b>{}</b>".format(_("Updating Cache")))
        self.Package = Package()
        if self.Package.updatecache():
            self.Package.getApps()
        else:
            print("Error while updating Cache")

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

    def apprequest(self):
        self.AppRequest = AppRequest()
        self.AppRequest.Request = self.Request
        print("apprequest completed")

    def gnomeComments(self):
        self.GnomeComment = GnomeComment()
        self.GnomeComment.gComment = self.gComment
        print("gnome comments completed")

    def on_dEventBox1_button_press_event(self, widget, event):
        self.imgfullscreen_count = 0
        self.setPopImage(1)
        self.resizePopImage()
        self.ImagePopover.show_all()
        self.ImagePopover.popup()

    def on_dEventBox2_button_press_event(self, widget, event):
        self.imgfullscreen_count = 0
        self.setPopImage(2)
        self.resizePopImage()
        self.ImagePopover.show_all()
        self.ImagePopover.popup()

    def on_imgBackButton_clicked(self, button):
        self.setPopImage(1)

    def on_imgNextButton_clicked(self, button):
        self.setPopImage(2)

    def on_imgCloseButton_clicked(self, button):
        self.ImagePopover.popdown()

    def on_imgFullButton_clicked(self, button):
        self.imgfullscreen_count += 1
        if self.imgfullscreen_count % 2 == 1:
            self.imgfullscreen = True
            self.resizePopImage(True)
        else:
            self.imgfullscreen = False
            self.resizePopImage()

    def on_ImagePopover_key_press_event(self, widget, event):

        if event.keyval == Gdk.KEY_Left:
            self.setPopImage(1)
            return True
        elif event.keyval == Gdk.KEY_Right:
            self.setPopImage(2)
            return True
        elif event.keyval == Gdk.KEY_f or event.keyval == Gdk.KEY_F:
            self.imgfullscreen_count += 1
            if self.imgfullscreen_count % 2 == 1:
                self.imgfullscreen = True
                self.resizePopImage(True)
                return True
            else:
                self.imgfullscreen = False
                self.resizePopImage()
                return True

    def setPopImage(self, image):
        if image == 1:
            self.imgLabel.set_text("{} 1".format(_("Image")))
            self.ImagePopoverStack.set_visible_child_name("image1")
        elif image == 2:
            self.imgLabel.set_text("{} 2".format(_("Image")))
            self.ImagePopoverStack.set_visible_child_name("image2")

    def on_ImagePopover_closed(self, widget):
        self.imgfullscreen = False

    def setRepoCategories(self):
        # self.splashlabel.set_markup("<b>{}</b>".format(_("Setting Repo Categories")))
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
        # self.splashlabel.set_markup("<b>{}</b>".format(_("Setting Repo Apps")))
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
        column_toggle = Gtk.TreeViewColumn(_("Status"), renderer_toggle, active=3)
        column_toggle.set_resizable(True)
        column_toggle.set_sort_column_id(3)
        self.RepoAppsTreeView.append_column(column_toggle)

        renderer = Gtk.CellRendererText()
        column_name = Gtk.TreeViewColumn(_("Name"), renderer, text=0)
        column_name.set_resizable(True)
        column_name.set_sort_column_id(0)
        self.RepoAppsTreeView.append_column(column_name)

        renderer = Gtk.CellRendererText()
        column_cat = Gtk.TreeViewColumn(_("Section"), renderer, text=1)
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
        column_desc = Gtk.TreeViewColumn(_("Description"), renderer, text=5)
        column_desc.set_resizable(True)
        column_desc.set_sort_column_id(5)
        self.RepoAppsTreeView.append_column(column_desc)

        self.RepoAppsTreeView.show_all()

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
        # self.splashbar.pulse()
        print("Getting applications from server")
        self.splashlabel.set_markup("<b>{}</b>".format(_("Getting applications from server")))
        self.Server = Server()
        # self.serverappicons = self.Server.getAppIcons()
        # self.servercaticons = self.Server.getCategoryIcons()
        print("{} {}".format("server connection", self.Server.connection))

    def getIcons(self):
        if self.Server.connection:
            # self.splashbar.pulse()
            print("Getting icons from server")
            self.splashlabel.set_markup("<b>{}</b>".format(_("Getting icons from server")))
            self.serverappicons = self.Server.getAppIcons()
            self.servercaticons = self.Server.getCategoryIcons()
        else:
            print("icons cannot downloading because server connection is {}".format(self.Server.connection))

    def controlIcons(self):
        if self.Server.connection:
            print("Controlling icons")
            self.splashlabel.set_markup("<b>{}</b>".format(_("Controlling icons")))
            self.Server.controlIcons()
        else:
            print("icons cannot controlling because server connection is {}".format(self.Server.connection))
    def gnomeRatings(self):
        print("Getting ratings from gnome odrs")
        # self.splashlabel.set_markup("<b>{}</b>".format(_("Getting ratings from gnome odrs")))
        # self.GnomeServer = GnomeServer()
        # self.gnomeratings = self.GnomeServer.getGnomeRatings()
        # if self.gnomeratings is not False:
        #     print("gnomeratings successful")
        # else:
        #     print("gnomeratings none")

        self.GnomeRatingServer = GnomeRatingServer()
        self.GnomeRatingServer.gRatingServer = self.gRatingServer
        self.GnomeRatingServer.get()

    def gRatingServer(self, status, response):
        if status:
            print("gnomeratings successful")
            self.gnomeratings = response
            # GLib.idle_add(self.setGnomeRatings, self.gnomeratings[self.gnomename])
        else:
            self.gnomeratings = []
            print("gnomeratings not successful")

    def setPardusApps(self):
        if self.Server.connection:
            # self.splashlabel.set_markup("<b>{}</b>".format(_("Setting applications")))

            if self.UserSettings.config_usi:
                print("User want to use system icons [app]")
                for app in self.Server.applist:
                    appicon = self.getSystemAppIcon(app["name"])
                    appname = app['name']
                    prettyname = app["prettyname"][self.locale]
                    if prettyname == "" or prettyname is None:
                        prettyname = app["prettyname"]["en"]
                    category = ""
                    for i in app["category"]:
                        category += i[self.locale] + ","
                    category = category.rstrip(",")
                    # print(appname + " : " + category)
                    categorynumber = self.get_category_number(category)
                    GLib.idle_add(self.addToPardusApps, [appicon, appname, categorynumber, prettyname, category])
            else:
                print("User want to use server icons [app]")
                print("{} : {}".format("serverappicons", self.serverappicons))
                for app in self.Server.applist:
                    appicon = self.getServerAppIcon(app["name"])
                    appname = app['name']
                    prettyname = app['prettyname'][self.locale]
                    if prettyname == "" or prettyname is None:
                        prettyname = app["prettyname"]["en"]
                    category = ""
                    for i in app['category']:
                        category += i[self.locale] + ","
                    category = category.rstrip(",")
                    # print(appname + " : " + category)
                    categorynumber = self.get_category_number(category)
                    GLib.idle_add(self.addToPardusApps, [appicon, appname, categorynumber, prettyname, category])

    def addToPardusApps(self, list):
        self.PardusAppListStore.append(list)

    def setPardusCategories(self):
        if self.Server.connection:
            if self.locale == "tr":
                self.allcats = [{"name": "tümü", "icon": "all"}]
            else:
                self.allcats = [{"name": "all", "icon": "all"}]
            for cat in self.Server.catlist:
                self.allcats.append({"name": cat[self.locale], "icon": cat["en"]})
            self.categories = sorted(self.allcats, key=lambda x: x["name"])

            if self.UserSettings.config_usi:
                print("User want to use system icons [cat]")

                for cat in self.categories:
                    caticon = Gtk.Image.new()
                    caticon.set_from_pixbuf(self.getSystemCatIcon(cat["icon"]))
                    label = Gtk.Label.new()
                    label_text = str(cat["name"]).capitalize()
                    label.set_text(" " + label_text)
                    box1 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
                    box1.pack_start(caticon, False, True, 0)
                    box1.pack_start(label, False, True, 0)
                    box1.set_name("homecats")
                    GLib.idle_add(self.HomeCategoryFlowBox.insert, box1, GLib.PRIORITY_DEFAULT_IDLE)
            else:
                print("User want to use server icons [cat]")
                print("{} : {}".format("servercaticons", self.servercaticons))
                for cat in self.categories:
                    caticon = Gtk.Image.new()
                    caticon.set_from_pixbuf(self.getServerCatIcon(cat["icon"]))
                    label = Gtk.Label.new()
                    label_text = str(cat["name"]).capitalize()
                    label.set_text(" " + label_text)
                    box1 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
                    box1.pack_start(caticon, False, True, 0)
                    box1.pack_start(label, False, True, 0)
                    box1.set_name("homecats")
                    GLib.idle_add(self.HomeCategoryFlowBox.insert, box1, GLib.PRIORITY_DEFAULT_IDLE)

            GLib.idle_add(self.HomeCategoryFlowBox.show_all)

    def setEditorApps(self):
        if self.Server.connection:
            for ediapp in self.Server.ediapplist:
                if self.UserSettings.config_usi:
                    edipixbuf = self.getSystemAppIcon(ediapp['name'])
                else:
                    edipixbuf = self.getServerAppIcon(ediapp['name'])
                ediappname = ediapp["name"]
                ediprettyname = ediapp["prettyname"][self.locale]
                if ediprettyname == "" or ediprettyname is None:
                    ediprettyname = ediapp["prettyname"]["en"]
                edicategory = ""
                for i in ediapp['category']:
                    edicategory += i[self.locale] + ","
                edicategory = edicategory.rstrip(",")
                edicategorynumber = self.get_category_number(edicategory)
                GLib.idle_add(self.addToEditorApps, [edipixbuf, ediappname, edicategorynumber, ediprettyname])

    def addToEditorApps(self, list):
        self.EditorListStore.append(list)

    def setMostApps(self):
        if self.Server.connection:
            for mda in self.Server.mostdownapplist:
                icon = Gtk.Image.new()
                if self.UserSettings.config_usi:
                    icon.set_from_pixbuf(self.getSystemAppIcon(mda["name"], 64))
                else:
                    icon.set_from_pixbuf(self.getServerAppIcon(mda["name"], 64))

                label = Gtk.Label.new()
                label.set_text(str(self.getPrettyName(mda["name"])))
                label.set_line_wrap(True)
                label.set_max_width_chars(10)
                label.name = mda["name"]

                downicon = Gtk.Image.new_from_icon_name("document-save-symbolic", Gtk.IconSize.BUTTON)

                downlabel = Gtk.Label.new()
                downlabel.set_markup("<small>{}</small>".format(mda["download"]))

                rateicon = Gtk.Image.new_from_icon_name("star-new-symbolic", Gtk.IconSize.BUTTON)

                ratelabel = Gtk.Label.new()
                ratelabel.set_markup("<small>{:.1f}</small>".format(float(mda["rate"])))

                box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
                box1 = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
                box2 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
                box3 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)

                box2.pack_start(downicon, False, True, 0)
                box2.pack_start(downlabel, False, True, 0)

                box3.pack_start(rateicon, False, True, 0)
                box3.pack_start(ratelabel, False, True, 0)

                box1.set_homogeneous(True)
                box1.pack_start(box2, False, True, 0)
                box1.pack_start(box3, False, True, 0)

                box.pack_start(icon, False, True, 10)
                box.pack_start(label, False, True, 0)
                box.pack_end(box1, False, True, 10)

                frame = Gtk.Frame.new()
                frame.add(box)
                GLib.idle_add(self.MostDownFlowBox.insert, frame, GLib.PRIORITY_DEFAULT_IDLE)

            for mra in self.Server.mostrateapplist:
                icon = Gtk.Image.new()
                if self.UserSettings.config_usi:
                    icon.set_from_pixbuf(self.getSystemAppIcon(mra["name"], 64))
                else:
                    icon.set_from_pixbuf(self.getServerAppIcon(mra["name"], 64))

                label = Gtk.Label.new()
                label.set_text(str(self.getPrettyName(mra["name"])))
                label.set_line_wrap(True)
                label.set_max_width_chars(10)
                label.name = mra["name"]

                downicon = Gtk.Image.new_from_icon_name("document-save-symbolic", Gtk.IconSize.BUTTON)

                downlabel = Gtk.Label.new()
                downlabel.set_markup("<small>{}</small>".format(mra["download"]))

                rateicon = Gtk.Image.new_from_icon_name("star-new-symbolic", Gtk.IconSize.BUTTON)

                ratelabel = Gtk.Label.new()
                ratelabel.set_markup("<small>{:.1f}</small>".format(float(mra["rate"])))

                box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
                box1 = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
                box2 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
                box3 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)

                box2.pack_start(rateicon, False, True, 0)
                box2.pack_start(ratelabel, False, True, 0)

                box3.pack_start(downicon, False, True, 0)
                box3.pack_start(downlabel, False, True, 0)

                box1.set_homogeneous(True)
                box1.pack_start(box2, False, True, 0)
                box1.pack_start(box3, False, True, 0)

                box.pack_start(icon, False, True, 10)
                box.pack_start(label, False, True, 0)
                box.pack_end(box1, False, True, 10)

                frame = Gtk.Frame.new()
                frame.add(box)
                GLib.idle_add(self.MostRateFlowBox.insert, frame, GLib.PRIORITY_DEFAULT_IDLE)

            self.hometotaldc.set_markup("<small>{}</small>".format(self.Server.totalstatistics[0]["downcount"]))
            self.hometotalrc.set_markup("<small>{}</small>".format(self.Server.totalstatistics[0]["ratecount"]))

        GLib.idle_add(self.MostDownFlowBox.show_all)
        GLib.idle_add(self.MostRateFlowBox.show_all)

    def getPrettyName(self, name):
        prettyname = ""
        for i in self.Server.applist:
            if i["name"] == name:
                prettyname = i["prettyname"][self.locale]
                if prettyname == "" or prettyname is None:
                    prettyname = i["prettyname"]["en"]
        if len(prettyname.split(" ")) > 3:
            prettyname = " ".join(prettyname.split(" ")[:3]) + " ..."
        return prettyname

    def getSystemCatIcon(self, cat, size=48):
        try:
            caticon = Gtk.IconTheme.get_default().load_icon("applications-" + cat, size, Gtk.IconLookupFlags(16))
        except:
            print("{} {}".format(cat, "category icon not found in system icons"))
            try:
                if cat == "education":
                    caticon = Gtk.IconTheme.get_default().load_icon("applications-science", size,
                                                                    Gtk.IconLookupFlags(16))
                elif cat == "all":
                    caticon = Gtk.IconTheme.get_default().load_icon("applications-other", size, Gtk.IconLookupFlags(16))
                elif cat == "pardus":
                    caticon = Gtk.IconTheme.get_default().load_icon("emblem-pardus", size, Gtk.IconLookupFlags(16))
                else:
                    try:
                        caticon = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", size,
                                                                        Gtk.IconLookupFlags(16))
                    except:
                        caticon = Gtk.IconTheme.get_default().load_icon("image-missing", size, Gtk.IconLookupFlags(16))
            except:
                try:
                    caticon = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", size, Gtk.IconLookupFlags(16))
                except:
                    caticon = Gtk.IconTheme.get_default().load_icon("image-missing", size, Gtk.IconLookupFlags(16))
        return caticon

    def getServerCatIcon(self, cat, size=48):
        try:
            caticon = GdkPixbuf.Pixbuf.new_from_file_at_size(
                self.Server.cachedir + "categoryicons/" + cat + ".svg", size, size)
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

    # def on_timeout(self, user_data):
    #     if self.splashbarstatus:
    #         self.splashbar.pulse()
    #     else:
    #         self.splashbar.set_fraction(0)
    #     return True

    def get_category_number(self, thatcategory):
        listcat = list(thatcategory.split(","))
        lenlistcat = len(listcat)
        lencat = len(self.categories)
        for i in range(0, lencat):
            for j in range(0, lenlistcat):
                if self.categories[i]["name"] == listcat[j]:
                    return i

    def get_category_name(self, thatnumber):
        lencat = len(self.categories)
        for i in range(0, lencat):
            if thatnumber == i:
                return self.categories[i]["name"], self.categories[i]["icon"]

    def get_repo_category_number(self, thatcategory):
        repocatnumber = 404
        for i in self.Package.sections:
            if thatcategory == i["name"]:
                repocatnumber = i["number"]
        return repocatnumber

    def onDestroy(self, widget):
        self.MainWindow.destroy()

    def setAnimations(self):
        if self.UserSettings.config_anim:
            self.mainstack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
            self.mainstack.set_transition_duration(200)

            self.homestack.set_transition_type(Gtk.StackTransitionType.SLIDE_UP_DOWN)
            self.homestack.set_transition_duration(200)

            self.searchstack.set_transition_type(Gtk.StackTransitionType.SLIDE_UP)
            self.searchstack.set_transition_duration(200)

            self.rbotstack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.rbotstack.set_transition_duration(200)

            self.commentstack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
            self.commentstack.set_transition_duration(200)

        else:
            self.mainstack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.mainstack.set_transition_duration(0)

            self.homestack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.homestack.set_transition_duration(0)

            self.searchstack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.searchstack.set_transition_duration(0)

            self.commentstack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.commentstack.set_transition_duration(0)

    def on_menubackbutton_clicked(self, widget):
        print("menuback")
        if self.homestack.get_visible_child_name() == "pardusapps":
            self.homestack.set_visible_child_name("pardushome")
            self.HomeCategoryFlowBox.unselect_all()
            self.EditorAppsIconView.unselect_all()
            self.menubackbutton.set_sensitive(False)
        elif self.homestack.get_visible_child_name() == "pardusappsdetail":
            if self.fromeditorapps or self.frommostapps:
                self.homestack.set_visible_child_name("pardushome")
                self.HomeCategoryFlowBox.unselect_all()
                self.EditorAppsIconView.unselect_all()
                self.MostRateFlowBox.unselect_all()
                self.MostDownFlowBox.unselect_all()
                self.menubackbutton.set_sensitive(False)
            else:
                self.homestack.set_visible_child_name("pardusapps")
                self.PardusAppsIconView.unselect_all()

    def on_PardusAppsIconView_selection_changed(self, iconview):
        self.fromrepoapps = False
        mode = 0
        try:
            # detection of IconViews (PardusAppsIconView or EditorAppsIconView)
            iconview.get_model().get_name()
            self.fromeditorapps = True
        except:
            self.fromeditorapps = False
            # PardusAppsIconView TreeModelFilter has no attribute 'get_name'
            mode = 1

        self.menubackbutton.set_sensitive(True)
        self.descSw.set_state(False)
        self.setWpcStar(0)
        self.wpcstar = 0
        self.wpcformcontrolLabel.set_text("")
        self.wpcresultLabel.set_text("")
        self.wpcAuthor.set_text(self.Server.username)
        self.wpcComment.set_text("")
        self.wpcSendButton.set_sensitive(True)

        self.PardusAppDetailScroll.set_vadjustment(Gtk.Adjustment())

        try:
            selected_items = iconview.get_selected_items()
            lensel = len(selected_items)
            self.frommostapps = False
        except:
            self.frommostapps = True
            lensel = 1

        if lensel == 1:
            if not self.frommostapps:
                if mode == 1:
                    treeiter = self.PardusCategoryFilter.get_iter(selected_items[0])
                    self.appname = self.PardusCategoryFilter.get(treeiter, 1)[0]
                    # prettyname = self.PardusCategoryFilter.get(treeiter, 3)[0]
                else:
                    treeiter = self.EditorListStore.get_iter(selected_items[0])
                    self.appname = self.EditorListStore.get(treeiter, 1)[0]
                    # prettyname = self.EditorListStore.get(treeiter, 3)[0]
                print(selected_items[0])
                print(self.appname)
            else:
                self.appname = iconview

            self.homestack.set_visible_child_name("pardusappsdetail")

            if self.UserSettings.config_usi:
                pixbuf = self.getSystemAppIcon(self.appname, 128)
            else:
                pixbuf = self.getServerAppIcon(self.appname, 128)

            self.dIcon.set_from_pixbuf(pixbuf)

            for i in self.Server.applist:
                if i["name"] == self.appname:
                    self.description = i["description"][self.locale]
                    self.section = i["section"][0][self.locale]
                    if self.section == "" or self.section is None:
                        self.section = i["section"][0]["en"]
                    self.maintainer_name = i["maintainer"][0]["name"]
                    self.maintainer_mail = i["maintainer"][0]["mail"]
                    self.maintainer_web = i["maintainer"][0]["website"]
                    self.category = i["category"][0][self.locale].capitalize()
                    self.license = i["license"]
                    self.codenames = ", ".join(c["name"] for c in i["codename"])
                    self.gnomename = i["gnomename"]
                    self.screenshots = i["screenshots"]
                    self.desktop_file = i["desktop"]
                    self.component = i["component"]["name"]
                    prettyname = i["prettyname"][self.locale]
                    if prettyname is None or prettyname == "":
                        prettyname = i["prettyname"]["en"]

                    command = i["command"]
                    if command and command[self.locale].strip() != "":
                        self.command = command[self.locale]
                    else:
                        self.command = i["name"]

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
            if len(prettyname.split(" ")) > 3:
                prettyname = " ".join(prettyname.split(" ")[:3]) + "\n" + " ".join(prettyname.split(" ")[3:])
            self.dName.set_markup("<span font='21'><b>" + prettyname + "</b></span>")
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
                origins = self.Package.origins(self.appname)

                component = ""
                origin = ""
                if origins:
                    component = origins.component
                    origin = origins.origin

                if component == "non-free" or self.component == "non-free":
                    self.dDisclaimerButton.set_visible(True)
                    type = _("Non-Free")
                else:
                    self.dDisclaimerButton.set_visible(False)
                    type = _("Open Source")

                self.dVersion.set_markup(version)
                self.dSize.set_markup(size)
                self.dComponent.set_markup("{} {}".format(origin, component))
                self.dType.set_markup(type)

                if isinstalled:
                    if self.dActionButton.get_style_context().has_class("suggested-action"):
                        self.dActionButton.get_style_context().remove_class("suggested-action")
                    self.dActionButton.get_style_context().add_class("destructive-action")
                    self.dActionButton.set_label(_(" Uninstall"))
                    self.dActionButton.set_image(Gtk.Image.new_from_stock("gtk-delete", Gtk.IconSize.BUTTON))

                    if self.desktop_file != "" and self.desktop_file is not None:
                        self.dOpenButton.set_visible(True)
                    else:
                        self.dOpenButton.set_visible(False)

                else:
                    if self.dActionButton.get_style_context().has_class("destructive-action"):
                        self.dActionButton.get_style_context().remove_class("destructive-action")
                    self.dActionButton.get_style_context().add_class("suggested-action")
                    self.dActionButton.set_label(_(" Install"))
                    self.dActionButton.set_image(Gtk.Image.new_from_stock("gtk-save", Gtk.IconSize.BUTTON))

                    self.dOpenButton.set_visible(False)

                    self.wpcformcontrolLabel.set_markup(
                        "<span color='red'>{}</span>".format(_("You need to install the application")))

                if len(self.queue) > 0:
                    for qa in self.queue:
                        if self.appname == qa["name"]:
                            if isinstalled:
                                self.dActionButton.set_label(_(" Removing"))
                            else:
                                self.dActionButton.set_label(_(" Installing"))
                            self.dActionButton.set_sensitive(False)

            else:
                self.dActionButton.set_sensitive(False)
                if self.dActionButton.get_style_context().has_class("destructive-action"):
                    self.dActionButton.get_style_context().remove_class("destructive-action")
                if self.dActionButton.get_style_context().has_class("suggested-action"):
                    self.dActionButton.get_style_context().remove_class("suggested-action")

                self.dActionButton.set_label(_(" Not Found"))
                self.dActionButton.set_image(Gtk.Image.new_from_stock("gtk-dialog-warning", Gtk.IconSize.BUTTON))

                self.dVersion.set_markup(_("None"))
                self.dSize.set_markup(_("None"))
                self.dComponent.set_markup(_("None"))
                self.dType.set_markup(_("None"))

                self.dOpenButton.set_visible(False)
                self.dDisclaimerButton.set_visible(False)

                self.wpcformcontrolLabel.set_markup(
                    "<span color='red'>{}</span>".format(_("You need to install the application")))

            self.pixbuf1 = None
            self.pixbuf2 = None

            if self.screenshots[0] + "#1" in self.AppImage.imgcache:
                # print("image1 in cache")
                self.pixbuf1 = self.AppImage.imgcache[self.screenshots[0] + "#1"]
                self.resizeAppImage()
            else:
                self.pixbuf1 = None
                # print("image1 not in cache")
                self.AppImage.fetch(self.Server.serverurl, self.screenshots[0], "#1")

            if self.screenshots[1] + "#2" in self.AppImage.imgcache:
                # print("image2 in cache")
                self.pixbuf2 = self.AppImage.imgcache[self.screenshots[1] + "#2"]
                self.resizeAppImage()
            else:
                # print("image2 not in cache")
                self.pixbuf2 = None
                self.AppImage.fetch(self.Server.serverurl, self.screenshots[1], "#2")

            dic = {"mac": self.mac, "app": self.appname}
            self.AppDetail.get("POST", self.Server.serverurl + "/api/v2/details", dic)

            gdic = {"user_hash": "0000000000000000000000000000000000000000", "app_id": self.gnomename, "locale": "tr",
                    "distro": "Pardus", "version": "unknown", "limit": -1}
            self.GnomeComment.get("POST", self.Server.gnomecommentserver, gdic)

    def setPardusCommentStar(self, rate):
        self.cs1 = Gtk.Image.new()
        self.cs2 = Gtk.Image.new()
        self.cs3 = Gtk.Image.new()
        self.cs4 = Gtk.Image.new()
        self.cs5 = Gtk.Image.new()
        if rate == 0:
            self.cs1.set_from_pixbuf(self.cstaroff)
            self.cs2.set_from_pixbuf(self.cstaroff)
            self.cs3.set_from_pixbuf(self.cstaroff)
            self.cs4.set_from_pixbuf(self.cstaroff)
            self.cs5.set_from_pixbuf(self.cstaroff)
        elif rate == 1:
            self.cs1.set_from_pixbuf(self.cstaron)
            self.cs2.set_from_pixbuf(self.cstaroff)
            self.cs3.set_from_pixbuf(self.cstaroff)
            self.cs4.set_from_pixbuf(self.cstaroff)
            self.cs5.set_from_pixbuf(self.cstaroff)
        elif rate == 2:
            self.cs1.set_from_pixbuf(self.cstaron)
            self.cs2.set_from_pixbuf(self.cstaron)
            self.cs3.set_from_pixbuf(self.cstaroff)
            self.cs4.set_from_pixbuf(self.cstaroff)
            self.cs5.set_from_pixbuf(self.cstaroff)
        elif rate == 3:
            self.cs1.set_from_pixbuf(self.cstaron)
            self.cs2.set_from_pixbuf(self.cstaron)
            self.cs3.set_from_pixbuf(self.cstaron)
            self.cs4.set_from_pixbuf(self.cstaroff)
            self.cs5.set_from_pixbuf(self.cstaroff)
        elif rate == 4:
            self.cs1.set_from_pixbuf(self.cstaron)
            self.cs2.set_from_pixbuf(self.cstaron)
            self.cs3.set_from_pixbuf(self.cstaron)
            self.cs4.set_from_pixbuf(self.cstaron)
            self.cs5.set_from_pixbuf(self.cstaroff)
        elif rate == 5:
            self.cs1.set_from_pixbuf(self.cstaron)
            self.cs2.set_from_pixbuf(self.cstaron)
            self.cs3.set_from_pixbuf(self.cstaron)
            self.cs4.set_from_pixbuf(self.cstaron)
            self.cs5.set_from_pixbuf(self.cstaron)
        else:
            print("comment star error")

    def setGnomeCommentStar(self, rate):
        self.gcs1 = Gtk.Image.new()
        self.gcs2 = Gtk.Image.new()
        self.gcs3 = Gtk.Image.new()
        self.gcs4 = Gtk.Image.new()
        self.gcs5 = Gtk.Image.new()
        if rate == 0:
            self.gcs1.set_from_pixbuf(self.gcstaroff)
            self.gcs2.set_from_pixbuf(self.gcstaroff)
            self.gcs3.set_from_pixbuf(self.gcstaroff)
            self.gcs4.set_from_pixbuf(self.gcstaroff)
            self.gcs5.set_from_pixbuf(self.gcstaroff)
        elif rate == 1:
            self.gcs1.set_from_pixbuf(self.gcstaron)
            self.gcs2.set_from_pixbuf(self.gcstaroff)
            self.gcs3.set_from_pixbuf(self.gcstaroff)
            self.gcs4.set_from_pixbuf(self.gcstaroff)
            self.gcs5.set_from_pixbuf(self.gcstaroff)
        elif rate == 2:
            self.gcs1.set_from_pixbuf(self.gcstaron)
            self.gcs2.set_from_pixbuf(self.gcstaron)
            self.gcs3.set_from_pixbuf(self.gcstaroff)
            self.gcs4.set_from_pixbuf(self.gcstaroff)
            self.gcs5.set_from_pixbuf(self.gcstaroff)
        elif rate == 3:
            self.gcs1.set_from_pixbuf(self.gcstaron)
            self.gcs2.set_from_pixbuf(self.gcstaron)
            self.gcs3.set_from_pixbuf(self.gcstaron)
            self.gcs4.set_from_pixbuf(self.gcstaroff)
            self.gcs5.set_from_pixbuf(self.gcstaroff)
        elif rate == 4:
            self.gcs1.set_from_pixbuf(self.gcstaron)
            self.gcs2.set_from_pixbuf(self.gcstaron)
            self.gcs3.set_from_pixbuf(self.gcstaron)
            self.gcs4.set_from_pixbuf(self.gcstaron)
            self.gcs5.set_from_pixbuf(self.gcstaroff)
        elif rate == 5:
            self.gcs1.set_from_pixbuf(self.gcstaron)
            self.gcs2.set_from_pixbuf(self.gcstaron)
            self.gcs3.set_from_pixbuf(self.gcstaron)
            self.gcs4.set_from_pixbuf(self.gcstaron)
            self.gcs5.set_from_pixbuf(self.gcstaron)
        else:
            print("comment star error")

    def setPardusComments(self, comments):

        for row in self.PardusCommentListBox:
            self.PardusCommentListBox.remove(row)

        if comments:
            for comment in comments:
                self.setPardusCommentStar(comment["value"])
                label1 = Gtk.Label.new()
                label1.set_markup("<b>" + comment["author"] + "</b>")
                labeldate = Gtk.Label.new()
                labeldate.set_markup(comment["date"])
                box1 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
                box1.pack_start(self.cs1, False, True, 0)
                box1.pack_start(self.cs2, False, True, 0)
                box1.pack_start(self.cs3, False, True, 0)
                box1.pack_start(self.cs4, False, True, 0)
                box1.pack_start(self.cs5, False, True, 0)
                box1.pack_start(label1, False, True, 10)
                box1.pack_end(labeldate, False, True, 0)
                label2 = Gtk.Label.new()
                label2.set_text(comment["comment"])
                label2.set_selectable(True)
                label2.set_line_wrap(True)
                box2 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
                box2.pack_start(label2, False, True, 0)
                hsep = Gtk.HSeparator.new()
                self.box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 3)
                self.box.pack_start(box1, False, True, 5)
                self.box.pack_start(box2, False, True, 5)
                self.box.pack_start(hsep, False, True, 0)

                self.PardusCommentListBox.add(self.box)

        self.PardusCommentListBox.show_all()

    def on_descSw_state_set(self, switch, state):
        print("switched {}".format(state))
        if state:
            self.dDescriptionLabel.set_text(self.description)
        else:
            self.dDescriptionLabel.set_text(self.s_description)

    def Request(self, status, response):
        if status:
            # print(response)
            if response["response-type"] == 10:
                self.wpcSendButton.set_sensitive(True)
                if response["rating"]["status"]:
                    self.rate_average = response["rating"]["rate"]["average"]
                    self.rate_individual = response["rating"]["rate"]["individual"]
                    self.rate_author = response["rating"]["rate"]["author"]
                    self.rate_comment = response["rating"]["rate"]["comment"]

                    self.setAppStar(self.rate_average)
                    self.dtAverageRating.set_markup("<big>{:.1f}</big>".format(float(self.rate_average)))
                    self.dtUserRating.set_markup("{} {}".format(_("Your Rate"), self.rate_individual))
                    self.dtTotalRating.set_markup("( {} )".format(response["rating"]["rate"]["count"]))

                    if response["rating"]["rate"]["recommentable"]:
                        self.editCommentButton.set_visible(True)
                    else:
                        self.editCommentButton.set_visible(False)

                    if response["rating"]["justrate"]:
                        self.commentstack.set_visible_child_name("alreadysent")
                        self.wpcgetnameLabel.set_text(str(response["rating"]["rate"]["author"]))
                        self.wpcgetcommentLabel.set_text(str(response["rating"]["rate"]["comment"]))
                    else:
                        self.commentstack.set_visible_child_name("sendresult")
                        self.wpcresultLabel.set_text(
                            _("Your comment has been sent successfully. It will be published after approval."))
                else:
                    if response["rating"]["justrate"]:
                        print("justrate error")
                    else:
                        if response["rating"]["flood"]:
                            self.wpcformcontrolLabel.set_text(_("Please try again soon"))
                        else:
                            self.wpcformcontrolLabel.set_text(_("Error"))

            if response["response-type"] == 12:
                self.SuggestSend.set_sensitive(True)
                if response["suggestapp"]["status"]:
                    self.SuggestInfoLabel.set_text("")
                    self.SuggestStack.set_visible_child_name("success")
                    self.SuggestScroll.set_vadjustment(Gtk.Adjustment())
                    self.resetSuggestAppForm()
                else:
                    if response["suggestapp"]["flood"]:
                        self.SuggestInfoLabel.set_text(_("Please try again soon"))
                    else:
                        self.SuggestInfoLabel.set_text(_("Error"))
        else:
            self.wpcresultLabel.set_text(_("Error"))

    def Detail(self, status, response):
        if status:
            # print(response)
            self.dtDownload.set_markup(
                "{} {}".format(response["details"]["download"]["count"], _("Download")))

            self.dtTotalRating.set_markup(
                "( {} )".format(response["details"]["rate"]["count"]))

            self.dtAverageRating.set_markup(
                "<big>{:.1f}</big>".format(float(response["details"]["rate"]["average"])))

            if response["details"]["rate"]["individual"] == 0:
                self.rate_individual = _("is None")
                self.dtUserRating.set_markup("{} {}".format(_("Your Rate"), _("is None")))
                self.commentstack.set_visible_child_name("sendcomment")
                self.wpcgetnameLabel.set_text("")
                self.wpcgetcommentLabel.set_text("")
            else:
                self.rate_individual = response["details"]["individual"]["rate"]
                self.rate_author = response["details"]["individual"]["author"]
                self.rate_comment = response["details"]["individual"]["comment"]

                self.dtUserRating.set_markup("{} {}".format(_("Your Rate"), response["details"]["rate"]["individual"]))
                self.commentstack.set_visible_child_name("alreadysent")
                self.wpcgetnameLabel.set_text(str(response["details"]["individual"]["author"]))
                self.wpcgetcommentLabel.set_text(str(response["details"]["individual"]["comment"]))

                if response["details"]["individual"]["recommentable"]:
                    self.editCommentButton.set_visible(True)
                else:
                    self.editCommentButton.set_visible(False)

            self.rate_average = response["details"]["rate"]["average"]
            self.setAppStar(response["details"]["rate"]["average"])

            self.setPardusRatings(response["details"]["rate"]["count"], response["details"]["rate"]["average"],
                                  response["details"]["rate"]["rates"]["1"], response["details"]["rate"]["rates"]["2"],
                                  response["details"]["rate"]["rates"]["3"], response["details"]["rate"]["rates"]["4"],
                                  response["details"]["rate"]["rates"]["5"])

            self.setPardusComments(response["details"]["comment"])

    def gComment(self, status, response):
        if status:
            self.setGnomeComments(response)
        else:
            self.setGnomeComments(None)

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
            # print(gr)

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

    def setGnomeComments(self, comments):

        for row in self.GnomeCommentListBox:
            self.GnomeCommentListBox.remove(row)

        if comments:
            for comment in comments:
                if "rating" and "user_display" and "date_created" and "summary" and "description" in comment:
                    self.setGnomeCommentStar(comment["rating"] / 20)
                    label1 = Gtk.Label.new()
                    label1.set_markup("<b>" + str(comment["user_display"]) + "</b>")
                    labeldate = Gtk.Label.new()
                    labeldate.set_text(str(datetime.fromtimestamp(comment["date_created"])))
                    box1 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
                    box1.pack_start(self.gcs1, False, True, 0)
                    box1.pack_start(self.gcs2, False, True, 0)
                    box1.pack_start(self.gcs3, False, True, 0)
                    box1.pack_start(self.gcs4, False, True, 0)
                    box1.pack_start(self.gcs5, False, True, 0)
                    box1.pack_start(label1, False, True, 10)
                    box1.pack_end(labeldate, False, True, 0)
                    label2 = Gtk.Label.new()
                    label2.set_text(str(comment["summary"]) + "\n" + str(comment["description"]))
                    label2.set_selectable(True)
                    label2.set_line_wrap(True)
                    box2 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
                    box2.pack_start(label2, False, True, 0)
                    hsep = Gtk.HSeparator.new()
                    box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 3)
                    box.pack_start(box1, False, True, 5)
                    box.pack_start(box2, False, True, 5)
                    box.pack_start(hsep, False, True, 0)

                    self.GnomeCommentListBox.add(box)

        self.GnomeCommentListBox.show_all()

    def eventStarSet(self, widget):
        if widget == "star1":
            self.dtStar1.set_from_pixbuf(self.staronhover)
            self.dtStar2.set_from_pixbuf(self.staroffhover)
            self.dtStar3.set_from_pixbuf(self.staroffhover)
            self.dtStar4.set_from_pixbuf(self.staroffhover)
            self.dtStar5.set_from_pixbuf(self.staroffhover)
            self.dtUserRating.set_markup("{} {}".format(_("Your Rate"), 1))
        elif widget == "star2":
            self.dtStar1.set_from_pixbuf(self.staronhover)
            self.dtStar2.set_from_pixbuf(self.staronhover)
            self.dtStar3.set_from_pixbuf(self.staroffhover)
            self.dtStar4.set_from_pixbuf(self.staroffhover)
            self.dtStar5.set_from_pixbuf(self.staroffhover)
            self.dtUserRating.set_markup("{} {}".format(_("Your Rate"), 2))
        elif widget == "star3":
            self.dtStar1.set_from_pixbuf(self.staronhover)
            self.dtStar2.set_from_pixbuf(self.staronhover)
            self.dtStar3.set_from_pixbuf(self.staronhover)
            self.dtStar4.set_from_pixbuf(self.staroffhover)
            self.dtStar5.set_from_pixbuf(self.staroffhover)
            self.dtUserRating.set_markup("{} {}".format(_("Your Rate"), 3))
        elif widget == "star4":
            self.dtStar1.set_from_pixbuf(self.staronhover)
            self.dtStar2.set_from_pixbuf(self.staronhover)
            self.dtStar3.set_from_pixbuf(self.staronhover)
            self.dtStar4.set_from_pixbuf(self.staronhover)
            self.dtStar5.set_from_pixbuf(self.staroffhover)
            self.dtUserRating.set_markup("{} {}".format(_("Your Rate"), 4))
        elif widget == "star5":
            self.dtStar1.set_from_pixbuf(self.staronhover)
            self.dtStar2.set_from_pixbuf(self.staronhover)
            self.dtStar3.set_from_pixbuf(self.staronhover)
            self.dtStar4.set_from_pixbuf(self.staronhover)
            self.dtStar5.set_from_pixbuf(self.staronhover)
            self.dtUserRating.set_markup("{} {}".format(_("Your Rate"), 5))

    def on_starEvent_enter_notify_event(self, widget, event):
        self.eventStarSet(widget.get_name())

    def on_starEvent_leave_notify_event(self, widget, event):
        self.setAppStar(self.rate_average)
        self.dtUserRating.set_markup("{} {}".format(_("Your Rate"), self.rate_individual))

    def on_starEvent_button_press_event(self, widget, event):
        installed = self.Package.isinstalled(self.appname)
        if installed is None:
            installed = False

        if installed:
            dic = {"app": self.appname, "mac": self.mac, "value": widget.get_name()[-1], "author": self.Server.username,
                   "installed": installed, "comment": "", "justrate": True}
            self.AppRequest.send("POST", self.Server.serverurl + self.Server.serversendrate, dic)
        else:
            self.dtUserRating.set_markup("<span color='red'>{}</span>".format(_("You need to install the application")))

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
            # print("image not in cache")
            self.dImage1.set_from_pixbuf(self.missing_pixbuf)
            self.dImage2.set_from_pixbuf(self.missing_pixbuf)

            self.pop1Image.set_from_pixbuf(self.missing_pixbuf)
            self.pop2Image.set_from_pixbuf(self.missing_pixbuf)

    def on_PardusAppImageBox_size_allocate(self, widget, allocated):

        self.resizeAppImage()

    def resizeAppImage(self):
        size = self.MainWindow.get_size()
        w = size.width - size.width / 1.5  # this is for detail Image
        h = size.height - size.height / 1.5  # this is for detail Image

        if not self.imgfullscreen:
            pw = size.width - size.width / 4  # this is for popup Image
            ph = size.height - size.height / 4  # this is for popup Image
        else:
            pw = size.width - 125  # this is for popup Image
            ph = size.height - 75  # this is for popup Image

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

    def resizePopImage(self, fullscreen=False):

        size = self.MainWindow.get_size()
        if not fullscreen:
            pw = size.width - size.width / 4  # this is for popup Image
            ph = size.height - size.height / 4  # this is for popup Image
        else:
            pw = size.width - 125  # this is for popup Image
            ph = size.height - 75  # this is for popup Image

        if self.pixbuf1:
            poppixbuf = self.pixbuf1.scale_simple(pw, ph, GdkPixbuf.InterpType.BILINEAR)
            self.pop1Image.set_from_pixbuf(poppixbuf)
        if self.pixbuf2:
            poppixbuf = self.pixbuf2.scale_simple(pw, ph, GdkPixbuf.InterpType.BILINEAR)
            self.pop2Image.set_from_pixbuf(poppixbuf)

    def on_wpcStarE1_button_press_event(self, widget, event):
        self.setWpcStar(1)

    def on_wpcStarE2_button_press_event(self, widget, event):
        self.setWpcStar(2)

    def on_wpcStarE3_button_press_event(self, widget, event):
        self.setWpcStar(3)

    def on_wpcStarE4_button_press_event(self, widget, event):
        self.setWpcStar(4)

    def on_wpcStarE5_button_press_event(self, widget, event):
        self.setWpcStar(5)

    def on_editCommentButton_clicked(self, button):

        self.setWpcStar(self.rate_individual)
        self.wpcAuthor.set_text(self.rate_author)
        self.wpcComment.set_text(self.rate_comment)
        self.commentstack.set_visible_child_name("sendcomment")

    def on_wpcSendButton_clicked(self, button):
        print("on_wpcSendButton_clicked")

        author = self.wpcAuthor.get_text().strip()
        comment = self.wpcComment.get_text().strip()
        value = self.wpcstar
        status = True
        if value == 0 or comment == "" or author == "":
            self.wpcformcontrolLabel.set_text(_("Cannot be null"))
        else:
            installed = self.Package.isinstalled(self.appname)
            if installed is None:
                installed = False
            if installed:
                dic = {"mac": self.mac, "author": author, "comment": comment, "value": value, "app": self.appname,
                       "installed": installed, "justrate": False}
                try:
                    self.AppRequest.send("POST", self.Server.serverurl + self.Server.serversendrate, dic)
                except Exception as e:
                    status = False
                    self.commentstack.set_visible_child_name("sendresult")
                    self.wpcresultLabel.set_text(str(e))
                if status:
                    self.wpcSendButton.set_sensitive(False)
                else:
                    self.wpcresultLabel.set_text(_("Error"))
            else:
                self.wpcformcontrolLabel.set_markup(
                    "<span color='red'>{}</span>".format(_("You need to install the application")))

    def setWpcStar(self, rate):

        if rate == 0:
            self.wpcStar1.set_from_pixbuf(self.wpcstaroff)
            self.wpcStar2.set_from_pixbuf(self.wpcstaroff)
            self.wpcStar3.set_from_pixbuf(self.wpcstaroff)
            self.wpcStar4.set_from_pixbuf(self.wpcstaroff)
            self.wpcStar5.set_from_pixbuf(self.wpcstaroff)
            self.wpcStarLabel.set_markup(_("Choose star rating level"))
        elif rate == 1:
            self.wpcStar1.set_from_pixbuf(self.wpcstaron)
            self.wpcStar2.set_from_pixbuf(self.wpcstaroff)
            self.wpcStar3.set_from_pixbuf(self.wpcstaroff)
            self.wpcStar4.set_from_pixbuf(self.wpcstaroff)
            self.wpcStar5.set_from_pixbuf(self.wpcstaroff)
            self.wpcStarLabel.set_markup("<b>1</b>")
            self.wpcstar = 1
        elif rate == 2:
            self.wpcStar1.set_from_pixbuf(self.wpcstaron)
            self.wpcStar2.set_from_pixbuf(self.wpcstaron)
            self.wpcStar3.set_from_pixbuf(self.wpcstaroff)
            self.wpcStar4.set_from_pixbuf(self.wpcstaroff)
            self.wpcStar5.set_from_pixbuf(self.wpcstaroff)
            self.wpcStarLabel.set_markup("<b>2</b>")
            self.wpcstar = 2
        elif rate == 3:
            self.wpcStar1.set_from_pixbuf(self.wpcstaron)
            self.wpcStar2.set_from_pixbuf(self.wpcstaron)
            self.wpcStar3.set_from_pixbuf(self.wpcstaron)
            self.wpcStar4.set_from_pixbuf(self.wpcstaroff)
            self.wpcStar5.set_from_pixbuf(self.wpcstaroff)
            self.wpcStarLabel.set_markup("<b>3</b>")
            self.wpcstar = 3
        elif rate == 4:
            self.wpcStar1.set_from_pixbuf(self.wpcstaron)
            self.wpcStar2.set_from_pixbuf(self.wpcstaron)
            self.wpcStar3.set_from_pixbuf(self.wpcstaron)
            self.wpcStar4.set_from_pixbuf(self.wpcstaron)
            self.wpcStar5.set_from_pixbuf(self.wpcstaroff)
            self.wpcStarLabel.set_markup("<b>4</b>")
            self.wpcstar = 4

        elif rate == 5:
            self.wpcStar1.set_from_pixbuf(self.wpcstaron)
            self.wpcStar2.set_from_pixbuf(self.wpcstaron)
            self.wpcStar3.set_from_pixbuf(self.wpcstaron)
            self.wpcStar4.set_from_pixbuf(self.wpcstaron)
            self.wpcStar5.set_from_pixbuf(self.wpcstaron)
            self.wpcStarLabel.set_markup("<b>5</b>")
            self.wpcstar = 5
        else:
            print("wpc star error")

    def PardusCategoryFilterFunction(self, model, iteration, data):
        search_entry_text = self.pardussearchbar.get_text()
        categorynumber = int(model[iteration][2])
        category = model[iteration][4]
        appname = model[iteration][1]
        showinstalled = self.pardusicb.get_active()
        pn_en = ""
        pn_tr = ""
        desc_en = ""
        desc_tr = ""

        if self.isPardusSearching:
            for i in self.Server.applist:
                if i["name"] == appname:
                    pn_en = i["prettyname"]["en"]
                    pn_tr = i["prettyname"]["tr"]
                    desc_en = i["description"]["en"]
                    desc_tr = i["description"]["tr"]
            self.HomeCategoryFlowBox.unselect_all()
            if search_entry_text.lower() in appname.lower() or search_entry_text.lower() in pn_en.lower() \
                    or search_entry_text.lower() in pn_tr.lower() or search_entry_text.lower() in desc_en \
                    or search_entry_text.lower() in desc_tr:
                if self.pardusicb.get_active():
                    if self.Package.isinstalled(appname):
                        return True
                else:
                    return True
        else:
            if self.PardusCurrentCategoryString == "all" or self.PardusCurrentCategoryString == "tümü":
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

    def on_sortPardusAppsCombo_changed(self, combo_box):
        if combo_box.get_active() == 0:  # sort by name
            self.Server.applist = sorted(self.Server.applist, key=lambda x: x["name"])
            self.PardusAppListStore.clear()
            self.setPardusApps()
        elif combo_box.get_active() == 1:  # sort by download
            self.Server.applist = sorted(self.Server.applist, key=lambda x: x["download"], reverse=True)
            self.PardusAppListStore.clear()
            self.setPardusApps()

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

    def on_MostFlowBox_child_activated(self, flow_box, child):

        self.mostappname = child.get_children()[0].get_children()[0].get_children()[1].name

        self.on_PardusAppsIconView_selection_changed(self.mostappname)

        self.MostDownFlowBox.unselect_all()
        self.MostRateFlowBox.unselect_all()

    def on_HomeCategoryFlowBox_child_activated(self, flow_box, child):
        self.isPardusSearching = False
        self.mainstack.set_visible_child_name("home")
        self.homestack.set_visible_child_name("pardusapps")
        self.menubackbutton.set_sensitive(True)
        self.PardusCurrentCategory = child.get_index()

        self.PardusCurrentCategoryString, self.PardusCurrentCategoryIcon = self.get_category_name(
            self.PardusCurrentCategory)
        print("home category selected " + str(self.PardusCurrentCategory) + " " + self.PardusCurrentCategoryString)

        if self.UserSettings.config_usi:
            pixbuf = self.getSystemCatIcon(self.PardusCurrentCategoryIcon, 32)
        else:
            pixbuf = self.getServerCatIcon(self.PardusCurrentCategoryIcon, 32)

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
        # print(row.get_child().get_text().lower().strip())

        if self.useDynamicListStore:

            if self.RepoCurrentCategory != "all" or self.RepoCurrentCategory != "tümü":

                self.RepoAppsTreeView.set_model(self.storedict[self.RepoCurrentCategory])
                self.RepoAppsTreeView.show_all()

            else:
                self.RepoAppsTreeView.set_model(self.RepoAppListStore)
                self.RepoAppsTreeView.show_all()

        else:

            if self.RepoCurrentCategory != "all" or self.RepoCurrentCategory != "tümü":

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

    def on_QueueListBox_row_activated(self, list_box, row):

        i = row.get_index()
        if i == 0:
            print("you can not remove because in progress")
        if i == 1:
            print("deleting 1")
            print("row is " + str(i))
            self.queue.pop(1)
            self.QueueListBox.remove(row)

    def on_clearqueuebutton_clicked(self, button):
        if len(self.queue) > 1:
            self.queue.pop(1)
            self.QueueListBox.remove(self.QueueListBox.get_row_at_index(1))

    def on_dDisclaimerButton_clicked(self, button):
        self.DisclaimerPopover.popup()

    def on_dOpenButton_clicked(self, button):

        subprocess.Popen(["gtk-launch", self.desktop_file])

    def on_dActionButton_clicked(self, button):

        self.dActionButton.set_sensitive(False)

        self.queue.append({"name": self.appname, "command": self.command})
        self.bottomstack.set_visible_child_name("queue")

        self.bottomrevealer.set_reveal_child(True)

        appicon = Gtk.Image.new()
        if self.UserSettings.config_usi:
            appicon.set_from_pixbuf(self.getSystemAppIcon(self.appname))
        else:
            appicon.set_from_pixbuf(self.getServerAppIcon(self.appname))
        label = Gtk.Label.new()
        label.set_text(self.appname)
        box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
        box.pack_start(appicon, False, True, 0)
        box.pack_start(label, False, True, 0)
        self.QueueListBox.add(box)
        self.QueueListBox.show_all()

        if not self.inprogress:
            self.actionPackage(self.appname, self.command)
            self.inprogress = True
            print("action " + self.appname)

    def on_raction_clicked(self, button):

        self.raction.set_sensitive(False)

        self.queue.append({"name": self.appname, "command": self.appname})
        self.bottomstack.set_visible_child_name("queue")

        self.bottomrevealer.set_reveal_child(True)

        appicon = Gtk.Image.new()
        if self.UserSettings.config_usi:
            appicon.set_from_pixbuf(self.getSystemAppIcon(self.appname))
        else:
            appicon.set_from_pixbuf(self.getServerAppIcon(self.appname))
        label = Gtk.Label.new()
        label.set_text(self.appname)
        box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
        box.pack_start(appicon, False, True, 0)
        box.pack_start(label, False, True, 0)
        self.QueueListBox.add(box)
        self.QueueListBox.show_all()

        if not self.inprogress:
            self.actionPackage(self.appname, self.appname)
            self.inprogress = True
            print("action " + self.appname)

    def on_topbutton1_clicked(self, button):
        if self.Server.connection and self.Server.app_scode == 200 and self.Server.cat_scode == 200:
            self.searchstack.set_visible_child_name("page0")
            self.homestack.set_visible_child_name("pardushome")
            self.HomeCategoryFlowBox.unselect_all()
            self.EditorAppsIconView.unselect_all()
            self.PardusAppsIconView.unselect_all()
            self.MostDownFlowBox.unselect_all()
            self.MostRateFlowBox.unselect_all()
        else:
            self.searchstack.set_visible_child_name("page2")
            self.homestack.set_visible_child_name("noserver")

        self.menubackbutton.set_sensitive(False)
        if self.topbutton2.get_style_context().has_class("suggested-action"):
            self.topbutton2.get_style_context().remove_class("suggested-action")
        if self.queuebutton.get_style_context().has_class("suggested-action"):
            self.queuebutton.get_style_context().remove_class("suggested-action")
        if not self.topbutton1.get_style_context().has_class("suggested-action"):
            self.topbutton1.get_style_context().add_class("suggested-action")

        self.topsearchbutton.set_active(self.statusoftopsearch)
        self.topsearchbutton.set_sensitive(True)

    def on_topbutton2_clicked(self, button):
        self.searchstack.set_visible_child_name("page1")
        self.homestack.set_visible_child_name("repohome")
        self.menubackbutton.set_sensitive(False)
        if self.topbutton1.get_style_context().has_class("suggested-action"):
            self.topbutton1.get_style_context().remove_class("suggested-action")
        if self.queuebutton.get_style_context().has_class("suggested-action"):
            self.queuebutton.get_style_context().remove_class("suggested-action")
        if not self.topbutton2.get_style_context().has_class("suggested-action"):
            self.topbutton2.get_style_context().add_class("suggested-action")

        # control for active actioned app

        if self.repoappclicked:
            self.RepoAppsTreeView.row_activated(self.activerepopath, self.RepoAppsTreeView.get_column(0))

            # Updating status tick of repo apps
            try:
                for row in self.searchstore:
                    installstatus = self.Package.isinstalled(row[0])
                    row[3] = installstatus
            except:
                pass

        self.statusoftopsearch = self.topsearchbutton.get_active()
        self.topsearchbutton.set_active(True)
        self.reposearchbar.grab_focus()

        self.topsearchbutton.set_sensitive(True)

    def on_queuebutton_clicked(self, button):
        self.homestack.set_visible_child_name("queue")
        self.menubackbutton.set_sensitive(False)
        if self.topbutton1.get_style_context().has_class("suggested-action"):
            self.topbutton1.get_style_context().remove_class("suggested-action")
        if self.topbutton2.get_style_context().has_class("suggested-action"):
            self.topbutton2.get_style_context().remove_class("suggested-action")
        if not self.queuebutton.get_style_context().has_class("suggested-action"):
            self.queuebutton.get_style_context().add_class("suggested-action")

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
        if self.locale == "tr":
            self.PardusCurrentCategoryString = "tümü"
        else:
            self.PardusCurrentCategoryString = "all"

        self.PardusCategoryFilter.refilter()

    def on_reposearchbutton_clicked(self, button):
        # self.RepoCategoryListBox.unselect_all()
        self.isRepoSearching = True
        # print("on_reposearchbutton_clicked")

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
        self.repoappclicked = True
        self.fromrepoapps = True
        self.activerepopath = path

        iter = self.searchstore.get_iter(path)
        value = self.searchstore.get_value(iter, 0)
        # print(value)

        self.repoappname = value
        self.appname = value
        isinstalled = self.Package.isinstalled(self.appname)

        if isinstalled is not None:
            self.raction.set_sensitive(True)
            if isinstalled:
                if self.raction.get_style_context().has_class("suggested-action"):
                    self.raction.get_style_context().remove_class("suggested-action")
                self.raction.get_style_context().add_class("destructive-action")
                self.raction.set_label(_(" Uninstall"))
                self.raction.set_image(Gtk.Image.new_from_stock("gtk-delete", Gtk.IconSize.BUTTON))
            else:
                if self.raction.get_style_context().has_class("destructive-action"):
                    self.raction.get_style_context().remove_class("destructive-action")
                self.raction.get_style_context().add_class("suggested-action")
                self.raction.set_label(_(" Install"))
                self.raction.set_image(Gtk.Image.new_from_stock("gtk-save", Gtk.IconSize.BUTTON))
        else:
            self.raction.set_sensitive(False)
            if self.raction.get_style_context().has_class("destructive-action"):
                self.raction.get_style_context().remove_class("destructive-action")
            if self.raction.get_style_context().has_class("suggested-action"):
                self.raction.get_style_context().remove_class("suggested-action")

            self.raction.set_label(_(" Not Found"))
            self.raction.set_image(Gtk.Image.new_from_stock("gtk-dialog-warning", Gtk.IconSize.BUTTON))

        if len(self.queue) > 0:
            for qa in self.queue:
                if self.appname == qa["name"]:
                    if isinstalled:
                        self.raction.set_label(_(" Removing"))
                    else:
                        self.raction.set_label(_(" Installing"))
                    self.raction.set_sensitive(False)

        self.rbotstack.set_visible_child_name("page1")
        self.rtitle.set_text(self.Package.summary(value))
        self.rdetail.set_text(self.Package.description(value, False))

    def on_topsearchbutton_toggled(self, button):
        if self.topsearchbutton.get_active():
            self.toprevealer.set_reveal_child(True)
            if self.searchstack.get_visible_child_name() == "page0":
                self.pardussearchbar.grab_focus()
                print("in grab focus")
            elif self.searchstack.get_visible_child_name() == "page1":
                self.reposearchbar.grab_focus()
        else:
            self.toprevealer.set_reveal_child(False)
            self.statusoftopsearch = False

    # def on_HeaderBarMenuButton_toggled(self, button):
    #     self.HeaderBarMenuButton.grab_focus()

    def on_menu_settings_clicked(self, button):
        self.PopoverMenu.popdown()
        self.topsearchbutton.set_active(False)
        self.topsearchbutton.set_sensitive(False)
        self.homestack.set_visible_child_name("preferences")
        self.menubackbutton.set_sensitive(False)
        self.UserSettings.readConfig()
        self.switchUSI.set_state(self.UserSettings.config_usi)
        self.switchEA.set_state(self.UserSettings.config_anim)
        self.topbutton2.get_style_context().remove_class("suggested-action")
        self.topbutton1.get_style_context().remove_class("suggested-action")
        self.preflabel.set_text("")
        self.prefcachebutton.set_sensitive(True)
        self.prefcachebutton.set_label(_("Clear"))
        self.prefapplybutton.set_sensitive(False)
        self.prefapplybutton.set_label(_("Apply"))

    def on_menu_updates_clicked(self, button):
        self.PopoverMenu.popdown()
        self.topsearchbutton.set_active(False)
        self.topsearchbutton.set_sensitive(False)
        self.homestack.set_visible_child_name("updates")
        self.menubackbutton.set_sensitive(False)
        self.topbutton2.get_style_context().remove_class("suggested-action")
        self.topbutton1.get_style_context().remove_class("suggested-action")
        self.updateerrorlabel.set_text("")

    def on_menu_about_clicked(self, button):
        self.PopoverMenu.popdown()
        self.aboutdialog.run()
        self.aboutdialog.hide()

    def on_menu_suggestapp_clicked(self, button):
        self.PopoverMenu.popdown()
        self.topsearchbutton.set_active(False)
        self.topsearchbutton.set_sensitive(False)
        self.menubackbutton.set_sensitive(False)
        self.topbutton2.get_style_context().remove_class("suggested-action")
        self.topbutton1.get_style_context().remove_class("suggested-action")
        self.SuggestCat.remove_all()
        self.SuggestCat.append_text(_("Select Category"))
        self.SuggestCat.set_active(0)
        cats = []
        for cat in self.Server.catlist:
            cats.append(cat[self.locale])
        cats = sorted(cats)
        for cat in cats:
            self.SuggestCat.append_text(cat)
        self.homestack.set_visible_child_name("suggestapp")
        self.SuggestStack.set_visible_child_name("suggest")
        self.SuggestSend.set_sensitive(True)

    def on_SuggestSend_clicked(self, button):
        self.sug_appname = self.SuggestAppName.get_text()

        self.sug_category_id = self.SuggestCat.get_active()
        self.sug_category = self.SuggestCat.get_active_text()

        desc_tr_buffer = self.SuggestDescTR.get_buffer()
        self.sug_desc_tr = desc_tr_buffer.get_text(desc_tr_buffer.get_start_iter(), desc_tr_buffer.get_end_iter(), True)

        desc_en_buffer = self.SuggestDescEN.get_buffer()
        self.sug_desc_en = desc_en_buffer.get_text(desc_en_buffer.get_start_iter(), desc_en_buffer.get_end_iter(), True)

        self.sug_license = self.SuggestLicense.get_text()

        copyright_buffer = self.SuggestCopyright.get_buffer()
        self.sug_copyright = copyright_buffer.get_text(copyright_buffer.get_start_iter(),
                                                       copyright_buffer.get_end_iter(), True)

        self.sug_website = self.SuggestWeb.get_text()
        self.sug_icon = self.SuggestIconChooser.get_filename()
        self.sug_inrepo = self.SuggestInRepo.get_active()

        self.sug_name = self.SuggestName.get_text()
        self.sug_mail = self.SuggestMail.get_text()

        valid, message = self.controlSuggest()

        if valid:
            self.SuggestInfoLabel.set_text("")
            img_valid = True
            if self.sug_icon:
                img_valid, img_message = self.controlSuggestIcon()
            else:
                self.sug_icon_raw = ""
            if img_valid:
                self.SuggestSend.set_sensitive(False)
                self.SuggestInfoLabel.set_text("")
                dic = {"appname": self.controlText(self.sug_appname), "category": self.controlText(self.sug_category),
                       "desc_tr": self.controlText(self.sug_desc_tr), "desc_en": self.controlText(self.sug_desc_en),
                       "license": self.controlText(self.sug_license), "copyright": self.controlText(self.sug_copyright),
                       "website": self.controlText(self.sug_website), "icon": self.sug_icon_raw,
                       "inrepo": self.sug_inrepo, "name": self.controlText(self.sug_name),
                       "mail": self.controlText(self.sug_mail), "mac": self.mac}
                self.AppRequest.send("POST", self.Server.serverurl + self.Server.serversendsuggestapp, dic)
            else:
                self.SuggestInfoLabel.set_text("{}".format(img_message))
        else:
            self.SuggestInfoLabel.set_text("{} : {} {}".format(_("Error"), message, _("is empty")))

    def controlText(self, text):

        text = str(text).strip()

        if len(text) > 1000:
            text = text[:1000]

        return text

    def controlSuggest(self):

        if self.sug_appname.strip() == "":
            return False, _("Application Name")

        if self.sug_category_id == 0 or self.sug_category_id == -1:
            return False, _("Category")

        if self.sug_desc_tr.strip() == "":
            return False, _("Description ( Turkish )")

        if self.sug_desc_en.strip() == "":
            return False, _("Description ( English )")

        if self.sug_license.strip() == "":
            return False, _("License")

        if self.sug_copyright.strip() == "":
            return False, _("Copyright Text")

        if self.sug_website.strip() == "":
            return False, _("Website")

        # if self.sug_icon is None:
        #     return False, _("Icon")

        if self.sug_name.strip() == "":
            return False, _("Name")

        if self.sug_mail.strip() == "":
            return False, _("Mail")

        return True, "ok"

    def controlSuggestIcon(self):

        if not os.path.isfile(self.sug_icon):
            return False, _("Icon not found")

        if os.path.getsize(self.sug_icon) > 1048576:  # Max 1 MB
            return False, _("Icon size must be less than 1 MB")

        try:
            self.sug_icon_raw = open(self.sug_icon).read()
        except:
            return False, _("Icon file read error")

        try:
            filename, file_extension = os.path.splitext(self.sug_icon)
        except:
            return False, _("Icon file must be svg")

        if file_extension != ".svg":
            return False, _("Icon file must be svg")

        return True, "ok"

    def resetSuggestAppForm(self):
        self.SuggestAppName.set_text("")
        self.SuggestDescTR.get_buffer().delete(self.SuggestDescTR.get_buffer().get_start_iter(),
                                               self.SuggestDescTR.get_buffer().get_end_iter())
        self.SuggestDescEN.get_buffer().delete(self.SuggestDescEN.get_buffer().get_start_iter(),
                                               self.SuggestDescEN.get_buffer().get_end_iter())
        self.SuggestLicense.set_text("")
        self.SuggestCopyright.get_buffer().delete(self.SuggestCopyright.get_buffer().get_start_iter(),
                                                  self.SuggestCopyright.get_buffer().get_end_iter())
        self.SuggestWeb.set_text("")
        self.SuggestName.set_text("")
        self.SuggestMail.set_text("")
        self.SuggestInRepo.set_active(False)
        self.SuggestIconChooser.unselect_all()

    def on_prefapplybutton_clicked(self, button):
        print("on_prefbutton_clicked")
        usi = self.switchUSI.get_state()
        ea = self.switchEA.get_state()
        print("USI : {}".format(usi))
        print("EA : {}".format(ea))

        user_config_anim = self.UserSettings.config_anim
        user_config_usi = self.UserSettings.config_usi

        try:
            self.UserSettings.writeConfig(usi, ea)
            self.usersettings()

            if user_config_anim != ea:
                print("Updating user animation state")
                self.setAnimations()

            if user_config_usi != usi:
                print("Updating user icon state")
                self.PardusAppListStore.clear()
                self.EditorListStore.clear()
                for row in self.HomeCategoryFlowBox:
                    self.HomeCategoryFlowBox.remove(row)
                for row in self.MostDownFlowBox:
                    self.MostDownFlowBox.remove(row)
                for row in self.MostRateFlowBox:
                    self.MostRateFlowBox.remove(row)
                if not usi:
                    self.serverappicons = self.Server.getAppIcons()
                    self.servercaticons = self.Server.getCategoryIcons()
                self.setPardusApps()
                self.setPardusCategories()
                self.setEditorApps()
                self.setMostApps()

            self.prefapplybutton.set_sensitive(False)
            self.prefapplybutton.set_label(_("Applied"))
            self.preflabel.set_text(_("Changes applied successfully "))

        except Exception as e:
            self.prefapplybutton.set_sensitive(True)
            self.prefapplybutton.set_label(_("Error"))
            self.preflabel.set_text(str(e))

    def on_prefswitch_state_set(self, switch, state):
        self.prefapplybutton.set_sensitive(True)
        self.prefapplybutton.set_label(_("Apply"))

    def on_prefcachebutton_clicked(self, button):
        state, message = self.Server.deleteCache()
        if state:
            self.prefcachebutton.set_sensitive(False)
            self.prefcachebutton.set_label(_("Cleared"))
            self.preflabel.set_text(_("Cache files cleared, please close and reopen the application"))
        else:
            self.prefcachebutton.set_sensitive(True)
            self.prefcachebutton.set_label(_("Error"))
            self.preflabel.set_text(message)

    def on_bottomerrorbutton_clicked(self, button):
        self.bottomrevealer.set_reveal_child(False)

    def on_updatecontrolbutton_clicked(self, button):
        print("on_updatecontrolbutton_clicked")

        if len(self.queue) == 0:
            self.updateerrorlabel.set_text("")
            self.updateclicked = True
            self.updatecontrolbutton.set_sensitive(False)
            self.updatespinner.start()
            self.updatestack.set_visible_child_name("output")
            command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py", "update"]
            self.pid = self.startProcess(command)
            print("PID : {}".format(self.pid))
        else:
            print("wait for the queue to finish")
            self.updateerrorlabel.set_text(_("Package manager is busy"))

    def on_upgradebutton_clicked(self, button):
        subprocess.Popen(["gpk-update-viewer"])

    def on_autoremovebutton_clicked(self, button):
        if len(self.queue) == 0:
            self.updateerrorlabel.set_text("")
            self.updateclicked = True
            self.updatecontrolbutton.set_sensitive(False)
            self.updatespinner.start()
            self.updatestack.set_visible_child_name("output")
            command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py", "removeauto"]
            self.pid = self.startProcess(command)
            print("PID : {}".format(self.pid))
        else:
            print("wait for the queue to finish")
            self.updateerrorlabel.set_text(_("Package manager is busy"))

    def on_residualbutton_clicked(self, button):
        if len(self.queue) == 0:
            self.updateerrorlabel.set_text("")
            self.updateclicked = True
            self.updatecontrolbutton.set_sensitive(False)
            self.updatespinner.start()
            self.updatestack.set_visible_child_name("output")
            command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py", "removeresidual",
                       " ".join(self.Package.residual())]
            # print(command)
            self.pid = self.startProcess(command)
            print("PID : {}".format(self.pid))
        else:
            print("wait for the queue to finish")
            self.updateerrorlabel.set_text(_("Package manager is busy"))

    def getActiveAppOnUI(self):
        ui_appname = ""
        selected_items = self.PardusAppsIconView.get_selected_items()
        editor_selected_items = self.EditorAppsIconView.get_selected_items()
        if len(selected_items) == 1:
            treeiter = self.PardusCategoryFilter.get_iter(selected_items[0])
            ui_appname = self.PardusCategoryFilter.get(treeiter, 1)[0]
        if len(editor_selected_items) == 1:
            treeiter = self.EditorListStore.get_iter(editor_selected_items[0])
            ui_appname = self.EditorListStore.get(treeiter, 1)[0]
        if self.frommostapps:
            if self.mostappname:
                ui_appname = self.mostappname
            else:
                ui_appname = self.detailsappname
        if self.fromrepoapps:
            ui_appname = self.repoappname
        print("UI APP = " + ui_appname)
        return ui_appname

    def actionPackage(self, appname, command):

        self.inprogress = True
        self.topspinner.start()

        ui_appname = self.getActiveAppOnUI()

        if ui_appname == appname:
            self.dActionButton.set_sensitive(False)
            self.dActionButton.set_image(Gtk.Image.new_from_stock("gtk-convert", Gtk.IconSize.BUTTON))
            self.raction.set_sensitive(False)
            self.raction.set_image(Gtk.Image.new_from_stock("gtk-convert", Gtk.IconSize.BUTTON))

        self.actionedappname = appname
        self.actionedcommand = command
        self.actionedappdesktop = self.desktop_file
        self.isinstalled = self.Package.isinstalled(self.actionedappname)

        if self.isinstalled:
            if ui_appname == appname:
                self.dActionButton.set_label(_(" Removing"))
                self.raction.set_label(_(" Removing"))
            command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py", "remove",
                       self.actionedappname]
        else:
            if ui_appname == appname:
                self.dActionButton.set_label(_(" Installing"))
                self.raction.set_label(_(" Installing"))
            command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py", "install",
                       self.actionedcommand]

        self.pid = self.startProcess(command)
        print("PID : {}".format(self.pid))

    def startProcess(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(params, flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_output=True, standard_error=True)
        GLib.io_add_watch(GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.onProcessStdout)
        GLib.io_add_watch(GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.onProcessStderr)
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, self.onProcessExit)

        return pid

    def onProcessStdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False

        line = source.readline()
        # print(line)
        if self.updateclicked:
            self.updatetextview.get_buffer().insert(self.updatetextview.get_buffer().get_end_iter(), line)
            self.updatetextview.scroll_to_iter(self.updatetextview.get_buffer().get_end_iter(), 0.0, False, 0.0, 0.0)
        return True

    def onProcessStderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False

        line = source.readline()

        # print("error: " + line)

        if not self.updateclicked:
            if "dlstatus" in line:
                percent = line.split(":")[2].split(".")[0]
                # if self.Package.missingdeps(self.actionedappname):
                #     print("Downloading dependencies " + percent + " %")
                #     self.progresstextlabel.set_text(
                #         self.actionedappname + " | " + "Downloading dependencies : " + percent + " %")
                # else:
                #     print("Controlling dependencies : " + percent + " %")
                #     self.progresstextlabel.set_text(
                #         self.actionedappname + " | " + "Controlling dependencies : " + percent + " %")
                # print("1/2 : " + percent + " %")
                self.progresstextlabel.set_text(self.actionedappname + " : " + percent + " %")
            elif "pmstatus" in line:
                percent = line.split(":")[2].split(".")[0]
                # print("Processing : " + percent)
                if self.isinstalled:
                    self.progresstextlabel.set_text(
                        self.actionedappname + " | " + _("Removing") + ": " + percent + " %")
                else:
                    self.progresstextlabel.set_text(
                        self.actionedappname + " | " + _("Installing") + ": " + percent + " %")
            elif "E:" in line and ".deb" in line:
                print("connection error")
                self.error = True
            elif "E:" in line and "dpkg --configure -a" in line:
                print("dpkg --configure -a error")
                self.error = True
                self.dpkgconferror = True
            elif "E:" in line and "/var/lib/dpkg/lock-frontend" in line:
                print("/var/lib/dpkg/lock-frontend error")
                self.error = True
                self.dpkglockerror = True

        else:  # in apt update
            if "dlstatus" in line:
                percent = line.split(":")[2].split(".")[0]

        return True

    def onProcessExit(self, pid, status):

        if not self.updateclicked:

            if not self.error:
                if status == 0:
                    if self.isinstalled:
                        self.progresstextlabel.set_text(self.actionedappname + _(" | Removed : 100 %"))
                    else:
                        self.progresstextlabel.set_text(self.actionedappname + _(" | Installed : 100 %"))
                else:
                    self.progresstextlabel.set_text(self.actionedappname + _(" | " + " Not Completed"))
            else:
                self.errormessage = _("<b><span color='red'>Connection Error !</span></b>")
                if self.dpkglockerror:
                    self.errormessage = _("<b><span color='red'>Dpkg Lock Error !</span></b>")
                elif self.dpkgconferror:
                    self.errormessage = _("<b><span color='red'>Dpkg Interrupt Error !</span></b>")

            self.Package.updatecache()

            if status == 0 and not self.error:
                self.notify()
                self.sendDownloaded(self.actionedappname)

            self.controlView()

            ui_appname = self.getActiveAppOnUI()
            if ui_appname == self.actionedappname:
                self.dActionButton.set_sensitive(True)
                self.raction.set_sensitive(True)

            self.topspinner.stop()
            print("Exit Code : {}".format(status))

            self.inprogress = False
            self.queue.pop(0)
            self.QueueListBox.remove(self.QueueListBox.get_row_at_index(0))
            if len(self.queue) > 0:
                self.actionPackage(self.queue[0]["name"], self.queue[0]["command"])
            else:
                self.bottomrevealer.set_reveal_child(False)
                if not self.error:
                    self.progresstextlabel.set_text("")

            if self.error:
                self.bottomrevealer.set_reveal_child(True)
                self.bottomstack.set_visible_child_name("error")
                self.bottomerrorlabel.set_markup("<span color='red'>{}</span>".format(self.errormessage))

            self.error = False
            self.dpkglockerror = False
            self.dpkgconferror = False

            if status == 256:
                self.errormessage = _("Only one software management tool is allowed to run at the same time.\n"
                                      "Please close the other application e.g. 'Update Manager', 'aptitude' or 'Synaptic' first.")
                self.bottomrevealer.set_reveal_child(True)
                self.bottomstack.set_visible_child_name("error")
                self.bottomerrorlabel.set_markup("<span color='red'>{}</span>".format(self.errormessage))

        else:
            self.updateclicked = False
            self.updatecontrolbutton.set_sensitive(True)
            self.updatespinner.stop()
            self.updatetextview.scroll_to_iter(self.updatetextview.get_buffer().get_end_iter(), 0.0, False, 0.0, 0.0)
            if status == 0:
                self.Package.updatecache()

                residual = self.Package.residual()
                removable = self.Package.autoremovable()
                upgradable = self.Package.upgradable()

                if len(residual) == 0:
                    self.residualtextview.get_buffer().set_text(_("No action required"))
                    self.residualbutton.set_sensitive(False)
                else:
                    self.residualtextview.get_buffer().set_text("\n".join(self.Package.residual()))
                    self.residualbutton.set_sensitive(True)
                if len(removable) == 0:
                    self.removabletextview.get_buffer().set_text(_("No action required"))
                    self.autoremovebutton.set_sensitive(False)
                else:
                    self.removabletextview.get_buffer().set_text("\n".join(self.Package.autoremovable()))
                    self.autoremovebutton.set_sensitive(True)
                if len(upgradable) == 0:
                    self.upgradabletextview.get_buffer().set_text(_("All packages are up to date"))
                    self.upgradebutton.set_sensitive(False)
                else:
                    self.upgradabletextview.get_buffer().set_text("\n".join(self.Package.upgradable()))
                    self.upgradebutton.set_sensitive(True)

                self.updatestack.set_visible_child_name("list")
            else:
                self.updatestack.set_visible_child_name("output")

    def controlView(self):
        selected_items = self.PardusAppsIconView.get_selected_items()
        # print("selected_items " + str(selected_items))

        editor_selected_items = self.EditorAppsIconView.get_selected_items()
        print("editor_selected_items " + str(editor_selected_items))
        if len(selected_items) == 1:
            treeiter = self.PardusCategoryFilter.get_iter(selected_items[0])
            appname = self.PardusCategoryFilter.get(treeiter, 1)[0]
            print("in controlView " + appname)
            if appname == self.actionedappname:
                self.updateActionButtons(1)

        if len(editor_selected_items) == 1:
            treeiter = self.EditorListStore.get_iter(editor_selected_items[0])
            appname = self.EditorListStore.get(treeiter, 1)[0]
            print("in controlView " + appname)
            if appname == self.actionedappname:
                self.updateActionButtons(1)

        if self.frommostapps:
            # print("self.frommostapps" + str(self.frommostapps))
            if self.mostappname:
                if self.mostappname == self.actionedappname:
                    self.updateActionButtons(1)
            else:
                if self.detailsappname == self.actionedappname:
                    self.updateActionButtons(1)

        if self.fromrepoapps:
            if self.repoappname == self.actionedappname:
                self.updateActionButtons(2)

            # Updating status tick of repo apps
            try:
                for row in self.searchstore:
                    installstatus = self.Package.isinstalled(row[0])
                    row[3] = installstatus
            except:
                pass

    def updateActionButtons(self, repo):
        if repo == 1:  # pardus apps
            if self.Package.isinstalled(self.actionedappname):
                if self.dActionButton.get_style_context().has_class("suggested-action"):
                    self.dActionButton.get_style_context().remove_class("suggested-action")
                self.dActionButton.get_style_context().add_class("destructive-action")
                self.dActionButton.set_label(_(" Uninstall"))
                self.dActionButton.set_image(Gtk.Image.new_from_stock("gtk-delete", Gtk.IconSize.BUTTON))

                if self.actionedappdesktop != "" and self.actionedappdesktop is not None:
                    self.dOpenButton.set_visible(True)

                self.wpcformcontrolLabel.set_markup("")

            else:
                if self.dActionButton.get_style_context().has_class("destructive-action"):
                    self.dActionButton.get_style_context().remove_class("destructive-action")
                self.dActionButton.get_style_context().add_class("suggested-action")
                self.dActionButton.set_label(_(" Install"))
                self.dActionButton.set_image(Gtk.Image.new_from_stock("gtk-save", Gtk.IconSize.BUTTON))

                self.dOpenButton.set_visible(False)

                self.wpcformcontrolLabel.set_markup(
                    "<span color='red'>{}</span>".format(_("You need to install the application")))

        if repo == 2:  # repo apps
            if self.Package.isinstalled(self.actionedappname):
                if self.raction.get_style_context().has_class("suggested-action"):
                    self.raction.get_style_context().remove_class("suggested-action")
                self.raction.get_style_context().add_class("destructive-action")
                self.raction.set_label(_(" Uninstall"))
                self.raction.set_image(Gtk.Image.new_from_stock("gtk-delete", Gtk.IconSize.BUTTON))
            else:
                if self.raction.get_style_context().has_class("destructive-action"):
                    self.raction.get_style_context().remove_class("destructive-action")
                self.raction.get_style_context().add_class("suggested-action")
                self.raction.set_label(_(" Install"))
                self.raction.set_image(Gtk.Image.new_from_stock("gtk-save", Gtk.IconSize.BUTTON))

    def notify(self):

        if Notify.is_initted():
            Notify.uninit()

        Notify.init(self.actionedappname)
        if self.isinstalled:
            notification = Notify.Notification.new(self.actionedappname + _(" Removed"))
        else:
            notification = Notify.Notification.new(self.actionedappname + _(" Installed"))

        if self.UserSettings.config_usi:
            pixbuf = self.getSystemAppIcon(self.actionedappname, 96)
        else:
            pixbuf = self.getServerAppIcon(self.actionedappname, 96)

        notification.set_icon_from_pixbuf(pixbuf)
        notification.show()

    def sendDownloaded(self, appname):
        try:
            installed = self.Package.isinstalled(appname)
            if installed is None:
                installed = False
            dic = {"mac": self.mac, "app": appname, "installed": installed}
            self.AppRequest.send("POST", self.Server.serverurl + self.Server.serversenddownload, dic)
        except Exception as e:
            print(str(e))
