"""One-shot playback, restoration, pause/hide and non-persistence."""
import unittest
from unittest.mock import patch

from avatar import Action
from motion_preview import MotionPreview
from settings import Preferences, SettingsStore
import test_settings as settings_tests


class MotionPreviewTests(unittest.TestCase):
    setUp = settings_tests.SettingsTests.setUp
    tearDown = settings_tests.SettingsTests.tearDown
    window = settings_tests.SettingsTests.window

    def tick(self, window, dt=.1):
        window._last -= dt
        window._tick()

    def test_stage_progression_and_cancel(self):
        preview = MotionPreview()
        preview.start(1.62)
        preview.advance(Action.SIT_DOWN, 10)
        self.assertEqual(preview.stage, 'sitting')
        preview.advance(Action.REST, 0)
        preview.advance(Action.REST, 1.61)
        self.assertTrue(preview.wants_rest)
        preview.advance(Action.REST, .01)
        self.assertFalse(preview.wants_rest)
        preview.advance(Action.STAND_UP, 1)
        self.assertTrue(preview.active)
        preview.advance(None, 0)
        self.assertFalse(preview.active)

    def test_full_cycle_preserves_preferences_and_previous_mode(self):
        window = self.window()
        prefs = Preferences(height=105, speed=55)
        window.save_preferences(prefs)
        window.set_mode('idle')
        self.assertTrue(window.start_motion_preview())
        self.assertFalse(window.start_motion_preview())
        seen = set()
        x = window.avatar.x
        for _ in range(60):
            self.tick(window)
            seen.add(window.animation.action)
            self.assertEqual(window.avatar.x, x)
        self.assertTrue({Action.SIT_DOWN, Action.REST, Action.STAND_UP}.issubset(seen))
        self.assertFalse(window.motion_preview.active)
        self.assertEqual(window.mode, 'idle')
        self.assertEqual(SettingsStore(self.path).load(), prefs)

    def test_pause_hidden_and_manual_mode_override(self):
        window = self.window()
        window.set_paused(True)
        self.assertFalse(window.start_motion_preview())
        window.set_paused(False)
        window.set_hidden(True)
        self.assertFalse(window.start_motion_preview())
        window.set_hidden(False)
        window.start_motion_preview()
        self.tick(window)
        phase = window.rest_controller.phase
        window.set_paused(True)
        self.tick(window)
        self.assertEqual(window.rest_controller.phase, phase)
        self.assertTrue(window.motion_preview.active)
        window.set_mode('walk')
        self.assertFalse(window.motion_preview.active)

    def test_dialog_buttons_play_stop_without_saving(self):
        window = self.window()
        window.open_settings()
        dialog = window.settings_dialog
        dialog.tabs.setCurrentIndex(3)
        self.assertTrue(dialog.play_preview.isEnabled())
        dialog.play_preview.click()
        self.assertTrue(window.motion_preview.active)
        self.assertFalse(dialog.play_preview.isEnabled())
        self.assertTrue(dialog.stop_preview.isEnabled())
        dialog.stop_preview.click()
        self.assertFalse(window.motion_preview.active)
        self.assertTrue(dialog.isVisible())
        self.assertEqual(SettingsStore(self.path).load(), Preferences())

    def test_returns_to_rest_if_current_schedule_requires_it(self):
        window = self.window()
        window.start_motion_preview()
        with patch('overlay.routine_state', return_value='rest'):
            for _ in range(45):
                self.tick(window)
            self.assertFalse(window.motion_preview.active)
            for _ in range(20):
                self.tick(window)
        self.assertEqual(window.rest_controller.phase, Action.REST)
