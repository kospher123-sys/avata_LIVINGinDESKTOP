"""Monitor routing tests, including negative coordinates and disconnection."""
from dataclasses import replace
import unittest
from unittest.mock import patch

from PySide6.QtCore import QObject, QRect, Signal
from screens import screen_key, select_screen
import test_settings as settings_tests
from settings import SettingsStore

APP = settings_tests.APP


class FakeScreen(QObject):
    availableGeometryChanged = Signal()
    geometryChanged = Signal()
    logicalDotsPerInchChanged = Signal()

    def name(self): return 'external'
    def serialNumber(self): return 'external-123'
    def manufacturer(self): return 'Test'
    def model(self): return 'Monitor'
    def devicePixelRatio(self): return 1.5
    def geometry(self): return QRect(-1600, -200, 1600, 1000)
    def availableGeometry(self): return QRect(-1600, -200, 1600, 960)


class ScreenTests(unittest.TestCase):
    setUp = settings_tests.SettingsTests.setUp
    tearDown = settings_tests.SettingsTests.tearDown
    window = settings_tests.SettingsTests.window
    def test_preferred_missing_and_primary_selection(self):
        first = APP.primaryScreen()
        second = FakeScreen()
        self.assertIs(select_screen([first, second], screen_key(second), first), second)
        self.assertIs(select_screen([first], screen_key(second), first), first)
        self.assertIs(select_screen([first, second], '', second), second)
        self.assertIsNone(select_screen([], '', first))

    def test_switch_unplug_reconnect_and_cancel(self):
        window = self.window()
        primary = APP.primaryScreen()
        external = FakeScreen()
        preferred = replace(window.preferences, monitor=screen_key(external), auto_size=True)
        with patch('overlay.QApplication.screens', return_value=[primary, external]), patch.object(window, 'setScreen'):
            window.open_settings()
            dialog = window.settings_dialog
            dialog.refresh_screens()
            dialog.monitor.setCurrentIndex(dialog.monitor.findData(screen_key(external)))
            self.assertIs(window.display_screen, external)
            self.assertLess(window.left, 0)
            self.assertTrue(window.left <= window.avatar.x <= window.right)
            dialog.reject()
            self.assertIs(window.display_screen, primary)
            window.save_preferences(preferred)
            self.assertEqual(window.display_height, 133)
            self.assertEqual(SettingsStore(self.path).load().monitor, screen_key(external))
            with patch('overlay.QApplication.screens', return_value=[primary]):
                window._screen_removed(external)
                self.assertIs(window.display_screen, primary)
                self.assertEqual(window.preferences.monitor, screen_key(external))
            window._screens_changed()
            self.assertIs(window.display_screen, external)
            # Restore a real screen before the fake QObject goes out of scope.
            window.save_preferences(replace(preferred, monitor=''))
