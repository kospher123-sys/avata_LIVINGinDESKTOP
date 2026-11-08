"""Run: python -m unittest discover -s prototype_v0_8 -v"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication
from avatar import Action
from overlay import AvatarOverlay
from settings import Preferences, SettingsStore, automatic_height


APP = QApplication.instance() or QApplication([])


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "settings.ini"
        self.windows = []

    def tearDown(self):
        for window in self.windows:
            window.timer.stop()
            window.tray.hide()
            window.close()
            window.deleteLater()
        APP.processEvents()
        self.directory.cleanup()

    def window(self):
        window = AvatarOverlay(SettingsStore(self.path))
        window.timer.stop()
        self.windows.append(window)
        return window

    def test_default_and_persistence(self):
        self.assertEqual(SettingsStore(self.path).load(), Preferences())
        window = self.window()
        self.assertEqual(window.display_height, 120)
        prefs = Preferences(98, False, 40, False)
        self.assertTrue(window.save_preferences(prefs))
        restored = self.window()
        self.assertEqual(restored.preferences, prefs)
        self.assertEqual(restored.display_height, 98)
        self.assertEqual(restored.avatar.speed, 40)

    def test_corrupt_and_out_of_range(self):
        self.path.write_text('[General]\nheight=oops\nspeed=9999\nauto_size=invalid\nauto_move=false\n')
        self.assertEqual(SettingsStore(self.path).load(), Preferences(120, False, 150, False))

    def test_automatic_size(self):
        self.assertEqual(automatic_height(900), 120)
        self.assertEqual(automatic_height(1080), 144)
        self.assertEqual(automatic_height(1080 / 1.5), 96)
        self.assertEqual(automatic_height(100), 80)
        self.assertEqual(automatic_height(4000), 240)
        window = self.window()
        window.save_preferences(Preferences(123, True))
        self.assertEqual(window.display_height, automatic_height(window.display_screen.geometry().height()))
        window.save_preferences(Preferences(123, False))
        self.assertEqual(window.display_height, 123)

    def test_dialog_save_cancel_and_sync(self):
        window = self.window()
        window.open_settings()
        dialog = window.settings_dialog
        dialog.height_slider.setValue(100)
        self.assertEqual(dialog.height.value(), 100)
        self.assertEqual(window.display_height, 100)
        self.assertTrue(dialog.isVisible())
        self.assertEqual(SettingsStore(self.path).load(), Preferences())
        dialog.reject()
        self.assertEqual(window.display_height, 120)
        window.open_settings()
        self.assertEqual(dialog.height.value(), 120)
        dialog.height.setValue(110)
        dialog.speed.setValue(55)
        self.assertEqual(window.avatar.speed, 55)
        dialog.auto_move.setChecked(False)
        dialog.auto_size.setChecked(True)
        self.assertFalse(dialog.height.isEnabled())
        dialog.auto_size.setChecked(False)
        dialog.save()
        self.assertEqual(SettingsStore(self.path).load(), Preferences(110, False, 55, False))
        self.assertEqual(window.display_height, 110)
        self.assertFalse(dialog.isVisible())

    def test_close_rolls_back_live_preview(self):
        window = self.window()
        original = Preferences(135, False, 60, True)
        window.save_preferences(original)
        window.open_settings()
        dialog = window.settings_dialog
        dialog.height.setValue(90)
        dialog.speed.setValue(25)
        dialog.auto_move.setChecked(False)
        window._tick()
        self.assertEqual(window.avatar.action, Action.IDLE)
        dialog.close()
        self.assertIsNone(window.preview)
        self.assertEqual(window.display_height, 135)
        self.assertEqual(window.avatar.speed, 60)
        self.assertEqual(SettingsStore(self.path).load(), original)
        window.open_settings()
        self.assertEqual(dialog.height.value(), 135)

    def test_failed_save_keeps_preview_and_dialog_open(self):
        window = self.window()
        window.open_settings()
        dialog = window.settings_dialog
        dialog.height.setValue(100)
        with patch.object(window.store, 'save', side_effect=OSError('test')), patch('overlay.QMessageBox.warning'):
            dialog.save()
        self.assertTrue(dialog.isVisible())
        self.assertEqual(window.display_height, 100)
        self.assertEqual(window.preferences, Preferences())
        dialog.reject()
        self.assertEqual(window.display_height, 120)

    def test_movement_off_and_manual_override(self):
        window = self.window()
        window.save_preferences(Preferences(auto_move=False))
        window.avatar.x = (window.left + window.right) / 2
        position = window.avatar.x
        for _ in range(5):
            window._last -= .05
            window._tick()
        self.assertEqual(window.avatar.x, position)
        self.assertEqual(window.avatar.action, Action.IDLE)
        window.set_mode('walk')
        window._last -= .05
        window._tick()
        self.assertNotEqual(window.avatar.x, position)
        window.save_preferences(Preferences(auto_move=True))
        self.assertEqual(window.mode, 'auto')


if __name__ == '__main__':
    unittest.main()
