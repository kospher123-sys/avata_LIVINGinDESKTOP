"""Idle-only scheduling, native registration and action priority."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from animation import ASSET_ROOT, SpriteAnimation, ANCHOR, VISIBLE_HEIGHT
from avatar import Action
from idle_look import IdleLook
import test_settings as settings_tests


class IdleLookTests(unittest.TestCase):
    setUp = settings_tests.SettingsTests.setUp
    tearDown = settings_tests.SettingsTests.tearDown
    window = settings_tests.SettingsTests.window

    def test_only_idle_dwell_can_trigger_and_clip_is_one_shot(self):
        look = IdleLook()
        look.cooldown = .1
        self.assertFalse(look.update(1, False, True, 1.64))
        self.assertFalse(look.update(.4, True, True, 1.64))
        self.assertTrue(look.update(.1, True, True, 1.64))
        self.assertTrue(look.update(1.63, True, True, 1.64))
        self.assertFalse(look.update(.01, True, True, 1.64))
        self.assertGreaterEqual(look.cooldown, 20)
        self.assertLessEqual(look.cooldown, 40)

    def test_unavailable_and_higher_priority_interrupt(self):
        look = IdleLook()
        look.start(1.64)
        self.assertFalse(look.update(.1, False, True, 1.64))
        look.start(1.64)
        self.assertFalse(look.update(.1, True, False, 1.64))

    def test_native_frames_and_per_frame_sole_registration(self):
        animation = SpriteAnimation()
        self.assertEqual(animation.warnings, [])
        self.assertEqual(len(animation.frames[Action.LOOK_AROUND]), 4)
        self.assertAlmostEqual(animation.clip_duration(Action.LOOK_AROUND), 1.64)
        spec = json.loads((ASSET_ROOT / 'extra_clips.json').read_text())['clips']['look_around']
        audit = json.loads((ASSET_ROOT / 'audit/look_around/validation.json').read_text())
        animation.advance(Action.LOOK_AROUND, 0)
        elapsed = 0
        for index, duration in enumerate(spec['durations_ms']):
            animation.elapsed = elapsed + .001
            rect = animation.render_rect
            anchor = spec['anchors'][index]
            ratio = VISIBLE_HEIGHT / spec['standing_height']
            self.assertAlmostEqual(rect.x() + anchor[0] * ratio, ANCHOR[0])
            self.assertAlmostEqual(rect.y() + anchor[1] * ratio, ANCHOR[1])
            self.assertTrue(audit['frames'][index]['retained_rgba_unchanged'])
            elapsed += duration / 1000
        animation.advance(Action.LOOK_AROUND, 10)
        self.assertEqual(animation.index, 3)

    def test_overlay_freezes_model_and_rest_interrupts(self):
        window = self.window()
        window.set_mode('idle')
        window.idle_look.cooldown = 0
        x = window.avatar.x
        for _ in range(6):
            window._last -= .1
            window._tick()
        self.assertTrue(window.idle_look.playing)
        self.assertEqual(window.animation.action, Action.LOOK_AROUND)
        self.assertEqual(window.avatar.x, x)
        remaining = window.avatar.remaining
        window._last -= .1
        window._tick()
        self.assertEqual(window.avatar.remaining, remaining)
        window.set_mode('auto')
        with patch('overlay.routine_state', return_value='rest'):
            window._last -= .1
            window._tick()
        self.assertFalse(window.idle_look.playing)
        self.assertEqual(window.animation.action, Action.SIT_DOWN)

    def test_manual_preview_and_ui_button_do_not_save(self):
        window = self.window()
        window.open_settings()
        dialog = window.settings_dialog
        saved = window.preferences
        dialog.look_preview.click()
        self.assertTrue(window.idle_look.playing)
        window._last -= .1
        window._tick()
        self.assertEqual(window.animation.action, Action.LOOK_AROUND)
        for _ in range(18):
            window._last -= .1
            window._tick()
        self.assertFalse(window.idle_look.playing)
        self.assertEqual(window.preferences, saved)
        self.assertFalse(Path(self.path).exists())
