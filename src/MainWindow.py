#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import os
import re
import subprocess
import threading
import netifaces
import psutil
from datetime import datetime
import gi, sys
import locale
from locale import gettext as _
from locale import getlocale

import matplotlib.pyplot as plt
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas

locale.bindtextdomain('pardus-software', '/usr/share/locale')
locale.textdomain('pardus-software')

gi.require_version("GLib", "2.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Notify", "0.7")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Vte", "2.91")
from gi.repository import GLib, Gtk, GObject, Notify, GdkPixbuf, Gio, Gdk, Vte

from Package import Package
from Server import Server
from GnomeRatingServer import GnomeRatingServer
# from CellRendererButton import CellRendererButton

from AppImage import AppImage
from AppDetail import AppDetail
from AppRequest import AppRequest
from GnomeComment import GnomeComment
from PardusComment import PardusComment
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

        self.applist = []
        self.catlist = []

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
        self.SubCategoryFlowBox = self.GtkBuilder.get_object("SubCategoryFlowBox")
        self.MostDownFlowBox = self.GtkBuilder.get_object("MostDownFlowBox")
        self.MostRateFlowBox = self.GtkBuilder.get_object("MostRateFlowBox")
        self.LastAddedFlowBox = self.GtkBuilder.get_object("LastAddedFlowBox")

        self.hometotaldc = self.GtkBuilder.get_object("hometotaldc")
        self.hometotalrc = self.GtkBuilder.get_object("hometotalrc")
        self.statstotaldc = self.GtkBuilder.get_object("statstotaldc")
        self.statstotalrc = self.GtkBuilder.get_object("statstotalrc")
        self.statsweblabel = self.GtkBuilder.get_object("statsweblabel")
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
        self.reposearchbutton = self.GtkBuilder.get_object("reposearchbutton")
        self.toprevealer = self.GtkBuilder.get_object("toprevealer")
        self.bottomrevealer = self.GtkBuilder.get_object("bottomrevealer")

        self.bottomerrorlabel = self.GtkBuilder.get_object("bottomerrorlabel")
        self.bottomerrorbutton = self.GtkBuilder.get_object("bottomerrorbutton")

        self.pardusicb = self.GtkBuilder.get_object("pardusicb")
        self.sortPardusAppsCombo = self.GtkBuilder.get_object("sortPardusAppsCombo")
        self.SubCatCombo = self.GtkBuilder.get_object("SubCatCombo")

        self.mainstack = self.GtkBuilder.get_object("mainstack")
        self.homestack = self.GtkBuilder.get_object("homestack")
        self.searchstack = self.GtkBuilder.get_object("searchstack")
        self.bottomstack = self.GtkBuilder.get_object("bottomstack")
        self.commentstack = self.GtkBuilder.get_object("commentstack")
        self.prefstack = self.GtkBuilder.get_object("prefstack")
        self.activatestack = self.GtkBuilder.get_object("activatestack")
        self.pardusAppsStack = self.GtkBuilder.get_object("pardusAppsStack")
        self.tryfixstack = self.GtkBuilder.get_object("tryfixstack")
        self.queuestack = self.GtkBuilder.get_object("queuestack")
        self.myappsstack = self.GtkBuilder.get_object("myappsstack")
        self.myappsdetailsstack = self.GtkBuilder.get_object("myappsdetailsstack")
        self.activate_repo_label = self.GtkBuilder.get_object("activate_repo_label")
        self.activate_info_label = self.GtkBuilder.get_object("activate_info_label")
        self.activating_spinner = self.GtkBuilder.get_object("activating_spinner")
        self.dIcon = self.GtkBuilder.get_object("dIcon")
        self.dName = self.GtkBuilder.get_object("dName")
        self.dActionButton = self.GtkBuilder.get_object("dActionButton")
        self.dOpenButton = self.GtkBuilder.get_object("dOpenButton")
        self.dAptUpdateButton = self.GtkBuilder.get_object("dAptUpdateButton")
        self.dAptUpdateInfoLabel = self.GtkBuilder.get_object("dAptUpdateInfoLabel")
        self.dAptUpdateSpinner = self.GtkBuilder.get_object("dAptUpdateSpinner")
        self.dAptUpdateBox = self.GtkBuilder.get_object("dAptUpdateBox")
        # self.dOpenButton.get_style_context().add_class("circular")
        self.dDisclaimerButton = self.GtkBuilder.get_object("dDisclaimerButton")
        self.DisclaimerPopover = self.GtkBuilder.get_object("DisclaimerPopover")
        self.dDescriptionLabel = self.GtkBuilder.get_object("dDescriptionLabel")
        self.dSection = self.GtkBuilder.get_object("dSection")
        self.dMaintainer = self.GtkBuilder.get_object("dMaintainer")
        self.dVersion = self.GtkBuilder.get_object("dVersion")
        self.dSize = self.GtkBuilder.get_object("dSize")
        self.dSizeTitle = self.GtkBuilder.get_object("dSizeTitle")
        self.dSizeGrid = self.GtkBuilder.get_object("dSizeGrid")
        self.dComponent = self.GtkBuilder.get_object("dComponent")
        self.dType = self.GtkBuilder.get_object("dType")
        self.dCategory = self.GtkBuilder.get_object("dCategory")
        self.dLicense = self.GtkBuilder.get_object("dLicense")
        self.licensePopover = self.GtkBuilder.get_object("licensePopover")
        self.licenseHeader = self.GtkBuilder.get_object("licenseHeader")
        self.licenseBody = self.GtkBuilder.get_object("licenseBody")
        self.dCodename = self.GtkBuilder.get_object("dCodename")
        self.dWeb = self.GtkBuilder.get_object("dWeb")
        self.dMail = self.GtkBuilder.get_object("dMail")
        self.dtDownload = self.GtkBuilder.get_object("dtDownload")
        self.dtTotalRating = self.GtkBuilder.get_object("dtTotalRating")
        self.dtUserRating = self.GtkBuilder.get_object("dtUserRating")
        self.dtAverageRating = self.GtkBuilder.get_object("dtAverageRating")
        self.dViewonweb = self.GtkBuilder.get_object("dViewonweb")

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
        self.pcMoreButton = self.GtkBuilder.get_object("pcMoreButton")
        self.gcMoreButtonTR = self.GtkBuilder.get_object("gcMoreButtonTR")
        self.gcMoreButtonEN = self.GtkBuilder.get_object("gcMoreButtonEN")
        self.gcStack = self.GtkBuilder.get_object("gcStack")
        self.CommentsNotebook = self.GtkBuilder.get_object("CommentsNotebook")
        self.gcInfoLabel = self.GtkBuilder.get_object("gcInfoLabel")
        self.gcInfoLabel.set_markup("<small>{}</small>".format(
            _("These comments are pulled from <a href='https://odrs.gnome.org'>GNOME ODRS</a>.")))

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

        self.tryfixButton = self.GtkBuilder.get_object("tryfixButton")
        self.tryfixSpinner = self.GtkBuilder.get_object("tryfixSpinner")
        self.headerAptUpdateSpinner = self.GtkBuilder.get_object("headerAptUpdateSpinner")

        self.ui_myapps_app = self.GtkBuilder.get_object("ui_myapps_app")
        self.ui_myapps_package = self.GtkBuilder.get_object("ui_myapps_package")
        self.ui_myapps_icon = self.GtkBuilder.get_object("ui_myapps_icon")
        self.ui_myapps_description = self.GtkBuilder.get_object("ui_myapps_description")
        self.ui_myapps_uninstall_button = self.GtkBuilder.get_object("ui_myapps_uninstall_button")
        self.ui_myapps_accept_disclaimer = self.GtkBuilder.get_object("ui_myapps_accept_disclaimer")
        self.ui_myapps_spinner = self.GtkBuilder.get_object("ui_myapps_spinner")
        self.ui_myapps_disclaimer_label = self.GtkBuilder.get_object("ui_myapps_disclaimer_label")
        self.ui_myapp_toremove_label = self.GtkBuilder.get_object("ui_myapp_toremove_label")
        self.ui_myapp_toinstall_label = self.GtkBuilder.get_object("ui_myapp_toinstall_label")
        self.ui_myapp_broken_label = self.GtkBuilder.get_object("ui_myapp_broken_label")
        self.ui_myapp_fsize_label = self.GtkBuilder.get_object("ui_myapp_fsize_label")
        self.ui_myapp_dsize_label = self.GtkBuilder.get_object("ui_myapp_dsize_label")
        self.ui_myapp_isize_label = self.GtkBuilder.get_object("ui_myapp_isize_label")
        self.ui_myapp_toremove_box = self.GtkBuilder.get_object("ui_myapp_toremove_box")
        self.ui_myapp_toinstall_box = self.GtkBuilder.get_object("ui_myapp_toinstall_box")
        self.ui_myapp_broken_box = self.GtkBuilder.get_object("ui_myapp_broken_box")
        self.ui_myapp_fsize_box = self.GtkBuilder.get_object("ui_myapp_fsize_box")
        self.ui_myapp_dsize_box = self.GtkBuilder.get_object("ui_myapp_dsize_box")
        self.ui_myapp_isize_box = self.GtkBuilder.get_object("ui_myapp_isize_box")

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
        self.switchSAA = self.GtkBuilder.get_object("switchSAA")
        self.switchHERA = self.GtkBuilder.get_object("switchHERA")
        self.switchSGC = self.GtkBuilder.get_object("switchSGC")
        self.switchUDT = self.GtkBuilder.get_object("switchUDT")
        self.switchAPTU = self.GtkBuilder.get_object("switchAPTU")
        self.preflabel = self.GtkBuilder.get_object("preflabel")
        self.prefServerLabel = self.GtkBuilder.get_object("prefServerLabel")
        self.prefcachebutton = self.GtkBuilder.get_object("prefcachebutton")
        self.PopoverPrefTip = self.GtkBuilder.get_object("PopoverPrefTip")
        self.prefTipLabel = self.GtkBuilder.get_object("prefTipLabel")
        self.tip_usi = self.GtkBuilder.get_object("tip_usi")
        self.tip_ea = self.GtkBuilder.get_object("tip_ea")
        self.tip_soaa = self.GtkBuilder.get_object("tip_soaa")
        self.tip_hera = self.GtkBuilder.get_object("tip_hera")
        self.tip_icons = self.GtkBuilder.get_object("tip_icons")
        self.tip_sgc = self.GtkBuilder.get_object("tip_sgc")
        self.tip_udt = self.GtkBuilder.get_object("tip_udt")
        self.tip_aptu = self.GtkBuilder.get_object("tip_aptu")
        self.setServerIconCombo = self.GtkBuilder.get_object("setServerIconCombo")
        self.selecticonsBox = self.GtkBuilder.get_object("selecticonsBox")

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
        self.menu_myapps = self.GtkBuilder.get_object("menu_myapps")
        self.menu_statistics = self.GtkBuilder.get_object("menu_statistics")

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

        self.statstack = self.GtkBuilder.get_object("statstack")
        self.stats1ViewPort = self.GtkBuilder.get_object("stats1ViewPort")
        self.stats2ViewPort = self.GtkBuilder.get_object("stats2ViewPort")
        self.stats3ViewPort = self.GtkBuilder.get_object("stats3ViewPort")

        self.PardusCurrentCategory = -1
        if self.locale == "tr":
            self.PardusCurrentCategoryString = "tümü"
            self.RepoCurrentCategory = "tümü"
        else:
            self.PardusCurrentCategoryString = "all"
            self.RepoCurrentCategory = "all"

        self.PardusCurrentCategorySubCats = False
        self.PardusCurrentCategoryExternal = False
        self.PardusCurrentCategorySubCategories = []

        self.useDynamicListStore = False
        self.repoappname = ""
        self.repoappclicked = False

        self.PardusCategoryFilter = self.GtkBuilder.get_object("PardusCategoryFilter")
        self.PardusCategoryFilter.set_visible_func(self.PardusCategoryFilterFunction)
        # self.PardusCategoryFilter.refilter()

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
        self.appimage1stack = self.GtkBuilder.get_object("appimage1stack")
        self.appimage2stack = self.GtkBuilder.get_object("appimage2stack")
        self.fullscreen_image = self.GtkBuilder.get_object("fullscreen_image")
        # self.getDisplay()

        self.mac = self.getMac()

        self.par_desc_more = self.GtkBuilder.get_object("par_desc_more")

        self.MainWindow = self.GtkBuilder.get_object("MainWindow")
        self.MainWindow.set_application(application)

        self.mainstack.set_visible_child_name("splash")

        self.HeaderBarMenuButton.set_sensitive(False)
        self.menubackbutton.set_sensitive(False)
        self.topbutton1.set_sensitive(False)
        self.topbutton2.set_sensitive(False)
        self.topsearchbutton.set_sensitive(False)

        self.fromexternal = False
        self.externalactioned = False
        self.isinstalled = None
        self.correctsourcesclicked = False

        self.actionedappname = ""
        self.actionedenablingappname = ""
        self.actionedappdesktop = ""
        self.actionedenablingappdesktop = ""
        self.actionedappcommand = ""
        self.actionedenablingappcommand = ""

        self.queue = []
        self.inprogress = False

        self.serverappicons = False
        self.servercaticons = False

        self.frommostapps = False
        self.fromrepoapps = False
        self.fromdetails = False
        self.myapps_clicked = False
        self.mda_clicked = False
        self.mra_clicked = False
        self.la_clicked = False

        self.statisticsSetted = False

        self.repoappsinit = False

        self.isbroken = False

        self.mostappname = None
        self.detailsappname = None

        self.applist = []
        self.fullapplist = []
        self.catlist = []
        self.fullcatlist = []

        self.myapp_toremove_list = []
        self.myapp_toremove = ""
        self.myapp_toremove_desktop = ""

        self.important_packages = ["pardus-common-desktop", "pardus-xfce-desktop", "pardus-gnome-desktop",
                                   "pardus-edu-common-desktop", "pardus-edu-gnome-desktop", "eta-common-desktop"
                                   "eta-gnome-desktop", "eta-nonhid-gnome-desktop", "eta-gnome-desktop-other",
                                   "eta-nonhid-gnome-desktop-other"]

        self.prefback = "pardushome"

        self.statusoftopsearch = self.topsearchbutton.get_active()

        self.errormessage = ""

        self.updateclicked = False
        self.aptupdateclicked = False

        self.desktop_file = ""
        self.desktop_file_extras = ""

        self.command = ""

        self.rate_average = 0
        self.rate_individual = _("is None")
        self.rate_author = ""
        self.rate_comment = ""

        self.imgfullscreen = False

        self.imgfullscreen_count = 0
        self.down_image = 0

        cssProvider = Gtk.CssProvider()
        cssProvider.load_from_path(os.path.dirname(os.path.abspath(__file__)) + "/../css/style.css")
        screen = Gdk.Screen.get_default()
        styleContext = Gtk.StyleContext()
        styleContext.add_provider_for_screen(screen, cssProvider,
                                             Gtk.STYLE_PROVIDER_PRIORITY_USER)
        # With the others GTK_STYLE_PROVIDER_PRIORITY values get the same result.

        self.vteterm = Vte.Terminal()
        self.vteterm.set_scrollback_lines(-1)
        menu = Gtk.Menu()
        menu_items = Gtk.MenuItem(label=_("Copy selected text"))
        menu.append(menu_items)
        menu_items.connect("activate", self.menu_action, self.vteterm)
        menu_items.show()
        self.vteterm.connect_object("event", self.vte_event, menu)
        vtebox = self.GtkBuilder.get_object("VteBox")
        vtebox.add(self.vteterm)

        self.PardusCommentListBox = self.GtkBuilder.get_object("PardusCommentListBox")
        self.GnomeCommentListBoxEN = self.GtkBuilder.get_object("GnomeCommentListBoxEN")
        self.GnomeCommentListBoxTR = self.GtkBuilder.get_object("GnomeCommentListBoxTR")
        self.QueueListBox = self.GtkBuilder.get_object("QueueListBox")

        self.MyAppsListBox = self.GtkBuilder.get_object("MyAppsListBox")

        # Set version
        # If not getted from __version__ file then accept version in MainWindow.glade file
        try:
            version = open(os.path.dirname(os.path.abspath(__file__)) + "/__version__").readline()
            self.aboutdialog.set_version(version)
        except:
            pass

        self.status_serverapps = False
        self.status_servercats = False
        self.status_serverhome = False
        self.status_serverstatistics = False
        self.serverappicons_done = False
        self.servercaticons_done = False

        self.AppImage = AppImage()
        self.AppImage.Pixbuf = self.Pixbuf

        self.AppDetail = AppDetail()
        self.AppDetail.Detail = self.Detail

        self.AppRequest = AppRequest()
        self.AppRequest.Request = self.Request

        self.GnomeComment = GnomeComment()
        self.GnomeComment.gComment = self.gComment

        self.PardusComment = PardusComment()
        self.PardusComment.pComment = self.pComment

        self.usersettings()

        if self.UserSettings.config_udt:
            Gtk.Settings.get_default().props.gtk_application_prefer_dark_theme = True

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
            user_locale = os.getenv("LANG").split(".")[0].split("_")[0]
        except Exception as e:
            print("{}".format(e))
            try:
                user_locale = getlocale()[0].split("_")[0]
            except Exception as e:
                print("{}".format(e))
                user_locale = "en"
        if user_locale != "tr" and user_locale != "en":
            user_locale = "en"
        return user_locale

    def getDisplay(self):
        # defwindow = Gdk.get_default_root_window()
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        geometry = monitor.get_geometry()
        self.s_width = geometry.width
        self.s_height = geometry.height

    def worker(self):
        GLib.idle_add(self.splashspinner.start)
        self.setAnimations()
        self.package()
        self.server()

    def aptUpdate(self):
        if self.Server.connection and self.UserSettings.config_aptup:
            waittime = 86400
            if self.UserSettings.config_forceaptuptime == 0:
                waittime = self.Server.aptuptime
            else:
                waittime = self.UserSettings.config_forceaptuptime
            if self.UserSettings.config_lastaptup + waittime < int(datetime.now().timestamp()):
                self.headerAptUpdateSpinner.start()
                command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/AutoAptUpdate.py"]
                self.startAptUpdateProcess(command)

    def controlPSUpdate(self):
        if self.Server.connection and self.UserSettings.usercodename == "yirmibir" and not self.isbroken:
            user_version = self.Package.installedVersion("pardus-software")
            server_version = self.Server.appversion
            if user_version is not None and server_version != "":
                version = self.Package.versionCompare(user_version, server_version)
                if version < 0:
                    self.notify(message_summary=_("Pardus Software Center | New version available"),
                                message_body=_("Please upgrade application using Menu/Updates"))

    def controlAvailableApps(self):
        if self.Server.connection:
            self.setAvailableApps(available=self.UserSettings.config_saa, hideextapps=self.UserSettings.config_hera)

    def controlArgs(self):
        if "details" in self.Application.args.keys():
            found = False
            app = self.Application.args["details"]
            try:
                if app.endswith(".pardusapp"):
                    if os.path.isfile(app):
                        appfile = open(app, "r")
                        app = appfile.read().strip()
            except Exception as e:
                print(str(e))
            try:
                if ".desktop" in app:
                    app = "{}".format(app.split(".desktop")[0])
                for apps in self.fullapplist:
                    if app == apps["name"] or app == apps["desktop"].split(".desktop")[0] or \
                            app == apps["gnomename"].split(".desktop")[0] or \
                            any(app == e for e in apps["desktopextras"].replace(" ", "").replace(".desktop", "").split(",")):
                        found = True
                        app = apps["name"]  # if the name is coming from desktop then set it to app name
                        self.fromdetails = True
                        self.detailsappname = app
                        self.mostappname = None
                        GLib.idle_add(self.on_PardusAppsIconView_selection_changed, app)
                        if self.topbutton2.get_style_context().has_class("suggested-action"):
                            self.topbutton2.get_style_context().remove_class("suggested-action")
                        if self.queuebutton.get_style_context().has_class("suggested-action"):
                            self.queuebutton.get_style_context().remove_class("suggested-action")
                        if not self.topbutton1.get_style_context().has_class("suggested-action"):
                            self.topbutton1.get_style_context().add_class("suggested-action")
                        self.topsearchbutton.set_active(False)
            except Exception as e:
                print(str(e))
            try:
                if not found:
                    if ".desktop" in self.Application.args["details"]:
                        process = subprocess.run(["dpkg", "-S", self.Application.args["details"]], stdout=subprocess.PIPE)
                        output = process.stdout.decode("utf-8")
                        app = output[:output.find(":")].split(",")[0]
                    else:
                        app = "{}.desktop".format(self.Application.args["details"])
                        process = subprocess.run(["dpkg", "-S", app], stdout=subprocess.PIPE)
                        output = process.stdout.decode("utf-8")
                        app = output[:output.find(":")].split(",")[0]
                    if app == "":
                        app = "{}".format(self.Application.args["details"].split(".desktop")[0])

                    self.reposearchbar.set_text(app)
                    self.on_topbutton2_clicked(self.topbutton2)
                    self.on_reposearchbutton_clicked(self.reposearchbutton)
                    for row in self.searchstore:
                        if app == row[0]:
                            self.RepoAppsTreeView.set_cursor(row.path)
                            self.on_RepoAppsTreeView_row_activated(self.RepoAppsTreeView, row.path, 0)
            except Exception as e:
                print(str(e))


    def normalpage(self):
        self.mainstack.set_visible_child_name("home")
        if self.Server.connection:
            if not self.isbroken:
                self.homestack.set_visible_child_name("pardushome")
                GLib.idle_add(self.topsearchbutton.set_sensitive, True)
                GLib.idle_add(self.menu_suggestapp.set_sensitive, True)
                GLib.idle_add(self.menu_myapps.set_sensitive, True)
                GLib.idle_add(self.menu_statistics.set_sensitive, True)
            else:
                self.homestack.set_visible_child_name("fixapt")
                GLib.idle_add(self.topsearchbutton.set_sensitive, False)
                GLib.idle_add(self.menu_myapps.set_sensitive, False)
        else:
            self.homestack.set_visible_child_name("noserver")
            self.noserverlabel.set_markup(
                "<b>{}\n\n{}</b>".format(_("Could not connect to server."), self.Server.error_message))
            GLib.idle_add(self.topsearchbutton.set_sensitive, False)
            GLib.idle_add(self.menu_suggestapp.set_sensitive, False)
            GLib.idle_add(self.menu_myapps.set_sensitive, False)
            GLib.idle_add(self.menu_statistics.set_sensitive, False)

        self.splashspinner.stop()
        self.splashlabel.set_text("")

        GLib.idle_add(self.HeaderBarMenuButton.set_sensitive, True)
        GLib.idle_add(self.topbutton1.set_sensitive, True)
        GLib.idle_add(self.topbutton2.set_sensitive, True)

        if self.Server.connection and self.isbroken:
            GLib.idle_add(self.topbutton1.set_sensitive, False)
            GLib.idle_add(self.topbutton2.set_sensitive, False)

        print("page setted to normal")

    def package(self):
        # self.splashspinner.start()
        # self.splashbar.pulse()
        GLib.idle_add(self.splashlabel.set_markup, "<b>{}</b>".format(_("Updating Cache")))
        self.Package = Package()
        if self.Package.updatecache():
            self.isbroken = False
            self.Package.getApps()
        else:
            self.isbroken = True
            print("Error while updating Cache")

        print("package completed")

    def usersettings(self):
        self.UserSettings = UserSettings()
        self.UserSettings.createDefaultConfig()
        self.UserSettings.readConfig()

        print("{} {}".format("config_usi", self.UserSettings.config_usi))
        print("{} {}".format("config_anim", self.UserSettings.config_ea))
        print("{} {}".format("config_availableapps", self.UserSettings.config_saa))
        print("{} {}".format("config_hideextapps", self.UserSettings.config_hera))
        print("{} {}".format("config_icon", self.UserSettings.config_icon))
        print("{} {}".format("config_showgnomecommments", self.UserSettings.config_sgc))
        print("{} {}".format("config_usedarktheme", self.UserSettings.config_udt))
        print("{} {}".format("config_aptup", self.UserSettings.config_aptup))
        print("{} {}".format("config_lastaptup", self.UserSettings.config_lastaptup))
        print("{} {}".format("config_forceaptuptime", self.UserSettings.config_forceaptuptime))

    def on_dEventBox1_button_press_event(self, widget, event):
        self.imgfullscreen_count = 0
        self.setPopImage(1)
        self.resizePopImage()
        self.ImagePopover.show_all()
        self.ImagePopover.popup()
        self.fullscreen_image.set_from_icon_name("view-fullscreen-symbolic", Gtk.IconSize.BUTTON)

    def on_dEventBox2_button_press_event(self, widget, event):
        self.imgfullscreen_count = 0
        self.setPopImage(2)
        self.resizePopImage()
        self.ImagePopover.show_all()
        self.ImagePopover.popup()
        self.fullscreen_image.set_from_icon_name("view-fullscreen-symbolic", Gtk.IconSize.BUTTON)

    def on_imgBackButton_clicked(self, button):
        if self.ImagePopoverStack.get_visible_child_name() != "image1":
            self.setPopImage(1)
        else:
            self.setPopImage(2)

    def on_imgNextButton_clicked(self, button):
        if self.ImagePopoverStack.get_visible_child_name() != "image2":
            self.setPopImage(2)
        else:
            self.setPopImage(1)

    def on_imgCloseButton_clicked(self, button):
        self.ImagePopover.popdown()

    def on_imgWebButton_clicked(self, button):
        image = "{}{}".format(self.Server.serverurl, self.screenshots[self.down_image])
        subprocess.Popen(["xdg-open", image])

    def on_imgDownloadButton_clicked(self, button):
        filesave_chooser = Gtk.FileChooserDialog(title=_("Save File"), parent=self.MainWindow,
                                                 action=Gtk.FileChooserAction.SAVE)
        filesave_chooser.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
        filesave_chooser.add_button(_("Save"), Gtk.ResponseType.ACCEPT).get_style_context().add_class(
            "suggested-action")

        filesave_chooser.set_current_name("{}_{}.png".format(
            os.path.splitext(os.path.basename(self.screenshots[self.down_image]))[0],
            datetime.now().strftime("%Y-%m-%d_%H-%M-%S")))

        response = filesave_chooser.run()
        if response == Gtk.ResponseType.ACCEPT:
            file_path = filesave_chooser.get_filename()
            if self.down_image == 0:
                self.pixbuf1.savev(file_path, "png", [], [])
            elif self.down_image == 1:
                self.pixbuf2.savev(file_path, "png", [], [])
        filesave_chooser.destroy()

    def on_imgFullButton_clicked(self, button):
        self.imgfullscreen_count += 1
        if self.imgfullscreen_count % 2 == 1:
            self.imgfullscreen = True
            self.resizePopImage(True)
            self.fullscreen_image.set_from_icon_name("view-restore-symbolic", Gtk.IconSize.BUTTON)
        else:
            self.imgfullscreen = False
            self.resizePopImage()
            self.fullscreen_image.set_from_icon_name("view-fullscreen-symbolic", Gtk.IconSize.BUTTON)

    def on_ImagePopover_key_press_event(self, widget, event):

        if event.keyval == Gdk.KEY_Left:
            if self.ImagePopoverStack.get_visible_child_name() != "image1":
                self.setPopImage(1)
            else:
                self.setPopImage(2)
            return True
        elif event.keyval == Gdk.KEY_Right:
            if self.ImagePopoverStack.get_visible_child_name() != "image2":
                self.setPopImage(2)
            else:
                self.setPopImage(1)
            return True
        elif event.keyval == Gdk.KEY_f or event.keyval == Gdk.KEY_F:
            self.imgfullscreen_count += 1
            if self.imgfullscreen_count % 2 == 1:
                self.imgfullscreen = True
                self.resizePopImage(True)
                self.fullscreen_image.set_from_icon_name("view-restore-symbolic", Gtk.IconSize.BUTTON)
                return True
            else:
                self.imgfullscreen = False
                self.resizePopImage()
                self.fullscreen_image.set_from_icon_name("view-fullscreen-symbolic", Gtk.IconSize.BUTTON)
                return True

    def setPopImage(self, image):
        if image == 1:
            self.imgLabel.set_text("{} 1".format(_("Image")))
            self.ImagePopoverStack.set_visible_child_name("image1")
        elif image == 2:
            self.imgLabel.set_text("{} 2".format(_("Image")))
            self.ImagePopoverStack.set_visible_child_name("image2")
        if type(image) is int:
            self.down_image = image - 1
        else:
            self.down_image = 0

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
        # print("Repo apps setting")
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

        if not self.repoappsinit:
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

            self.repoappsinit = True

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
        GLib.idle_add(self.splashlabel.set_markup, "<b>{}</b>".format(_("Getting applications from server")))
        # self.splashlabel.set_markup()
        self.Server = Server()

        # set server url from config
        try:
            self.Server.serverurl = open("/etc/pardus/pardus-software.conf", "r").read().strip()
        except Exception as e:
            print("Error getting server url from conf so setting to https://apps.pardus.org.tr")
            print("{}".format(e))
            self.Server.serverurl = "https://apps.pardus.org.tr"

        self.Server.ServerAppsCB = self.ServerAppsCB
        self.Server.ServerIconsCB = self.ServerIconsCB
        self.Server.get(self.Server.serverurl + self.Server.serverapps, "apps")
        self.Server.get(self.Server.serverurl + self.Server.servercats, "cats")
        self.Server.get(self.Server.serverurl + self.Server.serverhomepage, "home")
        self.Server.get(self.Server.serverurl + self.Server.serverstatistics, "statistics")

        # self.applist = sorted(self.Server.applist, key=lambda x: x["prettyname"][self.locale])
        # self.fullapplist = self.applist
        # self.catlist = self.Server.catlist
        # self.Server.applist.clear()

        # self.serverappicons = self.Server.getAppIcons()
        # self.servercaticons = self.Server.getCategoryIcons()
        print("server func done")

    def afterServers(self):
        self.normalpage()
        GLib.idle_add(self.controlServer)
        GLib.idle_add(self.controlAvailableApps)
        GLib.idle_add(self.setPardusCategories)
        GLib.idle_add(self.setPardusApps)
        GLib.idle_add(self.setEditorApps)
        GLib.idle_add(self.setMostApps)
        GLib.idle_add(self.setRepoApps)
        GLib.idle_add(self.gnomeRatings)
        GLib.idle_add(self.controlArgs)
        GLib.idle_add(self.controlPSUpdate)
        GLib.idle_add(self.aptUpdate)

    def ServerAppsCB(self, success, response=None, type=None):
        if success:
            if type == "apps":
                print("server apps successful")
                self.status_serverapps = True
                self.applist = sorted(response["app-list"], key=lambda x: locale.strxfrm(x["prettyname"][self.locale]))
                self.fullapplist = self.applist
            elif type == "cats":
                print("server cats successful")
                self.status_servercats = True
                self.catlist = response["cat-list"]
                self.fullcatlist = self.catlist
            elif type == "home":
                print("server home successful")
                self.status_serverhome = True
                self.Server.ediapplist = response["editor-apps"]
                self.Server.mostdownapplist = response["mostdown-apps"]
                self.Server.mostrateapplist = response["mostrate-apps"]
                if "last-apps" in response:
                    self.Server.lastaddedapplist = response["last-apps"]
                self.Server.totalstatistics = response["total"]
                self.Server.servermd5 = response["md5"]
                self.Server.appversion = response["version"]
                self.Server.iconnames = response["iconnames"]
                self.Server.badwords = response["badwords"]
                self.Server.aptuptime = response["aptuptime"]
            elif type == "statistics":
                print("server statistics successful")
                self.status_serverstatistics = True
                self.Server.dailydowns = response["dailydowns"]
                self.Server.osdowns = response["osdowns"]
                self.Server.appdowns = response["appdowns"]
                self.Server.oscolors = response["oscolors"]
                self.Server.appcolors = response["appcolors"]

            if self.status_serverapps and self.status_servercats and self.status_serverhome and self.status_serverstatistics:
                self.Server.connection = True
                self.getIcons()
        else:
            self.Server.connection = False
            self.afterServers()

    def ServerIconsCB(self, status, type, fromsettings=False):

        if not fromsettings:
            if type == self.Server.serverappicons:
                self.serverappicons_done = True
                if not status:
                    self.notify(message_summary=_("Couldn't get icons"),
                                message_body=_("Application icons could not be retrieved from the server"))
            elif type == self.Server.servercaticons:
                self.servercaticons_done = True
                if not status:
                    self.notify(message_summary=_("Couldn't get icons"),
                                message_body=_("Category icons could not be retrieved from the server"))
            if self.serverappicons_done and self.servercaticons_done:
                self.afterServers()
        else:
            print("fromsettings, {} re-setting".format(type))
            self.usersettings()
            if type == self.Server.serverappicons:
                GLib.idle_add(self.PardusAppListStore.clear)
                self.EditorListStore.clear()
                for row in self.MostDownFlowBox:
                    self.MostDownFlowBox.remove(row)
                for row in self.MostRateFlowBox:
                    self.MostRateFlowBox.remove(row)
                for row in self.LastAddedFlowBox:
                    self.LastAddedFlowBox.remove(row)
                self.setPardusApps()
                self.setEditorApps()
                self.setMostApps()
            elif type == self.Server.servercaticons:
                for row in self.HomeCategoryFlowBox:
                    self.HomeCategoryFlowBox.remove(row)
                self.setPardusCategories()
            self.setSelectIcons()

    def getIcons(self):
        if self.Server.connection:
            print("Getting icons from server")
            GLib.idle_add(self.splashlabel.set_markup, "<b>{}</b>".format(_("Getting icons from server")))
            redown_app_icons, redown_cat_icons = self.Server.controlIcons()
            if redown_app_icons:
                self.Server.getIcons(
                    self.Server.serverurl + self.Server.serverfiles + self.Server.serverappicons + self.Server.serverarchive,
                    self.Server.serverappicons, force_download=True)
            else:
                self.Server.getIcons(
                    self.Server.serverurl + self.Server.serverfiles + self.Server.serverappicons + self.Server.serverarchive,
                    self.Server.serverappicons)
            if redown_cat_icons:
                self.Server.getIcons(
                    self.Server.serverurl + self.Server.serverfiles + self.Server.servercaticons + self.Server.serverarchive,
                    self.Server.servercaticons, force_download=True)
            else:
                self.Server.getIcons(
                    self.Server.serverurl + self.Server.serverfiles + self.Server.servercaticons + self.Server.serverarchive,
                    self.Server.servercaticons)
        else:
            print("icons cannot downloading because server connection is {}".format(self.Server.connection))

    def controlServer(self):
        if self.Server.connection:
            print("Controlling {}".format(self.Server.serverurl))
            self.AppDetail.control(self.Server.serverurl + "/api/v2/test")
            self.AppRequest.control(self.Server.serverurl + "/api/v2/test")
            self.PardusComment.control(self.Server.serverurl + "/api/v2/test")

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
        else:
            self.gnomeratings = []
            print("gnomeratings not successful")

    def setPardusApps(self):
        if self.Server.connection:
            for app in self.applist:
                if self.UserSettings.config_usi:
                    appicon = self.getServerAppIcon(app["name"])
                else:
                    appicon = self.getSystemAppIcon(app["name"])
                appname = app['name']
                prettyname = app["prettyname"][self.locale]
                if prettyname == "" or prettyname is None:
                    prettyname = app["prettyname"]["en"]
                category = ""
                for i in app["category"]:
                    category += i[self.locale] + ","
                category = category.rstrip(",")
                categorynumber = self.get_category_number(category)
                subcategory = ""
                if "subcategory" in app.keys():
                    for i in app["subcategory"]:
                        subcategory += i[self.locale].lower() + ","
                    subcategory = subcategory.rstrip(",")
                GLib.idle_add(self.addToPardusApps, [appicon, appname, categorynumber, prettyname, category, subcategory])

    def addToPardusApps(self, list):
        self.PardusAppListStore.append(list)

    def setPardusCategories(self):
        if self.Server.connection:
            self.catbuttons = []
            self.categories = []
            for cat in self.catlist:
                self.categories.append({"name": cat[self.locale], "icon": cat["en"], "external": cat["external"],
                                        "subcats": cat["subcats"],
                                        "subcategories": cat["subcategories"] if "subcategories" in cat.keys() else []})
            self.categories = sorted(self.categories, key=lambda x: x["name"])
            if self.locale == "tr":
                self.categories.insert(0, {"name": "tümü", "icon": "all", "external": False, "subcats": False,
                                           "subcategories": []})
            else:
                self.categories.insert(0, {"name": "all", "icon": "all", "external": False, "subcats": False,
                                           "subcategories": []})

            for cat in self.categories:
                caticon = Gtk.Image.new()
                if self.UserSettings.config_usi:
                    caticon.set_from_pixbuf(self.getServerCatIcon(cat["icon"]))
                else:
                    caticon.set_from_pixbuf(self.getSystemCatIcon(cat["icon"]))
                label = Gtk.Label.new()
                label_text = str(cat["name"]).title()
                label.set_text(" " + label_text)
                box1 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
                box1.pack_start(caticon, False, True, 0)
                box1.pack_start(label, False, True, 0)
                box1.set_name("homecats")
                button = Gtk.Button.new()
                button.add(box1)
                button.set_relief(Gtk.ReliefStyle.NONE)
                button.connect('clicked', self.on_catbutton_clicked)
                button.name = cat["name"]
                self.catbuttons.append(button)
                GLib.idle_add(self.HomeCategoryFlowBox.insert, button, GLib.PRIORITY_DEFAULT_IDLE)

            GLib.idle_add(self.HomeCategoryFlowBox.show_all)

    def on_catbutton_clicked(self, button):

        print("on_catbutton_clicked")
        if self.pardusicb.get_active() and self.myapps_clicked:
            self.pardusicb.set_active(False)
            self.myapps_clicked = False

        if self.mda_clicked and self.sortPardusAppsCombo.get_active() == 1:
            self.sortPardusAppsCombo.set_active(0)
            self.mda_clicked = False

        if self.mra_clicked and self.sortPardusAppsCombo.get_active() == 2:
            self.sortPardusAppsCombo.set_active(0)
            self.mra_clicked = False

        if self.la_clicked and self.sortPardusAppsCombo.get_active() == 3:
            self.sortPardusAppsCombo.set_active(0)
            self.la_clicked = False

        self.isPardusSearching = False
        self.menubackbutton.set_sensitive(True)
        self.PardusCurrentCategory = -2
        self.PardusCurrentCategoryString, self.PardusCurrentCategoryIcon, self.PardusCurrentCategorySubCats, \
        self.PardusCurrentCategoryExternal, self.PardusCurrentCategorySubCategories = self.get_category_name_from_button(button.name)

        print("HomeCategory: {} {} {} {} {}".format(self.PardusCurrentCategory, self.PardusCurrentCategoryString,
                                                 self.PardusCurrentCategorySubCats, self.PardusCurrentCategoryExternal,
                                                    self.PardusCurrentCategorySubCategories))
        if self.UserSettings.config_usi:
            pixbuf = self.getServerCatIcon(self.PardusCurrentCategoryIcon, 32)
        else:
            pixbuf = self.getSystemCatIcon(self.PardusCurrentCategoryIcon, 32)
        self.NavCategoryImage.set_from_pixbuf(pixbuf)
        self.NavCategoryLabel.set_text(self.PardusCurrentCategoryString.title())
        self.homestack.set_visible_child_name("pardusapps")

        self.SubCatCombo.remove_all()
        if self.PardusCurrentCategorySubCategories:
            self.SubCatCombo.append_text(_("All"))
            self.SubCatCombo.set_active(0)
            self.SubCatCombo.set_visible(True)
            for subcat in self.PardusCurrentCategorySubCategories:
                self.SubCatCombo.append_text("{}".format(subcat[self.locale].title()))
        else:
            self.SubCatCombo.set_visible(False)

        if self.PardusCurrentCategorySubCats and self.PardusCurrentCategoryExternal:
            self.pardusicb.set_visible(False)
            self.sortPardusAppsCombo.set_visible(False)
            self.pardusAppsStack.set_visible_child_name("subcats")
            for row in self.SubCategoryFlowBox:
                self.SubCategoryFlowBox.remove(row)
            subcats = []
            for i in self.applist:
                if i["external"]:
                    for cat in i["category"]:
                        if cat[self.locale] == self.PardusCurrentCategoryString:
                            subcats.append(
                                {"en": i["external"]["repoprettyen"], "tr": i["external"]["repoprettytr"],
                                 "reponame": i["external"]["reponame"]})
            subcats = list({u['reponame']: u for u in subcats}.values())
            for sub in subcats:
                caticon = Gtk.Image.new()
                caticon.set_from_pixbuf(self.getServerCatIcon(sub["reponame"]))
                label = Gtk.Label.new()
                label_text = str(sub[self.locale]).title()
                label.set_text(" " + label_text)
                box1 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
                box1.pack_start(caticon, False, True, 0)
                box1.pack_start(label, False, True, 0)
                box1.name = sub["reponame"]
                GLib.idle_add(self.SubCategoryFlowBox.insert, box1, GLib.PRIORITY_DEFAULT_IDLE)
            GLib.idle_add(self.SubCategoryFlowBox.show_all)
        else:
            self.pardusicb.set_visible(True)
            self.sortPardusAppsCombo.set_visible(True)
            self.pardusAppsStack.set_visible_child_name("normal")
            self.PardusCategoryFilter.refilter()

    def setEditorApps(self):
        if self.Server.connection:
            print("setting editor apps")
            for ediapp in self.Server.ediapplist:
                if self.UserSettings.config_usi:
                    edipixbuf = self.getServerAppIcon(ediapp['name'])
                else:
                    edipixbuf = self.getSystemAppIcon(ediapp['name'])
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
            print("setting mostapps")
            for mda in self.Server.mostdownapplist:
                icon = Gtk.Image.new()
                if self.UserSettings.config_usi:
                    icon.set_from_pixbuf(self.getServerAppIcon(mda["name"], 64))
                else:
                    icon.set_from_pixbuf(self.getSystemAppIcon(mda["name"], 64))

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

                listbox = Gtk.ListBox.new()
                listbox.set_selection_mode(Gtk.SelectionMode.NONE)
                listbox.get_style_context().add_class("pardus-software-listbox")
                listbox.add(box)

                frame = Gtk.Frame.new()
                frame.get_style_context().add_class("pardus-software-frame")
                frame.add(listbox)

                self.MostDownFlowBox.get_style_context().add_class("pardus-software-flowbox")

                GLib.idle_add(self.MostDownFlowBox.insert, frame, GLib.PRIORITY_DEFAULT_IDLE)

            for mra in self.Server.mostrateapplist:
                icon = Gtk.Image.new()
                if self.UserSettings.config_usi:
                    icon.set_from_pixbuf(self.getServerAppIcon(mra["name"], 64))
                else:
                    icon.set_from_pixbuf(self.getSystemAppIcon(mra["name"], 64))

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

                listbox = Gtk.ListBox.new()
                listbox.set_selection_mode(Gtk.SelectionMode.NONE)
                listbox.get_style_context().add_class("pardus-software-listbox")
                listbox.add(box)

                frame = Gtk.Frame.new()
                frame.get_style_context().add_class("pardus-software-frame")
                frame.add(listbox)

                self.MostRateFlowBox.get_style_context().add_class("pardus-software-flowbox")
                GLib.idle_add(self.MostRateFlowBox.insert, frame, GLib.PRIORITY_DEFAULT_IDLE)

            for la in self.Server.lastaddedapplist:
                icon = Gtk.Image.new()
                if self.UserSettings.config_usi:
                    icon.set_from_pixbuf(self.getServerAppIcon(la["name"], 64))
                else:
                    icon.set_from_pixbuf(self.getSystemAppIcon(la["name"], 64))

                label = Gtk.Label.new()
                label.set_text(str(self.getPrettyName(la["name"])))
                label.set_line_wrap(True)
                label.set_max_width_chars(10)
                label.name = la["name"]

                downicon = Gtk.Image.new_from_icon_name("document-save-symbolic", Gtk.IconSize.BUTTON)

                downlabel = Gtk.Label.new()
                downlabel.set_markup("<small>{}</small>".format(la["download"]))

                rateicon = Gtk.Image.new_from_icon_name("star-new-symbolic", Gtk.IconSize.BUTTON)

                ratelabel = Gtk.Label.new()
                ratelabel.set_markup("<small>{:.1f}</small>".format(float(la["rate"])))

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

                listbox = Gtk.ListBox.new()
                listbox.set_selection_mode(Gtk.SelectionMode.NONE)
                listbox.get_style_context().add_class("pardus-software-listbox")
                listbox.add(box)

                frame = Gtk.Frame.new()
                frame.get_style_context().add_class("pardus-software-frame")
                frame.add(listbox)

                self.LastAddedFlowBox.get_style_context().add_class("pardus-software-flowbox")
                GLib.idle_add(self.LastAddedFlowBox.insert, frame, GLib.PRIORITY_DEFAULT_IDLE)

            self.hometotaldc.set_markup("<small>{}</small>".format(self.Server.totalstatistics[0]["downcount"]))
            self.hometotalrc.set_markup("<small>{}</small>".format(self.Server.totalstatistics[0]["ratecount"]))

        GLib.idle_add(self.MostDownFlowBox.show_all)
        GLib.idle_add(self.MostRateFlowBox.show_all)
        GLib.idle_add(self.LastAddedFlowBox.show_all)

    def getPrettyName(self, name, split=True):
        prettyname = name
        # look full list of apps
        for i in self.fullapplist:
            if i["name"] == name:
                prettyname = i["prettyname"][self.locale]
                if prettyname == "" or prettyname is None:
                    prettyname = i["prettyname"]["en"]
        if split:
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
            if self.UserSettings.config_icon == "default":
                icons = "categoryicons"
            else:
                icons = "categoryicons-" + self.UserSettings.config_icon
        except Exception as e:
            icons = "categoryicons"
            print("{}".format(e))
        try:
            caticon = GdkPixbuf.Pixbuf.new_from_file_at_size(
                self.Server.cachedir + icons + "/" + cat + ".svg", size, size)
        except:
            # print("{} {}".format(cat, "icon not found in server cat icons"))
            try:
                caticon = GdkPixbuf.Pixbuf.new_from_file_at_size(
                    self.Server.cachedir + "categoryicons/" + cat + ".svg", size, size)
            except:
                try:
                    caticon = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", size, Gtk.IconLookupFlags(16))
                except:
                    caticon = Gtk.IconTheme.get_default().load_icon("image-missing", size, Gtk.IconLookupFlags(16))
        return caticon

    def getSystemAppIcon(self, app, size=64, notify=False, myappicon=False):
        try:
            appicon = Gtk.IconTheme.get_default().load_icon(app, size, Gtk.IconLookupFlags(16))
        except:
            try:
                appicon = self.parduspixbuf.load_icon(app, size, Gtk.IconLookupFlags(16))
            except:
                if notify:
                    try:
                        appicon = Gtk.IconTheme.get_default().load_icon("pardus-software", size,
                                                                        Gtk.IconLookupFlags(16))
                    except:
                        try:
                            appicon = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", size,
                                                                            Gtk.IconLookupFlags(16))
                        except:
                            appicon = Gtk.IconTheme.get_default().load_icon("image-missing", size,
                                                                            Gtk.IconLookupFlags(16))
                else:
                    if myappicon:
                        appicon = self.getMyAppIcon(app, size)
                    else:
                        try:
                            appicon = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", size,
                                                                            Gtk.IconLookupFlags(16))
                        except:
                            appicon = Gtk.IconTheme.get_default().load_icon("image-missing", size,
                                                                            Gtk.IconLookupFlags(16))
        return appicon

    def getServerAppIcon(self, app, size=64, notify=False, myappicon=False):
        try:
            if self.UserSettings.config_icon == "default":
                icons = "appicons"
            else:
                icons = "appicons-" + self.UserSettings.config_icon
        except Exception as e:
            icons = "appicons"
            print("{}".format(e))
        try:
            appicon = GdkPixbuf.Pixbuf.new_from_file_at_size(self.Server.cachedir + icons + "/" + app + ".svg", size,
                                                             size)
        except:
            # print("{} {}".format(app, "icon not found in server app icons"))
            try:
                appicon = GdkPixbuf.Pixbuf.new_from_file_at_size(self.Server.cachedir + "appicons/" + app + ".svg",
                                                                 size, size)
            except:
                if notify:
                    try:
                        appicon = GdkPixbuf.Pixbuf.new_from_file_at_size(
                            self.Server.cachedir + "appicons/pardus-software.svg", size, size)
                    except:
                        try:
                            appicon = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", size,
                                                                            Gtk.IconLookupFlags(16))
                        except:
                            appicon = Gtk.IconTheme.get_default().load_icon("image-missing", size,
                                                                            Gtk.IconLookupFlags(16))
                else:
                    if myappicon:
                        appicon = self.getMyAppIcon(app, size)
                        print(appicon)
                    else:
                        try:
                            appicon = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", size,
                                                                            Gtk.IconLookupFlags(16))
                        except:
                            appicon = Gtk.IconTheme.get_default().load_icon("image-missing", size,
                                                                            Gtk.IconLookupFlags(16))
        return appicon

    def getMyAppIcon(self, app, size=64):
        try:
            if self.UserSettings.config_icon == "default":
                icons = "appicons"
            else:
                icons = "appicons-" + self.UserSettings.config_icon
        except Exception as e:
            icons = "appicons"
            print("{}".format(e))
        try:
            appicon = GdkPixbuf.Pixbuf.new_from_file_at_size(self.Server.cachedir + icons + "/" + app + ".svg", size,
                                                             size)
        except:
            try:
                appicon = GdkPixbuf.Pixbuf.new_from_file_at_size(self.Server.cachedir + "appicons/" + app + ".svg",
                                                                 size, size)
            except:
                try:
                    appicon = Gtk.IconTheme.get_default().load_icon(app, size, Gtk.IconLookupFlags(16))
                except:
                    try:
                        appicon = self.parduspixbuf.load_icon(app, size, Gtk.IconLookupFlags(16))
                    except:
                        try:
                            appicon = GdkPixbuf.Pixbuf.new_from_file_at_size(app, size, size)
                        except:
                            try:
                                appicon = GdkPixbuf.Pixbuf.new_from_file_at_size(
                                    self.Server.cachedir + "appicons/pardus-software.svg", size, size)
                            except:
                                try:
                                    appicon = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", size,
                                                                                    Gtk.IconLookupFlags(16))
                                except:
                                    appicon = Gtk.IconTheme.get_default().load_icon("image-missing", size,
                                                                                    Gtk.IconLookupFlags(16))

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
                return self.categories[i]["name"], self.categories[i]["icon"], self.categories[i]["subcats"], \
                       self.categories[i]["external"], self.categories[i]["subcategories"]

    def get_category_name_from_button(self, name):
        lencat = len(self.categories)
        for i in range(0, lencat):
            if name == self.categories[i]["name"]:
                return self.categories[i]["name"], self.categories[i]["icon"], self.categories[i]["subcats"], \
                       self.categories[i]["external"], self.categories[i]["subcategories"]

    def get_repo_category_number(self, thatcategory):
        repocatnumber = 404
        for i in self.Package.sections:
            if thatcategory == i["name"]:
                repocatnumber = i["number"]
        return repocatnumber

    def onDestroy(self, widget):
        self.MainWindow.destroy()

    def setAnimations(self):
        if self.UserSettings.config_ea:
            self.mainstack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
            self.mainstack.set_transition_duration(200)

            self.homestack.set_transition_type(Gtk.StackTransitionType.SLIDE_UP_DOWN)
            self.homestack.set_transition_duration(200)

            self.pardusAppsStack.set_transition_type(Gtk.StackTransitionType.SLIDE_UP_DOWN)
            self.pardusAppsStack.set_transition_duration(200)

            self.searchstack.set_transition_type(Gtk.StackTransitionType.SLIDE_UP)
            self.searchstack.set_transition_duration(200)

            self.rbotstack.set_transition_type(Gtk.StackTransitionType.SLIDE_UP)
            self.rbotstack.set_transition_duration(200)

            self.commentstack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
            self.commentstack.set_transition_duration(200)

            self.gcStack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
            self.gcStack.set_transition_duration(200)

            self.appimage1stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
            self.appimage1stack.set_transition_duration(200)

            self.appimage2stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
            self.appimage2stack.set_transition_duration(200)

            self.activatestack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
            self.activatestack.set_transition_duration(200)

            self.updatestack.set_transition_type(Gtk.StackTransitionType.SLIDE_UP)
            self.updatestack.set_transition_duration(200)

            self.tryfixstack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
            self.tryfixstack.set_transition_duration(200)

            self.statstack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
            self.statstack.set_transition_duration(200)

            self.SuggestStack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
            self.SuggestStack.set_transition_duration(200)

            self.prefstack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
            self.prefstack.set_transition_duration(200)

            self.ImagePopoverStack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
            self.ImagePopoverStack.set_transition_duration(200)

            self.bottomrevealer.set_transition_type(Gtk.StackTransitionType.SLIDE_UP)
            self.bottomrevealer.set_transition_duration(200)

            self.toprevealer.set_transition_type(Gtk.StackTransitionType.SLIDE_DOWN)
            self.toprevealer.set_transition_duration(200)

            self.PopoverMenu.set_transitions_enabled(True)
            self.DisclaimerPopover.set_transitions_enabled(True)
            self.ImagePopover.set_transitions_enabled(True)
            self.licensePopover.set_transitions_enabled(True)
            self.PopoverPrefTip.set_transitions_enabled(True)

        else:
            self.mainstack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.mainstack.set_transition_duration(0)

            self.homestack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.homestack.set_transition_duration(0)

            self.pardusAppsStack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.pardusAppsStack.set_transition_duration(0)

            self.searchstack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.searchstack.set_transition_duration(0)

            self.rbotstack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.rbotstack.set_transition_duration(0)

            self.commentstack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.commentstack.set_transition_duration(0)

            self.gcStack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.gcStack.set_transition_duration(0)

            self.appimage1stack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.appimage1stack.set_transition_duration(0)

            self.appimage2stack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.appimage2stack.set_transition_duration(0)

            self.activatestack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.activatestack.set_transition_duration(0)

            self.updatestack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.updatestack.set_transition_duration(0)

            self.tryfixstack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.tryfixstack.set_transition_duration(0)

            self.statstack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.statstack.set_transition_duration(0)

            self.SuggestStack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.SuggestStack.set_transition_duration(0)

            self.prefstack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.prefstack.set_transition_duration(0)

            self.ImagePopoverStack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.ImagePopoverStack.set_transition_duration(0)

            self.bottomrevealer.set_transition_type(Gtk.StackTransitionType.NONE)
            self.bottomrevealer.set_transition_duration(0)

            self.toprevealer.set_transition_type(Gtk.StackTransitionType.NONE)
            self.toprevealer.set_transition_duration(0)

            self.PopoverMenu.set_transitions_enabled(False)
            self.DisclaimerPopover.set_transitions_enabled(False)
            self.ImagePopover.set_transitions_enabled(False)
            self.licensePopover.set_transitions_enabled(False)
            self.PopoverPrefTip.set_transitions_enabled(False)

    def on_menubackbutton_clicked(self, widget):
        print("menuback")
        hsname = self.homestack.get_visible_child_name()
        if hsname == "pardusapps":

            if self.topbutton2.get_style_context().has_class("suggested-action"):
                self.topbutton2.get_style_context().remove_class("suggested-action")
            if self.queuebutton.get_style_context().has_class("suggested-action"):
                self.queuebutton.get_style_context().remove_class("suggested-action")
            if not self.topbutton1.get_style_context().has_class("suggested-action"):
                self.topbutton1.get_style_context().add_class("suggested-action")

            self.searchstack.set_visible_child_name("pardus")

            if self.PardusCurrentCategorySubCats:
                self.SubCategoryFlowBox.unselect_all()
                if self.pardusAppsStack.get_visible_child_name() != "subcats":
                    self.pardusAppsStack.set_visible_child_name("subcats")
                    self.pardusicb.set_visible(False)
                    self.sortPardusAppsCombo.set_visible(False)
                else:
                    self.homestack.set_visible_child_name("pardushome")
                    self.EditorAppsIconView.unselect_all()
                    self.menubackbutton.set_sensitive(False)
            else:
                self.homestack.set_visible_child_name("pardushome")
                self.EditorAppsIconView.unselect_all()
                self.menubackbutton.set_sensitive(False)

        elif hsname == "pardusappsdetail":

            self.searchstack.set_visible_child_name("pardus")

            if self.topbutton2.get_style_context().has_class("suggested-action"):
                self.topbutton2.get_style_context().remove_class("suggested-action")
            if self.queuebutton.get_style_context().has_class("suggested-action"):
                self.queuebutton.get_style_context().remove_class("suggested-action")
            if not self.topbutton1.get_style_context().has_class("suggested-action"):
                self.topbutton1.get_style_context().add_class("suggested-action")

            if self.fromeditorapps or self.frommostapps:
                self.homestack.set_visible_child_name("pardushome")
                self.EditorAppsIconView.unselect_all()
                self.menubackbutton.set_sensitive(False)
            else:
                self.homestack.set_visible_child_name("pardusapps")
                self.PardusAppsIconView.unselect_all()

        elif hsname == "preferences" or hsname == "repohome" or hsname == "updates" or hsname == "suggestapp" or hsname == "queue" or hsname == "statistics":

            self.homestack.set_visible_child_name(self.prefback)

            self.topsearchbutton.set_active(self.statusoftopsearch)
            if not self.isbroken:
                self.topsearchbutton.set_sensitive(True)

            hsname1 = self.homestack.get_visible_child_name()

            if hsname1 == hsname:
                self.menubackbutton.set_sensitive(False)
            else:
                if hsname1 == "pardushome":
                    self.searchstack.set_visible_child_name("pardus")
                    self.menubackbutton.set_sensitive(False)
                    if self.topbutton2.get_style_context().has_class("suggested-action"):
                        self.topbutton2.get_style_context().remove_class("suggested-action")
                    if self.queuebutton.get_style_context().has_class("suggested-action"):
                        self.queuebutton.get_style_context().remove_class("suggested-action")
                    if not self.topbutton1.get_style_context().has_class("suggested-action"):
                        self.topbutton1.get_style_context().add_class("suggested-action")
                elif hsname1 == "repohome":
                    self.searchstack.set_visible_child_name("repo")
                    self.menubackbutton.set_sensitive(False)
                    if self.topbutton1.get_style_context().has_class("suggested-action"):
                        self.topbutton1.get_style_context().remove_class("suggested-action")
                    if self.queuebutton.get_style_context().has_class("suggested-action"):
                        self.queuebutton.get_style_context().remove_class("suggested-action")
                    if not self.topbutton2.get_style_context().has_class("suggested-action"):
                        self.topbutton2.get_style_context().add_class("suggested-action")
                elif hsname1 == "pardusappsdetail" or hsname1 == "pardusapps":
                    self.searchstack.set_visible_child_name("pardus")
                    if self.topbutton2.get_style_context().has_class("suggested-action"):
                        self.topbutton2.get_style_context().remove_class("suggested-action")
                    if self.queuebutton.get_style_context().has_class("suggested-action"):
                        self.queuebutton.get_style_context().remove_class("suggested-action")
                    if not self.topbutton1.get_style_context().has_class("suggested-action"):
                        self.topbutton1.get_style_context().add_class("suggested-action")
                elif hsname1 == "noserver":
                    self.topsearchbutton.set_sensitive(False)
                    self.menubackbutton.set_sensitive(False)
                    if self.topbutton2.get_style_context().has_class("suggested-action"):
                        self.topbutton2.get_style_context().remove_class("suggested-action")
                    if self.queuebutton.get_style_context().has_class("suggested-action"):
                        self.queuebutton.get_style_context().remove_class("suggested-action")
                    if not self.topbutton1.get_style_context().has_class("suggested-action"):
                        self.topbutton1.get_style_context().add_class("suggested-action")
                elif hsname1 == "queue":
                    if self.topbutton1.get_style_context().has_class("suggested-action"):
                        self.topbutton1.get_style_context().remove_class("suggested-action")
                    if self.topbutton2.get_style_context().has_class("suggested-action"):
                        self.topbutton2.get_style_context().remove_class("suggested-action")
                    if not self.queuebutton.get_style_context().has_class("suggested-action"):
                        self.queuebutton.get_style_context().add_class("suggested-action")
                elif hsname1 == "preferences" or hsname1 == "fixapt":
                    self.menubackbutton.set_sensitive(False)

    def on_PardusAppsIconView_selection_changed(self, iconview):
        self.fromrepoapps = False
        self.external = []
        self.fromexternal = False
        self.activatestack.set_visible_child_name("main")
        mode = 0
        prettyname = ""
        try:
            # detection of IconViews (PardusAppsIconView or EditorAppsIconView)
            iconview.get_model().get_name()
            self.fromeditorapps = True
        except:
            self.fromeditorapps = False
            # PardusAppsIconView TreeModelFilter has no attribute 'get_name'
            mode = 1

        self.menubackbutton.set_sensitive(True)
        self.par_desc_more.set_visible(False)
        self.setWpcStar(0)
        self.wpcstar = 0
        self.wpcformcontrolLabel.set_text("")
        self.wpcresultLabel.set_text("")
        self.wpcAuthor.set_text(self.Server.username)
        self.wpcComment.set_text("")
        self.wpcSendButton.set_sensitive(True)

        # loading screen for app images
        self.screenshots = []
        self.appimage1stack.set_visible_child_name("loading")
        self.appimage2stack.set_visible_child_name("loading")
        self.pop1Image.set_from_pixbuf(self.missing_pixbuf)
        self.pop2Image.set_from_pixbuf(self.missing_pixbuf)

        # set scroll position to top (reset)
        self.PardusAppDetailScroll.set_vadjustment(Gtk.Adjustment())

        # clear gnome comments
        self.gcMoreButtonTR.set_visible(False)
        self.gcMoreButtonEN.set_visible(False)
        self.setGnomeComments(comments=None, lang="all")

        # clear pardus comments
        self.rate_average = 0
        self.rate_individual = ""
        self.rate_author = ""
        self.rate_comment = ""
        self.dtDownload.set_markup("")
        self.dtTotalRating.set_markup("")
        self.dtAverageRating.set_markup("")
        self.dtUserRating.set_markup("")
        self.setAppStar(0)
        self.setPardusRatings(0, 0, 0, 0, 0, 0, 0)
        self.setPardusComments(None)
        self.pcMoreButton.set_visible(False)

        # reset comment notebook page and gnome comment page
        self.CommentsNotebook.set_current_page(0)
        self.gcStack.set_visible_child_name("gcTurkish")

        # clear size and requiered changes info
        self.dActionButton.set_tooltip_text(None)
        self.dSize.set_markup("...")
        self.dSizeTitle.set_text(_("Size"))
        self.dSizeGrid.set_tooltip_text(None)

        self.dAptUpdateBox.set_visible(False)
        self.dAptUpdateButton.set_visible(False)
        self.dAptUpdateInfoLabel.set_visible(False)

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
            else:
                self.appname = iconview

            print("APPNAME : {}".format(self.appname))

            if self.UserSettings.config_usi:
                pixbuf = self.getServerAppIcon(self.appname, 128)
            else:
                pixbuf = self.getSystemAppIcon(self.appname, 128)

            self.dIcon.set_from_pixbuf(pixbuf)

            # We are using self.fullapplist because self.applist may be showing only available apps.
            # If only available applications are shown and one of the homepage applications is not from this list,
            # we still show their information.
            found_pardusapp = False
            for i in self.fullapplist:
                if i["name"] == self.appname:
                    found_pardusapp = True
                    self.description = i["description"][self.locale]
                    self.section = i["section"][0][self.locale]
                    if self.section == "" or self.section is None:
                        self.section = i["section"][0]["en"]
                    self.maintainer_name = i["maintainer"][0]["name"]
                    self.maintainer_mail = i["maintainer"][0]["mail"]
                    self.maintainer_web = i["maintainer"][0]["website"]
                    self.category = i["category"][0][self.locale].title()
                    self.license = i["license"]
                    self.copyright = i["copyright"]
                    self.codenames = ", ".join(c["name"] for c in i["codename"])
                    self.gnomename = i["gnomename"]
                    self.screenshots = i["screenshots"]
                    self.desktop_file = i["desktop"]
                    self.desktop_file_extras = i["desktopextras"]
                    self.component = i["component"]["name"]
                    prettyname = i["prettyname"][self.locale]
                    if prettyname is None or prettyname == "":
                        prettyname = i["prettyname"]["en"]

                    command = i["command"]
                    if command and command[self.locale].strip() != "":
                        self.command = command[self.locale]
                    else:
                        self.command = i["name"]

                    self.external = i["external"]
                    break

            if not found_pardusapp:
                self.reposearchbar.set_text(self.appname)
                self.on_topbutton2_clicked(self.topbutton2)
                self.on_reposearchbutton_clicked(self.reposearchbutton)
                for row in self.searchstore:
                    if self.appname == row[0]:
                        self.RepoAppsTreeView.set_cursor(row.path)
                        self.on_RepoAppsTreeView_row_activated(self.RepoAppsTreeView, row.path, 0)
                return False

            self.homestack.set_visible_child_name("pardusappsdetail")

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
                self.par_desc_more.set_visible(True)
                self.dDescriptionLabel.set_text(self.s_description)
            elif len(self.description) > 300:
                self.s_description = "{} ...".format(self.description[:300])
                self.par_desc_more.set_visible(True)
                self.dDescriptionLabel.set_text(self.s_description)
            else:
                self.par_desc_more.set_visible(False)
                self.dDescriptionLabel.set_text(self.description)

            if len(prettyname.split(" ")) > 3:
                prettyname = " ".join(prettyname.split(" ")[:3]) + "\n" + " ".join(prettyname.split(" ")[3:6]) + \
                             "\n" + " ".join(prettyname.split(" ")[6:])
            self.dName.set_markup("<span size='x-large'><b>" + prettyname + "</b></span>")
            self.dName.set_tooltip_markup("<b>{}</b>".format(self.appname))
            self.dSection.set_markup("<i>" + self.section + "</i>")
            self.dMaintainer.set_markup("<i>" + self.maintainer_name + "</i>")
            self.dCategory.set_markup(self.category)
            if self.copyright != "" and self.copyright is not None:
                self.dLicense.set_markup("<a href=''>{}</a>".format(self.license))
                self.licenseHeader.set_markup("<b>{}</b>".format(self.license))
                self.licenseBody.set_text("{}".format(self.copyright))
            else:
                self.dLicense.set_text("{}".format(self.license))
                self.licenseHeader.set_text("")
                self.licenseBody.set_text("")
            self.dCodename.set_markup(self.codenames)
            self.dMail.set_markup(
                "<a title='{}' href='mailto:{}'>{}</a>".format(self.maintainer_mail, self.maintainer_mail, "E-Mail"))
            self.dWeb.set_markup(
                "<a title='{}' href='{}'>{}</a>".format(self.maintainer_web, self.maintainer_web, "Website"))
            self.dViewonweb.set_markup("{}<a href='https://apps.pardus.org.tr/app/{}'>apps.pardus.org.tr</a>{}".format(
                _("View on "), self.appname, _(".")))
            isinstalled = self.Package.isinstalled(self.appname)

            if isinstalled is not None:
                # ret = self.Package.adv_size(self.command)
                sizethread = threading.Thread(target=self.size_worker_thread, daemon=True)
                sizethread.start()

                self.dActionButton.set_sensitive(True)

                version = self.Package.version(self.appname)
                # size = self.Package.size(self.appname)
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
                # self.dSize.set_markup(size)
                self.dComponent.set_markup("{} {}".format(origin, component))
                self.dType.set_markup(type)

                if isinstalled:
                    if self.dActionButton.get_style_context().has_class("suggested-action"):
                        self.dActionButton.get_style_context().remove_class("suggested-action")
                    self.dActionButton.get_style_context().add_class("destructive-action")
                    self.dActionButton.set_label(_(" Uninstall"))
                    self.dActionButton.set_image(
                        Gtk.Image.new_from_icon_name("user-trash-symbolic", Gtk.IconSize.BUTTON))

                    if self.desktop_file != "" and self.desktop_file is not None:
                        self.dOpenButton.set_visible(True)
                    else:
                        self.dOpenButton.set_visible(False)

                else:
                    if self.dActionButton.get_style_context().has_class("destructive-action"):
                        self.dActionButton.get_style_context().remove_class("destructive-action")
                    self.dActionButton.get_style_context().add_class("suggested-action")
                    self.dActionButton.set_label(_(" Install"))
                    self.dActionButton.set_image(
                        Gtk.Image.new_from_icon_name("document-save-symbolic", Gtk.IconSize.BUTTON))

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
                            self.dActionButton.set_image(
                                Gtk.Image.new_from_icon_name("process-working-symbolic", Gtk.IconSize.BUTTON))
                            self.dActionButton.set_sensitive(False)

            else:
                self.dActionButton.set_sensitive(False)
                if self.dActionButton.get_style_context().has_class("destructive-action"):
                    self.dActionButton.get_style_context().remove_class("destructive-action")
                if self.dActionButton.get_style_context().has_class("suggested-action"):
                    self.dActionButton.get_style_context().remove_class("suggested-action")

                self.dActionButton.set_label(_(" Not Found"))
                self.dActionButton.set_image(
                    Gtk.Image.new_from_icon_name("dialog-warning-symbolic", Gtk.IconSize.BUTTON))

                self.dActionButton.set_tooltip_text(None)

                self.dVersion.set_markup(_("None"))
                self.dSize.set_markup(_("None"))
                self.dSizeTitle.set_text(_("Download Size"))
                self.dSizeGrid.set_tooltip_text(None)
                self.dComponent.set_markup(_("None"))
                self.dType.set_markup(_("None"))

                self.dOpenButton.set_visible(False)
                self.dDisclaimerButton.set_visible(False)

                self.wpcformcontrolLabel.set_markup(
                    "<span color='red'>{}</span>".format(_("You need to install the application")))

                if self.external:
                    if self.external["externalrepo"]:
                        self.fromexternal = True
                        self.dActionButton.set_sensitive(True)
                        self.dActionButton.set_label(_("Enable Repo"))
                        self.dActionButton.set_image(
                            Gtk.Image.new_from_icon_name("list-add-symbolic", Gtk.IconSize.BUTTON))
                        if self.component == "non-free":
                            self.dDisclaimerButton.set_visible(True)
                            type = _("Non-Free")
                        else:
                            self.dDisclaimerButton.set_visible(False)
                            type = _("Open Source")
                        self.dType.set_markup(type)
                else:
                    self.dAptUpdateButton.set_visible(True)
                    if self.aptupdateclicked:
                        self.dAptUpdateBox.set_visible(True)
                        self.dAptUpdateInfoLabel.set_visible(True)

            self.pixbuf1 = None
            self.pixbuf2 = None

            if self.screenshots[0] + "#1" in self.AppImage.imgcache:
                # print("image1 in cache")
                self.pixbuf1 = self.AppImage.imgcache[self.screenshots[0] + "#1"]
                self.resizeAppImage()
                self.appimage1stack.set_visible_child_name("loaded")
            else:
                self.pixbuf1 = None
                # print("image1 not in cache")
                self.AppImage.fetch(self.Server.serverurl, self.screenshots[0], "#1")

            if self.screenshots[1] + "#2" in self.AppImage.imgcache:
                # print("image2 in cache")
                self.pixbuf2 = self.AppImage.imgcache[self.screenshots[1] + "#2"]
                self.resizeAppImage()
                self.appimage2stack.set_visible_child_name("loaded")
            else:
                # print("image2 not in cache")
                self.pixbuf2 = None
                self.AppImage.fetch(self.Server.serverurl, self.screenshots[1], "#2")

            dic = {"mac": self.mac, "app": self.appname}
            self.AppDetail.get("POST", self.Server.serverurl + "/api/v2/details", dic, self.appname)

            self.gc_limit_tr = 10
            self.gc_limit_en = 10

            self.pc_limit = 10

            pcom = {"mac": self.mac, "app": self.appname, "limit": self.pc_limit}
            self.PardusComment.get("POST", self.Server.serverurl + self.Server.serverparduscomments, pcom, self.appname)

            if self.UserSettings.config_sgc:
                self.CommentsNotebook.get_nth_page(1).show()  # page_num 1 is Gnome Comments

                gdic_tr = {"user_hash": "0000000000000000000000000000000000000000", "app_id": self.gnomename,
                           "locale": "tr", "distro": "Pardus", "version": "unknown", "limit": self.gc_limit_tr}
                self.GnomeComment.get("POST", self.Server.gnomecommentserver, gdic_tr, self.appname, "tr")

                gdic_en = {"user_hash": "0000000000000000000000000000000000000000", "app_id": self.gnomename,
                           "locale": "en", "distro": "Pardus", "version": "unknown", "limit": self.gc_limit_en}
                self.GnomeComment.get("POST", self.Server.gnomecommentserver, gdic_en, self.appname, "en")
            else:
                self.CommentsNotebook.get_nth_page(1).hide()  # page_num 1 is Gnome Comments
                print("gnome comments disabled")

    def size_worker_thread(self, app=None):
        if app is None:
            self.size_worker()
        else:
            self.size_worker(app)
        GLib.idle_add(self.on_size_worker_done)

    def size_worker(self, app=None):
        if app is None:
            self.ret = self.Package.adv_size(self.command)
        else:
            self.ret = self.Package.adv_size(app)
        print(self.ret)

    def on_size_worker_done(self):
        # print("on_size_worker_done")
        isinstalled = self.Package.isinstalled(self.appname)
        if isinstalled:
            if self.ret["to_install"] and self.ret["to_install"] is not None:
                self.dActionButton.set_tooltip_markup("<b>{} :</b>\n{}\n\n<b>{} :</b>\n{}\n\n<b>{}</b> {}\n<b>{}</b> {}\n<b>{}</b> {}".format(
                    _("Packages to remove"), ", ".join(self.ret["to_delete"]),
                    _("Packages to install"), ", ".join(self.ret["to_install"]),
                    self.Package.beauty_size(self.ret["freed_size"]), _("of disk space freed"),
                    self.Package.beauty_size(self.ret["download_size"]), _("to download"),
                    self.Package.beauty_size(self.ret["install_size"]), _("of disk space required")))
            else:
                if self.ret["to_delete"] and self.ret["to_delete"] is not None:
                    self.dActionButton.set_tooltip_markup("<b>{} :</b>\n{}\n\n<b>{}</b> {}".format(
                    _("Packages to remove"), ", ".join(self.ret["to_delete"]), self.Package.beauty_size(self.ret["freed_size"]),
                    _("of disk space freed")))

            self.dSizeTitle.set_text(_("Installed Size"))
            self.dSize.set_text("{}".format(self.ret["freed_size"]))
            self.dSizeGrid.set_tooltip_text(None)
        else:
            if self.ret["to_delete"] and self.ret["to_delete"] is not None:
                self.dActionButton.set_tooltip_markup("<b>{} :</b>\n{}\n\n<b>{} :</b>\n{}\n\n<b>{}</b> {}\n<b>{}</b> {}\n<b>{}</b> {}".format(
                    _("Packages to install"), ", ".join(self.ret["to_install"]),
                    _("Packages to remove"), ", ".join(self.ret["to_delete"]),
                    self.Package.beauty_size(self.ret["download_size"]), _("to download"),
                    self.Package.beauty_size(self.ret["install_size"]), _("of disk space required"),
                    self.Package.beauty_size(self.ret["freed_size"]), _("of disk space freed")))
            else:
                if self.ret["to_install"] and self.ret["to_install"] is not None:
                    self.dActionButton.set_tooltip_markup("<b>{} :</b>\n{}\n\n<b>{}</b> {}\n<b>{}</b> {}".format(
                        _("Packages to install"), ", ".join(self.ret["to_install"]),
                        self.Package.beauty_size(self.ret["download_size"]), _("to download"),
                        self.Package.beauty_size(self.ret["install_size"]), _("of disk space required")))

            self.dSizeTitle.set_text(_("Download Size"))
            self.dSize.set_text("{}".format(self.Package.beauty_size(self.ret["download_size"])))
            self.dSizeGrid.set_tooltip_text("{}: {}".format(_("Installed Size"), self.Package.beauty_size(self.ret["install_size"])))


    def myapps_worker_thread(self):
        myapps = self.myapps_worker()
        GLib.idle_add(self.on_myapps_worker_done, myapps)

    def myapps_worker(self):
        return self.Package.installed_packages(lang=self.locale)

    def on_myapps_worker_done(self, myapps):
        print("on_myapps_worker_done")
        for pkg in myapps:
            self.addtoMyApps(pkg)
            # GLib.idle_add(self.addtoMyApps, pkg)
        GLib.idle_add(self.MyAppsListBox.show_all)


    def myappsdetail_worker_thread(self, app):
        myappdetails = self.myappsdetail_worker(app)
        GLib.idle_add(self.on_myappsdetail_worker_done, myappdetails)

    def myappsdetail_worker(self, app):

        myapp_details, myapp_package = self.Package.myapps_remove_details(app["desktop"])
        print(myapp_details)
        return myapp_details, myapp_package, app["name"], app["icon"], app["desktop"]

    def on_myappsdetail_worker_done(self, myapp):
        # print("on_myappsdetail_worker_done")
        self.myapp_toremove_list = []
        self.myapp_toremove = ""
        self.myapp_toremove_desktop = ""
        self.ui_myapps_spinner.stop()
        details, package, name, icon, desktop = myapp
        if details is not None:
            self.ui_myapps_uninstall_button.set_sensitive(True)
            self.ui_myapps_app.set_markup("<span size='x-large'><b>{}</b></span>".format(name))
            self.ui_myapps_package.set_markup("<i>{}</i>".format(package))
            self.ui_myapps_icon.set_from_pixbuf(self.getMyAppIcon(icon, size=96))
            self.ui_myapps_description.set_markup("{}".format(self.Package.adv_description(package)))
            if details["to_delete"] and details["to_delete"] is not None:
                self.ui_myapp_toremove_label.set_markup("{}".format(", ".join(details["to_delete"])))
                self.ui_myapp_toremove_box.set_visible(True)
                self.myapp_toremove_list = details["to_delete"]
                self.myapp_toremove = package
                self.myapp_toremove_desktop = desktop
            else:
                self.ui_myapp_toremove_box.set_visible(False)

            if details["to_install"] and details["to_install"] is not None:
                self.ui_myapp_toinstall_label.set_markup("{}".format(", ".join(details["to_install"])))
                self.ui_myapp_toinstall_box.set_visible(True)
            else:
                self.ui_myapp_toinstall_box.set_visible(False)

            if details["broken"] and details["broken"] is not None:
                self.ui_myapp_broken_label.set_markup("{}".format(", ".join(details["broken"])))
                self.ui_myapp_broken_box.set_visible(True)
            else:
                self.ui_myapp_broken_box.set_visible(False)

            if details["freed_size"] and details["freed_size"] is not None and details["freed_size"] > 0:
                self.ui_myapp_fsize_label.set_markup("{}".format(self.Package.beauty_size(details["freed_size"])))
                self.ui_myapp_fsize_box.set_visible(True)
            else:
                self.ui_myapp_fsize_box.set_visible(False)

            if details["download_size"] and details["download_size"] is not None and details["download_size"] > 0:
                self.ui_myapp_dsize_label.set_markup("{}".format(self.Package.beauty_size(details["download_size"])))
                self.ui_myapp_dsize_box.set_visible(True)
            else:
                self.ui_myapp_dsize_box.set_visible(False)

            if details["install_size"] and details["install_size"] is not None and details["install_size"] > 0:
                self.ui_myapp_isize_label.set_markup("{}".format(self.Package.beauty_size(details["install_size"])))
                self.ui_myapp_isize_box.set_visible(True)
            else:
                self.ui_myapp_isize_box.set_visible(False)

            self.myappsstack.set_visible_child_name("details")
            self.myappsdetailsstack.set_visible_child_name("details")

        else:
            print("package not found")
            self.myappsstack.set_visible_child_name("notfound")

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

    def setPardusComments(self, comments, appname=""):

        for row in self.PardusCommentListBox:
            self.PardusCommentListBox.remove(row)

        if comments and appname == self.getActiveAppOnUI():

            if len(comments) == self.pc_limit:
                self.pcMoreButton.set_visible(True)
                self.pcMoreButton.set_sensitive(True)
            else:
                self.pcMoreButton.set_visible(False)

            if comments:
                for comment in comments:
                    self.setPardusCommentStar(comment["value"])

                    label_author = Gtk.Label.new()
                    label_author.set_markup("<b>{}</b>".format(comment["author"]))
                    label_date = Gtk.Label.new()
                    label_date.set_markup("{}".format(comment["date"]))

                    box1 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
                    box1.pack_start(self.cs1, False, True, 0)
                    box1.pack_start(self.cs2, False, True, 0)
                    box1.pack_start(self.cs3, False, True, 0)
                    box1.pack_start(self.cs4, False, True, 0)
                    box1.pack_start(self.cs5, False, True, 0)
                    box1.pack_start(label_author, False, True, 10)
                    box1.pack_end(label_date, False, True, 3)

                    label_comment = Gtk.Label.new()
                    label_comment.set_text("{}".format(comment["comment"]))
                    label_comment.set_selectable(True)
                    label_comment.set_line_wrap(True)
                    label_comment.set_line_wrap_mode(2)  # WORD_CHAR

                    box2 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
                    box2.pack_start(label_comment, False, True, 0)

                    hsep = Gtk.HSeparator.new()

                    self.box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 3)
                    self.box.pack_start(box1, False, True, 5)
                    self.box.pack_start(box2, False, True, 5)
                    self.box.pack_start(hsep, False, True, 0)

                    if comment["distro"] is None or comment["distro"] == "":
                        comment["distro"] = _("unknown")

                    if comment["appversion"] is None or comment["appversion"] == "":
                        comment["appversion"] = _("unknown")

                    self.box.set_tooltip_markup("<b>{}</b> : {}\n<b>{}</b> : {}".format(
                        _("Distro"), comment["distro"], _("App Version"), comment["appversion"]))

                    self.PardusCommentListBox.add(self.box)

        self.PardusCommentListBox.show_all()

    def on_par_desc_more_clicked(self, button):

        self.dDescriptionLabel.set_text(self.description)
        button.set_visible(False)

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

    def Detail(self, status, response, appname=""):
        if status and appname == self.getActiveAppOnUI():
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

            # self.setPardusComments(response["details"]["comment"])

        else:
            self.rate_average = 0
            self.rate_individual = ""
            self.rate_author = ""
            self.rate_comment = ""
            self.dtDownload.set_markup("")
            self.dtTotalRating.set_markup("")
            self.dtAverageRating.set_markup("")
            self.setAppStar(0)
            self.setPardusRatings(0, 0, 0, 0, 0, 0, 0)
            self.setPardusComments(None)

    def gComment(self, status, response, appname="", lang=""):
        if status:
            self.setGnomeComments(response, appname, lang)
        else:
            self.setGnomeComments(comments=None, lang=lang)

    def pComment(self, status, response, appname=""):
        if status:
            self.setPardusComments(response["comments"], appname)
        else:
            self.setPardusComments(comments=None)

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
        self.dPardusRating.set_markup("<span size='xx-large'><b>{:.1f}</b></span>".format(float(r)))
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

            self.dGnomeRating.set_markup("<span size='xx-large'><b>{:.1f}</b></span>".format(float(average)))
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
            self.dGnomeRating.set_markup("<span size='xx-large'><b>{}</b></span>".format(0.0))
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

    def isCommentClean(self, content):
        if self.Server.connection and self.Server.badwords and content:
            for badword in self.Server.badwords:
                if re.search(r'\b' + badword["word"] + r'\b', content):
                    return False
        return True

    def setGnomeComments(self, comments, appname="", lang=""):

        if lang == "tr":
            for row in self.GnomeCommentListBoxTR:
                self.GnomeCommentListBoxTR.remove(row)
        elif lang == "en":
            for row in self.GnomeCommentListBoxEN:
                self.GnomeCommentListBoxEN.remove(row)
        elif lang == "all":
            for row in self.GnomeCommentListBoxTR:
                self.GnomeCommentListBoxTR.remove(row)
            for row in self.GnomeCommentListBoxEN:
                self.GnomeCommentListBoxEN.remove(row)

        if comments and appname == self.getActiveAppOnUI():
            if lang == "tr":
                if len(comments) == self.gc_limit_tr:
                    self.gcMoreButtonTR.set_visible(True)
                    self.gcMoreButtonTR.set_sensitive(True)
                else:
                    self.gcMoreButtonTR.set_visible(False)
            elif lang == "en":
                if len(comments) == self.gc_limit_en:
                    self.gcMoreButtonEN.set_visible(True)
                    self.gcMoreButtonEN.set_sensitive(True)
                else:
                    self.gcMoreButtonEN.set_visible(False)
            for comment in comments:
                if "rating" and "user_display" and "date_created" and "summary" and "description" in comment:
                    if self.isCommentClean(comment["summary"]) and self.isCommentClean(
                            comment["description"]) and self.isCommentClean(comment["user_display"]):
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
                        label2.set_line_wrap_mode(2)  # WORD_CHAR
                        box2 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
                        box2.pack_start(label2, False, True, 0)
                        hsep = Gtk.HSeparator.new()
                        box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 3)
                        box.pack_start(box1, False, True, 5)
                        box.pack_start(box2, False, True, 5)
                        box.pack_start(hsep, False, True, 0)

                        if lang == "tr":
                            self.GnomeCommentListBoxTR.add(box)
                        elif lang == "en":
                            self.GnomeCommentListBoxEN.add(box)
                    else:
                        try:
                            print("Comment is not clean, app_id: {}, review_id : {}".format(
                                comment["app_id"], comment["review_id"]))
                        except Exception as e:
                            print("{}".format(e))

        if lang == "tr":
            self.GnomeCommentListBoxTR.show_all()
        elif lang == "en":
            self.GnomeCommentListBoxEN.show_all()

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
            version = self.Package.installedVersion(self.appname)
            if version is None:
                version = ""
            dic = {"app": self.appname, "mac": self.mac, "value": widget.get_name()[-1], "author": self.Server.username,
                   "installed": installed, "comment": "", "appversion": version, "distro": self.UserSettings.userdistro,
                   "justrate": True}
            self.AppRequest.send("POST", self.Server.serverurl + self.Server.serversendrate, dic)
        else:
            self.dtUserRating.set_markup("<span color='red'>{}</span>".format(_("You need to install the application")))

    def Pixbuf(self, status, pixbuf, i):
        self.appimage1stack.set_visible_child_name("loaded")
        self.appimage2stack.set_visible_child_name("loaded")
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

        if not self.imgfullscreen:
            pw = size.width - size.width / 4  # this is for popup Image
        else:
            pw = size.width - 125  # this is for popup Image

        if self.pixbuf1:
            hsize = (w * self.pixbuf1.get_height()) / self.pixbuf1.get_width()
            if hsize > size.height - size.height / 1.55:
                hsize = size.height - size.height / 1.55
                w = (hsize * self.pixbuf1.get_width()) / self.pixbuf1.get_height()

            self.dImage1.set_from_pixbuf(self.pixbuf1.scale_simple(w, hsize, GdkPixbuf.InterpType.BILINEAR))

            phsize = (pw * self.pixbuf1.get_height()) / self.pixbuf1.get_width()
            if phsize + 110 > size.height:
                phsize = size.height - 110
                pw = (phsize * self.pixbuf1.get_width()) / self.pixbuf1.get_height()

            self.pop1Image.set_from_pixbuf(self.pixbuf1.scale_simple(pw, phsize, GdkPixbuf.InterpType.BILINEAR))

        if self.pixbuf2:
            hsize = (w * self.pixbuf2.get_height()) / self.pixbuf2.get_width()
            if hsize > size.height - size.height / 1.55:
                hsize = size.height - size.height / 1.55
                w = (hsize * self.pixbuf2.get_width()) / self.pixbuf2.get_height()

            self.dImage2.set_from_pixbuf(self.pixbuf2.scale_simple(w, hsize, GdkPixbuf.InterpType.BILINEAR))

            phsize = (pw * self.pixbuf2.get_height()) / self.pixbuf2.get_width()
            if phsize + 110 > size.height:
                phsize = size.height - 110
                pw = (phsize * self.pixbuf2.get_width()) / self.pixbuf2.get_height()

            self.pop2Image.set_from_pixbuf(self.pixbuf2.scale_simple(pw, phsize, GdkPixbuf.InterpType.BILINEAR))

    def resizePopImage(self, fullscreen=False):

        size = self.MainWindow.get_size()
        if not fullscreen:
            basewidth = size.width - size.width / 3
            self.ImagePopover.set_size_request(0, 0)
        else:
            basewidth = size.width - 125
            self.ImagePopover.set_size_request(size.width, size.height)

        if self.pixbuf1:
            hsize = (basewidth * self.pixbuf1.get_height()) / self.pixbuf1.get_width()
            if hsize + 110 > size.height:
                hsize = size.height - 110
                basewidth = (hsize * self.pixbuf1.get_width()) / self.pixbuf1.get_height()

            self.pop1Image.set_from_pixbuf(self.pixbuf1.scale_simple(basewidth, hsize, GdkPixbuf.InterpType.BILINEAR))

        if self.pixbuf2:
            hsize = (basewidth * self.pixbuf2.get_height()) / self.pixbuf2.get_width()
            if hsize + 110 > size.height:
                hsize = size.height - 110
                basewidth = (hsize * self.pixbuf2.get_width()) / self.pixbuf2.get_height()

            self.pop2Image.set_from_pixbuf(self.pixbuf2.scale_simple(basewidth, hsize, GdkPixbuf.InterpType.BILINEAR))

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
                version = self.Package.installedVersion(self.appname)
                if version is None:
                    version = ""
                dic = {"mac": self.mac, "author": author, "comment": comment, "value": value, "app": self.appname,
                       "installed": installed, "appversion": version, "distro": self.UserSettings.userdistro,
                       "justrate": False}
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
            self.wpcStarLabel.set_markup(_("How many stars would you give this app ?"))
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
        category = list(model[iteration][4].split(","))
        subcategory = list(model[iteration][5].split(","))
        # category = model[iteration][4]
        appname = model[iteration][1]
        showinstalled = self.pardusicb.get_active()
        pn_en = ""
        pn_tr = ""
        desc_en = ""
        desc_tr = ""

        if self.isPardusSearching:
            for i in self.applist:
                if i["name"] == appname:
                    pn_en = i["prettyname"]["en"]
                    pn_tr = i["prettyname"]["tr"]
                    desc_en = i["description"]["en"]
                    desc_tr = i["description"]["tr"]
            if search_entry_text.lower() in appname.lower() or search_entry_text.lower() in pn_en.lower() \
                    or search_entry_text.lower() in pn_tr.lower() or search_entry_text.lower() in desc_en.lower() \
                    or search_entry_text.lower() in desc_tr.lower():
                if self.pardusicb.get_active():
                    if self.Package.isinstalled(appname):
                        return True
                else:
                    return True
        else:
            if self.PardusCurrentCategorySubCats and self.PardusCurrentCategoryExternal:
                for i in self.applist:
                    if i["name"] == appname:
                        if i["external"]:
                            if i["external"]["reponame"] == self.externalreponame:
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
                                if self.SubCatCombo.get_active_text() is not None:
                                    if self.SubCatCombo.get_active_text().lower() == "all" or self.SubCatCombo.get_active_text().lower() == "tümü":
                                        return True
                                    else:
                                        if self.PardusCurrentCategorySubCategories:
                                            if self.SubCatCombo.get_active_text().lower() in subcategory:
                                                return True
                                else:
                                    return True
                        else:
                            if self.SubCatCombo.get_active_text() is not None:
                                if self.SubCatCombo.get_active_text().lower() == "all" or self.SubCatCombo.get_active_text().lower() == "tümü":
                                    return True
                                else:
                                    if self.PardusCurrentCategorySubCategories:
                                        if self.SubCatCombo.get_active_text().lower() in subcategory:
                                            return True
                            else:
                                return True

    # def isAppAvailable(self, package):
    #     inrepo = False
    #     incodename = False
    #     if self.Package.isinstalled(package) is not None:
    #         inrepo = True
    #     for app in self.applist:
    #         if package == app["name"]:
    #             for code in app["codename"]:
    #                 if code["name"] == self.UserSettings.usercodename:
    #                     incodename = True
    #     if inrepo or incodename:
    #         return True
    #     return False

    # def PardusCategoryFilterFunctionWithShowAvailable(self, model, iteration, data):
    #     search_entry_text = self.pardussearchbar.get_text()
    #     categorynumber = int(model[iteration][2])
    #     category = model[iteration][4]
    #     appname = model[iteration][1]
    #     showinstalled = self.pardusicb.get_active()
    #     showavailable = self.UserSettings.config_saa
    #     pn_en = ""
    #     pn_tr = ""
    #     desc_en = ""
    #     desc_tr = ""
    #
    #     if self.isPardusSearching:
    #         for i in self.applist:
    #             if i["name"] == appname:
    #                 pn_en = i["prettyname"]["en"]
    #                 pn_tr = i["prettyname"]["tr"]
    #                 desc_en = i["description"]["en"]
    #                 desc_tr = i["description"]["tr"]
    #         self.HomeCategoryFlowBox.unselect_all()
    #         if search_entry_text.lower() in appname.lower() or search_entry_text.lower() in pn_en.lower() \
    #                 or search_entry_text.lower() in pn_tr.lower() or search_entry_text.lower() in desc_en \
    #                 or search_entry_text.lower() in desc_tr:
    #             if showinstalled:
    #                 if self.Package.isinstalled(appname):
    #                     if showavailable:
    #                         if self.isAppAvailable(appname):
    #                             return True
    #                     else:
    #                         return True
    #             else:
    #                 if showavailable:
    #                     if self.isAppAvailable(appname):
    #                         return True
    #                 else:
    #                     return True
    #     else:
    #         if self.PardusCurrentCategoryString == "all" or self.PardusCurrentCategoryString == "tümü":
    #             if showinstalled:
    #                 if self.Package.isinstalled(appname):
    #                     if showavailable:
    #                         if self.isAppAvailable(appname):
    #                             return True
    #                     else:
    #                         return True
    #             else:
    #                 if showavailable:
    #                     if self.isAppAvailable(appname):
    #                         return True
    #                 else:
    #                     return True
    #         else:
    #             if self.PardusCurrentCategoryString in category:
    #                 if showinstalled:
    #                     if self.Package.isinstalled(appname):
    #                         if showavailable:
    #                             if self.isAppAvailable(appname):
    #                                 return True
    #                         else:
    #                             return True
    #                 else:
    #                     if showavailable:
    #                         if self.isAppAvailable(appname):
    #                             return True
    #                     else:
    #                         return True

    def on_pardusicb_toggled(self, button):
        self.PardusCategoryFilter.refilter()

    def on_SubCatCombo_changed(self, combo_box):
        if combo_box.get_active_text() is not None:
            print("on_SubCatCombo_changed : {}".format(combo_box.get_active_text()))
            self.PardusCategoryFilter.refilter()

    def on_sortPardusAppsCombo_changed(self, combo_box):
        if combo_box.get_active() == 0:  # sort by name
            self.applist = sorted(self.applist, key=lambda x: locale.strxfrm(x["prettyname"][self.locale]))
            GLib.idle_add(self.PardusAppListStore.clear)
            self.setPardusApps()
        elif combo_box.get_active() == 1:  # sort by download
            self.applist = sorted(self.applist, key=lambda x: (x["download"], x["rate_average"]), reverse=True)
            GLib.idle_add(self.PardusAppListStore.clear)
            self.setPardusApps()
        elif combo_box.get_active() == 2:  # sort by rating
            self.applist = sorted(self.applist, key=lambda x: (x["rate_average"], x["download"]), reverse=True)
            GLib.idle_add(self.PardusAppListStore.clear)
            self.setPardusApps()
        elif combo_box.get_active() == 3:  # sort by last added
            self.applist = sorted(self.applist, key=lambda x: datetime.strptime(x["date"], "%d-%m-%Y %H:%M"),
                                  reverse=True)
            GLib.idle_add(self.PardusAppListStore.clear)
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

        self.mostappname = child.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[
            1].name

        self.on_PardusAppsIconView_selection_changed(self.mostappname)

    def on_HomeCategoryFlowBox_child_activated(self, flow_box, child):
        if self.pardusicb.get_active() and self.myapps_clicked:
            self.pardusicb.set_active(False)
            self.myapps_clicked = False

        if self.mda_clicked and self.sortPardusAppsCombo.get_active() == 1:
            self.sortPardusAppsCombo.set_active(0)
            self.mda_clicked = False

        if self.mra_clicked and self.sortPardusAppsCombo.get_active() == 2:
            self.sortPardusAppsCombo.set_active(0)
            self.mra_clicked = False

        if self.la_clicked and self.sortPardusAppsCombo.get_active() == 3:
            self.sortPardusAppsCombo.set_active(0)
            self.la_clicked = False

        self.isPardusSearching = False
        self.menubackbutton.set_sensitive(True)
        self.PardusCurrentCategory = child.get_index()
        self.PardusCurrentCategoryString, self.PardusCurrentCategoryIcon, self.PardusCurrentCategorySubCats, \
        self.PardusCurrentCategoryExternal, self.PardusCurrentCategorySubCategories = self.get_category_name(self.PardusCurrentCategory)

        print("HomeCategory: {} {} {} {} {}".format(self.PardusCurrentCategory, self.PardusCurrentCategoryString,
                                                 self.PardusCurrentCategorySubCats, self.PardusCurrentCategoryExternal,
                                                    self.PardusCurrentCategorySubCategories))
        if self.UserSettings.config_usi:
            pixbuf = self.getServerCatIcon(self.PardusCurrentCategoryIcon, 32)
        else:
            pixbuf = self.getSystemCatIcon(self.PardusCurrentCategoryIcon, 32)
        self.NavCategoryImage.set_from_pixbuf(pixbuf)
        self.NavCategoryLabel.set_text(self.PardusCurrentCategoryString.title())
        self.homestack.set_visible_child_name("pardusapps")

        self.SubCatCombo.remove_all()
        if self.PardusCurrentCategorySubCategories:
            self.SubCatCombo.append_text(_("All"))
            self.SubCatCombo.set_active(0)
            self.SubCatCombo.set_visible(True)
            for subcat in self.PardusCurrentCategorySubCategories:
                self.SubCatCombo.append_text("{}".format(subcat[self.locale].title()))
        else:
            self.SubCatCombo.set_visible(False)

        if self.PardusCurrentCategorySubCats and self.PardusCurrentCategoryExternal:
            self.pardusicb.set_visible(False)
            self.sortPardusAppsCombo.set_visible(False)
            self.pardusAppsStack.set_visible_child_name("subcats")
            for row in self.SubCategoryFlowBox:
                self.SubCategoryFlowBox.remove(row)
            subcats = []
            for i in self.applist:
                if i["external"]:
                    for cat in i["category"]:
                        if cat[self.locale] == self.PardusCurrentCategoryString:
                            subcats.append(
                                {"en": i["external"]["repoprettyen"], "tr": i["external"]["repoprettytr"],
                                 "reponame": i["external"]["reponame"]})
            subcats = list({u['reponame']: u for u in subcats}.values())
            for sub in subcats:
                caticon = Gtk.Image.new()
                caticon.set_from_pixbuf(self.getServerCatIcon(sub["reponame"]))
                label = Gtk.Label.new()
                label_text = str(sub[self.locale]).title()
                label.set_text(" " + label_text)
                box1 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
                box1.pack_start(caticon, False, True, 0)
                box1.pack_start(label, False, True, 0)
                box1.name = sub["reponame"]
                GLib.idle_add(self.SubCategoryFlowBox.insert, box1, GLib.PRIORITY_DEFAULT_IDLE)
            GLib.idle_add(self.SubCategoryFlowBox.show_all)
        else:
            self.pardusicb.set_visible(True)
            self.sortPardusAppsCombo.set_visible(True)
            self.pardusAppsStack.set_visible_child_name("normal")
            self.PardusCategoryFilter.refilter()

    def on_SubCategoryFlowBox_child_activated(self, flow_box, child):
        # print(child.get_children()[0].name)
        self.externalreponame = child.get_children()[0].name
        self.pardusicb.set_visible(True)
        self.sortPardusAppsCombo.set_visible(True)
        self.PardusCategoryFilter.refilter()
        self.pardusAppsStack.set_visible_child_name("normal")

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

    # def on_QueueListBox_row_activated(self, list_box, row):
    #
    #     i = row.get_index()
    #     if i == 0:
    #         print("you can not remove because in progress")
    #     if i == 1:
    #         print("deleting 1")
    #         print("row is " + str(i))
    #         self.queue.pop(1)
    #         self.QueueListBox.remove(row)

    # def on_clearqueuebutton_clicked(self, button):
    #     if len(self.queue) > 1:
    #         self.queue.pop(1)
    #         self.QueueListBox.remove(self.QueueListBox.get_row_at_index(1))

    def on_gcMoreButtonTR_clicked(self, button):
        self.gcMoreButtonTR.set_sensitive(False)
        self.gc_limit_tr = self.gc_limit_tr + 10
        gdic_tr = {"user_hash": "0000000000000000000000000000000000000000", "app_id": self.gnomename, "locale": "tr",
                   "distro": "Pardus", "version": "unknown", "limit": self.gc_limit_tr}
        self.GnomeComment.get("POST", self.Server.gnomecommentserver, gdic_tr, self.appname, lang="tr")

    def on_gcMoreButtonEN_clicked(self, button):
        self.gcMoreButtonEN.set_sensitive(False)
        self.gc_limit_en = self.gc_limit_en + 10
        gdic_en = {"user_hash": "0000000000000000000000000000000000000000", "app_id": self.gnomename, "locale": "en",
                   "distro": "Pardus", "version": "unknown", "limit": self.gc_limit_en}
        self.GnomeComment.get("POST", self.Server.gnomecommentserver, gdic_en, self.appname, lang="en")

    def on_pcMoreButton_clicked(self, button):
        self.pcMoreButton.set_sensitive(False)
        self.pc_limit = self.pc_limit + 10
        pcom = {"mac": self.mac, "app": self.appname, "limit": self.pc_limit}
        self.PardusComment.get("POST", self.Server.serverurl + self.Server.serverparduscomments, pcom, self.appname)

    def on_dDisclaimerButton_clicked(self, button):
        self.DisclaimerPopover.popup()

    def on_dOpenButton_clicked(self, button):
        if not self.openDesktop(self.desktop_file):
            if self.desktop_file_extras != "":
                extras = self.desktop_file_extras.split(",")
                for extra in extras:
                    if self.openDesktop(extra):
                        break

    def openDesktop(self, desktop):
        try:
            subprocess.check_call(["gtk-launch", desktop])
            return True
        except subprocess.CalledProcessError:
            print("error opening " + desktop)
            return False

    def on_dActionButton_clicked(self, button):

        if not self.fromexternal:
            self.bottomstack.set_visible_child_name("queue")
            self.bottomrevealer.set_reveal_child(True)
            self.queuestack.set_visible_child_name("inprogress")
            self.dActionButton.set_sensitive(False)
            self.queue.append({"name": self.appname, "command": self.command})
            self.addtoQueue(self.appname)
            if not self.inprogress:
                self.actionPackage(self.appname, self.command)
                self.inprogress = True
                print("action " + self.appname)
        else:
            self.activatestack.set_visible_child_name("activate")
            self.activate_repo_label.set_text(self.external["reposlist"])
            self.activate_info_label.set_text("")
            self.activate_info_label.set_visible(False)

    def on_dAptUpdateButton_clicked(self, button):
        if len(self.queue) == 0:
            self.aptupdateclicked = True
            self.dAptUpdateSpinner.start()
            self.dAptUpdateBox.set_visible(True)
            self.dAptUpdateButton.set_sensitive(False)
            self.dAptUpdateInfoLabel.set_visible(True)
            self.dAptUpdateInfoLabel.set_text(_("Updating"))
            command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/SysActions.py", "update"]
            self.uppid = self.startSysProcess(command)
        else:
            self.dAptUpdateBox.set_visible(True)
            self.dAptUpdateInfoLabel.set_visible(True)
            self.dAptUpdateInfoLabel.set_markup(
                "<span color='red'>{}</span>".format(_("Package manager is busy, try again later.")))

    def on_activate_yes_button_clicked(self, button):

        if len(self.queue) == 0:
            self.activating_spinner.start()
            self.activatestack.set_visible_child_name("activating")
            self.externalactioned = True
            self.actionEnablePackage(self.appname)
        else:
            self.activate_info_label.set_visible(True)
            self.activate_info_label.set_markup("<b><span color='red'>{}</span></b>".format(
                _("Please try again after the processes in the queue are completed.")))

    def on_activate_no_button_clicked(self, button):
        self.externalactioned = False
        self.activatestack.set_visible_child_name("main")

    def on_raction_clicked(self, button):
        self.fromexternal = False
        self.raction.set_sensitive(False)

        self.queue.append({"name": self.appname, "command": self.appname})
        self.bottomstack.set_visible_child_name("queue")

        self.bottomrevealer.set_reveal_child(True)
        self.queuestack.set_visible_child_name("inprogress")

        self.addtoQueue(self.appname)

        if not self.inprogress:
            self.actionPackage(self.appname, self.appname)
            self.inprogress = True
            print("action " + self.appname)

    def on_topbutton1_clicked(self, button):
        if self.Server.connection:
            self.searchstack.set_visible_child_name("pardus")
            self.homestack.set_visible_child_name("pardushome")
            self.EditorAppsIconView.unselect_all()
            self.PardusAppsIconView.unselect_all()
            self.topsearchbutton.set_active(self.statusoftopsearch)
            self.topsearchbutton.set_sensitive(True)
        else:
            self.searchstack.set_visible_child_name("noserver")
            self.homestack.set_visible_child_name("noserver")
            self.topsearchbutton.set_active(False)
            self.topsearchbutton.set_sensitive(False)

        self.menubackbutton.set_sensitive(False)
        if self.topbutton2.get_style_context().has_class("suggested-action"):
            self.topbutton2.get_style_context().remove_class("suggested-action")
        if self.queuebutton.get_style_context().has_class("suggested-action"):
            self.queuebutton.get_style_context().remove_class("suggested-action")
        if not self.topbutton1.get_style_context().has_class("suggested-action"):
            self.topbutton1.get_style_context().add_class("suggested-action")

    def on_topbutton2_clicked(self, button):
        self.menubackbutton.set_sensitive(True)
        self.prefback = self.homestack.get_visible_child_name()

        self.searchstack.set_visible_child_name("repo")
        self.homestack.set_visible_child_name("repohome")
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
        self.menubackbutton.set_sensitive(True)
        self.prefback = self.homestack.get_visible_child_name()
        self.homestack.set_visible_child_name("queue")
        if self.topbutton1.get_style_context().has_class("suggested-action"):
            self.topbutton1.get_style_context().remove_class("suggested-action")
        if self.topbutton2.get_style_context().has_class("suggested-action"):
            self.topbutton2.get_style_context().remove_class("suggested-action")
        if not self.queuebutton.get_style_context().has_class("suggested-action"):
            self.queuebutton.get_style_context().add_class("suggested-action")

    def addtoQueue(self, appname, myappicon=False):

        appicon = Gtk.Image.new()
        if self.UserSettings.config_usi:
            appicon.set_from_pixbuf(self.getServerAppIcon(self.appname, myappicon=myappicon))
        else:
            appicon.set_from_pixbuf(self.getSystemAppIcon(self.appname, myappicon=myappicon))
        label = Gtk.Label.new()
        label.set_text(self.getPrettyName(self.appname, split=False))
        actlabel = Gtk.Label.new()

        isinstalled = self.Package.isinstalled(self.appname)
        if isinstalled:
            actlabel.set_markup("<span color='#e01b24'>{}</span>".format(_("Will be removed")))
        else:
            actlabel.set_markup("<span color='#3584e4'>{}</span>".format(_("Will be installed")))

        button = Gtk.Button.new()
        button.name = self.appname
        button.connect("clicked", self.remove_from_queue_clicked)
        button.props.valign = Gtk.Align.CENTER
        button.props.halign = Gtk.Align.CENTER
        button.props.always_show_image = True
        button.set_image(Gtk.Image.new_from_icon_name("edit-delete-symbolic", Gtk.IconSize.BUTTON))
        if len(self.queue) == 1:
            button.set_sensitive(False)
            button.set_tooltip_text(_("You cannot cancel because the application is in progress."))
            if isinstalled:
                actlabel.set_markup("<span color='#e01b24'>{}</span>".format(_("Removing")))
            else:
                actlabel.set_markup("<span color='#3584e4'>{}</span>".format(_("Installing")))
        box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
        box.set_margin_top(5)
        box.set_margin_bottom(5)
        box.set_margin_start(5)
        box.set_margin_end(5)
        box.pack_start(appicon, False, True, 0)
        box.pack_start(label, False, True, 0)
        box.pack_end(button, False, True, 13)
        box.pack_end(actlabel, False, True, 13)
        box.name = self.appname
        self.QueueListBox.add(box)
        self.QueueListBox.show_all()

    def remove_from_queue_clicked(self, button):
        for row in self.QueueListBox:
            if row.get_children()[0].name == button.name:
                if row.get_index() != 0:
                    self.QueueListBox.remove(row)
                    # removing from queue list too
                    index = next((index for (index, app) in enumerate(self.queue) if app["name"] == button.name), None)
                    self.queue.pop(index)

    def addtoMyApps(self, app):

        appicon = Gtk.Image.new()
        appicon.set_from_pixbuf(self.getMyAppIcon(app["icon"]))

        name = Gtk.Label.new()
        name.set_markup("<b>{}</b>".format(GLib.markup_escape_text(app["name"], -1)))
        name.props.halign = Gtk.Align.START

        # sizelabel = Gtk.Label.new()
        # sizelabel.set_markup("{}".format(self.Package.beauty_size(app["size"])))
        # sizelabel.props.valign = Gtk.Align.CENTER

        summarylabel = Gtk.Label.new()
        summarylabel.set_markup("<small>{}</small>".format(GLib.markup_escape_text(app["comment"], -1)))
        summarylabel.set_line_wrap(True)
        summarylabel.set_line_wrap_mode(2)  # WORD_CHAR
        summarylabel.props.halign = Gtk.Align.START

        uninstallbutton = Gtk.Button.new()
        uninstallbutton.name = {"name": app["name"], "desktop": app["desktop"], "icon": app["icon"]}
        uninstallbutton.props.valign = Gtk.Align.CENTER
        uninstallbutton.props.halign = Gtk.Align.CENTER
        uninstallbutton.props.always_show_image = True
        uninstallbutton.set_image(Gtk.Image.new_from_icon_name("user-trash-symbolic", Gtk.IconSize.BUTTON))
        uninstallbutton.set_label("")
        uninstallbutton.set_tooltip_text(_("Uninstall"))
        uninstallbutton.get_style_context().add_class("destructive-action")
        uninstallbutton.connect("clicked", self.remove_from_myapps)

        openbutton = Gtk.Button.new()
        openbutton.name = app["desktop"]
        openbutton.props.valign = Gtk.Align.CENTER
        openbutton.props.halign = Gtk.Align.CENTER
        openbutton.props.always_show_image = True
        openbutton.set_image(Gtk.Image.new_from_icon_name("system-run-symbolic", Gtk.IconSize.BUTTON))
        openbutton.set_label("")
        openbutton.set_tooltip_text(_("Open"))
        openbutton.connect("clicked", self.open_from_myapps)

        box1 = Gtk.Box.new(Gtk.Orientation.VERTICAL, 3)
        box1.pack_start(name, False, True, 0)
        box1.pack_start(summarylabel, False, True, 0)
        box1.props.valign = Gtk.Align.CENTER

        box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
        box.set_margin_top(5)
        box.set_margin_bottom(5)
        box.set_margin_start(5)
        box.set_margin_end(5)
        box.pack_start(appicon, False, True, 5)
        box.pack_start(box1, False, True, 5)
        box.pack_end(uninstallbutton, False, True, 13)
        box.pack_end(openbutton, False, True, 5)
        # box.pack_end(sizelabel, False, True, 13)
        box.name = app["desktop"]

        GLib.idle_add(self.MyAppsListBox.add, box)

    def remove_from_myapps(self, button):
        print(button.name)

        self.myappsstack.set_visible_child_name("details")
        self.myappsdetailsstack.set_visible_child_name("spinner")
        self.ui_myapps_spinner.start()
        myappsdetailsthread = threading.Thread(target=self.myappsdetail_worker_thread, args=(button.name,), daemon=True)
        myappsdetailsthread.start()

    def open_from_myapps(self, button):
        print(button.name)
        self.openDesktop(os.path.basename(button.name))

    def on_ui_myapps_cancel_clicked(self, button):
        self.myappsstack.set_visible_child_name("myapps")

    def on_ui_myapps_cancel_disclaimer_clicked(self, button):
        self.myappsdetailsstack.set_visible_child_name("details")

    def on_ui_myapps_uninstall_button_clicked(self, button):
        importants =  [i for i in self.important_packages if i in self.myapp_toremove_list]
        if importants:
            self.myappsdetailsstack.set_visible_child_name("disclaimer")
            self.ui_myapps_disclaimer_label.set_markup("<big>{}\n\n<b>{}</b>\n\n{}</big>".format(
                _("The following important packages will also be removed."),
                ", ".join(importants),
            _("Are you sure you accept this ?")))
        else:
            print("not important package")
            self.ui_myapps_uninstall()

    def on_ui_myapps_accept_disclaimer_clicked(self, button):
        self.myappsdetailsstack.set_visible_child_name("details")
        self.ui_myapps_uninstall()

    def ui_myapps_uninstall(self):
        self.appname = self.myapp_toremove
        self.command = self.myapp_toremove
        self.desktop_file = self.myapp_toremove_desktop
        self.bottomstack.set_visible_child_name("queue")
        self.bottomrevealer.set_reveal_child(True)
        self.queuestack.set_visible_child_name("inprogress")
        self.ui_myapps_uninstall_button.set_sensitive(False)
        self.queue.append({"name": self.appname, "command": self.command})
        self.addtoQueue(self.appname, myappicon=True)
        if not self.inprogress:
            self.actionPackage(self.appname, self.command)
            self.inprogress = True
            print("action " + self.appname)

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
            pixbuf = self.getServerCatIcon("all", 32)
        else:
            pixbuf = self.getSystemCatIcon("all", 32)

        self.NavCategoryImage.set_from_pixbuf(pixbuf)
        self.NavCategoryLabel.set_text(_("all").title())
        if self.locale == "tr":
            self.PardusCurrentCategoryString = "tümü"
        else:
            self.PardusCurrentCategoryString = "all"

        self.SubCatCombo.remove_all()
        self.SubCatCombo.set_visible(False)

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
                self.raction.set_image(Gtk.Image.new_from_icon_name("user-trash-symbolic", Gtk.IconSize.BUTTON))
            else:
                if self.raction.get_style_context().has_class("destructive-action"):
                    self.raction.get_style_context().remove_class("destructive-action")
                self.raction.get_style_context().add_class("suggested-action")
                self.raction.set_label(_(" Install"))
                self.raction.set_image(Gtk.Image.new_from_icon_name("document-save-symbolic", Gtk.IconSize.BUTTON))
        else:
            self.raction.set_sensitive(False)
            if self.raction.get_style_context().has_class("destructive-action"):
                self.raction.get_style_context().remove_class("destructive-action")
            if self.raction.get_style_context().has_class("suggested-action"):
                self.raction.get_style_context().remove_class("suggested-action")

            self.raction.set_label(_(" Not Found"))
            self.raction.set_image(Gtk.Image.new_from_icon_name("dialog-warning-symbolic", Gtk.IconSize.BUTTON))

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
            if self.searchstack.get_visible_child_name() == "pardus":
                self.pardussearchbar.grab_focus()
                print("in grab focus")
            elif self.searchstack.get_visible_child_name() == "repo":
                self.reposearchbar.grab_focus()
        else:
            self.toprevealer.set_reveal_child(False)
            self.statusoftopsearch = False

    # def on_HeaderBarMenuButton_toggled(self, button):
    #     self.HeaderBarMenuButton.grab_focus()

    def on_main_key_press_event(self, widget, event):
        if self.mainstack.get_visible_child_name() == "home":
            if self.homestack.get_visible_child_name() == "pardushome" or self.homestack.get_visible_child_name() == "pardusapps":
                if not self.topsearchbutton.get_active():
                    if event.string.isdigit() or event.string.isalpha():
                        self.pardussearchbar.get_buffer().delete_text(0, -1)
                        self.pardussearchbar.grab_focus()
                        self.topsearchbutton.set_active(True)
                        self.toprevealer.set_reveal_child(True)
                        self.pardussearchbar.get_buffer().insert_text(1, event.string, 1)
                        self.pardussearchbar.set_position(2)
                        return True
                else:
                    if event.keyval == Gdk.KEY_Escape:
                        self.pardussearchbar.get_buffer().delete_text(0, -1)
                        self.topsearchbutton.set_active(False)
                        self.toprevealer.set_reveal_child(False)
                        return True

    def on_menu_settings_clicked(self, button):
        self.prefback = self.homestack.get_visible_child_name()
        self.PopoverMenu.popdown()
        self.topsearchbutton.set_active(False)
        self.topsearchbutton.set_sensitive(False)
        self.prefstack.set_visible_child_name("main")
        self.homestack.set_visible_child_name("preferences")
        self.menubackbutton.set_sensitive(True)
        self.UserSettings.readConfig()
        self.switchUSI.set_state(self.UserSettings.config_usi)
        self.switchEA.set_state(self.UserSettings.config_ea)
        self.switchSAA.set_state(self.UserSettings.config_saa)
        self.switchHERA.set_state(self.UserSettings.config_hera)
        self.switchSGC.set_state(self.UserSettings.config_sgc)
        self.switchUDT.set_state(self.UserSettings.config_udt)
        self.switchAPTU.set_state(self.UserSettings.config_aptup)
        self.prefServerLabel.set_markup("<small><span weight='light'>{} : {}</span></small>".format(
            _("Server Address"), self.Server.serverurl))
        self.topbutton2.get_style_context().remove_class("suggested-action")
        self.topbutton1.get_style_context().remove_class("suggested-action")
        self.queuebutton.get_style_context().remove_class("suggested-action")
        self.preflabel.set_text("")
        self.prefcachebutton.set_sensitive(True)
        self.prefcachebutton.set_label(_("Clear"))

        self.setSelectIcons()

    def setSelectIcons(self):
        if self.UserSettings.config_usi:
            self.selecticonsBox.set_visible(True)
            self.setServerIconCombo.remove_all()
            iconnames = self.Server.iconnames.split(",")
            self.setServerIconCombo.append("default", _("Default"))
            for icon in iconnames:
                self.setServerIconCombo.append(icon, icon.capitalize())
            user_config_icon = self.UserSettings.config_icon
            self.setServerIconCombo.set_active_id(user_config_icon)
        else:
            self.selecticonsBox.set_visible(False)

    def on_menu_myapps_clicked(self, button):

        ### this shows only available apps on pardus-software (old method)
        #
        # self.PardusAppsIconView.unselect_all()
        # if self.topbutton2.get_style_context().has_class("suggested-action"):
        #     self.topbutton2.get_style_context().remove_class("suggested-action")
        # if self.queuebutton.get_style_context().has_class("suggested-action"):
        #     self.queuebutton.get_style_context().remove_class("suggested-action")
        # if not self.topbutton1.get_style_context().has_class("suggested-action"):
        #     self.topbutton1.get_style_context().add_class("suggested-action")
        # # self.topsearchbutton.set_active(True)
        # self.topsearchbutton.set_sensitive(True)
        # self.searchstack.set_visible_child_name("pardus")
        #
        # self.menubackbutton.set_sensitive(True)
        # if not self.pardusicb.get_active():
        #     self.myapps_clicked = True
        # self.pardusicb.set_visible(True)
        # self.PopoverMenu.popdown()
        # self.PardusCurrentCategoryString = "all"
        # self.PardusCurrentCategoryIcon = "all"
        # self.PardusCurrentCategorySubCats = False
        # self.PardusCurrentCategoryExternal = False
        # self.isPardusSearching = False
        # self.pardussearchbar.set_text("")
        # self.topsearchbutton.set_active(False)
        # if self.UserSettings.config_usi:
        #     pixbuf = self.getServerCatIcon(self.PardusCurrentCategoryIcon, 32)
        # else:
        #     pixbuf = self.getSystemCatIcon(self.PardusCurrentCategoryIcon, 32)
        # self.NavCategoryImage.set_from_pixbuf(pixbuf)
        # self.NavCategoryLabel.set_text(_("all").title())
        # if self.sortPardusAppsCombo.get_active != 0:
        #     self.sortPardusAppsCombo.set_active(0)
        # if not self.pardusicb.get_active():
        #     self.pardusicb.set_active(True)
        # self.PardusCategoryFilter.refilter()
        # self.pardusAppsStack.set_visible_child_name("normal")
        #
        ### this shows only available apps on pardus-software (old method)


        self.PopoverMenu.popdown()
        self.PardusAppsIconView.unselect_all()
        self.EditorAppsIconView.unselect_all()
        if self.topbutton1.get_style_context().has_class("suggested-action"):
            self.topbutton1.get_style_context().remove_class("suggested-action")
        if self.topbutton2.get_style_context().has_class("suggested-action"):
            self.topbutton2.get_style_context().remove_class("suggested-action")
        if self.queuebutton.get_style_context().has_class("suggested-action"):
            self.queuebutton.get_style_context().remove_class("suggested-action")
        self.topsearchbutton.set_sensitive(True)
        self.searchstack.set_visible_child_name("pardus")
        self.pardussearchbar.set_text("")
        self.topsearchbutton.set_active(False)
        self.menubackbutton.set_sensitive(True)
        self.homestack.set_visible_child_name("myapps")
        self.myappsstack.set_visible_child_name("myapps")

        for row in self.MyAppsListBox:
            self.MyAppsListBox.remove(row)

        myappsthread = threading.Thread(target=self.myapps_worker_thread, daemon=True)
        myappsthread.start()

    def on_menu_statistics_clicked(self, button):
        self.prefback = self.homestack.get_visible_child_name()
        self.PopoverMenu.popdown()
        self.topsearchbutton.set_active(False)
        self.topsearchbutton.set_sensitive(False)
        self.menubackbutton.set_sensitive(True)
        self.homestack.set_visible_child_name("statistics")
        self.topbutton2.get_style_context().remove_class("suggested-action")
        self.topbutton1.get_style_context().remove_class("suggested-action")
        self.queuebutton.get_style_context().remove_class("suggested-action")

        if self.Server.connection:
            self.setStatistics()

    def setStatistics(self):
        if not self.statisticsSetted:
            self.statstotaldc.set_markup("<small><b>{}</b></small>".format(self.Server.totalstatistics[0]["downcount"]))
            self.statstotalrc.set_markup("<small><b>{}</b></small>".format(self.Server.totalstatistics[0]["ratecount"]))
            self.statsweblabel.set_markup(
                "<small>{}<a href='https://apps.pardus.org.tr/statistics' title='https://apps.pardus.org.tr/statistics'>apps.pardus.org.tr</a>{}</small>".format(
                    _("View on "), _(".")))
            dates = []
            downs = []
            for data in self.Server.dailydowns:
                dates.append(data["date"])
                downs.append(data["count"])
            fig1, ax1 = plt.subplots()
            p1 = ax1.bar(dates, downs, width=0.9, edgecolor="white", linewidth=1)
            plt.title(_("Daily App Download Counts (Last 30 Days)"))
            plt.tight_layout()
            # ax.bar_label(p1, label_type='edge', fontsize="small") # requires version 3.4-2+
            fig1.autofmt_xdate(rotation=60)
            canvas1 = FigureCanvas(fig1)
            self.stats1ViewPort.add(canvas1)

            osnames = []
            osdowns = []
            for osdata in self.Server.osdowns:
                for key, value in osdata.items():
                    if self.locale == "tr" and key == "Others":
                        key = "Diğerleri"
                    osnames.append(key)
                    osdowns.append(value)

            explode = (0.1, 0.3, 0.4, 0.5)
            fig2, ax2 = plt.subplots()
            p2 = ax2.pie(osdowns, labels=osnames, colors=self.Server.oscolors, explode=explode,
                         autopct=lambda p: f'{p * sum(osdowns) / 100 :.0f} (%{p:.2f})')
            # plt.setp(p2[1], size="small", weight="bold")
            # plt.setp(p2[2], size="small", weight="bold")
            ax2.axis('equal')
            plt.title(_("Used Operating Systems (For App Download)"))
            plt.tight_layout()
            canvas2 = FigureCanvas(fig2)
            self.stats2ViewPort.add(canvas2)

            appnames = []
            appdowns = []
            for appdata in self.Server.appdowns:
                if self.locale == "tr":
                    appnames.append(appdata["name_tr"])
                else:
                    appnames.append(appdata["name_en"])
                appdowns.append(appdata["count"])
            fig3, ax3 = plt.subplots()
            p3 = ax3.bar(appnames, appdowns, width=0.9, edgecolor="white", linewidth=1, color=self.Server.appcolors)
            plt.title(_("Top 30 App Downloads"))
            plt.xticks(size="small")
            plt.tight_layout()
            # ax.bar_label(p1, label_type='edge', fontsize="small") # requires version 3.4-2+
            fig3.autofmt_xdate(rotation=45)
            canvas3 = FigureCanvas(fig3)
            self.stats3ViewPort.add(canvas3)

            self.stats1ViewPort.show_all()
            self.stats2ViewPort.show_all()
            self.stats3ViewPort.show_all()

            self.statisticsSetted = True

    def on_menu_updates_clicked(self, button):
        self.prefback = self.homestack.get_visible_child_name()
        self.menubackbutton.set_sensitive(True)
        self.PopoverMenu.popdown()
        self.topsearchbutton.set_active(False)
        self.topsearchbutton.set_sensitive(False)
        self.homestack.set_visible_child_name("updates")
        self.topbutton2.get_style_context().remove_class("suggested-action")
        self.topbutton1.get_style_context().remove_class("suggested-action")
        self.queuebutton.get_style_context().remove_class("suggested-action")
        self.updateerrorlabel.set_text("")

    def on_menu_about_clicked(self, button):
        self.PopoverMenu.popdown()
        self.aboutdialog.run()
        self.aboutdialog.hide()

    def on_menu_suggestapp_clicked(self, button):
        self.prefback = self.homestack.get_visible_child_name()
        self.menubackbutton.set_sensitive(True)
        self.PopoverMenu.popdown()
        self.topsearchbutton.set_active(False)
        self.topsearchbutton.set_sensitive(False)
        self.topbutton2.get_style_context().remove_class("suggested-action")
        self.topbutton1.get_style_context().remove_class("suggested-action")
        self.queuebutton.get_style_context().remove_class("suggested-action")
        self.SuggestCat.remove_all()
        self.SuggestCat.append_text(_("Select Category"))
        self.SuggestCat.set_active(0)
        cats = []
        for cat in self.fullcatlist:
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

    def on_pref_tip_clicked(self, button):
        self.prefTipLabel.set_max_width_chars(-1)
        if button.get_name() == "tip_usi":
            self.PopoverPrefTip.set_relative_to(self.tip_usi)
            self.prefTipLabel.set_text("{}\n{}\n{}".format(
                _("If you use the server icons, the application icons will be pulled from the server completely."),
                _("If you turn this option off, application icons will be pulled from your system,"),
                _("which may cause some application icons to appear blank.")))
            self.PopoverPrefTip.popup()
        elif button.get_name() == "tip_ea":
            self.PopoverPrefTip.set_relative_to(self.tip_ea)
            self.prefTipLabel.set_text(_("Transition animations in the application."))
            self.PopoverPrefTip.popup()
        elif button.get_name() == "tip_soaa":
            self.PopoverPrefTip.set_relative_to(self.tip_soaa)
            self.prefTipLabel.set_text("{} {} {}\n{}\n{}".format(
                _("Show only available applications in"), self.UserSettings.usercodename, _("repository."),
                _("If you turn this option off, all apps will be shown, but"),
                _("'Not Found' will be displayed for apps not available in the repository.")))
            self.PopoverPrefTip.popup()
        elif button.get_name() == "tip_hera":
            self.PopoverPrefTip.set_relative_to(self.tip_hera)
            self.prefTipLabel.set_text("{}\n{}".format(
                _("Hide applications offered from external repositories (other than Official Pardus repository)."),
                _("For example, publisher's applications in the Publishers category.")
            ))
            self.PopoverPrefTip.popup()
        elif button.get_name() == "tip_icons":
            self.PopoverPrefTip.set_relative_to(self.tip_icons)
            self.prefTipLabel.set_markup("{} {}\n{} {}\n{} {}\n{} {}\n{} {}\n{} {}\n{} {}\n{} {}\n{} {}".format(
                _("Default icons use Papirus icon theme."),
                ("<a href='https://github.com/PapirusDevelopmentTeam/papirus-icon-theme'>Site</a>"),
                _("Candy is Candy icon theme."),
                ("<a href='https://github.com/EliverLara/candy-icons/'>Site</a>"),
                _("Flat is Flat Remix icon theme."),
                ("<a href='https://github.com/daniruiz/Flat-Remix'>Site</a>"),
                _("Flatery is Flatery icon theme."),
                ("<a href='https://github.com/cbrnix/Flatery'>Site</a>"),
                _("Kora is Kora icon theme."),
                ("<a href='https://github.com/bikass/kora'>Site</a>"),
                _("Numix is Numix Circle icon theme."),
                ("<a href='https://github.com/numixproject/numix-icon-theme-circle'>Site</a>"),
                _("Oranchelo is Oranchelo icon theme."),
                ("<a href='https://github.com/OrancheloTeam/oranchelo-icon-theme'>Site</a>"),
                _("Tela is Tela icon theme."),
                ("<a href='https://github.com/vinceliuice/Tela-icon-theme'>Site</a>"),
                _("Zafiro is Zafiro icon theme."),
                ("<a href='https://github.com/zayronxio/Zafiro-icons'>Site</a>")
            ))
            self.PopoverPrefTip.popup()
        elif button.get_name() == "tip_sgc":
            self.PopoverPrefTip.set_relative_to(self.tip_sgc)
            self.prefTipLabel.set_markup("{}\n{}".format(
                _("Show gnome comments in app comments."),
                _("GNOME comments are pulled from <a href='https://odrs.gnome.org'>GNOME ODRS</a>.")
            ))
            self.PopoverPrefTip.popup()
        elif button.get_name() == "tip_udt":
            self.PopoverPrefTip.set_relative_to(self.tip_udt)
            self.prefTipLabel.set_markup("{}\n{}".format(
                _("Whether the application prefers to use a dark theme."),
                _("If a GTK+ theme includes a dark variant, it will be used instead of the configured theme.")
            ))
            self.PopoverPrefTip.popup()
        elif button.get_name() == "tip_aptu":
            if self.UserSettings.config_forceaptuptime != 0:
                force = "{} ( {} )".format(_("The value in your configuration file is used as the wait time."),
                                           self.displayTime(self.UserSettings.config_forceaptuptime))
            else:
                force = False
            self.PopoverPrefTip.set_relative_to(self.tip_aptu)
            self.prefTipLabel.set_max_width_chars(60)
            if force is False:
                self.prefTipLabel.set_markup("{} {} {}\n<u>{}:</u> <b>{}</b>".format(
                    _("Allows the package manager cache to be updated again on the next application start if"),
                    self.displayTime(self.Server.aptuptime),
                    _("have passed since the last successful update."),
                    _("Last successful update time is"),
                    datetime.fromtimestamp(self.UserSettings.config_lastaptup)
                ))
            else:
                self.prefTipLabel.set_markup("{} {} {}\n<u>{}:</u> <b>{}</b>\n\n<span color='red'>{}</span>".format(
                    _("Allows the package manager cache to be updated again on the next application start if"),
                    self.displayTime(self.Server.aptuptime),
                    _("have passed since the last successful update."),
                    _("Last successful update time is"),
                    datetime.fromtimestamp(self.UserSettings.config_lastaptup),
                    force
                ))
            self.PopoverPrefTip.popup()

    def displayTime(self, seconds, granularity=5):
        result = []
        intervals = (
            (_("weeks"), 604800),  # 60 * 60 * 24 * 7
            (_("days"), 86400),  # 60 * 60 * 24
            (_("hours"), 3600),  # 60 * 60
            (_("minutes"), 60),
            (_("seconds"), 1),
        )
        for name, count in intervals:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip('s')
                result.append("{} {}".format(value, name))
        return ', '.join(result[:granularity])

    def on_switchUSI_state_set(self, switch, state):
        user_config_usi = self.UserSettings.config_usi
        if state != user_config_usi:
            print("Updating user icon state")
            try:
                self.UserSettings.writeConfig(state, self.UserSettings.config_ea, self.UserSettings.config_saa,
                                              self.UserSettings.config_hera, self.UserSettings.config_icon,
                                              self.UserSettings.config_sgc, self.UserSettings.config_udt,
                                              self.UserSettings.config_aptup, self.UserSettings.config_lastaptup,
                                              self.UserSettings.config_forceaptuptime)
                self.usersettings()
                GLib.idle_add(self.clearBoxes)
                if state:
                    self.Server.getIcons(
                        self.Server.serverurl + self.Server.serverfiles + self.Server.serverappicons + self.Server.serverarchive,
                        self.Server.serverappicons, fromsettings=True)

                    self.Server.getIcons(
                        self.Server.serverurl + self.Server.serverfiles + self.Server.servercaticons + self.Server.serverarchive,
                        self.Server.servercaticons, fromsettings=True)
                else:
                    self.setPardusApps()
                    self.setPardusCategories()
                    self.setEditorApps()
                    self.setMostApps()
                    self.setSelectIcons()
            except Exception as e:
                self.preflabel.set_text(str(e))
                print(e)

    def on_switchEA_state_set(self, switch, state):
        user_config_ea = self.UserSettings.config_ea
        if state != user_config_ea:
            print("Updating user animation state")
            try:
                self.UserSettings.writeConfig(self.UserSettings.config_usi, state, self.UserSettings.config_saa,
                                              self.UserSettings.config_hera, self.UserSettings.config_icon,
                                              self.UserSettings.config_sgc, self.UserSettings.config_udt,
                                              self.UserSettings.config_aptup, self.UserSettings.config_lastaptup,
                                              self.UserSettings.config_forceaptuptime)
                self.usersettings()
                self.setAnimations()
            except Exception as e:
                self.preflabel.set_text(str(e))

    def on_switchSAA_state_set(self, switch, state):
        user_config_saa = self.UserSettings.config_saa
        if state != user_config_saa:
            print("Updating show available apps state")
            try:
                self.UserSettings.writeConfig(self.UserSettings.config_usi, self.UserSettings.config_ea, state,
                                              self.UserSettings.config_hera, self.UserSettings.config_icon,
                                              self.UserSettings.config_sgc, self.UserSettings.config_udt,
                                              self.UserSettings.config_aptup, self.UserSettings.config_lastaptup,
                                              self.UserSettings.config_forceaptuptime)
                self.usersettings()
                self.setAvailableApps(available=state, hideextapps=self.UserSettings.config_hera)
            except Exception as e:
                self.preflabel.set_text(str(e))

            GLib.idle_add(self.clearBoxes)
            self.setPardusApps()
            self.setPardusCategories()
            self.setEditorApps()
            self.setMostApps()

    def on_switchHERA_state_set(self, switch, state):
        user_config_hera = self.UserSettings.config_hera
        if state != user_config_hera:
            print("Updating hide external apps state")
            try:
                self.UserSettings.writeConfig(self.UserSettings.config_usi, self.UserSettings.config_ea,
                                              self.UserSettings.config_saa, state, self.UserSettings.config_icon,
                                              self.UserSettings.config_sgc, self.UserSettings.config_udt,
                                              self.UserSettings.config_aptup, self.UserSettings.config_lastaptup,
                                              self.UserSettings.config_forceaptuptime)
                self.usersettings()
                self.setAvailableApps(available=self.UserSettings.config_saa, hideextapps=state)
            except Exception as e:
                self.preflabel.set_text(str(e))

            GLib.idle_add(self.clearBoxes)
            self.setPardusApps()
            self.setPardusCategories()
            self.setEditorApps()
            self.setMostApps()

    def on_setServerIconCombo_changed(self, combo_box):
        user_config_icon = self.UserSettings.config_icon
        active = combo_box.get_active_id()
        if active != user_config_icon and active is not None:
            print("changing icons to " + str(combo_box.get_active_id()))
            self.UserSettings.writeConfig(self.UserSettings.config_usi, self.UserSettings.config_ea,
                                          self.UserSettings.config_saa, self.UserSettings.config_hera, active,
                                          self.UserSettings.config_sgc, self.UserSettings.config_udt,
                                          self.UserSettings.config_aptup, self.UserSettings.config_lastaptup,
                                          self.UserSettings.config_forceaptuptime)
            self.usersettings()
            GLib.idle_add(self.clearBoxes)
            self.setPardusApps()
            self.setPardusCategories()
            self.setEditorApps()
            self.setMostApps()

    def on_switchSGC_state_set(self, switch, state):
        user_config_sgc = self.UserSettings.config_sgc
        if state != user_config_sgc:
            print("Updating show gnome apps state as {}".format(state))
            self.UserSettings.writeConfig(self.UserSettings.config_usi, self.UserSettings.config_ea,
                                          self.UserSettings.config_saa, self.UserSettings.config_hera,
                                          self.UserSettings.config_icon, state, self.UserSettings.config_udt,
                                          self.UserSettings.config_aptup, self.UserSettings.config_lastaptup,
                                          self.UserSettings.config_forceaptuptime)
            self.usersettings()

    def on_switchUDT_state_set(self, switch, state):
        user_config_udt = self.UserSettings.config_udt
        if state != user_config_udt:
            print("Updating use dark theme state as {}".format(state))
            self.UserSettings.writeConfig(self.UserSettings.config_usi, self.UserSettings.config_ea,
                                          self.UserSettings.config_saa, self.UserSettings.config_hera,
                                          self.UserSettings.config_icon, self.UserSettings.config_sgc, state,
                                          self.UserSettings.config_aptup, self.UserSettings.config_lastaptup,
                                          self.UserSettings.config_forceaptuptime)
        if state:
            Gtk.Settings.get_default().props.gtk_application_prefer_dark_theme = True
        else:
            Gtk.Settings.get_default().props.gtk_application_prefer_dark_theme = False

        self.usersettings()

    def on_switchAPTU_state_set(self, switch, state):
        user_config_aptup = self.UserSettings.config_aptup
        if state != user_config_aptup:
            print("Updating auto apt update state as {}".format(state))
            self.UserSettings.writeConfig(self.UserSettings.config_usi, self.UserSettings.config_ea,
                                          self.UserSettings.config_saa, self.UserSettings.config_hera,
                                          self.UserSettings.config_icon, self.UserSettings.config_sgc,
                                          self.UserSettings.config_udt, state,
                                          self.UserSettings.config_lastaptup, self.UserSettings.config_forceaptuptime)
            self.usersettings()

    def clearBoxes(self):
        self.EditorListStore.clear()
        self.PardusAppListStore.clear()
        for row in self.HomeCategoryFlowBox:
            self.HomeCategoryFlowBox.remove(row)
        for row in self.MostDownFlowBox:
            self.MostDownFlowBox.remove(row)
        for row in self.MostRateFlowBox:
            self.MostRateFlowBox.remove(row)
        for row in self.LastAddedFlowBox:
            self.LastAddedFlowBox.remove(row)

    def setAvailableApps(self, available, hideextapps):
        newlist = []
        for app in self.fullapplist:
            inrepo = False
            incodename = False
            inexternalrepo = False

            if available:
                if self.Package.isinstalled(app["name"]) is not None:
                    inrepo = True
                for code in app["codename"]:
                    if code["name"] == self.UserSettings.usercodename:
                        incodename = True
            else:
                inrepo = True
                incodename = True

            if not hideextapps and app["external"]:
                inexternalrepo = True

            if hideextapps and app["external"]:
                inrepo = False
                incodename = False
                inexternalrepo = False

            if inrepo or incodename or inexternalrepo:
                newlist.append(app)

        self.applist = newlist

        if hideextapps:  # control category list too
            newlist = []
            for cat in self.fullcatlist:
                if cat["external"] is False:
                    newlist.append(cat)
            self.catlist = newlist
        else:
            self.catlist = self.fullcatlist

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

    def on_prefcorrectbutton_clicked(self, button):
        self.prefstack.set_visible_child_name("confirm")

    def on_prefconfirm_cancelbutton_clicked(self, button):
        self.prefstack.set_visible_child_name("main")

    def on_prefconfirm_acceptbutton_clicked(self, button):
        command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/SysActions.py",
                   "correctsourceslist"]

        self.startSysProcess(command)
        self.prefstack.set_visible_child_name("main")
        self.correctsourcesclicked = True

    def on_bottomerrorbutton_clicked(self, button):
        self.bottomrevealer.set_reveal_child(False)

    def on_dLicense_activate_link(self, label, url):
        self.licensePopover.popup()

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

    def on_retrybutton_clicked(self, button):
        self.mainstack.set_visible_child_name("splash")
        p1 = threading.Thread(target=self.worker)
        p1.daemon = True
        p1.start()

    def on_mdabutton_clicked(self, button):
        self.menubackbutton.set_sensitive(True)
        if self.sortPardusAppsCombo.get_active() != 1:
            self.mda_clicked = True
        self.PardusCurrentCategoryString = "all"
        self.PardusCurrentCategoryIcon = "all"
        if self.UserSettings.config_usi:
            pixbuf = self.getServerCatIcon(self.PardusCurrentCategoryIcon, 32)
        else:
            pixbuf = self.getSystemCatIcon(self.PardusCurrentCategoryIcon, 32)
        self.NavCategoryImage.set_from_pixbuf(pixbuf)
        self.NavCategoryLabel.set_text(_("all").title())
        if self.sortPardusAppsCombo.get_active != 1:
            self.sortPardusAppsCombo.set_active(1)
        if self.pardusicb.get_active():
            self.pardusicb.set_active(False)
        self.PardusCategoryFilter.refilter()
        self.homestack.set_visible_child_name("pardusapps")

    def on_mrabutton_clicked(self, button):
        self.menubackbutton.set_sensitive(True)
        if self.sortPardusAppsCombo.get_active() != 2:
            self.mra_clicked = True
        self.PardusCurrentCategoryString = "all"
        self.PardusCurrentCategoryIcon = "all"
        if self.UserSettings.config_usi:
            pixbuf = self.getServerCatIcon(self.PardusCurrentCategoryIcon, 32)
        else:
            pixbuf = self.getSystemCatIcon(self.PardusCurrentCategoryIcon, 32)
        self.NavCategoryImage.set_from_pixbuf(pixbuf)
        self.NavCategoryLabel.set_text(_("all").title())
        if self.sortPardusAppsCombo.get_active != 2:
            self.sortPardusAppsCombo.set_active(2)
        if self.pardusicb.get_active():
            self.pardusicb.set_active(False)
        self.PardusCategoryFilter.refilter()
        self.homestack.set_visible_child_name("pardusapps")

    def on_labutton_clicked(self, button):
        self.menubackbutton.set_sensitive(True)
        if self.sortPardusAppsCombo.get_active() != 3:
            self.la_clicked = True
        self.PardusCurrentCategoryString = "all"
        self.PardusCurrentCategoryIcon = "all"
        if self.UserSettings.config_usi:
            pixbuf = self.getServerCatIcon(self.PardusCurrentCategoryIcon, 32)
        else:
            pixbuf = self.getSystemCatIcon(self.PardusCurrentCategoryIcon, 32)
        self.NavCategoryImage.set_from_pixbuf(pixbuf)
        self.NavCategoryLabel.set_text(_("all").title())
        if self.sortPardusAppsCombo.get_active != 3:
            self.sortPardusAppsCombo.set_active(3)
        if self.pardusicb.get_active():
            self.pardusicb.set_active(False)
        self.PardusCategoryFilter.refilter()
        self.homestack.set_visible_child_name("pardusapps")

    def actionPackage(self, appname, command):

        self.inprogress = True
        self.topspinner.start()

        ui_appname = self.getActiveAppOnUI()

        if ui_appname == appname:
            self.dActionButton.set_sensitive(False)
            self.dActionButton.set_image(Gtk.Image.new_from_icon_name("process-working-symbolic", Gtk.IconSize.BUTTON))
            self.raction.set_sensitive(False)
            self.raction.set_image(Gtk.Image.new_from_icon_name("process-working-symbolic", Gtk.IconSize.BUTTON))

        self.actionedappname = appname
        self.actionedcommand = command
        self.actionedappdesktop = self.desktop_file
        self.isinstalled = self.Package.isinstalled(self.actionedappname)

        if self.isinstalled is True:
            if ui_appname == appname:
                self.dActionButton.set_label(_(" Removing"))
                self.raction.set_label(_(" Removing"))
            command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py", "remove",
                       self.actionedcommand]
        elif self.isinstalled is False:
            if ui_appname == appname:
                self.dActionButton.set_label(_(" Installing"))
                self.raction.set_label(_(" Installing"))
            command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py", "install",
                       self.actionedcommand]
        else:
            print("actionPackage func error")

        self.pid = self.startProcess(command)

    def actionEnablePackage(self, appname):
        self.actionedenablingappname = appname
        self.actionedenablingappdesktop = self.desktop_file
        self.actionedenablingappcommand = self.command
        self.dActionButton.set_label(_(" Activating"))
        command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/SysActions.py", "externalrepo",
                   self.external["repokey"], self.external["reposlist"], self.external["reponame"]]
        self.expid = self.startSysProcess(command)

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
        print(line)
        if self.updateclicked:
            self.updatetextview.get_buffer().insert(self.updatetextview.get_buffer().get_end_iter(), line)
            self.updatetextview.scroll_to_iter(self.updatetextview.get_buffer().get_end_iter(), 0.0, False, 0.0, 0.0)
        return True

    def onProcessStderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False

        line = source.readline()

        print(line)

        if not self.updateclicked:
            if "dlstatus" in line:
                percent = line.split(":")[2].split(".")[0]
                self.progresstextlabel.set_text(
                    "{} | {} : {} %".format(self.actionedappname, _("Downloading"), percent))
            elif "pmstatus" in line:
                percent = line.split(":")[2].split(".")[0]
                if self.isinstalled:
                    self.progresstextlabel.set_text(
                        "{} | {} : {} %".format(self.actionedappname, _("Removing"), percent))
                else:
                    self.progresstextlabel.set_text(
                        "{} | {} : {} %".format(self.actionedappname, _("Installing"), percent))
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

            cachestatus = self.Package.updatecache()

            # print("Cache Status: {}, Package Cache Status: {}".format(cachestatus, self.Package.controlPackageCache(self.actionedappname)))

            if status == 0 and not self.error and cachestatus:
                if self.Package.controlPackageCache(self.actionedappname):
                    self.notify()
                    self.sendDownloaded(self.actionedappname)
                else:
                    if self.isinstalled:
                        self.notify()

            self.control_myapps(self.actionedappname, self.actionedappdesktop, status, self.error, cachestatus)

            self.controlView(self.actionedappname, self.actionedappdesktop, self.actionedcommand)

            ui_appname = self.getActiveAppOnUI()
            if ui_appname == self.actionedappname:
                if cachestatus and self.Package.controlPackageCache(ui_appname):
                    self.dActionButton.set_sensitive(True)
                    self.raction.set_sensitive(True)

            self.topspinner.stop()
            print("Exit Code : {}".format(status))

            self.inprogress = False

            self.queue.pop(0)
            self.QueueListBox.remove(self.QueueListBox.get_row_at_index(0))
            if len(self.queue) > 0:
                self.actionPackage(self.queue[0]["name"], self.queue[0]["command"])
                # Update QueueListBox's first element too
                queuecancelbutton = self.QueueListBox.get_row_at_index(0).get_children()[0].get_children()[3]
                queuecancelbutton.set_sensitive(False)
                queuecancelbutton.set_tooltip_text(_("You cannot cancel because the application is in progress."))
                queueactlabel = self.QueueListBox.get_row_at_index(0).get_children()[0].get_children()[2]
                if self.Package.isinstalled(self.actionedappname):
                    queueactlabel.set_markup("<span color='#e01b24'>{}</span>".format(_("Removing")))
                else:
                    queueactlabel.set_markup("<span color='#3584e4'>{}</span>".format(_("Installing")))
            else:
                self.bottomrevealer.set_reveal_child(False)
                if not self.error:
                    self.progresstextlabel.set_text("")
                    self.queuestack.set_visible_child_name("completed")

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

    def controlView(self, actionedappname, actionedappdesktop, actionedappcommand):
        selected_items = self.PardusAppsIconView.get_selected_items()
        editor_selected_items = self.EditorAppsIconView.get_selected_items()

        if len(selected_items) == 1:
            treeiter = self.PardusCategoryFilter.get_iter(selected_items[0])
            appname = self.PardusCategoryFilter.get(treeiter, 1)[0]
            print("in controlView " + appname)
            if appname == actionedappname:
                self.updateActionButtons(1, actionedappname, actionedappdesktop, actionedappcommand)

        if len(editor_selected_items) == 1:
            treeiter = self.EditorListStore.get_iter(editor_selected_items[0])
            appname = self.EditorListStore.get(treeiter, 1)[0]
            print("in controlView " + appname)
            if appname == actionedappname:
                self.updateActionButtons(1, actionedappname, actionedappdesktop, actionedappcommand)

        if self.frommostapps:
            if self.mostappname:
                if self.mostappname == actionedappname:
                    self.updateActionButtons(1, actionedappname, actionedappdesktop, actionedappcommand)
            else:
                if self.detailsappname == actionedappname:
                    self.updateActionButtons(1, actionedappname, actionedappdesktop, actionedappcommand)

        if self.fromrepoapps:
            if self.repoappname == actionedappname:
                self.updateActionButtons(2, actionedappname, actionedappdesktop, actionedappcommand)

            # Updating status tick of repo apps
            try:
                for row in self.searchstore:
                    installstatus = self.Package.isinstalled(row[0])
                    row[3] = installstatus
            except:
                pass

    def updateActionButtons(self, repo, actionedappname, actionedappdesktop, actionedappcommand):
        if repo == 1:  # pardus apps
            self.fromexternal = False
            if self.Package.isinstalled(actionedappname) is True:
                self.dActionButton.set_sensitive(True)
                if self.dActionButton.get_style_context().has_class("suggested-action"):
                    self.dActionButton.get_style_context().remove_class("suggested-action")
                self.dActionButton.get_style_context().add_class("destructive-action")
                self.dActionButton.set_label(_(" Uninstall"))
                self.dActionButton.set_image(Gtk.Image.new_from_icon_name("user-trash-symbolic", Gtk.IconSize.BUTTON))

                if actionedappdesktop != "" and actionedappdesktop is not None:
                    self.dOpenButton.set_visible(True)

                self.wpcformcontrolLabel.set_markup("")

                sizethread1 = threading.Thread(target=self.size_worker_thread, daemon=True)
                sizethread1.start()

            elif self.Package.isinstalled(actionedappname) is False:
                self.dActionButton.set_sensitive(True)
                if self.dActionButton.get_style_context().has_class("destructive-action"):
                    self.dActionButton.get_style_context().remove_class("destructive-action")
                self.dActionButton.get_style_context().add_class("suggested-action")
                self.dActionButton.set_label(_(" Install"))
                self.dActionButton.set_image(
                    Gtk.Image.new_from_icon_name("document-save-symbolic", Gtk.IconSize.BUTTON))

                self.dOpenButton.set_visible(False)

                self.wpcformcontrolLabel.set_markup(
                    "<span color='red'>{}</span>".format(_("You need to install the application")))

                sizethread2 = threading.Thread(target=self.size_worker_thread, daemon=True, args=(actionedappcommand, ))
                sizethread2.start()

            else:
                if self.external:
                    if self.external["externalrepo"]:
                        self.fromexternal = True
                        self.dActionButton.set_sensitive(True)
                        self.dActionButton.set_label(_("Enable Repo"))
                        self.dActionButton.set_image(
                            Gtk.Image.new_from_icon_name("list-add-symbolic", Gtk.IconSize.BUTTON))
                else:
                    self.dAptUpdateButton.set_visible(True)
                    if self.aptupdateclicked:
                        self.dAptUpdateBox.set_visible(True)
                        self.dAptUpdateInfoLabel.set_visible(True)

                    self.dActionButton.set_label(_(" Not Found"))
                    self.dActionButton.set_image(
                        Gtk.Image.new_from_icon_name("dialog-warning-symbolic", Gtk.IconSize.BUTTON))
                    self.dOpenButton.set_visible(False)

                    self.dActionButton.set_sensitive(False)
                    if self.dActionButton.get_style_context().has_class("destructive-action"):
                        self.dActionButton.get_style_context().remove_class("destructive-action")
                    if self.dActionButton.get_style_context().has_class("suggested-action"):
                        self.dActionButton.get_style_context().remove_class("suggested-action")

                self.dActionButton.set_tooltip_text(None)
                self.dSize.set_markup(_("None"))
                self.dSizeTitle.set_text(_("Download Size"))
                self.dSizeGrid.set_tooltip_text(None)

        if repo == 2:  # repo apps
            if self.Package.isinstalled(actionedappname):
                if self.raction.get_style_context().has_class("suggested-action"):
                    self.raction.get_style_context().remove_class("suggested-action")
                self.raction.get_style_context().add_class("destructive-action")
                self.raction.set_label(_(" Uninstall"))
                self.raction.set_image(Gtk.Image.new_from_icon_name("user-trash-symbolic", Gtk.IconSize.BUTTON))
            else:
                if self.raction.get_style_context().has_class("destructive-action"):
                    self.raction.get_style_context().remove_class("destructive-action")
                self.raction.get_style_context().add_class("suggested-action")
                self.raction.set_label(_(" Install"))
                self.raction.set_image(Gtk.Image.new_from_icon_name("document-save-symbolic", Gtk.IconSize.BUTTON))

    def control_myapps(self, actionedappname, actionedappdesktop, status, error, cachestatus):
        print("in control_myapps")
        if self.homestack.get_visible_child_name() == "myapps":
            if status == 0 and not error and cachestatus:
                print("in homestack myapps")
                for row in self.MyAppsListBox:
                    if row.get_children()[0].name == actionedappdesktop:
                        self.MyAppsListBox.remove(row)
                if self.myappsstack.get_visible_child_name() == "details" and actionedappname == self.myapp_toremove:
                    print("in myappsstack details actionedappname status=0")
                    self.ui_myapps_uninstall_button.set_sensitive(False)
            else:
                if self.myappsstack.get_visible_child_name() == "details" and actionedappname == self.myapp_toremove:
                    print("in myappsstack details actionedappname status!=0")
                    self.ui_myapps_uninstall_button.set_sensitive(True)

    def notify(self, message_summary="", message_body=""):
        try:
            if Notify.is_initted():
                Notify.uninit()

            if message_summary == "" and message_body == "":
                Notify.init(self.actionedappname)
                if self.isinstalled:
                    notification = Notify.Notification.new(
                        self.getPrettyName(self.actionedappname, False) + _(" Removed"))
                else:
                    notification = Notify.Notification.new(
                        self.getPrettyName(self.actionedappname, False) + _(" Installed"))
                if self.UserSettings.config_usi:
                    pixbuf = self.getServerAppIcon(self.actionedappname, 96, notify=True)
                else:
                    pixbuf = self.getSystemAppIcon(self.actionedappname, 96, notify=True)
                notification.set_icon_from_pixbuf(pixbuf)
            else:
                Notify.init(message_summary)
                notification = Notify.Notification.new(message_summary, message_body, "pardus-software")
            notification.show()
        except Exception as e:
            print("{}".format(e))

    def sendDownloaded(self, appname):
        try:
            installed = self.Package.isinstalled(appname)
            if installed is None:
                installed = False
            version = self.Package.installedVersion(appname)
            if version is None:
                version = ""
            dic = {"mac": self.mac, "app": appname, "installed": installed, "appversion": version,
                   "distro": self.UserSettings.userdistro}
            self.AppRequest.send("POST", self.Server.serverurl + self.Server.serversenddownload, dic)
        except Exception as e:
            print("sendDownloaded Error: {}".format(e))

    def startSysProcess(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(params, flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_output=True, standard_error=True)
        GLib.io_add_watch(GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.onSysProcessStdout)
        GLib.io_add_watch(GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.onSysProcessStderr)
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, self.onSysProcessExit)

        return pid

    def onSysProcessStdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        print(line)
        return True

    def onSysProcessStderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        print(line)
        return True

    def onSysProcessExit(self, pid, status):
        if self.externalactioned:
            ui_appname = self.getActiveAppOnUI()
            if ui_appname == self.actionedenablingappname:
                self.dActionButton.set_sensitive(True)
                self.raction.set_sensitive(True)
                self.activating_spinner.stop()
                self.activatestack.set_visible_child_name("main")
                if status == 0:
                    self.externalactioned = False
                else:  # if cancelled then may be retry
                    self.externalactioned = True
            else:
                self.externalactioned = False

            self.Package.updatecache()

            if status == 0 and not self.error:
                self.notify(message_summary=_("Pardus Software Center"), message_body=_("Repo Activation Completed"))

            self.controlView(self.actionedenablingappname, self.actionedenablingappdesktop, self.actionedenablingappcommand)

        if self.correctsourcesclicked and status == 0:
            self.preflabel.set_markup("{}\n{}\n<span weight='bold'>{}</span>".format(
                _("Fixing of system package manager sources list is done."),
                _("You can now update package manager cache."),
                _("Pardus Software Center > Menu > Updates > Update Package Cache")))

        self.correctsourcesclicked = False

        if self.aptupdateclicked:
            print("apt update done (detail page), status code : {}".format(status))
            self.dAptUpdateButton.set_sensitive(True)
            self.dAptUpdateSpinner.stop()
            self.Package.updatecache()
            self.controlView(self.appname, self.desktop_file, self.command)
            if status == 0:
                self.dAptUpdateBox.set_visible(False)
                self.dAptUpdateButton.set_visible(False)
                self.dAptUpdateInfoLabel.set_visible(True)
                self.dAptUpdateInfoLabel.set_text("")
            elif status == 32256:
                self.dAptUpdateInfoLabel.set_visible(True)
                self.dAptUpdateInfoLabel.set_text("")
                print("wrong password on apt update (detail page)")
            else:
                self.dAptUpdateBox.set_visible(True)
                self.dAptUpdateInfoLabel.set_visible(True)
                self.dAptUpdateInfoLabel.set_markup("<span color='red'>{}{}</span>".format(
                    _("An error occurred while updating the package cache. Exit Code : "), status))
            self.aptupdateclicked = False

        print("SysProcess Exit Code : {}".format(status))

    def startAptUpdateProcess(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(params, flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_output=True, standard_error=True)
        GLib.io_add_watch(GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.onAptUpdateProcessStdout)
        GLib.io_add_watch(GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.onAptUpdateProcessStderr)
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, self.onAptUpdateProcessExit)

        return pid

    def onAptUpdateProcessStdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        print(line)
        return True

    def onAptUpdateProcessStderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        print(line)
        return True

    def onAptUpdateProcessExit(self, pid, status):
        self.Package.updatecache()
        self.headerAptUpdateSpinner.set_visible(False)
        self.headerAptUpdateSpinner.stop()
        if status == 0:
            try:
                timestamp = int(datetime.now().timestamp())
            except Exception as e:
                print("timestamp Error: {}".format(e))
                timestamp = 0
            self.UserSettings.writeConfig(self.UserSettings.config_usi, self.UserSettings.config_ea,
                                          self.UserSettings.config_saa, self.UserSettings.config_hera,
                                          self.UserSettings.config_icon, self.UserSettings.config_sgc,
                                          self.UserSettings.config_udt, self.UserSettings.config_aptup,
                                          timestamp, self.UserSettings.config_forceaptuptime)

    def on_tryfixButton_clicked(self, button):
        self.tryfixstack.set_visible_child_name("info")

    def on_tryfixconfirm_clicked(self, button):
        command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/SysActions.py",
                   "fixapt"]
        self.tryfixstack.set_visible_child_name("main")
        self.tryfixButton.set_sensitive(False)
        self.tryfixSpinner.start()
        self.startVteProcess(command)

    def on_tryfixcancel_clicked(self, button):
        self.tryfixstack.set_visible_child_name("main")

    def on_tryfixdone_clicked(self, button):
        self.homestack.set_visible_child_name("pardushome")

    def vte_event(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            if event.button.button == 3:
                widget.popup_for_device(None, None, None, None, None,
                                        event.button.button, event.time)
                return True
        return False

    def menu_action(self, widget, terminal):
        terminal.copy_clipboard()

    def startVteProcess(self, params):
        status, pid = self.runVteCommand(self.vteterm, params)
        return pid

    def onVteDone(self, obj, status):
        self.tryfixSpinner.stop()
        self.tryfixButton.set_sensitive(True)
        if status == 0:
            self.Package = Package()
            if self.Package.updatecache():
                self.tryfixstack.set_visible_child_name("done")
                self.isbroken = False
                self.Package.getApps()
                GLib.idle_add(self.topsearchbutton.set_sensitive, True)
                GLib.idle_add(self.menu_myapps.set_sensitive, True)
                GLib.idle_add(self.topbutton1.set_sensitive, True)
                GLib.idle_add(self.topbutton2.set_sensitive, True)
            else:
                self.tryfixstack.set_visible_child_name("error")
                self.isbroken = True
                print("Error while updating Cache")
        else:
            print("onVteDone status: {}".format(status))

    def runVteCommand(self, term, command):
        pty = Vte.Pty.new_sync(Vte.PtyFlags.DEFAULT)
        term.set_pty(pty)
        term.connect("child-exited", self.onVteDone)
        return term.spawn_sync(Vte.PtyFlags.DEFAULT,
                               os.environ['HOME'],
                               command,
                               [],
                               GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                               None,
                               None,
                               )
