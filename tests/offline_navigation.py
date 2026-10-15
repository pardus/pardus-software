"""GTK regression checks; run from a desktop session with the app dependencies.

Only the server result and APT health are supplied by the fixture. Widgets,
Glade signal bindings, navigation and filtering use the application code.
The constructor is bypassed to avoid starting network/package workers.
"""

import logging
from pathlib import Path
import sys
import traceback
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from MainWindow import MainWindow, GLib, Gtk


class OfflineNavigationTests(unittest.TestCase):
    def setUp(self):
        # PyGObject reports callback exceptions via sys.excepthook; unittest
        # would otherwise report success even when a signal handler failed.
        self.callback_errors = []
        self.addCleanup(setattr, sys, "excepthook", sys.excepthook)
        sys.excepthook = lambda *error: self.callback_errors.append("".join(traceback.format_exception(*error)))
        self.window = MainWindow.__new__(MainWindow)
        window = self.window
        window.GtkBuilder = Gtk.Builder.new_from_file(str(ROOT / "ui/MainWindow.glade"))
        for obj in window.GtkBuilder.get_objects():
            if isinstance(obj, Gtk.Buildable):
                setattr(window, Gtk.Buildable.get_name(obj), obj)
        window.Logger = logging.getLogger(__name__)
        window.Server = SimpleNamespace(connection=False, error_message="Offline", serverurl="https://example.invalid")
        window.myapps_perm = 1
        window.isbroken = False
        window.searching = False
        window.stack_history = []
        window.repo_final_list = []
        window.ui_top_searchentry.set_sensitive(False)
        window.ui_right_stack.set_visible_child_name("discover")
        window.ui_back_button.set_sensitive(False)
        window.ui_installedapps_flowbox.set_filter_func(window.installedapps_filter_function)
        window.GtkBuilder.connect_signals(window)

    def tearDown(self):
        self.window.ui_top_searchentry.disconnect_by_func(self.window.on_ui_top_searchentry_search_changed)
        for obj in self.window.GtkBuilder.get_objects():
            if isinstance(obj, Gtk.Window):
                obj.destroy()
        self.flush_events()
        self.assertEqual(self.callback_errors, [])

    def flush_events(self):
        context = GLib.MainContext.default()
        while context.pending():
            context.iteration(False)

    def show_home(self):
        self.window.set_initial_home()
        self.flush_events()

    def assert_page(self, page, home, search):
        window = self.window
        self.assertEqual(window.ui_right_stack.get_visible_child_name(), page)
        self.assertEqual(window.homestack.get_visible_child_name(), home)
        self.assertEqual(window.ui_top_searchentry.get_sensitive(), search)

    def test_offline_button_opens_an_empty_installed_list(self):
        self.show_home()
        button = self.window.GtkBuilder.get_object("offline_installed_button")
        self.assertIsNotNone(button)
        self.assertTrue(button.get_sensitive())
        button.clicked()
        self.assert_page("installed", "pardushome", True)
        self.assertTrue(self.window.ui_back_button.get_sensitive())
        self.window.ui_back_button.clicked()
        self.assert_page("discover", "noserver", False)
        self.assertFalse(self.window.ui_back_button.get_sensitive())

    def test_offline_button_respects_permission_and_apt_health(self):
        for permission, broken in ((0, False), (1, True), (0, True), (1, False)):
            with self.subTest(permission=permission, broken=broken):
                self.window.myapps_perm = permission
                self.window.isbroken = broken
                self.show_home()
                button = self.window.GtkBuilder.get_object("offline_installed_button")
                self.assertIsNotNone(button)
                self.assertEqual(button.get_sensitive(), bool(permission) and not broken)

    def test_offline_search_filters_local_rows(self):
        window = self.window
        self.show_home()
        for name in ("Mousepad", "Terminal"):
            row = Gtk.ListBoxRow()
            row.name = {"name": name}
            box = Gtk.ListBox()
            box.add(row)
            window.ui_installedapps_flowbox.add(box)
        window.ui_installedapps_flowbox.show_all()
        window.ui_right_stack_navigate_to("installed")
        self.assertTrue(window.ui_top_searchentry.get_sensitive())
        window.ui_top_searchentry.set_text("mouse")
        window.ui_top_searchentry.emit("search-changed")
        visible = [row for row in window.ui_installedapps_flowbox.get_children() if row.get_child_visible()]
        self.assertEqual(len(visible), 1)
        self.assertEqual(visible[0].get_child().get_row_at_index(0).name["name"], "Mousepad")

    def test_offline_details_back_restores_installed_search(self):
        window = self.window
        self.show_home()
        window.ui_right_stack_navigate_to("installed")
        window.ui_right_stack_navigate_to("appdetails")
        self.assert_page("appdetails", "pardushome", False)
        window.ui_back_button.clicked()
        self.assert_page("installed", "pardushome", True)
        window.ui_back_button.clicked()
        self.assert_page("discover", "noserver", False)
        self.assertEqual(window.stack_history, [])

    def test_delayed_search_after_back_does_not_open_catalog(self):
        window = self.window
        self.show_home()
        window.ui_right_stack_navigate_to("installed")
        window.ui_top_searchentry.set_text("")
        window.ui_back_button.clicked()
        # Deliver the delayed GTK search signal after navigation has finished.
        window.ui_top_searchentry.emit("search-changed")
        self.assert_page("discover", "noserver", False)
        self.assertEqual(window.stack_history, [])

    def test_offline_settings_back_returns_to_connection_error(self):
        self.show_home()
        self.window.ui_right_stack_navigate_to("settings")
        self.assert_page("settings", "pardushome", False)
        self.window.ui_back_button.clicked()
        self.assert_page("discover", "noserver", False)

    def test_offline_hides_unavailable_catalog_controls(self):
        self.show_home()
        self.window.set_upgradables()
        self.flush_events()
        self.assertFalse(self.window.ui_leftcats_box.get_visible())
        self.assertFalse(self.window.ui_upgradableapps_box.get_visible())
        self.assertFalse(self.window.ui_upgradableapps_flowbox.get_visible())

    def test_online_result_restores_home_after_failure(self):
        self.show_home()
        self.window.Server.connection = True
        self.show_home()
        self.assert_page("discover", "pardushome", True)
        self.assertTrue(self.window.ui_leftcats_box.get_visible())

    def test_online_navigation_keeps_catalog_search_available(self):
        self.window.Server.connection = True
        self.show_home()
        for page in ("installed", "appdetails", "settings", "discover"):
            with self.subTest(page=page):
                self.window.ui_right_stack_navigate_to(page)
                self.assert_page(page, "pardushome", True)

    def test_online_broken_apt_still_shows_repair_page(self):
        self.window.Server.connection = True
        self.window.isbroken = True
        self.show_home()
        self.assert_page("discover", "fixapt", False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
