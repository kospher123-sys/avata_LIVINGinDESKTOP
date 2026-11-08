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
