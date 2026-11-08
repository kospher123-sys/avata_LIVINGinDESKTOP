"""Pause/hide state and process ownership/duplicate activation tests."""
import os
import subprocess
import sys
import unittest

from PySide6.QtTest import QSignalSpy
from single_instance import SingleInstance
import test_settings as settings_tests

APP = settings_tests.APP


class RuntimeTests(unittest.TestCase):
    setUp = settings_tests.SettingsTests.setUp
    tearDown = settings_tests.SettingsTests.tearDown
    window = settings_tests.SettingsTests.window

    def test_pause_freezes_movement_animation_and_state(self):
        window = self.window()
        window.set_mode('walk')
        window.set_paused(True)
        state = (window.avatar.x, window.avatar.remaining, window.animation.elapsed,
                 window.rest_controller.phase)
        window._last -= 100
        window._tick()
        self.assertEqual(state, (window.avatar.x, window.avatar.remaining, window.animation.elapsed,
                                 window.rest_controller.phase))
        self.assertFalse(window.timer.isActive())
        self.assertEqual(window.pause_action.text(), '재개')
        window.set_paused(False)
        self.assertTrue(window.timer.isActive())
        window._last -= .05
        window._tick()
        self.assertNotEqual(window.avatar.x, state[0])

    def test_hidden_stays_hidden_during_settings_and_screen_changes(self):
        window = self.window()
        window.set_paused(True)
        window.set_hidden(True)
        self.assertFalse(window.isVisible())
        window._set_interactive(True)
        window._screen_changed()
        self.assertFalse(window.isVisible())
        self.assertFalse(window.timer.isActive())
        window.open_settings()
        self.assertTrue(window.settings_dialog.isVisible())
        self.assertFalse(window.isVisible())
        window.set_hidden(False)
        self.assertTrue(window.isVisible())
        self.assertTrue(window.paused)
        self.assertFalse(window.timer.isActive())
        window.set_paused(False)
        self.assertTrue(window.timer.isActive())

    def test_hidden_freezes_then_resumes_without_long_time_jump(self):
        window = self.window()
        window.set_mode('walk')
        x = window.avatar.x
        window.set_hidden(True)
        window._last -= 3600
        window._tick()
        self.assertEqual(window.avatar.x, x)
        window.set_hidden(False)
        window._last -= .05
        window._tick()
        self.assertTrue(0 < abs(window.avatar.x - x) <= window.avatar.speed * .1)

    def test_second_process_notifies_primary_and_exits(self):
        primary = SingleInstance(self.directory.name)
        self.assertTrue(primary.acquire())
        spy = QSignalSpy(primary.activated)
        code = ('from PySide6.QtWidgets import QApplication; from single_instance import SingleInstance; '
                'import sys; app=QApplication([]); guard=SingleInstance(sys.argv[1]); '
                'print(guard.acquire()); guard.close()')
        try:
            result = subprocess.run([sys.executable, '-c', code, self.directory.name],
                                    cwd=os.path.dirname(__file__), capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), 'False')
            APP.processEvents()
            self.assertEqual(spy.count(), 1)
            self.assertTrue(primary.primary)
        finally:
            primary.close()
        replacement = SingleInstance(self.directory.name)
        try:
            self.assertTrue(replacement.acquire())
        finally:
            replacement.close()

    def test_crashed_owner_does_not_block_restart(self):
        code = ('from PySide6.QtWidgets import QApplication; from single_instance import SingleInstance; '
                'import os,sys; app=QApplication([]); guard=SingleInstance(sys.argv[1]); '
                'assert guard.acquire(); os._exit(0)')
        result = subprocess.run([sys.executable, '-c', code, self.directory.name],
                                cwd=os.path.dirname(__file__), capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        replacement = SingleInstance(self.directory.name)
        try:
            self.assertTrue(replacement.acquire())
        finally:
            replacement.close()
