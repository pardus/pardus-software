#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import grp
import locale
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from locale import getlocale
from locale import gettext as _

import gi
import netifaces
import psutil

locale.bindtextdomain('pardus-software', '/usr/share/locale')
locale.textdomain('pardus-software')

gi.require_version("GLib", "2.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Notify", "0.7")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Vte", "2.91")
from gi.repository import GLib, Gtk, GObject, Notify, GdkPixbuf, Gdk, Vte, Pango

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
from Utils import Utils
from Logger import Logger


class MainWindow(object):
    def __init__(self, application):
        self.Application = application

        self.Logger = Logger(__name__)

        self.MainWindowUIFileName = os.path.dirname(os.path.abspath(__file__)) + "/../ui/MainWindow.glade"
        try:
            self.GtkBuilder = Gtk.Builder.new_from_file(self.MainWindowUIFileName)
            self.GtkBuilder.connect_signals(self)
        except GObject.GError as e:
            self.Logger.warning("Error reading GUI file")
            self.Logger.exception("{}".format(e))
            raise

        self.applist = []
        self.catlist = []

        self.locale = self.getLocale()
        self.Logger.info("{}".format(self.locale))

        self.parduspixbuf = Gtk.IconTheme.new()
        self.parduspixbuf.set_custom_theme("pardus")

        self.error = False
        self.dpkglockerror = False
        self.dpkgconferror = False
        self.dpkglockerror_message = ""
        self.error_message = ""

        try:
            self.missing_pixbuf = Gtk.IconTheme.get_default().load_icon("image-missing", 96,
                                                                        Gtk.IconLookupFlags(16))
        except:
            self.missing_pixbuf = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", 96,
                                                                        Gtk.IconLookupFlags(16))

        self.staron = GdkPixbuf.Pixbuf.new_from_file_at_size(
            os.path.dirname(os.path.abspath(__file__)) + "/../images/rating-1.svg", 24, 24)
        self.staroff = GdkPixbuf.Pixbuf.new_from_file_at_size(
            os.path.dirname(os.path.abspath(__file__)) + "/../images/rating-0.svg", 24, 24)

        self.staron_03 = GdkPixbuf.Pixbuf.new_from_file_at_size(
            os.path.dirname(os.path.abspath(__file__)) + "/../images/rating-0-3.svg", 24, 24)
        self.staron_05 = GdkPixbuf.Pixbuf.new_from_file_at_size(
            os.path.dirname(os.path.abspath(__file__)) + "/../images/rating-0-5.svg", 24, 24)
        self.staron_08 = GdkPixbuf.Pixbuf.new_from_file_at_size(
            os.path.dirname(os.path.abspath(__file__)) + "/../images/rating-0-8.svg", 24, 24)

        self.staronhover = GdkPixbuf.Pixbuf.new_from_file_at_size(
            os.path.dirname(os.path.abspath(__file__)) + "/../images/rating-hover-full.svg", 24, 24)
        self.staroffhover = GdkPixbuf.Pixbuf.new_from_file_at_size(
            os.path.dirname(os.path.abspath(__file__)) + "/../images/rating-hover-empty.svg", 24, 24)

        self.cstaron = GdkPixbuf.Pixbuf.new_from_file_at_size(
            os.path.dirname(os.path.abspath(__file__)) + "/../images/rating-1.svg", 16, 16)
        self.cstaroff = GdkPixbuf.Pixbuf.new_from_file_at_size(
            os.path.dirname(os.path.abspath(__file__)) + "/../images/rating-0.svg", 16, 16)

        self.gcstaron = GdkPixbuf.Pixbuf.new_from_file_at_size(
            os.path.dirname(os.path.abspath(__file__)) + "/../images/rating-1.svg", 16, 16)
        self.gcstaroff = GdkPixbuf.Pixbuf.new_from_file_at_size(
            os.path.dirname(os.path.abspath(__file__)) + "/../images/rating-0.svg", 16, 16)

        self.wpcstaron = GdkPixbuf.Pixbuf.new_from_file_at_size(
            os.path.dirname(os.path.abspath(__file__)) + "/../images/rating-1.svg", 38, 38)
        self.wpcstaroff = GdkPixbuf.Pixbuf.new_from_file_at_size(
            os.path.dirname(os.path.abspath(__file__)) + "/../images/rating-0.svg", 38, 38)

        self.isPardusSearching = False
        self.isRepoSearching = False

        self.RepoCategoryListBox = self.GtkBuilder.get_object("RepoCategoryListBox")

        self.HomeCategoryFlowBox = self.GtkBuilder.get_object("HomeCategoryFlowBox")
        self.SubCategoryFlowBox = self.GtkBuilder.get_object("SubCategoryFlowBox")
        self.MostDownFlowBox = self.GtkBuilder.get_object("MostDownFlowBox")
        self.MostRateFlowBox = self.GtkBuilder.get_object("MostRateFlowBox")
        self.LastAddedFlowBox = self.GtkBuilder.get_object("LastAddedFlowBox")

        self.MyAppsListBox = self.GtkBuilder.get_object("MyAppsListBox")
        self.MyAppsListBox.set_filter_func(self.myapps_filter_func)

        self.hometotaldc = self.GtkBuilder.get_object("hometotaldc")
        self.hometotalrc = self.GtkBuilder.get_object("hometotalrc")
        self.statstotaldc = self.GtkBuilder.get_object("statstotaldc")
        self.statstotalrc = self.GtkBuilder.get_object("statstotalrc")
        self.statsweblabel = self.GtkBuilder.get_object("statsweblabel")

        self.pardus_searchentry = self.GtkBuilder.get_object("pardus_searchentry")
        self.repo_searchentry = self.GtkBuilder.get_object("repo_searchentry")
        self.myapps_searchentry = self.GtkBuilder.get_object("myapps_searchentry")
        self.repo_searchbutton = self.GtkBuilder.get_object("repo_searchbutton")
        self.reposearch_buttonbox = self.GtkBuilder.get_object("reposearch_buttonbox")
        self.reposearch_buttonbox.set_homogeneous(False)
        self.topsearchbutton = self.GtkBuilder.get_object("topsearchbutton")
        self.toprevealer = self.GtkBuilder.get_object("toprevealer")
        self.bottomrevealer = self.GtkBuilder.get_object("bottomrevealer")

        self.bottomerrorlabel = self.GtkBuilder.get_object("bottomerrorlabel")
        self.bottomerrorbutton = self.GtkBuilder.get_object("bottomerrorbutton")

        self.bottominterruptlabel = self.GtkBuilder.get_object("bottominterruptlabel")
        self.bottominterrupt_fix_button = self.GtkBuilder.get_object("bottominterrupt_fix_button")
        self.bottominterrupthide_button = self.GtkBuilder.get_object("bottominterrupthide_button")

        self.pop_interruptinfo_label = self.GtkBuilder.get_object("pop_interruptinfo_label")
        self.pop_interruptinfo_spinner = self.GtkBuilder.get_object("pop_interruptinfo_spinner")
        self.pop_interruptinfo_ok_button = self.GtkBuilder.get_object("pop_interruptinfo_ok_button")
        self.interruptpopover = self.GtkBuilder.get_object("interruptpopover")

        self.bottomerrordetails_popover = self.GtkBuilder.get_object("bottomerrordetails_popover")
        self.bottomerrordetails_label = self.GtkBuilder.get_object("bottomerrordetails_label")
        self.bottomerrordetails_button = self.GtkBuilder.get_object("bottomerrordetails_button")

        self.sortPardusAppsCombo = self.GtkBuilder.get_object("sortPardusAppsCombo")
        self.SubCatCombo = self.GtkBuilder.get_object("SubCatCombo")
        self.ui_showapps_buttonbox = self.GtkBuilder.get_object("ui_showapps_buttonbox")
        self.ui_showall_button = self.GtkBuilder.get_object("ui_showall_button")
        self.ui_showinstalled_button = self.GtkBuilder.get_object("ui_showinstalled_button")
        self.ui_shownotinstalled_button = self.GtkBuilder.get_object("ui_shownotinstalled_button")
        self.ui_showappcount_label = self.GtkBuilder.get_object("ui_showappcount_label")

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
        self.dActionInfoButton = self.GtkBuilder.get_object("dActionInfoButton")
        self.dActionCancelButton = self.GtkBuilder.get_object("dActionCancelButton")
        self.dActionButtonBox = self.GtkBuilder.get_object("dActionButtonBox")
        self.dActionButtonBox.set_homogeneous(False)
        self.dOpenButton = self.GtkBuilder.get_object("dOpenButton")
        self.dAptUpdateButton = self.GtkBuilder.get_object("dAptUpdateButton")
        self.dAptUpdateInfoLabel = self.GtkBuilder.get_object("dAptUpdateInfoLabel")
        self.dAptUpdateSpinner = self.GtkBuilder.get_object("dAptUpdateSpinner")
        self.dAptUpdateBox = self.GtkBuilder.get_object("dAptUpdateBox")
        self.dDisclaimerButton = self.GtkBuilder.get_object("dDisclaimerButton")
        self.DisclaimerPopover = self.GtkBuilder.get_object("DisclaimerPopover")
        self.RequiredChangesPopover = self.GtkBuilder.get_object("RequiredChangesPopover")
        self.dapp_packagename_box = self.GtkBuilder.get_object("dapp_packagename_box")
        self.dapp_toremove_box = self.GtkBuilder.get_object("dapp_toremove_box")
        self.dapp_toinstall_box = self.GtkBuilder.get_object("dapp_toinstall_box")
        self.dapp_broken_box = self.GtkBuilder.get_object("dapp_broken_box")
        self.dapp_fsize_box = self.GtkBuilder.get_object("dapp_fsize_box")
        self.dapp_dsize_box = self.GtkBuilder.get_object("dapp_dsize_box")
        self.dapp_isize_box = self.GtkBuilder.get_object("dapp_isize_box")
        self.dapp_packagename_label = self.GtkBuilder.get_object("dapp_packagename_label")
        self.dapp_toremove_label = self.GtkBuilder.get_object("dapp_toremove_label")
        self.dapp_toinstall_label = self.GtkBuilder.get_object("dapp_toinstall_label")
        self.dapp_broken_label = self.GtkBuilder.get_object("dapp_broken_label")
        self.dapp_fsize_label = self.GtkBuilder.get_object("dapp_fsize_label")
        self.dapp_dsize_label = self.GtkBuilder.get_object("dapp_dsize_label")
        self.dapp_isize_label = self.GtkBuilder.get_object("dapp_isize_label")

        self.dDescriptionLabel = self.GtkBuilder.get_object("dDescriptionLabel")
        self.dPackage = self.GtkBuilder.get_object("dPackage")
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
        self.wpcinfoLabel = self.GtkBuilder.get_object("wpcinfoLabel")
        self.wpcComment = self.GtkBuilder.get_object("wpcComment")
        self.wpcAuthor = self.GtkBuilder.get_object("wpcAuthor")
        self.wpcSendButton = self.GtkBuilder.get_object("wpcSendButton")
        self.wpcgetnameLabel = self.GtkBuilder.get_object("wpcgetnameLabel")
        self.wpcgetcommentLabel = self.GtkBuilder.get_object("wpcgetcommentLabel")
        self.wpcresultLabel = self.GtkBuilder.get_object("wpcresultLabel")
        self.wpcformcontrolLabel = self.GtkBuilder.get_object("wpcformcontrolLabel")
        self.addCommentInfoLabel = self.GtkBuilder.get_object("addCommentInfoLabel")
        self.addCommentButton = self.GtkBuilder.get_object("addCommentButton")
        self.wpcCommentBox = self.GtkBuilder.get_object("wpcCommentBox")
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
        self.ractioninfo = self.GtkBuilder.get_object("ractioninfo")
        self.raction_buttonbox = self.GtkBuilder.get_object("raction_buttonbox")
        self.raction_buttonbox.set_homogeneous(False)
        self.rpackage = self.GtkBuilder.get_object("rpackage_name")
        self.rtitle = self.GtkBuilder.get_object("rtitle")
        self.rdetail = self.GtkBuilder.get_object("rdetail")
        self.r_maintainername = self.GtkBuilder.get_object("r_maintainername")
        self.r_maintainermail = self.GtkBuilder.get_object("r_maintainermail")
        self.r_homepage = self.GtkBuilder.get_object("r_homepage")
        self.r_section = self.GtkBuilder.get_object("r_section")
        self.r_architecture = self.GtkBuilder.get_object("r_architecture")
        self.r_version = self.GtkBuilder.get_object("r_version")
        self.r_origin = self.GtkBuilder.get_object("r_origin")
        self.rstack = self.GtkBuilder.get_object("rstack")

        self.repo_required_changes_popover = self.GtkBuilder.get_object("repo_required_changes_popover")
        self.repo_required_stack = self.GtkBuilder.get_object("repo_required_stack")
        self.repo_required_spinner = self.GtkBuilder.get_object("repo_required_spinner")
        self.rapp_packagename_box = self.GtkBuilder.get_object("rapp_packagename_box")
        self.rapp_package_broken_box = self.GtkBuilder.get_object("rapp_package_broken_box")
        self.rapp_toremove_box = self.GtkBuilder.get_object("rapp_toremove_box")
        self.rapp_toinstall_box = self.GtkBuilder.get_object("rapp_toinstall_box")
        self.rapp_broken_box = self.GtkBuilder.get_object("rapp_broken_box")
        self.rapp_size_box = self.GtkBuilder.get_object("rapp_size_box")
        self.rapp_fsize_box = self.GtkBuilder.get_object("rapp_fsize_box")
        self.rapp_dsize_box = self.GtkBuilder.get_object("rapp_dsize_box")
        self.rapp_isize_box = self.GtkBuilder.get_object("rapp_isize_box")
        self.rapp_packagename_label = self.GtkBuilder.get_object("rapp_packagename_label")
        self.rapp_toremove_label = self.GtkBuilder.get_object("rapp_toremove_label")
        self.rapp_toinstall_label = self.GtkBuilder.get_object("rapp_toinstall_label")
        self.rapp_broken_label = self.GtkBuilder.get_object("rapp_broken_label")
        self.rapp_fsize_label = self.GtkBuilder.get_object("rapp_fsize_label")
        self.rapp_dsize_label = self.GtkBuilder.get_object("rapp_dsize_label")
        self.rapp_isize_label = self.GtkBuilder.get_object("rapp_isize_label")

        self.store_button = self.GtkBuilder.get_object("store_button")
        self.store_button.get_style_context().add_class("suggested-action")
        self.repo_button = self.GtkBuilder.get_object("repo_button")
        self.myapps_button = self.GtkBuilder.get_object("myapps_button")
        self.updates_button = Gtk.Button.new()
        self.updates_button.set_label(_("Updates"))
        self.updates_button.connect("clicked", self.on_updates_button_clicked)
        self.queue_button = self.GtkBuilder.get_object("queue_button")
        self.header_buttonbox = self.GtkBuilder.get_object("header_buttonbox")

        self.splashspinner = self.GtkBuilder.get_object("splashspinner")
        self.splashbar = self.GtkBuilder.get_object("splashbar")
        self.splashlabel = self.GtkBuilder.get_object("splashlabel")
        self.splashbarstatus = True

        self.upgrade_stack = self.GtkBuilder.get_object("upgrade_stack")
        self.upgrade_stack_spinnner = self.GtkBuilder.get_object("upgrade_stack_spinnner")
        self.upgradables_listbox = self.GtkBuilder.get_object("upgradables_listbox")
        self.upgrade_vte_sw = self.GtkBuilder.get_object("upgrade_vte_sw")
        self.upgrade_buttonbox = self.GtkBuilder.get_object("upgrade_buttonbox")
        self.upgrade_buttonbox.set_homogeneous(False)
        self.upgrade_options_popover = self.GtkBuilder.get_object("upgrade_options_popover")
        self.upgrade_options_defaults_button = self.GtkBuilder.get_object("upgrade_options_defaults_button")
        self.upgrade_new_conf_radiobutton = self.GtkBuilder.get_object("upgrade_new_conf_radiobutton")
        self.upgrade_old_conf_radiobutton = self.GtkBuilder.get_object("upgrade_old_conf_radiobutton")
        self.upgrade_ask_conf_radiobutton = self.GtkBuilder.get_object("upgrade_ask_conf_radiobutton")
        self.upgrade_withyq_radiobutton = self.GtkBuilder.get_object("upgrade_withyq_radiobutton")
        self.upgrade_withoutyq_radiobutton = self.GtkBuilder.get_object("upgrade_withoutyq_radiobutton")
        self.upgrade_info_back_button = self.GtkBuilder.get_object("upgrade_info_back_button")
        self.upgrade_info_ok_button = self.GtkBuilder.get_object("upgrade_info_ok_button")
        self.upgrade_info_dpkgfix_button = self.GtkBuilder.get_object("upgrade_info_dpkgfix_button")
        self.upgrade_info_box = self.GtkBuilder.get_object("upgrade_info_box")
        self.upgrade_info_label = self.GtkBuilder.get_object("upgrade_info_label")
        self.upgrade_dsize_label = self.GtkBuilder.get_object("upgrade_dsize_label")
        self.upgrade_isize_label = self.GtkBuilder.get_object("upgrade_isize_label")
        self.upgrade_ucount_label = self.GtkBuilder.get_object("upgrade_ucount_label")
        self.upgrade_ncount_label = self.GtkBuilder.get_object("upgrade_ncount_label")
        self.upgrade_rcount_label = self.GtkBuilder.get_object("upgrade_rcount_label")
        self.upgrade_kcount_label = self.GtkBuilder.get_object("upgrade_kcount_label")
        self.upgrade_dsize_box = self.GtkBuilder.get_object("upgrade_dsize_box")
        self.upgrade_isize_box = self.GtkBuilder.get_object("upgrade_isize_box")
        self.upgrade_ucount_box = self.GtkBuilder.get_object("upgrade_ucount_box")
        self.upgrade_ncount_box = self.GtkBuilder.get_object("upgrade_ncount_box")
        self.upgrade_rcount_box = self.GtkBuilder.get_object("upgrade_rcount_box")
        self.upgrade_kcount_box = self.GtkBuilder.get_object("upgrade_kcount_box")

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
        self.ui_myapps_notfoundname_box = self.GtkBuilder.get_object("ui_myapps_notfoundname_box")
        self.ui_myapps_notfoundname_image = self.GtkBuilder.get_object("ui_myapps_notfoundname_image")
        self.ui_myapps_notfoundname_name = self.GtkBuilder.get_object("ui_myapps_notfoundname_name")
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
        self.MyAppsDetailsPopover = self.GtkBuilder.get_object("MyAppsDetailsPopover")
        self.MyAppsDetailsPopover.set_relative_to(self.MyAppsListBox)
        self.myapps_apps_sw = self.GtkBuilder.get_object("myapps_apps_sw")
        self.ma_maintainername = self.GtkBuilder.get_object("ma_maintainername")
        self.ma_maintainermail = self.GtkBuilder.get_object("ma_maintainermail")
        self.ma_homepage = self.GtkBuilder.get_object("ma_homepage")
        self.ma_version = self.GtkBuilder.get_object("ma_version")
        self.ma_origin = self.GtkBuilder.get_object("ma_origin")
        self.ma_size = self.GtkBuilder.get_object("ma_size")
        # self.ma_section = self.GtkBuilder.get_object("ma_section")
        # self.ma_architecture = self.GtkBuilder.get_object("ma_architecture")
        self.ma_action_buttonbox = self.GtkBuilder.get_object("ma_action_buttonbox")
        self.ma_action_button = self.GtkBuilder.get_object("ma_action_button")
        self.ma_action_info_button = self.GtkBuilder.get_object("ma_action_info_button")
        self.ma_action_buttonbox.set_homogeneous(False)

        # myapps remove popup
        self.ui_myapp_pop_stack = self.GtkBuilder.get_object("ui_myapp_pop_stack")
        self.ui_myapp_pop_spinner = self.GtkBuilder.get_object("ui_myapp_pop_spinner")
        self.ui_myapp_pop_sw = self.GtkBuilder.get_object("ui_myapp_pop_sw")

        self.ui_myapp_pop_app = self.GtkBuilder.get_object("ui_myapp_pop_app")
        self.ui_myapp_pop_package = self.GtkBuilder.get_object("ui_myapp_pop_package")
        self.ui_myapp_pop_icon = self.GtkBuilder.get_object("ui_myapp_pop_icon")
        self.ui_myapp_pop_uninstall_button = self.GtkBuilder.get_object("ui_myapp_pop_uninstall_button")

        self.ui_myapp_pop_toremove_label = self.GtkBuilder.get_object("ui_myapp_pop_toremove_label")
        self.ui_myapp_pop_toinstall_label = self.GtkBuilder.get_object("ui_myapp_pop_toinstall_label")
        self.ui_myapp_pop_broken_label = self.GtkBuilder.get_object("ui_myapp_pop_broken_label")
        self.ui_myapp_pop_fsize_label = self.GtkBuilder.get_object("ui_myapp_pop_fsize_label")
        self.ui_myapp_pop_dsize_label = self.GtkBuilder.get_object("ui_myapp_pop_dsize_label")
        self.ui_myapp_pop_isize_label = self.GtkBuilder.get_object("ui_myapp_pop_isize_label")

        self.ui_myapp_pop_disclaimer_label = self.GtkBuilder.get_object("ui_myapp_pop_disclaimer_label")

        self.ui_myapp_pop_notfound_image = self.GtkBuilder.get_object("ui_myapp_pop_notfound_image")
        self.ui_myapp_pop_notfound_name = self.GtkBuilder.get_object("ui_myapp_pop_notfound_name")

        self.ui_myapp_pop_toremove_box = self.GtkBuilder.get_object("ui_myapp_pop_toremove_box")
        self.ui_myapp_pop_toinstall_box = self.GtkBuilder.get_object("ui_myapp_pop_toinstall_box")
        self.ui_myapp_pop_broken_box = self.GtkBuilder.get_object("ui_myapp_pop_broken_box")
        self.ui_myapp_pop_fsize_box = self.GtkBuilder.get_object("ui_myapp_pop_fsize_box")
        self.ui_myapp_pop_dsize_box = self.GtkBuilder.get_object("ui_myapp_pop_dsize_box")
        self.ui_myapp_pop_isize_box = self.GtkBuilder.get_object("ui_myapp_pop_isize_box")

        self.ui_myapp_to_store_button = self.GtkBuilder.get_object("ui_myapp_to_store_button")

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
        if self.aboutdialog.get_titlebar() is None:
            about_headerbar = Gtk.HeaderBar.new()
            about_headerbar.set_show_close_button(True)
            about_headerbar.set_title(_("About Pardus Software Center"))
            about_headerbar.pack_start(Gtk.Image.new_from_icon_name("pardus-software", Gtk.IconSize.LARGE_TOOLBAR))
            about_headerbar.show_all()
            self.aboutdialog.set_titlebar(about_headerbar)

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
        self.prefcorrectbutton = self.GtkBuilder.get_object("prefcorrectbutton")
        self.ui_cache_size = self.GtkBuilder.get_object("ui_cache_size")
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
        self.passwordlessbutton = self.GtkBuilder.get_object("passwordlessbutton")

        self.menubackbutton = self.GtkBuilder.get_object("menubackbutton")

        self.updatecontrolbutton = self.GtkBuilder.get_object("updatecontrolbutton")
        self.updatetextview = self.GtkBuilder.get_object("updatetextview")
        self.updatespinner = self.GtkBuilder.get_object("updatespinner")

        self.updateerrorlabel = self.GtkBuilder.get_object("updateerrorlabel")

        self.residualtextview = self.GtkBuilder.get_object("residualtextview")
        self.removabletextview = self.GtkBuilder.get_object("removabletextview")
        self.upgradabletextview = self.GtkBuilder.get_object("upgradabletextview")

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

        self.PardusCommentScroll = self.GtkBuilder.get_object("PardusCommentScroll")
        self.GnomeTRCommentScroll = self.GtkBuilder.get_object("GnomeTRCommentScroll")
        self.GnomeENCommentScroll = self.GtkBuilder.get_object("GnomeENCommentScroll")

        self.statstack = self.GtkBuilder.get_object("statstack")
        self.statmainstack = self.GtkBuilder.get_object("statmainstack")
        self.stat_spinner = self.GtkBuilder.get_object("stat_spinner")
        self.stat_ilabel = self.GtkBuilder.get_object("stat_ilabel")
        self.stats1ViewPort = self.GtkBuilder.get_object("stats1ViewPort")
        self.stats2ViewPort = self.GtkBuilder.get_object("stats2ViewPort")
        self.stats3ViewPort = self.GtkBuilder.get_object("stats3ViewPort")
        self.matplot_error = _("matplotlib is not found")

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

        self.store_button_clicked = False

        self.PardusCategoryFilter = self.GtkBuilder.get_object("PardusCategoryFilter")
        self.PardusCategoryFilter.set_visible_func(self.PardusCategoryFilterFunction)

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

        self.mac = self.getMac()

        self.par_desc_more = self.GtkBuilder.get_object("par_desc_more")

        self.MainWindow = self.GtkBuilder.get_object("MainWindow")
        self.MainWindow.set_application(application)
        self.MainWindow.set_title(_("Pardus Software Center"))
        self.controlDisplay()
        self.mainstack.set_visible_child_name("splash")

        self.HeaderBarMenuButton.set_sensitive(False)
        self.menubackbutton.set_sensitive(False)
        self.store_button.set_sensitive(False)
        self.repo_button.set_sensitive(False)
        self.myapps_button.set_sensitive(False)
        self.topsearchbutton.set_sensitive(False)

        self.fromexternal = False
        self.externalactioned = False
        self.isinstalled = None
        self.correctsourcesclicked = False

        self.dpkgconfiguring = False

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
        self.fromqueue = False
        self.frommyapps = False
        self.mda_clicked = False
        self.mra_clicked = False
        self.la_clicked = False

        self.statisticsSetted = False
        self.matplot_install_clicked = False

        self.repoappsinit = False

        self.isbroken = False

        self.mostappname = None
        self.detailsappname = None
        self.queueappname = None
        self.myappname = None

        self.connection_error_after = False
        self.auto_apt_update_finished = False
        self.upgradables_page_setted = False
        self.upgrade_inprogress = False
        self.keep_ok_clicked = False

        self.applist = []
        self.fullapplist = []
        self.catlist = []
        self.fullcatlist = []
        self.upgradable_packages = []

        self.myapp_toremove_list = []
        self.myapp_toremove = ""
        self.myapp_toremove_desktop = ""

        self.important_packages = ["pardus-common-desktop", "pardus-xfce-desktop", "pardus-gnome-desktop",
                                   "pardus-edu-common-desktop", "pardus-edu-gnome-desktop", "eta-common-desktop",
                                   "eta-gnome-desktop", "eta-nonhid-gnome-desktop", "eta-gnome-desktop-other",
                                   "eta-nonhid-gnome-desktop-other", "xfce4-session", "gnome-session",
                                   "cinnamon", "cinnamon-session", "cinnamon-desktop-data", "eta-desktop"]

        self.i386_packages = ["wine"]

        self.prefback = "pardushome"
        self.prefback_preferences = None
        self.prefback_statistics = None
        self.prefback_suggestapp = None
        self.prefback_queue = None

        self.clicked_myapp = ""

        self.errormessage = ""
        self.grouperrormessage = ""

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

        settings = Gtk.Settings.get_default()
        theme_name = "{}".format(settings.get_property('gtk-theme-name')).lower().strip()

        cssProvider = Gtk.CssProvider()
        if theme_name.startswith("pardus") or theme_name.startswith("adwaita"):
            cssProvider.load_from_path(os.path.dirname(os.path.abspath(__file__)) + "/../css/all.css")
        elif theme_name.startswith("adw-gtk3") or theme_name.startswith("eta"):
            cssProvider.load_from_path(os.path.dirname(os.path.abspath(__file__)) + "/../css/adw.css")
        else:
            cssProvider.load_from_path(os.path.dirname(os.path.abspath(__file__)) + "/../css/base.css")
        screen = Gdk.Screen.get_default()
        styleContext = Gtk.StyleContext()
        styleContext.add_provider_for_screen(screen, cssProvider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        # fix apt vte box
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

        # upgrade vte box
        self.upgrade_vteterm = Vte.Terminal()
        self.upgrade_vteterm.set_scrollback_lines(-1)
        upgrade_vte_menu = Gtk.Menu()
        upgrade_vte_menu_items = Gtk.MenuItem(label=_("Copy selected text"))
        upgrade_vte_menu.append(upgrade_vte_menu_items)
        upgrade_vte_menu_items.connect("activate", self.upgrade_vte_menu_action, self.upgrade_vteterm)
        upgrade_vte_menu_items.show()
        self.upgrade_vteterm.connect_object("event", self.upgrade_vte_event, upgrade_vte_menu)
        self.upgrade_vte_sw.add(self.upgrade_vteterm)

        self.dpkgconfigure_vteterm = None
        self.interrupt_vte_box = self.GtkBuilder.get_object("interrupt_vte_box")

        self.PardusCommentListBox = self.GtkBuilder.get_object("PardusCommentListBox")
        self.GnomeCommentListBoxEN = self.GtkBuilder.get_object("GnomeCommentListBoxEN")
        self.GnomeCommentListBoxTR = self.GtkBuilder.get_object("GnomeCommentListBoxTR")
        self.QueueListBox = self.GtkBuilder.get_object("QueueListBox")

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

        self.utils()
        self.usersettings()

        self.user_distro_full = "{}, ({})".format(self.UserSettings.userdistro, self.user_desktop_env)
        self.Logger.info("{}".format(self.user_distro_full))

        if self.UserSettings.config_udt:
            Gtk.Settings.get_default().props.gtk_application_prefer_dark_theme = True

        self.MainWindow.show_all()

        self.hide_some_widgets()

        p1 = threading.Thread(target=self.worker)
        p1.daemon = True
        p1.start()
        self.Logger.info("start done")

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
            if AF_LINK in netifaces.ifaddresses(interface):
                mac = netifaces.ifaddresses(interface)[AF_LINK][0]["addr"].upper()
            break
        if mac is None or mac == "":
            self.Logger.info("mac address can not get from netifaces, trying psutil")
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
            self.Logger.exception("{}".format(e))
            try:
                user_locale = getlocale()[0].split("_")[0]
            except Exception as e:
                self.Logger.exception("{}".format(e))
                user_locale = "en"
        if user_locale != "tr" and user_locale != "en":
            user_locale = "en"
        return user_locale

    def controlDisplay(self):
        width = 857
        height = 657
        s = 1
        w = 1920
        h = 1080
        try:
            display = Gdk.Display.get_default()
            monitor = display.get_primary_monitor()
            geometry = monitor.get_geometry()
            w = geometry.width
            h = geometry.height
            s = Gdk.Monitor.get_scale_factor(monitor)

            if w > 1920 or h > 1080:
                width = int(w / 2.24)
                height = int(h / 1.643)

            self.MainWindow.resize(width, height)

        except Exception as e:
            self.Logger.warning("Error in controlDisplay: {}")
            self.Logger.exception("{}".format(e))

        self.Logger.info("window w:{} h:{} | monitor w:{} h:{} s:{}".format(width, height, w, h, s))

    def hide_some_widgets(self):
        self.dActionCancelButton.set_visible(False)

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
            else:
                self.auto_apt_update_finished = True
        else:
            self.auto_apt_update_finished = True

    def controlPSUpdate(self):
        if self.UserSettings.usercodename == "yirmibir" or self.UserSettings.usercodename == "yirmiuc":
            if self.Server.connection and not self.isbroken:
                user_version = self.Package.installed_version("pardus-software")
                if self.UserSettings.usercodename == "yirmibir":
                    server_version = self.Server.appversion_pardus21
                else:
                    server_version = self.Server.appversion_pardus23
                if user_version is not None:
                    version = self.Package.versionCompare(user_version, server_version)
                    if version and version < 0:
                        self.notify(message_summary=_("Pardus Software Center | New version available"),
                                    message_body=_("Please upgrade application using Menu/Updates"))

    def controlAvailableApps(self):
        if self.Server.connection:
            self.setAvailableApps(available=self.UserSettings.config_saa, hideextapps=self.UserSettings.config_hera)

    def controlArgs(self):
        if "details" in self.Application.args.keys():
            found = False
            myapps_found = False
            app = self.Application.args["details"]
            try:
                if app.endswith(".pardusapp"):
                    if os.path.isfile(app):
                        appfile = open(app, "r")
                        app = appfile.read().strip()
            except Exception as e:
                self.Logger.exception("{}".format(e))
            try:
                if ".desktop" in app:
                    app = "{}".format(app.split(".desktop")[0])
                for apps in self.fullapplist:
                    if app == apps["name"] or app == apps["desktop"].split(".desktop")[0] or \
                            app == apps["gnomename"].split(".desktop")[0] or \
                            any(app == e for e in
                                apps["desktopextras"].replace(" ", "").replace(".desktop", "").split(",")):
                        found = True
                        # self.set_stack_n_search(1)
                        self.topsearchbutton.set_active(False)
                        app = apps["name"]  # if the name is coming from desktop then set it to app name
                        self.fromdetails = True
                        self.detailsappname = app
                        self.mostappname = None
                        self.fromqueue = False
                        GLib.idle_add(self.on_PardusAppsIconView_selection_changed, app)
            except Exception as e:
                self.Logger.exception("{}".format(e))
            try:
                if not found:
                    app = self.Application.args["details"]
                    if ".desktop" not in self.Application.args["details"]:
                        app = "{}.desktop".format(self.Application.args["details"])
                    for row in self.MyAppsListBox:
                        id = "{}".format(row.get_children()[0].name.rsplit('/', 1)[-1])
                        if id == app:
                            myapps_found = True
                            self.open_myapps_detailspage_from_desktopfile(row.get_children()[0].name)
                    if not myapps_found:
                        process = subprocess.run(["dpkg", "-S", app], stdout=subprocess.PIPE)
                        output = process.stdout.decode("utf-8")
                        app = output[:output.find(":")].split(",")[0]
                        if app == "":
                            app = "{}".format(self.Application.args["details"].split(".desktop")[0])
                        self.repo_searchentry.set_text(app)
                        self.on_repo_button_clicked(None)
                        self.on_repo_searchbutton_clicked(self.repo_searchbutton)
                        for row in self.searchstore:
                            if app == row[1]:
                                self.RepoAppsTreeView.set_cursor(row.path)
                                # self.on_RepoAppsTreeView_row_activated(self.RepoAppsTreeView, row.path, 0)
            except Exception as e:
                self.Logger.exception("{}".format(e))

        elif "remove" in self.Application.args.keys():
            if self.myapps_perm == 1:
                app = self.Application.args["remove"]
                if not app.endswith(".desktop"):
                    app = "{}.desktop".format(app)

                self.open_myapps_detailspage_from_desktopfile(app)

            else:
                self.Logger.info("myapps permission is 0 so you can not use remove arg")
        else:
            if len(sys.argv) > 1:
                try:
                    app = sys.argv[1].replace("pardus-software-app://", "")
                    if ".desktop" in app:
                        app = "{}".format(app.split(".desktop")[0])
                    for apps in self.fullapplist:
                        if app == apps["name"] or app == apps["desktop"].split(".desktop")[0] or \
                                app == apps["gnomename"].split(".desktop")[0] or \
                                any(app == e for e in
                                    apps["desktopextras"].replace(" ", "").replace(".desktop", "").split(",")):
                            self.topsearchbutton.set_active(False)
                            app = apps["name"]  # if the name is coming from desktop then set it to app name
                            self.fromdetails = True
                            self.detailsappname = app
                            self.mostappname = None
                            self.fromqueue = False
                            GLib.idle_add(self.on_PardusAppsIconView_selection_changed, app)
                except Exception as e:
                    self.Logger.exception("{}".format(e))

    def normalpage(self):
        self.mainstack.set_visible_child_name("home")
        if self.Server.connection:
            if not self.isbroken:
                self.homestack.set_visible_child_name("pardushome")
                GLib.idle_add(self.topsearchbutton.set_sensitive, True)
                GLib.idle_add(self.menu_suggestapp.set_sensitive, True)
                if self.myapps_perm == 1:
                    GLib.idle_add(self.myapps_button.set_sensitive, True)
                else:
                    GLib.idle_add(self.myapps_button.set_sensitive, False)
                GLib.idle_add(self.menu_statistics.set_sensitive, True)
            else:
                self.homestack.set_visible_child_name("fixapt")
                GLib.idle_add(self.topsearchbutton.set_sensitive, False)
                GLib.idle_add(self.myapps_button.set_sensitive, False)
        else:
            self.homestack.set_visible_child_name("noserver")
            self.noserverlabel.set_markup(
                "<b>{}\n\n{}\n\n{}: {}</b>".format(_("Could not connect to server."), self.Server.error_message,
                                                   _("Server address"), self.Server.serverurl))
            GLib.idle_add(self.topsearchbutton.set_sensitive, False)
            GLib.idle_add(self.menu_suggestapp.set_sensitive, False)
            if self.myapps_perm == 1:
                GLib.idle_add(self.myapps_button.set_sensitive, True)
            else:
                GLib.idle_add(self.myapps_button.set_sensitive, False)
            GLib.idle_add(self.menu_statistics.set_sensitive, False)

        self.splashspinner.stop()
        self.splashlabel.set_text("")

        GLib.idle_add(self.HeaderBarMenuButton.set_sensitive, True)
        GLib.idle_add(self.store_button.set_sensitive, True)
        if self.repo_perm == 1:
            GLib.idle_add(self.repo_button.set_sensitive, True)
        else:
            GLib.idle_add(self.repo_button.set_sensitive, False)

        if self.Server.connection and self.isbroken:
            GLib.idle_add(self.store_button.set_sensitive, False)
            GLib.idle_add(self.repo_button.set_sensitive, False)

        if self.Package.upgradable():
            GLib.idle_add(self.header_buttonbox.pack_start, self.updates_button, False, True, 0)
            GLib.idle_add(self.updates_button.set_visible, True)
            GLib.idle_add(self.updates_button.set_sensitive, True)
        else:
            GLib.idle_add(self.updates_button.set_visible, False)
            GLib.idle_add(self.updates_button.set_sensitive, False)

        self.Logger.info("page setted to normal")

    def package(self):
        GLib.idle_add(self.splashlabel.set_markup, "<b>{}</b>".format(_("Updating Cache")))
        self.Package = Package()
        if self.Package.updatecache():
            self.isbroken = False
            self.Package.getApps()
        else:
            self.isbroken = True
            self.Logger.warning("Error while updating Cache")

        self.Logger.info("package completed")

    def utils(self):
        self.Utils = Utils()
        desktop_env = self.Utils.get_desktop_env()
        desktop_env_vers = self.Utils.get_desktop_env_version(desktop_env)
        session = self.Utils.get_session_type()
        self.user_desktop_env = "{} {}, {}".format(desktop_env, desktop_env_vers, session)

    def usersettings(self):
        self.UserSettings = UserSettings()
        self.UserSettings.createDefaultConfig()
        self.UserSettings.readConfig()

        self.Logger.info("{} {}".format("config_usi", self.UserSettings.config_usi))
        self.Logger.info("{} {}".format("config_anim", self.UserSettings.config_ea))
        self.Logger.info("{} {}".format("config_availableapps", self.UserSettings.config_saa))
        self.Logger.info("{} {}".format("config_hideextapps", self.UserSettings.config_hera))
        self.Logger.info("{} {}".format("config_icon", self.UserSettings.config_icon))
        self.Logger.info("{} {}".format("config_showgnomecommments", self.UserSettings.config_sgc))
        self.Logger.info("{} {}".format("config_usedarktheme", self.UserSettings.config_udt))
        self.Logger.info("{} {}".format("config_aptup", self.UserSettings.config_aptup))
        self.Logger.info("{} {}".format("config_lastaptup", self.UserSettings.config_lastaptup))
        self.Logger.info("{} {}".format("config_forceaptuptime", self.UserSettings.config_forceaptuptime))

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

        filesave_chooser.set_do_overwrite_confirmation(True)

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

    def setRepoApps(self):
        if self.repo_perm == 1:

            if not self.repoappsinit:
                renderer_toggle = Gtk.CellRendererToggle()
                renderer_toggle.connect("toggled", self.on_cell_toggled)
                column_toggle = Gtk.TreeViewColumn(_("Status"), renderer_toggle, active=0)
                column_toggle.set_resizable(True)
                column_toggle.set_sort_column_id(0)
                self.RepoAppsTreeView.append_column(column_toggle)

                renderer = Gtk.CellRendererText()
                column_name = Gtk.TreeViewColumn(_("Name"), renderer, text=1)
                column_name.set_resizable(True)
                column_name.set_sort_column_id(1)
                self.RepoAppsTreeView.append_column(column_name)

                renderer = Gtk.CellRendererText()
                column_cat = Gtk.TreeViewColumn(_("Section"), renderer, text=2)
                column_cat.set_resizable(True)
                column_cat.set_sort_column_id(2)
                self.RepoAppsTreeView.append_column(column_cat)

                self.RepoAppsTreeView.set_search_column(1)

                self.RepoAppsTreeView.show_all()

                self.repoappsinit = True

        elif self.repo_perm == 0:
            self.Logger.info("repo_perm is 0 so repo apps not setting")
            self.repo_button.set_sensitive(False)

    def on_cell_toggled(self, widget, path):
        self.Logger.info("cell toggled")

    def server(self):
        self.Logger.info("Getting applications from server")
        GLib.idle_add(self.splashlabel.set_markup, "<b>{}</b>".format(_("Getting applications from server")))
        self.Server = Server()

        conffile = "/etc/pardus/pardus-software.conf"
        self.repo_perm = 1
        self.myapps_perm = 1
        try:
            conf = open(os.path.join(conffile), "r").read()
            # strip all whitespaces to get more accurate results
            conf = conf.replace(" ", "")

            for line in conf.splitlines():
                if not line.startswith("#"):
                    if line.startswith("server="):
                        self.Server.serverurl = line.split("server=")[1]
                    if line.startswith("repo="):
                        self.repo_perm = line.split("repo=")[1]
                    if line.startswith("myapps="):
                        self.myapps_perm = line.split("myapps=")[1]
        except Exception as e:
            self.Logger.exception("{}".format(e))

        if not self.Server.serverurl:
            try:
                self.Server.serverurl = open(conffile, "r").read().strip()
                self.Logger.info("server url getted from old type one line config")
            except Exception as e:
                self.Logger.warning("Error getting server url from conf so setting to https://apps.pardus.org.tr")
                self.Logger.exception("{}".format(e))
                self.Server.serverurl = "https://apps.pardus.org.tr"
        else:
            self.Logger.info("{}".format("server url getted from new type config"))

        try:
            self.repo_perm = int(self.repo_perm)
        except:
            self.Logger.warning("repo key's value must be int. 1 or 0. So setting to default value 1")
            self.repo_perm = 1

        try:
            self.myapps_perm = int(self.myapps_perm)
        except:
            self.Logger.warning("myapps_perm key's value must be int. 1 or 0. So setting to default value 1")
            self.myapps_perm = 1

        self.Logger.info("server url: {}".format(self.Server.serverurl))
        self.Logger.info("repo permission: {}".format(self.repo_perm))
        self.Logger.info("myapps permission: {}".format(self.myapps_perm))

        self.Server.ServerAppsControlCB = self.ServerAppsControlCB
        self.Server.ServerAppsCB = self.ServerAppsCB
        self.Server.ServerIconsCB = self.ServerIconsCB
        self.Server.control_server(self.Server.serverurl + "/api/v2/test")

        self.Logger.info("server func done")

    def afterServers(self):
        self.normalpage()
        GLib.idle_add(self.controlServer)
        GLib.idle_add(self.controlAvailableApps)
        GLib.idle_add(self.clearBoxes)
        GLib.idle_add(self.setPardusCategories)
        GLib.idle_add(self.setPardusApps)
        GLib.idle_add(self.setEditorApps)
        GLib.idle_add(self.setMostApps)
        GLib.idle_add(self.setRepoApps)
        GLib.idle_add(self.gnomeRatings)
        GLib.idle_add(self.controlPSUpdate)
        GLib.idle_add(self.aptUpdate)
        GLib.idle_add(self.myapps_worker_thread)

    def ServerAppsControlCB(self, status):
        self.Logger.info("ServerAppsControlCB : {}".format(status))

        if not status:
            self.Server.serverurl = self.Server.serverurl.replace("https://", "http://")
            self.Logger.info("{}".format(self.Server.serverurl))

        self.Server.get(self.Server.serverurl + self.Server.serverapps, "apps")
        self.Server.get(self.Server.serverurl + self.Server.servercats, "cats")
        self.Server.get(self.Server.serverurl + self.Server.serverhomepage, "home")
        self.Server.get(self.Server.serverurl + self.Server.serverstatistics, "statistics")

    def ServerAppsCB(self, success, response=None, type=None):
        if success:
            if type == "apps":
                self.Logger.info("server apps successful")
                self.status_serverapps = True
                self.applist = sorted(response["app-list"], key=lambda x: locale.strxfrm(x["prettyname"][self.locale]))
                self.fullapplist = self.applist
            elif type == "cats":
                self.Logger.info("server cats successful")
                self.status_servercats = True
                self.catlist = response["cat-list"]
                self.fullcatlist = self.catlist
            elif type == "home":
                self.Logger.info("server home successful")
                self.status_serverhome = True
                self.Server.ediapplist = response["editor-apps"]
                self.Server.mostdownapplist = response["mostdown-apps"]
                self.Server.mostrateapplist = response["mostrate-apps"]
                if "last-apps" in response:
                    self.Server.lastaddedapplist = response["last-apps"]
                self.Server.totalstatistics = response["total"]
                self.Server.servermd5 = response["md5"]
                self.Server.appversion = response["version"]
                if "version_pardus21" in response.keys():
                    self.Server.appversion_pardus21 = response["version_pardus21"]
                else:
                    self.Server.appversion_pardus21 = self.Server.appversion
                if "version_pardus23" in response.keys():
                    self.Server.appversion_pardus23 = response["version_pardus23"]
                else:
                    self.Server.appversion_pardus23 = self.Server.appversion
                self.Server.iconnames = response["iconnames"]
                self.Server.badwords = response["badwords"]
                if "important-packages" in response and response["important-packages"]:
                    self.important_packages = response["important-packages"]
                if "i386-packages" in response and response["i386-packages"]:
                    self.i386_packages = response["i386-packages"]
                self.Server.aptuptime = response["aptuptime"]
            elif type == "statistics":
                self.Logger.info("server statistics successful")
                self.status_serverstatistics = True
                self.Server.dailydowns = response["dailydowns"]
                if "osdownsv23" in response.keys():
                    self.Server.osdowns = response["osdownsv23"]
                else:
                    self.Server.osdowns = response["osdowns"]
                if "oscolorsv23" in response.keys():
                    self.Server.oscolors = response["oscolorsv23"]
                else:
                    self.Server.oscolors = response["oscolors"]
                self.Server.appdowns = response["appdowns"]
                self.Server.appcolors = response["appcolors"]
                if "osexplode" in response.keys():
                    self.Server.osexplode = response["osexplode"]
                else:
                    for os in self.Server.osdowns:
                        self.Server.osexplode.append(0.2)

            if self.status_serverapps and self.status_servercats and self.status_serverhome and self.status_serverstatistics:
                self.Server.connection = True
                self.getIcons()
        else:
            if not self.connection_error_after:
                self.Server.connection = False
                self.afterServers()
                self.connection_error_after = True

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
            self.Logger.info("fromsettings, {} re-setting".format(type))
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
            self.Logger.info("Getting icons from server")
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
            self.Logger.info("icons cannot downloading because server connection is {}".format(self.Server.connection))

    def controlServer(self):
        if self.Server.connection:
            self.Logger.info("Controlling {}".format(self.Server.serverurl))
            self.AppDetail.control(self.Server.serverurl + "/api/v2/test")
            self.AppRequest.control(self.Server.serverurl + "/api/v2/test")
            self.PardusComment.control(self.Server.serverurl + "/api/v2/test")

    def gnomeRatings(self):
        self.Logger.info("Getting ratings from gnome odrs")

        self.GnomeRatingServer = GnomeRatingServer()
        self.GnomeRatingServer.gRatingServer = self.gRatingServer
        self.GnomeRatingServer.get()

    def gRatingServer(self, status, response):
        if status:
            self.Logger.info("gnomeratings successful")
            self.gnomeratings = response
        else:
            self.gnomeratings = []
            self.Logger.info("gnomeratings not successful")

    def setPardusApps(self):
        GLib.idle_add(self.PardusAppListStore.clear)
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
                GLib.idle_add(self.addToPardusApps,
                              [appicon, appname, categorynumber, prettyname, category, subcategory])

    def addToPardusApps(self, list):
        self.PardusAppListStore.append(list)

    def setPardusCategories(self):
        self.HomeCategoryFlowBox.foreach(lambda child: self.HomeCategoryFlowBox.remove(child))
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

        self.Logger.info("on_catbutton_clicked")

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
        self.PardusCurrentCategoryString, self.PardusCurrentCategoryIcon, \
            self.PardusCurrentCategorySubCats, self.PardusCurrentCategoryExternal, \
            self.PardusCurrentCategorySubCategories = self.get_category_name_from_button(button.name)

        self.Logger.info("HomeCategory: {} {} {} {} {}".format(self.PardusCurrentCategory,
                                                               self.PardusCurrentCategoryString,
                                                               self.PardusCurrentCategorySubCats,
                                                               self.PardusCurrentCategoryExternal,
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
            self.ui_showapps_buttonbox.set_visible(False)
            self.ui_showappcount_label.set_visible(False)
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
            self.ui_showapps_buttonbox.set_visible(True)
            self.ui_showappcount_label.set_visible(True)
            self.sortPardusAppsCombo.set_visible(True)
            self.pardusAppsStack.set_visible_child_name("normal")
            self.PardusCategoryFilter.refilter()
            self.set_app_count_label()

    def setEditorApps(self):
        GLib.idle_add(self.EditorListStore.clear)
        if self.Server.connection:
            self.Logger.info("setting editor apps")
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
        self.MostDownFlowBox.foreach(lambda child: self.MostDownFlowBox.remove(child))
        self.MostRateFlowBox.foreach(lambda child: self.MostRateFlowBox.remove(child))
        self.LastAddedFlowBox.foreach(lambda child: self.LastAddedFlowBox.remove(child))
        if self.Server.connection:
            self.Logger.info("setting mostapps")
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

                rateicon = Gtk.Image.new_from_icon_name("starred-symbolic", Gtk.IconSize.BUTTON)

                ratelabel = Gtk.Label.new()
                ratelabel.set_markup("<small>{:.1f}</small>".format(float(mda["rate"])))

                box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
                box1 = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
                box2 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
                box3 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)

                box2.pack_start(downicon, False, True, 0)
                box2.pack_start(downlabel, False, True, 0)
                box2.set_spacing(3)

                box3.pack_start(rateicon, False, True, 0)
                box3.pack_start(ratelabel, False, True, 0)
                box3.set_spacing(3)

                box1.set_homogeneous(True)
                box1.pack_start(box2, False, True, 0)
                box1.pack_start(box3, False, True, 0)

                box.pack_start(icon, False, True, 0)
                box.pack_start(label, False, True, 0)
                box.pack_end(box1, False, True, 0)
                box.set_margin_start(8)
                box.set_margin_end(8)
                box.set_margin_top(3)
                box.set_margin_bottom(3)
                box.set_spacing(8)

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

                rateicon = Gtk.Image.new_from_icon_name("starred-symbolic", Gtk.IconSize.BUTTON)

                ratelabel = Gtk.Label.new()
                ratelabel.set_markup("<small>{:.1f}</small>".format(float(mra["rate"])))

                box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
                box1 = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
                box2 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
                box3 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)

                box2.pack_start(downicon, False, True, 0)
                box2.pack_start(downlabel, False, True, 0)
                box2.set_spacing(3)

                box3.pack_start(rateicon, False, True, 0)
                box3.pack_start(ratelabel, False, True, 0)
                box3.set_spacing(3)

                box1.set_homogeneous(True)
                box1.pack_start(box2, False, True, 0)
                box1.pack_start(box3, False, True, 0)

                box.pack_start(icon, False, True, 0)
                box.pack_start(label, False, True, 0)
                box.pack_end(box1, False, True, 0)
                box.set_margin_start(8)
                box.set_margin_end(8)
                box.set_margin_top(3)
                box.set_margin_bottom(3)
                box.set_spacing(8)

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

                rateicon = Gtk.Image.new_from_icon_name("starred-symbolic", Gtk.IconSize.BUTTON)

                ratelabel = Gtk.Label.new()
                ratelabel.set_markup("<small>{:.1f}</small>".format(float(la["rate"])))

                box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
                box1 = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
                box2 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
                box3 = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)

                box2.pack_start(downicon, False, True, 0)
                box2.pack_start(downlabel, False, True, 0)
                box2.set_spacing(3)

                box3.pack_start(rateicon, False, True, 0)
                box3.pack_start(ratelabel, False, True, 0)
                box3.set_spacing(3)

                box1.set_homogeneous(True)
                box1.pack_start(box2, False, True, 0)
                box1.pack_start(box3, False, True, 0)

                box.pack_start(icon, False, True, 0)
                box.pack_start(label, False, True, 0)
                box.pack_end(box1, False, True, 0)
                box.set_margin_start(8)
                box.set_margin_end(8)
                box.set_margin_top(3)
                box.set_margin_bottom(3)
                box.set_spacing(8)

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
            self.Logger.info("{} {}".format(cat, "category icon not found in system icons"))
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
                        caticon = Gtk.IconTheme.get_default().load_icon("image-missing", size,
                                                                        Gtk.IconLookupFlags(16))
                    except:
                        caticon = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", size,
                                                                        Gtk.IconLookupFlags(16))
            except:
                try:
                    caticon = Gtk.IconTheme.get_default().load_icon("image-missing", size, Gtk.IconLookupFlags(16))
                except:
                    caticon = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", size, Gtk.IconLookupFlags(16))
        return caticon

    def getServerCatIcon(self, cat, size=48):
        try:
            if self.UserSettings.config_icon == "default":
                icons = "categoryicons"
            else:
                icons = "categoryicons-" + self.UserSettings.config_icon
        except Exception as e:
            icons = "categoryicons"
            self.Logger.exception("{}".format(e))
        try:
            caticon = GdkPixbuf.Pixbuf.new_from_file_at_size(
                self.Server.cachedir + icons + "/" + cat + ".svg", size, size)
        except:
            try:
                caticon = GdkPixbuf.Pixbuf.new_from_file_at_size(
                    self.Server.cachedir + "categoryicons/" + cat + ".svg", size, size)
            except:
                try:
                    caticon = Gtk.IconTheme.get_default().load_icon("image-missing", size, Gtk.IconLookupFlags(16))
                except:
                    caticon = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", size, Gtk.IconLookupFlags(16))
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
                            appicon = Gtk.IconTheme.get_default().load_icon("image-missing", size,
                                                                            Gtk.IconLookupFlags(16))
                        except:
                            appicon = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", size,
                                                                            Gtk.IconLookupFlags(16))
                else:
                    if myappicon:
                        appicon = self.getMyAppIcon(app, size)
                    else:
                        try:
                            appicon = Gtk.IconTheme.get_default().load_icon("image-missing", size,
                                                                            Gtk.IconLookupFlags(16))
                        except:
                            appicon = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", size,
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
            self.Logger.exception("{}".format(e))
        try:
            appicon = GdkPixbuf.Pixbuf.new_from_file_at_size(self.Server.cachedir + icons + "/" + app + ".svg", size,
                                                             size)
        except:
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
                            appicon = Gtk.IconTheme.get_default().load_icon("image-missing", size,
                                                                            Gtk.IconLookupFlags(16))
                        except:
                            appicon = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", size,
                                                                            Gtk.IconLookupFlags(16))
                else:
                    if myappicon:
                        appicon = self.getMyAppIcon(app, size)
                    else:
                        try:
                            appicon = Gtk.IconTheme.get_default().load_icon("image-missing", size,
                                                                            Gtk.IconLookupFlags(16))
                        except:
                            appicon = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", size,
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
            self.Logger.exception("{}".format(e))
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
                                    appicon = Gtk.IconTheme.get_default().load_icon("image-missing", size,
                                                                                    Gtk.IconLookupFlags(16))
                                except:
                                    appicon = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", size,
                                                                                    Gtk.IconLookupFlags(16))

        return appicon

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

            self.rstack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
            self.rstack.set_transition_duration(200)

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

            self.tryfixstack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
            self.tryfixstack.set_transition_duration(200)

            self.statstack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
            self.statstack.set_transition_duration(250)

            self.statmainstack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
            self.statmainstack.set_transition_duration(250)

            self.SuggestStack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
            self.SuggestStack.set_transition_duration(200)

            self.prefstack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
            self.prefstack.set_transition_duration(200)

            self.myappsstack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
            self.myappsstack.set_transition_duration(200)

            self.myappsdetailsstack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
            self.myappsdetailsstack.set_transition_duration(200)

            self.ImagePopoverStack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
            self.ImagePopoverStack.set_transition_duration(200)

            self.bottomrevealer.set_transition_type(Gtk.StackTransitionType.SLIDE_UP)
            self.bottomrevealer.set_transition_duration(200)

            self.toprevealer.set_transition_type(Gtk.StackTransitionType.SLIDE_DOWN)
            self.toprevealer.set_transition_duration(200)

        else:
            self.mainstack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.mainstack.set_transition_duration(0)

            self.homestack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.homestack.set_transition_duration(0)

            self.pardusAppsStack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.pardusAppsStack.set_transition_duration(0)

            self.searchstack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.searchstack.set_transition_duration(0)

            self.rstack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.rstack.set_transition_duration(0)

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

            self.tryfixstack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.tryfixstack.set_transition_duration(0)

            self.statstack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.statstack.set_transition_duration(0)

            self.statmainstack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.statmainstack.set_transition_duration(0)

            self.SuggestStack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.SuggestStack.set_transition_duration(0)

            self.prefstack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.prefstack.set_transition_duration(0)

            self.myappsstack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.myappsstack.set_transition_duration(0)

            self.myappsdetailsstack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.myappsdetailsstack.set_transition_duration(0)

            self.ImagePopoverStack.set_transition_type(Gtk.StackTransitionType.NONE)
            self.ImagePopoverStack.set_transition_duration(0)

            self.bottomrevealer.set_transition_type(Gtk.StackTransitionType.NONE)
            self.bottomrevealer.set_transition_duration(0)

            self.toprevealer.set_transition_type(Gtk.StackTransitionType.NONE)
            self.toprevealer.set_transition_duration(0)

        self.PopoverMenu.set_transitions_enabled(self.UserSettings.config_ea)
        self.DisclaimerPopover.set_transitions_enabled(self.UserSettings.config_ea)
        self.ImagePopover.set_transitions_enabled(self.UserSettings.config_ea)
        self.licensePopover.set_transitions_enabled(self.UserSettings.config_ea)
        self.PopoverPrefTip.set_transitions_enabled(self.UserSettings.config_ea)
        self.RequiredChangesPopover.set_transitions_enabled(self.UserSettings.config_ea)

    def on_menubackbutton_clicked(self, widget):
        hsname = self.homestack.get_visible_child_name()
        if hsname == "pardusapps":

            self.set_stack_n_search(1)

            if self.PardusCurrentCategorySubCats:
                self.SubCategoryFlowBox.unselect_all()
                if self.pardusAppsStack.get_visible_child_name() != "subcats":
                    self.pardusAppsStack.set_visible_child_name("subcats")
                    self.ui_showapps_buttonbox.set_visible(False)
                    self.ui_showappcount_label.set_visible(False)
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

            self.set_stack_n_search(1)

            if self.fromeditorapps or self.frommostapps:
                self.homestack.set_visible_child_name("pardushome")
                self.EditorAppsIconView.unselect_all()
                self.menubackbutton.set_sensitive(False)
            elif self.frommyapps:
                self.homestack.set_visible_child_name("myapps")
                self.set_stack_n_search(3)
                self.menubackbutton.set_sensitive(True)
            else:
                if self.fromqueue:
                    self.homestack.set_visible_child_name("queue")
                    self.set_stack_n_search(4)
                else:
                    self.homestack.set_visible_child_name("pardusapps")
                    self.PardusAppsIconView.unselect_all()

        elif hsname == "myapps":

            self.set_stack_n_search(3)
            self.menubackbutton.set_sensitive(False)

            masname = self.myappsstack.get_visible_child_name()
            if masname == "details":
                madsname = self.myappsdetailsstack.get_visible_child_name()
                if madsname == "details":
                    self.myappsstack.set_visible_child_name("myapps")
                elif madsname == "disclaimer":
                    self.myappsdetailsstack.set_visible_child_name("details")
                    self.menubackbutton.set_sensitive(True)
            elif masname == "notfound":
                self.menubackbutton.set_sensitive(True)
                self.myappsstack.set_visible_child_name("myapps")

        elif hsname == "preferences" or hsname == "repohome" or hsname == "suggestapp" or hsname == "queue" or hsname == "statistics":

            if hsname == "preferences":
                self.homestack.set_visible_child_name(self.prefback_preferences)
            elif hsname == "statistics":
                self.homestack.set_visible_child_name(self.prefback_statistics)
            elif hsname == "suggestapp":
                self.homestack.set_visible_child_name(self.prefback_suggestapp)
            elif hsname == "queue":
                self.homestack.set_visible_child_name(self.prefback_queue)
            else:
                self.homestack.set_visible_child_name(self.prefback)

            if not self.isbroken:
                self.topsearchbutton.set_sensitive(True)

            hsname1 = self.homestack.get_visible_child_name()

            if hsname1 == hsname:
                self.menubackbutton.set_sensitive(False)
            else:
                if hsname1 == "pardushome":
                    self.set_stack_n_search(1)
                    self.menubackbutton.set_sensitive(False)
                elif hsname1 == "repohome":
                    self.set_stack_n_search(2)
                    self.menubackbutton.set_sensitive(False)
                elif hsname1 == "myapps":
                    self.set_stack_n_search(3)
                    self.menubackbutton.set_sensitive(False)
                elif hsname1 == "pardusappsdetail" or hsname1 == "pardusapps":
                    self.set_stack_n_search(1)
                elif hsname1 == "noserver":
                    self.set_stack_n_search(1)
                    self.topsearchbutton.set_sensitive(False)
                    self.menubackbutton.set_sensitive(False)
                elif hsname1 == "queue":
                    self.set_stack_n_search(4)
                elif hsname1 == "fixapt":
                    self.menubackbutton.set_sensitive(False)

    def set_stack_n_search(self, id):
        '''
        id:  1 = pardus, 2 = repo, 3 = myapps, 4 = queue, 5 = updates
        '''
        if id == 1:
            if not self.store_button.get_style_context().has_class("suggested-action"):
                self.store_button.get_style_context().add_class("suggested-action")
            self.searchstack.set_visible_child_name("pardus")
            if self.repo_button.get_style_context().has_class("suggested-action"):
                self.repo_button.get_style_context().remove_class("suggested-action")
            if self.myapps_button.get_style_context().has_class("suggested-action"):
                self.myapps_button.get_style_context().remove_class("suggested-action")
            if self.queue_button.get_style_context().has_class("suggested-action"):
                self.queue_button.get_style_context().remove_class("suggested-action")
            if self.updates_button.get_style_context().has_class("suggested-action"):
                self.updates_button.get_style_context().remove_class("suggested-action")
        elif id == 2:
            if not self.repo_button.get_style_context().has_class("suggested-action"):
                self.repo_button.get_style_context().add_class("suggested-action")
            self.searchstack.set_visible_child_name("repo")
            if self.store_button.get_style_context().has_class("suggested-action"):
                self.store_button.get_style_context().remove_class("suggested-action")
            if self.myapps_button.get_style_context().has_class("suggested-action"):
                self.myapps_button.get_style_context().remove_class("suggested-action")
            if self.queue_button.get_style_context().has_class("suggested-action"):
                self.queue_button.get_style_context().remove_class("suggested-action")
            if self.updates_button.get_style_context().has_class("suggested-action"):
                self.updates_button.get_style_context().remove_class("suggested-action")
        elif id == 3:
            if not self.myapps_button.get_style_context().has_class("suggested-action"):
                self.myapps_button.get_style_context().add_class("suggested-action")
            self.searchstack.set_visible_child_name("myapps")
            if self.store_button.get_style_context().has_class("suggested-action"):
                self.store_button.get_style_context().remove_class("suggested-action")
            if self.repo_button.get_style_context().has_class("suggested-action"):
                self.repo_button.get_style_context().remove_class("suggested-action")
            if self.queue_button.get_style_context().has_class("suggested-action"):
                self.queue_button.get_style_context().remove_class("suggested-action")
            if self.updates_button.get_style_context().has_class("suggested-action"):
                self.updates_button.get_style_context().remove_class("suggested-action")
        elif id == 4:
            if not self.queue_button.get_style_context().has_class("suggested-action"):
                self.queue_button.get_style_context().add_class("suggested-action")
            if self.store_button.get_style_context().has_class("suggested-action"):
                self.store_button.get_style_context().remove_class("suggested-action")
            if self.repo_button.get_style_context().has_class("suggested-action"):
                self.repo_button.get_style_context().remove_class("suggested-action")
            if self.myapps_button.get_style_context().has_class("suggested-action"):
                self.myapps_button.get_style_context().remove_class("suggested-action")
            if self.updates_button.get_style_context().has_class("suggested-action"):
                self.updates_button.get_style_context().remove_class("suggested-action")
        elif id == 5:
            if not self.updates_button.get_style_context().has_class("suggested-action"):
                self.updates_button.get_style_context().add_class("suggested-action")
            if self.store_button.get_style_context().has_class("suggested-action"):
                self.store_button.get_style_context().remove_class("suggested-action")
            if self.repo_button.get_style_context().has_class("suggested-action"):
                self.repo_button.get_style_context().remove_class("suggested-action")
            if self.myapps_button.get_style_context().has_class("suggested-action"):
                self.myapps_button.get_style_context().remove_class("suggested-action")
            if self.queue_button.get_style_context().has_class("suggested-action"):
                self.queue_button.get_style_context().remove_class("suggested-action")

    def set_button_class(self, button, state):
        '''
        state 0 = app is not installed, state 1 = app is installed, state 2 = app is not found
        '''
        if state == 1:
            if button.get_style_context().has_class("suggested-action"):
                button.get_style_context().remove_class("suggested-action")
            button.get_style_context().add_class("destructive-action")
            button.set_sensitive(True)
        elif state == 0:
            if button.get_style_context().has_class("destructive-action"):
                button.get_style_context().remove_class("destructive-action")
            button.get_style_context().add_class("suggested-action")
            button.set_sensitive(True)
        elif state == 2:
            if button.get_style_context().has_class("suggested-action"):
                button.get_style_context().remove_class("suggested-action")
            if button.get_style_context().has_class("destructive-action"):
                button.get_style_context().remove_class("destructive-action")
            button.set_sensitive(False)

    def on_PardusAppsIconView_selection_changed(self, iconview):
        self.set_stack_n_search(1)
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
        self.wpcformcontrolLabel.set_visible(False)
        self.wpcformcontrolLabel.set_text("")
        self.wpcresultLabel.set_text("")
        self.wpcAuthor.set_text(self.UserSettings.user_real_name)
        start, end = self.wpcComment.get_buffer().get_bounds()
        self.wpcComment.get_buffer().delete(start, end)
        self.wpcSendButton.set_sensitive(True)

        # loading screen for app images
        self.screenshots = []
        self.appimage1stack.set_visible_child_name("loading")
        self.appimage2stack.set_visible_child_name("loading")
        self.pop1Image.set_from_pixbuf(self.missing_pixbuf)
        self.pop2Image.set_from_pixbuf(self.missing_pixbuf)

        # set scroll position to top (reset)
        self.PardusAppDetailScroll.set_vadjustment(Gtk.Adjustment())
        self.PardusCommentScroll.set_vadjustment(Gtk.Adjustment())
        self.GnomeTRCommentScroll.set_vadjustment(Gtk.Adjustment())
        self.GnomeENCommentScroll.set_vadjustment(Gtk.Adjustment())

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
        self.clear_drequired_popup()
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
            self.fromqueue = False
            self.frommyapps = False
        except:
            if not self.fromqueue and not self.frommyapps:
                self.frommostapps = True
            lensel = 1

        if lensel == 1:
            if not self.frommostapps:
                if not self.fromqueue and not self.frommyapps:
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
            else:
                self.appname = iconview

            self.Logger.info("APPNAME : {}".format(self.appname))

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
                        self.command = []
                        for package in command[self.locale].split(" "):
                            if self.Package.controlPackageCache(package):
                                self.command.append(package)
                        if self.command:
                            self.command = " ".join(self.command)
                        else:
                            self.command = i["name"]
                    else:
                        self.command = i["name"]

                    self.external = i["external"]
                    break

            if not found_pardusapp:
                self.repo_searchentry.set_text(self.appname)
                self.on_repo_button_clicked(self.repo_button)
                self.on_repo_searchbutton_clicked(self.repo_searchbutton)
                for row in self.searchstore:
                    if self.appname == row[1]:
                        self.RepoAppsTreeView.set_cursor(row.path)
                        # self.on_RepoAppsTreeView_row_activated(self.RepoAppsTreeView, row.path, 0)
                return False

            GLib.idle_add(self.homestack.set_visible_child_name, "pardusappsdetail")

            if self.gnomename != "" and self.gnomename is not None:
                try:
                    self.setGnomeRatings(self.gnomeratings[self.gnomename])
                except Exception as e:
                    self.setGnomeRatings("")
                    self.Logger.warning("{} {}".format(self.gnomename, "not found in gnomeratings"))
                    self.Logger.exception("{}".format(e))
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
            # self.dName.set_tooltip_markup("<b>{}</b>".format(self.appname))
            self.dPackage.set_markup("<i>" + self.appname + "</i>")
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

            self.dViewonweb.set_markup(_("View on {}.").format(
                "<a href='https://apps.pardus.org.tr/app/{}'>apps.pardus.org.tr</a>".format(self.appname)))

            isinstalled = self.Package.isinstalled(self.appname)

            if isinstalled is not None:
                sizethread = threading.Thread(target=self.size_worker_thread, daemon=True)
                sizethread.start()

                version = self.Package.candidate_version(self.appname)
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
                self.dComponent.set_markup("{} {}".format(origin, component))
                self.dType.set_markup(type)

                if isinstalled:

                    self.set_button_class(self.dActionButton, 1)
                    self.set_button_class(self.dActionInfoButton, 1)

                    self.dActionButton.set_label(_(" Uninstall"))
                    self.dActionButton.set_image(
                        Gtk.Image.new_from_icon_name("user-trash-symbolic", Gtk.IconSize.BUTTON))

                    if self.desktop_file != "" and self.desktop_file is not None:
                        self.dOpenButton.set_visible(True)
                    else:
                        self.dOpenButton.set_visible(False)

                else:

                    self.set_button_class(self.dActionButton, 0)
                    self.set_button_class(self.dActionInfoButton, 0)

                    self.dActionButton.set_label(_(" Install"))
                    self.dActionButton.set_image(
                        Gtk.Image.new_from_icon_name("document-save-symbolic", Gtk.IconSize.BUTTON))

                    self.dOpenButton.set_visible(False)
                    self.wpcformcontrolLabel.set_visible(True)
                    self.wpcformcontrolLabel.set_markup(
                        "<span color='red'>{}</span>".format(_("You need to install the application")))

                app_in_queue = False
                if len(self.queue) > 0:
                    for qa in self.queue:
                        if self.appname == qa["name"]:
                            app_in_queue = True
                if app_in_queue:
                    if isinstalled:
                        self.dActionButton.set_label(_(" Removing"))
                    else:
                        self.dActionButton.set_label(_(" Installing"))
                    self.dActionButton.set_image(
                        Gtk.Image.new_from_icon_name("process-working-symbolic", Gtk.IconSize.BUTTON))
                    self.dActionButton.set_sensitive(False)
                    self.dActionInfoButton.set_sensitive(False)

            else:
                self.set_button_class(self.dActionButton, 2)
                self.set_button_class(self.dActionInfoButton, 2)

                self.dActionButton.set_label(_(" Not Found"))
                self.dActionButton.set_image(
                    Gtk.Image.new_from_icon_name("dialog-warning-symbolic", Gtk.IconSize.BUTTON))

                self.clear_drequired_popup()

                self.dVersion.set_markup(_("None"))
                self.dSize.set_markup(_("None"))
                self.dSizeTitle.set_text(_("Download Size"))
                self.dSizeGrid.set_tooltip_text(None)
                self.dComponent.set_markup(_("None"))
                self.dType.set_markup(_("None"))

                self.dOpenButton.set_visible(False)
                self.dDisclaimerButton.set_visible(False)

                self.wpcformcontrolLabel.set_visible(True)
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
                self.pixbuf1 = self.AppImage.imgcache[self.screenshots[0] + "#1"]
                self.resizeAppImage()
                self.appimage1stack.set_visible_child_name("loaded")
            else:
                self.pixbuf1 = None
                self.AppImage.fetch(self.Server.serverurl, self.screenshots[0], "#1")

            if self.screenshots[1] + "#2" in self.AppImage.imgcache:
                self.pixbuf2 = self.AppImage.imgcache[self.screenshots[1] + "#2"]
                self.resizeAppImage()
                self.appimage2stack.set_visible_child_name("loaded")
            else:
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
                self.Logger.info("gnome comments disabled")

    def clear_drequired_popup(self):
        self.dapp_packagename_label.set_text("{}".format(""))
        self.dapp_toremove_label.set_text("{}".format(""))
        self.dapp_toinstall_label.set_text("{}".format(""))
        self.dapp_broken_label.set_text("{}".format(""))
        self.dapp_fsize_label.set_text("{}".format(""))
        self.dapp_dsize_label.set_text("{}".format(""))
        self.dapp_isize_label.set_text("{}".format(""))

    def repo_required_worker_thread(self, package):
        rc = self.repo_required_worker(package)
        GLib.idle_add(self.on_required_worker_done, package, rc)

    def repo_required_worker(self, package):
        return self.Package.required_changes(package)

    def on_required_worker_done(self, package, rc):

        self.repo_required_spinner.stop()
        self.repo_required_stack.set_visible_child_name("details")

        self.rapp_packagename_box.set_visible(True)
        self.rapp_packagename_label.set_markup("<b>{}</b>".format(package))

        if rc["package_broken"] or rc["package_broken"] is None:
            self.rapp_package_broken_box.set_visible(True)
            self.raction.set_sensitive(False)

        if rc["to_delete"] and rc["to_delete"] is not None:
            self.rapp_toremove_label.set_markup("{}".format(", ".join(rc["to_delete"])))
            self.rapp_toremove_box.set_visible(True)

        if rc["to_install"] and rc["to_install"] is not None:
            self.rapp_toinstall_label.set_markup("{}".format(", ".join(rc["to_install"])))
            self.rapp_toinstall_box.set_visible(True)

        if rc["broken"] and rc["broken"] is not None:
            self.rapp_broken_label.set_markup("{}".format(", ".join(rc["broken"])))
            self.rapp_broken_box.set_visible(True)

        if rc["freed_size"] and rc["freed_size"] is not None and rc["freed_size"] > 0:
            self.rapp_fsize_label.set_markup("{}".format(self.Package.beauty_size(rc["freed_size"])))
            self.rapp_fsize_box.set_visible(True)
            self.rapp_size_box.set_visible(True)

        if rc["download_size"] and rc["download_size"] is not None and rc["download_size"] > 0:
            self.rapp_dsize_label.set_markup("{}".format(self.Package.beauty_size(rc["download_size"])))
            self.rapp_dsize_box.set_visible(True)
            self.rapp_size_box.set_visible(True)

        if rc["install_size"] and rc["install_size"] is not None and rc["install_size"] > 0:
            self.rapp_isize_label.set_markup("{}".format(self.Package.beauty_size(rc["install_size"])))
            self.rapp_isize_box.set_visible(True)
            self.rapp_size_box.set_visible(True)

    def size_worker_thread(self, app=None):
        if app is None:
            self.size_worker()
        else:
            self.size_worker(app)
        GLib.idle_add(self.on_size_worker_done)

    def size_worker(self, app=None):
        if app is None:
            self.ret = self.Package.required_changes(self.command)
        else:
            self.ret = self.Package.required_changes(app)
        self.Logger.info("{}".format(self.ret))

    def on_size_worker_done(self):

        self.dapp_packagename_label.set_markup("<b>{}</b>".format(self.appname))

        if self.ret["to_delete"] and self.ret["to_delete"] is not None:
            self.dapp_toremove_label.set_markup("{}".format(", ".join(self.ret["to_delete"])))
            self.dapp_toremove_box.set_visible(True)
        else:
            self.dapp_toremove_box.set_visible(False)

        if self.ret["to_install"] and self.ret["to_install"] is not None:
            self.dapp_toinstall_label.set_markup("{}".format(", ".join(self.ret["to_install"])))
            self.dapp_toinstall_box.set_visible(True)
        else:
            self.dapp_toinstall_box.set_visible(False)

        if self.ret["broken"] and self.ret["broken"] is not None:
            self.dapp_broken_label.set_markup("{}".format(", ".join(self.ret["broken"])))
            self.dapp_broken_box.set_visible(True)
        else:
            self.dapp_broken_box.set_visible(False)

        if self.ret["freed_size"] and self.ret["freed_size"] is not None and self.ret["freed_size"] > 0:
            self.dapp_fsize_label.set_markup("{}".format(self.Package.beauty_size(self.ret["freed_size"])))
            self.dapp_fsize_box.set_visible(True)
        else:
            self.dapp_fsize_box.set_visible(False)

        if self.ret["download_size"] and self.ret["download_size"] is not None and self.ret["download_size"] > 0:
            self.dapp_dsize_label.set_markup("{}".format(self.Package.beauty_size(self.ret["download_size"])))
            self.dapp_dsize_box.set_visible(True)
        else:
            self.dapp_dsize_box.set_visible(False)

        if self.ret["install_size"] and self.ret["install_size"] is not None and self.ret["install_size"] > 0:
            self.dapp_isize_label.set_markup("{}".format(self.Package.beauty_size(self.ret["install_size"])))
            self.dapp_isize_box.set_visible(True)
        else:
            self.dapp_isize_box.set_visible(False)

        isinstalled = self.Package.isinstalled(self.appname)

        if isinstalled is not None:
            if isinstalled:
                self.dSizeTitle.set_text(_("Installed Size"))
                self.dSize.set_text("{}".format(self.Package.beauty_size(self.ret["freed_size"])))
                self.dSizeGrid.set_tooltip_text(None)
            else:
                self.dSizeTitle.set_text(_("Download Size"))
                self.dSize.set_text("{}".format(self.Package.beauty_size(self.ret["download_size"])))
                self.dSizeGrid.set_tooltip_text("{}: {}".format(
                    _("Installed Size"), self.Package.beauty_size(self.ret["install_size"])))
        else:
            self.dSize.set_markup(_("None"))
            self.dSizeTitle.set_text(_("Download Size"))
            self.dSizeGrid.set_tooltip_text(None)

    def myapps_worker_thread(self):
        for row in self.MyAppsListBox:
            self.MyAppsListBox.remove(row)
        myapps = self.myapps_worker()
        GLib.idle_add(self.on_myapps_worker_done, myapps)

    def myapps_worker(self):
        return self.Package.get_installed_apps()

    def on_myapps_worker_done(self, myapps):
        for pkg in myapps:
            self.addtoMyApps(pkg)
        GLib.idle_add(self.MyAppsListBox.show_all)
        GLib.idle_add(self.controlArgs)
        self.Logger.info("on_myapps_worker_done")

    def myappsdetail_worker_thread(self, app, popup=False):
        myappdetails = self.myappsdetail_worker(app)
        GLib.idle_add(self.on_myappsdetail_worker_done, myappdetails, popup)

    def myappsdetail_worker(self, app):

        valid, myapp_details, myapp_package = self.Package.myapps_remove_details(app["filename"])
        self.Logger.info("{}".format(myapp_details))
        return valid, myapp_details, myapp_package, app["name"], app["icon"], app["filename"], app["description"]

    def set_myapp_popup_details(self, myapp):

        self.ui_myapp_pop_toremove_box.set_visible(False)
        self.ui_myapp_pop_toinstall_box.set_visible(False)
        self.ui_myapp_pop_broken_box.set_visible(False)
        self.ui_myapp_pop_fsize_box.set_visible(False)
        self.ui_myapp_pop_dsize_box.set_visible(False)
        self.ui_myapp_pop_isize_box.set_visible(False)

        valid, details, package, name, icon, desktop, description = myapp
        if valid and details is not None:
            self.ui_myapp_pop_app.set_markup(
                "<span size='large'><b>{}</b></span>".format(GLib.markup_escape_text(name, -1)))
            self.ui_myapp_pop_package.set_markup("<i>{}</i>".format(package))
            self.ui_myapp_pop_icon.set_from_pixbuf(self.getMyAppIcon(icon, size=64))
            self.ui_myapp_pop_uninstall_button.set_sensitive(True)

            if details["to_delete"] and details["to_delete"] is not None:
                self.ui_myapp_pop_toremove_label.set_markup(
                    "{}".format(", ".join(details["to_delete"])))
                self.ui_myapp_pop_toremove_box.set_visible(True)

            if details["to_install"] and details["to_install"] is not None:
                self.ui_myapp_pop_toinstall_label.set_markup(
                    "{}".format(", ".join(details["to_install"])))
                self.ui_myapp_pop_toinstall_box.set_visible(True)

            if details["broken"] and details["broken"] is not None:
                self.ui_myapp_pop_broken_label.set_markup(
                    "{}".format(", ".join(details["broken"])))
                self.ui_myapp_pop_broken_box.set_visible(True)

            if details["freed_size"] and details["freed_size"] is not None and details["freed_size"] > 0:
                self.ui_myapp_pop_fsize_label.set_markup(
                    "{}".format(self.Package.beauty_size(details["freed_size"])))
                self.ui_myapp_pop_fsize_box.set_visible(True)

            if details["download_size"] and details["download_size"] is not None and details["download_size"] > 0:
                self.ui_myapp_pop_dsize_label.set_markup(
                    "{}".format(self.Package.beauty_size(details["download_size"])))
                self.ui_myapp_pop_dsize_box.set_visible(True)

            if details["install_size"] and details["install_size"] is not None and details["install_size"] > 0:
                self.ui_myapp_pop_isize_label.set_markup(
                    "{}".format(self.Package.beauty_size(details["install_size"])))
                self.ui_myapp_pop_isize_box.set_visible(True)

            self.ui_myapp_pop_stack.set_visible_child_name("details")
            self.ui_myapp_pop_uninstall_button.grab_focus()


        else:
            self.Logger.info("package not found")
            self.ui_myapp_pop_stack.set_visible_child_name("notfound")
            self.ui_myapp_pop_notfound_image.set_from_pixbuf(self.getMyAppIcon(icon, size=64))
            self.ui_myapp_pop_notfound_name.set_markup("<span size='large'><b>{}</b></span>".format(name))

    def on_myappsdetail_worker_done(self, myapp, popup=False):
        self.clicked_myapp = myapp
        self.myapp_toremove_list = []
        self.myapp_toremove = ""
        self.myapp_toremove_desktop = ""
        self.ui_myapp_to_store_button.set_visible(False)
        self.ui_myapp_to_store_button.name = ""
        self.ui_myapps_spinner.stop()
        self.ui_myapp_toremove_box.set_visible(False)
        self.ui_myapp_toinstall_box.set_visible(False)
        self.ui_myapp_broken_box.set_visible(False)
        self.ui_myapp_fsize_box.set_visible(False)
        self.ui_myapp_dsize_box.set_visible(False)
        self.ui_myapp_isize_box.set_visible(False)

        valid, details, package, name, icon, desktop, description = myapp
        if valid and details is not None:
            self.ui_myapp_pop_app.set_markup(
                "<span size='large'><b>{}</b></span>".format(GLib.markup_escape_text(name, -1)))
            self.ui_myapp_pop_package.set_markup("<i>{}</i>".format(package))
            self.ui_myapp_pop_icon.set_from_pixbuf(self.getMyAppIcon(icon, size=64))
            self.ui_myapp_pop_uninstall_button.set_sensitive(True)
            self.ma_action_buttonbox.set_sensitive(True)
            self.ui_myapps_app.set_markup(
                "<span size='x-large'><b>{}</b></span>".format(GLib.markup_escape_text(name, -1)))
            self.ui_myapps_package.set_markup("<i>{}</i>".format(package))
            self.ui_myapps_icon.set_from_pixbuf(self.getMyAppIcon(icon, size=128))
            self.ui_myapps_description.set_markup("{}".format(description))

            name = any(package == e["name"] for e in self.fullapplist)
            if name:
                self.ui_myapp_to_store_button.set_visible(True)
                self.ui_myapp_to_store_button.name = package
            else:
                command = any(package in e["command"][self.locale] for e in self.fullapplist if e["command"])
                if command:
                    appname = None
                    for app in self.fullapplist:
                        if app["command"]:
                            if package in app["command"][self.locale]:
                                appname = app["name"]
                                break
                    if appname:
                        self.ui_myapp_to_store_button.set_visible(True)
                        self.ui_myapp_to_store_button.name = appname

            if details["to_delete"] and details["to_delete"] is not None:
                self.ui_myapp_pop_toremove_label.set_markup(
                    "{}".format(", ".join(details["to_delete"])))
                self.ui_myapp_pop_toremove_box.set_visible(True)
                self.ui_myapp_toremove_label.set_markup(
                    "{}".format(", ".join(details["to_delete"])))
                self.ui_myapp_toremove_box.set_visible(True)
                self.myapp_toremove_list = details["to_delete"]
                self.myapp_toremove = package
                self.myapp_toremove_desktop = desktop

            if details["to_install"] and details["to_install"] is not None:
                self.ui_myapp_pop_toinstall_label.set_markup(
                    "{}".format(", ".join(details["to_install"])))
                self.ui_myapp_pop_toinstall_box.set_visible(True)
                self.ui_myapp_toinstall_label.set_markup(
                    "{}".format(", ".join(details["to_install"])))
                self.ui_myapp_toinstall_box.set_visible(True)

            if details["broken"] and details["broken"] is not None:
                self.ui_myapp_pop_broken_label.set_markup(
                    "{}".format(", ".join(details["broken"])))
                self.ui_myapp_pop_broken_box.set_visible(True)
                self.ui_myapp_broken_label.set_markup(
                    "{}".format(", ".join(details["broken"])))
                self.ui_myapp_broken_box.set_visible(True)

            if details["freed_size"] and details["freed_size"] is not None and details["freed_size"] > 0:
                self.ui_myapp_pop_fsize_label.set_markup(
                    "{}".format(self.Package.beauty_size(details["freed_size"])))
                self.ui_myapp_pop_fsize_box.set_visible(True)
                self.ui_myapp_fsize_label.set_markup(
                    "{}".format(self.Package.beauty_size(details["freed_size"])))
                self.ui_myapp_fsize_box.set_visible(True)
                self.ma_size.set_markup(
                    "{}".format(self.Package.beauty_size(details["freed_size"])))

            if details["download_size"] and details["download_size"] is not None and details["download_size"] > 0:
                self.ui_myapp_pop_dsize_label.set_markup(
                    "{}".format(self.Package.beauty_size(details["download_size"])))
                self.ui_myapp_pop_dsize_box.set_visible(True)
                self.ui_myapp_dsize_label.set_markup(
                    "{}".format(self.Package.beauty_size(details["download_size"])))
                self.ui_myapp_dsize_box.set_visible(True)

            if details["install_size"] and details["install_size"] is not None and details["install_size"] > 0:
                self.ui_myapp_pop_isize_label.set_markup(
                    "{}".format(self.Package.beauty_size(details["install_size"])))
                self.ui_myapp_pop_isize_box.set_visible(True)
                self.ui_myapp_isize_label.set_markup(
                    "{}".format(self.Package.beauty_size(details["install_size"])))
                self.ui_myapp_isize_box.set_visible(True)

            isinstalled = self.Package.isinstalled(package)

            if isinstalled is not None:
                if isinstalled:
                    version = self.Package.installed_version(package)
                else:
                    version = self.Package.candidate_version(package)
            else:
                version = ""

            maintainer_name, maintainer_mail, homepage, arch = self.Package.get_records(package)
            origins = self.Package.origins(package)
            section = self.Package.get_section(package)

            if maintainer_name != "":
                self.ma_maintainername.set_markup("<i>{}</i>".format(maintainer_name))
            else:
                self.ma_maintainername.set_text("-")

            if maintainer_mail != "":
                self.ma_maintainermail.set_markup("<a title='{}' href='mailto:{}'>{}</a>".format(
                    GLib.markup_escape_text(maintainer_mail, -1),
                    GLib.markup_escape_text(maintainer_mail, -1),
                    "E-Mail"))
            else:
                self.ma_maintainermail.set_text("-")

            if homepage != "":
                self.ma_homepage.set_markup("<a title='{}' href='{}'>{}</a>".format(
                    GLib.markup_escape_text(homepage, -1),
                    GLib.markup_escape_text(homepage, -1),
                    "Website"))
            else:
                self.ma_homepage.set_text("-")

            # if section != "":
            #     self.ma_section.set_text(section)
            # else:
            #     self.ma_section.set_text("-")

            # if arch != "":
            #     self.ma_architecture.set_text(arch)
            # else:
            #     self.ma_architecture.set_text("-")

            if version is not None and version != "":
                self.ma_version.set_text(version)
            else:
                self.ma_version.set_text("-")

            if origins is not None and origins != "":
                self.ma_origin.set_markup("{} {}".format(origins.origin, origins.component))
            else:
                self.ma_origin.set_text("-")

            self.ui_myapp_pop_stack.set_visible_child_name("details")
            self.ui_myapp_pop_uninstall_button.grab_focus()
            if not popup:
                self.myappsstack.set_visible_child_name("details")
                self.myappsdetailsstack.set_visible_child_name("details")
                self.menubackbutton.set_sensitive(True)

        else:
            self.Logger.info("package not found")
            self.ui_myapp_pop_stack.set_visible_child_name("notfound")
            self.ui_myapp_pop_notfound_image.set_from_pixbuf(self.getMyAppIcon(icon, size=64))
            self.ui_myapp_pop_notfound_name.set_markup("<span size='large'><b>{}</b></span>".format(name))
            self.ui_myapps_notfoundname_box.set_visible(True)
            self.ui_myapps_notfoundname_image.set_from_pixbuf(self.getMyAppIcon(icon, size=96))
            self.ui_myapps_notfoundname_name.set_markup("<span size='large'><b>{}</b></span>".format(name))
            if not popup:
                self.myappsstack.set_visible_child_name("notfound")

    def open_store_page_from_myapps(self, packagename):
        self.frommyapps = True
        self.frommostapps = False
        self.fromqueue = False
        self.fromeditorapps = False
        self.myappname = packagename
        self.on_PardusAppsIconView_selection_changed(packagename)

    def on_ui_myapp_to_store_button_clicked(self, button):
        self.open_store_page_from_myapps(button.name)

    def on_MyAppsDetailsPopover_closed(self, popover):
        self.ui_myapp_pop_spinner.stop()
        self.ui_myapp_pop_stack.set_visible_child_name("spinner")
        self.ui_myapp_pop_app.set_can_focus(False)
        self.ui_myapp_pop_package.set_can_focus(False)
        self.ui_myapp_pop_toremove_label.set_can_focus(False)
        self.ui_myapp_pop_toinstall_label.set_can_focus(False)
        self.ui_myapp_pop_broken_label.set_can_focus(False)
        self.ui_myapp_pop_fsize_label.set_can_focus(False)
        self.ui_myapp_pop_dsize_label.set_can_focus(False)
        self.ui_myapp_pop_isize_label.set_can_focus(False)

    def on_ui_myapp_pop_close_clicked(self, button):
        self.MyAppsDetailsPopover.popdown()

    def on_ma_action_info_button_clicked(self, button):
        self.set_myapp_popup_details(self.clicked_myapp)
        self.MyAppsDetailsPopover.set_relative_to(button)
        self.MyAppsDetailsPopover.popup()

    def on_ma_details_open_button_clicked(self, button):
        valid, details, package, name, icon, desktop, description = self.clicked_myapp
        self.openDesktop(os.path.basename(desktop))

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
            self.Logger.info("comment star error")

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
            self.Logger.info("comment star error")

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

                    if comment["distro"] is None or comment["distro"] == "":
                        comment["distro"] = _("unknown")

                    if comment["appversion"] is None or comment["appversion"] == "":
                        comment["appversion"] = _("unknown")

                    label_author = Gtk.Label.new()
                    label_author.set_markup("<b>{}</b>".format(comment["author"]))
                    label_author.set_selectable(True)

                    label_date = Gtk.Label.new()
                    label_date.set_markup("{}".format(comment["date"]))
                    label_date.set_selectable(True)

                    label_distro = Gtk.Label.new()
                    label_distro.set_markup("<small>{}: {}</small>".format(_("Distro"), comment["distro"]))
                    label_distro.set_selectable(True)
                    label_distro.props.halign = Gtk.Align.START

                    label_appversion = Gtk.Label.new()
                    label_appversion.set_markup("<small>{}: {}</small>".format(_("App Version"), comment["appversion"]))
                    label_appversion.set_selectable(True)
                    label_appversion.props.halign = Gtk.Align.START

                    hbox_top = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
                    hbox_top.set_margin_top(8)
                    hbox_top.pack_start(self.cs1, False, False, 0)
                    hbox_top.pack_start(self.cs2, False, False, 0)
                    hbox_top.pack_start(self.cs3, False, False, 0)
                    hbox_top.pack_start(self.cs4, False, False, 0)
                    hbox_top.pack_start(self.cs5, False, False, 0)
                    hbox_top.pack_start(label_author, False, False, 8)
                    hbox_top.pack_end(label_date, False, False, 0)

                    label_comment = Gtk.Label.new()
                    label_comment.set_text("{}".format(comment["comment"]))
                    label_comment.set_selectable(True)
                    label_comment.set_line_wrap(True)
                    label_comment.set_line_wrap_mode(2)  # WORD_CHAR
                    label_comment.props.halign = Gtk.Align.START

                    sep = Gtk.VSeparator.new()
                    sep.set_margin_top(8)

                    main_vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 8)
                    main_vbox.pack_start(hbox_top, False, False, 0)
                    main_vbox.pack_start(label_distro, False, False, 0)
                    main_vbox.pack_start(label_appversion, False, False, 0)
                    main_vbox.pack_start(label_comment, False, False, 0)
                    main_vbox.pack_start(sep, False, False, 0)

                    row = Gtk.ListBoxRow()
                    row.add(main_vbox)

                    self.PardusCommentListBox.add(row)

                self.PardusCommentListBox.show_all()

    def on_par_desc_more_clicked(self, button):

        self.dDescriptionLabel.set_text(self.description)
        button.set_visible(False)

    def Request(self, status, response, appname=""):
        if status:
            if response["response-type"] == 10 and appname == self.getActiveAppOnUI():
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
                        self.addCommentButton.set_visible(True)
                        self.addCommentInfoLabel.set_visible(True)
                    else:
                        self.addCommentButton.set_visible(False)
                        self.addCommentInfoLabel.set_visible(False)

                    if self.rate_comment == "" or self.rate_comment is None:
                        self.wpcCommentBox.set_visible(False)
                        self.addCommentButton.set_label(_("Add Comment"))
                    else:
                        self.wpcCommentBox.set_visible(True)
                        self.addCommentButton.set_label(_("Edit Comment"))

                    if response["rating"]["justrate"]:

                        if response["rating"]["rate"]["recommentable"]:
                            # scroll to add comment
                            vadj = self.PardusAppDetailScroll.get_vadjustment()
                            bot = vadj.get_upper()
                            vadj.set_value(bot)
                            self.PardusAppDetailScroll.set_vadjustment(vadj)

                            self.setWpcStar(response["rating"]["rate"]["individual"])
                            self.wpcAuthor.set_text(str(response["rating"]["rate"]["author"]))
                            start, end = self.wpcComment.get_buffer().get_bounds()
                            self.wpcComment.get_buffer().delete(start, end)
                            self.wpcComment.get_buffer().insert(self.wpcComment.get_buffer().get_end_iter(),
                                                                "{}".format(response["rating"]["rate"]["comment"]))

                            self.CommentsNotebook.set_current_page(2)
                            self.wpcComment.grab_focus()

                            self.wpcinfoLabel.set_visible(True)

                        else:
                            self.commentstack.set_visible_child_name("alreadysent")
                            self.wpcgetnameLabel.set_text(str(response["rating"]["rate"]["author"]))
                            self.wpcgetcommentLabel.set_text(str(response["rating"]["rate"]["comment"]))

                    else:
                        self.commentstack.set_visible_child_name("sendresult")
                        self.wpcresultLabel.set_text(
                            _("Your comment has been sent successfully. It will be published after approval."))
                else:
                    if response["rating"]["justrate"]:
                        self.Logger.info("justrate error")
                    else:
                        self.wpcformcontrolLabel.set_visible(True)
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
                        self.SuggestInfoLabel.set_markup("<b><span color='red'>{}</span></b>".format(
                            _("Please try again soon")))
                    else:
                        self.SuggestInfoLabel.set_markup("<b><span color='red'>{}</span></b>".format(
                            _("Error")))
        else:
            self.wpcresultLabel.set_text(_("Error"))

    def Detail(self, status, response, appname=""):
        if status and appname == self.getActiveAppOnUI():
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
                    self.addCommentButton.set_visible(True)
                    self.addCommentInfoLabel.set_visible(True)
                else:
                    self.addCommentButton.set_visible(False)
                    self.addCommentInfoLabel.set_visible(False)

                if self.rate_comment == "" or self.rate_comment is None:
                    self.wpcCommentBox.set_visible(False)
                    self.addCommentButton.set_label(_("Add Comment"))
                else:
                    self.wpcCommentBox.set_visible(True)
                    self.addCommentButton.set_label(_("Edit Comment"))

            self.rate_average = response["details"]["rate"]["average"]
            self.setAppStar(response["details"]["rate"]["average"])

            self.setPardusRatings(response["details"]["rate"]["count"], response["details"]["rate"]["average"],
                                  response["details"]["rate"]["rates"]["1"], response["details"]["rate"]["rates"]["2"],
                                  response["details"]["rate"]["rates"]["3"], response["details"]["rate"]["rates"]["4"],
                                  response["details"]["rate"]["rates"]["5"])

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

    def get_star_subpoint(self, fraction):
        if fraction >= 8:
            return self.staron_08
        elif fraction >= 5:
            return self.staron_05
        elif fraction >= 3:
            return self.staron_03
        else:
            return self.staroff

    def setAppStar(self, average):
        point = int("{:.1f}".format(average).split(".")[1])
        average = int(average)
        if average == 0:
            self.dtStar1.set_from_pixbuf(self.get_star_subpoint(point))
            self.dtStar2.set_from_pixbuf(self.staroff)
            self.dtStar3.set_from_pixbuf(self.staroff)
            self.dtStar4.set_from_pixbuf(self.staroff)
            self.dtStar5.set_from_pixbuf(self.staroff)
        elif average == 1:
            self.dtStar1.set_from_pixbuf(self.staron)
            self.dtStar2.set_from_pixbuf(self.get_star_subpoint(point))
            self.dtStar3.set_from_pixbuf(self.staroff)
            self.dtStar4.set_from_pixbuf(self.staroff)
            self.dtStar5.set_from_pixbuf(self.staroff)
        elif average == 2:
            self.dtStar1.set_from_pixbuf(self.staron)
            self.dtStar2.set_from_pixbuf(self.staron)
            self.dtStar3.set_from_pixbuf(self.get_star_subpoint(point))
            self.dtStar4.set_from_pixbuf(self.staroff)
            self.dtStar5.set_from_pixbuf(self.staroff)
        elif average == 3:
            self.dtStar1.set_from_pixbuf(self.staron)
            self.dtStar2.set_from_pixbuf(self.staron)
            self.dtStar3.set_from_pixbuf(self.staron)
            self.dtStar4.set_from_pixbuf(self.get_star_subpoint(point))
            self.dtStar5.set_from_pixbuf(self.staroff)
        elif average == 4:
            self.dtStar1.set_from_pixbuf(self.staron)
            self.dtStar2.set_from_pixbuf(self.staron)
            self.dtStar3.set_from_pixbuf(self.staron)
            self.dtStar4.set_from_pixbuf(self.staron)
            self.dtStar5.set_from_pixbuf(self.get_star_subpoint(point))
        elif average == 5:
            self.dtStar1.set_from_pixbuf(self.staron)
            self.dtStar2.set_from_pixbuf(self.staron)
            self.dtStar3.set_from_pixbuf(self.staron)
            self.dtStar4.set_from_pixbuf(self.staron)
            self.dtStar5.set_from_pixbuf(self.staron)
        else:
            self.Logger.info("star error")

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
                if "rating" and "user_display" and "date_created" and "summary" and "description" and "distro" and "version" in comment:
                    if self.isCommentClean(comment["summary"]) and self.isCommentClean(
                            comment["description"]) and self.isCommentClean(comment["user_display"]):
                        self.setGnomeCommentStar(comment["rating"] / 20)

                        label_author = Gtk.Label.new()
                        label_author.set_markup("<b>{}</b>".format(comment["user_display"]))
                        label_author.set_selectable(True)

                        label_date = Gtk.Label.new()
                        label_date.set_markup("{}".format(datetime.fromtimestamp(comment["date_created"])))
                        label_date.set_selectable(True)

                        label_distro = Gtk.Label.new()
                        label_distro.set_markup("<small>{}: {}</small>".format(_("Distro"), comment["distro"]))
                        label_distro.set_selectable(True)
                        label_distro.props.halign = Gtk.Align.START

                        label_appversion = Gtk.Label.new()
                        label_appversion.set_markup(
                            "<small>{}: {}</small>".format(_("App Version"), comment["version"]))
                        label_appversion.set_selectable(True)
                        label_appversion.props.halign = Gtk.Align.START

                        hbox_top = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
                        hbox_top.set_margin_top(8)
                        hbox_top.pack_start(self.gcs1, False, False, 0)
                        hbox_top.pack_start(self.gcs2, False, False, 0)
                        hbox_top.pack_start(self.gcs3, False, False, 0)
                        hbox_top.pack_start(self.gcs4, False, False, 0)
                        hbox_top.pack_start(self.gcs5, False, False, 0)
                        hbox_top.pack_start(label_author, False, False, 8)
                        hbox_top.pack_end(label_date, False, False, 0)

                        label_comment = Gtk.Label.new()
                        label_comment.set_text("{}\n{}".format(comment["summary"], comment["description"]))
                        label_comment.set_selectable(True)
                        label_comment.set_line_wrap(True)
                        label_comment.set_line_wrap_mode(2)  # WORD_CHAR
                        label_comment.props.halign = Gtk.Align.START

                        sep = Gtk.VSeparator.new()
                        sep.set_margin_top(8)

                        main_vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 8)
                        main_vbox.pack_start(hbox_top, False, False, 0)
                        main_vbox.pack_start(label_distro, False, False, 0)
                        main_vbox.pack_start(label_appversion, False, False, 0)
                        main_vbox.pack_start(label_comment, False, False, 0)
                        main_vbox.pack_start(sep, False, False, 0)

                        row = Gtk.ListBoxRow()
                        row.add(main_vbox)

                        if lang == "tr":
                            self.GnomeCommentListBoxTR.add(row)
                        elif lang == "en":
                            self.GnomeCommentListBoxEN.add(row)
                    else:
                        try:
                            self.Logger.info("Comment is not clean, app_id: {}, review_id : {}".format(
                                comment["app_id"], comment["review_id"]))
                        except Exception as e:
                            self.Logger.exception("{}".format(e))

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
            version = self.Package.installed_version(self.appname)
            if version is None:
                version = ""
            dic = {"app": self.appname, "mac": self.mac, "value": widget.get_name()[-1],
                   "author": self.UserSettings.user_real_name, "installed": installed, "comment": "",
                   "appversion": version, "distro": self.user_distro_full, "justrate": True}
            self.AppRequest.send("POST", self.Server.serverurl + self.Server.serversendrate, dic, self.appname)
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

    def on_wpcStar_button_press_event(self, widget, event):
        self.setWpcStar(int(widget.get_name()[-1]))

    def on_addCommentButton_clicked(self, button):
        self.setWpcStar(self.rate_individual)
        self.wpcAuthor.set_text(self.rate_author)
        start, end = self.wpcComment.get_buffer().get_bounds()
        self.wpcComment.get_buffer().delete(start, end)
        self.wpcComment.get_buffer().insert(self.wpcComment.get_buffer().get_end_iter(), self.rate_comment)

        self.commentstack.set_visible_child_name("sendcomment")

    def on_wpcSendButton_clicked(self, button):
        self.Logger.info("on_wpcSendButton_clicked")

        author = self.wpcAuthor.get_text().strip()
        start, end = self.wpcComment.get_buffer().get_bounds()
        comment = self.wpcComment.get_buffer().get_text(start, end, True).strip()
        value = self.wpcstar
        status = True
        if value == 0 or comment == "" or author == "":
            self.wpcformcontrolLabel.set_visible(True)
            self.wpcformcontrolLabel.set_text(_("Cannot be null"))
        else:
            installed = self.Package.isinstalled(self.appname)
            if installed is None:
                installed = False
            if installed:
                version = self.Package.installed_version(self.appname)
                if version is None:
                    version = ""
                dic = {"mac": self.mac, "author": author, "comment": comment, "value": value, "app": self.appname,
                       "installed": installed, "appversion": version, "distro": self.user_distro_full,
                       "justrate": False}
                try:
                    self.AppRequest.send("POST", self.Server.serverurl + self.Server.serversendrate, dic, self.appname)
                except Exception as e:
                    status = False
                    self.commentstack.set_visible_child_name("sendresult")
                    self.wpcresultLabel.set_text(str(e))
                if status:
                    self.wpcSendButton.set_sensitive(False)
                else:
                    self.wpcresultLabel.set_text(_("Error"))
            else:
                self.wpcformcontrolLabel.set_visible(True)
                self.wpcformcontrolLabel.set_markup(
                    "<span color='red'>{}</span>".format(_("You need to install the application")))

    def setWpcStar(self, rate):

        if rate == 0:
            self.wpcStar1.set_from_pixbuf(self.wpcstaroff)
            self.wpcStar2.set_from_pixbuf(self.wpcstaroff)
            self.wpcStar3.set_from_pixbuf(self.wpcstaroff)
            self.wpcStar4.set_from_pixbuf(self.wpcstaroff)
            self.wpcStar5.set_from_pixbuf(self.wpcstaroff)
            self.wpcinfoLabel.set_visible(False)
            self.wpcStarLabel.set_visible(True)
            self.wpcStarLabel.set_markup(_("How many stars would you give this app?"))
        elif rate == 1:
            self.wpcStar1.set_from_pixbuf(self.wpcstaron)
            self.wpcStar2.set_from_pixbuf(self.wpcstaroff)
            self.wpcStar3.set_from_pixbuf(self.wpcstaroff)
            self.wpcStar4.set_from_pixbuf(self.wpcstaroff)
            self.wpcStar5.set_from_pixbuf(self.wpcstaroff)
            self.wpcStarLabel.set_visible(False)
            # self.wpcStarLabel.set_markup("<b>{}</b>".format(_("Hate it")))
            self.wpcstar = 1
        elif rate == 2:
            self.wpcStar1.set_from_pixbuf(self.wpcstaron)
            self.wpcStar2.set_from_pixbuf(self.wpcstaron)
            self.wpcStar3.set_from_pixbuf(self.wpcstaroff)
            self.wpcStar4.set_from_pixbuf(self.wpcstaroff)
            self.wpcStar5.set_from_pixbuf(self.wpcstaroff)
            self.wpcStarLabel.set_visible(False)
            # self.wpcStarLabel.set_markup("<b>{}</b>".format(_("Don't like it")))
            self.wpcstar = 2
        elif rate == 3:
            self.wpcStar1.set_from_pixbuf(self.wpcstaron)
            self.wpcStar2.set_from_pixbuf(self.wpcstaron)
            self.wpcStar3.set_from_pixbuf(self.wpcstaron)
            self.wpcStar4.set_from_pixbuf(self.wpcstaroff)
            self.wpcStar5.set_from_pixbuf(self.wpcstaroff)
            self.wpcStarLabel.set_visible(False)
            # self.wpcStarLabel.set_markup("<b>{}</b>".format(_("It's OK")))
            self.wpcstar = 3
        elif rate == 4:
            self.wpcStar1.set_from_pixbuf(self.wpcstaron)
            self.wpcStar2.set_from_pixbuf(self.wpcstaron)
            self.wpcStar3.set_from_pixbuf(self.wpcstaron)
            self.wpcStar4.set_from_pixbuf(self.wpcstaron)
            self.wpcStar5.set_from_pixbuf(self.wpcstaroff)
            self.wpcStarLabel.set_visible(False)
            # self.wpcStarLabel.set_markup("<b>{}</b>".format(_("Like it")))
            self.wpcstar = 4

        elif rate == 5:
            self.wpcStar1.set_from_pixbuf(self.wpcstaron)
            self.wpcStar2.set_from_pixbuf(self.wpcstaron)
            self.wpcStar3.set_from_pixbuf(self.wpcstaron)
            self.wpcStar4.set_from_pixbuf(self.wpcstaron)
            self.wpcStar5.set_from_pixbuf(self.wpcstaron)
            self.wpcStarLabel.set_visible(False)
            # self.wpcStarLabel.set_markup("<b>{}</b>".format(_("Love it")))
            self.wpcstar = 5
        else:
            self.Logger.info("wpc star error")

    def PardusCategoryFilterFunction(self, model, iteration, data):
        def control_show_filter(show_all, show_installed, app_name=""):
            if show_all:
                return True
            else:
                if show_installed:
                    return self.Package.isinstalled(app_name)
                else:
                    return not self.Package.isinstalled(app_name)

        search_entry_text = self.pardus_searchentry.get_text()
        categorynumber = int(model[iteration][2])
        category = list(model[iteration][4].split(","))
        subcategory = list(model[iteration][5].split(","))
        # category = model[iteration][4]
        appname = model[iteration][1]
        # showinstalled = self.pardusicb.get_active()
        pn_en = ""
        pn_tr = ""
        desc_en = ""
        desc_tr = ""

        showall = True
        showinstalled = None

        if self.ui_showall_button.get_active():
            showall = True
            showinstalled = None
        elif self.ui_showinstalled_button.get_active():
            showall = False
            showinstalled = True
        elif self.ui_shownotinstalled_button.get_active():
            showall = False
            showinstalled = False

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
                return control_show_filter(showall, showinstalled, appname)
        else:
            if self.PardusCurrentCategorySubCats and self.PardusCurrentCategoryExternal:
                for i in self.applist:
                    if i["name"] == appname:
                        if i["external"]:
                            if i["external"]["reponame"] == self.externalreponame:
                                return control_show_filter(showall, showinstalled, appname)
            else:
                if self.PardusCurrentCategoryString == "all" or self.PardusCurrentCategoryString == "tümü":
                    return control_show_filter(showall, showinstalled, appname)
                else:
                    if self.PardusCurrentCategoryString in category:
                        if self.SubCatCombo.get_active_text() is not None:
                            if self.SubCatCombo.get_active_text().lower() == "all" or self.SubCatCombo.get_active_text().lower() == "tümü":
                                return control_show_filter(showall, showinstalled, appname)
                            else:
                                if self.PardusCurrentCategorySubCategories:
                                    if self.SubCatCombo.get_active_text().lower() in subcategory:
                                        return control_show_filter(showall, showinstalled, appname)
                        else:
                            return control_show_filter(showall, showinstalled, appname)

    def on_ui_showinstalled_button_clicked(self, button):
        if button.get_active():
            self.Logger.info("active : installed")
            self.ui_showall_button.set_active(False)
            self.ui_shownotinstalled_button.set_active(False)
            self.PardusCategoryFilter.refilter()
            self.set_app_count_label()
        else:
            if not self.ui_showall_button.get_active() and not self.ui_shownotinstalled_button.get_active():
                button.set_active(True)

    def on_ui_shownotinstalled_button_clicked(self, button):
        if button.get_active():
            self.Logger.info("active : notinstalled")
            self.ui_showall_button.set_active(False)
            self.ui_showinstalled_button.set_active(False)
            self.PardusCategoryFilter.refilter()
            self.set_app_count_label()
        if not self.ui_showall_button.get_active() and not self.ui_showinstalled_button.get_active():
            button.set_active(True)

    def on_ui_showall_button_clicked(self, button):
        if button.get_active():
            self.Logger.info("active : showall")
            self.ui_showinstalled_button.set_active(False)
            self.ui_shownotinstalled_button.set_active(False)
            self.PardusCategoryFilter.refilter()
            self.set_app_count_label()
        if not self.ui_showinstalled_button.get_active() and not self.ui_shownotinstalled_button.get_active():
            button.set_active(True)

    def set_app_count_label(self):
        count = len(self.PardusCategoryFilter)
        if self.ui_showall_button.get_active():
            status_text = _("available")
        elif self.ui_showinstalled_button.get_active():
            status_text = _("installed")
        elif self.ui_shownotinstalled_button.get_active():
            status_text = _("not installed")

        app_text = _("app")
        if count > 1:
            app_text = _("apps")

        self.ui_showappcount_label.set_markup("<small>{} {} {}</small>".format(count, app_text, status_text))

    def on_SubCatCombo_changed(self, combo_box):
        if combo_box.get_active_text() is not None:
            self.Logger.info("on_SubCatCombo_changed : {}".format(combo_box.get_active_text()))
            self.PardusCategoryFilter.refilter()
            self.set_app_count_label()

    def on_sortPardusAppsCombo_changed(self, combo_box):
        if combo_box.get_active() == 0:  # sort by name
            self.applist = sorted(self.applist, key=lambda x: locale.strxfrm(x["prettyname"][self.locale]))
            GLib.idle_add(self.PardusAppListStore.clear)
            self.setPardusApps()
        elif combo_box.get_active() == 1:  # sort by download
            self.applist = sorted(self.applist, key=lambda x: (x["download"], x["rate_average"]), reverse=True)
            GLib.idle_add(self.PardusAppListStore.clear)
            self.setPardusApps()
        elif combo_box.get_active() == 2:  # sort by popularity
            self.applist = sorted(self.applist,
                                  key=lambda x: (x["popularity"] if "popularity" in x.keys() else x["rate_average"],
                                                 x["download"]), reverse=True)
            GLib.idle_add(self.PardusAppListStore.clear)
            self.setPardusApps()
        elif combo_box.get_active() == 3:  # sort by last added
            self.applist = sorted(self.applist, key=lambda x: datetime.strptime(x["date"], "%d-%m-%Y %H:%M"),
                                  reverse=True)
            GLib.idle_add(self.PardusAppListStore.clear)
            self.setPardusApps()

    def on_MostFlowBox_child_activated(self, flow_box, child):

        self.mostappname = child.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[
            1].name
        self.fromqueue = False
        self.frommyapps = False

        self.on_PardusAppsIconView_selection_changed(self.mostappname)

    def on_HomeCategoryFlowBox_child_activated(self, flow_box, child):

        self.set_app_count_label()

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
            self.PardusCurrentCategoryExternal, self.PardusCurrentCategorySubCategories = self.get_category_name(
            self.PardusCurrentCategory)

        self.Logger.info("HomeCategory: {} {} {} {} {}".format(self.PardusCurrentCategory,
                                                               self.PardusCurrentCategoryString,
                                                               self.PardusCurrentCategorySubCats,
                                                               self.PardusCurrentCategoryExternal,
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
            self.ui_showapps_buttonbox.set_visible(False)
            self.ui_showappcount_label.set_visible(False)
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
            self.ui_showapps_buttonbox.set_visible(True)
            self.ui_showappcount_label.set_visible(True)
            self.sortPardusAppsCombo.set_visible(True)
            self.pardusAppsStack.set_visible_child_name("normal")
            self.PardusCategoryFilter.refilter()
            self.set_app_count_label()

    def on_SubCategoryFlowBox_child_activated(self, flow_box, child):
        self.externalreponame = child.get_children()[0].name
        self.ui_showapps_buttonbox.set_visible(True)
        self.ui_showappcount_label.set_visible(True)
        self.sortPardusAppsCombo.set_visible(True)
        self.PardusCategoryFilter.refilter()
        self.set_app_count_label()
        self.pardusAppsStack.set_visible_child_name("normal")

    def on_HomeCategoryFlowBox_selected_children_changed(self, flow_box):
        self.Logger.info("on_HomeCategoryFlowBox_selected_children_changed")
        self.isPardusSearching = False

    def on_QueueListBox_row_activated(self, list_box, row):
        self.queueappname = row.get_children()[0].name
        self.Logger.info("queueappname : {}".format(self.queueappname))
        self.fromqueue = True
        self.frommostapps = False
        self.fromdetails = False
        self.fromrepoapps = False
        self.repoappclicked = False
        self.on_PardusAppsIconView_selection_changed(self.queueappname)

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

    def on_dActionInfoButton_clicked(self, button):
        self.RequiredChangesPopover.popup()

    def on_dActionCancelButton_clicked(self, button):
        self.Logger.info("Cancelling {} {}".format(self.actionedappname, self.pid))
        command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py",
                   "kill", "{}".format(self.pid)]
        self.start_kill_process(command)

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
        except subprocess.CalledProcessError as e:
            self.Logger.warning("error opening {}".format(desktop))
            self.Logger.exception("{}".format(e))
            return False

    def on_dActionButton_clicked(self, button):

        if not self.fromexternal:
            self.bottomstack.set_visible_child_name("queue")
            self.bottomrevealer.set_reveal_child(True)
            self.queuestack.set_visible_child_name("inprogress")
            self.dActionButton.set_sensitive(False)
            self.dActionInfoButton.set_sensitive(False)
            self.queue.append({"name": self.appname, "command": self.command})
            self.addtoQueue(self.appname)
            if not self.inprogress:
                self.actionPackage(self.appname, self.command)
                self.inprogress = True
                self.Logger.info("action {}".format(self.appname))
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

    def on_ractioninfo_clicked(self, button):

        self.rapp_packagename_box.set_visible(False)
        self.rapp_package_broken_box.set_visible(False)
        self.rapp_toremove_box.set_visible(False)
        self.rapp_toinstall_box.set_visible(False)
        self.rapp_broken_box.set_visible(False)
        self.rapp_size_box.set_visible(False)
        self.rapp_fsize_box.set_visible(False)
        self.rapp_dsize_box.set_visible(False)
        self.rapp_isize_box.set_visible(False)

        self.repo_required_spinner.start()
        self.repo_required_stack.set_visible_child_name("spinner")

        self.repo_required_changes_popover.popup()

        path = self.RepoAppsTreeView.get_cursor().path
        iter = self.searchstore.get_iter(path)
        package = self.searchstore.get_value(iter, 1)

        myappsdetailsthread = threading.Thread(target=self.repo_required_worker_thread, args=(package,), daemon=True)
        myappsdetailsthread.start()

    def on_raction_clicked(self, button):
        self.fromexternal = False
        self.raction.set_sensitive(False)

        self.desktop_file = ""

        self.queue.append({"name": self.appname, "command": self.appname})
        self.bottomstack.set_visible_child_name("queue")

        self.bottomrevealer.set_reveal_child(True)
        self.queuestack.set_visible_child_name("inprogress")

        self.addtoQueue(self.appname)

        if not self.inprogress:
            self.actionPackage(self.appname, self.appname)
            self.inprogress = True
            self.Logger.info("action {}".format(self.appname))

    def on_store_button_clicked(self, button):
        self.set_stack_n_search(1)
        if self.pardus_searchentry.get_text().strip() != "":
            self.store_button_clicked = True
            self.pardus_searchentry.set_text("")
        self.topsearchbutton.set_active(False)
        if self.Server.connection:
            self.homestack.set_visible_child_name("pardushome")
            self.EditorAppsIconView.unselect_all()
            self.PardusAppsIconView.unselect_all()
            self.topsearchbutton.set_sensitive(True)
        else:
            self.searchstack.set_visible_child_name("noserver")
            self.homestack.set_visible_child_name("noserver")
            self.topsearchbutton.set_sensitive(False)
        self.menubackbutton.set_sensitive(False)

    def on_repo_button_clicked(self, button):
        if self.repo_perm == 1:

            if self.homestack.get_visible_child_name() == "repohome":
                self.Logger.info("already repohome page")
            else:
                self.prefback = self.homestack.get_visible_child_name()

            self.menubackbutton.set_sensitive(False)
            self.homestack.set_visible_child_name("repohome")
            self.set_stack_n_search(2)

            # control for active actioned app
            if self.repoappclicked:
                self.RepoAppsTreeView.row_activated(self.activerepopath, self.RepoAppsTreeView.get_column(0))
                # Updating status tick of repo apps
                try:
                    for row in self.searchstore:
                        installstatus = self.Package.isinstalled(row[1])
                        row[0] = installstatus
                except:
                    pass

            self.topsearchbutton.set_active(True)
            self.repo_searchentry.grab_focus()
            self.topsearchbutton.set_sensitive(True)
        else:
            self.Logger.info("repo perm is 0 so you can not use repo button")

    def on_myapps_button_clicked(self, button):
        if self.myapps_perm == 1:
            if button is not None:
                self.prefback = self.homestack.get_visible_child_name()
            else:
                self.prefback = "pardushome"
            self.menubackbutton.set_sensitive(False)
            self.set_stack_n_search(3)
            if self.myapps_searchentry.get_text().strip() != "":
                self.myapps_searchentry.set_text("")
            self.topsearchbutton.set_active(False)
            self.topsearchbutton.set_sensitive(True)
            self.homestack.set_visible_child_name("myapps")
            self.myappsstack.set_visible_child_name("myapps")
            # set scroll position to top (reset)
            self.myapps_apps_sw.set_vadjustment(Gtk.Adjustment())
        else:
            self.Logger.info("myapps perm is 0 so you can not use myapps button")

    def on_updates_button_clicked(self, button):

        def start_thread():
            self.upgradables_listbox.foreach(lambda child: self.upgradables_listbox.remove(child))
            self.upgrade_dsize_box.set_visible(False)
            self.upgrade_isize_box.set_visible(False)
            self.upgrade_ucount_box.set_visible(False)
            self.upgrade_ncount_box.set_visible(False)
            self.upgrade_rcount_box.set_visible(False)
            self.upgrade_kcount_box.set_visible(False)
            self.topsearchbutton.set_active(False)
            self.topsearchbutton.set_sensitive(False)
            self.menubackbutton.set_sensitive(False)
            GLib.idle_add(self.updates_button.set_sensitive, False)
            GLib.idle_add(self.homestack.set_visible_child_name, "upgrade")
            GLib.idle_add(self.upgrade_stack.set_visible_child_name, "spinner")
            GLib.idle_add(self.upgrade_stack_spinnner.start)
            self.set_stack_n_search(5)
            upg_thread = threading.Thread(target=self.upgradables_worker_thread, daemon=True)
            upg_thread.start()

        def set_stack(stack_name):
            self.topsearchbutton.set_active(False)
            self.topsearchbutton.set_sensitive(False)
            self.menubackbutton.set_sensitive(False)
            GLib.idle_add(self.homestack.set_visible_child_name, "upgrade")
            GLib.idle_add(self.upgrade_stack.set_visible_child_name, stack_name)
            self.set_stack_n_search(5)

        if self.upgrade_inprogress:
            set_stack("upgrade")
            return

        if self.auto_apt_update_finished and self.upgradables_page_setted:
            set_stack("main")
        else:
            start_thread()

    def upgradables_worker_thread(self):
        rcu = self.rcu_worker()
        GLib.idle_add(self.on_upgradables_worker_done, rcu)

    def rcu_worker(self):
        return self.Package.required_changes_upgrade()

    def on_upgradables_worker_done(self, requireds):

        def add_to_listbox(package, state):

            image = Gtk.Image.new_from_icon_name("go-up-symbolic" if state == 1 else "list-add-symbolic",
                                                 Gtk.IconSize.BUTTON)
            name = Gtk.Label.new()
            name.set_markup("<b>{}</b>".format(GLib.markup_escape_text(package, -1)))
            name.props.halign = Gtk.Align.START

            summarylabel = Gtk.Label.new()
            summarylabel.set_markup(
                "<small>{}</small>".format(GLib.markup_escape_text(self.Package.summary(package), -1)))
            summarylabel.set_ellipsize(Pango.EllipsizeMode.END)
            summarylabel.props.halign = Gtk.Align.START

            old_version = Gtk.Label.new()
            old_version.set_markup("<span size='x-small'>{}</span>".format(
                GLib.markup_escape_text(self.Package.installed_version(package), -1)))
            old_version.set_ellipsize(Pango.EllipsizeMode.END)

            sep_label = Gtk.Label.new()
            sep_label.set_markup("<span size='x-small'>>></span>")

            new_version = Gtk.Label.new()
            new_version.set_markup("<span size='x-small'>{}</span>".format(
                GLib.markup_escape_text(self.Package.candidate_version(package), -1)))
            new_version.set_ellipsize(Pango.EllipsizeMode.END)

            box_version = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)
            box_version.pack_start(old_version, False, True, 0)
            box_version.pack_start(sep_label, False, True, 0)
            box_version.pack_start(new_version, False, True, 0)

            box1 = Gtk.Box.new(Gtk.Orientation.VERTICAL, 3)
            box1.pack_start(name, False, True, 0)
            box1.pack_start(summarylabel, False, True, 0)
            box1.pack_start(box_version, False, True, 0)
            box1.props.valign = Gtk.Align.CENTER
            box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
            box.set_margin_top(5)
            box.set_margin_bottom(5)
            box.set_margin_start(5)
            box.set_margin_end(5)
            box.pack_start(image, False, True, 5)
            box.pack_start(box1, False, True, 5)
            GLib.idle_add(self.upgradables_listbox.insert, box, GLib.PRIORITY_DEFAULT_IDLE)

        if requireds["cache_error"]:
            GLib.idle_add(self.upgrade_stack.set_visible_child_name, "upgrade")
            GLib.idle_add(self.upgrade_info_label.set_markup,
                          "<span color='red'>{}</span>".format(self.Package.update_cache_error_msg))
            GLib.idle_add(self.upgrade_info_box.set_visible, True)
            GLib.idle_add(self.upgrade_vte_sw.set_visible, False)
            GLib.idle_add(self.upgrade_stack_spinnner.stop)
            GLib.idle_add(self.updates_button.set_sensitive, True)
            GLib.idle_add(self.upgrade_info_back_button.set_visible, False)
            GLib.idle_add(self.upgrade_info_ok_button.set_visible, False)
            GLib.idle_add(self.upgrade_info_dpkgfix_button.set_visible, False)
            return

        if not requireds["changes_available"]:
            GLib.idle_add(self.upgrade_stack.set_visible_child_name, "upgrade")
            if requireds["to_keep"]:
                GLib.idle_add(self.upgrade_info_label.set_markup, "<b>{}</b>\n\n{}:\n\n{}".format(
                    _("Updates are complete. Your system is up to date."),
                    _("List of packages on hold"),
                    " ".join(self.Package.upgradable())))
                self.keep_ok_clicked = True
            else:
                GLib.idle_add(self.upgrade_info_label.set_markup,
                              "<b>{}</b>".format(_("Updates are complete. Your system is up to date.")))
            GLib.idle_add(self.upgrade_info_box.set_visible, True)
            GLib.idle_add(self.upgrade_vte_sw.set_visible, False)
            GLib.idle_add(self.upgrade_stack_spinnner.stop)
            GLib.idle_add(self.updates_button.set_sensitive, True)
            GLib.idle_add(self.upgrade_info_back_button.set_visible, False)
            GLib.idle_add(self.upgrade_info_dpkgfix_button.set_visible, False)
            GLib.idle_add(self.upgrade_info_ok_button.set_visible, True)
            return

        if requireds["to_upgrade"] and requireds["to_upgrade"] is not None:
            for package in requireds["to_upgrade"]:
                add_to_listbox(package, 1)

        if requireds["to_install"] and requireds["to_install"] is not None:
            for package in requireds["to_install"]:
                add_to_listbox(package, 2)

        GLib.idle_add(self.upgradables_listbox.show_all)
        GLib.idle_add(self.upgrade_stack.set_visible_child_name, "main")
        GLib.idle_add(self.upgrade_stack_spinnner.stop)
        GLib.idle_add(self.updates_button.set_sensitive, True)

        if requireds["download_size"] and requireds["download_size"] is not None:
            GLib.idle_add(self.upgrade_dsize_label.set_markup,
                          "{}".format(self.Package.beauty_size(requireds["download_size"])))
            GLib.idle_add(self.upgrade_dsize_box.set_visible, True)

        if requireds["install_size"] and requireds["install_size"] is not None and requireds["install_size"] > 0:
            GLib.idle_add(self.upgrade_isize_label.set_markup,
                          "{}".format(self.Package.beauty_size(requireds["install_size"])))
            GLib.idle_add(self.upgrade_isize_box.set_visible, True)

        if requireds["to_upgrade"] and requireds["to_upgrade"] is not None:
            GLib.idle_add(self.upgrade_ucount_label.set_markup,
                          "{}".format(len(requireds["to_upgrade"])))
            GLib.idle_add(self.upgrade_ucount_box.set_visible, True)

        if requireds["to_install"] and requireds["to_install"] is not None:
            GLib.idle_add(self.upgrade_ncount_label.set_markup, "{}".format(len(requireds["to_install"])))
            GLib.idle_add(self.upgrade_ncount_box.set_visible, True)

        if requireds["to_delete"] and requireds["to_delete"] is not None:
            GLib.idle_add(self.upgrade_rcount_label.set_markup, "{}".format(len(requireds["to_delete"])))
            GLib.idle_add(self.upgrade_rcount_box.set_visible, True)

        if requireds["to_keep"] and requireds["to_keep"] is not None:
            GLib.idle_add(self.upgrade_kcount_label.set_markup, "{}".format(requireds["to_keep"]))
            GLib.idle_add(self.upgrade_kcount_box.set_visible, True)

        self.Logger.info("on_upgradables_worker_done")
        self.upgradables_page_setted = True

    def on_upgrade_conf_radiobutton_toggled(self, button):
        self.upgrade_options_defaults_button.set_visible(
            not self.upgrade_new_conf_radiobutton.get_active() or not self.upgrade_withyq_radiobutton.get_active())

    def on_upgrade_options_defaults_button_clicked(self, button):
        self.upgrade_new_conf_radiobutton.set_active(True)
        self.upgrade_withyq_radiobutton.set_active(True)

    def on_upgrade_options_button_clicked(self, button):
        self.upgrade_options_popover.popup()
        self.upgrade_options_defaults_button.set_visible(
            not self.upgrade_new_conf_radiobutton.get_active() or not self.upgrade_withyq_radiobutton.get_active())

    def on_upgrade_button_clicked(self, button):
        self.upgrade_vteterm.reset(True, True)
        self.upgrade_info_box.set_visible(False)
        self.upgrade_vte_sw.set_visible(True)
        self.upgrade_info_back_button.set_visible(True)
        self.upgrade_info_ok_button.set_visible(False)
        self.upgrade_info_dpkgfix_button.set_visible(False)
        self.upgrade_stack.set_visible_child_name("upgrade")

        yq_conf = ""
        if self.upgrade_withyq_radiobutton.get_active():
            yq_conf = "-y -q"
        elif self.upgrade_withoutyq_radiobutton.get_active():
            yq_conf = ""

        dpkg_conf = ""
        if self.upgrade_new_conf_radiobutton.get_active():
            dpkg_conf = "-o Dpkg::Options::=--force-confnew"
        elif self.upgrade_old_conf_radiobutton.get_active():
            dpkg_conf = "-o Dpkg::Options::=--force-confold"
        elif self.upgrade_ask_conf_radiobutton.get_active():
            dpkg_conf = ""

        self.Logger.info("yq_conf: {}\ndpkg_conf: {}".format(yq_conf, dpkg_conf))
        if len(self.queue) == 0:
            command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/SysActions.py",
                       "upgrade", yq_conf, dpkg_conf]
            self.upgrade_vte_start_process(command)
            self.upgrade_inprogress = True
        else:
            self.upgrade_info_label.set_markup(
                "<span color='red'>{}</span>".format(_("Package manager is busy, try again later.")))
            self.upgrade_info_box.set_visible(True)
            self.upgrade_vte_sw.set_visible(False)

    def on_upgrade_info_dpkgfix_button_clicked(self, button):

        self.upgrade_info_dpkgfix_button.set_sensitive(False)

        self.pop_interruptinfo_spinner.set_visible(True)
        self.pop_interruptinfo_spinner.start()

        self.pop_interruptinfo_label.set_markup("<b>{}</b>".format(_("The process is in progress. Please wait...")))

        self.pop_interruptinfo_ok_button.set_visible(False)

        self.interruptpopover.set_relative_to(button)
        self.interruptpopover.popup()

        command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/SysActions.py", "dpkgconfigure"]

        if not self.dpkgconfiguring:
            self.dpkgconfigure_vte_start_process(command)
            self.dpkgconfiguring = True
        else:
            self.Logger.info("dpkgconfiguring in progress")

    def on_upgrade_info_back_button_clicked(self, button):
        self.upgrade_stack.set_visible_child_name("main")

    def on_upgrade_info_ok_button_clicked(self, button):
        if self.Package.upgradable() and not self.keep_ok_clicked:
            self.upgradables_page_setted = False
            self.on_updates_button_clicked(None)
        else:
            self.set_stack_n_search(1)
            GLib.idle_add(self.updates_button.set_visible, False)
            GLib.idle_add(self.menubackbutton.set_sensitive, False)
            if self.Server.connection:
                GLib.idle_add(self.homestack.set_visible_child_name, "pardushome")
                self.topsearchbutton.set_sensitive(True)
            else:
                self.searchstack.set_visible_child_name("noserver")
                self.homestack.set_visible_child_name("noserver")
                self.topsearchbutton.set_sensitive(False)

    def on_queue_button_clicked(self, button):
        if self.homestack.get_visible_child_name() == "queue":
            self.Logger.info("already queue page")
            return
        self.menubackbutton.set_sensitive(True)
        self.prefback = self.homestack.get_visible_child_name()
        self.prefback_queue = self.prefback
        self.homestack.set_visible_child_name("queue")
        self.set_stack_n_search(4)

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
        summarylabel.set_markup("<small>{}</small>".format(GLib.markup_escape_text(app["description"], -1)))
        summarylabel.set_line_wrap(True)
        summarylabel.set_line_wrap_mode(2)  # WORD_CHAR
        summarylabel.props.halign = Gtk.Align.START

        uninstallbutton = Gtk.Button.new()
        uninstallbutton.name = {"name": app["name"], "filename": app["filename"], "icon": app["icon"],
                                "description": app["description"], "keywords": app["keywords"],
                                "executable": app["executable"]}
        uninstallbutton.props.valign = Gtk.Align.CENTER
        uninstallbutton.props.halign = Gtk.Align.CENTER
        uninstallbutton.props.always_show_image = True
        uninstallbutton.set_image(Gtk.Image.new_from_icon_name("user-trash-symbolic", Gtk.IconSize.BUTTON))
        uninstallbutton.set_label("")
        uninstallbutton.set_tooltip_text(_("Uninstall"))
        uninstallbutton.get_style_context().add_class("destructive-action")
        uninstallbutton.connect("clicked", self.remove_from_myapps)

        openbutton = Gtk.Button.new()
        openbutton.name = app["id"]
        openbutton.props.valign = Gtk.Align.CENTER
        openbutton.props.halign = Gtk.Align.CENTER
        openbutton.props.always_show_image = True
        openbutton.set_image(Gtk.Image.new_from_icon_name("media-playback-start-symbolic", Gtk.IconSize.BUTTON))
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
        box.name = app["filename"]

        GLib.idle_add(self.MyAppsListBox.add, box)

    def remove_from_myapps(self, button):
        self.Logger.info("remove_from_myapps {}".format(button.name))

        self.ui_myapp_pop_toremove_box.set_visible(False)
        self.ui_myapp_pop_toinstall_box.set_visible(False)
        self.ui_myapp_pop_broken_box.set_visible(False)
        self.ui_myapp_pop_fsize_box.set_visible(False)
        self.ui_myapp_pop_dsize_box.set_visible(False)
        self.ui_myapp_pop_isize_box.set_visible(False)

        self.ui_myapp_pop_spinner.start()
        self.ui_myapp_pop_stack.set_visible_child_name("spinner")

        self.MyAppsDetailsPopover.set_relative_to(button)
        self.MyAppsDetailsPopover.popup()

        myappsdetailsthread = threading.Thread(target=self.myappsdetail_worker_thread,
                                               args=(button.name, True,), daemon=True)
        myappsdetailsthread.start()

    def open_from_myapps(self, button):
        self.Logger.info("{}".format(button.name))
        self.openDesktop(os.path.basename(button.name))

    def on_ui_myapps_cancel_clicked(self, button):
        self.menubackbutton.set_sensitive(False)
        self.myappsstack.set_visible_child_name("myapps")
        if not len(self.MyAppsListBox) > 0:
            self.Logger.info("MyAppsListBox creating")
            GLib.idle_add(self.on_myapps_button_clicked, None)

    def on_ui_myapps_cancel_disclaimer_clicked(self, button):
        self.myappsdetailsstack.set_visible_child_name("details")

    def on_ui_myapps_uninstall_button_clicked(self, button):
        importants = [i for i in self.important_packages if i in self.myapp_toremove_list]
        if importants:
            self.myappsdetailsstack.set_visible_child_name("disclaimer")
            self.ui_myapps_disclaimer_label.set_markup("<big>{}\n\n<b>{}</b>\n\n{}</big>".format(
                _("The following important packages will also be removed."),
                ", ".join(importants),
                _("Are you sure you accept this?")))
        else:
            self.Logger.info("not important package")
            self.ui_myapps_uninstall()

    def on_ui_myapps_accept_disclaimer_clicked(self, button):
        self.myappsdetailsstack.set_visible_child_name("details")
        self.ui_myapps_uninstall()

    def on_ui_myapp_pop_uninstall_button_clicked(self, button):
        importants = [i for i in self.important_packages if i in self.myapp_toremove_list]
        if importants:
            self.ui_myapp_pop_stack.set_visible_child_name("disclaimer")
            self.ui_myapp_pop_disclaimer_label.set_markup("<big>{}\n\n<b>{}</b>\n\n{}</big>".format(
                _("The following important packages will also be removed."),
                ", ".join(importants),
                _("Are you sure you accept this?")))
        else:
            self.Logger.info("not important package")
            self.ui_myapps_uninstall()

    def on_ui_myapp_pop_accept_disclaimer_clicked(self, button):
        self.ui_myapp_pop_stack.set_visible_child_name("details")
        self.ui_myapps_uninstall()

    def on_ui_myapp_pop_cancel_disclaimer_clicked(self, button):
        self.ui_myapp_pop_stack.set_visible_child_name("details")

    def ui_myapps_uninstall(self):
        self.appname = self.myapp_toremove
        self.command = self.myapp_toremove
        self.desktop_file = self.myapp_toremove_desktop
        self.bottomstack.set_visible_child_name("queue")
        self.bottomrevealer.set_reveal_child(True)
        self.queuestack.set_visible_child_name("inprogress")

        self.ma_action_buttonbox.set_sensitive(False)
        self.ui_myapp_pop_uninstall_button.set_sensitive(False)

        self.queue.append({"name": self.appname, "command": self.command})
        self.addtoQueue(self.appname, myappicon=True)
        if not self.inprogress:
            self.actionPackage(self.appname, self.command)
            self.inprogress = True
            self.Logger.info("action {}".format(self.appname))

    def myapps_filter_func(self, row):
        # app info defined in uninstall button so getting this widget
        myapp_name = row.get_children()[0].get_children()[3].name
        search = self.myapps_searchentry.get_text().lower()
        if search in myapp_name["name"].lower() or search in myapp_name["description"].lower() or \
                search in myapp_name["keywords"].lower() or search in myapp_name["executable"].lower():
            return True

    def myapps_sort_func(self, row1, row2):
        return locale.strxfrm(row1.get_children()[0].get_children()[3].name["name"]) > locale.strxfrm(
            row2.get_children()[0].get_children()[3].name["name"])

    def on_MyAppsListBox_row_activated(self, list_box, row):
        self.ui_myapp_pop_toremove_box.set_visible(False)
        self.ui_myapp_pop_toinstall_box.set_visible(False)
        self.ui_myapp_pop_broken_box.set_visible(False)
        self.ui_myapp_pop_fsize_box.set_visible(False)
        self.ui_myapp_pop_dsize_box.set_visible(False)
        self.ui_myapp_pop_isize_box.set_visible(False)

        self.ui_myapp_pop_spinner.start()
        self.ui_myapp_pop_stack.set_visible_child_name("spinner")

        desktopfilename = row.get_children()[0].name

        self.open_myapps_detailspage_from_desktopfile(desktopfilename)

    def open_myapps_detailspage_from_desktopfile(self, desktopfilename):
        valid, dic = self.Package.parse_desktopfile(os.path.basename(desktopfilename))
        self.homestack.set_visible_child_name("myapps")
        self.set_stack_n_search(3)
        self.topsearchbutton.set_sensitive(True)
        self.searchstack.set_visible_child_name("myapps")
        if valid:
            self.myappsstack.set_visible_child_name("details")
            self.myappsdetailsstack.set_visible_child_name("spinner")
            self.ui_myapps_spinner.start()
            myappsdetailsthread = threading.Thread(target=self.myappsdetail_worker_thread, args=(dic,), daemon=True)
            myappsdetailsthread.start()
        else:
            self.myappsstack.set_visible_child_name("notfound")
            if dic is None:
                self.ui_myapps_notfoundname_box.set_visible(False)
            else:
                self.ui_myapps_notfoundname_box.set_visible(True)
                self.ui_myapps_notfoundname_image.set_from_pixbuf(self.getMyAppIcon(dic["icon"], size=64))
                self.ui_myapps_notfoundname_name.set_markup("<big>{}</big>".format(dic["name"]))

    def on_myapps_searchentry_search_changed(self, entry_search):
        self.homestack.set_visible_child_name("myapps")
        self.myappsstack.set_visible_child_name("myapps")
        self.MyAppsListBox.invalidate_filter()
        # set scroll position to top (reset)
        self.myapps_apps_sw.set_vadjustment(Gtk.Adjustment())

    def on_myapps_searchentry_button_press_event(self, widget, click):
        self.homestack.set_visible_child_name("myapps")
        self.myappsstack.set_visible_child_name("myapps")
        self.MyAppsListBox.invalidate_filter()

    def on_myapps_searchentry_focus_in_event(self, widget, click):
        self.homestack.set_visible_child_name("myapps")
        self.myappsstack.set_visible_child_name("myapps")
        self.MyAppsListBox.invalidate_filter()

    def on_pardus_searchentry_search_changed(self, entry_search):
        self.Logger.info("on_pardus_searchentry_search_changed")
        self.isPardusSearching = True
        if not self.store_button_clicked:
            self.homestack.set_visible_child_name("pardusapps")
            self.menubackbutton.set_sensitive(True)
            self.PardusCategoryFilter.refilter()
            self.set_app_count_label()
        self.store_button_clicked = False

    def on_pardus_searchentry_button_press_event(self, widget, click):
        self.Logger.info("on_pardus_searchentry_button_press_event")
        self.homestack.set_visible_child_name("pardusapps")
        self.menubackbutton.set_sensitive(True)
        self.isPardusSearching = True
        self.PardusCategoryFilter.refilter()
        self.set_app_count_label()

    def on_pardus_searchentry_focus_in_event(self, widget, click):
        self.Logger.info("on_pardus_searchentry_focus_in_event")
        self.homestack.set_visible_child_name("pardusapps")
        self.menubackbutton.set_sensitive(True)
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
        self.set_app_count_label()

    def on_repo_searchbutton_clicked(self, button):
        self.isRepoSearching = True
        reposearch_list_tmp = []
        self.reposearch_list = []
        text = self.repo_searchentry.get_text()

        self.searchstore = Gtk.ListStore(bool, str, str, str)

        for i in self.Package.apps:
            if text in i["name"]:
                reposearch_list_tmp.append({"name": i["name"], "category": i["category"]})

        for t in reposearch_list_tmp:
            if t["name"].startswith(text):
                self.reposearch_list.append({"name": t["name"], "category": t["category"]})

        for tt in reposearch_list_tmp:
            self.reposearch_list.append({"name": tt["name"], "category": tt["category"]})

        self.reposearch_list = list({v["name"]: v for v in self.reposearch_list}.values())

        for package in self.reposearch_list:
            installstatus = self.Package.isinstalled(package["name"])
            self.searchstore.append(
                [installstatus, package["name"], package["category"], self.Package.summary(package["name"])])

        self.RepoAppsTreeView.set_model(self.searchstore)
        self.RepoAppsTreeView.set_search_column(1)
        self.RepoAppsTreeView.show_all()

    def repoapps_selection_changed(self, path):
        self.repoappclicked = True
        self.fromrepoapps = True
        self.activerepopath = path

        iter = self.searchstore.get_iter(path)
        value = self.searchstore.get_value(iter, 1)
        section = self.searchstore.get_value(iter, 2)

        self.repoappname = value
        self.appname = value
        isinstalled = self.Package.isinstalled(self.appname)

        if isinstalled is not None:
            self.raction.set_sensitive(True)
            if isinstalled:
                self.set_button_class(self.raction, 1)
                self.set_button_class(self.ractioninfo, 1)
                self.raction.set_label(_(" Uninstall"))
                self.raction.set_image(Gtk.Image.new_from_icon_name("user-trash-symbolic", Gtk.IconSize.BUTTON))
                version = self.Package.installed_version(self.appname)
            else:
                self.set_button_class(self.raction, 0)
                self.set_button_class(self.ractioninfo, 0)
                self.raction.set_label(_(" Install"))
                self.raction.set_image(Gtk.Image.new_from_icon_name("document-save-symbolic", Gtk.IconSize.BUTTON))
                version = self.Package.candidate_version(self.appname)
        else:
            self.raction.set_sensitive(False)
            self.set_button_class(self.raction, 2)
            self.set_button_class(self.ractioninfo, 2)
            self.raction.set_label(_(" Not Found"))
            self.raction.set_image(Gtk.Image.new_from_icon_name("dialog-warning-symbolic", Gtk.IconSize.BUTTON))
            version = ""

        if len(self.queue) > 0:
            for qa in self.queue:
                if self.appname == qa["name"]:
                    if isinstalled:
                        self.raction.set_label(_(" Removing"))
                    else:
                        self.raction.set_label(_(" Installing"))
                    self.raction.set_sensitive(False)

        summary = self.Package.summary(value)
        description = self.Package.adv_description(value)
        maintainer_name, maintainer_mail, homepage, arch = self.Package.get_records(value)
        origins = self.Package.origins(value)
        downloadable, r_uri = self.Package.get_uri(value)

        self.rstack.set_visible_child_name("package")
        self.rpackage.set_markup("<span size='x-large'><b>{}</b></span>".format(value))
        self.rtitle.set_text(summary)
        self.rtitle.set_tooltip_text("{}".format(summary))

        if summary != description:
            self.rdetail.set_text(description)
        else:
            self.rdetail.set_text("")

        if maintainer_name != "":
            self.r_maintainername.set_text(maintainer_name)
        else:
            self.r_maintainername.set_text("-")

        if maintainer_mail != "":
            self.r_maintainermail.set_markup("<a title='{}' href='mailto:{}'>{}</a>".format(
                GLib.markup_escape_text(maintainer_mail, -1),
                GLib.markup_escape_text(maintainer_mail, -1),
                GLib.markup_escape_text(maintainer_mail, -1)))
        else:
            self.r_maintainermail.set_text("-")

        if homepage != "":
            self.r_homepage.set_markup("<a title='{}' href='{}'>{}</a>".format(
                GLib.markup_escape_text(homepage, -1),
                GLib.markup_escape_text(homepage, -1),
                GLib.markup_escape_text(homepage, -1)))
        else:
            self.r_homepage.set_text("-")

        if section != "":
            self.r_section.set_text(section)
        else:
            self.r_section.set_text("-")

        if arch != "":
            self.r_architecture.set_text(arch)
        else:
            self.r_architecture.set_text("-")

        if version is not None and version != "":
            self.r_version.set_text(version)
        else:
            self.r_version.set_text("-")

        if origins is not None and origins != "":
            self.r_origin.set_markup("{} {}".format(origins.origin, origins.component))
        else:
            self.r_origin.set_text("-")

        # if downloadable and r_uri != "":
        #     self.r_url.set_markup(
        #         "<a href='{}' title='{}'>{}</a>".format(r_uri, r_uri, _("Download")))
        # else:
        #     self.r_origin.set_text("-")

    def on_RepoAppsTreeView_cursor_changed(self, tree_view):
        path = tree_view.get_cursor().path
        if path is not None:
            self.repoapps_selection_changed(path)

    def on_topsearchbutton_toggled(self, button):
        if self.topsearchbutton.get_active():
            self.toprevealer.set_reveal_child(True)
            if self.searchstack.get_visible_child_name() == "pardus":
                self.pardus_searchentry.grab_focus()
                self.Logger.info("in grab focus")
            elif self.searchstack.get_visible_child_name() == "repo":
                self.repo_searchentry.grab_focus()
            elif self.searchstack.get_visible_child_name() == "myapps":
                self.myapps_searchentry.grab_focus()
                if not len(self.MyAppsListBox) > 0:
                    self.Logger.info("MyAppsListBox creating")
                    self.on_myapps_button_clicked(None)
        else:
            self.toprevealer.set_reveal_child(False)

    def on_main_key_press_event(self, widget, event):
        if self.mainstack.get_visible_child_name() == "home":
            if self.homestack.get_visible_child_name() == "pardushome" or self.homestack.get_visible_child_name() == "pardusapps":
                if not self.topsearchbutton.get_active():
                    if event.string.isdigit() or event.string.isalpha():
                        self.pardus_searchentry.get_buffer().delete_text(0, -1)
                        self.pardus_searchentry.grab_focus()
                        self.topsearchbutton.set_active(True)
                        self.toprevealer.set_reveal_child(True)
                        self.pardus_searchentry.get_buffer().insert_text(1, event.string, 1)
                        self.pardus_searchentry.set_position(2)
                        return True
                else:
                    if event.keyval == Gdk.KEY_Escape:
                        self.pardus_searchentry.get_buffer().delete_text(0, -1)
                        self.topsearchbutton.set_active(False)
                        self.toprevealer.set_reveal_child(False)
                        return True
            elif self.homestack.get_visible_child_name() == "myapps" and self.myappsstack.get_visible_child_name() == "myapps":
                if not self.topsearchbutton.get_active():
                    if event.string.isdigit() or event.string.isalpha():
                        self.myapps_searchentry.get_buffer().delete_text(0, -1)
                        self.myapps_searchentry.grab_focus()
                        self.topsearchbutton.set_active(True)
                        self.toprevealer.set_reveal_child(True)
                        self.myapps_searchentry.get_buffer().insert_text(1, event.string, 1)
                        self.myapps_searchentry.set_position(2)
                        return True
                else:
                    if event.keyval == Gdk.KEY_Escape:
                        self.myapps_searchentry.get_buffer().delete_text(0, -1)
                        self.topsearchbutton.set_active(False)
                        self.toprevealer.set_reveal_child(False)
                        return True

    def on_menu_settings_clicked(self, button):
        if self.homestack.get_visible_child_name() == "preferences":
            self.Logger.info("already preferences page")
        else:
            self.prefback = self.homestack.get_visible_child_name()
            self.prefback_preferences = self.prefback
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
        self.store_button.get_style_context().remove_class("suggested-action")
        self.repo_button.get_style_context().remove_class("suggested-action")
        self.myapps_button.get_style_context().remove_class("suggested-action")
        self.queue_button.get_style_context().remove_class("suggested-action")
        self.prefcachebutton.set_sensitive(True)
        self.prefcachebutton.set_label(_("Clear"))
        self.preflabel_settext("")

        self.control_groups()

        self.setSelectIcons()

        self.set_cache_size()

    def set_cache_size(self):
        cache_size = self.Utils.get_path_size(self.Server.cachedir)
        self.Logger.info("{} : {} bytes".format(self.Server.cachedir, cache_size))
        self.ui_cache_size.set_text("({})".format(self.Package.beauty_size(cache_size)))

    def control_groups(self):
        try:
            self.usergroups = [g.gr_name for g in grp.getgrall() if self.UserSettings.username in g.gr_mem]
        except Exception as e:
            self.Logger.exception("control_groups: {}".format(e))
            self.usergroups = []

        if self.usergroups:
            self.passwordlessbutton.set_visible(True)
            if "pardus-software" in self.usergroups:
                self.passwordlessbutton.set_label(_("Deactivate"))
            else:
                self.passwordlessbutton.set_label(_("Activate"))
            self.passwordlessbutton.set_sensitive(True)
        else:
            self.passwordlessbutton.set_visible(False)

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

    def on_menu_statistics_clicked(self, button):
        if self.homestack.get_visible_child_name() == "statistics":
            self.Logger.info("already statistics page")
            self.PopoverMenu.popdown()
            return
        self.prefback = self.homestack.get_visible_child_name()
        self.prefback_statistics = self.prefback
        self.PopoverMenu.popdown()
        self.topsearchbutton.set_active(False)
        self.topsearchbutton.set_sensitive(False)
        self.menubackbutton.set_sensitive(True)
        self.homestack.set_visible_child_name("statistics")
        self.store_button.get_style_context().remove_class("suggested-action")
        self.repo_button.get_style_context().remove_class("suggested-action")
        self.myapps_button.get_style_context().remove_class("suggested-action")
        self.queue_button.get_style_context().remove_class("suggested-action")

        if self.Server.connection:
            GLib.idle_add(self.setStatistics)

    def setStatistics(self):

        if not self.statisticsSetted or self.matplot_install_clicked:

            self.statstotaldc.set_markup(
                "<small><b>{}</b></small>".format(self.Server.totalstatistics[0]["downcount"]))
            self.statstotalrc.set_markup(
                "<small><b>{}</b></small>".format(self.Server.totalstatistics[0]["ratecount"]))

            self.statsweblabel.set_markup("<small>" + _("View on {}.").format(
                "<a href='https://apps.pardus.org.tr/statistics' title='https://apps.pardus.org.tr/statistics'>apps.pardus.org.tr</a>") + "</small>")

            self.statmainstack.set_visible_child_name("splash")
            self.stat_spinner.start()

            statsthread = threading.Thread(target=self.stats_worker_thread, daemon=True)
            statsthread.start()

            if self.matplot_install_clicked:
                installed = self.Package.isinstalled("python3-matplotlib")
                if installed is not None:
                    if installed:
                        self.matplot_install_clicked = False
        else:
            self.statmainstack.set_visible_child_name("stats")

    def stats_worker_thread(self):
        libfound = self.stats_worker()
        GLib.idle_add(self.on_stats_worker_done, libfound)

    def stats_worker(self):
        time.sleep(0.25)
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
            return True
        except ModuleNotFoundError as e:
            self.Logger.exception("{}".format(e))
            self.matplot_error = "{}\n\n{}".format(e,
                                                   _("The python3-matplotlib library is required to view statistics."))
            return False
        except Exception as e:
            self.matplot_error = "{}\n\n{}".format(e,
                                                   _("Try again by closing and reopening the application."))
            return False

    def on_stats_worker_done(self, libfound):
        if libfound:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas

            dates = []
            downs = []
            for data in self.Server.dailydowns:
                dates.append(data["date"])
                downs.append(data["count"])
            fig1, ax1 = plt.subplots()
            p1 = ax1.bar(dates, downs, width=0.9, edgecolor="white", linewidth=1)
            plt.title(_("Daily App Download Counts (Last 30 Days)"))
            plt.tight_layout()
            # if hasattr(ax1, "bar_label"):
            #     ax1.bar_label(p1, label_type='edge', fontsize="small")  # requires version 3.4-2+
            fig1.autofmt_xdate(rotation=60)
            canvas1 = FigureCanvas(fig1)
            GLib.idle_add(self.stats1ViewPort.add, canvas1)

            osnames = []
            osdowns = []
            for osdata in self.Server.osdowns:
                for key, value in osdata.items():
                    if self.locale == "tr" and key == "Others":
                        key = "Diğerleri"
                    osnames.append(key)
                    osdowns.append(value)
            # explode = (0.2, 0.3, 0.2, 0.2, 0.7)
            fig2, ax2 = plt.subplots()
            p2 = ax2.pie(osdowns, labels=osnames, colors=self.Server.oscolors, explode=self.Server.osexplode,
                         autopct=lambda p: f'{p * sum(osdowns) / 100 :.0f} (%{p:.2f})')
            # plt.setp(p2[1], size="small", weight="bold")
            # plt.setp(p2[2], size="small", weight="bold")
            ax2.axis('equal')
            plt.title(_("Used Operating Systems (For App Download)"))
            plt.tight_layout()
            canvas2 = FigureCanvas(fig2)
            GLib.idle_add(self.stats2ViewPort.add, canvas2)

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
            # if hasattr(ax3, "bar_label"):
            #     ax3.bar_label(p3, label_type='edge', fontsize="small")  # requires version 3.4-2+
            fig3.autofmt_xdate(rotation=45)
            canvas3 = FigureCanvas(fig3)
            GLib.idle_add(self.stats3ViewPort.add, canvas3)

            GLib.idle_add(self.stats1ViewPort.show_all)
            GLib.idle_add(self.stats2ViewPort.show_all)
            GLib.idle_add(self.stats3ViewPort.show_all)
            GLib.idle_add(self.statmainstack.set_visible_child_name, "stats")

            plt.close('all')

            self.statisticsSetted = True

        else:
            GLib.idle_add(self.statmainstack.set_visible_child_name, "info")
            GLib.idle_add(self.stat_ilabel.set_text, "{}".format(self.matplot_error))
            self.Logger.info("matplotlib is not found")

        GLib.idle_add(self.stat_spinner.stop)

    def on_install_matplotlib_button_clicked(self, button):
        self.matplot_install_clicked = True
        app = "python3-matplotlib"
        self.repo_searchentry.set_text(app)
        self.on_repo_button_clicked(None)
        self.on_repo_searchbutton_clicked(self.repo_searchbutton)
        for row in self.searchstore:
            if app == row[1]:
                self.RepoAppsTreeView.set_cursor(row.path)
                # self.on_RepoAppsTreeView_row_activated(self.RepoAppsTreeView, row.path, 0)

    def on_menu_about_clicked(self, button):
        self.PopoverMenu.popdown()
        self.aboutdialog.run()
        self.aboutdialog.hide()

    def on_menu_suggestapp_clicked(self, button):
        if self.homestack.get_visible_child_name() == "suggestapp":
            self.Logger.info("already suggestapp page")
            self.PopoverMenu.popdown()
            return
        self.prefback = self.homestack.get_visible_child_name()
        self.prefback_suggestapp = self.prefback
        self.menubackbutton.set_sensitive(True)
        self.PopoverMenu.popdown()
        self.topsearchbutton.set_active(False)
        self.topsearchbutton.set_sensitive(False)
        self.store_button.get_style_context().remove_class("suggested-action")
        self.repo_button.get_style_context().remove_class("suggested-action")
        self.myapps_button.get_style_context().remove_class("suggested-action")
        self.queue_button.get_style_context().remove_class("suggested-action")
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
                self.SuggestInfoLabel.set_markup("<b><span color='red'>{}</span></b>".format(img_message))
        else:
            self.SuggestInfoLabel.set_markup("<b><span color='red'>{} : {} {}</span></b>".format(
                _("Error"), message, _("is empty")))

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
            return False, _("Description (Turkish)")

        if self.sug_desc_en.strip() == "":
            return False, _("Description (English)")

        if self.sug_license.strip() == "":
            return False, _("License")

        # if self.sug_copyright.strip() == "":
        #     return False, _("Copyright Text")

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
            self.Logger.info("Updating user icon state")
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
                self.preflabel_settext("{}".format(e))
                self.Logger.exception("{}".format(e))

    def on_switchEA_state_set(self, switch, state):
        user_config_ea = self.UserSettings.config_ea
        if state != user_config_ea:
            self.Logger.info("Updating user animation state")
            try:
                self.UserSettings.writeConfig(self.UserSettings.config_usi, state, self.UserSettings.config_saa,
                                              self.UserSettings.config_hera, self.UserSettings.config_icon,
                                              self.UserSettings.config_sgc, self.UserSettings.config_udt,
                                              self.UserSettings.config_aptup, self.UserSettings.config_lastaptup,
                                              self.UserSettings.config_forceaptuptime)
                self.usersettings()
                self.setAnimations()
            except Exception as e:
                self.preflabel_settext("{}".format(e))

    def on_switchSAA_state_set(self, switch, state):
        user_config_saa = self.UserSettings.config_saa
        if state != user_config_saa:
            self.Logger.info("Updating show available apps state")
            try:
                self.UserSettings.writeConfig(self.UserSettings.config_usi, self.UserSettings.config_ea, state,
                                              self.UserSettings.config_hera, self.UserSettings.config_icon,
                                              self.UserSettings.config_sgc, self.UserSettings.config_udt,
                                              self.UserSettings.config_aptup, self.UserSettings.config_lastaptup,
                                              self.UserSettings.config_forceaptuptime)
                self.usersettings()
                self.setAvailableApps(available=state, hideextapps=self.UserSettings.config_hera)
            except Exception as e:
                self.preflabel_settext("{}".format(e))

            GLib.idle_add(self.clearBoxes)
            self.setPardusApps()
            self.setPardusCategories()
            self.setEditorApps()
            self.setMostApps()

    def on_switchHERA_state_set(self, switch, state):
        user_config_hera = self.UserSettings.config_hera
        if state != user_config_hera:
            self.Logger.info("Updating hide external apps state")
            try:
                self.UserSettings.writeConfig(self.UserSettings.config_usi, self.UserSettings.config_ea,
                                              self.UserSettings.config_saa, state, self.UserSettings.config_icon,
                                              self.UserSettings.config_sgc, self.UserSettings.config_udt,
                                              self.UserSettings.config_aptup, self.UserSettings.config_lastaptup,
                                              self.UserSettings.config_forceaptuptime)
                self.usersettings()
                self.setAvailableApps(available=self.UserSettings.config_saa, hideextapps=state)
            except Exception as e:
                self.preflabel_settext("{}".format(e))

            GLib.idle_add(self.clearBoxes)
            self.setPardusApps()
            self.setPardusCategories()
            self.setEditorApps()
            self.setMostApps()

    def on_setServerIconCombo_changed(self, combo_box):
        user_config_icon = self.UserSettings.config_icon
        active = combo_box.get_active_id()
        if active != user_config_icon and active is not None:
            self.Logger.info("changing icons to {}".format(combo_box.get_active_id()))
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
            self.Logger.info("Updating show gnome apps state as {}".format(state))
            self.UserSettings.writeConfig(self.UserSettings.config_usi, self.UserSettings.config_ea,
                                          self.UserSettings.config_saa, self.UserSettings.config_hera,
                                          self.UserSettings.config_icon, state, self.UserSettings.config_udt,
                                          self.UserSettings.config_aptup, self.UserSettings.config_lastaptup,
                                          self.UserSettings.config_forceaptuptime)
            self.usersettings()

    def on_switchUDT_state_set(self, switch, state):
        user_config_udt = self.UserSettings.config_udt
        if state != user_config_udt:
            self.Logger.info("Updating use dark theme state as {}".format(state))
            self.UserSettings.writeConfig(self.UserSettings.config_usi, self.UserSettings.config_ea,
                                          self.UserSettings.config_saa, self.UserSettings.config_hera,
                                          self.UserSettings.config_icon, self.UserSettings.config_sgc, state,
                                          self.UserSettings.config_aptup, self.UserSettings.config_lastaptup,
                                          self.UserSettings.config_forceaptuptime)

            Gtk.Settings.get_default().props.gtk_application_prefer_dark_theme = state

            self.usersettings()

    def on_switchAPTU_state_set(self, switch, state):
        user_config_aptup = self.UserSettings.config_aptup
        if state != user_config_aptup:
            self.Logger.info("Updating auto apt update state as {}".format(state))
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
            self.preflabel_settext(_("Cache files cleared, please close and reopen the application"))
        else:
            self.prefcachebutton.set_sensitive(True)
            self.prefcachebutton.set_label(_("Error"))
            self.preflabel_settext("{}".format(message))
        self.set_cache_size()

    def on_prefcorrectbutton_clicked(self, button):
        self.prefstack.set_visible_child_name("confirm")

    def on_prefconfirm_cancelbutton_clicked(self, button):
        self.prefstack.set_visible_child_name("main")

    def on_prefconfirm_acceptbutton_clicked(self, button):
        command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/SysActions.py",
                   "correctsourceslist"]

        self.headerAptUpdateSpinner.set_visible(True)
        self.headerAptUpdateSpinner.start()
        self.prefcorrectbutton.set_sensitive(False)

        self.startSysProcess(command)
        self.prefstack.set_visible_child_name("main")
        self.correctsourcesclicked = True

    def preflabel_settext(self, text):
        self.preflabel.set_markup(text)

    def on_passwordlessbutton_clicked(self, button):
        self.passwordlessbutton.set_sensitive(False)
        self.preflabel_settext("")
        self.grouperrormessage = ""
        if "pardus-software" in self.usergroups:
            command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Group.py", "del",
                       self.UserSettings.username]
        else:
            command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Group.py", "add",
                       self.UserSettings.username]
        self.startGroupProcess(command)

    def on_bottomerrorbutton_clicked(self, button):
        self.bottomrevealer.set_reveal_child(False)

    def on_dLicense_activate_link(self, label, url):
        self.licensePopover.popup()

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
            elif self.detailsappname:
                ui_appname = self.detailsappname
        if self.fromqueue:
            ui_appname = self.queueappname
        if self.frommyapps:
            ui_appname = self.myappname
        if self.fromrepoapps:
            ui_appname = self.repoappname
        self.Logger.info("ui_app : {}".format(ui_appname))
        return ui_appname

    def on_retrybutton_clicked(self, button):
        self.connection_error_after = False
        self.mainstack.set_visible_child_name("splash")
        p1 = threading.Thread(target=self.worker)
        p1.daemon = True
        p1.start()

    def on_mdabutton_clicked(self, button):
        self.SubCatCombo.remove_all()
        self.SubCatCombo.set_visible(False)
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
        if not self.ui_showall_button.get_active():
            self.ui_showall_button.set_active(True)
        self.PardusCategoryFilter.refilter()
        self.set_app_count_label()
        self.homestack.set_visible_child_name("pardusapps")

    def on_mrabutton_clicked(self, button):
        self.SubCatCombo.remove_all()
        self.SubCatCombo.set_visible(False)
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
        if not self.ui_showall_button.get_active():
            self.ui_showall_button.set_active(True)
        self.PardusCategoryFilter.refilter()
        self.set_app_count_label()
        self.homestack.set_visible_child_name("pardusapps")

    def on_labutton_clicked(self, button):
        self.SubCatCombo.remove_all()
        self.SubCatCombo.set_visible(False)
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
        if not self.ui_showall_button.get_active():
            self.ui_showall_button.set_active(True)
        self.PardusCategoryFilter.refilter()
        self.set_app_count_label()
        self.homestack.set_visible_child_name("pardusapps")

    def actionPackage(self, appname, command):

        self.inprogress = True
        self.topspinner.start()

        ui_appname = self.getActiveAppOnUI()

        if ui_appname == appname:
            self.dActionButton.set_sensitive(False)
            self.dActionButton.set_image(Gtk.Image.new_from_icon_name("process-working-symbolic", Gtk.IconSize.BUTTON))
            self.dActionInfoButton.set_sensitive(False)
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
            packagelist = self.actionedcommand.split(" ")
            if [i for i in self.i386_packages if i in packagelist]:
                command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py",
                           "enablei386andinstall", self.actionedcommand]
        else:
            self.Logger.info("actionPackage func error")

        self.pid = self.startProcess(command)
        self.Logger.info("started pid : {}".format(self.pid))

    def actionEnablePackage(self, appname):
        self.actionedenablingappname = appname
        self.actionedenablingappdesktop = self.desktop_file
        self.actionedenablingappcommand = self.command
        self.dActionButton.set_label(_(" Activating"))
        command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/SysActions.py", "externalrepo",
                   self.external["repokey"], self.external["reposlist"], self.external["reponame"]]
        self.expid = self.startSysProcess(command)

    def on_bottominterrupt_fix_button_clicked(self, button):
        self.bottominterrupt_fix_button.set_sensitive(False)
        self.bottominterrupthide_button.set_sensitive(False)

        self.pop_interruptinfo_spinner.set_visible(True)
        self.pop_interruptinfo_spinner.start()

        self.pop_interruptinfo_label.set_markup("<b>{}</b>".format(_("The process is in progress. Please wait...")))

        self.pop_interruptinfo_ok_button.set_visible(False)

        self.interruptpopover.set_relative_to(button)
        self.interruptpopover.popup()

        command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/SysActions.py", "dpkgconfigure"]

        if not self.dpkgconfiguring:
            self.dpkgconfigure_vte_start_process(command)
            self.dpkgconfiguring = True
        else:
            self.Logger.info("dpkgconfiguring in progress")

    def on_pop_interruptinfo_ok_button_clicked(self, button):
        self.bottomrevealer.set_reveal_child(False)
        self.interruptpopover.popdown()
        self.upgrade_stack.set_visible_child_name("main")

    def on_bottominterrupthide_button_clicked(self, button):
        self.bottomrevealer.set_reveal_child(False)

    def on_bottomerrordetails_button_clicked(self, button):
        self.bottomerrordetails_popover.popup()

    def start_kill_process(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(params, flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_output=True, standard_error=True)
        GLib.io_add_watch(GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.on_start_kill_process_stdout)
        GLib.io_add_watch(GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.on_start_kill_process_stderr)
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, self.on_start_kill_process_exit)
        return pid

    def on_start_kill_process_stdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        self.Logger.info("{}".format(line))
        return True

    def on_start_kill_process_stderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False

    def on_start_kill_process_exit(self, pid, status):
        self.Logger.info("on_start_kill_process_exit: {}".format(pid))

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
        self.Logger.info("{}".format(line))

        return True

    def onProcessStderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False

        line = source.readline()

        self.Logger.info("{}".format(line))

        if "dlstatus" in line:
            percent = line.split(":")[2].split(".")[0]
            self.progresstextlabel.set_text(
                "{} | {} : {} %".format(self.actionedappname, _("Downloading"), percent))
            self.dActionCancelButton.set_visible(True)
        elif "pmstatus" in line:
            percent = line.split(":")[2].split(".")[0]
            if self.isinstalled:
                self.progresstextlabel.set_text(
                    "{} | {} : {} %".format(self.actionedappname, _("Removing"), percent))
            else:
                self.progresstextlabel.set_text(
                    "{} | {} : {} %".format(self.actionedappname, _("Installing"), percent))
            self.dActionCancelButton.set_visible(False)
        elif "E:" in line and ".deb" in line:
            self.Logger.warning("connection error")
            self.error = True
            self.error_message += line
        elif "E:" in line and "dpkg --configure -a" in line:
            self.Logger.warning("dpkg --configure -a error")
            self.error = True
            self.dpkgconferror = True
        elif "E:" in line and "/var/lib/dpkg/lock-frontend" in line:
            self.Logger.warning("/var/lib/dpkg/lock-frontend error")
            self.error = True
            self.dpkglockerror = True
            self.dpkglockerror_message += line
        elif "pardus-software-i386-start" in line:
            self.progresstextlabel.set_text(
                "{} | {}".format(self.actionedappname, _("i386 activating")))
        return True

    def onProcessExit(self, pid, status):
        self.dActionCancelButton.set_visible(False)
        self.bottomerrordetails_button.set_visible(False)

        if not self.error:
            if status == 0:
                if self.isinstalled:
                    self.progresstextlabel.set_text(self.actionedappname + _(" | Removed: 100%"))
                else:
                    self.progresstextlabel.set_text(self.actionedappname + _(" | Installed: 100%"))
            else:
                self.progresstextlabel.set_text(self.actionedappname + _(" | Not Completed"))
        else:
            self.errormessage = _("<b><span color='red'>Connection Error!</span></b>")
            if self.dpkglockerror:
                self.errormessage = _("<b><span color='red'>Dpkg Lock Error!</span></b>")
            elif self.dpkgconferror:
                self.errormessage = _("<b><span color='red'>Dpkg Interrupt Error!</span></b>")

        cachestatus = self.Package.updatecache()

        self.Logger.info("Cache Status: {}, Package Cache Status: {}".format(
            cachestatus, self.Package.controlPackageCache(self.actionedappname)))

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
                self.dActionInfoButton.set_sensitive(True)
                self.raction.set_sensitive(True)

        self.topspinner.stop()
        self.Logger.info("Exit Code: {}".format(status))

        self.inprogress = False

        if len(self.queue) > 0:
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

        if status == 256:
            self.errormessage = _("Only one software management tool is allowed to run at the same time.\n"
                                  "Please close the other application e.g. 'Update Manager', 'aptitude' or 'Synaptic' first.")
            self.bottomrevealer.set_reveal_child(True)
            self.bottomstack.set_visible_child_name("error")
            self.bottomerrorlabel.set_markup("<span color='red'>{}</span>".format(self.errormessage))
            if self.dpkglockerror:
                self.bottomerrordetails_button.set_visible(True)
                self.bottomerrordetails_label.set_markup(
                    "<b>{}</b>".format(GLib.markup_escape_text(self.dpkglockerror_message, -1)))

            elif self.Package.control_dpkg_interrupt():
                self.bottomstack.set_visible_child_name("interrupt")
                self.bottominterruptlabel.set_markup("<span color='red'><b>{}</b></span>".format(
                    _("dpkg interrupt detected. Click the 'Fix' button or\n"
                      "manually run 'sudo dpkg --configure -a' to fix the problem.")
                ))

        self.error = False
        self.dpkglockerror = False
        self.dpkgconferror = False
        self.error_message = ""
        self.dpkglockerror_message = ""

    def controlView(self, actionedappname, actionedappdesktop, actionedappcommand):
        selected_items = self.PardusAppsIconView.get_selected_items()
        editor_selected_items = self.EditorAppsIconView.get_selected_items()

        if len(selected_items) == 1:
            treeiter = self.PardusCategoryFilter.get_iter(selected_items[0])
            appname = self.PardusCategoryFilter.get(treeiter, 1)[0]
            self.Logger.info("in controlView {}".format(appname))
            if appname == actionedappname:
                self.updateActionButtons(1, actionedappname, actionedappdesktop, actionedappcommand)

        if len(editor_selected_items) == 1:
            treeiter = self.EditorListStore.get_iter(editor_selected_items[0])
            appname = self.EditorListStore.get(treeiter, 1)[0]
            self.Logger.info("in controlView {}".format(appname))
            if appname == actionedappname:
                self.updateActionButtons(1, actionedappname, actionedappdesktop, actionedappcommand)

        if self.frommostapps:
            if self.mostappname:
                if self.mostappname == actionedappname:
                    self.updateActionButtons(1, actionedappname, actionedappdesktop, actionedappcommand)
            else:
                if self.detailsappname == actionedappname:
                    self.updateActionButtons(1, actionedappname, actionedappdesktop, actionedappcommand)

        if self.fromqueue:
            if self.queueappname:
                if self.queueappname == actionedappname:
                    self.updateActionButtons(1, actionedappname, actionedappdesktop, actionedappcommand)

        if self.frommyapps:
            if self.myappname:
                if self.myappname == actionedappname:
                    self.updateActionButtons(1, actionedappname, actionedappdesktop, actionedappcommand)

        if self.fromrepoapps:
            if self.repoappname == actionedappname:
                self.updateActionButtons(2, actionedappname, actionedappdesktop, actionedappcommand)

            # Updating status tick of repo apps
            try:
                for row in self.searchstore:
                    installstatus = self.Package.isinstalled(row[1])
                    row[0] = installstatus
            except:
                pass

    def updateActionButtons(self, repo, actionedappname, actionedappdesktop, actionedappcommand):
        if repo == 1:  # pardus apps
            self.fromexternal = False
            if self.Package.isinstalled(actionedappname) is True:

                self.set_button_class(self.dActionButton, 1)
                self.set_button_class(self.dActionInfoButton, 1)

                self.dActionButton.set_label(_(" Uninstall"))
                self.dActionButton.set_image(Gtk.Image.new_from_icon_name("user-trash-symbolic", Gtk.IconSize.BUTTON))

                if actionedappdesktop != "" and actionedappdesktop is not None:
                    self.dOpenButton.set_visible(True)

                self.wpcformcontrolLabel.set_visible(False)
                self.wpcformcontrolLabel.set_markup("")

                sizethread1 = threading.Thread(target=self.size_worker_thread, daemon=True)
                sizethread1.start()

            elif self.Package.isinstalled(actionedappname) is False:

                self.set_button_class(self.dActionButton, 0)
                self.set_button_class(self.dActionInfoButton, 0)

                self.dActionButton.set_label(_(" Install"))
                self.dActionButton.set_image(
                    Gtk.Image.new_from_icon_name("document-save-symbolic", Gtk.IconSize.BUTTON))

                self.dOpenButton.set_visible(False)

                self.wpcformcontrolLabel.set_visible(True)
                self.wpcformcontrolLabel.set_markup(
                    "<span color='red'>{}</span>".format(_("You need to install the application")))

                sizethread2 = threading.Thread(target=self.size_worker_thread, daemon=True, args=(actionedappcommand,))
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

                    self.set_button_class(self.dActionButton, 2)
                    self.set_button_class(self.dActionInfoButton, 2)

                self.clear_drequired_popup()

                self.dSize.set_markup(_("None"))
                self.dSizeTitle.set_text(_("Download Size"))
                self.dSizeGrid.set_tooltip_text(None)

        if repo == 2:  # repo apps
            if self.Package.isinstalled(actionedappname):
                self.set_button_class(self.raction, 1)
                self.set_button_class(self.ractioninfo, 1)
                self.raction.set_label(_(" Uninstall"))
                self.raction.set_image(Gtk.Image.new_from_icon_name("user-trash-symbolic", Gtk.IconSize.BUTTON))
            else:
                self.set_button_class(self.raction, 0)
                self.set_button_class(self.ractioninfo, 0)
                self.raction.set_label(_(" Install"))
                self.raction.set_image(Gtk.Image.new_from_icon_name("document-save-symbolic", Gtk.IconSize.BUTTON))

    def control_myapps(self, actionedappname, actionedappdesktop, status, error, cachestatus):
        self.Logger.info("in control_myapps")
        # if self.homestack.get_visible_child_name() == "myapps":
        if status == 0 and not error and cachestatus:
            if self.isinstalled:
                self.Logger.info("{} removing from myapps".format(actionedappdesktop))
                if "/" in actionedappdesktop:
                    for row in self.MyAppsListBox:
                        if row.get_children()[0].name == actionedappdesktop:
                            if self.ui_myapp_pop_stack.get_visible_child_name() == "details" and actionedappname == self.myapp_toremove:
                                self.Logger.info("in pop_myapp popdown")
                                self.MyAppsDetailsPopover.set_relative_to(self.MyAppsListBox)
                                self.MyAppsDetailsPopover.popdown()
                            self.MyAppsListBox.remove(row)
                else:
                    for row in self.MyAppsListBox:
                        try:
                            rowapp = os.path.basename(row.get_children()[0].name)
                            if rowapp == actionedappdesktop:
                                if self.ui_myapp_pop_stack.get_visible_child_name() == "details" and actionedappname == self.myapp_toremove:
                                    self.Logger.info("in pop_myapp popdown")
                                    self.MyAppsDetailsPopover.set_relative_to(self.MyAppsListBox)
                                    self.MyAppsDetailsPopover.popdown()

                                self.MyAppsListBox.remove(row)
                        except Exception as e:
                            self.Logger.warning("Error in control_myapps")
                            self.Logger.exception("{}".format(e))
                            pass
            else:
                self.Logger.info("{} adding to myapps".format(actionedappdesktop))
                valid, dic = self.Package.parse_desktopfile(os.path.basename(actionedappdesktop))
                if valid:
                    self.addtoMyApps(dic)
                    GLib.idle_add(self.MyAppsListBox.show_all)
                    self.MyAppsListBox.set_sort_func(self.myapps_sort_func)

            if self.myappsstack.get_visible_child_name() == "details" and actionedappname == self.myapp_toremove:
                self.Logger.info("in myappsstack details actionedappname status=0")
                self.ma_action_buttonbox.set_sensitive(False)

            if self.ui_myapp_pop_stack.get_visible_child_name() == "details" and actionedappname == self.myapp_toremove:
                self.Logger.info("in pop_myapp details status=0")
                self.ui_myapp_pop_uninstall_button.set_sensitive(False)
                self.MyAppsDetailsPopover.popdown()

        else:
            if self.myappsstack.get_visible_child_name() == "details" and actionedappname == self.myapp_toremove:
                self.Logger.info("in myappsstack details actionedappname status!=0")
                self.ma_action_buttonbox.set_sensitive(True)

            if self.ui_myapp_pop_stack.get_visible_child_name() == "details" and actionedappname == self.myapp_toremove:
                self.Logger.info("in pop_myapp details status!=0")
                self.ui_myapp_pop_uninstall_button.set_sensitive(True)

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
            self.Logger.exception("{}".format(e))

    def sendDownloaded(self, appname):
        try:
            installed = self.Package.isinstalled(appname)
            if installed is None:
                installed = False
            version = self.Package.installed_version(appname)
            if version is None:
                version = ""
            dic = {"mac": self.mac, "app": appname, "installed": installed, "appversion": version,
                   "distro": self.user_distro_full}
            self.AppRequest.send("POST", self.Server.serverurl + self.Server.serversenddownload, dic)
        except Exception as e:
            self.Logger.warning("sendDownloaded Error")
            self.Logger.exception("{}".format(e))

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
        self.Logger.info("{}".format(line))
        return True

    def onSysProcessStderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        self.Logger.info("{}".format(line))
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

            self.controlView(self.actionedenablingappname, self.actionedenablingappdesktop,
                             self.actionedenablingappcommand)

        if self.correctsourcesclicked:
            if status == 0:
                self.preflabel_settext("<span weight='bold'>{}\n{}</span>".format(
                    _("Fixing of system package manager sources list is done."),
                    _("Package manager cache automatically updated.")))
                self.Package.updatecache()
            self.headerAptUpdateSpinner.set_visible(False)
            self.headerAptUpdateSpinner.stop()
            self.prefcorrectbutton.set_sensitive(True)

            self.correctsourcesclicked = False

        if self.aptupdateclicked:
            self.Logger.info("apt update done (detail page), status code : {}".format(status))
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
                self.Logger.info("wrong password on apt update (detail page)")
            else:
                self.dAptUpdateBox.set_visible(True)
                self.dAptUpdateInfoLabel.set_visible(True)
                self.dAptUpdateInfoLabel.set_markup("<span color='red'>{}{}</span>".format(
                    _("An error occurred while updating the package cache. Exit Code: "), status))
            self.aptupdateclicked = False

        self.Logger.info("SysProcess Exit Code: {}".format(status))

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
        self.Logger.info("{}".format(line))
        return True

    def onAptUpdateProcessStderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        self.Logger.info("{}".format(line))
        return True

    def onAptUpdateProcessExit(self, pid, status):
        self.Package.updatecache()
        self.headerAptUpdateSpinner.set_visible(False)
        self.headerAptUpdateSpinner.stop()
        if status == 0:
            try:
                timestamp = int(datetime.now().timestamp())
            except Exception as e:
                self.Logger.warning("timestamp Error: {}")
                self.Logger.exception("{}".format(e))

                timestamp = 0
            self.UserSettings.writeConfig(self.UserSettings.config_usi, self.UserSettings.config_ea,
                                          self.UserSettings.config_saa, self.UserSettings.config_hera,
                                          self.UserSettings.config_icon, self.UserSettings.config_sgc,
                                          self.UserSettings.config_udt, self.UserSettings.config_aptup,
                                          timestamp, self.UserSettings.config_forceaptuptime)

            if self.Package.upgradable():
                if not self.updates_button.get_visible():
                    GLib.idle_add(self.header_buttonbox.pack_start, self.updates_button, False, True, 0)
                    GLib.idle_add(self.updates_button.set_visible, True)
                    GLib.idle_add(self.updates_button.set_sensitive, True)
            else:
                GLib.idle_add(self.updates_button.set_visible, False)
                GLib.idle_add(self.updates_button.set_sensitive, False)

            self.auto_apt_update_finished = True

    def startGroupProcess(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(params, flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_output=True, standard_error=True)
        GLib.io_add_watch(GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.onGroupProcessStdout)
        GLib.io_add_watch(GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.onGroupProcessStderr)
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, self.onGroupProcessExit)

        return pid

    def onGroupProcessStdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        self.Logger.info("onGroupProcessStdout - line: {}".format(line))
        return True

    def onGroupProcessStderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        self.Logger.info("onGroupProcessStderr - line: {}".format(line))
        self.grouperrormessage = line
        return True

    def onGroupProcessExit(self, pid, status):
        self.Logger.info("onGroupProcessExit - status: {}".format(status))
        self.control_groups()
        if status == 32256:  # operation cancelled | Request dismissed
            self.preflabel_settext("")
        else:
            self.preflabel_settext(
                "<small><span color='red' weight='light'>{}</span></small>".format(self.grouperrormessage))

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

    def startVteProcess(self, command):
        pty = Vte.Pty.new_sync(Vte.PtyFlags.DEFAULT)
        self.vteterm.set_pty(pty)
        self.vteterm.connect("child-exited", self.onVteDone)
        self.vteterm.spawn_sync(
            Vte.PtyFlags.DEFAULT,
            os.environ['HOME'],
            command,
            [],
            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            None,
            None,
        )

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
                if self.myapps_perm == 1:
                    GLib.idle_add(self.myapps_button.set_sensitive, True)
                else:
                    GLib.idle_add(self.myapps_button.set_sensitive, False)
                GLib.idle_add(self.store_button.set_sensitive, True)
                if self.repo_perm == 1:
                    GLib.idle_add(self.repo_button.set_sensitive, True)
                else:
                    GLib.idle_add(self.repo_button.set_sensitive, False)
            else:
                self.tryfixstack.set_visible_child_name("error")
                self.isbroken = True
                self.Logger.warning("Error while updating Cache")
        else:
            self.Logger.info("onVteDone status: {}".format(status))

    def upgrade_vte_event(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            if event.button.button == 3:
                widget.popup_for_device(None, None, None, None, None,
                                        event.button.button, event.time)
                return True
        return False

    def upgrade_vte_menu_action(self, widget, terminal):
        terminal.copy_clipboard()

    def upgrade_vte_start_process(self, command):
        pty = Vte.Pty.new_sync(Vte.PtyFlags.DEFAULT)
        self.upgrade_vteterm.set_pty(pty)
        try:
            self.upgrade_vteterm.spawn_async(
                Vte.PtyFlags.DEFAULT,
                os.environ['HOME'],
                command,
                None,
                GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                None,
                None,
                -1,
                None,
                self.upgrade_vte_create_spawn_callback,
                None
            )
        except Exception as e:
            # old version VTE doesn't have spawn_async so use spawn_sync
            self.Logger.exception("{}".format(e))
            self.upgrade_vteterm.connect("child-exited", self.upgrade_vte_on_done)
            self.upgrade_vteterm.spawn_sync(
                Vte.PtyFlags.DEFAULT,
                os.environ['HOME'],
                command,
                [],
                GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                None,
                None,
            )

    def upgrade_vte_create_spawn_callback(self, terminal, pid, error, userdata):
        self.upgrade_vteterm.connect("child-exited", self.upgrade_vte_on_done)

    def upgrade_vte_on_done(self, terminal, status):
        self.Logger.info("upgrade_vte_on_done status: {}".format(status))
        self.upgrade_inprogress = False
        if status == 32256:  # operation cancelled | Request dismissed
            self.upgrade_stack.set_visible_child_name("main")
        elif status == 2816:  # dpkg lock error
            GLib.idle_add(self.upgrade_info_box.set_visible, True)
            GLib.idle_add(self.upgrade_info_dpkgfix_button.set_visible, True)
            GLib.idle_add(self.upgrade_info_back_button.set_visible, True)
            self.upgrade_info_label.set_markup("<span color='red'><b>{}</b></span>".format(
                _("Only one software management tool is allowed to run at the same time.\n"
                  "Please close the other application e.g. 'Update Manager', 'aptitude' or 'Synaptic' first.")))
        elif status == 3072:  # dpkg interrupt error
            GLib.idle_add(self.upgrade_info_box.set_visible, True)
            GLib.idle_add(self.upgrade_info_dpkgfix_button.set_visible, True)
            GLib.idle_add(self.upgrade_info_back_button.set_visible, True)
            self.upgrade_info_label.set_markup("<span color='red'><b>{}</b></span>".format(
                _("dpkg interrupt detected. Click the 'Fix' button or\n"
                  "manually run 'sudo dpkg --configure -a' to fix the problem.")))
        else:
            self.Package.updatecache()
            self.upgradables_page_setted = False
            if self.homestack.get_visible_child_name() == "upgrade":
                GLib.idle_add(self.upgrade_info_label.set_markup,
                              "<b>{}</b>".format(_("Process completed.")))
                GLib.idle_add(self.upgrade_info_box.set_visible, True)
                GLib.idle_add(self.upgrade_info_back_button.set_visible, False)
                GLib.idle_add(self.upgrade_info_ok_button.set_visible, True)

    def dpkgconfigure_vte_event(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            if event.button.button == 3:
                widget.popup_for_device(None, None, None, None, None,
                                        event.button.button, event.time)
                return True
        return False

    def dpkgconfigure_vte_menu_action(self, widget, terminal):
        terminal.copy_clipboard()

    def dpkgconfigure_vte_start_process(self, command):
        if self.dpkgconfigure_vteterm:
            self.dpkgconfigure_vteterm.get_parent().remove(self.dpkgconfigure_vteterm)

        self.dpkgconfigure_vteterm = Vte.Terminal()
        self.dpkgconfigure_vteterm.set_scrollback_lines(-1)
        dpkgconfigure_vte_menu = Gtk.Menu()
        dpkgconfigure_vte_menu_items = Gtk.MenuItem(label=_("Copy selected text"))
        dpkgconfigure_vte_menu.append(dpkgconfigure_vte_menu_items)
        dpkgconfigure_vte_menu_items.connect("activate", self.dpkgconfigure_vte_menu_action, self.dpkgconfigure_vteterm)
        dpkgconfigure_vte_menu_items.show()
        self.dpkgconfigure_vteterm.connect_object("event", self.dpkgconfigure_vte_event, dpkgconfigure_vte_menu)
        self.interrupt_vte_box.add(self.dpkgconfigure_vteterm)
        self.dpkgconfigure_vteterm.show_all()

        pty = Vte.Pty.new_sync(Vte.PtyFlags.DEFAULT)
        self.dpkgconfigure_vteterm.set_pty(pty)
        try:
            self.dpkgconfigure_vteterm.spawn_async(
                Vte.PtyFlags.DEFAULT,
                os.environ['HOME'],
                command,
                None,
                GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                None,
                None,
                -1,
                None,
                self.dpkgconfigure_vte_create_spawn_callback,
                None
            )
        except Exception as e:
            # old version VTE doesn't have spawn_async so use spawn_sync
            self.Logger.exception("{}".format(e))
            self.dpkgconfigure_vteterm.connect("child-exited", self.dpkgconfigure_vte_on_done)
            self.dpkgconfigure_vteterm.spawn_sync(
                Vte.PtyFlags.DEFAULT,
                os.environ['HOME'],
                command,
                [],
                GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                None,
                None,
            )

    def dpkgconfigure_vte_create_spawn_callback(self, terminal, pid, error, userdata):
        self.dpkgconfigure_vteterm.connect("child-exited", self.dpkgconfigure_vte_on_done)

    def dpkgconfigure_vte_on_done(self, terminal, status):
        self.Logger.info("dpkgconfigure_vte_on_done status: {}".format(status))

        self.dpkgconfiguring = False
        self.bottominterrupt_fix_button.set_sensitive(True)
        self.bottominterrupthide_button.set_sensitive(True)

        self.upgrade_info_dpkgfix_button.set_sensitive(True)

        self.pop_interruptinfo_spinner.set_visible(False)
        self.pop_interruptinfo_spinner.stop()

        if status == 32256:  # operation cancelled | Request dismissed
            self.pop_interruptinfo_label.set_markup("<b>{}</b>".format(_("Error.")))
        else:
            self.pop_interruptinfo_label.set_markup("<b>{}</b>".format(_("Process completed.")))
            self.pop_interruptinfo_ok_button.set_visible(True)
