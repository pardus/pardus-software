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
import threading
import json
import cairo
from pathlib import Path
from hashlib import md5
from datetime import datetime, timezone
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

        self.user_locale = self.get_user_locale()
        self.Logger.info("user_locale: {}".format(self.user_locale))

        self.error = False
        self.dpkglockerror = False
        self.dpkgconferror = False
        self.dpkglockerror_message = ""
        self.error_message = ""

        self.searching = False

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

        self.mainstack = self.GtkBuilder.get_object("mainstack")
        self.homestack = self.GtkBuilder.get_object("homestack")
        self.bottomstack = self.GtkBuilder.get_object("bottomstack")

        self.ui_back_button = self.GtkBuilder.get_object("ui_back_button")
        self.ui_back_button.set_sensitive(False)

        self.splashspinner = self.GtkBuilder.get_object("splashspinner")
        self.splashbar = self.GtkBuilder.get_object("splashbar")
        self.splashlabel = self.GtkBuilder.get_object("splashlabel")
        self.splashbarstatus = True

        # myapps remove popup
        self.ui_myapp_pop_stack = self.GtkBuilder.get_object("ui_myapp_pop_stack")
        self.ui_myapp_pop_spinner = self.GtkBuilder.get_object("ui_myapp_pop_spinner")
        self.ui_myapp_pop_sw = self.GtkBuilder.get_object("ui_myapp_pop_sw")

        self.ui_myapp_pop_app = self.GtkBuilder.get_object("ui_myapp_pop_app")
        self.ui_myapp_pop_package = self.GtkBuilder.get_object("ui_myapp_pop_package")
        self.ui_myapp_pop_uninstall_button = self.GtkBuilder.get_object("ui_myapp_pop_uninstall_button")

        self.ui_myapp_pop_toremove_label = self.GtkBuilder.get_object("ui_myapp_pop_toremove_label")
        self.ui_myapp_pop_toinstall_label = self.GtkBuilder.get_object("ui_myapp_pop_toinstall_label")
        self.ui_myapp_pop_broken_label = self.GtkBuilder.get_object("ui_myapp_pop_broken_label")
        self.ui_myapp_pop_fsize_label = self.GtkBuilder.get_object("ui_myapp_pop_fsize_label")
        self.ui_myapp_pop_dsize_label = self.GtkBuilder.get_object("ui_myapp_pop_dsize_label")
        self.ui_myapp_pop_isize_label = self.GtkBuilder.get_object("ui_myapp_pop_isize_label")

        self.ui_myapp_pop_disclaimer_remove_label = self.GtkBuilder.get_object("ui_myapp_pop_disclaimer_remove_label")

        self.ui_myapp_pop_notfound_image = self.GtkBuilder.get_object("ui_myapp_pop_notfound_image")
        self.ui_myapp_pop_notfound_name = self.GtkBuilder.get_object("ui_myapp_pop_notfound_name")

        self.ui_myapp_pop_toremove_box = self.GtkBuilder.get_object("ui_myapp_pop_toremove_box")
        self.ui_myapp_pop_toinstall_box = self.GtkBuilder.get_object("ui_myapp_pop_toinstall_box")
        self.ui_myapp_pop_broken_box = self.GtkBuilder.get_object("ui_myapp_pop_broken_box")
        self.ui_myapp_pop_fsize_box = self.GtkBuilder.get_object("ui_myapp_pop_fsize_box")
        self.ui_myapp_pop_dsize_box = self.GtkBuilder.get_object("ui_myapp_pop_dsize_box")
        self.ui_myapp_pop_isize_box = self.GtkBuilder.get_object("ui_myapp_pop_isize_box")

        self.ui_myapps_combobox = self.GtkBuilder.get_object("ui_myapps_combobox")
        self.ui_myapps_du_progress_box = self.GtkBuilder.get_object("ui_myapps_du_progress_box")
        self.ui_myapps_du_spinner = self.GtkBuilder.get_object("ui_myapps_du_spinner")

        self.ui_right_stack = self.GtkBuilder.get_object("ui_right_stack")

        self.ui_currentcat_label = self.GtkBuilder.get_object("ui_currentcat_label")
        self.ui_currentcat_image = self.GtkBuilder.get_object("ui_currentcat_image")

        self.ui_top_searchentry = self.GtkBuilder.get_object("ui_top_searchentry")
        self.ui_top_searchentry.set_sensitive(False)
        self.ui_top_searchentry.props.primary_icon_activatable = True
        self.ui_top_searchentry.props.primary_icon_sensitive = True

        self.ui_repoapps_flowbox = self.GtkBuilder.get_object("ui_repoapps_flowbox")
        self.ui_repotitle_box = self.GtkBuilder.get_object("ui_repotitle_box")

        self.ui_pardusapps_flowbox = self.GtkBuilder.get_object("ui_pardusapps_flowbox")
        self.ui_pardusapps_flowbox.set_filter_func(self.pardusapps_filter_function)

        self.ui_pardusapps_title_stack = self.GtkBuilder.get_object("ui_pardusapps_title_stack")
        self.ui_searchterm_label = self.GtkBuilder.get_object("ui_searchterm_label")

        self.ui_trend_flowbox = self.GtkBuilder.get_object("ui_trend_flowbox")
        self.ui_mostdown_flowbox = self.GtkBuilder.get_object("ui_mostdown_flowbox")
        self.ui_recent_flowbox = self.GtkBuilder.get_object("ui_recent_flowbox")
        self.ui_editor_flowbox = self.GtkBuilder.get_object("ui_editor_flowbox")

        self.ui_trendapps_flowbox = self.GtkBuilder.get_object("ui_trendapps_flowbox")
        self.ui_mostdownapps_flowbox = self.GtkBuilder.get_object("ui_mostdownapps_flowbox")
        self.ui_recentapps_flowbox = self.GtkBuilder.get_object("ui_recentapps_flowbox")

        self.ui_upgradableapps_flowbox = self.GtkBuilder.get_object("ui_upgradableapps_flowbox")
        self.ui_upgradableapps_box = self.GtkBuilder.get_object("ui_upgradableapps_box")
        self.ui_upgradableapps_count_label = self.GtkBuilder.get_object("ui_upgradableapps_count_label")
        self.ui_upgradables_combobox = self.GtkBuilder.get_object("ui_upgradables_combobox")
        self.ui_installedapps_box = self.GtkBuilder.get_object("ui_installedapps_box")
        self.ui_installedapps_flowbox = self.GtkBuilder.get_object("ui_installedapps_flowbox")
        self.ui_installedapps_flowbox.set_filter_func(self.installedapps_filter_function)

        self.ui_appdetails_scrolledwindow = self.GtkBuilder.get_object("ui_appdetails_scrolledwindow")

        self.ui_ad_name = self.GtkBuilder.get_object("ui_ad_name")
        self.ui_ad_icon = self.GtkBuilder.get_object("ui_ad_icon")
        self.ui_ad_subcategory_label = self.GtkBuilder.get_object("ui_ad_subcategory_label")
        self.ui_ad_top_category_label = self.GtkBuilder.get_object("ui_ad_top_category_label")
        self.ui_ad_top_avgrate_label = self.GtkBuilder.get_object("ui_ad_top_avgrate_label")
        self.ui_ad_top_download_label = self.GtkBuilder.get_object("ui_ad_top_download_label")
        self.ui_ad_top_size_label = self.GtkBuilder.get_object("ui_ad_top_size_label")
        self.ui_ad_top_depends_count_label = self.GtkBuilder.get_object("ui_ad_top_depends_count_label")
        self.ui_ad_action_button = self.GtkBuilder.get_object("ui_ad_action_button")
        self.ui_ad_disclaimer_button = self.GtkBuilder.get_object("ui_ad_disclaimer_button")
        self.ui_ad_remove_button = self.GtkBuilder.get_object("ui_ad_remove_button")
        self.ui_ad_image_box = self.GtkBuilder.get_object("ui_ad_image_box")

        self.ui_disclaimer_popover = self.GtkBuilder.get_object("ui_disclaimer_popover")

        self.ui_ad_top_stack = self.GtkBuilder.get_object("ui_ad_top_stack")
        self.ui_ad_action_stack = self.GtkBuilder.get_object("ui_ad_action_stack")
        self.ui_ad_about_box = self.GtkBuilder.get_object("ui_ad_about_box")
        self.ui_ad_details_box = self.GtkBuilder.get_object("ui_ad_details_box")
        self.ui_ad_dependencies_box = self.GtkBuilder.get_object("ui_ad_dependencies_box")
        self.ui_ad_availablerepos_box = self.GtkBuilder.get_object("ui_ad_availablerepos_box")
        self.ui_ad_ratings_box = self.GtkBuilder.get_object("ui_ad_ratings_box")

        self.ui_ad_image_scrolledwindow = self.GtkBuilder.get_object("ui_ad_image_scrolledwindow")
        self.ui_ad_image_scrolledwindow.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK
        )
        self.ui_ad_image_scrolledwindow.connect("button-press-event", self.on_ui_ad_image_button_press)
        self.ui_ad_image_scrolledwindow.connect("motion-notify-event", self.on_ui_ad_image_mouse_drag)
        self.ui_ad_image_scrolledwindow.connect("button-release-event", self.on_ui_ad_image_button_release)
        self.ui_ad_image_dragging = False
        self.ui_ad_image_last_x = 0
        self.ui_ad_image_total_drag = 0
        self.ui_ad_image_drag_threshold = 8
        self.ui_ad_image_drag_touch_threshold = 2
        self.ui_ad_image_is_touch = False

        self.ui_ad_description_label = self.GtkBuilder.get_object("ui_ad_description_label")
        self.ui_ad_version_label = self.GtkBuilder.get_object("ui_ad_version_label")
        self.ui_ad_sizetitle_label = self.GtkBuilder.get_object("ui_ad_sizetitle_label")
        self.ui_ad_size_label = self.GtkBuilder.get_object("ui_ad_size_label")
        self.ui_ad_required_sizetitle_label = self.GtkBuilder.get_object("ui_ad_required_sizetitle_label")
        self.ui_ad_required_size_label = self.GtkBuilder.get_object("ui_ad_required_size_label")
        self.ui_ad_type_label = self.GtkBuilder.get_object("ui_ad_type_label")
        self.ui_ad_category_label = self.GtkBuilder.get_object("ui_ad_category_label")
        self.ui_ad_license_label = self.GtkBuilder.get_object("ui_ad_license_label")
        self.ui_ad_component_label = self.GtkBuilder.get_object("ui_ad_component_label")
        self.ui_ad_maintainer_name_label = self.GtkBuilder.get_object("ui_ad_maintainer_name_label")
        self.ui_ad_maintainer_web_label = self.GtkBuilder.get_object("ui_ad_maintainer_web_label")
        self.ui_ad_maintainer_mail_label = self.GtkBuilder.get_object("ui_ad_maintainer_mail_label")
        self.ui_ad_available_repos_box = self.GtkBuilder.get_object("ui_ad_available_repos_box")

        self.ui_ad_install_list_box = self.GtkBuilder.get_object("ui_ad_install_list_box")
        self.ui_ad_install_list_eventbox = self.GtkBuilder.get_object("ui_ad_install_list_eventbox")
        self.ui_ad_install_list_image = self.GtkBuilder.get_object("ui_ad_install_list_image")
        self.ui_ad_install_list_revealer = self.GtkBuilder.get_object("ui_ad_install_list_revealer")
        self.ui_ad_install_list_label = self.GtkBuilder.get_object("ui_ad_install_list_label")
        self.ui_ad_install_list_count_label = self.GtkBuilder.get_object("ui_ad_install_list_count_label")

        self.ui_ad_remove_list_box = self.GtkBuilder.get_object("ui_ad_remove_list_box")
        self.ui_ad_remove_list_eventbox = self.GtkBuilder.get_object("ui_ad_remove_list_eventbox")
        self.ui_ad_remove_list_image = self.GtkBuilder.get_object("ui_ad_remove_list_image")
        self.ui_ad_remove_list_revealer = self.GtkBuilder.get_object("ui_ad_remove_list_revealer")
        self.ui_ad_remove_list_label = self.GtkBuilder.get_object("ui_ad_remove_list_label")
        self.ui_ad_remove_list_count_label = self.GtkBuilder.get_object("ui_ad_remove_list_count_label")

        self.ui_ad_broken_list_box = self.GtkBuilder.get_object("ui_ad_broken_list_box")
        self.ui_ad_broken_list_eventbox = self.GtkBuilder.get_object("ui_ad_broken_list_eventbox")
        self.ui_ad_broken_list_image = self.GtkBuilder.get_object("ui_ad_broken_list_image")
        self.ui_ad_broken_list_revealer = self.GtkBuilder.get_object("ui_ad_broken_list_revealer")
        self.ui_ad_broken_list_label = self.GtkBuilder.get_object("ui_ad_broken_list_label")
        self.ui_ad_broken_list_count_label = self.GtkBuilder.get_object("ui_ad_broken_list_count_label")

        self.ui_ad_bottom_avgrate_label = self.GtkBuilder.get_object("ui_ad_bottom_avgrate_label")
        self.ui_ad_bottom_rate_count_label = self.GtkBuilder.get_object("ui_ad_bottom_rate_count_label")

        self.ui_ad_rating_star1_image = self.GtkBuilder.get_object("ui_ad_rating_star1_image")
        self.ui_ad_rating_star2_image = self.GtkBuilder.get_object("ui_ad_rating_star2_image")
        self.ui_ad_rating_star3_image = self.GtkBuilder.get_object("ui_ad_rating_star3_image")
        self.ui_ad_rating_star4_image = self.GtkBuilder.get_object("ui_ad_rating_star4_image")
        self.ui_ad_rating_star5_image = self.GtkBuilder.get_object("ui_ad_rating_star5_image")

        self.ui_rating_prg1_progressbar = self.GtkBuilder.get_object("ui_rating_prg1_progressbar")
        self.ui_rating_prg2_progressbar = self.GtkBuilder.get_object("ui_rating_prg2_progressbar")
        self.ui_rating_prg3_progressbar = self.GtkBuilder.get_object("ui_rating_prg3_progressbar")
        self.ui_rating_prg4_progressbar = self.GtkBuilder.get_object("ui_rating_prg4_progressbar")
        self.ui_rating_prg5_progressbar = self.GtkBuilder.get_object("ui_rating_prg5_progressbar")

        self.ui_rating_count1_label = self.GtkBuilder.get_object("ui_rating_count1_label")
        self.ui_rating_count2_label = self.GtkBuilder.get_object("ui_rating_count2_label")
        self.ui_rating_count3_label = self.GtkBuilder.get_object("ui_rating_count3_label")
        self.ui_rating_count4_label = self.GtkBuilder.get_object("ui_rating_count4_label")
        self.ui_rating_count5_label = self.GtkBuilder.get_object("ui_rating_count5_label")

        self.ui_ad_comments_flowbox = self.GtkBuilder.get_object("ui_ad_comments_flowbox")
        self.ui_ad_more_comment_button = self.GtkBuilder.get_object("ui_ad_more_comment_button")

        self.ui_comment_dialog = self.GtkBuilder.get_object("ui_comment_dialog")
        self.ui_comment_main_stack = self.GtkBuilder.get_object("ui_comment_main_stack")
        self.ui_comment_mid_stack = self.GtkBuilder.get_object("ui_comment_mid_stack")
        self.ui_comment_mid_editable_stack = self.GtkBuilder.get_object("ui_comment_mid_editable_stack")
        self.ui_comment_bottom_stack = self.GtkBuilder.get_object("ui_comment_bottom_stack")
        self.ui_comment_icon_image = self.GtkBuilder.get_object("ui_comment_icon_image")
        self.ui_comment_appname_label = self.GtkBuilder.get_object("ui_comment_appname_label")
        self.ui_comment_subcategory_label = self.GtkBuilder.get_object("ui_comment_subcategory_label")
        self.ui_comment_version_label = self.GtkBuilder.get_object("ui_comment_version_label")
        self.ui_comment_fullname_entry = self.GtkBuilder.get_object("ui_comment_fullname_entry")
        self.ui_comment_content_textview = self.GtkBuilder.get_object("ui_comment_content_textview")
        self.ui_comment_content_textbuffer = self.GtkBuilder.get_object("ui_comment_content_textbuffer")
        self.ui_comment_send_button = self.GtkBuilder.get_object("ui_comment_send_button")
        self.ui_comment_error_label = self.GtkBuilder.get_object("ui_comment_error_label")
        self.ui_comment_info_label = self.GtkBuilder.get_object("ui_comment_info_label")
        self.ui_comment_star1_image = self.GtkBuilder.get_object("ui_comment_star1_image")
        self.ui_comment_star2_image = self.GtkBuilder.get_object("ui_comment_star2_image")
        self.ui_comment_star3_image = self.GtkBuilder.get_object("ui_comment_star3_image")
        self.ui_comment_star4_image = self.GtkBuilder.get_object("ui_comment_star4_image")
        self.ui_comment_star5_image = self.GtkBuilder.get_object("ui_comment_star5_image")
        self.ui_comment_own_star1_image = self.GtkBuilder.get_object("ui_comment_own_star1_image")
        self.ui_comment_own_star2_image = self.GtkBuilder.get_object("ui_comment_own_star2_image")
        self.ui_comment_own_star3_image = self.GtkBuilder.get_object("ui_comment_own_star3_image")
        self.ui_comment_own_star4_image = self.GtkBuilder.get_object("ui_comment_own_star4_image")
        self.ui_comment_own_star5_image = self.GtkBuilder.get_object("ui_comment_own_star5_image")
        self.ui_comment_own_fullname_label = self.GtkBuilder.get_object("ui_comment_own_fullname_label")
        self.ui_comment_own_content_label = self.GtkBuilder.get_object("ui_comment_own_content_label")
        self.ui_comment_own_edit_button = self.GtkBuilder.get_object("ui_comment_own_edit_button")
        self.ui_comment_own_date_label = self.GtkBuilder.get_object("ui_comment_own_date_label")

        self.ui_suggest_dialog = self.GtkBuilder.get_object("ui_suggest_dialog")
        self.ui_suggest_main_stack = self.GtkBuilder.get_object("ui_suggest_main_stack")
        self.ui_suggest_appname_entry = self.GtkBuilder.get_object("ui_suggest_appname_entry")
        self.ui_suggest_appweb_entry = self.GtkBuilder.get_object("ui_suggest_appweb_entry")
        self.ui_suggest_username_entry = self.GtkBuilder.get_object("ui_suggest_username_entry")
        self.ui_suggest_usermail_entry = self.GtkBuilder.get_object("ui_suggest_usermail_entry")
        self.ui_suggest_appweb_entry = self.GtkBuilder.get_object("ui_suggest_appweb_entry")
        self.ui_suggest_why_textview = self.GtkBuilder.get_object("ui_suggest_why_textview")
        self.ui_suggest_why_textbuffer = self.GtkBuilder.get_object("ui_suggest_why_textbuffer")
        self.ui_suggest_error_label = self.GtkBuilder.get_object("ui_suggest_error_label")
        self.ui_suggest_send_button = self.GtkBuilder.get_object("ui_suggest_send_button")

        self.ui_image_popover = self.GtkBuilder.get_object("ui_image_popover")
        self.ui_image_stack = self.GtkBuilder.get_object("ui_image_stack")
        self.ui_image_resize_image = self.GtkBuilder.get_object("ui_image_resize_image")

        self.ui_myapp_details_popover = self.GtkBuilder.get_object("ui_myapp_details_popover")

        self.ui_headermenu_popover = self.GtkBuilder.get_object("ui_headermenu_popover")
        self.ui_headermenu_button = self.GtkBuilder.get_object("ui_headermenu_button")

        self.ui_header_queue_button = self.GtkBuilder.get_object("ui_header_queue_button")
        self.ui_header_aptupdate_spinner = self.GtkBuilder.get_object("ui_header_aptupdate_spinner")

        self.aboutdialog = self.GtkBuilder.get_object("aboutdialog")
        self.aboutdialog.set_program_name(_("Pardus Software Center"))
        if self.aboutdialog.get_titlebar() is None:
            about_headerbar = Gtk.HeaderBar.new()
            about_headerbar.set_show_close_button(True)
            about_headerbar.set_title(_("About Pardus Software Center"))
            about_headerbar.pack_start(Gtk.Image.new_from_icon_name("pardus-software", Gtk.IconSize.LARGE_TOOLBAR))
            about_headerbar.show_all()
            self.aboutdialog.set_titlebar(about_headerbar)

        self.ui_settings_dark_switch = self.GtkBuilder.get_object("ui_settings_dark_switch")
        self.ui_settings_animations_switch = self.GtkBuilder.get_object("ui_settings_animations_switch")
        self.ui_settings_gcomments_switch = self.GtkBuilder.get_object("ui_settings_gcomments_switch")
        self.ui_settings_update_switch = self.GtkBuilder.get_object("ui_settings_update_switch")
        self.ui_settings_available_switch = self.GtkBuilder.get_object("ui_settings_available_switch")

        self.ui_settings_update_label = self.GtkBuilder.get_object("ui_settings_update_label")

        self.ui_settings_cache_button = self.GtkBuilder.get_object("ui_settings_cache_button")
        self.ui_settings_cache_info_label = self.GtkBuilder.get_object("ui_settings_cache_info_label")
        self.ui_settings_cache_size_label = self.GtkBuilder.get_object("ui_settings_cache_size_label")
        self.ui_settings_password_button = self.GtkBuilder.get_object("ui_settings_password_button")
        self.ui_settings_password_info_label = self.GtkBuilder.get_object("ui_settings_password_info_label")

        self.ui_tryfix_stack = self.GtkBuilder.get_object("ui_tryfix_stack")
        self.ui_tryfix_button = self.GtkBuilder.get_object("ui_tryfix_button")
        self.ui_tryfix_spinner = self.GtkBuilder.get_object("ui_tryfix_spinner")
        self.ui_tryfix_spinner = self.GtkBuilder.get_object("ui_tryfix_spinner")
        self.ui_tryfix_cancel_button = self.GtkBuilder.get_object("ui_tryfix_cancel_button")
        self.ui_tryfix_confirm_button = self.GtkBuilder.get_object("ui_tryfix_confirm_button")
        self.ui_tryfix_done_button = self.GtkBuilder.get_object("ui_tryfix_done_button")


        self.noserverlabel = self.GtkBuilder.get_object("noserverlabel")

        if self.user_locale == "tr":
            self.current_category = "tümü"
        else:
            self.current_category = "all"

        self.mac = self.getMac()

        self.par_desc_more = self.GtkBuilder.get_object("par_desc_more")

        self.MainWindow = self.GtkBuilder.get_object("MainWindow")
        self.MainWindow.set_application(application)
        self.MainWindow.set_title(_("Pardus Software Center"))
        self.control_display()
        self.mainstack.set_visible_child_name("splash")

        self.isinstalled = None
        self.isupgrade = False

        self.dpkgconfiguring = False

        self.ui_comment_own = {}

        self.ui_app_name = ""

        self.inprogress_app_name = ""
        self.inprogress_command = ""
        self.inprogress_desktop = ""

        self.queue = []
        self.inprogress = False

        self.isbroken = False

        self.connection_error_after = False
        self.auto_apt_update_finished = False

        self.apps = {}
        self.apps_full = {}
        self.cats = []

        self.myapp_toremove_list = []
        self.myapp_toremove = ""
        self.myapp_toremove_desktop = ""
        self.myapp_toremove_icon = ""

        self.important_packages = ["pardus-common-desktop", "pardus-xfce-desktop", "pardus-gnome-desktop",
                                   "pardus-edu-common-desktop", "pardus-edu-gnome-desktop", "eta-common-desktop",
                                   "eta-gnome-desktop", "eta-nonhid-gnome-desktop", "eta-gnome-desktop-other",
                                   "eta-nonhid-gnome-desktop-other", "xfce4-session", "gnome-session",
                                   "cinnamon", "cinnamon-session", "cinnamon-desktop-data", "eta-desktop"]

        self.i386_packages = ["wine"]

        self.errormessage = ""
        self.grouperrormessage = ""

        self.imgfullscreen_count = 0

        self.slider_current_page = 0

        self.comment_star_point = 0

        self.stack_history = []

        settings = Gtk.Settings.get_default()
        layout = settings.get_property("gtk-decoration-layout") or ""
        self.Logger.info(f"decoration_layout: {layout}")

        # remove icon from left side of decoration
        parts = layout.split(":", 1)
        left = parts[0]
        right = parts[1] if len(parts) > 1 else None
        left_items = [item.strip() for item in left.split(",") if item.strip() and item.strip() != "icon"]
        left_clean = ",".join(left_items)
        if right is None:
            new_layout = left_clean
        else:
            new_left = left_clean
            new_right = right
            if new_left == "" and new_right != "":
                new_layout = f":{new_right}"
            elif new_left != "" and new_right == "":
                new_layout = f"{new_left}:"
            elif new_left != "" and new_right != "":
                new_layout = f"{new_left}:{new_right}"
            else:
                new_layout = ":"

        settings.set_property("gtk-decoration-layout", new_layout)
        self.Logger.info(f"new_decoration_layout: {new_layout}")

        theme_name = "{}".format(settings.get_property('gtk-theme-name')).lower().strip()
        self.Logger.info(f"theme_name: {theme_name}")

        cssProvider = Gtk.CssProvider()
        if theme_name.startswith("pardus") or theme_name.startswith("adwaita"):
            cssProvider.load_from_path(os.path.dirname(os.path.abspath(__file__)) + "/../css/adwaita.css")
        else:
            cssProvider.load_from_path(os.path.dirname(os.path.abspath(__file__)) + "/../css/base.css")
        screen = Gdk.Screen.get_default()
        styleContext = Gtk.StyleContext()
        styleContext.add_provider_for_screen(screen, cssProvider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        self.tryfix_vteterm = None
        self.ui_tryfix_vte_sw = self.GtkBuilder.get_object("ui_tryfix_vte_sw")

        self.dpkgconfigure_vteterm = None
        self.interrupt_vte_box = self.GtkBuilder.get_object("interrupt_vte_box")

        self.ui_queue_flowbox = self.GtkBuilder.get_object("ui_queue_flowbox")
        self.ui_queue_stack = self.GtkBuilder.get_object("ui_queue_stack")

        self.ui_leftcats_box = self.GtkBuilder.get_object("ui_leftcats_box")
        self.ui_leftcats_listbox = self.GtkBuilder.get_object("ui_leftcats_listbox")
        self.ui_leftupdates_listbox = self.GtkBuilder.get_object("ui_leftupdates_listbox")
        self.ui_leftupdates_separator = self.GtkBuilder.get_object("ui_leftupdates_separator")
        self.ui_leftinstalled_listbox = self.GtkBuilder.get_object("ui_leftinstalled_listbox")
        self.ui_slider_stack = self.GtkBuilder.get_object("ui_slider_stack")
        self.ui_slider_overlay = self.GtkBuilder.get_object("ui_slider_overlay")

        # Set version
        # If not getted from __version__ file then accept version in MainWindow.glade file
        try:
            version = open(os.path.dirname(os.path.abspath(__file__)) + "/__version__").readline()
            self.aboutdialog.set_version(version)
        except:
            pass

        self.home_trend_count = 8
        self.home_mostdown_count = 8
        self.home_recent_count = 4

        self.myapps_du_cancel_event = None

        self.status_server_apps = False
        self.status_server_icons = False
        self.status_server_images = False
        self.status_server_cats = False
        self.status_server_home = False

        self.AppImage = AppImage()
        self.AppImage.app_image_from_server = self.app_image_from_server

        self.AppDetail = AppDetail()
        self.AppDetail.app_details_from_server = self.app_details_from_server

        self.AppRequest = AppRequest()
        self.AppRequest.rating_response_from_server = self.rating_response_from_server

        self.GnomeComment = GnomeComment()
        self.GnomeComment.gnome_comments_from_server = self.gnome_comments_from_server

        self.PardusComment = PardusComment()
        self.PardusComment.pardus_comments_from_server = self.pardus_comments_from_server

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

    def get_user_locale(self):
        lang = os.getenv("LANG")
        if lang:
            lang = lang.split(".", 1)[0].split("_", 1)[0]
        if not lang:
            loc = locale.getlocale()[0]
            if loc:
                lang = loc.split("_", 1)[0]
        lang = (lang or "en").lower()
        return lang if lang in ("tr", "en") else "en"

    # def on_MainWindow_configure_event(self, widget, event):
    #     width, height = widget.get_size()
    #     print("Size: {} x {}".format(width, height))

    def control_display(self):
        self.display_width = 1920
        width = 1071
        height = 750
        s = 1
        w = 1920
        h = 1080
        try:
            def get_active_monitor():
                display = Gdk.Display.get_default()
                monitor = display.get_primary_monitor()
                if monitor:
                    self.Logger.info("monitor from get_primary_monitor")
                    return monitor
                device_manager = display.get_device_manager()
                pointer = device_manager.get_client_pointer()
                if pointer:
                    screen, x, y = pointer.get_position()
                    monitor_num = screen.get_monitor_at_point(x, y)
                    if monitor_num >= 0:
                        self.Logger.info("monitor from pointer position")
                        return display.get_monitor(monitor_num)
                self.Logger.info("monitor from get_monitor(0)")
                return display.get_monitor(0)

            monitor = get_active_monitor()
            geometry = monitor.get_geometry()
            w = geometry.width
            h = geometry.height
            s = monitor.get_scale_factor()

            self.display_width = w

            if w > 1920 or h > 1080:
                width = int(w * 0.5578)
                height = int(h * 0.6944)

            if w <= 1370 or h <= 768:
                width = 1028
                height = 661

            if w <= 1024:
                width = 925

            self.MainWindow.resize(width, height)

        except Exception as e:
            self.Logger.warning("Error in controlDisplay")
            self.Logger.exception("{}".format(e))

        self.Logger.info("window w:{} h:{} | monitor w:{} h:{} s:{}".format(width, height, w, h, s))

    def hide_some_widgets(self):
        self.ui_myapps_du_progress_box.set_visible(False)
        self.ui_header_queue_button.set_visible(False)
        self.ui_header_aptupdate_spinner.set_visible(False)
        self.ui_upgradables_combobox.set_visible(False)
        self.ui_suggest_error_label.set_visible(False)
        self.bottomerrordetails_button.set_visible(False)
        self.ui_repotitle_box.set_visible(False)

    def worker(self):
        GLib.idle_add(self.splashspinner.start)
        self.setAnimations()
        self.package()
        self.server()

    def start_auto_apt_update_control(self):
        if self.Server.connection and self.UserSettings.config_aptup:
            waittime = 86400
            if self.UserSettings.config_forceaptuptime == 0:
                waittime = self.Server.aptuptime
            else:
                waittime = self.UserSettings.config_forceaptuptime
            if self.UserSettings.config_lastaptup + waittime < int(datetime.now().timestamp()):
                GLib.idle_add(self.ui_header_aptupdate_spinner.start)
                GLib.idle_add(self.ui_header_aptupdate_spinner.set_visible, True)
                command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/AutoAptUpdate.py"]
                self.apt_update_process(command)
            else:
                self.auto_apt_update_finished = True
        else:
            self.auto_apt_update_finished = True

    def control_pardus_software_update(self):
        if self.UserSettings.usercodename == "yirmibes":
            if self.Server.connection and not self.isbroken:
                user_version = self.Package.installed_version("pardus-software")
                server_version = self.Server.appversion_pardus25
                if server_version:
                    if user_version is not None:
                        version = self.Package.versionCompare(user_version, server_version)
                        if version and version < 0:
                            self.notify(message_summary=_("Pardus Software Center | New version available"),
                                        message_body=_("Please upgrade application"))

    def control_available_apps(self):
        if self.Server.connection:
            self.set_available_apps(available=self.UserSettings.config_saa)

    def control_args(self):
        if "details" in self.Application.args.keys():
            pardus_found = False
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
                package_name = ""
                app_name_without_desktop = app.replace(".desktop", "").strip()
                for key, details in self.apps_full.items():
                    candidates = [
                        key,
                        (details.get("desktop") or "").replace(".desktop", ""),
                        (details.get("gnomename") or "").replace(".desktop", "")
                    ]
                    extras = (details.get("desktopextras") or "").replace(" ", "")
                    if extras:
                        candidates.extend(e.replace(".desktop", "") for e in extras.split(",") if e)
                    if app_name_without_desktop in candidates:
                        pardus_found = True
                        package_name = key
                        break
                if pardus_found:
                    GLib.idle_add(self.set_app_details_page, package_name)
            except Exception as e:
                self.Logger.exception("{}".format(e))
            try:
                if not pardus_found:
                    app_name_with_desktop = app
                    if not app.endswith(".desktop"):
                        app_name_with_desktop = f"{app}.desktop"
                    for fbc in self.ui_installedapps_flowbox:
                        myapp_dic = fbc.get_children()[0].get_children()[0].name
                        if myapp_dic["id"] == app_name_with_desktop:
                            myapps_found = True
                            threading.Thread(target=self.myappsdetail_page_worker_thread,
                                             args=(myapp_dic["filename"], myapp_dic,), daemon=True).start()
                    if not myapps_found:
                        app_name = app.replace(".desktop", "").strip()
                        details = {"name": app_name, "icon_name": "ps-repo-package-symbolic",
                                   "description": self.Package.adv_description(app), "repo_app": True}
                        self.set_app_details_page({app_name: details}, source=2)
                        self.Logger.info(f"control_args: {app} not found")
                        pass
            except Exception as e:
                self.Logger.exception("{}".format(e))

    def set_initial_home(self):
        self.Logger.info("in set_initial_home")

        GLib.idle_add(self.mainstack.set_visible_child_name, "home")
        if self.Server.connection:
            if not self.isbroken:
                GLib.idle_add(self.homestack.set_visible_child_name, "pardushome")
                GLib.idle_add(self.ui_top_searchentry.set_sensitive, True)
            else:
                GLib.idle_add(self.homestack.set_visible_child_name, "fixapt")
        else:
            GLib.idle_add(self.homestack.set_visible_child_name, "noserver")
            GLib.idle_add(self.noserverlabel.set_markup, "<b>{}\n\n{}\n\n{}: {}</b>".format(
                _("Could not connect to server."),
                self.Server.error_message,
                _("Server address"),
                self.Server.serverurl))

        GLib.idle_add(self.splashspinner.stop)
        GLib.idle_add(self.splashlabel.set_text, "")

        self.Logger.info("set_initial_home done.")

    def prepend_server_icons(self):
        icon_theme = Gtk.IconTheme.get_default()
        icon_theme.prepend_search_path(self.UserSettings.app_icons_dir)
        icon_theme.prepend_search_path(self.UserSettings.cat_icons_dir)

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
        self.Logger.info("{} {}".format("config_showextapps", self.UserSettings.config_sera))
        self.Logger.info("{} {}".format("config_icon", self.UserSettings.config_icon))
        self.Logger.info("{} {}".format("config_showgnomecommments", self.UserSettings.config_sgc))
        self.Logger.info("{} {}".format("config_usedarktheme", self.UserSettings.config_udt))
        self.Logger.info("{} {}".format("config_aptup", self.UserSettings.config_aptup))
        self.Logger.info("{} {}".format("config_lastaptup", self.UserSettings.config_lastaptup))
        self.Logger.info("{} {}".format("config_forceaptuptime", self.UserSettings.config_forceaptuptime))

    def server(self):
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

        # self.Server.ServerAppsURLControlCB = self.ServerAppsURLControlCB
        self.Server.ServerHashesCB = self.ServerHashesCB
        self.Server.ServerFilesCB = self.ServerFilesCB

        # self.Logger.info("Controlling server")
        # GLib.idle_add(self.splashlabel.set_markup, "<b>{}</b>".format(_("Controlling server")))
        # self.Server.control_server(self.Server.serverurl + "/api/v2/test")

        self.Logger.info("Controlling server hashes")
        GLib.idle_add(self.splashlabel.set_markup, "<b>{}</b>".format(_("Controlling server hashes")))
        self.Server.get_hashes(self.Server.serverurl + self.Server.serverhash)

        self.Logger.info("server func done")

    def afterServers(self):
        GLib.idle_add(self.set_initial_home)
        GLib.idle_add(self.control_available_apps)
        GLib.idle_add(self.set_categories)
        GLib.idle_add(self.set_applications)
        GLib.idle_add(self.get_upgradables)
        GLib.idle_add(self.set_upgradables)
        GLib.idle_add(self.set_slider)
        GLib.idle_add(self.set_most_apps)
        GLib.idle_add(self.start_auto_apt_update_control)
        GLib.idle_add(self.control_pardus_software_update)

        GLib.idle_add(self.set_myapps)

    # def ServerAppsURLControlCB(self, status):
    #     self.Logger.info("ServerAppsURLControlCB : {}".format(status))
    #
    #     if not status:
    #         self.Server.serverurl = self.Server.serverurl.replace("https://", "http://")
    #         self.Logger.info("{}".format(self.Server.serverurl))
    #
    #     self.Logger.info("Controlling server hashes")
    #     GLib.idle_add(self.splashlabel.set_markup, "<b>{}</b>".format(_("Controlling server hashes")))
    #     self.Server.get_hashes(self.Server.serverurl + self.Server.serverhash)

    def ServerHashesCB(self, status, response=None):
        self.Logger.info("ServerHashesCB : {}".format(status))

        def compare_md5_re_download(local_file, server_md5):
            if not Path(local_file).exists():
                return True
            local_md5 = md5(open(local_file, "rb").read()).hexdigest()
            return local_md5 != server_md5

        if status:
            # download_apps = compare_md5_re_download(self.UserSettings.apps_dir + self.UserSettings.apps_archive, response["md5"]["apps"])
            download_apps = True
            # download_home = compare_md5_re_download(self.UserSettings.home_dir + self.UserSettings.home_archive, response["md5"]["home"])
            download_home = True

            download_icons = compare_md5_re_download(self.UserSettings.icons_dir + self.UserSettings.icons_archive, response["md5"]["icons"])
            download_images = compare_md5_re_download(self.UserSettings.images_dir + self.UserSettings.images_archive, response["md5"]["images"])
            download_cats = compare_md5_re_download(self.UserSettings.cats_dir + self.UserSettings.cats_archive, response["md5"]["cats"])

            self.Logger.info("download_apps: {}".format(download_apps))
            self.Logger.info("download_icons: {}".format(download_icons))
            self.Logger.info("download_images: {}".format(download_images))
            self.Logger.info("download_cats: {}".format(download_cats))
            self.Logger.info("download_home: {}".format(download_home))

            self.status_server_apps = not download_apps
            self.status_server_icons = not download_icons
            self.status_server_images = not download_images
            self.status_server_cats = not download_cats
            self.status_server_home = not download_home

            if download_apps or download_icons or download_images or download_cats or download_home:

                self.Logger.info("Getting application metadata from server")
                GLib.idle_add(self.splashlabel.set_markup,
                              "<b>{}</b>".format(_("Getting application metadata from server")))

                if download_apps:
                    self.Logger.info("Getting applications from server")
                    # GLib.idle_add(self.splashlabel.set_markup,
                    #               "<b>{}</b>".format(_("Getting applications from server")))

                    # self.Server.get_file(url=self.Server.serverurl + "/files/" + self.Server.server_apps_archive,
                    #                      download_location=self.UserSettings.apps_dir + self.UserSettings.apps_archive,
                    #                      server_md5=response["md5"]["apps"], type="apps")
                    self.Server.get_file(url=self.Server.serverurl + self.Server.serverapps,
                                         download_location=self.UserSettings.apps_dir + self.UserSettings.apps_archive,
                                         type="apps", save_file=False)
                if download_icons:
                    self.Logger.info("Getting icons from server")
                    # GLib.idle_add(self.splashlabel.set_markup,
                    #               "<b>{}</b>".format(_("Getting icons from server")))

                    self.Server.get_file(url=self.Server.serverurl + "/files/" + self.Server.server_icons_archive,
                                         download_location=self.UserSettings.icons_dir + self.UserSettings.icons_archive,
                                         server_md5=response["md5"]["icons"], type="icons")

                if download_images:
                    self.Logger.info("Getting images from server")
                    # GLib.idle_add(self.splashlabel.set_markup,
                    #               "<b>{}</b>".format(_("Getting icons from server")))

                    self.Server.get_file(url=self.Server.serverurl + "/files/" + self.Server.server_images_archive,
                                         download_location=self.UserSettings.images_dir + self.UserSettings.images_archive,
                                         server_md5=response["md5"]["images"], type="images")

                if download_cats:
                    self.Logger.info("Getting categories from server")
                    # GLib.idle_add(self.splashlabel.set_markup,
                    #               "<b>{}</b>".format(_("Getting categories from server")))

                    self.Server.get_file(url=self.Server.serverurl + "/files/" + self.Server.server_cats_archive,
                                         download_location=self.UserSettings.cats_dir + self.UserSettings.cats_archive,
                                         server_md5=response["md5"]["cats"], type="cats")
                if download_home:
                    self.Logger.info("Getting homepage from server")
                    # GLib.idle_add(self.splashlabel.set_markup,
                    #               "<b>{}</b>".format(_("Getting homepage from server")))
                    # self.Server.get_file(url=self.Server.serverurl + "/files/" + self.Server.server_home_archive,
                    #                      download_location=self.UserSettings.home_dir + self.UserSettings.home_archive,
                    #                      server_md5=response["md5"]["home"], type="home")
                    self.Server.get_file(url=self.Server.serverurl + self.Server.serverhomepage,
                                         download_location=self.UserSettings.home_dir + self.UserSettings.home_archive,
                                         type="home", save_file=False)

            else:
                self.ServerFilesCB(True, "ok")
        else:
            if not self.connection_error_after:
                self.Server.connection = False
                GLib.idle_add(self.afterServers)
                self.connection_error_after = True

    def ServerFilesCB(self, status, type="", response=None):
        self.Logger.info("ServerFilesCB {} : {}".format(type, status))

        if status:
            if type == "apps":
                self.status_server_apps = True
                self.apps = dict(sorted(response.items(),
                                        key=lambda item: locale.strxfrm(item[1]["prettyname"][self.user_locale])))
                self.apps_full = self.apps.copy()
            elif type == "icons":
                self.status_server_icons = True
            elif type == "images":
                self.status_server_images = True
            elif type == "cats":
                self.status_server_cats = True
            elif type == "home":
                self.status_server_home = True
                self.Server.ediapplist = response.get("editor-apps", [])
                self.Server.sliderapplist = response.get("slider-apps", [])
                self.Server.mostdownapplist = response.get("mostdown-apps", [])
                self.Server.trendapplist = response.get("trend-apps", [])
                self.Server.lastaddedapplist = response.get("last-apps", [])
                self.Server.appversion_pardus25 = response.get("version_pardus25")
                self.Server.blocked_gnome_reviews = response.get("blocked_gnome_reviews", [])
                if response.get("important-packages"):
                    self.important_packages = response.get("important-packages")
                if response.get("i386-packages"):
                    self.i386_packages = response.get("i386-packages")
                self.Server.aptuptime = response.get("aptuptime", 86400)

            if self.status_server_apps and self.status_server_icons and self.status_server_images and self.status_server_cats and self.status_server_home:
                # with open(self.UserSettings.apps_dir + self.UserSettings.apps_file, 'r', encoding='utf-8') as f:
                #     response = json.load(f)
                #     self.applist = dict(sorted(response.items(),
                #                                key=lambda item: locale.strxfrm(item[1]["prettyname"][self.user_locale])))

                with open(self.UserSettings.cats_dir + self.UserSettings.cats_file, 'r', encoding='utf-8') as f:
                    response = json.load(f)
                    self.cats = response.get("cat-list", [])

                # with open(self.UserSettings.home_dir + self.UserSettings.home_file, 'r', encoding='utf-8') as f:
                #     response = json.load(f)
                #     self.Server.ediapplist = response["editor-apps"]
                #     self.Server.sliderapplist = response["slider-apps"]
                #     self.Server.mostdownapplist = response["mostdown-apps"]
                #     self.Server.trendapplist = response["trend-apps"]
                #     self.Server.lastaddedapplist = response["last-apps"]
                #     # self.Server.totalstatistics = response["total"]
                #     # self.Server.servermd5 = response["md5"]
                #     self.Server.appversion = response["version"]
                #     if "version_pardus21" in response.keys():
                #         self.Server.appversion_pardus21 = response["version_pardus21"]
                #     else:
                #         self.Server.appversion_pardus21 = self.Server.appversion
                #     if "version_pardus23" in response.keys():
                #         self.Server.appversion_pardus23 = response["version_pardus23"]
                #     else:
                #         self.Server.appversion_pardus23 = self.Server.appversion
                #     # self.Server.iconnames = response["iconnames"]
                #     self.Server.badwords = response["badwords"]
                #     if "important-packages" in response and response["important-packages"]:
                #         self.important_packages = response["important-packages"]
                #     if "i386-packages" in response and response["i386-packages"]:
                #         self.i386_packages = response["i386-packages"]
                #     self.Server.aptuptime = response["aptuptime"]

                self.prepend_server_icons()

                self.Logger.info("Preparing the application interface")
                GLib.idle_add(self.splashlabel.set_markup,
                              "<b>{}</b>".format(_("Preparing the application interface")))

                self.Server.connection = True
                GLib.idle_add(self.afterServers)
        else:
            if not self.connection_error_after:
                self.Server.connection = False
                GLib.idle_add(self.afterServers)
                self.connection_error_after = True

    # def controlServer(self):
    #     if self.Server.connection:
    #         self.Logger.info("Controlling {}".format(self.Server.serverurl))
    #         self.AppDetail.control(self.Server.serverurl + "/api/v2/test")
    #         self.AppRequest.control(self.Server.serverurl + "/api/v2/test")
    #         self.PardusComment.control(self.Server.serverurl + "/api/v2/test")

    def set_slider(self):

        stack_counter = 0
        for slider_app in self.Server.sliderapplist:

            slider_app_name = slider_app["name"]
            slider_app_pretty_name = slider_app["prettyname"].get(self.user_locale) or slider_app["prettyname"].get("en")
            slider_app_slogan = slider_app["slogan"].get(self.user_locale) or slider_app["slogan"].get("en")
            slider_app_short_desc = slider_app["shortdesc"].get(self.user_locale) or slider_app["shortdesc"].get("en")

            label_name = Gtk.Label.new()
            label_name.props.halign = Gtk.Align.START
            label_name.set_markup("<b>{}</b>".format(slider_app_pretty_name))

            label_slogan = Gtk.Label.new()
            label_slogan.props.halign = Gtk.Align.START
            label_slogan.set_line_wrap(True)
            label_slogan.set_max_width_chars(35)
            label_slogan.set_lines(4)
            label_slogan.set_ellipsize(Pango.EllipsizeMode.END)
            label_slogan.set_markup("<span size='x-large'>{}</span>".format(slider_app_slogan))

            label_summary = Gtk.Label.new()
            label_summary.props.halign = Gtk.Align.START
            label_summary.set_markup("<span weight='light'>{}</span>".format(slider_app_short_desc))

            vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 12)
            vbox.set_border_width(6)
            vbox.pack_start(label_name, False, False, 0)
            vbox.pack_start(label_slogan, False, False, 0)
            vbox.pack_start(label_summary, False, False, 0)
            vbox.set_margin_top(24)
            vbox.set_margin_start(24)

            hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
            hbox.pack_start(vbox, True, True, 0)
            hbox.show_all()

            css = """
            .pardus-software-slider {{
                background-image: url("{}");
                background-size: cover;
                background-repeat: no-repeat;
                background-position: right;
                border-radius: 8px;
            }}
            """.format(os.path.join(self.UserSettings.slider_images_dir, "{}.svg".format(slider_app_name)))

            style_provider = Gtk.CssProvider()
            style_provider.load_from_data(str.encode(css))

            flowbox = Gtk.FlowBox()
            flowbox.set_min_children_per_line(1)
            flowbox.set_max_children_per_line(1)
            flowbox.set_row_spacing(0)
            flowbox.set_column_spacing(0)
            flowbox.set_homogeneous(True)
            flowbox.connect("child-activated", self.on_slider_app_activated)

            flowbox_child = Gtk.FlowBoxChild()
            flowbox_child.name = slider_app_name
            flowbox_child.add(hbox)
            flowbox_child.set_size_request(-1, 200)
            flowbox_child.get_style_context().add_class("pardus-software-slider")
            flowbox_child.get_style_context().add_provider(style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

            flowbox.add(flowbox_child)

            self.ui_slider_stack.add_named(flowbox, "{}".format(stack_counter))
            stack_counter += 1

        # Slider back button
        btn_prev = Gtk.Button()
        btn_prev.set_image(Gtk.Image.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.BUTTON))
        btn_prev.set_valign(Gtk.Align.END)
        btn_prev.set_halign(Gtk.Align.END)
        btn_prev.set_margin_end(50)
        btn_prev.set_margin_bottom(10)
        btn_prev.connect("clicked", self.on_ui_slider_left_button_clicked)
        GLib.idle_add(self.ui_slider_overlay.add_overlay, btn_prev)

        # Slider next button
        btn_next = Gtk.Button()
        btn_next.set_image(Gtk.Image.new_from_icon_name("go-next-symbolic", Gtk.IconSize.BUTTON))
        btn_next.set_valign(Gtk.Align.END)
        btn_next.set_halign(Gtk.Align.END)
        btn_next.set_margin_end(10)
        btn_next.set_margin_bottom(10)
        btn_next.connect("clicked", self.on_ui_slider_right_button_clicked)
        GLib.idle_add(self.ui_slider_overlay.add_overlay, btn_next)

        GLib.idle_add(self.ui_slider_overlay.show_all)
        # GLib.idle_add(self.ui_slider_stack.show_all)

    def on_slider_app_activated(self, flow_box, child):
        print(child.name)
        self.set_app_details_page(child.name)

    def on_ui_slider_left_button_clicked(self, button):

        slider_stack_len = 0
        for row in self.ui_slider_stack:
            slider_stack_len += 1

        def get_prev_page(page):
            increase = 0
            for i in range(0, slider_stack_len):
                increase += -1
                if self.ui_slider_stack.get_child_by_name("{}".format(page + increase)) != None:
                    return page + increase
            return slider_stack_len - 1

        self.ui_slider_stack.set_visible_child_name("{}".format(get_prev_page(self.slider_current_page)))
        self.slider_current_page = int(self.ui_slider_stack.get_visible_child_name())


    def on_ui_slider_right_button_clicked(self, button):

        slider_stack_len = 0
        for row in self.ui_slider_stack:
            slider_stack_len += 1

        def get_next_page(page):
            increase = 0
            for i in range(0, slider_stack_len):
                increase += 1
                if self.ui_slider_stack.get_child_by_name("{}".format(page + increase)) != None:
                    return page + increase
            return 0

        self.ui_slider_stack.set_visible_child_name("{}".format(get_next_page(self.slider_current_page)))
        self.slider_current_page = int(self.ui_slider_stack.get_visible_child_name())

    def get_upgradables(self):
        if not self.Server.connection:
            return
        self.upgradables = {}
        for app, details in self.apps.items():
            is_installed = self.Package.isinstalled(app)
            is_upgradable = self.Package.is_upgradable(app)

            if is_installed and is_upgradable:
                self.upgradables[app] = details

    def set_upgradables(self):
        if not self.Server.connection:
            return
        self.Logger.info("in set_upgradables")

        GLib.idle_add(lambda: (self.ui_upgradableapps_flowbox and self.ui_upgradableapps_flowbox.foreach(
            lambda row: self.ui_upgradableapps_flowbox.remove(row)), False))

        GLib.idle_add(lambda: (self.ui_leftupdates_listbox and self.ui_leftupdates_listbox.foreach(
            lambda child: self.ui_leftupdates_listbox.remove(child)), False))

        GLib.idle_add(self.ui_leftupdates_separator.set_visible, self.upgradables)
        GLib.idle_add(self.ui_upgradableapps_box.set_visible, self.upgradables)

        if self.Server.connection and self.upgradables:
            updates_icon = Gtk.Image.new_from_icon_name("ps-cat-updates-symbolic", Gtk.IconSize.BUTTON)
            updates_icon.props.halign = Gtk.Align.START

            label = Gtk.Label.new()
            label.set_markup("<b>{}</b>".format(_("Updates")))
            box_updates_count = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
            label_updates_count = Gtk.Label.new()
            label_updates_count.set_markup("{}".format(len(self.upgradables)))
            label_updates_count.set_margin_start(5)
            label_updates_count.set_margin_end(5)
            label_updates_count.set_margin_top(3)
            label_updates_count.set_margin_bottom(3)
            box_updates_count.pack_start(label_updates_count, False, True, 0)
            box_updates_count.props.halign = Gtk.Align.END
            box_updates_count.get_style_context().add_class("pardus-software-left-updates-count-box")

            label_updates = Gtk.Label.new()
            label_updates.set_markup("<small>{}</small>".format(_("Some applications are outdated.")))
            label_updates.set_max_width_chars(23)
            label_updates.set_ellipsize(Pango.EllipsizeMode.END)
            label_updates.props.halign = Gtk.Align.START
            label_updates.set_margin_start(3)
            label_updates.set_opacity(0.7)

            box_h = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 12)
            box_h.pack_start(updates_icon, False, True, 0)
            box_h.pack_start(label, False, True, 0)
            box_h.pack_end(box_updates_count, True, True, 0)

            box_v = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
            box_v.pack_start(box_h, False, True, 0)
            box_v.pack_start(label_updates, False, True, 0)
            box_v.set_margin_start(8)
            box_v.set_margin_end(12)
            box_v.set_margin_top(5)
            box_v.set_margin_bottom(5)
            box_v.set_spacing(8)

            row = Gtk.ListBoxRow()
            row.add(box_v)
            row.name = "updates"
            row.props.valign = Gtk.Align.END
            row.set_vexpand(True)

            GLib.idle_add(self.ui_leftupdates_listbox.add, row)

            for app, details in self.upgradables.items():
                listbox = self.create_upgradable_myapp_widget(app, details)
                GLib.idle_add(self.ui_upgradableapps_flowbox.insert, listbox, -1)

            self.ui_upgradableapps_count_label.set_markup("<span size='large'><b>({})</b></span>".format(len(self.upgradables)))

            GLib.idle_add(self.ui_upgradableapps_flowbox.show_all)
            GLib.idle_add(self.ui_leftupdates_listbox.show_all)

        self.Logger.info("set_upgradables done")

    def set_applications(self):
        self.Logger.info("in set_applications")
        GLib.idle_add(lambda: (self.ui_pardusapps_flowbox and self.ui_pardusapps_flowbox.foreach(
            lambda row: self.ui_pardusapps_flowbox.remove(row)), False))

        if self.Server.connection:
            for app, details in self.apps.items():

                listbox = self.create_app_widget(app, details)
                GLib.idle_add(self.ui_pardusapps_flowbox.insert, listbox, -1)

            GLib.idle_add(self.ui_pardusapps_flowbox.show_all)

        self.Logger.info("set_applications done")

    # def on_pardus_apps_listbox_released(self, widget, event, listbox):
    #     print("on_pardus_apps_listbox_released")
    #     print(listbox.name)

    # def on_ui_pardusapps_flowbox_child_activated(self, flowbox, child):
    #     print(f"Left clicked: {child.get_children()[0].get_children()[0].name}")
    #     GLib.idle_add(flowbox.unselect_all)
    #     self.set_app_details_page(child.get_children()[0].get_children()[0].name)

    def set_categories(self):
        GLib.idle_add(lambda: (self.ui_leftcats_listbox and self.ui_leftcats_listbox.foreach(
            lambda child: self.ui_leftcats_listbox.remove(child)), False))

        if self.Server.connection:
            self.categories = []
            for cat in self.cats:
                self.categories.append({"name": cat[self.user_locale], "icon": cat["en"]})

            self.categories = sorted(self.categories, key=lambda x: x["name"])

            if self.user_locale == "tr":
                self.categories.insert(0, {"name": "tümü", "icon": "all"})
            else:
                self.categories.insert(0, {"name": "all", "icon": "all"})

            # discover
            icon = Gtk.Image.new_from_icon_name("ps-cat-discover-symbolic",  Gtk.IconSize.BUTTON)
            label = Gtk.Label.new()
            label.set_markup("<b>{}</b>".format(_("Discover")))
            box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 12)
            box.pack_start(icon, False, True, 0)
            box.pack_start(label, False, True, 0)
            box.set_margin_start(8)
            box.set_margin_end(30)
            box.set_margin_top(8)
            box.set_margin_bottom(8)
            row = Gtk.ListBoxRow()
            row.add(box)
            row.name = "discover"
            GLib.idle_add(self.ui_leftcats_listbox.add, row)

            # categories
            for cat in self.categories:

                cat["icon"] = "ps-cat-{}-symbolic".format(cat["icon"])
                cat_icon = Gtk.Image.new_from_icon_name(cat["icon"],  Gtk.IconSize.BUTTON)

                label = Gtk.Label.new()
                label.set_markup("<b>{}</b>".format(cat["name"].title()))

                box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 12)
                box.pack_start(cat_icon, False, True, 0)
                box.pack_start(label, False, True, 0)
                box.set_margin_start(8)
                box.set_margin_end(30)
                box.set_margin_top(8)
                box.set_margin_bottom(8)

                row = Gtk.ListBoxRow()
                row.add(box)
                row.name = cat["name"]

                GLib.idle_add(self.ui_leftcats_listbox.add, row)

            # installed
            installed_icon = Gtk.Image.new_from_icon_name("ps-cat-installed-symbolic",  Gtk.IconSize.BUTTON)

            label = Gtk.Label.new()
            label.set_markup("<b>{}</b>".format(_("Installed Apps")))
            label.set_ellipsize(Pango.EllipsizeMode.END)

            box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 12)
            box.pack_start(installed_icon, False, True, 0)
            box.pack_start(label, False, True, 0)
            box.set_margin_start(8)
            box.set_margin_end(30)
            box.set_margin_top(8)
            box.set_margin_bottom(8)

            row = Gtk.ListBoxRow()
            row.add(box)
            row.name = "installed"
            GLib.idle_add(self.ui_leftinstalled_listbox.add, row)

            # show widgets
            GLib.idle_add(self.ui_leftcats_listbox.show_all)
            GLib.idle_add(self.ui_leftinstalled_listbox.show_all)

            # default select discover
            GLib.idle_add(lambda: self.ui_leftcats_listbox.select_row(self.ui_leftcats_listbox.get_row_at_index(0)))

    def on_ui_leftcats_listbox_row_activated(self, listbox, row):
        self.searching = False
        self.ui_leftupdates_listbox.unselect_all()
        self.ui_leftinstalled_listbox.unselect_all()
        print(row.name)
        self.current_category = row.name
        if self.current_category == "discover":
            print("in discover")
            self.ui_right_stack_navigate_to("discover")
        # elif self.current_category == "installed":
        #     print("in installed")
        #     self.ui_right_stack_navigate_to("installed")
        else:
            print("in category")
            self.ui_pardusapps_flowbox.invalidate_filter()
            self.ui_right_stack_navigate_to("apps")
            self.ui_pardusapps_title_stack.set_visible_child_name("apps")
            self.ui_repotitle_box.set_visible(False)
            self.ui_repoapps_flowbox.set_visible(False)

            self.ui_currentcat_label.set_markup("<span size='x-large'><b>{}</b></span>".format(self.current_category.title()))
            icon = next((cat["icon"] for cat in self.categories if cat["name"] == self.current_category), "image-missing-symbolic")
            self.ui_currentcat_image.set_from_icon_name(icon, Gtk.IconSize.DIALOG)
            self.ui_currentcat_image.set_pixel_size(55)

    def on_ui_leftupdates_listbox_row_activated(self, listbox, row):
        self.searching = False
        # self.ui_installedapps_box.set_visible(False)
        # self.ui_installedapps_flowbox.set_visible(False)
        # self.ui_upgradableapps_box.set_visible(True)
        # self.ui_upgradableapps_flowbox.set_visible(True)
        self.ui_leftcats_listbox.unselect_all()
        self.ui_leftinstalled_listbox.unselect_all()
        print("in updates")
        self.ui_right_stack_navigate_to("installed")
        self.ui_installedapps_flowbox.invalidate_filter()

    def on_ui_leftinstalled_listbox_row_activated(self, listbox, row):
        self.searching = False
        # self.ui_installedapps_box.set_visible(True)
        # self.ui_installedapps_flowbox.set_visible(True)
        # self.ui_upgradableapps_box.set_visible(False)
        # self.ui_upgradableapps_flowbox.set_visible(False)
        self.ui_leftcats_listbox.unselect_all()
        self.ui_leftupdates_listbox.unselect_all()
        print("in installed")
        self.ui_right_stack_navigate_to("installed")
        self.ui_installedapps_flowbox.invalidate_filter()

    def on_queue_cancel_button_clicked(self, button):
        for fbc in self.ui_queue_flowbox.get_children():
            lb = fbc.get_child()
            if lb.get_children():
                lbr = lb.get_children()[0]
                if lbr.name == button.name:
                    children = self.ui_queue_flowbox.get_children()
                    index = children.index(fbc)
                    if index != 0:
                        self.ui_queue_flowbox.remove(fbc)
                        q_index = next((i for i, app in enumerate(self.queue)
                                        if app["name"] == button.name), None)
                        if q_index is not None:
                            self.queue.pop(q_index)
                            # update widget actions
                            self.Logger.info(f"{button.name} removed from queue, updating widget actions")
                            self.update_app_widget_label(app_name=button.name, from_queue_cancelled=True)
                    else:
                        self.Logger.info("Cancelling {} {}".format(self.inprogress_app_name, self.pid))
                        command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py",
                                   "kill", "{}".format(self.pid)]
                        self.start_kill_process(command)
                    break

    def app_widget_action_clicked(self, button):

        app = button.get_parent().get_parent().get_parent().name

        self.Logger.info(f"app_widget_action_clicked: {app}")

        if isinstance(app, dict):
            app_name, details = next(iter(app.items()))
        elif isinstance(app, str):
            app_name = app
            details = self.apps_full.get(app_name, {})
        else:
            self.Logger.warning("{} {}".format("app_widget_action_clicked func ERROR for: ", app))
            return

        if not details:
            self.Logger.warning("{} details not found on app_widget_action_clicked.".format(app_name))
            return

        if button.name == 3:
            print("{} opening".format(app_name))
            desktop = details.get("desktop")
            desk_id = details.get("id")
            extras = details.get("desktopextras", "")
            if desktop:
                if self.launch_desktop_file(desktop):
                    return
            if extras:
                for extra in extras.split(","):
                    if self.launch_desktop_file(extra):
                        break
            if desk_id:
                if self.launch_desktop_file(desk_id):
                    return
            return

        if button.name == 9:
            print("{} opening details page".format(app_name))
            repo_app = details.get("repo_app", "")
            self.set_app_details_page(app, source=1 if not repo_app else 2)
            return

        print("app_name: {}".format(app_name))
        print("details: {}".format(details))

        self.update_app_widget_label(app_name)

        command = app_name
        cmd = details.get("command", [])
        if isinstance(cmd, dict):
            command = cmd.get(self.user_locale, "").strip()
            packages = [p for p in command.split() if self.Package.controlPackageCache(p)]
            command = " ".join(packages) if packages else app_name

        desktop_id = details.get("desktop", "")

        self.ui_header_queue_button.set_visible(True)

        self.ui_queue_stack.set_visible_child_name("inprogress")

        self.queue.append({"name": app_name, "command": command, "desktop_id": desktop_id, "upgrade": button.name == 2})
        self.add_to_queue_ui(app_name, button.name == 2, details.get("icon_name"))
        if not self.inprogress:
            self.action_package(app_name, command, desktop_id, button.name == 2)
            self.Logger.info("action_package app: {}, command: {}, desktop_id: {}, upgrade: {}".format(
                app_name, command, desktop_id, button.name == 2))

    def on_ui_ad_action_button_clicked(self, button):
        if self.ui_app_name in self.apps_full.keys():
            name = self.ui_app_name
        else:
            name = self.ui_myapp_name_dic
        button.get_parent().get_parent().get_parent().name = name
        self.app_widget_action_clicked(button)

    def on_ui_ad_remove_button_clicked(self, button):
        if self.ui_app_name in self.apps_full.keys():
            name = self.ui_app_name
        else:
            name = self.ui_myapp_name_dic
        button.get_parent().get_parent().get_parent().name = name
        self.app_widget_action_clicked(button)

    def on_ui_ad_disclaimer_button_clicked(self, button):
        self.ui_disclaimer_popover.popup()

    def launch_desktop_file(self, desktop):
        try:
            subprocess.check_call(["gtk-launch", desktop])
            return True
        except subprocess.CalledProcessError as e:
            self.Logger.warning("error opening {}".format(desktop))
            self.Logger.exception("{}".format(e))
            return False

    def add_to_queue_ui(self, app_name, upgrade=False, icon_name=None):
        listbox = self.create_queue_widget(app_name, upgrade, icon_name)
        GLib.idle_add(self.ui_queue_flowbox.insert, listbox, -1)
        GLib.idle_add(self.ui_queue_flowbox.show_all)

    def action_package(self, app_name, command, desktop_id="", upgrade=False):
        self.inprogress = True

        self.inprogress_app_name = app_name
        self.inprogress_command = command
        self.inprogress_desktop = desktop_id

        self.isinstalled = self.Package.isinstalled(app_name)
        self.isupgrade = self.Package.is_upgradable(app_name) and upgrade

        if self.isinstalled is True:
            if self.isupgrade:
                command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py", "upgrade",
                           self.inprogress_command]
            else:
                command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py", "remove",
                           self.inprogress_command]
        elif self.isinstalled is False:
            command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py", "install",
                       self.inprogress_command]
            packagelist = self.inprogress_command.split(" ")
            if [i for i in self.i386_packages if i in packagelist]:
                command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py",
                           "enablei386andinstall", self.inprogress_command]
        else:
            self.Logger.info("actionPackage func error")

        self.pid = self.action_process(command)
        self.Logger.info("started pid : {}".format(self.pid))

    def update_app_widget_label(self, app_name, from_queue_cancelled=False):
        self.Logger.info("inprogress_app_name: {}, app_name: {}".format(self.inprogress_app_name, app_name))
        def to_spinner(action_button):
            action_button.remove(action_button.get_children()[0])
            action_button.set_sensitive(False)
            spinner = Gtk.Spinner()
            action_button.add(spinner)
            spinner.start()
            spinner.show_all()

        def to_normal(action_button):
            action_button.remove(action_button.get_children()[0])
            action_button_label = Gtk.Label.new()
            action_button_label.set_line_wrap(False)
            action_button_label.set_justify(Gtk.Justification.LEFT)
            action_button_label.set_max_width_chars(6)
            action_button_label.set_ellipsize(Pango.EllipsizeMode.END)
            is_installed = self.Package.isinstalled(app_name)
            is_upgradable = self.Package.is_upgradable(app_name)
            is_openable = self.get_desktop_filename_from_app_name(app_name) != ""
            if is_installed is not None:
                action_button.add(action_button_label)
                if is_installed:
                    if is_upgradable:
                        self.set_button_class(action_button, 3)
                        action_button_label.set_markup("<small>{}</small>".format(_("Update")))
                        action_button.name = 2
                    else:
                        if is_openable:
                            self.set_button_class(action_button, 4)
                            action_button_label.set_markup("<small>{}</small>".format(_("Open")))
                            action_button.name = 3
                        else:
                            # self.set_button_class(action_button, 1)
                            # action_button_label.set_markup("<small>{}</small>".format(_("Uninstall")))
                            # action_button.name = 0
                            self.set_button_class(action_button, 4)
                            action_button_label.set_markup("<small>{}</small>".format(_("Open")))
                            action_button.name = 9
                else:
                    self.set_button_class(action_button, 0)
                    action_button_label.set_markup("<small>{}</small>".format(_("Install")))
                    action_button.name = 1
            else:
                self.set_button_class(action_button, 2)
                not_found_image = Gtk.Image.new_from_icon_name("action-unavailable-symbolic", Gtk.IconSize.BUTTON)
                action_button.add(not_found_image)
            action_button.show_all()

        for fbc in self.ui_pardusapps_flowbox:
            if next(iter(fbc.get_children()[0].get_children()[0].name)) == app_name:
                action_button = fbc.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[2]
                if (self.inprogress_app_name != app_name) != from_queue_cancelled:
                    to_spinner(action_button)
                else:
                    to_normal(action_button)

        for fbc in self.ui_repoapps_flowbox:
            if next(iter(fbc.get_children()[0].get_children()[0].name)) == app_name:
                action_button = fbc.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[2]
                if (self.inprogress_app_name != app_name) != from_queue_cancelled:
                    to_spinner(action_button)
                else:
                    to_normal(action_button)

        for fbc in self.ui_trend_flowbox:
            if fbc.get_children()[0].get_children()[0].name == app_name:
                action_button = fbc.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3]
                if (self.inprogress_app_name != app_name) != from_queue_cancelled:
                    to_spinner(action_button)
                else:
                    to_normal(action_button)

        for fbc in self.ui_mostdown_flowbox:
            if fbc.get_children()[0].get_children()[0].name == app_name:
                action_button = fbc.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[2]
                if (self.inprogress_app_name != app_name) != from_queue_cancelled:
                    to_spinner(action_button)
                else:
                    to_normal(action_button)

        for fbc in self.ui_recent_flowbox:
            if fbc.get_children()[0].get_children()[0].name == app_name:
                action_button = fbc.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[2]
                if (self.inprogress_app_name != app_name) != from_queue_cancelled:
                    to_spinner(action_button)
                else:
                    to_normal(action_button)

        for fbc in self.ui_trendapps_flowbox:
            if fbc.get_children()[0].get_children()[0].name == app_name:
                action_button = fbc.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3]
                if (self.inprogress_app_name != app_name) != from_queue_cancelled:
                    to_spinner(action_button)
                else:
                    to_normal(action_button)

        for fbc in self.ui_mostdownapps_flowbox:
            if fbc.get_children()[0].get_children()[0].name == app_name:
                action_button = fbc.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[2]
                if (self.inprogress_app_name != app_name) != from_queue_cancelled:
                    to_spinner(action_button)
                else:
                    to_normal(action_button)

        for fbc in self.ui_recentapps_flowbox:
            if fbc.get_children()[0].get_children()[0].name == app_name:
                action_button = fbc.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[2]
                if (self.inprogress_app_name != app_name) != from_queue_cancelled:
                    to_spinner(action_button)
                else:
                    to_normal(action_button)

        for fbc in self.ui_editor_flowbox:
            if fbc.get_children()[0].get_children()[0].name == app_name:
                action_button = fbc.get_children()[0].get_children()[0].get_children()[0].get_children()[1].get_children()[2]
                if (self.inprogress_app_name != app_name) != from_queue_cancelled:
                    to_spinner(action_button)
                else:
                    to_normal(action_button)

        for fbc in self.ui_upgradableapps_flowbox:
            if next(iter(fbc.get_children()[0].get_children()[0].name)) == app_name:
                action_button = fbc.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3]
                remove_button = fbc.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[4]
                if (self.inprogress_app_name != app_name) != from_queue_cancelled:
                    to_spinner(action_button)
                    remove_button.set_sensitive(False)
                else:
                    to_normal(action_button)
                    remove_button.set_sensitive(True)

        if self.ui_right_stack.get_visible_child_name() == "appdetails":
            if (self.inprogress_app_name != app_name) != from_queue_cancelled:
                to_spinner(self.ui_ad_action_button)
                self.ui_ad_remove_button.set_sensitive(False)
            else:
                to_normal(self.ui_ad_action_button)
                self.ui_ad_remove_button.set_sensitive(True)
                self.ui_ad_remove_button.set_visible(self.Package.isinstalled(app_name))

    def create_app_widget(self, app, details=None, number=0, repo_app=False):

        if repo_app:
            details = {"name": app, "icon_name": "ps-repo-package-symbolic",
                       "description": self.Package.adv_description(app), "repo_app": True}

        app_icon = Gtk.Image.new_from_icon_name(app if not repo_app else "ps-repo-package-symbolic", Gtk.IconSize.DND)
        app_icon.set_pixel_size(32)
        app_icon.get_style_context().add_class("pardus-software-mostapp-icon")
        app_icon.props.halign = Gtk.Align.CENTER
        app_icon.props.valign = Gtk.Align.CENTER

        prettyname = "{}".format(self.get_pretty_name_from_app_name(app) if not repo_app else app)

        app_name = Gtk.Label.new()
        app_name.set_markup("<b>{}</b>".format(prettyname))
        app_name.set_line_wrap(False)
        app_name.set_justify(Gtk.Justification.LEFT)
        app_name.set_max_width_chars(23 if number==0 else 21)
        app_name.set_ellipsize(Pango.EllipsizeMode.END)
        app_name.props.halign = Gtk.Align.START

        action_button = Gtk.Button.new()
        action_button.connect("clicked", self.app_widget_action_clicked)
        action_button.props.halign = Gtk.Align.END
        action_button.props.valign = Gtk.Align.CENTER
        action_button.set_hexpand(True)
        action_button.set_size_request(77, -1)

        action_button_label = Gtk.Label.new()
        action_button_label.set_line_wrap(False)
        action_button_label.set_justify(Gtk.Justification.LEFT)
        action_button_label.set_max_width_chars(6)
        action_button_label.set_ellipsize(Pango.EllipsizeMode.END)

        is_installed = self.Package.isinstalled(app)
        is_upgradable = self.Package.is_upgradable(app)
        is_openable = self.get_desktop_filename_from_app_name(app) != ""
        if is_installed is not None:
            action_button.add(action_button_label)
            if is_installed:
                if is_upgradable:
                    self.set_button_class(action_button, 3)
                    action_button_label.set_markup("<small>{}</small>".format(_("Update")))
                    action_button.name = 2
                else:
                    if is_openable:
                        self.set_button_class(action_button, 4)
                        action_button_label.set_markup("<small>{}</small>".format(_("Open")))
                        action_button.name = 3
                    else:
                        self.set_button_class(action_button, 4)
                        action_button_label.set_markup("<small>{}</small>".format(_("Open")))
                        action_button.name = 9
            else:
                self.set_button_class(action_button, 0)
                action_button_label.set_markup("<small>{}</small>".format(_("Install")))
                action_button.name = 1
        else:
            self.set_button_class(action_button, 2)
            not_found_image = Gtk.Image.new_from_icon_name("action-unavailable-symbolic", Gtk.IconSize.BUTTON)
            action_button.add(not_found_image)

        summary_label = Gtk.Label.new()
        summary_label.set_markup("<span weight='light' size='small'>{}</span>".format(GLib.markup_escape_text(
            self.get_sub_category_name_from_app_name(app), -1)))
        summary_label.props.valign = Gtk.Align.START
        summary_label.props.halign = Gtk.Align.START
        summary_label.set_line_wrap(False)
        summary_label.set_max_width_chars(23 if number==0 else 21)
        summary_label.set_ellipsize(Pango.EllipsizeMode.END)
        summary_label.set_margin_start(1)

        box_app = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        box_app.props.valign = Gtk.Align.CENTER
        box_app.pack_start(app_name, False, True, 0)
        box_app.pack_start(summary_label, False, True, 0)
        box_app.set_margin_end(8)

        box_h = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 16)
        if number != 0:
            number_label = Gtk.Label.new()
            number_label.set_markup("{}".format(number))
            number_label.props.halign = Gtk.Align.CENTER
            number_label.props.valign = Gtk.Align.CENTER
            box_h.pack_start(number_label, False, True, 0)
        box_h.pack_start(app_icon, False, True, 0)
        box_h.pack_start(box_app, False, True, 0)
        box_h.pack_start(action_button, False, True, 0)
        box_h.set_margin_start(8)
        box_h.set_margin_end(8)
        box_h.set_margin_top(8)
        box_h.set_margin_bottom(5)

        bottom_separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
        bottom_separator.props.valign = Gtk.Align.END
        bottom_separator.set_vexpand(True)
        if 1024 < self.display_width <= 1370:
            bottom_separator.set_size_request(333, -1)
        GLib.idle_add(bottom_separator.get_style_context().add_class, "pardus-software-mostdown-bottom-seperator")

        box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 7)
        box.pack_start(box_h, False, True, 0)
        box.pack_end(bottom_separator, True, True, 0)

        listbox = Gtk.ListBox.new()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        listbox.connect("row-activated", self.on_app_listbox_row_activated if not repo_app else self.on_repoapp_listbox_row_activated)
        listbox_row = Gtk.ListBoxRow()
        GLib.idle_add(listbox_row.add, box)
        listbox_row.name = {app: details} if details else app
        GLib.idle_add(listbox.add, listbox_row)

        GLib.idle_add(listbox.get_style_context().add_class, "pardus-software-listbox-mostdown")
        return listbox

    def create_myapp_widget(self, app, du=False):

        app_name = Gtk.Label.new()
        app_name.set_markup("<b>{}</b>".format(GLib.markup_escape_text(app["name"], -1)))
        app_name.props.halign = Gtk.Align.START
        app_name.set_line_wrap(False)
        app_name.set_justify(Gtk.Justification.LEFT)
        app_name.set_max_width_chars(23)
        app_name.set_ellipsize(Pango.EllipsizeMode.END)
        app_name.props.halign = Gtk.Align.START

        try:
            if os.path.isfile(app["icon_name"]):
                px = GdkPixbuf.Pixbuf.new_from_file_at_size(app["icon_name"], 32, 32)
                app_icon = Gtk.Image.new()
                app_icon.set_from_pixbuf(px)
            else:
                app_icon = Gtk.Image.new_from_icon_name(app["icon_name"], Gtk.IconSize.DND)
        except Exception as e:
            app_icon = Gtk.Image.new_from_icon_name("image-missing-symbolic", Gtk.IconSize.DND)
            print("Exception on create_myapp_widget: {}, app: {}".format(e, app))
        app_icon.set_pixel_size(32)
        app_icon.get_style_context().add_class("pardus-software-mostapp-icon")
        app_icon.props.halign = Gtk.Align.CENTER
        app_icon.props.valign = Gtk.Align.CENTER

        action_button = Gtk.Button.new()
        action_button.connect("clicked", self.open_from_myapps)
        action_button.props.valign = Gtk.Align.CENTER
        action_button.set_size_request(77, -1)
        action_button_label = Gtk.Label.new()
        action_button_label.set_line_wrap(False)
        action_button_label.set_justify(Gtk.Justification.LEFT)
        action_button_label.set_max_width_chars(6)
        action_button_label.set_ellipsize(Pango.EllipsizeMode.END)
        action_button.add(action_button_label)
        self.set_button_class(action_button, 4)
        action_button_label.set_markup("<small>{}</small>".format(_("Open")))
        action_button.name = app["id"]

        uninstallbutton = Gtk.Button.new()
        uninstallbutton.name = app
        uninstallbutton.props.valign = Gtk.Align.CENTER
        uninstallbutton.props.always_show_image = True
        uninstallbutton.set_image(Gtk.Image.new_from_icon_name("user-trash-symbolic", Gtk.IconSize.BUTTON))
        uninstallbutton.set_label("")
        uninstallbutton.set_tooltip_text(_("Uninstall"))
        uninstallbutton.set_relief(Gtk.ReliefStyle.NONE)
        uninstallbutton.connect("clicked", self.remove_from_myapps_popup)

        summary_label = Gtk.Label.new()
        summary_label.set_markup("<span weight='light' size='small'>{}</span>".format(
            GLib.markup_escape_text(app["description"], -1)))
        summary_label.props.valign = Gtk.Align.START
        summary_label.props.halign = Gtk.Align.START
        summary_label.set_line_wrap(False)
        summary_label.set_max_width_chars(33)
        summary_label.set_ellipsize(Pango.EllipsizeMode.END)

        box_app = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        box_app.props.valign = Gtk.Align.CENTER
        box_app.pack_start(app_name, False, True, 0)
        box_app.pack_start(summary_label, False, True, 0)
        # box_app.set_hexpand(True)

        du_static = Gtk.Label.new()
        du_static.set_line_wrap(False)

        du_size = Gtk.Label.new()
        du_size.set_line_wrap(False)

        box_du = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        box_du.props.halign = Gtk.Align.START
        box_du.pack_start(du_static, False, True, 0)
        box_du.pack_start(du_size, False, True, 0)
        box_du.set_size_request(77, -1)

        if du:
            du_static.set_markup("<b>{}</b>".format(_("Disk Usage")))
            du_size.set_markup("<span weight='light' size='small'>{}</span>".format(self.Package.beauty_size(app["disk_usage"])))
        else:
            du_static.set_markup("")
            du_size.set_markup("")

        box_h = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 12)
        box_h.pack_start(app_icon, False, True, 0)
        box_h.pack_start(box_app, False, True, 0)
        box_h.pack_end(uninstallbutton, False, True, 0)
        box_h.pack_end(action_button, False, True, 0)
        box_h.pack_end(box_du, False, True, 40 if self.display_width >= 1920 else 20)

        box_h.set_margin_start(8)
        box_h.set_margin_end(8)
        box_h.set_margin_top(8)
        box_h.set_margin_bottom(5)

        bottom_separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
        bottom_separator.props.valign = Gtk.Align.END
        bottom_separator.set_vexpand(True)
        GLib.idle_add(bottom_separator.get_style_context().add_class, "pardus-software-mostdown-bottom-seperator")

        box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 7)
        box.pack_start(box_h, False, True, 0)
        box.pack_end(bottom_separator, True, True, 0)

        listbox = Gtk.ListBox.new()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        listbox.connect("row-activated", self.on_myapp_listbox_row_activated)
        listbox_row = Gtk.ListBoxRow()
        GLib.idle_add(listbox_row.add, box)
        listbox_row.name = app
        GLib.idle_add(listbox.add, listbox_row)

        GLib.idle_add(listbox.get_style_context().add_class, "pardus-software-listbox-mostdown")

        return listbox

    def create_upgradable_myapp_widget(self, app, details=None):

        app_name = Gtk.Label.new()
        app_name.set_markup("<b>{}</b>".format(GLib.markup_escape_text("{}".format(self.get_pretty_name_from_app_name(app)), -1)))
        app_name.props.halign = Gtk.Align.START
        app_name.set_line_wrap(False)
        app_name.set_justify(Gtk.Justification.LEFT)
        app_name.set_max_width_chars(23)
        app_name.set_ellipsize(Pango.EllipsizeMode.END)
        app_name.props.halign = Gtk.Align.START

        app_icon = Gtk.Image.new_from_icon_name(app, Gtk.IconSize.DND)
        app_icon.set_pixel_size(32)
        app_icon.get_style_context().add_class("pardus-software-mostapp-icon")
        app_icon.props.halign = Gtk.Align.CENTER
        app_icon.props.valign = Gtk.Align.CENTER

        action_button = Gtk.Button.new()
        action_button.connect("clicked", self.app_widget_action_clicked)
        action_button.props.valign = Gtk.Align.CENTER
        action_button.set_size_request(77, -1)

        action_button_label = Gtk.Label.new()
        action_button_label.set_line_wrap(False)
        action_button_label.set_justify(Gtk.Justification.LEFT)
        action_button_label.set_max_width_chars(6)
        action_button_label.set_ellipsize(Pango.EllipsizeMode.END)

        is_installed = self.Package.isinstalled(app)
        is_upgradable = self.Package.is_upgradable(app)
        is_openable = self.get_desktop_filename_from_app_name(app) != ""
        if is_installed is not None:
            action_button.add(action_button_label)
            if is_installed:
                if is_upgradable:
                    self.set_button_class(action_button, 3)
                    action_button_label.set_markup("<small>{}</small>".format(_("Update")))
                    action_button.name = 2
                else:
                    if is_openable:
                        self.set_button_class(action_button, 4)
                        action_button_label.set_markup("<small>{}</small>".format(_("Open")))
                        action_button.name = 3
                    else:
                        self.set_button_class(action_button, 4)
                        action_button_label.set_markup("<small>{}</small>".format(_("Open")))
                        action_button.name = 9
            else:
                self.set_button_class(action_button, 0)
                action_button_label.set_markup("<small>{}</small>".format(_("Install")))
                action_button.name = 1
        else:
            self.set_button_class(action_button, 2)
            not_found_image = Gtk.Image.new_from_icon_name("action-unavailable-symbolic", Gtk.IconSize.BUTTON)
            action_button.add(not_found_image)

        uninstallbutton = Gtk.Button.new()
        uninstallbutton.name = 0
        uninstallbutton.props.valign = Gtk.Align.CENTER
        uninstallbutton.props.always_show_image = True
        uninstallbutton.set_image(Gtk.Image.new_from_icon_name("user-trash-symbolic", Gtk.IconSize.BUTTON))
        uninstallbutton.set_label("")
        uninstallbutton.set_tooltip_text(_("Uninstall"))
        uninstallbutton.set_relief(Gtk.ReliefStyle.NONE)
        uninstallbutton.connect("clicked", self.app_widget_action_clicked)

        summary_label = Gtk.Label.new()
        summary_label.set_markup("<span weight='light' size='small'>{}</span>".format(GLib.markup_escape_text(
            self.get_sub_category_name_from_app_name(app), -1)))
        summary_label.props.valign = Gtk.Align.START
        summary_label.props.halign = Gtk.Align.START
        summary_label.set_line_wrap(False)
        summary_label.set_max_width_chars(33)
        summary_label.set_ellipsize(Pango.EllipsizeMode.END)

        box_app = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        box_app.props.valign = Gtk.Align.CENTER
        box_app.pack_start(app_name, False, True, 0)
        box_app.pack_start(summary_label, False, True, 0)
        # box_app.set_hexpand(True)

        du_static = Gtk.Label.new()
        du_static.set_line_wrap(False)
        du_static.set_markup("")

        du_size = Gtk.Label.new()
        du_size.set_line_wrap(False)
        du_size.set_markup("")

        box_du = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        box_du.props.valign = Gtk.Align.CENTER
        box_du.pack_start(du_static, False, True, 0)
        box_du.pack_start(du_size, False, True, 0)
        box_du.set_size_request(177, -1)

        box_h = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 12)
        box_h.pack_start(app_icon, False, True, 0)
        box_h.pack_start(box_app, False, True, 0)
        box_h.pack_end(uninstallbutton, False, True, 0)
        box_h.pack_end(action_button, False, True, 0)
        box_h.pack_end(box_du, False, True, 40 if self.display_width >= 1920 else 20)

        box_h.set_margin_start(8)
        box_h.set_margin_end(8)
        box_h.set_margin_top(8)
        box_h.set_margin_bottom(5)

        bottom_separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
        bottom_separator.props.valign = Gtk.Align.END
        bottom_separator.set_vexpand(True)
        GLib.idle_add(bottom_separator.get_style_context().add_class, "pardus-software-mostdown-bottom-seperator")

        box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 7)
        box.pack_start(box_h, False, True, 0)
        box.pack_end(bottom_separator, True, True, 0)

        listbox = Gtk.ListBox.new()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        listbox.connect("row-activated", self.on_app_listbox_row_activated)
        listbox_row = Gtk.ListBoxRow()
        GLib.idle_add(listbox_row.add, box)
        listbox_row.name = {app: details} if details else app
        GLib.idle_add(listbox.add, listbox_row)

        GLib.idle_add(listbox.get_style_context().add_class, "pardus-software-listbox-mostdown")

        return listbox

    def create_queue_widget(self, app, upgrade=False, icon_name=None):

        app_name = Gtk.Label.new()
        app_name.set_markup("<b>{}</b>".format(GLib.markup_escape_text(self.get_pretty_name_from_app_name(app), -1)))
        app_name.props.halign = Gtk.Align.START
        app_name.set_line_wrap(False)
        app_name.set_justify(Gtk.Justification.LEFT)
        app_name.set_max_width_chars(23 if self.display_width >= 1920 else 21)
        app_name.set_ellipsize(Pango.EllipsizeMode.END)
        app_name.props.halign = Gtk.Align.START

        try:
            if os.path.isfile(icon_name if icon_name else app):
                px = GdkPixbuf.Pixbuf.new_from_file_at_size(app, 32, 32)
                app_icon = Gtk.Image.new()
                app_icon.set_from_pixbuf(px)
            else:
                app_icon = Gtk.Image.new_from_icon_name(icon_name if icon_name else app, Gtk.IconSize.DND)
        except Exception as e:
            app_icon = Gtk.Image.new_from_icon_name("image-missing-symbolic", Gtk.IconSize.DND)
            print("Exception on create_queue_widget: {}, app: {}".format(e, app))
        app_icon.set_pixel_size(32)
        app_icon.get_style_context().add_class("pardus-software-mostapp-icon")
        app_icon.props.halign = Gtk.Align.CENTER
        app_icon.props.valign = Gtk.Align.CENTER

        cancel_button = Gtk.Button.new()
        cancel_button.connect("clicked", self.on_queue_cancel_button_clicked)
        cancel_button.props.valign = Gtk.Align.CENTER
        cancel_button.set_size_request(77, -1)
        cancel_button_label = Gtk.Label.new()
        cancel_button_label.set_line_wrap(False)
        cancel_button_label.set_justify(Gtk.Justification.LEFT)
        cancel_button_label.set_max_width_chars(6)
        cancel_button_label.set_ellipsize(Pango.EllipsizeMode.END)
        cancel_button.add(cancel_button_label)
        cancel_button_label.set_markup("<small>{}</small>".format(_("Cancel")))
        cancel_button.name = app

        summary_label = Gtk.Label.new()
        summary_label.set_markup("<span weight='light' size='small'>{}</span>".format(GLib.markup_escape_text(
            self.get_sub_category_name_from_app_name(app), -1)))
        summary_label.props.valign = Gtk.Align.START
        summary_label.props.halign = Gtk.Align.START
        summary_label.set_line_wrap(False)
        summary_label.set_max_width_chars(23 if self.display_width >= 1920 else 21)
        summary_label.set_ellipsize(Pango.EllipsizeMode.END)

        box_app = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        box_app.props.valign = Gtk.Align.CENTER
        box_app.pack_start(app_name, False, True, 0)
        box_app.pack_start(summary_label, False, True, 0)
        # box_app.set_hexpand(True)

        version_title = Gtk.Label.new()
        version_title.set_line_wrap(False)
        version_title.set_markup("<b>{}</b>".format(_("Version")))

        version_label =Gtk.Label.new()
        version_label.set_line_wrap(False)
        version_label.set_max_width_chars(21 if self.display_width >= 1920 else 13)
        version_label.set_ellipsize(Pango.EllipsizeMode.END)
        version_label.set_markup("<span weight='light' size='small'>{}</span>".format(self.Package.candidate_version(app)))

        box_version = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        box_version.props.halign = Gtk.Align.END
        box_version.props.valign = Gtk.Align.CENTER
        box_version.pack_start(version_title, False, True, 0)
        box_version.pack_start(version_label, False, True, 0)
        box_version.set_size_request(120, -1)

        progress_bar = Gtk.ProgressBar.new()
        progress_bar.set_show_text(True)
        progress_bar.set_ellipsize(Pango.EllipsizeMode.END)
        progress_bar.props.valign = Gtk.Align.CENTER
        if self.Package.isinstalled(app):
            if self.Package.is_upgradable(app) and upgrade:
                progress_bar.set_text("{}".format(_("Will be upgraded")))
            else:
                progress_bar.set_text("{}".format(_("Will be removed")))
        else:
            progress_bar.set_text("{}".format(_("Will be installed")))

        box_h = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 12)
        box_h.pack_start(app_icon, False, True, 0)
        box_h.pack_start(box_app, False, True, 0)
        box_h.pack_end(cancel_button, False, True, 0)
        box_h.pack_end(progress_bar, False, True, 20 if self.display_width >= 1920 else 6)
        box_h.pack_end(box_version, False, True, 20 if self.display_width >= 1920 else 6)

        box_h.set_margin_start(8)
        box_h.set_margin_end(8)
        box_h.set_margin_top(8)
        box_h.set_margin_bottom(5)

        bottom_separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
        bottom_separator.props.valign = Gtk.Align.END
        bottom_separator.set_vexpand(True)
        GLib.idle_add(bottom_separator.get_style_context().add_class, "pardus-software-mostdown-bottom-seperator")

        box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 7)
        box.pack_start(box_h, False, True, 0)
        box.pack_end(bottom_separator, True, True, 0)

        listbox = Gtk.ListBox.new()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        # listbox.connect("row-activated", self.on_app_listbox_row_activated)
        listbox_row = Gtk.ListBoxRow()
        GLib.idle_add(listbox_row.add, box)
        listbox_row.name = app
        GLib.idle_add(listbox.add, listbox_row)

        GLib.idle_add(listbox.get_style_context().add_class, "pardus-software-listbox-mostdown")

        return listbox

    def set_most_apps(self):
        # GLib.idle_add(lambda: self.ui_mostdown_flowbox.foreach(lambda child: self.ui_mostdown_flowbox.remove(child)))
        # GLib.idle_add(lambda: self.ui_recent_flowbox.foreach(lambda child: self.ui_recent_flowbox.remove(child)))
        # GLib.idle_add(lambda: self.ui_editor_flowbox.foreach(lambda child: self.ui_editor_flowbox.remove(child)))

        if self.Server.connection:
            self.Logger.info("in set_most_apps")
            GLib.idle_add(self.set_trend_apps)
            GLib.idle_add(self.set_editor_apps)
            GLib.idle_add(self.set_mostdown_apps)
            GLib.idle_add(self.set_recent_apps)

    def set_editor_apps(self):
        self.Logger.info("in set_editor_apps")

        GLib.idle_add(lambda: self.ui_editor_flowbox.foreach(lambda child: self.ui_editor_flowbox.remove(child)))

        for editor_app in self.Server.ediapplist:

            editor_app_name = editor_app["name"]
            editor_app_pretty_name = self.get_pretty_name_from_app_name(editor_app_name)
            editor_app_sub_categoy = self.get_sub_category_name_from_app_name(editor_app_name)

            app_image = Gtk.Image.new()
            app_image.set_pixel_size(200)
            app_image.set_hexpand(True)
            app_image.props.halign = Gtk.Align.FILL

            css = """
            .pardus-software-editor {{
                background-image: url("{}");
                background-size: cover;
                background-repeat: no-repeat;
                background-position: center;
                border-radius: 8px;
            }}
            """.format(os.path.join(self.UserSettings.editor_images_dir, "{}.png".format(editor_app_name)))
            style_provider = Gtk.CssProvider()
            style_provider.load_from_data(str.encode(css))
            app_image.get_style_context().add_class("pardus-software-editor")
            app_image.get_style_context().add_provider(style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

            app_name = Gtk.Label.new()
            app_name.set_markup("<b>{}</b>".format(editor_app_pretty_name))
            app_name.set_line_wrap(False)
            app_name.set_justify(Gtk.Justification.LEFT)
            app_name.set_max_width_chars(23)
            app_name.set_ellipsize(Pango.EllipsizeMode.END)
            app_name.props.halign = Gtk.Align.START

            app_icon = Gtk.Image.new_from_icon_name(editor_app_name, Gtk.IconSize.DND)
            app_icon.set_pixel_size(32)
            app_icon.get_style_context().add_class("pardus-software-mostapp-icon")
            app_icon.props.halign = Gtk.Align.CENTER
            app_icon.props.valign = Gtk.Align.CENTER

            action_button = Gtk.Button.new()
            action_button.connect("clicked", self.app_widget_action_clicked)
            action_button.props.halign = Gtk.Align.END
            action_button.props.valign = Gtk.Align.CENTER
            action_button.set_hexpand(True)
            action_button.set_size_request(77, -1)

            action_button_label = Gtk.Label.new()
            action_button_label.set_line_wrap(False)
            action_button_label.set_justify(Gtk.Justification.LEFT)
            action_button_label.set_max_width_chars(6)
            action_button_label.set_ellipsize(Pango.EllipsizeMode.END)

            is_installed = self.Package.isinstalled(editor_app_name)
            is_upgradable = self.Package.is_upgradable(editor_app_name)
            is_openable = self.get_desktop_filename_from_app_name(editor_app_name) != ""
            if is_installed is not None:
                action_button.add(action_button_label)
                if is_installed:
                    if is_upgradable:
                        self.set_button_class(action_button, 3)
                        action_button_label.set_markup("<small>{}</small>".format(_("Update")))
                        action_button.name = 2
                    else:
                        if is_openable:
                            self.set_button_class(action_button, 4)
                            action_button_label.set_markup("<small>{}</small>".format(_("Open")))
                            action_button.name = 3
                        else:
                            self.set_button_class(action_button, 4)
                            action_button_label.set_markup("<small>{}</small>".format(_("Open")))
                            action_button.name = 9
                else:
                    self.set_button_class(action_button, 0)
                    action_button_label.set_markup("<small>{}</small>".format(_("Install")))
                    action_button.name = 1
            else:
                self.set_button_class(action_button, 2)
                not_found_image = Gtk.Image.new_from_icon_name("action-unavailable-symbolic", Gtk.IconSize.BUTTON)
                action_button.add(not_found_image)

            summary_label = Gtk.Label.new()
            summary_label.set_markup("<span weight='light' size='small'>{}</span>".format(editor_app_sub_categoy))
            summary_label.props.halign = Gtk.Align.START
            summary_label.set_line_wrap(False)
            summary_label.set_max_width_chars(22)
            summary_label.set_ellipsize(Pango.EllipsizeMode.END)

            box_v = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
            box_v.props.valign = Gtk.Align.CENTER
            box_v.pack_start(app_name, False, True, 0)
            box_v.pack_start(summary_label, False, True, 0)
            box_v.set_margin_end(12)

            box_h = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 12)
            box_h.pack_start(app_icon, False, True, 0)
            box_h.pack_start(box_v, False, True, 0)
            box_h.pack_start(action_button, False, True, 0)
            box_h.set_margin_start(5)
            box_h.set_margin_end(5)
            box_h.set_margin_top(5)
            box_h.set_margin_bottom(5)

            bottom_separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
            bottom_separator.props.valign = Gtk.Align.END
            GLib.idle_add(bottom_separator.get_style_context().add_class, "pardus-software-mostdown-bottom-seperator")

            box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 7)
            box.pack_start(app_image, False, True, 0)
            box.pack_start(box_h, True, True, 0)
            box.pack_start(bottom_separator, True, True, 0)
            box.set_margin_start(5)
            box.set_margin_end(5)
            box.set_margin_top(5)

            listbox = Gtk.ListBox.new()
            listbox.set_selection_mode(Gtk.SelectionMode.NONE)
            listbox.connect("row-activated", self.on_app_listbox_row_activated)
            listbox_row = Gtk.ListBoxRow()
            GLib.idle_add(listbox_row.add, box)
            listbox_row.name = editor_app_name
            GLib.idle_add(listbox.add, listbox_row)

            GLib.idle_add(listbox.get_style_context().add_class, "pardus-software-listbox-mostdown")
            GLib.idle_add(self.ui_editor_flowbox.insert, listbox, -1)

        GLib.idle_add(self.ui_editor_flowbox.show_all)

    def set_trend_apps(self):
        self.Logger.info("in set_trend_apps")
        GLib.idle_add(lambda: self.ui_trend_flowbox.foreach(lambda child: self.ui_trend_flowbox.remove(child)))
        counter = 0
        for app in self.Server.trendapplist[:self.home_trend_count]:
            counter += 1
            listbox = self.create_app_widget(app["name"], None, counter)
            GLib.idle_add(self.ui_trend_flowbox.insert, listbox, -1)
        GLib.idle_add(self.ui_trend_flowbox.show_all)

        GLib.idle_add(lambda: self.ui_trendapps_flowbox.foreach(lambda child: self.ui_trendapps_flowbox.remove(child)))
        counter = 0
        for app in self.Server.trendapplist:
            counter += 1
            listbox = self.create_app_widget(app["name"], None, counter)
            GLib.idle_add(self.ui_trendapps_flowbox.insert, listbox, -1)
        GLib.idle_add(self.ui_trendapps_flowbox.show_all)

    def set_mostdown_apps(self):
        self.Logger.info("in set_mostdown_apps")
        GLib.idle_add(lambda: self.ui_mostdown_flowbox.foreach(lambda child: self.ui_mostdown_flowbox.remove(child)))
        for app in self.Server.mostdownapplist[:self.home_mostdown_count]:
            listbox = self.create_app_widget(app["name"], None)
            GLib.idle_add(self.ui_mostdown_flowbox.insert, listbox, -1)
        GLib.idle_add(self.ui_mostdown_flowbox.show_all)

        GLib.idle_add(lambda: self.ui_mostdownapps_flowbox.foreach(lambda child: self.ui_mostdownapps_flowbox.remove(child)))
        for app in self.Server.mostdownapplist:
            listbox = self.create_app_widget(app["name"], None)
            GLib.idle_add(self.ui_mostdownapps_flowbox.insert, listbox, -1)
        GLib.idle_add(self.ui_mostdownapps_flowbox.show_all)

    def set_recent_apps(self):
        self.Logger.info("in set_recent_apps")
        GLib.idle_add(lambda: self.ui_recent_flowbox.foreach(lambda child: self.ui_recent_flowbox.remove(child)))
        for app in self.Server.lastaddedapplist[:self.home_recent_count]:
            listbox = self.create_app_widget(app["name"], None)
            GLib.idle_add(self.ui_recent_flowbox.insert, listbox, -1)
        GLib.idle_add(self.ui_recent_flowbox.show_all)

        GLib.idle_add(lambda: self.ui_recentapps_flowbox.foreach(lambda child: self.ui_recentapps_flowbox.remove(child)))
        for app in self.Server.lastaddedapplist:
            listbox = self.create_app_widget(app["name"], None)
            GLib.idle_add(self.ui_recentapps_flowbox.insert, listbox, -1)
        GLib.idle_add(self.ui_recentapps_flowbox.show_all)

    def on_app_listbox_row_activated(self, listbox, row):
        print(f"on_app_listbox_row_activated: {row.name}")
        # unselect the flowbox
        GLib.idle_add(listbox.get_parent().get_parent().unselect_all)
        self.set_app_details_page(row.name)

    def on_repoapp_listbox_row_activated(self, listbox, row):
        print(f"on_repoapp_listbox_row_activated: {row.name}")
        # unselect the flowbox
        GLib.idle_add(listbox.get_parent().get_parent().unselect_all)
        self.set_app_details_page(row.name, source=2)

    def set_rating_stars(self, average):
        sub_point = int("{:.1f}".format(average).split(".")[1])
        avg = int(average)

        def get_star_subname(fraction):
            if fraction >= 5:
                return "ps-rating-star-half"
            else:
                return "ps-rating-star-empty"

        if avg == 0:
            self.ui_ad_rating_star1_image.set_from_icon_name(get_star_subname(sub_point), Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star2_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star3_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star4_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star5_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
        elif avg == 1:
            self.ui_ad_rating_star1_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star2_image.set_from_icon_name(get_star_subname(sub_point), Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star3_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star4_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star5_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
        elif avg == 2:
            self.ui_ad_rating_star1_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star2_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star3_image.set_from_icon_name(get_star_subname(sub_point), Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star4_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star5_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
        elif avg == 3:
            self.ui_ad_rating_star1_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star2_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star3_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star4_image.set_from_icon_name(get_star_subname(sub_point), Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star5_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
        elif avg == 4:
            self.ui_ad_rating_star1_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star2_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star3_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star4_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star5_image.set_from_icon_name(get_star_subname(sub_point), Gtk.IconSize.LARGE_TOOLBAR)
        elif avg == 5:
            self.ui_ad_rating_star1_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star2_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star3_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star4_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_ad_rating_star5_image.set_from_icon_name("ps-rating-star-full", Gtk.IconSize.LARGE_TOOLBAR)

    def set_rating_progressbar(self, total_count, count_1, count_2, count_3, count_4, count_5):
        self.ui_rating_count1_label.set_text("{}".format(count_1))
        self.ui_rating_count2_label.set_text("{}".format(count_2))
        self.ui_rating_count3_label.set_text("{}".format(count_3))
        self.ui_rating_count4_label.set_text("{}".format(count_4))
        self.ui_rating_count5_label.set_text("{}".format(count_5))
        if total_count != 0:
            self.ui_rating_prg1_progressbar.set_fraction(count_1 / total_count)
            self.ui_rating_prg2_progressbar.set_fraction(count_2 / total_count)
            self.ui_rating_prg3_progressbar.set_fraction(count_3 / total_count)
            self.ui_rating_prg4_progressbar.set_fraction(count_4 / total_count)
            self.ui_rating_prg5_progressbar.set_fraction(count_5 / total_count)
        else:
            self.ui_rating_prg1_progressbar.set_fraction(0)
            self.ui_rating_prg2_progressbar.set_fraction(0)
            self.ui_rating_prg3_progressbar.set_fraction(0)
            self.ui_rating_prg4_progressbar.set_fraction(0)
            self.ui_rating_prg5_progressbar.set_fraction(0)

    def set_comment_stars(self, point):
        self.comment_star_point = point
        if point == 0:
            self.ui_comment_star1_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_star2_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_star3_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_star4_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_star5_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
        else:
            self.ui_comment_star1_image.set_from_icon_name(
                "ps-rating-star-full" if point >= 1 else "ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_star2_image.set_from_icon_name(
                "ps-rating-star-full" if point >= 2 else "ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_star3_image.set_from_icon_name(
                "ps-rating-star-full" if point >= 3 else "ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_star4_image.set_from_icon_name(
                "ps-rating-star-full" if point >= 4 else "ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_star5_image.set_from_icon_name(
                "ps-rating-star-full" if point == 5 else "ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)

    def set_comment_own_stars(self, point):
        if point == 0:
            self.ui_comment_own_star1_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_own_star2_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_own_star3_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_own_star4_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_own_star5_image.set_from_icon_name("ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
        else:
            self.ui_comment_own_star1_image.set_from_icon_name(
                "ps-rating-star-full" if point >= 1 else "ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_own_star2_image.set_from_icon_name(
                "ps-rating-star-full" if point >= 2 else "ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_own_star3_image.set_from_icon_name(
                "ps-rating-star-full" if point >= 3 else "ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_own_star4_image.set_from_icon_name(
                "ps-rating-star-full" if point >= 4 else "ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)
            self.ui_comment_own_star5_image.set_from_icon_name(
                "ps-rating-star-full" if point == 5 else "ps-rating-star-empty", Gtk.IconSize.LARGE_TOOLBAR)

    def clear_app_details(self):
        self.ui_ad_name.set_text("")
        self.ui_ad_subcategory_label.set_text("")
        self.ui_ad_top_category_label.set_text("")

        self.ui_ad_top_avgrate_label.set_text("")
        self.ui_ad_top_size_label.set_text("")
        self.ui_ad_top_depends_count_label.set_text("")
        self.ui_ad_version_label.set_text("")
        self.ui_ad_size_label.set_text("")
        self.ui_ad_required_size_label.set_text("")
        self.ui_ad_type_label.set_text("")
        self.ui_ad_category_label.set_text("")
        self.ui_ad_license_label.set_text("")
        self.ui_ad_component_label.set_text("")
        self.ui_ad_maintainer_name_label.set_text("")
        self.ui_ad_maintainer_web_label.set_text("")
        self.ui_ad_maintainer_mail_label.set_text("")

        self.ui_ad_remove_button.set_visible(False)
        self.ui_ad_disclaimer_button.set_visible(False)

        self.ui_ad_remove_list_box.set_visible(False)
        self.ui_ad_install_list_box.set_visible(False)
        self.ui_ad_broken_list_box.set_visible(False)

        self.ui_ad_more_comment_button.set_visible(False)

        self.ui_ad_bottom_avgrate_label.set_text("")
        self.ui_ad_bottom_rate_count_label.set_text("")

        self.set_rating_stars(0)
        self.set_rating_progressbar(0, 0, 0, 0, 0, 0)

        for row in self.ui_ad_image_box:
            self.ui_ad_image_box.remove(row)

        for row in self.ui_ad_comments_flowbox:
            self.ui_ad_comments_flowbox.remove(row)

        self.ui_ad_more_comment_button.name = "pardus"

        self.set_comment_stars(0)
        self.ui_comment_fullname_entry.set_text("")
        start, end = self.ui_comment_content_textbuffer.get_bounds()
        self.ui_comment_content_textbuffer.delete(start, end)
        self.ui_comment_error_label.set_text("")
        self.ui_comment_error_label.set_visible(False)
        self.ui_comment_send_button.set_sensitive(False)
        self.ui_comment_main_stack.set_visible_child_name("main")

        self.ui_comment_own = {}

        self.image_stack_names = []
        self.image_stack_current_index = 0
        self.image_original_pixbufs = {}
        for image in self.ui_image_stack:
            self.ui_image_stack.remove(image)

        for child in self.ui_ad_available_repos_box.get_children():
            self.ui_ad_available_repos_box.remove(child)

    def set_app_details_page(self, app, source=1):
        """
        :param app: package name of application
        :param source: 1:store_app, 2:repo_app, 0:external_app
        """

        self.ui_app_name = ""

        self.ui_myapp_name_dic = ""

        if isinstance(app, dict):
            app_name, details = next(iter(app.items()))
        elif isinstance(app, str):
            app_name = app
            details = self.apps_full.get(app_name, {})
        else:
            self.Logger.warning("{} {}".format("set_app_details_page func ERROR for: ", app))
            return

        if not details:
            self.Logger.warning("{} details not found.".format(app_name))
            return

        print("app_name: {}".format(app_name))
        print("details: {}".format(details))

        self.ui_app_name = app_name

        self.clear_app_details()

        self.ui_ad_image_scrolledwindow.set_visible(source == 1)
        self.ui_ad_ratings_box.set_visible(source == 1)
        self.ui_ad_about_box.set_visible(source == 1 or source == 2)
        self.ui_ad_details_box.set_visible(source == 1 or source == 2)
        self.ui_ad_dependencies_box.set_visible(source == 1 or source == 2)
        self.ui_ad_availablerepos_box.set_visible(source == 1 or source == 2)
        self.ui_ad_top_stack.set_visible_child_name("stats" if source == 1 else "limited" if source == 2 else "external")
        self.ui_ad_action_stack.set_visible_child_name("action" if source == 1 or source == 2 else "external")

        # set scroll position to top (reset)
        self.ui_appdetails_scrolledwindow.set_vadjustment(Gtk.Adjustment())

        self.ui_right_stack_navigate_to("appdetails")

        # store app operations
        if source == 1:
            for image in details["screenshots"]:
                self.AppImage.get_image(self.Server.serverurl + image, app_name)

            self.AppDetail.get_details(self.Server.serverurl + self.Server.serverdetails, {"mac": self.mac, "app": app_name})

            self.comment_limit = 10
            self.gnome_comment_limit = 10
            self.PardusComment.get_comments(self.Server.serverurl + self.Server.serverparduscomments,
                                            {"mac": self.mac, "app": app_name, "limit": self.comment_limit}, app_name)

            app_pretty_name = details["prettyname"].get(self.user_locale) or details["prettyname"].get("en", "{}".format(app_name.title()))
            app_category_name = ((details.get("category") or [{}])[0].get(self.user_locale, "") or "").title()
            app_subcategory_name = (details.get("subcategory") or [{}])[0].get(self.user_locale) or (details.get("subcategory") or [{}])[0].get("en") or ""

            self.ui_ad_name.set_text("{}".format(app_pretty_name))
            self.ui_ad_top_category_label.set_text("{}".format(app_category_name))
            self.ui_ad_subcategory_label.set_text("{}".format(app_subcategory_name))

            self.ui_ad_icon.set_from_icon_name(app_name, Gtk.IconSize.DIALOG)
            self.ui_ad_icon.set_pixel_size(68)

            self.ui_ad_description_label.set_text(details["description"][self.user_locale])
            app_version = self.Package.installed_version(app_name)
            self.ui_ad_version_label.set_text("{}".format(app_version))

            maintainer_info = (details.get("maintainer") or [{}])[0]
            m_name = maintainer_info.get("name", "")
            m_mail = maintainer_info.get("mail", "")
            m_web = maintainer_info.get("website", "")
            self.ui_ad_maintainer_name_label.set_markup(m_name)
            self.ui_ad_maintainer_mail_label.set_markup("<a title='{}' href='mailto:{}'>{}</a>".format(
                GLib.markup_escape_text(m_mail, -1),
                GLib.markup_escape_text(m_mail, -1),
                GLib.markup_escape_text(m_mail, -1)))

            self.ui_ad_maintainer_web_label.set_markup("<a title='{}' href='{}'>{}</a>".format(
                GLib.markup_escape_text(m_web, -1),
                GLib.markup_escape_text(m_web, -1),
                GLib.markup_escape_text(m_web, -1)))

            self.ui_ad_category_label.set_text(app_category_name)
            self.ui_ad_license_label.set_text(details.get("license") or "")

            codenames = [c.get("name") for c in (details.get("codename") or [])]
            for codename in codenames:
                label = Gtk.Label.new()
                label.set_markup("<b>{}</b>".format(codename.title()))
                label.get_style_context().add_class("pardus-software-codename-label")
                label.set_alignment(0.5, 0.5)
                label.set_margin_left(4)
                label.set_margin_right(4)
                label.set_margin_top(4)
                label.set_margin_bottom(4)
                self.ui_ad_available_repos_box.pack_start(label, False, False, 0)
            self.ui_ad_available_repos_box.show_all()

            self.ui_comment_appname_label.set_markup("<b>{}</b>".format(app_pretty_name))
            self.ui_comment_subcategory_label.set_markup("{}".format(app_subcategory_name))
            self.ui_comment_icon_image.set_from_icon_name(app_name, Gtk.IconSize.DIALOG)
            self.ui_comment_icon_image.set_pixel_size(48)
            self.ui_comment_version_label.set_text("{}".format(app_version))
            self.ui_comment_fullname_entry.set_text("{}".format(self.UserSettings.user_real_name))

        # store app and repo app operations
        if source == 1 or source == 2:
            self.ui_ad_action_button.remove(self.ui_ad_action_button.get_children()[0])
            action_button_label = Gtk.Label.new()
            action_button_label.set_line_wrap(False)
            action_button_label.set_justify(Gtk.Justification.LEFT)
            action_button_label.set_ellipsize(Pango.EllipsizeMode.END)
            self.ui_ad_action_button.add(action_button_label)
            is_installed = self.Package.isinstalled(app_name)
            is_upgradable = self.Package.is_upgradable(app_name)
            if source == 1:
                is_openable = self.get_desktop_filename_from_app_name(app_name) != ""
            else:
                is_openable = details.get("id", False)
            if is_installed is not None:
                threading.Thread(target=self.app_detail_requireds_thread, args=(app_name,), daemon=True).start()
                if is_installed:
                    self.ui_ad_remove_button.set_visible(True)
                    self.ui_ad_remove_button.set_sensitive(True)
                    if is_upgradable:
                        self.set_button_class(self.ui_ad_action_button, 3)
                        action_button_label.set_markup("<small>{}</small>".format(_("Update")))
                        self.ui_ad_action_button.name = 2
                    else:
                        if is_openable:
                            self.set_button_class(self.ui_ad_action_button, 4)
                            action_button_label.set_markup("<small>{}</small>".format(_("Open")))
                            self.ui_ad_action_button.name = 3
                        else:
                            self.set_button_class(self.ui_ad_action_button, 4)
                            action_button_label.set_markup("<small>{}</small>".format(_("Open")))
                            self.ui_ad_action_button.name = 9
                else:
                    self.set_button_class(self.ui_ad_action_button, 0)
                    action_button_label.set_markup("<small>{}</small>".format(_("Install")))
                    self.ui_ad_action_button.name = 1
            else:
                self.set_button_class(self.ui_ad_action_button, 2)
                action_button_label.set_markup("<small>{}</small>".format(_("Not Found")))
                self.ui_ad_sizetitle_label.set_text(_("Download Size"))
                self.ui_ad_required_sizetitle_label.set_text(_("Required Disk Space"))
                self.ui_ad_size_label.set_text("{}".format(_("None")))
                self.ui_ad_required_size_label.set_text("{}".format(_("None")))
                self.ui_ad_top_size_label.set_text("{}".format(_("None")))
            self.ui_ad_action_button.show_all()

            self.ui_ad_remove_button.name = 0

            app_in_queue = next((q for q in self.queue if q["name"] == app_name), None)
            if app_in_queue:
                if is_installed:
                    if is_upgradable and app_in_queue["upgrade"]:
                        self.ui_ad_action_button.set_label(_("Upgrading"))
                    else:
                        self.ui_ad_action_button.set_label(_("Removing"))
                else:
                    self.ui_ad_action_button.set_label(_("Installing"))
                self.ui_ad_action_button.set_sensitive(False)
                if self.ui_ad_remove_button.get_visible():
                    self.ui_ad_remove_button.set_sensitive(False)

            origin_info = self.Package.origins(app_name)
            component = getattr(origin_info, "component", "")
            origin = getattr(origin_info, "origin", "")
            if component == "non-free" or (details.get("component") or {}).get("name", "") == "non-free":
                self.ui_ad_disclaimer_button.set_visible(True)
                type_label = _("Non-Free")
            else:
                self.ui_ad_disclaimer_button.set_visible(False)
                type_label = _("Open Source")
            self.ui_ad_component_label.set_markup(f"{origin} {component}" if origin_info else _("None"))
            self.ui_ad_type_label.set_markup(type_label)

        # repo app and external app operations
        if source == 2 or source == 0:
            self.ui_ad_name.set_text(details["name"])
            try:
                if os.path.isfile(details["icon_name"]):
                    px = GdkPixbuf.Pixbuf.new_from_file_at_size(details["icon_name"], 68, 68)
                    self.ui_ad_icon.set_from_pixbuf(px)
                else:
                    self.ui_ad_icon.set_from_icon_name(details["icon_name"], Gtk.IconSize.DIALOG)
            except Exception as e:
                self.ui_ad_icon.set_from_icon_name("image-missing-symbolic", Gtk.IconSize.DIALOG)
            self.ui_ad_icon.set_pixel_size(68)

        # repo app operations
        if source == 2:

            self.ui_myapp_name_dic = {app_name : details}

            maintainer_name = ""
            maintainer_mail = ""
            maintainer_web = ""
            app_section = ""
            app_version = ""
            app_license = ""
            record = self.Package.get_record(app_name)
            if record:
                app_section = record.get("Section", "")
                app_version = record.get("Version", "")
                maintainer = record.get("Maintainer", "")
                maintainer_web = record.get("Homepage", "")
                app_license = record.get("License", "")
                try:
                    match = re.match(r"^(.*?)(?:\s*<([^>]+)>)?$", maintainer)
                    if match:
                        maintainer_name = (match.group(1) or "").strip()
                        maintainer_mail = (match.group(2) or "").strip()
                except Exception as e:
                    self.Logger.exception("{}".format(e))

            self.ui_ad_maintainer_name_label.set_markup(maintainer_name)
            self.ui_ad_maintainer_mail_label.set_markup("<a title='{}' href='mailto:{}'>{}</a>".format(
                GLib.markup_escape_text(maintainer_mail, -1),
                GLib.markup_escape_text(maintainer_mail, -1),
                GLib.markup_escape_text(maintainer_mail, -1)) if maintainer_mail else "-")

            self.ui_ad_maintainer_web_label.set_markup("<a title='{}' href='{}'>{}</a>".format(
                GLib.markup_escape_text(maintainer_web, -1),
                GLib.markup_escape_text(maintainer_web, -1),
                GLib.markup_escape_text(maintainer_web, -1)) if maintainer_web else "-")

            self.ui_ad_top_category_label.set_text("{}".format(app_section))
            self.ui_ad_subcategory_label.set_text("{}".format(app_name))
            self.ui_ad_version_label.set_text("{}".format(app_version))
            self.ui_ad_category_label.set_text("{}".format(app_section if app_section else "-"))
            self.ui_ad_description_label.set_text(details["description"])

            if not app_license:
                app_license = self.Package.get_license_from_file(app_name)
            self.ui_ad_license_label.set_text("{}".format(app_license if app_license else "-"))

    def app_detail_requireds_thread(self, app):
        app_detail_requireds = self.app_detail_requireds_worker(app)
        GLib.idle_add(self.app_detail_requireds_worker_done, app_detail_requireds)

    def app_detail_requireds_worker(self, app=None):
        return self.Package.required_changes(app)

    def app_detail_requireds_worker_done(self, adr):
        self.Logger.info("app_detail_requireds_worker_done: {}".format(adr))

        is_installed = self.Package.isinstalled(self.ui_app_name)
        if is_installed is not None:
            if is_installed:
                GLib.idle_add(self.ui_ad_sizetitle_label.set_text, _("Package Size"))
                GLib.idle_add(self.ui_ad_required_sizetitle_label.set_text, _("Installed Size"))
                GLib.idle_add(self.ui_ad_size_label.set_text, "{}".format(
                    self.Package.beauty_size(self.Package.get_size(self.ui_app_name))))
                GLib.idle_add(self.ui_ad_required_size_label.set_text, "{}".format(
                    self.Package.beauty_size(adr["freed_size"])))
                GLib.idle_add(self.ui_ad_top_size_label.set_text, "{}".format(
                    self.Package.beauty_size(adr["freed_size"])))
            else:
                GLib.idle_add(self.ui_ad_sizetitle_label.set_text, _("Download Size"))
                GLib.idle_add(self.ui_ad_required_sizetitle_label.set_text, _("Required Disk Space"))
                GLib.idle_add(self.ui_ad_size_label.set_text, "{}".format(
                    self.Package.beauty_size(adr["download_size"])))
                GLib.idle_add(self.ui_ad_required_size_label.set_text, "{}".format(
                    self.Package.beauty_size(adr["install_size"])))
                GLib.idle_add(self.ui_ad_top_size_label.set_text, "{}".format(
                    self.Package.beauty_size(adr["install_size"])))

        if adr["to_delete"]:
            self.ui_ad_remove_list_label.set_text("{}".format(", ".join(adr["to_delete"])))
            self.ui_ad_remove_list_count_label.set_text("({})".format(len(adr["to_delete"])))
            self.ui_ad_remove_list_box.set_visible(True)
            self.ui_ad_top_depends_count_label.set_text("{}".format(len(adr["to_delete"])))
        else:
            self.ui_ad_remove_list_box.set_visible(False)

        if adr["to_install"]:
            self.ui_ad_install_list_label.set_text("{}".format(", ".join(adr["to_install"])))
            self.ui_ad_install_list_count_label.set_text("({})".format(len(adr["to_install"])))
            self.ui_ad_install_list_box.set_visible(True)
            self.ui_ad_top_depends_count_label.set_text("{}".format(len(adr["to_install"])))
        else:
            self.ui_ad_install_list_box.set_visible(False)

        if adr["broken"]:
            self.ui_ad_broken_list_label.set_text("{}".format(", ".join(adr["broken"])))
            self.ui_ad_broken_list_count_label.set_text("({})".format(len(adr["broken"])))
            self.ui_ad_broken_list_box.set_visible(True)
        else:
            self.ui_ad_broken_list_box.set_visible(False)

        return False

    def on_ui_ad_install_list_eventbox_button_press_event(self, widget, event):

        state = not self.ui_ad_install_list_revealer.get_reveal_child()
        self.ui_ad_install_list_revealer.set_reveal_child(state)
        icon = "go-up-symbolic" if state else "go-down-symbolic"
        self.ui_ad_install_list_image.set_from_icon_name(icon, Gtk.IconSize.BUTTON)

    def on_ui_ad_remove_list_eventbox_button_press_event(self, widget, event):

        state = not self.ui_ad_remove_list_revealer.get_reveal_child()
        self.ui_ad_remove_list_revealer.set_reveal_child(state)
        icon = "go-up-symbolic" if state else "go-down-symbolic"
        self.ui_ad_remove_list_image.set_from_icon_name(icon, Gtk.IconSize.BUTTON)

    def on_ui_ad_broken_list_eventbox_button_press_event(self, widget, event):

        state = not self.ui_ad_broken_list_revealer.get_reveal_child()
        self.ui_ad_broken_list_revealer.set_reveal_child(state)
        icon = "go-up-symbolic" if state else "go-down-symbolic"
        self.ui_ad_broken_list_image.set_from_icon_name(icon, Gtk.IconSize.BUTTON)

    def add_to_image_popover(self, pixbuf, uri):
        name = uri.rsplit("/", 1)[-1].split(".", 1)[0]

        self.image_original_pixbufs[name] = pixbuf.copy()

        image = Gtk.Image.new_from_pixbuf(pixbuf)

        self.image_stack_names.append(name)

        GLib.idle_add(self.ui_image_stack.add_named, image, "{}".format(name))

    def get_pretty_name_from_app_name(self, name):
        details = self.apps_full.get(name)
        if not details:
            return name

        pretty = details.get("prettyname", {})
        return pretty.get(self.user_locale) or pretty.get("en") or name

    def get_category_name_from_app_name(self, name):
        details = self.apps_full.get(name)
        if not details:
            return _("Unknown")

        category_list = details.get("category") or []
        if not category_list:
            return _("Unknown")

        value = category_list[0].get(self.user_locale) or category_list[0].get("en") or _("Unknown")

        return value.title()

    def get_sub_category_name_from_app_name(self, name):
        details = self.apps_full.get(name)
        if not details:
            return ""

        subcat_list = details.get("subcategory") or []
        if not subcat_list:
            return ""

        subcat = subcat_list[0]
        value = subcat.get(self.user_locale) or subcat.get("en") or ""

        return value.title()

    def get_description_from_app_name(self, name):
        details = self.apps_full.get(name)
        if not details:
            return _("Unknown")

        desc = details.get("description", {})
        return desc.get(self.user_locale) or desc.get("en") or _("Unknown")

    def get_desktop_filename_from_app_name(self, name):
        details = self.apps_full.get(name)
        return details.get("desktop") if details else ""

    def get_gnome_desktop_filename_from_app_name(self, name):
        details = self.apps_full.get(name)
        return details.get("gnomename") if details else ""

    def onDestroy(self, widget):
        self.MainWindow.destroy()

    def setAnimations(self):
        pass

    def set_button_class(self, button, state):
        '''
        state 0 = app is not installed
        state 1 = app is installed
        state 2 = app is not found
        state 3 = app is upgradable
        state 4 = app is openable
        '''
        if state == 1:
            if button.get_style_context().has_class("suggested-action"):
                button.get_style_context().remove_class("suggested-action")
            if button.get_style_context().has_class("openup-action"):
                button.get_style_context().remove_class("openup-action")
            button.get_style_context().add_class("destructive-action")
            button.set_sensitive(True)
        elif state == 0:
            if button.get_style_context().has_class("destructive-action"):
                button.get_style_context().remove_class("destructive-action")
            if button.get_style_context().has_class("openup-action"):
                button.get_style_context().remove_class("openup-action")
            button.get_style_context().add_class("suggested-action")
            button.set_sensitive(True)
        elif state == 2:
            if button.get_style_context().has_class("suggested-action"):
                button.get_style_context().remove_class("suggested-action")
            if button.get_style_context().has_class("destructive-action"):
                button.get_style_context().remove_class("destructive-action")
            if button.get_style_context().has_class("openup-action"):
                button.get_style_context().remove_class("openup-action")
            button.set_sensitive(False)
        elif state == 3:
            if button.get_style_context().has_class("suggested-action"):
                button.get_style_context().remove_class("suggested-action")
            if button.get_style_context().has_class("destructive-action"):
                button.get_style_context().remove_class("destructive-action")
            button.get_style_context().add_class("openup-action")
            button.set_sensitive(True)
        elif state == 4:
            if button.get_style_context().has_class("suggested-action"):
                button.get_style_context().remove_class("suggested-action")
            if button.get_style_context().has_class("destructive-action"):
                button.get_style_context().remove_class("destructive-action")
            button.get_style_context().add_class("openup-action")
            button.set_sensitive(True)

    def set_myapps(self, du=False):
        def clear_flowbox():
            if self.ui_installedapps_flowbox:
                self.ui_installedapps_flowbox.foreach(lambda row: self.ui_installedapps_flowbox.remove(row))
            return False

        GLib.idle_add(self.ui_myapps_combobox.set_sensitive, False)
        GLib.idle_add(clear_flowbox)
        if du:
            GLib.idle_add(self.ui_myapps_du_progress_box.set_visible, True)
            GLib.idle_add(self.ui_myapps_du_spinner.start)
            self.myapps_du_cancel_event = threading.Event()

        def run_worker():
            myapps = self.myapps_worker(du=du, cancel_event=self.myapps_du_cancel_event)

            if myapps is not None:
                GLib.idle_add(self.on_myapps_worker_done, myapps, du)
            else:
                GLib.idle_add(self.on_myapps_worker_cancelled)

        threading.Thread(target=run_worker, daemon=True).start()

    def myapps_worker(self, du=False, cancel_event=None):
        return self.Package.get_installed_apps(du=du, cancel_event=cancel_event)

    def on_myapps_worker_done(self, myapps, du=False):
        for pkg in myapps:
            self.add_to_myapps_ui(pkg, du=du)
        GLib.idle_add(self.ui_myapps_du_progress_box.set_visible, False)
        GLib.idle_add(self.ui_myapps_du_spinner.stop)
        GLib.idle_add(self.ui_myapps_combobox.set_sensitive, True)
        GLib.idle_add(self.ui_installedapps_flowbox.show_all)
        GLib.idle_add(self.control_args)
        if du:
            self.ui_installedapps_flowbox.set_sort_func(None)
        self.Logger.info("on_myapps_worker_done")

    def on_myapps_worker_cancelled(self):
        GLib.idle_add(self.ui_myapps_du_spinner.stop)
        GLib.idle_add(self.ui_myapps_du_progress_box.set_visible, False)
        GLib.idle_add(self.ui_myapps_combobox.set_sensitive, True)
        self.Logger.info("on_myapps_worker_cancelled")
        self.myapps_du_cancel_event = None
        self.Logger.info("on_myapps_worker_cancelled: setting apps as default")
        GLib.idle_add(self.ui_myapps_combobox.set_active, 0)

    def on_myapps_du_cancel_button_clicked(self, button):
        if self.myapps_du_cancel_event:
            self.myapps_du_cancel_event.set()

    def myappsdetail_popup_worker_thread(self, app, popup=False):
        myappdetails = self.myappsdetail_popup_worker(app)
        GLib.idle_add(self.on_myappsdetail_popup_worker_done, myappdetails, popup)

    def myappsdetail_popup_worker(self, app):
        valid, myapp_details, myapp_package = self.Package.myapps_remove_details(app["filename"])
        self.Logger.info("{}".format(myapp_details))
        return valid, myapp_details, myapp_package, app["name"], app["icon_name"], app["filename"], app["description"]

    def on_myappsdetail_popup_worker_done(self, myapp, popup=False):
        self.myapp_toremove_list = []
        self.myapp_toremove = ""
        self.myapp_toremove_desktop = ""
        self.myapp_toremove_icon = ""

        valid, details, package, name, icon, desktop, description = myapp
        if valid and details is not None:
            self.ui_myapp_pop_app.set_markup(
                "<span size='large'><b>{}</b></span>".format(GLib.markup_escape_text(name, -1)))
            self.ui_myapp_pop_package.set_markup("<i>{}</i>".format(package))

            self.myapp_toremove_icon = icon

            self.ui_myapp_pop_uninstall_button.set_sensitive(True)

            if details["to_delete"] and details["to_delete"] is not None:
                self.ui_myapp_pop_toremove_label.set_markup(
                    "{}".format(", ".join(details["to_delete"])))
                self.ui_myapp_pop_toremove_box.set_visible(True)

                self.myapp_toremove_list = details["to_delete"]
                self.myapp_toremove = package
                self.myapp_toremove_desktop = desktop

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
            self.Logger.info("package not found: {}".format(myapp))
            self.ui_myapp_pop_stack.set_visible_child_name("notfound")

            try:
                if os.path.isfile(icon):
                    px = GdkPixbuf.Pixbuf.new_from_file_at_size(icon, 64, 64)
                    self.ui_myapp_pop_notfound_image.set_from_pixbuf(px)
                else:
                    self.ui_myapp_pop_notfound_image.set_from_icon_name(icon, Gtk.IconSize.DIALOG)
            except Exception as e:
                self.ui_myapp_pop_notfound_image.set_from_icon_name("image-missing-symbolic", Gtk.IconSize.DIALOG)
            self.ui_myapp_pop_notfound_image.set_pixel_size(64)

            self.ui_myapp_pop_notfound_name.set_markup("<span size='large'><b>{}</b></span>".format(name))

    def on_ui_myapp_details_popover_closed(self, popover):
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
        self.ui_myapp_details_popover.popdown()

    def on_myapp_listbox_row_activated(self, listbox, row):
        print(f"on_myapp_listbox_row_activated: {row.name}")
        # unselect the flowbox
        GLib.idle_add(listbox.get_parent().get_parent().unselect_all)

        threading.Thread(target=self.myappsdetail_page_worker_thread,
                         args=(row.name["filename"], row.name,), daemon=True).start()

    def myappsdetail_page_worker_thread(self, filename, details):
        package = self.myappsdetail_page_worker(filename)
        GLib.idle_add(self.on_myappsdetail_page_worker_done, package, details)

    def myappsdetail_page_worker(self, filename):
        package = self.Package.get_appname_from_desktopfile(filename)
        return package

    def on_myappsdetail_page_worker_done(self, package, details):
        found, package_name = package

        if found:
            if package_name in self.apps_full.keys():
                self.set_app_details_page(app=package_name, source=1)
            else:
                self.set_app_details_page(app={package_name: details}, source=2)
        else:
            self.set_app_details_page(app={package_name: details}, source=0)

    def format_date_as_ago(self, dt_utc):
        local_tz = datetime.now().astimezone().tzinfo

        try:
            if isinstance(dt_utc, (int, float)):
                dt_utc = datetime.fromtimestamp(dt_utc, tz=timezone.utc)
            elif isinstance(dt_utc, str):
                dt_utc = datetime.fromisoformat(dt_utc)
            else:
                return "{}".format(dt_utc)
        except Exception:
            return "{}".format(dt_utc)

        try:
            dt_local = dt_utc.astimezone(local_tz)
        except Exception:
            return "{}".format(dt_utc)

        now = datetime.now(local_tz)
        diff = now - dt_local
        seconds = diff.total_seconds()

        minutes = seconds / 60
        hours = minutes / 60
        days = hours / 24
        weeks = days / 7
        months = days / 30
        years = days / 365

        if seconds < 60:
            return _("{} seconds ago").format(int(seconds))
        elif minutes < 60:
            return _("{} minutes ago").format(int(minutes))
        elif hours < 24:
            return _("{} hours ago").format(int(hours))
        elif days < 7:
            return _("{} days ago").format(int(days))
        elif weeks < 4:
            return _("{} weeks ago").format(int(weeks))
        elif months < 12:
            return _("{} months ago").format(int(months))
        else:
            return _("{} years ago").format(int(years))

    def format_date_as_full(self, dt_utc):
        local_tz = datetime.now().astimezone().tzinfo

        try:
            if isinstance(dt_utc, (int, float)):
                dt_utc = datetime.fromtimestamp(dt_utc, tz=timezone.utc)
            elif isinstance(dt_utc, str):
                dt_utc = datetime.fromisoformat(dt_utc)
            else:
                return "{}".format(dt_utc)
        except Exception:
            return "{}".format(dt_utc)

        try:
            dt_local = dt_utc.astimezone(local_tz)
        except Exception:
            return "{}".format(dt_utc)

        return dt_local.strftime("%d-%m-%Y %H:%M")

    def rating_response_from_server(self, status, response=None, appname=None):
        if status:
            r_type = response.get("response-type", 0)
            if r_type == 10:
                if appname != self.ui_app_name:
                    return
                self.ui_comment_send_button.set_sensitive(True)
                if response["rating"]["status"]:
                    self.set_rating_stars(response["rating"]["rate"]["average"])
                    self.ui_ad_top_avgrate_label.set_text("{:.1f}".format(float(response["rating"]["rate"]["average"])))
                    self.ui_ad_bottom_avgrate_label.set_markup(
                        "<span font='54'><b>{:.1f}</b></span>".format(float(response["rating"]["rate"]["average"])))
                    self.ui_ad_bottom_rate_count_label.set_text(_("{} Ratings").format(response["rating"]["rate"]["count"]))

                    GLib.idle_add(self.set_rating_progressbar, response["rating"]["rate"]["count"],
                                  response["rating"]["rate"]["rates"]["1"], response["rating"]["rate"]["rates"]["2"],
                                  response["rating"]["rate"]["rates"]["3"], response["rating"]["rate"]["rates"]["4"],
                                  response["rating"]["rate"]["rates"]["5"])

                    self.ui_comment_main_stack.set_visible_child_name("done")
                else:
                    self.ui_comment_error_label.set_visible(True)
                    if response["rating"]["flood"]:
                        self.ui_comment_error_label.set_text(_("Please try again soon"))
                    else:
                        self.ui_comment_error_label.set_text(_("Error"))

            elif r_type == 12:
                self.ui_suggest_send_button.set_sensitive(True)
                if response["suggestapp"]["status"]:
                    self.ui_suggest_main_stack.set_visible_child_name("done")
                    self.clear_suggest_dialog()
                else:
                    self.ui_suggest_error_label.set_visible(True)
                    if response["suggestapp"]["flood"]:
                        self.ui_suggest_error_label.set_text("{}".format(_("Please try again soon")))
                    else:
                        self.ui_suggest_error_label.set_markup("{}".format(_("Error")))
        else:
            self.ui_comment_error_label.set_visible(True)
            self.ui_comment_error_label.set_text(_("Error"))
            self.ui_suggest_error_label.set_visible(True)
            self.ui_suggest_error_label.set_text(_("Error"))

    def app_details_from_server(self, status, response=None, appname=None):
        print("app_details_from_server, status: {}".format(status))
        print("app_details_from_server, appname: {}".format(appname))
        print("{}".format(response))

        if status and appname == self.ui_app_name:
            GLib.idle_add(self.ui_ad_top_avgrate_label.set_text,
                "{:.1f}".format(float(response["details"]["rate"]["average"])))

            GLib.idle_add(self.ui_ad_top_download_label.set_text,
                "{}".format(response["details"]["download"]["count"]))

            GLib.idle_add(self.ui_ad_bottom_avgrate_label.set_markup,
                "<span font='54'><b>{:.1f}</b></span>".format(float(response["details"]["rate"]["average"])))

            GLib.idle_add(self.set_rating_stars, response["details"]["rate"]["average"])

            GLib.idle_add(self.ui_ad_bottom_rate_count_label.set_text,
                "{} Ratings".format(response["details"]["rate"]["count"]))

            GLib.idle_add(self.set_rating_progressbar, response["details"]["rate"]["count"],
                          response["details"]["rate"]["rates"]["1"], response["details"]["rate"]["rates"]["2"],
                          response["details"]["rate"]["rates"]["3"], response["details"]["rate"]["rates"]["4"],
                          response["details"]["rate"]["rates"]["5"])

            self.ui_comment_main_stack.set_visible_child_name("main")
            if response["details"]["rate"]["individual"] == 0:
                self.ui_comment_mid_stack.set_visible_child_name("write")
                self.ui_comment_bottom_stack.set_visible_child_name("disclaimer")
                self.ui_comment_send_button.set_sensitive(True)
                self.ui_comment_own = {}
            else:
                self.ui_comment_mid_stack.set_visible_child_name("read")
                self.ui_comment_bottom_stack.set_visible_child_name("info")

                self.ui_comment_own_date_label.set_text("{}".format(self.format_date_as_ago(
                    response["details"]["individual"]["date"])))
                self.ui_comment_own_date_label.set_tooltip_text(self.format_date_as_full(
                    response["details"]["individual"]["date"]))

                self.ui_comment_own_fullname_label.set_text("{}".format(response["details"]["individual"]["author"]))
                self.ui_comment_own_content_label.set_text("{}".format(response["details"]["individual"]["comment"]))
                self.set_comment_own_stars(response["details"]["individual"]["rate"])

                if response["details"]["individual"]["recommentable"]:
                    self.ui_comment_mid_editable_stack.set_visible_child_name("edit")
                    if response["details"]["individual"]["comment"]:
                        self.ui_comment_info_label.set_text("{}".format(
                            _("Your comment is under review.")))
                    else:
                        self.ui_comment_info_label.set_text("{}".format(
                            _("You can also add a comment if you want.")))
                else:
                    self.ui_comment_mid_editable_stack.set_visible_child_name("read")
                    self.ui_comment_info_label.set_text("{}".format(
                        _("You wrote a review about the application before, thank you.")))

                self.ui_comment_own = {"fullname": response["details"]["individual"]["author"],
                                       "comment": response["details"]["individual"]["comment"],
                                       "point": response["details"]["rate"]["individual"]}

    def pardus_comments_from_server(self, status, response=None, appname=None):
        self.Logger.info("pardus_comments_from_server: {} {} {}".format(status, appname, response))
        if status and response and "comments" in response and appname == self.ui_app_name:
            self.ui_ad_more_comment_button.name = "pardus"
            # GLib.idle_add(lambda: self.ui_ad_comments_flowbox.foreach(lambda child: self.ui_ad_comments_flowbox.remove(child)))

            def remove_pardus_rows():
                for child in self.ui_ad_comments_flowbox.get_children():
                    inner = child.get_child().get_children()[0]
                    if inner and inner.name == "pardus":
                        self.ui_ad_comments_flowbox.remove(child)
            GLib.idle_add(remove_pardus_rows)

            response_comment_len = len(response["comments"])
            GLib.idle_add(self.ui_ad_more_comment_button.set_visible, response_comment_len == self.comment_limit)
            GLib.idle_add(self.ui_ad_more_comment_button.set_sensitive, response_comment_len == self.comment_limit)

            for comment in response["comments"]:
                listbox = self.create_comment_widget(comment)
                GLib.idle_add(self.ui_ad_comments_flowbox.insert, listbox, -1)
            GLib.idle_add(self.ui_ad_comments_flowbox.show_all)

            if response_comment_len != self.comment_limit:
                if self.UserSettings.config_sgc:
                    self.ui_ad_more_comment_button.name = "gnome"
                    gdic = {"user_hash": "0000000000000000000000000000000000000000",
                            "app_id": self.get_gnome_desktop_filename_from_app_name(self.ui_app_name),
                            "locale": "tr", "distro": "Pardus", "version": "unknown", "limit": self.gnome_comment_limit}
                    self.GnomeComment.get_comments(self.Server.gnomecommentserver, gdic, self.ui_app_name)

    def gnome_comments_from_server(self, status, response=None, appname=None):
        self.Logger.info("gnome_comments_from_server: {} {} {}".format(status, appname, response))
        if status and response and appname == self.ui_app_name:
            def remove_gnome_rows():
                for child in self.ui_ad_comments_flowbox.get_children():
                    inner = child.get_child().get_children()[0]
                    if inner and inner.name == "gnome":
                        self.ui_ad_comments_flowbox.remove(child)
            GLib.idle_add(remove_gnome_rows)

            response_comment_len = len(response)
            GLib.idle_add(self.ui_ad_more_comment_button.set_visible, response_comment_len == self.gnome_comment_limit)
            GLib.idle_add(self.ui_ad_more_comment_button.set_sensitive, response_comment_len == self.gnome_comment_limit)

            required_keys = ["rating", "user_display", "date_created", "summary", "description", "distro", "version", "review_id"]

            for comment in response:
                if all(key in comment for key in required_keys):
                    if comment["review_id"] not in self.Server.blocked_gnome_reviews:
                        listbox = self.create_comment_widget(comment, True)
                        GLib.idle_add(self.ui_ad_comments_flowbox.insert, listbox, -1)
                    else:
                        self.Logger.info(f"Gnome comment blocked: {comment['review_id']}")
            GLib.idle_add(self.ui_ad_comments_flowbox.show_all)

    def on_ui_ad_more_comment_button_clicked(self, button):
        self.ui_ad_more_comment_button.set_sensitive(False)
        if button.name == "pardus":
            self.comment_limit = self.comment_limit + 10
            self.PardusComment.get_comments(self.Server.serverurl + self.Server.serverparduscomments,
                                            {"mac": self.mac, "app": self.ui_app_name, "limit": self.comment_limit},
                                            self.ui_app_name)
        elif button.name == "gnome":
            self.gnome_comment_limit = self.gnome_comment_limit + 10
            gdic = {"user_hash": "0000000000000000000000000000000000000000",
                    "app_id": self.get_gnome_desktop_filename_from_app_name(self.ui_app_name),
                    "locale": "tr", "distro": "Pardus", "version": "unknown", "limit": self.gnome_comment_limit}
            self.GnomeComment.get_comments(self.Server.gnomecommentserver, gdic, self.ui_app_name)

    def create_comment_widget(self, comment, gnome=False):
        if not gnome:
            if comment["distro"] is None or comment["distro"] == "":
                comment["distro"] = _("unknown")

            if comment["appversion"] is None or comment["appversion"] == "":
                comment["appversion"] = _("unknown")

            distro = comment["distro"]
            app_version = comment["appversion"]
            author = comment["author"]
            date = comment["date"]
            value = comment["value"]
            comment = comment["comment"]

        else:
            distro = comment["distro"]
            app_version = comment["version"]
            author = comment["user_display"]
            date = comment["date_created"]
            value = comment["rating"] / 20
            comment = "{}\n{}".format(comment["summary"], comment["description"])

        label_author = Gtk.Label.new()
        label_author.set_markup("<b>{}</b>".format(author))
        label_author.set_selectable(True)

        label_date = Gtk.Label.new()
        label_date.set_text("{}".format(self.format_date_as_ago(date)))
        label_date.set_tooltip_text("{}".format(self.format_date_as_full(date)))
        label_date.set_selectable(True)

        star_image_1 = Gtk.Image.new_from_icon_name(
            "ps-rating-star-full" if value >= 1 else "ps-rating-star-empty", Gtk.IconSize.BUTTON)
        star_image_2 = Gtk.Image.new_from_icon_name(
            "ps-rating-star-full" if value >= 2 else "ps-rating-star-empty", Gtk.IconSize.BUTTON)
        star_image_3 = Gtk.Image.new_from_icon_name(
            "ps-rating-star-full" if value >= 3 else "ps-rating-star-empty", Gtk.IconSize.BUTTON)
        star_image_4 = Gtk.Image.new_from_icon_name(
            "ps-rating-star-full" if value >= 4 else "ps-rating-star-empty", Gtk.IconSize.BUTTON)
        star_image_5 = Gtk.Image.new_from_icon_name(
            "ps-rating-star-full" if value >= 5 else "ps-rating-star-empty", Gtk.IconSize.BUTTON)

        box_star = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 3)
        box_star.pack_start(star_image_1, False, True, 0)
        box_star.pack_start(star_image_2, False, True, 0)
        box_star.pack_start(star_image_3, False, True, 0)
        box_star.pack_start(star_image_4, False, True, 0)
        box_star.pack_start(star_image_5, False, True, 0)

        box_top = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 8)
        box_top.pack_start(box_star, False, True, 0)
        box_top.pack_start(Gtk.Separator.new(Gtk.Orientation.VERTICAL), False, True, 0)
        box_top.pack_start(label_author, False, True, 0)
        box_top.pack_end(label_date, False, True, 0)

        label_comment = Gtk.Label.new()
        label_comment.set_text("{}".format(comment))
        label_comment.set_selectable(True)
        label_comment.set_line_wrap(True)
        label_comment.set_line_wrap_mode(1)
        label_comment.props.halign = Gtk.Align.START
        label_comment.set_xalign = 0.0

        label_distro = Gtk.Label.new()
        label_distro.set_markup("{}".format(distro))
        label_distro.set_selectable(True)

        label_appversion = Gtk.Label.new()
        label_appversion.set_markup("{}: {}".format(_("App"), app_version))
        label_appversion.set_selectable(True)

        box_bottom = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 8)
        box_bottom.pack_start(label_distro, False, True, 0)
        box_bottom.pack_start(label_appversion, False, True, 0)

        bottom_separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
        bottom_separator.props.valign = Gtk.Align.END
        bottom_separator.set_vexpand(True)
        GLib.idle_add(bottom_separator.get_style_context().add_class, "pardus-software-mostdown-bottom-seperator")

        box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 20)
        box.pack_start(box_top, False, True, 0)
        box.pack_start(label_comment, False, True, 0)
        box.pack_start(box_bottom, False, True, 0)
        box.pack_end(bottom_separator, False, True, 0)
        box.set_margin_start(8)
        box.set_margin_end(8)
        box.set_margin_top(8)

        listbox = Gtk.ListBox.new()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        listbox_row = Gtk.ListBoxRow()
        listbox_row.name = "pardus" if not gnome else "gnome"
        GLib.idle_add(listbox_row.add, box)
        GLib.idle_add(listbox.add, listbox_row)

        GLib.idle_add(listbox.get_style_context().add_class, "pardus-software-listbox-mostdown")

        return listbox

    def round_corners(self, pixbuf, radius):
        width = pixbuf.get_width()
        height = pixbuf.get_height()

        # Create an ARGB surface (with alpha channel)
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(surface)

        # Draw a rounded rectangle path
        # Top-left corner
        ctx.arc(radius, radius, radius, 3.1415, 3.1415 * 1.5)
        # Top-right corner
        ctx.arc(width - radius, radius, radius, 3.1415 * 1.5, 0)
        # Bottom-right corner
        ctx.arc(width - radius, height - radius, radius, 0, 3.1415 * 0.5)
        # Bottom-left corner
        ctx.arc(radius, height - radius, radius, 3.1415 * 0.5, 3.1415)
        ctx.close_path()

        # Clip drawing area to the rounded rectangle
        ctx.clip()

        # Paint the original Pixbuf inside the clipping region
        Gdk.cairo_set_source_pixbuf(ctx, pixbuf, 0, 0)
        ctx.paint()

        # Convert the Cairo surface back to a Pixbuf without color changes
        new_pixbuf = Gdk.pixbuf_get_from_surface(surface, 0, 0, width, height)

        return new_pixbuf

    def app_image_from_server(self, status, pixbuf=None, uri=None, app_name=""):
        self.Logger.info(
            f"app_image_from_server: status: {status}, "
            f"app_name: {app_name}, "
            f"ui_app_name: {self.ui_app_name}, "
            f"pixbuf: {'OK' if pixbuf else pixbuf}, uri: {uri}"
        )

        if status and app_name == self.ui_app_name:
            name = uri.rsplit("/", 1)[-1].split(".", 1)[0]
            original_width = pixbuf.get_width()
            original_height = pixbuf.get_height()
            fixed_height = 256
            image = Gtk.Image.new_from_pixbuf(self.round_corners((pixbuf.scale_simple(
                int(original_width * fixed_height / original_height), fixed_height, GdkPixbuf.InterpType.BILINEAR)), 7))
            image.name = name
            GLib.idle_add(self.ui_ad_image_box.add, image)
            GLib.idle_add(self.ui_ad_image_box.show_all)

            self.add_to_image_popover(pixbuf, uri)
            GLib.idle_add(self.ui_image_stack.show_all)

    def on_ui_image_prev_button_clicked(self, button):
        if not self.image_stack_names:
            return

        self.image_stack_current_index -= 1
        if self.image_stack_current_index < 0:
            self.image_stack_current_index = len(self.image_stack_names) - 1

        name = self.image_stack_names[self.image_stack_current_index]
        self.ui_image_stack.set_visible_child_name(name)

    def on_ui_image_next_button_clicked(self, button):

        if not self.image_stack_names:
            return

        self.image_stack_current_index += 1
        if self.image_stack_current_index >= len(self.image_stack_names):
            self.image_stack_current_index = 0

        name = self.image_stack_names[self.image_stack_current_index]
        self.ui_image_stack.set_visible_child_name(name)

    def on_ui_image_fullscreen_button_clicked(self, button):
        self.imgfullscreen_count += 1
        if self.imgfullscreen_count % 2 == 1:
            self.resize_popover_image(True)
            self.ui_image_resize_image.set_from_icon_name("view-restore-symbolic", Gtk.IconSize.BUTTON)
        else:
            self.resize_popover_image()
            self.ui_image_resize_image.set_from_icon_name("view-fullscreen-symbolic", Gtk.IconSize.BUTTON)

    def on_ui_image_popover_key_press_event(self, widget, event):
        if event.keyval == Gdk.KEY_Left:
            self.on_ui_image_prev_button_clicked(widget)
            return True
        elif event.keyval == Gdk.KEY_Right:
            self.on_ui_image_next_button_clicked(widget)
            return True
        elif event.keyval == Gdk.KEY_f or event.keyval == Gdk.KEY_F:
            self.on_ui_image_fullscreen_button_clicked(widget)
            return True

    def resize_popover_image(self, fullscreen=False):

        size = self.MainWindow.get_size()

        if not fullscreen:
            basewidth = size.width - size.width / 3
            self.ui_image_popover.set_size_request(0, 0)
            self.ui_image_resize_image.set_from_icon_name("view-fullscreen-symbolic", Gtk.IconSize.BUTTON)
        else:
            basewidth = size.width - 125
            self.ui_image_popover.set_size_request(size.width, size.height)
            self.ui_image_resize_image.set_from_icon_name("view-restore-symbolic", Gtk.IconSize.BUTTON)

        for name in self.image_stack_names:
            image = self.ui_image_stack.get_child_by_name(name)

            pixbuf = self.image_original_pixbufs.get(name)
            if pixbuf is None:
                continue

            orig_w = pixbuf.get_width()
            orig_h = pixbuf.get_height()

            hsize = (basewidth * orig_h) / orig_w

            if hsize + 110 > size.height:
                hsize = size.height - 110
                basewidth = (hsize * orig_w) / orig_h

            scaled = pixbuf.scale_simple(int(basewidth), int(hsize), GdkPixbuf.InterpType.BILINEAR)

            image.set_from_pixbuf(scaled)

    def on_ui_image_close_button_clicked(self, button):
        self.ui_image_popover.popdown()

    def installedapps_filter_function(self, row):
        search_entry_text = self.ui_top_searchentry.get_text().lower()
        app = row.get_children()[0].get_children()[0].name

        name = app.get("name", "")
        description = app.get("description", "")
        keywords = app.get("keywords", "")
        executable = app.get("executable", "")

        if self.searching:
            if any(search_entry_text in field.lower() for field in [name, description, keywords, executable]):
                return True
        else:
            return True

        return False

    def pardusapps_filter_function(self, row):
        app = row.get_children()[0].get_children()[0].name
        appname, details = next(iter(app.items()))

        categories = {cat[self.user_locale] for cat in details.get("category", [])}

        search_entry_text = self.ui_top_searchentry.get_text().lower()

        pn_en = details.get("prettyname", {}).get("en", "")
        pn_tr = details.get("prettyname", {}).get("tr", "")
        desc_en = details.get("description", {}).get("en", "")
        desc_tr = details.get("description", {}).get("tr", "")

        if self.searching:
            if any(search_entry_text in field.lower() for field in [appname, pn_en, pn_tr, desc_en, desc_tr]):
                return True
        else:
            if self.current_category in {"all", "tümü"} or self.current_category in categories:
                return True

        return False

    def on_ui_pardusapps_combobox_changed(self, combo_box):
        if combo_box.get_active() == 0:  # sort by name
            self.apps = dict(sorted(self.apps.items(),
                                    key=lambda item: locale.strxfrm(item[1]["prettyname"][self.user_locale])))
            GLib.idle_add(self.set_applications)
        elif combo_box.get_active() == 1:  # sort by download
            self.apps = dict(sorted(
                self.apps.items(),
                key=lambda item: (item[1]["download"], item[1]["rate_average"]),
                reverse=True
            ))
            GLib.idle_add(self.set_applications)
        elif combo_box.get_active() == 2:  # sort by popularity
            self.apps = dict(sorted(
                self.apps.items(),
                key=lambda item: (item[1].get("popularity", item[1]["rate_average"]), item[1]["download"]),
                reverse=True
            ))
            GLib.idle_add(self.set_applications)
        elif combo_box.get_active() == 3:  # sort by last added
            self.apps = dict(sorted(
                self.apps.items(),
                key=lambda item: datetime.strptime(item[1]["date"], "%d-%m-%Y %H:%M"),
                reverse=True
            ))
            GLib.idle_add(self.set_applications)

    def on_ui_upgradables_combobox_changed(self, combo_box):
        if combo_box.get_active() == 0:  # sort by name
            self.upgradables = dict(sorted(self.upgradables.items(),
                                           key=lambda item: locale.strxfrm(item[1]["prettyname"][self.user_locale])))
            GLib.idle_add(self.set_upgradables)
        elif combo_box.get_active() == 1:  # sort by download
            self.upgradables = dict(sorted(
                self.upgradables.items(),
                key=lambda item: (item[1]["download"], item[1]["rate_average"]),
                reverse=True
            ))
            GLib.idle_add(self.set_upgradables)
        elif combo_box.get_active() == 2:  # sort by popularity
            self.upgradables = dict(sorted(
                self.upgradables.items(),
                key=lambda item: (item[1].get("popularity", item[1]["rate_average"]), item[1]["download"]),
                reverse=True
            ))
            GLib.idle_add(self.set_upgradables)
        elif combo_box.get_active() == 3:  # sort by last added
            self.upgradables = dict(sorted(
                self.upgradables.items(),
                key=lambda item: datetime.strptime(item[1]["date"], "%d-%m-%Y %H:%M"),
                reverse=True
            ))
            GLib.idle_add(self.set_upgradables)

    def on_ui_myapps_combobox_changed(self, combo_box):
        if combo_box.get_active() == 0:  # sort by name
            GLib.idle_add(self.set_myapps)
        elif combo_box.get_active() == 1:  # sort by download
            GLib.idle_add(self.set_myapps, True)

    def on_ui_header_queue_button_clicked(self, button):
        self.ui_right_stack_navigate_to("queue")

    def remove_from_queue_clicked(self, button):
        for row in self.QueueListBox:
            if row.get_children()[0].name == button.name:
                if row.get_index() != 0:
                    self.QueueListBox.remove(row)
                    # removing from queue list too
                    index = next((index for (index, app) in enumerate(self.queue) if app["name"] == button.name), None)
                    self.queue.pop(index)

    def add_to_myapps_ui(self, app, du=False):

        listbox = self.create_myapp_widget(app, du=du)
        GLib.idle_add(self.ui_installedapps_flowbox.insert, listbox, -1)

    def remove_from_myapps_popup(self, button):
        self.Logger.info("remove_from_myapps_popup {}".format(button.name))

        self.ui_myapp_pop_toremove_box.set_visible(False)
        self.ui_myapp_pop_toinstall_box.set_visible(False)
        self.ui_myapp_pop_broken_box.set_visible(False)
        self.ui_myapp_pop_fsize_box.set_visible(False)
        self.ui_myapp_pop_dsize_box.set_visible(False)
        self.ui_myapp_pop_isize_box.set_visible(False)

        self.ui_myapp_pop_spinner.start()
        self.ui_myapp_pop_stack.set_visible_child_name("spinner")

        self.ui_myapp_details_popover.set_relative_to(button)
        self.ui_myapp_details_popover.popup()

        threading.Thread(target=self.myappsdetail_popup_worker_thread, args=(button.name, True,), daemon=True).start()

    def open_from_myapps(self, button):
        self.Logger.info("Opening {}".format(button.name))
        self.launch_desktop_file(button.name)

    def on_ui_myapp_pop_uninstall_button_clicked(self, button):
        importants = [i for i in self.important_packages if i in self.myapp_toremove_list]
        if importants:
            self.ui_myapp_pop_stack.set_visible_child_name("disclaimer")
            self.ui_myapp_pop_disclaimer_remove_label.set_markup("{}".format(", ".join(importants)))
        else:
            self.Logger.info("not important package")
            self.ui_myapps_uninstall()

    def on_ui_myapp_pop_accept_disclaimer_clicked(self, button):
        self.ui_myapp_pop_stack.set_visible_child_name("details")
        self.ui_myapps_uninstall()

    def on_ui_myapp_pop_cancel_disclaimer_clicked(self, button):
        self.ui_myapp_pop_stack.set_visible_child_name("details")

    def ui_myapps_uninstall(self):
        self.ui_header_queue_button.set_visible(True)
        self.ui_queue_stack.set_visible_child_name("inprogress")

        self.ui_myapp_pop_uninstall_button.set_sensitive(False)

        self.queue.append({"name": self.myapp_toremove, "command": self.myapp_toremove,
                           "desktop_id": self.myapp_toremove_desktop, "upgrade": False})
        self.add_to_queue_ui(self.myapp_toremove, icon_name=self.myapp_toremove_icon)
        if not self.inprogress:
            self.action_package(self.myapp_toremove, self.myapp_toremove, self.myapp_toremove_desktop)
            self.inprogress = True
            self.Logger.info("action_package app: {}, command: {}, desktop_id: {}, upgrade: {}".format(
                self.myapp_toremove, self.myapp_toremove, self.myapp_toremove_desktop, False))

    def myapps_filter_func(self, row):
        # app info defined in uninstall button so getting this widget
        myapp_name = row.get_children()[0].get_children()[3].name
        search = self.myapps_searchentry.get_text().lower()
        if search in myapp_name["name"].lower() or search in myapp_name["description"].lower() or \
                search in myapp_name["keywords"].lower() or search in myapp_name["executable"].lower():
            return True

    def installedapps_sort_func(self, row1, row2):
        # get app name from uninstal button widget name
        return locale.strxfrm(row1.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[4].name["name"]) > locale.strxfrm(
            row2.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[4].name["name"])

    def on_ui_top_searchentry_focus_in_event(self, widget, event):
        print("on_ui_top_searchentry_focus_in_event")
        self.searching = True

        if self.ui_right_stack.get_visible_child_name() == "installed":
            self.ui_installedapps_flowbox.invalidate_filter()
        else:
            self.ui_right_stack_navigate_to("apps")
            self.ui_pardusapps_title_stack.set_visible_child_name("search")
            self.ui_repotitle_box.set_visible(True)
            self.ui_repoapps_flowbox.set_visible(True)

            self.ui_leftcats_listbox.unselect_all()
            self.ui_leftinstalled_listbox.unselect_all()
            self.ui_leftupdates_listbox.unselect_all()

            self.ui_pardusapps_flowbox.invalidate_filter()

    def on_ui_top_searchentry_search_changed(self, entry_search):
        print("on_top_searchentry_search_changed")
        self.searching = True

        if self.ui_right_stack.get_visible_child_name() == "installed":
            self.ui_installedapps_flowbox.invalidate_filter()
        else:
            self.ui_right_stack_navigate_to("apps")
            self.ui_pardusapps_title_stack.set_visible_child_name("search")

            self.ui_pardusapps_flowbox.invalidate_filter()

            text = entry_search.get_text().strip().lower()

            self.ui_searchterm_label.set_text(_("Results for {}").format(text))

            if hasattr(self, "_repo_search_cancel_flag"):
                self._repo_search_cancel_flag = True

            self._repo_search_cancel_flag = False

            GLib.idle_add(self._clear_repo_results)

            if len(text) < 3:
                return

            GLib.idle_add(self._start_repo_search, text)

    def _clear_repo_results(self):
        if self.ui_repoapps_flowbox:
            for row in list(self.ui_repoapps_flowbox.get_children()):
                self.ui_repoapps_flowbox.remove(row)

    def _start_repo_search(self, text):
        if hasattr(self, "_repo_search_cancel_flag"):
            self._repo_search_cancel_flag = True

        if len(text) < 3:
            return

        self._repo_search_cancel_flag = False

        repo_list = self.Package.load_repo_packages()

        GLib.idle_add(self._clear_repo_results)

        self._repo_search_text = text
        self._repo_startswith = []
        self._repo_contains = []
        self._repo_results = []
        self._repo_matched_set = set()
        self._repo_phase = "startswith"

        self._repo_iter = iter(repo_list)

        GLib.idle_add(self._repo_search_step)

    def _repo_search_step(self):
        if self._repo_search_cancel_flag:
            return False

        text = self._repo_search_text
        CHUNK = 400

        try:
            if self._repo_phase == "startswith":
                for _ in range(CHUNK):
                    pkg = next(self._repo_iter)
                    name = pkg.lower()
                    if name.startswith(text):
                        if pkg not in self._repo_matched_set:
                            self._repo_startswith.append(pkg)
                            self._repo_matched_set.add(pkg)

                            if len(self._repo_startswith) >= 6:
                                return self._repo_search_finish()
                return True

            elif self._repo_phase == "contains":
                for _ in range(CHUNK):
                    pkg = next(self._repo_iter)
                    name = pkg.lower()
                    if pkg in self._repo_matched_set:
                        continue
                    if text in name:
                        self._repo_contains.append(pkg)
                        self._repo_matched_set.add(pkg)

                        if len(self._repo_startswith) + len(self._repo_contains) >= 6:
                            return self._repo_search_finish()
                return True

        except StopIteration:
            if self._repo_phase == "startswith":
                repo_list = self.Package.load_repo_packages()
                self._repo_iter = iter(repo_list)
                self._repo_phase = "contains"

                return True
            else:
                return self._repo_search_finish()

        return True

    def _repo_search_finish(self):
        if self._repo_search_cancel_flag:
            return False

        final_list = list(self._repo_startswith)

        if len(final_list) < 6:
            need = 6 - len(final_list)
            final_list += self._repo_contains[:need]

        for pkg in final_list:
            widget = self.create_app_widget(pkg, repo_app=True)
            GLib.idle_add(self.ui_repoapps_flowbox.add, widget)

        GLib.idle_add(self.ui_repoapps_flowbox.show_all)
        GLib.idle_add(self.ui_repotitle_box.set_visible, final_list)

        self._repo_startswith = []
        self._repo_contains = []
        self._repo_matched_set = set()
        self._repo_phase = None
        return False

    def on_ui_top_searchentry_activate(self, entry):
        print("on_ui_top_searchentry_activate")

    def on_ui_top_searchentry_icon_press(self, entry, icon_pos, event):
        print("on_ui_top_searchentry_icon_press")

    def on_main_key_press_event(self, widget, event):
        if self.mainstack.get_visible_child_name() == "home":
            if self.homestack.get_visible_child_name() == "pardushome":

                entry = self.ui_top_searchentry
                buf = entry.get_buffer()

                if entry.is_focus():
                    return False

                if event.string.isdigit() or event.string.isalpha():
                    buf.delete_text(0, -1)
                    entry.grab_focus()
                    buf.insert_text(0, event.string, -1)
                    entry.set_position(-1)
                    return True

        return False

    def on_ui_queue_goto_discover_button_clicked(self, button):
        self.searching = False
        self.ui_leftupdates_listbox.unselect_all()
        self.ui_leftinstalled_listbox.unselect_all()
        self.ui_right_stack_navigate_to("discover")
        self.ui_leftcats_listbox.select_row(self.ui_leftcats_listbox.get_row_at_index(0))

    def on_menu_settings_clicked(self, button):
        self.ui_headermenu_button.grab_focus()
        self.ui_right_stack_navigate_to("settings")
        self.ui_headermenu_popover.popdown()

        self.ui_leftcats_listbox.unselect_all()
        self.ui_leftinstalled_listbox.unselect_all()
        self.ui_leftupdates_listbox.unselect_all()

        self.UserSettings.readConfig()

        self.ui_settings_animations_switch.set_state(self.UserSettings.config_ea)
        self.ui_settings_available_switch.set_state(self.UserSettings.config_saa)
        self.ui_settings_gcomments_switch.set_state(self.UserSettings.config_sgc)
        self.ui_settings_dark_switch.set_state(self.UserSettings.config_udt)
        self.ui_settings_update_switch.set_state(self.UserSettings.config_aptup)

        self.control_groups()
        self.set_cache_size()

        self.set_settings_tooltips()

    def on_ui_back_button_clicked(self, button):
        # If there is no history, there is nowhere to go back to.
        if not self.stack_history:
            return

        # Get the previous page from history.
        previous = self.stack_history.pop()

        # Navigate back without recording this transition in history.
        # Using navigate_to ensures the back button visibility is updated.
        self.ui_right_stack_navigate_to(previous, record=False)

    def ui_right_stack_navigate_to(self, page_name, record=True):
        current = self.ui_right_stack.get_visible_child_name()

        # Do nothing if trying to navigate to the current page.
        if current == page_name:
            return

        # When moving forward (record=True), push the current page into history
        # unless it's already the last entry (prevents duplicates).
        if record and current:
            if not self.stack_history or self.stack_history[-1] != current:
                self.stack_history.append(current)

        # Perform the actual page switch.
        # Back navigation sets record=False to avoid polluting history.
        self.ui_right_stack.set_visible_child_name(page_name)

        # Update back button availability after the page change.
        self.update_back_button_visibility()

    def update_back_button_visibility(self):
        current = self.ui_right_stack.get_visible_child_name()

        # Disable the back button when on the root page (discover).
        self.ui_back_button.set_sensitive(current != "discover")

    def set_cache_size(self):
        cache_size = self.Utils.get_path_size(self.Server.cachedir)
        self.Logger.info("{} : {} bytes".format(self.Server.cachedir, cache_size))
        self.ui_settings_cache_size_label.set_markup("<b>({})</b>".format(self.Package.beauty_size(cache_size)))

    def control_groups(self):
        try:
            self.usergroups = [g.gr_name for g in grp.getgrall() if self.UserSettings.username in g.gr_mem]
        except Exception as e:
            self.Logger.exception("control_groups: {}".format(e))
            self.usergroups = []

        if self.usergroups:
            self.ui_settings_password_button.set_visible(True)
            if "pardus-software" in self.usergroups:
                self.ui_settings_password_button.set_label(_("Deactivate"))
                self.set_button_class(self.ui_settings_password_button, 1)
            else:
                self.ui_settings_password_button.set_label(_("Activate"))
                self.set_button_class(self.ui_settings_password_button, 0)
            self.ui_settings_password_button.set_sensitive(True)
        else:
            self.ui_settings_password_button.set_visible(False)

    def set_settings_tooltips(self):
        if self.UserSettings.config_forceaptuptime != 0:
            self.ui_settings_update_label.set_tooltip_text(
                "{} {} {}\n{}: {}\n\n{} ( {} )".format(
                    _("Allows the package manager cache to be updated again on the next application start if"),
                    self.displayTime(self.Server.aptuptime),
                    _("have passed since the last successful update."),
                    _("Last successful update time is"),
                    datetime.fromtimestamp(self.UserSettings.config_lastaptup),
                    _("The value in your configuration file is used as the wait time."),
                    self.displayTime(self.UserSettings.config_forceaptuptime)
                ))
        else:
            self.ui_settings_update_label.set_tooltip_text("{} {} {}\n{}: {}".format(
                _("Allows the package manager cache to be updated again on the next application start if"),
                self.displayTime(self.Server.aptuptime),
                _("have passed since the last successful update."),
                _("Last successful update time is"),
                datetime.fromtimestamp(self.UserSettings.config_lastaptup)
            ))

    def on_menu_about_clicked(self, button):
        self.ui_headermenu_popover.popdown()
        self.aboutdialog.run()
        self.aboutdialog.hide()

    def on_ui_trend_seeall_eventbox_button_release_event(self, widget, event):
        self.ui_right_stack_navigate_to("trendapps")

    def on_ui_mostdown_seeall_eventbox_button_release_event(self, widget, event):
        self.ui_right_stack_navigate_to("mostdownapps")

    def on_ui_recent_seeall_eventbox_button_release_event(self, widget, event):
        self.ui_right_stack_navigate_to("recentapps")

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

    def on_ui_settings_dark_switch_state_set(self, switch, state):
        user_config_dark = self.UserSettings.config_udt
        if state != user_config_dark:
            self.Logger.info("Updating dark theme state as {}".format(state))
            self.UserSettings.writeConfig(self.UserSettings.config_usi, self.UserSettings.config_ea,
                                          self.UserSettings.config_saa, self.UserSettings.config_sera,
                                          self.UserSettings.config_icon, self.UserSettings.config_sgc, state,
                                          self.UserSettings.config_aptup, self.UserSettings.config_lastaptup,
                                          self.UserSettings.config_forceaptuptime)
            Gtk.Settings.get_default().props.gtk_application_prefer_dark_theme = state
            self.usersettings()

    def on_ui_settings_animations_switch_state_set(self, switch, state):
        user_config_animations = self.UserSettings.config_ea
        if state != user_config_animations:
            self.Logger.info("Updating animations state as {}".format(state))
            self.UserSettings.writeConfig(self.UserSettings.config_usi, state, self.UserSettings.config_saa,
                                          self.UserSettings.config_sera, self.UserSettings.config_icon,
                                          self.UserSettings.config_sgc, self.UserSettings.config_udt,
                                          self.UserSettings.config_aptup, self.UserSettings.config_lastaptup,
                                          self.UserSettings.config_forceaptuptime)
            self.usersettings()
            self.setAnimations()

    def on_ui_settings_gcomments_switch_state_set(self, switch, state):
        user_config_gcomments = self.UserSettings.config_sgc
        if state != user_config_gcomments:
            self.Logger.info("Updating gnome comments state as {}".format(state))
            self.UserSettings.writeConfig(self.UserSettings.config_usi, self.UserSettings.config_ea,
                                          self.UserSettings.config_saa, self.UserSettings.config_sera,
                                          self.UserSettings.config_icon, state, self.UserSettings.config_udt,
                                          self.UserSettings.config_aptup, self.UserSettings.config_lastaptup,
                                          self.UserSettings.config_forceaptuptime)
            self.usersettings()

    def on_ui_settings_update_switch_state_set(self, switch, state):
        user_config_update = self.UserSettings.config_aptup
        if state != user_config_update:
            self.Logger.info("Updating auto apt update state as {}".format(state))
            self.UserSettings.writeConfig(self.UserSettings.config_usi, self.UserSettings.config_ea,
                                          self.UserSettings.config_saa, self.UserSettings.config_sera,
                                          self.UserSettings.config_icon, self.UserSettings.config_sgc,
                                          self.UserSettings.config_udt, state,
                                          self.UserSettings.config_lastaptup, self.UserSettings.config_forceaptuptime)
            self.usersettings()

    def on_ui_settings_available_switch_state_set(self, switch, state):
        user_config_available = self.UserSettings.config_saa
        if state != user_config_available:
            self.Logger.info("Updating show available apps state")
            self.UserSettings.writeConfig(self.UserSettings.config_usi, self.UserSettings.config_ea, state,
                                          self.UserSettings.config_sera, self.UserSettings.config_icon,
                                          self.UserSettings.config_sgc, self.UserSettings.config_udt,
                                          self.UserSettings.config_aptup, self.UserSettings.config_lastaptup,
                                          self.UserSettings.config_forceaptuptime)
            self.usersettings()
            self.set_available_apps(available=state)
            GLib.idle_add(self.set_applications)

    def on_ui_settings_cache_button_clicked(self, button):
        state, message = self.Server.delete_cache()
        if state:
            self.ui_settings_cache_button.set_sensitive(False)
            self.ui_settings_cache_button.set_label(_("Cleared"))
            self.ui_settings_cache_info_label.set_markup(_("Cache files cleared, please close and reopen the application"))
        else:
            self.ui_settings_cache_button.set_sensitive(True)
            self.ui_settings_cache_button.set_label(_("Error"))
            self.ui_settings_cache_info_label.set_markup("{}".format(message))
        self.set_cache_size()

    def on_ui_settings_password_button_clicked(self, button):
        self.ui_settings_password_button.set_sensitive(False)
        self.ui_settings_password_info_label.set_text("")
        self.grouperrormessage = ""
        if "pardus-software" in self.usergroups:
            command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Group.py", "del",
                       self.UserSettings.username]
        else:
            command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Group.py", "add",
                       self.UserSettings.username]
        self.group_process(command)

    def on_ui_ad_image_button_press(self, widget, event):
        # Detect input device type (mouse/touchpad vs touchscreen)
        source = event.get_source_device().get_source()
        self.ui_ad_image_is_touch = (source == Gdk.InputSource.TOUCHSCREEN)

        # Only treat Mouse/Touchpad left button as valid drag start
        if not self.ui_ad_image_is_touch and event.button != 1:
            return

        # Start drag
        self.ui_ad_image_dragging = True
        self.ui_ad_image_last_x = event.x
        self.ui_ad_image_total_drag = 0

    def on_ui_ad_image_mouse_drag(self, widget, event):
        if self.ui_ad_image_dragging:
            # Get scrollbar adjustment
            adj = self.ui_ad_image_scrolledwindow.get_hadjustment()
            # Calculate move difference
            dx = self.ui_ad_image_last_x - event.x

            # Scroll horizontally
            adj.set_value(adj.get_value() + dx)

            # Update total drag distance
            self.ui_ad_image_total_drag += abs(dx)
            self.ui_ad_image_last_x = event.x

    def on_ui_ad_image_button_release(self, widget, event):
        def get_clicked_image(event):
            # Get horizontal scroll offset
            adj = self.ui_ad_image_scrolledwindow.get_hadjustment()
            scroll_x = adj.get_value()

            # Convert event.x to box coordinate system
            # (ScrolledWindow → Box)
            x_in_box = scroll_x + event.x

            # Iterate over children of ui_ad_image_box
            for child in self.ui_ad_image_box.get_children():
                # Skip non-image widgets
                if not isinstance(child, Gtk.Image):
                    continue

                # Get widget allocation (position & size)
                alloc = child.get_allocation()

                # Check if click is inside this image
                if x_in_box >= alloc.x and x_in_box <= alloc.x + alloc.width:
                    return child  # Found the real clicked image

            return None  # Empty area clicked

        # if drag wasn't started, ignore
        if not self.ui_ad_image_dragging:
            return

        # stop dragging now
        self.ui_ad_image_dragging = False

        # Detect which image was clicked
        clicked_image = get_clicked_image(event)
        if clicked_image is None:
            return  # clicked empty area, do nothing

        # touchscreen
        if self.ui_ad_image_is_touch:
            if self.ui_ad_image_total_drag < self.ui_ad_image_drag_touch_threshold:
                self.Logger.info("Fullscreen Image (Touchscreen)")
                clicked_image_name = clicked_image.name
                if clicked_image_name in self.image_stack_names:
                    self.image_stack_current_index = self.image_stack_names.index(clicked_image_name)
                self.ui_image_stack.set_visible_child_name(clicked_image_name)
                self.imgfullscreen_count = 0
                self.resize_popover_image()
                self.ui_image_popover.popup()
            return

        # mouse or touchpad
        if event.button == 1 and self.ui_ad_image_total_drag < self.ui_ad_image_drag_threshold:
            self.Logger.info("Fullscreen Image (Mouse or Touchpad)")
            clicked_image_name = clicked_image.name
            if clicked_image_name in self.image_stack_names:
                self.image_stack_current_index = self.image_stack_names.index(clicked_image_name)
            self.ui_image_stack.set_visible_child_name(clicked_image_name)
            self.imgfullscreen_count = 0
            self.resize_popover_image()
            self.ui_image_popover.popup()

    def on_ui_write_comment_button_clicked(self, button):
        self.ui_comment_dialog.run()
        self.ui_comment_dialog.hide()

    def on_ui_comment_close_button_clicked(self, button):
        self.ui_comment_dialog.hide()

    def on_ui_comment_star_button_press_event(self, widget, event):
        star = int(widget.get_name())
        self.set_comment_stars(star)

    def on_ui_comment_own_edit_button_clicked(self, button):
        self.ui_comment_mid_stack.set_visible_child_name("write")
        self.ui_comment_bottom_stack.set_visible_child_name("disclaimer")
        self.ui_comment_send_button.set_sensitive(True)
        if self.ui_comment_own:
            self.ui_comment_fullname_entry.set_text(self.ui_comment_own["fullname"])
            start, end = self.ui_comment_content_textbuffer.get_bounds()
            self.ui_comment_content_textbuffer.delete(start, end)
            self.ui_comment_content_textbuffer.insert(
                self.ui_comment_content_textbuffer.get_end_iter(),
                "{}".format(self.ui_comment_own["comment"]))
            self.set_comment_stars(self.ui_comment_own["point"])

    def on_ui_comment_send_button_clicked(self, button):
        author = self.ui_comment_fullname_entry.get_text().strip()
        start, end = self.ui_comment_content_textbuffer.get_bounds()
        comment = self.ui_comment_content_textbuffer.get_text(start, end, False).strip()
        value = self.comment_star_point
        if value == 0 or comment == "" or author == "":
            self.ui_comment_error_label.set_visible(True)
            self.ui_comment_error_label.set_text(_("All fields must be filled."))
        else:
            # installed = self.Package.isinstalled(self.ui_app_name)
            # if installed is None:
            #     installed = False
            version = self.Package.installed_version(self.ui_app_name)
            if version is None:
                version = ""
            dic = {"mac": self.mac, "author": author, "comment": comment, "value": value, "app": self.ui_app_name,
                   "installed": True, "appversion": version, "distro": self.user_distro_full,
                   "justrate": False}
            try:
                self.AppRequest.send(self.Server.serverurl + self.Server.serversendrate, dic, self.ui_app_name)
                self.ui_comment_send_button.set_sensitive(False)
            except Exception as e:
                self.ui_comment_error_label.set_visible(True)
                self.ui_comment_error_label.set_text(f"{e}")

    def on_ui_comment_content_textbuffer_insert_text(self, buffer, location, text, length):
        max_chars = 500
        current_len = buffer.get_char_count()
        new_len = len(text)
        if current_len + new_len > max_chars:
            GObject.signal_stop_emission_by_name(buffer, "insert-text")
            remaining = max_chars - current_len
            if remaining > 0:
                buffer.insert(location, text[:remaining])

    def on_ui_suggestapp_eventbox_button_press_event(self, widget, event):
        self.ui_suggest_main_stack.set_visible_child_name("main")
        self.ui_suggest_dialog.run()
        self.ui_suggest_dialog.hide()

    def on_ui_suggest_close_button_clicked(self, button):
        self.ui_suggest_dialog.hide()

    def on_ui_suggest_send_button_clicked(self, button):
        app_name = self.ui_suggest_appname_entry.get_text().strip()
        app_web = self.ui_suggest_appweb_entry.get_text().strip()
        user_name = self.ui_suggest_username_entry.get_text().strip()
        user_mail = self.ui_suggest_usermail_entry.get_text().strip()
        start, end = self.ui_suggest_why_textbuffer.get_bounds()
        why = self.ui_suggest_why_textbuffer.get_text(start, end, False).strip()

        if app_name == "" or app_web == "" or user_name == "" or user_mail == "" or why == "":
            self.ui_suggest_error_label.set_visible(True)
            self.ui_suggest_error_label.set_text(_("All fields must be filled."))
        else:

            dic = {"app_name": app_name, "app_web": app_web, "user_name": user_name, "user_mail": user_mail, "why": why,
                   "mac": self.mac, "distro": self.user_distro_full}
            try:
                self.AppRequest.send(self.Server.serverurl + self.Server.serversendsuggest, dic)
                self.ui_suggest_send_button.set_sensitive(False)
            except Exception as e:
                self.ui_suggest_error_label.set_visible(True)
                self.ui_suggest_error_label.set_text(f"{e}")

    def on_ui_suggest_why_textbuffer_insert_text(self, buffer, location, text, length):
        max_chars = 500
        current_len = buffer.get_char_count()
        new_len = len(text)
        if current_len + new_len > max_chars:
            GObject.signal_stop_emission_by_name(buffer, "insert-text")
            remaining = max_chars - current_len
            if remaining > 0:
                buffer.insert(location, text[:remaining])

    def clear_suggest_dialog(self):
        self.ui_suggest_appname_entry.set_text("")
        self.ui_suggest_appweb_entry.set_text("")
        self.ui_suggest_username_entry.set_text("")
        self.ui_suggest_usermail_entry.set_text("")
        self.ui_suggest_error_label.set_text("")
        self.ui_suggest_error_label.set_visible(False)
        start, end = self.ui_suggest_why_textbuffer.get_bounds()
        self.ui_suggest_why_textbuffer.delete(start, end)

    def set_available_apps(self, available):
        self.apps = {
            app: details
            for app, details in self.apps_full.items()
            if (
                    (available and (self.Package.isinstalled(app) is not None or any(
                        code["name"] == self.UserSettings.usercodename for code in details["codename"])))
                    or
                    (not available)
            )
        }

    def on_bottomerrorbutton_clicked(self, button):
        self.bottomrevealer.set_reveal_child(False)

    def on_retrybutton_clicked(self, button):
        self.connection_error_after = False
        self.mainstack.set_visible_child_name("splash")
        p1 = threading.Thread(target=self.worker)
        p1.daemon = True
        p1.start()

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

    def on_bottominterrupthide_button_clicked(self, button):
        self.bottomrevealer.set_reveal_child(False)

    def on_bottomerrordetails_button_clicked(self, button):
        self.bottomerrordetails_popover.popup()

    def on_ui_tryfix_button_clicked(self, button):
        self.ui_tryfix_stack.set_visible_child_name("info")

    def on_ui_tryfix_confirm_button_clicked(self, button):
        command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/SysActions.py",
                   "fixapt"]
        self.ui_tryfix_stack.set_visible_child_name("main")
        self.ui_tryfix_button.set_sensitive(False)
        self.ui_tryfix_spinner.start()
        self.tryfix_vte_process(command)

    def on_ui_tryfix_cancel_button_clicked(self, button):
        self.ui_tryfix_stack.set_visible_child_name("main")

    def on_ui_tryfix_done_button_clicked(self, button):
        GLib.idle_add(self.afterServers)

    def update_vte_color(self, vte):
        style_context = self.MainWindow.get_style_context()
        background_color = style_context.get_background_color(Gtk.StateFlags.NORMAL);
        foreground_color = style_context.get_color(Gtk.StateFlags.NORMAL);
        vte.set_color_background(background_color)
        vte.set_color_foreground(foreground_color)

    def send_downloaded_request(self, appname):
        try:
            installed = self.Package.isinstalled(appname)
            if installed is None:
                installed = False
            version = self.Package.installed_version(appname)
            if version is None:
                version = ""
            dic = {"mac": self.mac, "app": appname, "installed": installed, "appversion": version,
                   "distro": self.user_distro_full}
            self.AppRequest.send(self.Server.serverurl + self.Server.serversenddownload, dic)
        except Exception as e:
            self.Logger.warning("send_downloaded_request Error")
            self.Logger.exception("{}".format(e))

    def control_myapps(self, actionedappname, actionedappdesktop, status, error, cachestatus):
        self.Logger.info("in control_myapps")
        if status == 0 and not error and cachestatus:
            if self.isinstalled:
                if self.isupgrade:
                    return
                self.Logger.info("{} removing from myapps".format(actionedappdesktop))
                desktop_id = actionedappdesktop.rsplit('/', 1)[-1]
                for fbc in self.ui_installedapps_flowbox:
                    # get desktop id from open button widget name
                    if fbc.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].name == desktop_id:
                        if self.ui_myapp_pop_stack.get_visible_child_name() == "details" and actionedappname == self.myapp_toremove:
                            self.Logger.info("in pop_myapp popdown")
                            self.ui_myapp_details_popover.set_relative_to(self.ui_installedapps_flowbox)
                            self.ui_myapp_details_popover.popdown()
                        self.ui_installedapps_flowbox.remove(fbc)
            else:
                self.Logger.info("{} adding to myapps".format(actionedappdesktop))
                valid, dic = self.Package.parse_desktopfile(os.path.basename(actionedappdesktop))
                if valid:
                    self.add_to_myapps_ui(dic)
                    GLib.idle_add(self.ui_installedapps_flowbox.show_all)
                    self.ui_installedapps_flowbox.set_sort_func(self.installedapps_sort_func)
            if self.ui_myapp_pop_stack.get_visible_child_name() == "details" and actionedappname == self.myapp_toremove:
                self.Logger.info("in pop_myapp details status=0")
                self.ui_myapp_pop_uninstall_button.set_sensitive(False)
                self.ui_myapp_details_popover.popdown()
        else:
            if self.ui_myapp_pop_stack.get_visible_child_name() == "details" and actionedappname == self.myapp_toremove:
                self.Logger.info("in pop_myapp details status!=0")
                self.ui_myapp_pop_uninstall_button.set_sensitive(True)

    def notify(self, message_summary="", message_body=""):
        try:
            if Notify.is_initted():
                Notify.uninit()

            if message_summary == "" and message_body == "":
                Notify.init(self.inprogress_app_name)
                if self.isinstalled:
                    notification = Notify.Notification.new("{} {}".format(
                        self.get_pretty_name_from_app_name(self.inprogress_app_name),_("Updated") if self.isupgrade else _("Removed")))
                else:
                    notification = Notify.Notification.new("{} {}".format(
                        self.get_pretty_name_from_app_name(self.inprogress_app_name), _("Installed")))
                try:
                    notification.set_app_icon("pardus-software")
                except AttributeError:
                    notification.set_image_from_pixbuf(
                        Gtk.IconTheme.get_default().load_icon("pardus-software", 64, Gtk.IconLookupFlags(16)))
                except Exception as e:
                    self.Logger.exception("{}".format(e))
            else:
                Notify.init(message_summary)
                notification = Notify.Notification.new(message_summary, message_body, "pardus-software")
            notification.show()
        except Exception as e:
            self.Logger.exception("{}".format(e))

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

    def action_process(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(params, flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_output=True, standard_error=True)
        GLib.io_add_watch(GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.on_action_process_stdout)
        GLib.io_add_watch(GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.on_action_process_stderr)
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, self.on_action_process_exit)

        return pid

    def on_action_process_stdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False

        line = source.readline()
        self.Logger.info("{}".format(line))

        return True

    def on_action_process_stderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False

        line = source.readline()

        self.Logger.info("{}".format(line))

        if "dlstatus" in line:
            percent = line.split(":")[2].split(".")[0]
            self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].set_fraction(int(percent) / 100)
            self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].set_text("{} : {} %".format(_("Downloading"), percent))
            self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[4].set_sensitive(True)
        elif "pmstatus" in line:
            percent = line.split(":")[2].split(".")[0]
            self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].set_fraction(int(percent) / 100)
            if self.isinstalled:
                if self.isupgrade:
                    self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].set_text("{} : {} %".format(_("Upgrading"), percent))
                else:
                    self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].set_text("{} : {} %".format(_("Removing"), percent))
            else:
                self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].set_text("{} : {} %".format(_("Installing"), percent))
            self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[4].set_sensitive(False)
        elif ":" in line and ".deb" in line:
            self.Logger.warning("connection error")
            self.error = True
            self.error_message += line
        elif ":" in line and "dpkg --configure -a" in line:
            self.Logger.warning("dpkg --configure -a error")
            self.error = True
            self.dpkgconferror = True
        elif ":" in line and "/var/lib/dpkg/lock-frontend" in line:
            self.Logger.warning("/var/lib/dpkg/lock-frontend error")
            self.error = True
            self.dpkglockerror = True
            self.dpkglockerror_message += line
        elif "pardus-software-i386-start" in line:
            self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].set_text("{}".format(_("i386 activating")))
        return True

    def on_action_process_exit(self, pid, status):
        self.ui_header_queue_button.set_visible(False)

        if not self.error:
            if status == 0:
                self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].set_fraction(1)
                if self.isinstalled:
                    self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].set_text(_("Removed: 100%"))
                else:
                    self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].set_text(_("Installed: 100%"))
            else:
                self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[0].get_children()[3].set_text(_("Not Completed"))
        else:
            self.errormessage = _("<b><span color='red'>Connection Error!</span></b>")
            if self.dpkglockerror:
                self.errormessage = _("<b><span color='red'>Dpkg Lock Error!</span></b>")
            elif self.dpkgconferror:
                self.errormessage = _("<b><span color='red'>Dpkg Interrupt Error!</span></b>")

        cachestatus = self.Package.updatecache()

        self.Logger.info("Cache Status: {}, Package Cache Status: {}".format(
            cachestatus, self.Package.controlPackageCache(self.inprogress_app_name)))

        if status == 0 and not self.error and cachestatus:
            if self.Package.controlPackageCache(self.inprogress_app_name):
                self.notify()
                self.send_downloaded_request(self.inprogress_app_name)
            else:
                if self.isinstalled:
                    self.notify()

        self.control_myapps(self.inprogress_app_name, self.inprogress_desktop, status, self.error, cachestatus)

        self.update_app_widget_label(self.inprogress_app_name)

        if self.isupgrade:
            self.get_upgradables()
            self.set_upgradables()

        self.Logger.info("Exit Code: {}".format(status))

        self.inprogress = False
        self.inprogress_app_name = ""
        self.inprogress_command = ""
        self.inprogress_desktop = ""

        if len(self.queue) > 0:
            self.queue.pop(0)
            self.ui_queue_flowbox.remove(self.ui_queue_flowbox.get_children()[0])
        if len(self.queue) > 0:
            self.action_package(self.queue[0]["name"], self.queue[0]["command"], self.queue[0]["desktop_id"],
                                self.queue[0]["upgrade"])
            self.Logger.info("action_package app: {}, command: {}, desktop_id: {}, upgrade: {}".format(
                self.queue[0]["name"], self.queue[0]["command"], self.queue[0]["desktop_id"],
                self.queue[0]["upgrade"]))
            progressbar = self.ui_queue_flowbox.get_children()[0].get_children()[0].get_children()[0].get_children()[
                0].get_children()[0].get_children()[3]
            if self.Package.isinstalled(self.inprogress_app_name):
                if self.Package.is_upgradable(self.inprogress_app_name) and self.queue[0]["upgrade"]:
                    progressbar.set_text("{}".format(_("Upgrading")))
                else:
                    progressbar.set_text("{}".format(_("Removing")))
            else:
                progressbar.set_text("{}".format(_("Installing")))
        else:
            self.bottomrevealer.set_reveal_child(False)
            if not self.error:
                self.ui_queue_stack.set_visible_child_name("completed")

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

    def apt_update_process(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(params, flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_output=True, standard_error=True)
        GLib.io_add_watch(GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.on_apt_update_process_stdout)
        GLib.io_add_watch(GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.on_apt_update_process_stderr)
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, self.on_apt_update_process_exit)

        return pid

    def on_apt_update_process_stdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        self.Logger.info("{}".format(line))
        return True

    def on_apt_update_process_stderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        self.Logger.info("{}".format(line))
        return True

    def on_apt_update_process_exit(self, pid, status):
        self.Package.updatecache()
        GLib.idle_add(self.ui_header_aptupdate_spinner.stop)
        GLib.idle_add(self.ui_header_aptupdate_spinner.set_visible, False)
        if status == 0:
            try:
                timestamp = int(datetime.now().timestamp())
            except Exception as e:
                self.Logger.warning("timestamp Error: {}")
                self.Logger.exception("{}".format(e))
                timestamp = 0

            self.UserSettings.writeConfig(self.UserSettings.config_usi, self.UserSettings.config_ea,
                                          self.UserSettings.config_saa, self.UserSettings.config_sera,
                                          self.UserSettings.config_icon, self.UserSettings.config_sgc,
                                          self.UserSettings.config_udt, self.UserSettings.config_aptup,
                                          timestamp, self.UserSettings.config_forceaptuptime)

            old_upgradables = self.upgradables.copy()
            self.get_upgradables()
            if old_upgradables != self.upgradables:
                self.set_upgradables()

            self.auto_apt_update_finished = True

    def group_process(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(params, flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_output=True, standard_error=True)
        GLib.io_add_watch(GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.on_group_process_stdout)
        GLib.io_add_watch(GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.on_group_process_stderr)
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, self.on_group_process_exit)

        return pid

    def on_group_process_stdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        self.Logger.info("on_group_process_stdout - line: {}".format(line))
        return True

    def on_group_process_stderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        self.Logger.info("on_group_process_stderr - line: {}".format(line))
        self.grouperrormessage = line
        return True

    def on_group_process_exit(self, pid, status):
        self.Logger.info("on_group_process_exit - status: {}".format(status))
        self.control_groups()
        if status != 0:
            self.ui_settings_password_info_label.set_markup(
                "<small><span color='red' weight='light'>{}</span></small>".format(self.grouperrormessage))
        else:
            self.ui_settings_password_info_label.set_text("")

    def tryfix_vte_process(self, command):
        if self.tryfix_vteterm:
            self.tryfix_vteterm.get_parent().remove(self.tryfix_vteterm)

        self.tryfix_vteterm = Vte.Terminal()
        self.update_vte_color(self.tryfix_vteterm)
        self.tryfix_vteterm.set_scrollback_lines(-1)
        tryfix_vte_menu = Gtk.Menu()
        tryfix_vte_menu_items = Gtk.MenuItem(label=_("Copy selected text"))
        tryfix_vte_menu.append(tryfix_vte_menu_items)
        tryfix_vte_menu_items.connect("activate", self.on_tryfix_vte_menu_action, self.tryfix_vteterm)
        tryfix_vte_menu_items.show()
        self.tryfix_vteterm.connect_object("event", self.on_tryfix_vte_event, tryfix_vte_menu)
        self.ui_tryfix_vte_sw.add(self.tryfix_vteterm)
        self.tryfix_vteterm.show_all()

        pty = Vte.Pty.new_sync(Vte.PtyFlags.DEFAULT)
        self.tryfix_vteterm.set_pty(pty)
        try:
            self.tryfix_vteterm.spawn_async(
                Vte.PtyFlags.DEFAULT,
                os.environ['HOME'],
                command,
                None,
                GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                None,
                None,
                -1,
                None,
                self.on_tryfix_vte_create_spawn_callback,
                None
            )
        except Exception as e:
            # old version VTE doesn't have spawn_async so use spawn_sync
            self.Logger.exception("{}".format(e))
            self.tryfix_vteterm.connect("child-exited", self.on_tryfix_vte_process_done)
            self.tryfix_vteterm.spawn_sync(
                Vte.PtyFlags.DEFAULT,
                os.environ['HOME'],
                command,
                [],
                GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                None,
                None,
            )

    def on_tryfix_vte_menu_action(self, widget, terminal):
        terminal.copy_clipboard()

    def on_tryfix_vte_event(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            if event.button.button == 3:
                widget.popup_for_device(None, None, None, None, None,
                                        event.button.button, event.time)
                return True
        return False

    def on_tryfix_vte_create_spawn_callback(self, terminal, pid, error, userdata):
        self.tryfix_vteterm.connect("child-exited", self.on_tryfix_vte_process_done)

    def on_tryfix_vte_process_done(self, obj, status):
        self.Logger.info("on_tryfix_vte_process_done: status: {}".format(status))
        self.ui_tryfix_spinner.stop()
        self.ui_tryfix_button.set_sensitive(True)
        if status == 0:
            self.Package = Package()
            if self.Package.updatecache():
                self.ui_tryfix_stack.set_visible_child_name("done")
                self.isbroken = False
                self.Package.getApps()
            else:
                self.ui_tryfix_stack.set_visible_child_name("error")
                self.isbroken = True
                self.Logger.warning("on_tryfix_vte_process_done: Error while updating Cache")

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

    def dpkgconfigure_vte_event(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            if event.button.button == 3:
                widget.popup_for_device(None, None, None, None, None,
                                        event.button.button, event.time)
                return True
        return False

    def dpkgconfigure_vte_menu_action(self, widget, terminal):
        terminal.copy_clipboard()

    def dpkgconfigure_vte_create_spawn_callback(self, terminal, pid, error, userdata):
        self.dpkgconfigure_vteterm.connect("child-exited", self.dpkgconfigure_vte_on_done)

    def dpkgconfigure_vte_on_done(self, terminal, status):
        self.Logger.info("dpkgconfigure_vte_on_done status: {}".format(status))

        self.dpkgconfiguring = False
        self.bottominterrupt_fix_button.set_sensitive(True)
        self.bottominterrupthide_button.set_sensitive(True)
        self.pop_interruptinfo_spinner.set_visible(False)
        self.pop_interruptinfo_spinner.stop()

        if status == 32256:  # operation cancelled | Request dismissed
            self.pop_interruptinfo_label.set_markup("<b>{}</b>".format(_("Error.")))
        else:
            self.pop_interruptinfo_label.set_markup("<b>{}</b>".format(_("Process completed.")))
            self.pop_interruptinfo_ok_button.set_visible(True)
