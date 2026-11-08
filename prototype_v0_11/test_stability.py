"""Recovery, bounded diagnostics and packaged path checks."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from app_paths import asset_root
from diagnostics import configure_logging
from recovery import GapDetector, is_resume_message
from avatar import Action
import test_settings as settings_tests


class StabilityTests(unittest.TestCase):
    setUp = settings_tests.SettingsTests.setUp
    tearDown = settings_tests.SettingsTests.tearDown
    window = settings_tests.SettingsTests.window

    def test_gap_and_native_resume_selection(self):
        detector = GapDetector()
        self.assertFalse(detector.check(100))
        self.assertFalse(detector.check(102))
        self.assertTrue(detector.check(150))
        self.assertTrue(detector.check(90))
        self.assertTrue(is_resume_message(0x218, 0x12))
        self.assertFalse(is_resume_message(0x218, 4))
        self.assertFalse(is_resume_message(0x100, 0x12))

    def test_recovery_keeps_hidden_and_pause_and_clamps_position(self):
        window = self.window()
        window.set_hidden(True)
        window.set_paused(True)
        window.avatar.x = 999999
        window._last -= 1000
        window.recover_runtime()
        self.assertTrue(window.left <= window.avatar.x <= window.right)
        self.assertFalse(window.isVisible())
        self.assertTrue(window.paused)
        self.assertFalse(window.timer.isActive())
        window.set_hidden(False)
        window.set_paused(False)
        with patch('overlay.routine_state', return_value='rest'):
            window._tick()
        self.assertEqual(window.avatar.action, Action.IDLE)

    def test_recovery_moves_settings_back_on_screen_and_coalesces(self):
        window = self.window()
        window.open_settings()
        dialog = window.settings_dialog
        dialog.move(99999, 99999)
        dialog.height.setValue(105)
        window.request_recovery('first')
        window.request_recovery('second')
        self.assertTrue(window.recovery_timer.isActive())
        self.assertTrue(window.recovery_timer.isSingleShot())
        window.recovery_timer.stop()
        window.recover_runtime()
        self.assertTrue(window.display_screen.availableGeometry().contains(dialog.pos()))
        self.assertEqual(window.preview.height, 105)

    def test_packaged_assets_are_next_to_executable(self):
        with patch.object(sys, 'frozen', True, create=True), patch.object(sys, 'executable',
                str(Path(self.directory.name) / 'Aang.exe')):
            self.assertEqual(asset_root(), Path(self.directory.name).resolve() / 'assets/characters/aang')

    def test_settings_opens_centered_and_recovers_visible_offscreen_window(self):
        window = self.window()
        window.move(window.left, window.floor)
        window.open_settings()
        dialog = window.settings_dialog
        settings_tests.APP.processEvents()
        area = window.display_screen.availableGeometry()
        self.assertTrue(area.contains(dialog.frameGeometry()))
        self.assertLessEqual(abs(dialog.frameGeometry().center().x() - area.center().x()), 2)
        self.assertLessEqual(abs(dialog.frameGeometry().center().y() - area.center().y()), 2)
        dialog.move(99999, 99999)
        window.open_settings()
        self.assertTrue(area.contains(dialog.frameGeometry()))

    def test_utf8_and_rotating_logs_are_bounded(self):
        logger = configure_logging(self.directory.name)
        handler = logger.handlers[0]
        handler.maxBytes = 256
        logger.info('아앙 오류 기록 확인')
        handler.flush()
        self.assertIn('아앙 오류 기록 확인', (Path(self.directory.name) / 'app.log').read_text(encoding='utf-8'))
        for _ in range(100):
            logger.info('Bounded rotation check ' + 'x' * 50)
        handler.flush()
        self.assertLessEqual(len(list(Path(self.directory.name).glob('app.log*'))), 4)
        logger.removeHandler(handler)
        handler.close()
