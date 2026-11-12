"""Active-version selection, extensible showcase, multi-streaks and window policy."""
import unittest
from unittest.mock import patch
from PySide6.QtCore import QPointF, QRectF
from animation import SpriteAnimation
from air_blast_v3 import AirBlastV3Effects
from avatar import Action
from motion_preview import ActionShowcase
from window_stack import covers_monitor, WindowsStack
import test_settings


class RuntimeFeatureTests(unittest.TestCase):
    setUp = test_settings.SettingsTests.setUp
    tearDown = test_settings.SettingsTests.tearDown
    window = test_settings.SettingsTests.window

    def tick(self, window, dt=.1):
        with patch("overlay.time.monotonic", return_value=window._last + dt):
            window._tick()

    def test_default_exe_mapping_is_v3_and_has_one_blast(self):
        animation = SpriteAnimation()
        self.assertIsInstance(animation.blast_effects, AirBlastV3Effects)
        self.assertEqual(animation.active_versions[Action.AIR_BLAST], "AIR_BLAST V3 multi-streak")
        self.assertEqual(sum(action == Action.AIR_BLAST for action in animation.frames), 1)
        self.assertTrue(str(animation.blast_effects.path).replace("\\", "/").endswith("air_blast_v3/effects.json"))
        self.assertFalse(animation.warnings)

    def test_showcase_automatically_includes_new_registration_once(self):
        window = self.window()
        animation = window.animation
        animation.frames["future_action"] = [animation.frames[Action.IDLE][0]]
        animation.frame_times["future_action"] = [.15]
        animation.frames["missing_action"] = []
        animation.frame_times["missing_action"] = [.15]
        preview = ActionShowcase()
        self.assertTrue(preview.start(animation))
        seen = []
        for _ in range(1000):
            if not preview.active:
                break
            if not seen or preview.action != seen[-1]:
                seen.append(preview.action)
            preview.advance(.05)
        self.assertEqual(seen, [action for action, frames in animation.frames.items() if frames])
        self.assertEqual(seen.count("future_action"), 1)
        self.assertNotIn("missing_action", seen)

    @patch("overlay.routine_state", return_value="active")
    def test_settings_showcase_plays_air_actions_and_future_clip(self, _):
        window = self.window()
        window.set_mode("idle")
        before = window.preferences
        x = window.avatar.x
        window.animation.frames["future_action"] = [window.animation.frames[Action.IDLE][0]]
        window.animation.frame_times["future_action"] = [.15]
        window.open_settings()
        window.settings_dialog.play_preview.click()
        self.assertTrue(window.showcase.active)
        seen = set()
        for _ in range(400):
            self.tick(window)
            seen.add(window.animation.action)
            if not window.showcase.active:
                break
        self.assertEqual(seen, set(window.animation.frames))
        self.assertEqual(window.preferences, before)
        self.assertEqual(window.avatar.x, x)
        self.assertIsNone(window.blast_window.scene)
        self.assertFalse(window.showcase.active)

    @patch("overlay.routine_state", return_value="active")
    def test_pause_cancel_and_modes_during_showcase(self, _):
        window = self.window()
        self.assertTrue(window.start_all_motion_preview())
        self.tick(window)
        window.set_paused(True)
        elapsed = window.showcase.elapsed
        self.tick(window)
        self.assertEqual(window.showcase.elapsed, elapsed)
        window.set_paused(False)
        window.set_mode("walk")
        self.assertFalse(window.showcase.active)
        self.tick(window)
        self.assertEqual(window.animation.action, Action.WALK)

    def test_four_independent_streaks_and_single_natural_flow(self):
        effects = SpriteAnimation().blast_effects
        scene = effects.scene(.960, QRectF(0, 0, 2560, 1400), QPointF(300, 1300), 120, 1, 6)
        self.assertEqual(len(scene.streaks), 4)
        self.assertGreater(len({round(streak.rect.x(), 3) for streak in scene.streaks}), 1)
        self.assertGreater(len({round(streak.rect.width(), 3) for streak in scene.streaks}), 1)
        self.assertGreater(len({round(streak.rect.y(), 3) for streak in scene.streaks}), 1)
        self.assertGreater(len({streak.index for streak in scene.streaks}), 1)
        self.assertEqual(scene.flow_rect.left(), 0)
        self.assertAlmostEqual(scene.front.width(), scene.flow_rect.width())
        effects.reset()
        repeated = effects.scene(.960, scene.area, QPointF(300, 1300), 120, 1, 6)
        self.assertEqual([s.rect for s in scene.streaks], [s.rect for s in repeated.streaks])

    def test_fullscreen_policy_excludes_maximized_and_bordered_windows(self):
        monitor = (0, 0, 2560, 1440)
        self.assertTrue(covers_monitor(monitor, monitor, False, False))
        self.assertFalse(covers_monitor(monitor, monitor, True, False))
        self.assertFalse(covers_monitor(monitor, monitor, False, True))
        self.assertFalse(covers_monitor((0, 0, 2560, 1392), monitor, False, False))
        self.assertTrue(covers_monitor((-1600, -200, 0, 800), (-1600, -200, 0, 800), False, False))
