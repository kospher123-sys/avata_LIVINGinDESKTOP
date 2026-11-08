"""Optional asset loading and transitions, without creating production artwork."""
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

from animation import ASSET_ROOT, SpriteAnimation
from avatar import Action
from rest_controller import RestController
import test_settings as settings_tests


class RestTests(unittest.TestCase):
    setUp = settings_tests.SettingsTests.setUp
    tearDown = settings_tests.SettingsTests.tearDown
    window = settings_tests.SettingsTests.window

    def asset_root(self):
        root = Path(self.directory.name) / 'assets'
        for name in ('idle', 'walk'):
            shutil.copytree(ASSET_ROOT / name, root / name)
        return root

    def add_clip(self, root, action, count):
        folder = root / action.value
        folder.mkdir(exist_ok=True)
        # Test-only copies of existing art; never installed as real rest assets.
        for index in range(1, count + 1):
            shutil.copyfile(ASSET_ROOT / 'idle/idle_01.png', folder / f'{action.value}_{index:02}.png')

    def test_no_optional_art_uses_idle(self):
        animation = SpriteAnimation(self.asset_root())
        self.assertFalse(animation.has_clip(Action.REST))
        animation.advance(Action.REST, .1)
        self.assertEqual(animation.action, Action.IDLE)
        self.assertEqual(animation.warnings, [])

    def test_invalid_optional_clip_is_ignored_and_can_reload(self):
        root = self.asset_root()
        folder = root / 'rest'
        folder.mkdir()
        (folder / 'rest_01.png').write_bytes(b'incomplete upload')
        animation = SpriteAnimation(root)
        self.assertFalse(animation.has_clip(Action.REST))
        self.assertEqual(len(animation.warnings), 1)
        self.add_clip(root, Action.REST, 4)
        self.assertTrue(SpriteAnimation(root).has_clip(Action.REST))
        (folder / 'rest_02.png').rename(folder / 'rest_06.png')
        self.assertFalse(SpriteAnimation(root).has_clip(Action.REST))

    def test_transitions_play_once_and_rest_loops(self):
        root = self.asset_root()
        for action, count in ((Action.REST, 4), (Action.SIT_DOWN, 3), (Action.STAND_UP, 3)):
            self.add_clip(root, action, count)
        animation = SpriteAnimation(root)
        animation.advance(Action.SIT_DOWN, 0)
        animation.advance(Action.SIT_DOWN, 99)
        self.assertEqual(animation.index, 2)
        animation.advance(Action.REST, 0)
        animation.advance(Action.REST, 2.5)
        self.assertEqual(animation.index, 1)
        controller = RestController(.45, .45)
        self.assertEqual(controller.update(True, .1), Action.SIT_DOWN)
        self.assertEqual(controller.update(True, .45), Action.REST)
        self.assertEqual(controller.update(False, .1), Action.STAND_UP)
        self.assertIsNone(controller.update(False, .45))
        self.assertEqual(controller.update(True, 0), Action.SIT_DOWN)
        self.assertEqual(controller.update(False, 0), Action.STAND_UP)
        self.assertEqual(controller.update(True, 0), Action.SIT_DOWN)

    def test_hot_reload_and_failed_required_load_preserves_current_art(self):
        root = self.asset_root()
        window = self.window()
        window.animation = SpriteAnimation(root)
        self.add_clip(root, Action.REST, 4)
        with patch.object(window.tray, 'showMessage'):
            self.assertTrue(window.reload_assets())
        self.assertTrue(window.animation.has_clip(Action.REST))
        window.set_mode('rest')
        x = window.avatar.x
        window._tick()
        self.assertEqual(window.animation.action, Action.REST)
        self.assertEqual(window.avatar.x, x)
        previous = window.animation
        (root / 'idle/idle_01.png').unlink()
        with patch('overlay.QMessageBox.warning'):
            self.assertFalse(window.reload_assets())
        self.assertIs(window.animation, previous)

    def test_rest_without_art_does_not_move_or_turn_at_screen_edge(self):
        window = self.window()
        window.avatar.direction = -1
        x = window.avatar.x
        window.set_mode('rest')
        window._tick()
        self.assertEqual(window.avatar.x, x)
        self.assertEqual(window.avatar.direction, -1)
        self.assertEqual(window.animation.action, Action.IDLE)
        window.set_mode('auto')
        with patch('overlay.routine_state', return_value='active'):
            window._tick()
        self.assertEqual(window.avatar.action, Action.WALK)

    def test_overlay_holds_position_until_standing_finishes(self):
        root = self.asset_root()
        for action in (Action.REST, Action.SIT_DOWN, Action.STAND_UP):
            self.add_clip(root, action, 3)
        window = self.window()
        window.animation = SpriteAnimation(root)
        window.rest_controller = window._make_rest_controller()
        window.avatar.x = (window.left + window.right) / 2
        x = window.avatar.x
        window.set_mode('rest')
        window._tick()
        self.assertEqual(window.animation.action, Action.SIT_DOWN)
        for _ in range(5):
            window._last -= .1
            window._tick()
        self.assertEqual(window.animation.action, Action.REST)
        self.assertEqual(window.avatar.x, x)
        window.set_mode('auto')
        with patch('overlay.routine_state', return_value='active'):
            window._tick()
            self.assertEqual(window.animation.action, Action.STAND_UP)
            self.assertEqual(window.avatar.x, x)
            for _ in range(5):
                window._last -= .1
                window._tick()
        self.assertEqual(window.animation.action, Action.WALK)
        self.assertNotEqual(window.avatar.x, x)
