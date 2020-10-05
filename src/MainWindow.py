#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import os
import threading

import gi

gi.require_version("GLib", "2.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Notify", "0.7")
from gi.repository import GLib, Gtk, GObject, Notify

from Package import Package
from Server import Server


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

        self.categories = ["all", "development", "education", "games", "graphics", "internet", "multimedia", "office",
                           "system", "other"]

        for i in self.categories:

            try:
                caticon = Gtk.Image.new_from_pixbuf(
                    Gtk.IconTheme.get_default().load_icon("applications-" + i, 48, Gtk.IconLookupFlags(16)))
            except:
                if i == "education":
                    caticon = Gtk.Image.new_from_pixbuf(
                        Gtk.IconTheme.get_default().load_icon("applications-science", 48, Gtk.IconLookupFlags(16)))
                elif i == "all":
                    caticon = Gtk.Image.new_from_pixbuf(
                        Gtk.IconTheme.get_default().load_icon("applications-other", 48, Gtk.IconLookupFlags(16)))
                else:
                    caticon = Gtk.Image.new_from_pixbuf(
                        Gtk.IconTheme.get_default().load_icon("gtk-missing-image", 48, Gtk.IconLookupFlags(16)))

            label = Gtk.Label.new()
            label_text = str(i).capitalize()
            label.set_text(" " + label_text)

            grid = Gtk.Grid.new()

            grid.add(caticon)

            grid.attach(label, 1, 0, 3, 1)

            self.HomeCategoryFlowBox.add(grid)

        self.searchbar = self.GtkBuilder.get_object("searchbar")
        self.pardussearchbar = self.GtkBuilder.get_object("pardussearchbar")
        self.reposearchbar = self.GtkBuilder.get_object("reposearchbar")

        self.mainstack = self.GtkBuilder.get_object("mainstack")
        self.homestack = self.GtkBuilder.get_object("homestack")
        self.searchstack = self.GtkBuilder.get_object("searchstack")
        self.dIcon = self.GtkBuilder.get_object("dIcon")
        self.dName = self.GtkBuilder.get_object("dName")
        self.dActionButton = self.GtkBuilder.get_object("dActionButton")

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
        self.menu1.set_label("Menu 1")
        self.menu1.set_image(Gtk.Image.new_from_icon_name('gtk-dialog-question', Gtk.IconSize.BUTTON))
        self.menu2 = self.GtkBuilder.get_object("menu2")
        self.menu2.set_use_stock(False)
        self.menu2.set_label("Menu 2")
        self.menu2.set_image(Gtk.Image.new_from_icon_name('gtk-dialog-question', Gtk.IconSize.BUTTON))

        self.menubackbutton = self.GtkBuilder.get_object("menubackbutton")
        self.menubackbutton.set_sensitive(False)

        self.progresstextlabel = self.GtkBuilder.get_object("progresstextlabel")
        self.topspinner = self.GtkBuilder.get_object("topspinner")

        self.apps = [{'name': '0ad', 'category': 'games', 'prettyname': '0 A.D.'},
                     {'name': 'akis', 'category': 'other', 'prettyname': 'Akis'},
                     {'name': 'alien-arena', 'category': 'games', 'prettyname': 'Alien Arena'},
                     {'name': 'amule', 'category': 'internet', 'prettyname': 'aMule'},
                     {'name': 'android-studio', 'category': 'development', 'prettyname': 'Android Studio'},
                     {'name': 'anjuta', 'category': 'development', 'prettyname': 'Anjuta'},
                     {'name': 'anydesk', 'category': 'system', 'prettyname': 'AnyDesk'},
                     {'name': 'arduino', 'category': 'development', 'prettyname': 'Arduino'},
                     {'name': 'armagetronad', 'category': 'games', 'prettyname': 'Armagetron Advanced'},
                     {'name': 'atom', 'category': 'development', 'prettyname': 'Atom'},
                     {'name': 'atomix', 'category': 'games', 'prettyname': 'Atomix'},
                     {'name': 'audacious', 'category': 'multimedia', 'prettyname': 'Audacious'},
                     {'name': 'audacity', 'category': 'multimedia', 'prettyname': 'Audacity'},
                     {'name': 'baobab', 'category': 'system', 'prettyname': 'Disk Usage Analyzer'},
                     {'name': 'bleachbit', 'category': 'system', 'prettyname': 'BleachBit'},
                     {'name': 'blender', 'category': 'graphics', 'prettyname': 'Blender'},
                     {'name': 'bless', 'category': 'development', 'prettyname': 'Bless Hex Editor'},
                     {'name': 'blobby', 'category': 'games', 'prettyname': 'Blobby Volley 2'},
                     {'name': 'boswars', 'category': 'games', 'prettyname': 'Bos Wars'},
                     {'name': 'brasero', 'category': 'multimedia', 'prettyname': 'Brasero CD/DVD Creator'},
                     {'name': 'calibre', 'category': 'office', 'prettyname': 'calibre'},
                     {'name': 'cheese', 'category': 'multimedia', 'prettyname': 'Cheese'},
                     {'name': 'chessx', 'category': 'games', 'prettyname': 'ChessX'},
                     {'name': 'chromium', 'category': 'internet', 'prettyname': 'Chromium'},
                     {'name': 'clamtk', 'category': 'system', 'prettyname': 'ClamTk'},
                     {'name': 'code', 'category': 'development', 'prettyname': 'Visual Studio Code'},
                     {'name': 'codeblocks', 'category': 'development', 'prettyname': 'Code::Blocks IDE'},
                     {'name': 'darktable', 'category': 'graphics', 'prettyname': 'Darktable'},
                     {'name': 'deepin-movie', 'category': 'multimedia', 'prettyname': 'Deepin Movie'},
                     {'name': 'deepin-music', 'category': 'multimedia', 'prettyname': 'Deepin Music'},
                     {'name': 'deepin-terminal', 'category': 'system', 'prettyname': 'Deepin Terminal'},
                     {'name': 'deja-dup', 'category': 'system', 'prettyname': 'Deja Dup Backup Monitor'},
                     {'name': 'discord', 'category': 'internet', 'prettyname': 'Discord'},
                     {'name': 'diyanet-cocuktakvim', 'category': 'other', 'prettyname': 'Diyanet Çocuk Takvimi'},
                     {'name': 'diyanet-namazvaktim', 'category': 'other', 'prettyname': 'Diyanet Namaz Vaktim'},
                     {'name': 'drawing', 'category': 'graphics', 'prettyname': 'Drawing'},
                     {'name': 'driconf', 'category': 'system', 'prettyname': '3D Acceleration'},
                     {'name': 'dropbox', 'category': 'internet', 'prettyname': 'Dropbox'},
                     {'name': 'emacs24', 'category': 'office', 'prettyname': 'GNU Emacs 24 (GUI)'},
                     {'name': 'entangle', 'category': 'graphics', 'prettyname': 'Entangle'},
                     {'name': 'eog', 'category': 'graphics', 'prettyname': 'Eye of GNOME'},
                     {'name': 'epiphany', 'category': 'games', 'prettyname': 'Epiphany'},
                     {'name': 'epiphany-browser', 'category': 'internet', 'prettyname': 'Epiphany Browser'},
                     {'name': 'eric', 'category': 'internet', 'prettyname': 'Eric python IDE'},
                     {'name': 'eureka', 'category': 'games', 'prettyname': 'Eureka DOOM Editor'},
                     {'name': 'evince', 'category': 'office', 'prettyname': 'Evince'},
                     {'name': 'evolution', 'category': 'internet', 'prettyname': 'Evolution'},
                     {'name': 'ferdi', 'category': 'internet', 'prettyname': 'Ferdi'},
                     {'name': 'filelight', 'category': 'system', 'prettyname': 'Filelight'},
                     {'name': 'filezilla', 'category': 'internet', 'prettyname': 'FileZilla'},
                     {'name': 'firefox-esr', 'category': 'internet', 'prettyname': 'Firefox Esr'},
                     {'name': 'five-or-more', 'category': 'games', 'prettyname': 'Five or More'},
                     {'name': 'fluid', 'category': 'development', 'prettyname': 'FLUID'},
                     {'name': 'focuswriter', 'category': 'office', 'prettyname': 'FocusWriter'},
                     {'name': 'fontforge', 'category': 'graphics', 'prettyname': 'FontForge'},
                     {'name': 'foobillardplus', 'category': 'games', 'prettyname': 'FooBillard++'},
                     {'name': 'four-in-a-row', 'category': 'games', 'prettyname': 'Four-in-a-row'},
                     {'name': 'franz', 'category': 'internet', 'prettyname': 'Franz'},
                     {'name': 'freecad', 'category': 'graphics', 'prettyname': 'FreeCAD'},
                     {'name': 'freeorion', 'category': 'games', 'prettyname': 'FreeOrion'},
                     {'name': 'freeplane', 'category': 'graphics', 'prettyname': 'Freeplane'},
                     {'name': 'frescobaldi', 'category': 'multimedia', 'prettyname': 'Frescobaldi'},
                     {'name': 'fritzing', 'category': 'development', 'prettyname': 'Fritzing'},
                     {'name': 'frozen-bubble', 'category': 'games', 'prettyname': 'Frozen-Bubble'},
                     {'name': 'fs-uae-launcher', 'category': 'system', 'prettyname': 'FS-UAE Launcher'},
                     {'name': 'gbrainy', 'category': 'education', 'prettyname': 'gbrainy'},
                     {'name': 'gcompris', 'category': 'education', 'prettyname': 'GCompris'},
                     {'name': 'gdebi', 'category': 'other', 'prettyname': 'GDebi'},
                     {'name': 'geany', 'category': 'development', 'prettyname': 'Geany'},
                     {'name': 'geary', 'category': 'internet', 'prettyname': 'Geary'},
                     {'name': 'gedit', 'category': 'office', 'prettyname': 'Gedit'},
                     {'name': 'geeqie', 'category': 'graphics', 'prettyname': 'Geeqie'},
                     {'name': 'gelemental', 'category': 'education', 'prettyname': 'Periodic Table'},
                     {'name': 'geogebra', 'category': 'education', 'prettyname': 'GeoGebra'},
                     {'name': 'ghex', 'category': 'development', 'prettyname': 'GHex'},
                     {'name': 'giggle', 'category': 'development', 'prettyname': 'Giggle'},
                     {'name': 'gimp', 'category': 'graphics', 'prettyname': 'GIMP'},
                     {'name': 'glade', 'category': 'graphics', 'prettyname': 'Glade'},
                     {'name': 'gnome-2048', 'category': 'games', 'prettyname': '2048'},
                     {'name': 'gnome-boxes', 'category': 'system', 'prettyname': 'Boxes'},
                     {'name': 'gnome-builder', 'category': 'development', 'prettyname': 'Builder'},
                     {'name': 'gnome-characters', 'category': 'other', 'prettyname': 'Characters'},
                     {'name': 'gnome-mpv', 'category': 'multimedia', 'prettyname': 'GNOME MPV'},
                     {'name': 'google-chrome-stable', 'category': 'internet', 'prettyname': 'Google Chrome'},
                     {'name': 'gparted', 'category': 'system', 'prettyname': 'GParted'},
                     {'name': 'guake', 'category': 'development', 'prettyname': 'Guake'},
                     {'name': 'hardinfo', 'category': 'system', 'prettyname': 'System Profiler and Benchmark'},
                     {'name': 'hexchat', 'category': 'internet', 'prettyname': 'HexChat'},
                     {'name': 'inkscape', 'category': 'graphics', 'prettyname': 'Inkscape'},
                     {'name': 'kazam', 'category': 'multimedia', 'prettyname': 'Kazam'},
                     {'name': 'kdenlive', 'category': 'multimedia', 'prettyname': 'Kdenlive'},
                     {'name': 'leocad', 'category': 'graphics', 'prettyname': 'LeoCAD'},
                     {'name': 'librecad', 'category': 'graphics', 'prettyname': 'LibreCAD'},
                     {'name': 'libreoffice', 'category': 'office', 'prettyname': 'LibreOffice'},
                     {'name': 'linphone', 'category': 'internet', 'prettyname': 'Linphone'},
                     {'name': 'master-pdf-editor', 'category': 'office', 'prettyname': 'Master PDF Editor 5'},
                     {'name': 'mblock-4', 'category': 'development', 'prettyname': 'mBlock'},
                     {'name': 'mpv', 'category': 'multimedia', 'prettyname': 'mpv Media Player'},
                     {'name': 'nautilus', 'category': 'system', 'prettyname': 'Nautilus'},
                     {'name': 'obs-studio', 'category': 'multimedia', 'prettyname': 'OBS Studio'},
                     {'name': 'openscad', 'category': 'graphics', 'prettyname': 'OpenSCAD'},
                     {'name': 'opera-stable', 'category': 'internet', 'prettyname': 'Opera'},
                     {'name': 'pardus-imagewriter', 'category': 'system', 'prettyname': 'Pardus Image Writer'},
                     {'name': 'pdebi', 'category': 'system', 'prettyname': 'Pardus Package Installer'},
                     {'name': 'pdfarranger', 'category': 'office', 'prettyname': 'PDF Arranger'},
                     {'name': 'pdfsam', 'category': 'office', 'prettyname': 'PDFsam Basic'},
                     {'name': 'pergono', 'category': 'other', 'prettyname': 'Pergono'},
                     {'name': 'pidgin', 'category': 'internet', 'prettyname': 'Pidgin Internet Messenger'},
                     {'name': 'pinta', 'category': 'graphics', 'prettyname': 'Pinta'},
                     {'name': 'playonlinux', 'category': 'games', 'prettyname': 'PlayOnLinux'},
                     {'name': 'pokerth', 'category': 'games', 'prettyname': 'PokerTH'},
                     {'name': 'polari', 'category': 'internet', 'prettyname': 'Polari'},
                     {'name': 'pycharm', 'category': 'development', 'prettyname': 'PyCharm Community Edition'},
                     {'name': 'pythoncad', 'category': 'graphics', 'prettyname': 'PyCAD'},
                     {'name': 'qbittorrent', 'category': 'internet', 'prettyname': 'qBittorrent'},
                     {'name': 'qtcreator', 'category': 'development', 'prettyname': 'Qt Creator'},
                     {'name': 'remmina', 'category': 'system', 'prettyname': 'Remmina'},
                     {'name': 'rhythmbox', 'category': 'multimedia', 'prettyname': 'Rhythmbox'},
                     {'name': 'scratch', 'category': 'development', 'prettyname': 'Scratch'},
                     {'name': 'scribus', 'category': 'graphics', 'prettyname': 'Scribus'},
                     {'name': 'skypeforlinux', 'category': 'internet', 'prettyname': 'Skype'},
                     {'name': 'smplayer', 'category': 'multimedia', 'prettyname': 'SMPlayer'},
                     {'name': 'solvespace', 'category': 'graphics', 'prettyname': 'SolveSpace'},
                     {'name': 'soundconverter', 'category': 'multimedia', 'prettyname': 'Sound Converter'},
                     {'name': 'sound-juicer', 'category': 'multimedia', 'prettyname': 'Sound Juicer'},
                     {'name': 'spotify-client', 'category': 'multimedia', 'prettyname': 'Spotify'},
                     {'name': 'spyder3', 'category': 'development', 'prettyname': 'Spyder3'},
                     {'name': 'stacer', 'category': 'system', 'prettyname': 'Stacer'},
                     {'name': 'steam', 'category': 'games', 'prettyname': 'Steam'},
                     {'name': 'sublime-text', 'category': 'development', 'prettyname': 'Sublime Text'},
                     {'name': 'supertux', 'category': 'games', 'prettyname': 'SuperTux 2'},
                     {'name': 'swell-foop', 'category': 'games', 'prettyname': 'Swell Foop'},
                     {'name': 'synaptic', 'category': 'system', 'prettyname': 'Synaptic Package Manager'},
                     {'name': 'sysprof', 'category': 'system', 'prettyname': 'Sysprof'},
                     {'name': 'teamviewer', 'category': 'system', 'prettyname': 'TeamViewer'},
                     {'name': 'telegram-desktop', 'category': 'internet', 'prettyname': 'Telegram'},
                     {'name': 'thunderbird', 'category': 'internet', 'prettyname': 'Thunderbird'},
                     {'name': 'timeshift', 'category': 'system', 'prettyname': 'Timeshift'},
                     {'name': 'transmission', 'category': 'internet', 'prettyname': 'Transmission'},
                     {'name': 'tuxguitar', 'category': 'multimedia', 'prettyname': 'tuxguitar'},
                     {'name': 'tuxmath', 'category': 'education', 'prettyname': 'Tux Math'},
                     {'name': 'uget', 'category': 'internet', 'prettyname': 'uGet'},
                     {'name': 'viber', 'category': 'internet', 'prettyname': 'Viber'},
                     {'name': 'virt-manager', 'category': 'system', 'prettyname': 'Virtual Machine Manager'},
                     {'name': 'virtualbox-6.0', 'category': 'system', 'prettyname': 'Oracle VM VirtualBox'},
                     {'name': 'vlc', 'category': 'multimedia', 'prettyname': 'VLC media player'},
                     {'name': 'vmpk', 'category': 'multimedia', 'prettyname': 'VMPK'},
                     {'name': 'vokoscreen', 'category': 'multimedia', 'prettyname': 'vokoscreen'},
                     {'name': 'vym', 'category': 'development', 'prettyname': 'VYM - View Your Mind'},
                     {'name': 'warmux', 'category': 'games', 'prettyname': 'Warmux'},
                     {'name': 'zeal', 'category': 'development', 'prettyname': 'Zeal'},
                     {'name': 'zegrapher', 'category': 'education', 'prettyname': 'ZeGrapher'},
                     {'name': 'zenmap', 'category': 'system', 'prettyname': 'Zenmap'},
                     {'name': 'zim', 'category': 'office', 'prettyname': 'Zim Desktop Wiki'}]

        for app in self.apps:
            try:
                pixbuf = Gtk.IconTheme.get_default().load_icon(app['name'], 64, Gtk.IconLookupFlags(16))
                # pixbuf = self.appiconpixbuf.load_icon(app['name'], 64, 0)
            except:
                # pixbuf = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", 64, 0)
                try:
                    pixbuf = self.parduspixbuf.load_icon(app['name'], 64, Gtk.IconLookupFlags(16))
                except:
                    pixbuf = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", 64, Gtk.IconLookupFlags(16))

            appname = app['name']
            prettyname = app['prettyname']
            category = app['category']
            categorynumber = self.get_category_number(app['category'])
            self.PardusAppListStore.append([pixbuf, appname, categorynumber, prettyname])

        self.editorapps = [{'name': '0ad', 'category': 'games', 'prettyname': '0 A.D.'},
                           {'name': 'akis', 'category': 'other', 'prettyname': 'Akis'},
                           {'name': 'alien-arena', 'category': 'games', 'prettyname': 'Alien Arena'}]

        for ediapp in self.editorapps:
            try:
                edipixbuf = Gtk.IconTheme.get_default().load_icon(ediapp['name'], 64, Gtk.IconLookupFlags(16))
                # pixbuf = self.appiconpixbuf.load_icon(app['name'], 64, 0)
            except:
                # pixbuf = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", 64, 0)
                try:
                    edipixbuf = self.parduspixbuf.load_icon(ediapp['name'], 64, Gtk.IconLookupFlags(16))
                except:
                    edipixbuf = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", 64, Gtk.IconLookupFlags(16))

            ediappname = ediapp['name']
            ediprettyname = ediapp['prettyname']
            edicategory = ediapp['category']
            edicategorynumber = self.get_category_number(ediapp['category'])
            self.EditorListStore.append([edipixbuf, ediappname, edicategorynumber, ediprettyname])

        self.PardusCurrentCategory = -1
        self.RepoCurrentCategory = "empty"

        self.useDynamicListStore = True

        self.PardusCategoryFilter = self.GtkBuilder.get_object("PardusCategoryFilter")
        self.PardusCategoryFilter.set_visible_func(self.PardusCategoryFilterFunction)
        self.PardusCategoryFilter.refilter()

        # self.RepoCategoryFilter = self.GtkBuilder.get_object("RepoCategoryFilter")
        # self.RepoCategoryFilter.set_visible_func(self.RepoCategoryFilterFunction)
        # self.RepoCategoryFilter.refilter()

        self.MainWindow = self.GtkBuilder.get_object("MainWindow")
        self.MainWindow.set_application(application)
        self.mainstack.set_visible_child_name("page0")
        self.MainWindow.show_all()

        p1 = threading.Thread(target=self.worker)
        p1.start()
        print("start done")

    def worker(self):
        self.package()
        self.setRepoCategories()
        self.setRepoApps()
        self.server()
        self.normalpage()

    def normalpage(self):
        # self.mainstack.set_visible_child_name("page1")
        self.mainstack.set_visible_child_name("page2")
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

    def setRepoCategories(self):
        self.splashlabel.set_markup("<b>Setting Repo Categories</b>")
        for i in self.Package.sections:
            # row = Gtk.ListBoxRow.new()
            # self.RepoCategoryListBox.add(row)
            #
            label = Gtk.Label.new()
            label.set_text(" " + str(i["name"]).capitalize())
            label.set_property("xalign", 0)

            row = Gtk.ListBoxRow()
            row.add(label)

            self.RepoCategoryListBox.add(row)

        self.RepoCategoryListBox.show_all()
        print("Repo Categories setted")

    def setRepoApps(self):
        self.splashlabel.set_markup("<b>Setting Repo Apps</b>")
        print("Repo apps setting")
        for app in self.Package.apps:
            appname = app['name']
            category = app['category']
            # categorynumber = self.get_repo_category_number(app["category"])
            self.RepoAppListStore.append([appname, category, 0])

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Name", renderer, text=0)
        self.RepoAppsTreeView.append_column(column)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Section", renderer, text=1)
        self.RepoAppsTreeView.append_column(column)
        self.RepoAppsTreeView.show_all()

        self.repoapps = self.Package.repoapps

        if self.useDynamicListStore:

            self.storedict = {}

            for i in self.repoapps:
                self.storedict[i] = Gtk.ListStore(str, str)

            for i in self.storedict:
                for j in self.repoapps[i]:
                    self.storedict[i].append([j["name"], j["category"]])

    def server(self):
        self.splashbar.pulse()
        self.splashlabel.set_markup("<b>Getting applications from server</b>")
        self.Server = Server()
        print("server completed")

    def on_timeout(self, user_data):
        if self.splashbarstatus:
            self.splashbar.pulse()
        else:
            self.splashbar.set_fraction(0)
        return True

    def get_category_number(self, thatcategory):
        if thatcategory == "all":
            return 0
        if thatcategory == "development":
            return 1
        elif thatcategory == "education":
            return 2
        elif thatcategory == "games":
            return 3
        elif thatcategory == "graphics":
            return 4
        elif thatcategory == "internet":
            return 5
        elif thatcategory == "multimedia":
            return 6
        elif thatcategory == "office":
            return 7
        elif thatcategory == "system":
            return 8
        elif thatcategory == "other":
            return 9
        else:
            return 404

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
        if self.homestack.get_visible_child_name() == "page2":
            self.homestack.set_visible_child_name("page0")
            self.HomeCategoryFlowBox.unselect_all()
            self.EditorAppsIconView.unselect_all()
            self.menubackbutton.set_sensitive(False)
        elif self.homestack.get_visible_child_name() == "page3":
            self.homestack.set_visible_child_name("page2")
            self.PardusAppsIconView.unselect_all()

    def on_PardusAppsIconView_selection_changed(self, iconview):

        self.menubackbutton.set_sensitive(True)

        selected_items = iconview.get_selected_items()

        if len(selected_items) == 1:
            treeiter = self.PardusCategoryFilter.get_iter(selected_items[0])
            self.appname = self.PardusCategoryFilter.get(treeiter, 1)[0]
            prettyname = self.PardusCategoryFilter.get(treeiter, 3)[0]
            print(selected_items[0])
            print(self.appname)

            self.homestack.set_visible_child_name("page3")

            try:
                pixbuf = Gtk.IconTheme.get_default().load_icon(self.appname, 96, Gtk.IconLookupFlags(16))
                # pixbuf = self.appiconpixbuf.load_icon(app['name'], 64, 0)
            except:
                # pixbuf = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", 64, 0)
                try:
                    pixbuf = self.parduspixbuf.load_icon(self.appname, 96, Gtk.IconLookupFlags(16))
                except:
                    pixbuf = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", 96, Gtk.IconLookupFlags(16))

            self.dIcon.set_from_pixbuf(pixbuf)

            self.dName.set_markup("<b> " + prettyname + "</b>")

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
        appname = model[iteration][1]
        showall = True

        if self.isPardusSearching:
            self.HomeCategoryFlowBox.unselect_all()
            if search_entry_text in appname:
                return True
        else:

            if showall and self.PardusCurrentCategory == -1:
                return True
            elif showall and self.PardusCurrentCategory == 0:
                return True
            else:
                return categorynumber == self.PardusCurrentCategory

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
        self.homestack.set_visible_child_name("page2")
        self.menubackbutton.set_sensitive(True)
        self.PardusCurrentCategory = child.get_index()
        self.PardusCategoryFilter.refilter()

        print("home category selected " + str(self.PardusCurrentCategory))

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

                store = Gtk.ListStore(str, str)

                for i in self.repoapps[self.RepoCurrentCategory]:
                    store.append([i["name"], i["category"]])

                print(self.repoapps[self.RepoCurrentCategory])

                self.RepoAppsTreeView.set_model(store)

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
        self.searchstack.set_visible_child_name("page0")
        self.homestack.set_visible_child_name("page0")
        self.HomeCategoryFlowBox.unselect_all()
        self.EditorAppsIconView.unselect_all()
        self.PardusAppsIconView.unselect_all()
        self.menubackbutton.set_sensitive(False)
        if self.topbutton2.get_style_context().has_class("suggested-action"):
            self.topbutton2.get_style_context().remove_class("suggested-action")
        if not self.topbutton1.get_style_context().has_class("suggested-action"):
            self.topbutton1.get_style_context().add_class("suggested-action")

    def on_topbutton2_clicked(self, button):
        self.searchstack.set_visible_child_name("page1")
        self.homestack.set_visible_child_name("page1")
        self.menubackbutton.set_sensitive(False)
        if self.topbutton1.get_style_context().has_class("suggested-action"):
            self.topbutton1.get_style_context().remove_class("suggested-action")
        if not self.topbutton2.get_style_context().has_class("suggested-action"):
            self.topbutton2.get_style_context().add_class("suggested-action")

    def on_pardussearchbar_search_changed(self, entry_search):
        self.isPardusSearching = True
        self.homestack.set_visible_child_name("page2")
        self.menubackbutton.set_sensitive(True)
        # self.SearchFilter.refilter()
        self.PardusCategoryFilter.refilter()

    def on_pardussearchbar_button_press_event(self, widget, click):
        self.homestack.set_visible_child_name("page2")
        # self.SearchFilter.refilter()
        self.menubackbutton.set_sensitive(True)
        self.isPardusSearching = True
        print("on_searchbar_button_press_event")
        self.PardusCategoryFilter.refilter()

    def on_pardussearchbar_focus_in_event(self, widget, click):
        self.homestack.set_visible_child_name("page2")
        self.menubackbutton.set_sensitive(True)
        print("on_searchbar_focus_in_event")
        self.isPardusSearching = True
        self.PardusCategoryFilter.refilter()

    def on_reposearchbar_search_changed(self, entry_search):
        self.RepoCategoryListBox.unselect_all()
        self.isRepoSearching = True
        # self.RepoCategoryFilter.refilter()

        print("searched for : " + entry_search.get_text())

        # searchstore = Gtk.ListStore(str, str)
        # for i in self.Package.apps:
        #     if entry_search.get_text() in i["name"]:
        #         searchstore.append([i["name"], i["category"]])
        #
        # self.RepoAppsTreeView.set_model(searchstore)
        # self.RepoAppsTreeView.show_all()

    def on_reposearchbar_button_press_event(self, widget, click):
        self.RepoCategoryListBox.unselect_all()
        self.isRepoSearching = True
        print("on_reposearchbar_button_press_event")

    def on_reposearchbar_focus_in_event(self, widget, click):
        self.RepoCategoryListBox.unselect_all()
        print("on_reposearchbar_focus_in_event")
        self.isRepoSearching = True
        # if self.reposearchbar.get_text() != "":
        #     self.RepoCategoryFilter.refilter()

    def on_reposearchbutton_clicked(self, button):
        self.isRepoSearching = True
        print("on_reposearchbutton_clicked")

        searchstore = Gtk.ListStore(str, str)
        for i in self.Package.apps:
            if self.reposearchbar.get_text() in i["name"]:
                searchstore.append([i["name"], i["category"]])

        self.RepoAppsTreeView.set_model(searchstore)
        self.RepoAppsTreeView.show_all()

    def actionPackage(self):

        self.topspinner.start()

        self.dActionButton.set_sensitive(False)

        self.dActionButton.set_image(Gtk.Image.new_from_stock("gtk-convert", Gtk.IconSize.BUTTON))

        self.actionedappname = self.appname

        self.isinstalled = self.Package.isinstalled(self.appname)

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
                        pixbuf = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", 96, Gtk.IconLookupFlags(16))

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
                pixbuf = Gtk.IconTheme.get_default().load_icon("gtk-missing-image", 96, Gtk.IconLookupFlags(16))
        notification.set_icon_from_pixbuf(pixbuf)
        notification.show()
