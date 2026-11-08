"""Clock boundaries, persistence, live preview and activity resumption."""
from dataclasses import replace
from datetime import datetime
import unittest
from unittest.mock import patch

from PySide6.QtCore import QTime
from avatar import Action
from routine import is_rest_time, routine_state
from settings import Preferences, SettingsStore
import test_settings as settings_tests


class RoutineTests(unittest.TestCase):
    setUp = settings_tests.SettingsTests.setUp
    tearDown = settings_tests.SettingsTests.tearDown
    window = settings_tests.SettingsTests.window

    def test_midnight_and_exact_boundaries(self):
        for minute in range(1440):
            self.assertEqual(is_rest_time(minute, 1320, 420), minute >= 1320 or minute < 420)
            self.assertEqual(is_rest_time(minute, 720, 780), 720 <= minute < 780)
            self.assertFalse(is_rest_time(minute, 420, 420))

    def test_priority_and_disabled_schedule(self):
        now = datetime(2026, 11, 8, 23, 30)
        self.assertEqual(routine_state(Preferences(), now), 'free')
        prefs = Preferences(routine_enabled=True)
        self.assertEqual(routine_state(prefs, now), 'rest')
        self.assertEqual(routine_state(prefs, now.replace(hour=7, minute=0)), 'active')
        self.assertEqual(routine_state(replace(prefs, auto_move=False), now), 'stopped')

    def test_pause_resume_and_temporary_walk(self):
        window = self.window()
        window.avatar.x = (window.left + window.right) / 2
        position = window.avatar.x
        with patch('overlay.routine_state', return_value='rest'):
            window._last -= .05
            window._tick()
            self.assertEqual(window.avatar.x, position)
            self.assertEqual(window.avatar.action, Action.IDLE)
            window.set_mode('walk')
            window._last -= .05
            window._tick()
            self.assertEqual(window.avatar.action, Action.WALK)
        window.set_mode('auto')
        window._routine_state = 'rest'
        with patch('overlay.routine_state', return_value='active'):
            window._last -= .05
            window._tick()
            self.assertEqual(window.avatar.action, Action.WALK)

    def test_schedule_preview_cancel_and_save(self):
        window = self.window()
        window.open_settings()
        dialog = window.settings_dialog
        dialog.routine_enabled.setChecked(True)
        dialog.rest_start.setTime(QTime(21, 30))
        dialog.rest_end.setTime(QTime(8, 15))
        self.assertEqual(window.preview.rest_start, 1290)
        self.assertFalse(SettingsStore(self.path).load().routine_enabled)
        dialog.reject()
        self.assertIsNone(window.preview)
        window.open_settings()
        self.assertFalse(dialog.routine_enabled.isChecked())
        dialog.routine_enabled.setChecked(True)
        dialog.rest_start.setTime(QTime(21, 30))
        dialog.rest_end.setTime(QTime(8, 15))
        dialog.save()
        saved = SettingsStore(self.path).load()
        self.assertTrue(saved.routine_enabled)
        self.assertEqual((saved.rest_start, saved.rest_end), (1290, 495))

    def test_current_time_buttons_and_tabs_keep_preview(self):
        window = self.window()
        window.open_settings()
        dialog = window.settings_dialog
        self.assertEqual([dialog.tabs.tabText(i) for i in range(dialog.tabs.count())],
                         ['화면·크기', '움직임', '생활 시간표'])
        self.assertFalse(dialog.rest_start_now.isEnabled())
        dialog.tabs.setCurrentIndex(2)
        dialog.routine_enabled.setChecked(True)
        with patch('settings_dialog.QTime') as clock:
            clock.currentTime.return_value = QTime(14, 23, 40)
            dialog.rest_start_now.click()
            self.assertEqual(window.preview.rest_start, 14 * 60 + 23)
            self.assertEqual(window.preview.rest_end, 420)
            clock.currentTime.return_value = QTime(16, 45, 10)
            dialog.rest_end_now.click()
            self.assertEqual(window.preview.rest_end, 16 * 60 + 45)
        dialog.tabs.setCurrentIndex(0)
        dialog.height.setValue(105)
        dialog.tabs.setCurrentIndex(1)
        dialog.speed.setValue(45)
        self.assertTrue(dialog.isVisible())
        self.assertFalse(SettingsStore(self.path).load().routine_enabled)
        dialog.save()
        saved = SettingsStore(self.path).load()
        self.assertEqual((saved.height, saved.speed, saved.rest_start, saved.rest_end),
                         (105, 45, 863, 1005))

    def test_reset_schedule_preserves_other_unsaved_changes(self):
        window = self.window()
        saved = Preferences(height=135, speed=60, routine_enabled=True, rest_start=1200, rest_end=480)
        window.save_preferences(saved)
        window.open_settings()
        dialog = window.settings_dialog
        dialog.height.setValue(100)
        dialog.speed.setValue(45)
        dialog.reset_routine_button.click()
        self.assertEqual(window.preview, Preferences(height=100, speed=45))
        self.assertEqual(SettingsStore(self.path).load(), saved)
        self.assertTrue(dialog.isVisible())
        dialog.reject()
        self.assertEqual(window.display_height, 135)
        self.assertEqual(window.preferences, saved)

    def test_reset_all_can_cancel_or_save(self):
        window = self.window()
        saved = Preferences(height=140, auto_size=True, speed=30, auto_move=False,
                            monitor='disconnected', routine_enabled=True, rest_start=1200, rest_end=480)
        window.save_preferences(saved)
        window.set_mode('idle')
        window.open_settings()
        dialog = window.settings_dialog
        dialog.reset_all_button.click()
        self.assertEqual(window.preview, Preferences())
        self.assertEqual(dialog.values(), Preferences())
        self.assertEqual(SettingsStore(self.path).load(), saved)
        self.assertTrue(dialog.isVisible())
        dialog.close()
        self.assertEqual(window.preferences, saved)
        self.assertEqual(window.mode, 'idle')
        window.open_settings()
        dialog.reset_all_button.click()
        dialog.save()
        self.assertEqual(SettingsStore(self.path).load(), Preferences())
