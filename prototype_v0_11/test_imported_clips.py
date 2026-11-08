"""Actual imported native-size art, registration, timing and fallbacks."""
import json
from pathlib import Path
import unittest

from animation import ASSET_ROOT, ANCHOR, SpriteAnimation
from avatar import Action
import test_settings as settings_tests


class ImportedClipTests(unittest.TestCase):
    setUp = settings_tests.SettingsTests.setUp
    tearDown = settings_tests.SettingsTests.tearDown
    window = settings_tests.SettingsTests.window

    def test_actual_asset_counts_timings_and_anchor(self):
        animation = SpriteAnimation()
        self.assertEqual(animation.warnings, [])
        for action, count, duration in ((Action.IDLE, 1, .7), (Action.WALK, 6, .72),
                (Action.REST, 4, 1.62), (Action.SIT_DOWN, 6, 1.18), (Action.STAND_UP, 6, 1.18)):
            self.assertEqual(len(animation.frames[action]), count)
            self.assertAlmostEqual(animation.clip_duration(action), duration)
        for action in (Action.REST, Action.SIT_DOWN, Action.STAND_UP, Action.IDLE):
            animation.advance(action, 0)
            rect = animation.render_rect
            self.assertAlmostEqual(rect.x() + 256 / 512 * rect.width(), ANCHOR[0])
            self.assertAlmostEqual(rect.y() + 735 / 768 * rect.height(), ANCHOR[1])
        animation.advance(Action.REST, 0)
        for elapsed, index in ((.59, 0), (.60, 1), (.92, 2), (1.02, 3)):
            animation.elapsed = elapsed
            self.assertEqual(animation.index, index)
        animation.advance(Action.SIT_DOWN, 0)
        animation.advance(Action.SIT_DOWN, 20)
        self.assertEqual(animation.index, 5)

    def test_all_new_frames_render_without_changing_window_or_scale(self):
        window = self.window()
        size = window.size()
        for action in (Action.IDLE, Action.REST, Action.SIT_DOWN, Action.STAND_UP):
            window.animation.advance(action, 0)
            for direction in (-1, 1):
                window.avatar.direction = direction
                elapsed = 0
                for duration in window.animation.frame_times[action]:
                    window.animation.elapsed = elapsed + .001
                    image = window.grab().toImage()
                    alpha = bytes(image.convertToFormat(image.Format.Format_RGBA8888).constBits())[3::4]
                    self.assertGreater(max(alpha), 0)
                    self.assertEqual(image.pixelColor(0, 0).alpha(), 0)
                    self.assertEqual(window.size(), size)
                    elapsed += duration

    def test_bad_manifest_keeps_legacy_clips(self):
        # Use only the required pre-existing assets in a temporary fixture.
        import shutil
        root = Path(self.directory.name) / 'assets'
        for name in ('idle', 'walk'):
            shutil.copytree(ASSET_ROOT / name, root / name)
        (root / 'clips.json').write_text(json.dumps({'version':1, 'clips':{'rest':{
            'directory':'../outside','prefix':'rest','canvas':[512,768],
            'anchor':[256,735],'standing_height':680,'durations_ms':[500]}}}))
        animation = SpriteAnimation(root)
        self.assertTrue(animation.warnings)
        self.assertFalse(animation.has_clip(Action.REST))
        self.assertEqual(len(animation.frames[Action.IDLE]), 4)
