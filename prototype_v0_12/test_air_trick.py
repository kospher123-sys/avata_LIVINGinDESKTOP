"""AIR_IDLE_TRICK asset fallback and overlay playback regression tests."""
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

from animation import ASSET_ROOT, SpriteAnimation
from avatar import Action
import test_settings


class AirTrickTests(unittest.TestCase):
    setUp = test_settings.SettingsTests.setUp
    tearDown = test_settings.SettingsTests.tearDown
    window = test_settings.SettingsTests.window

    def tick(self, window, dt=0.1):
        with patch("overlay.time.monotonic", return_value=window._last + dt):
            window._tick()

    @patch("overlay.routine_state", return_value="active")
    def test_preview_plays_all_frames_and_returns_to_idle(self, _):
        window = self.window()
        window.set_mode("idle")
        window.set_display_height(120)
        window.open_settings()
        window.settings_dialog.air_preview.click()
        self.tick(window)
        self.assertEqual(window.animation.action, Action.AIR_IDLE_TRICK)
        position = window.pos()
        frames = []
        for _ in range(53):
            frames.append(window.animation.index)
            self.tick(window, .02)
        self.assertEqual(sorted(set(frames)), list(range(6)))
        self.assertEqual(window.animation.action, Action.IDLE)
        self.assertEqual(window.pos(), position)
        self.assertTrue(window.settings_dialog.air_preview.isEnabled())

    @patch("overlay.routine_state", return_value="active")
    def test_automatic_pause_mirror_and_interruption(self, routine):
        window = self.window()
        window.set_mode("idle")
        window.set_display_height(120)
        window.air_trick.cooldown = 0
        for _ in range(7):
            self.tick(window)
        self.assertEqual(window.animation.action, Action.AIR_IDLE_TRICK)
        window.set_paused(True)
        elapsed = window.animation.elapsed
        self.tick(window)
        self.assertEqual(window.animation.elapsed, elapsed)
        right = window.grab().toImage()
        window._turn()
        left = window.grab().toImage()
        self.assertNotEqual(right, left)
        window.set_paused(False)
        window.set_mode("auto")
        self.assertEqual(window.animation.action, Action.IDLE)
        window.preview_air_trick()
        routine.return_value = "rest"
        self.tick(window)
        self.assertFalse(window.air_trick.playing)
        self.assertIn(window.animation.action, (Action.SIT_DOWN, Action.REST))

    def test_missing_effect_disables_only_air_trick(self):
        root = Path(self.directory.name) / "aang"
        for name in ("idle", "walk", "air_idle_trick"):
            shutil.copytree(ASSET_ROOT / name, root / name)
        shutil.copy2(ASSET_ROOT / "extra_clips.json", root)
        (root / "air_idle_trick/wind/air_idle_trick_04.png").unlink()
        animation = SpriteAnimation(root)
        self.assertTrue(any("air_idle_trick" in warning for warning in animation.warnings))
        self.assertFalse(animation.has_clip(Action.AIR_IDLE_TRICK))
        animation.advance(Action.AIR_IDLE_TRICK, 0)
        self.assertEqual(animation.action, Action.IDLE)
        self.assertTrue(animation.has_clip(Action.WALK))
    @patch("overlay.routine_state", return_value="active")
    def test_air_sequence_repeats_hold_then_returns_to_idle(self, _):
        window = self.window()
        window.set_mode("idle")
        window.set_display_height(120)
        window.open_settings()
        window.settings_dialog.air_sequence_preview.click()
        self.tick(window)
        action = Action.AIR_TRICK
        self.assertEqual(window.animation.action, action)
        self.assertAlmostEqual(window.animation.clip_duration(action), 6.7)
        sequence = window.animation.frames[action]
        self.assertEqual(len(sequence), 38)
        for cycle in range(1, 5):
            start = 4 + cycle * 6
            self.assertEqual(sequence[start:start + 6], sequence[4:10])
        seen = set()
        position = window.pos()
        for _ in range(336):
            if window.animation.action == action:
                seen.add(window.animation.index)
            self.tick(window, .02)
        self.assertEqual(seen, set(range(38)))
        self.assertEqual(window.animation.action, Action.IDLE)
        self.assertEqual(window.pos(), position)
