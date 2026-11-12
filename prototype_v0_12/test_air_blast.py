"""AIR_BLAST v1.1 launch geometry, timing, cleanup and asset regression checks."""
from pathlib import Path
from dataclasses import replace
import json
import shutil
import unittest
from unittest.mock import patch

from PySide6.QtCore import QPointF, QRect, QRectF, Qt
from PySide6.QtGui import QImage, QPainter

from animation import ANCHOR, ASSET_ROOT, SpriteAnimation, VISIBLE_HEIGHT
from avatar import Action
from screens import screen_key
from test_screens import FakeScreen
import test_settings


class AirBlastTests(unittest.TestCase):
    setUp = test_settings.SettingsTests.setUp
    tearDown = test_settings.SettingsTests.tearDown
    window = test_settings.SettingsTests.window

    @classmethod
    def setUpClass(cls):
        cls.animation = SpriteAnimation()
        cls.effects = cls.animation.blast_effects

    def tick(self, window, dt=.02):
        with patch("overlay.time.monotonic", return_value=window._last + dt):
            window._tick()

    def test_launch_on_release_03_and_forward_duration(self):
        animation = self.animation
        animation.advance(Action.AIR_BLAST, 0)
        animation.elapsed = self.effects.launch - .001
        self.assertEqual(animation.index, 5)
        animation.elapsed = self.effects.launch
        self.assertEqual(animation.index, 6)
        self.assertEqual(self.effects.launch, .760)
        self.assertAlmostEqual(self.effects.flow + self.effects.fade, 1.2)
        self.assertLess(self.effects.launch + self.effects.flow + self.effects.fade,
                        animation.clip_duration(Action.AIR_BLAST))

    def test_palms_scale_and_mirror_about_rendered_ground_anchor(self):
        area = QRectF(-1600, -200, 1600, 960)
        ground = QPointF(-800, 740)
        for height in (80, 120, 180):
            for direction in (-1, 1):
                scene = self.effects.scene(.760, area, ground, height, direction, 6)
                ratio = height / 606
                self.assertAlmostEqual(scene.palm.x(), ground.x() + direction * (474 - 288) * ratio)
                self.assertAlmostEqual(scene.palm.y(), ground.y() + (232 - 650) * ratio)
                self.assertEqual(scene.direction, direction)

    def test_first_firing_frame_already_reaches_work_area_edge(self):
        area = QRectF(-1600, -200, 1600, 960)
        for x in (-1590, -800, -10):
            for direction in (-1, 1):
                for height in (80, 120, 180):
                    ground = QPointF(x, 735)
                    before = self.effects.scene(self.effects.launch - .001, area, ground, height, direction, 5)
                    self.assertTrue(before.front.isEmpty())
                    for time in (self.effects.launch, self.effects.launch + 1 / 60):
                        scene = self.effects.scene(time, area, ground, height, direction, 6)
                        expected = max(0, area.right() - scene.palm.x() if direction > 0
                                       else scene.palm.x() - area.left())
                        expected = min(expected, scene.flow_rect.width())
                        self.assertAlmostEqual(scene.front.width(), expected)
                        if expected > 0:
                            front = scene.world_rect(scene.front)
                            edge = front.right() if direction > 0 else front.left()
                            self.assertAlmostEqual(edge, scene.palm.x() + direction * expected)
                        self.assertTrue(area.contains(scene.bounds) or scene.bounds.isEmpty())

    def test_flow_height_uses_uniform_native_scale(self):
        self.effects.reset()
        scene = self.effects.scene(.760, QRectF(0, 0, 1920, 1040), QPointF(600, 1000), 120, 1, 6)
        source = self.effects.source_rects["flow_field"][0]
        self.assertAlmostEqual(scene.flow_rect.height(), source.height() * .4)
        self.assertAlmostEqual(scene.flow_rect.width(), source.width() * .4)

    def test_qscreen_integer_work_area_uses_full_width_without_off_by_one(self):
        area = QRect(-1600, -200, 1600, 960)
        for direction in (-1, 1):
            scene = self.effects.scene(.760, area, QPointF(-800, 740), 120, direction, 6)
            front = scene.world_rect(scene.front)
            self.assertAlmostEqual(front.right() if direction > 0 else front.left(),
                                   0 if direction > 0 else -1600)
            self.assertEqual(scene.area, QRectF(area))

    def test_backdraft_is_80_percent_height_and_stays_behind_character(self):
        area = QRectF(0, 0, 1920, 1040)
        ground = QPointF(900, 1000)
        for direction in (-1, 1):
            scene = self.effects.scene(.8, area, ground, 120, direction, 6)
            self.assertAlmostEqual(scene.rear.width(), 96)
            body_back = ground.x() + direction * (56 - 288) * 120 / 606
            rear = scene.world_rect(scene.rear)
            if direction > 0:
                self.assertLess(rear.right(), body_back)
            else:
                self.assertGreater(rear.left(), body_back)
        self.assertLess(self.effects.rear_opacity, .6)

    def test_both_layers_move_in_the_facing_direction(self):
        image = QImage(1920, 1040, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        phases = []
        for time in (.801, .811):
            scene = self.effects.scene(time, QRectF(image.rect()), QPointF(600, 1000), 120, 1, 6)
            with patch.object(self.effects, "_draw_tiles") as tiles:
                self.effects.paint(painter, scene)
                phases.append([call.args[6] for call in tiles.call_args_list])
        painter.end()
        # Rear intake, main flow and auxiliary streaks all advance along local +X.
        self.assertEqual(len(phases[0]), 1)
        for previous, current in zip(*phases):
            self.assertGreater(current, previous)

    def test_software_render_clips_at_palm_and_work_area(self):
        area = QRectF(30, 20, 900, 380)
        image = QImage(1000, 440, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        ground = QPointF(400, 350)
        scene = self.effects.scene(self.effects.launch, area, ground, 120, 1, 6)
        painter = QPainter(image)
        self.effects.paint(painter, scene)
        painter.end()
        self.assertEqual(image.pixelColor(950, 250).alpha(), 0)
        band = scene.world_rect(scene.front).toAlignedRect()
        self.assertGreater(sum(image.pixelColor(x, y).alpha()
                               for x in range(910, 929) for y in range(band.top(), band.bottom())), 0)
        self.assertTrue(scene.front.left() == 0)

    @patch("overlay.routine_state", return_value="active")
    def test_live_size_direction_pause_hide_stop_and_cleanup(self, _):
        window = self.window()
        window.set_mode("idle")
        window.avatar.x = (window.left + window.right) / 2
        window._layout_sprite()
        self.assertTrue(window.preview_air_blast())
        for _ in range(41):
            self.tick(window)
        effects = window.blast_window
        self.assertTrue(effects.isVisible())
        scene = effects.scene
        ground_x = window.x() + window._horizontal_padding + ANCHOR[0] * window.scale
        window._turn()
        self.assertAlmostEqual(scene.palm.x() + effects.scene.palm.x(), 2 * ground_x)
        window.set_paused(True)
        elapsed = window.animation.elapsed
        self.tick(window)
        self.assertEqual(window.animation.elapsed, elapsed)
        window.set_display_height(180)
        self.assertAlmostEqual(effects.scene.ratio, 180 / 606)
        window.set_hidden(True)
        self.assertFalse(effects.isVisible())
        window.set_hidden(False)
        self.assertTrue(effects.isVisible())
        window.stop_motion_preview()
        self.assertFalse(effects.isVisible())
        self.assertIsNone(effects.scene)
        self.assertEqual(window.animation.action, Action.IDLE)
        self.assertTrue(effects.windowFlags() & Qt.WindowType.WindowTransparentForInput)
        self.assertTrue(effects.windowFlags() & Qt.WindowType.WindowDoesNotAcceptFocus)

    @patch("overlay.routine_state", return_value="active")
    def test_monitor_change_and_drag_mode_keep_effect_input_transparent(self, _):
        window = self.window()
        window.set_mode("idle")
        window.preview_air_blast()
        for _ in range(41):
            self.tick(window)
        primary = test_settings.APP.primaryScreen()
        external = FakeScreen()
        original = window.preferences
        try:
            with patch("overlay.QApplication.screens", return_value=[primary, external]), patch.object(window, "setScreen"):
                window.preferences = replace(original, monitor=screen_key(external))
                window.apply_preferences()
                self.assertEqual(window.blast_window.scene.area, QRectF(external.availableGeometry()))
                self.assertTrue(QRectF(external.availableGeometry()).contains(window.blast_window.scene.bounds))
                window._set_interactive(True)
                self.assertTrue(window.blast_window.windowFlags() & Qt.WindowType.WindowTransparentForInput)
                self.assertFalse(window.click_through)
                window._set_interactive(False)
        finally:
            window.stop_motion_preview()
            window.preferences = original
            window.apply_preferences()

    @patch("overlay.routine_state", return_value="active")
    def test_natural_finish_recovers_and_hides_effect_window(self, _):
        window = self.window()
        window.set_mode("idle")
        window.preview_air_blast()
        seen = set()
        for _ in range(105):
            self.tick(window)
            if window.animation.action == Action.AIR_BLAST:
                seen.add(window.animation.index)
        self.assertEqual(seen, set(range(12)))
        self.assertEqual(window.animation.action, Action.IDLE)
        self.assertFalse(window.blast_window.isVisible())
        self.assertIsNone(window.blast_window.scene)
        self.assertEqual(window._horizontal_padding, 0)

    def test_missing_effect_or_malformed_metadata_uses_optional_fallback(self):
        root = Path(self.directory.name) / "aang"
        for name in ("idle", "walk", "air_blast_v3"):
            shutil.copytree(ASSET_ROOT / name, root / name)
        source = json.loads((ASSET_ROOT / "extra_clips.json").read_text(encoding="utf-8"))
        source["clips"] = {"air_blast": source["clips"]["air_blast"]}
        (root / "extra_clips.json").write_text(json.dumps(source), encoding="utf-8")
        config_path = root / "air_blast_v3/effects.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        for invalid in ([], dict(config, launch_ms=500), dict(config, flow_ms=1400),
                        dict(config, palm_offset=[float("nan"), 0])):
            config_path.write_text(json.dumps(invalid), encoding="utf-8")
            animation = SpriteAnimation(root)
            self.assertFalse(animation.has_clip(Action.AIR_BLAST))
            self.assertTrue(animation.warnings)
            self.assertIsNone(animation.blast_effects)
        config_path.write_text(json.dumps(dict(config, flow_ms=1000, fade_ms=500)), encoding="utf-8")
        animation = SpriteAnimation(root)
        self.assertTrue(animation.has_clip(Action.AIR_BLAST))
        self.assertAlmostEqual(animation.clip_duration(Action.AIR_BLAST), 2.3)
        config_path.write_text(json.dumps(config), encoding="utf-8")
        (root / "air_blast_v3/frames/projectile/air_blast_projectile_effect_03.png").unlink()
        animation = SpriteAnimation(root)
        self.assertFalse(animation.has_clip(Action.AIR_BLAST))
        animation.advance(Action.AIR_BLAST, 0)
        self.assertEqual(animation.action, Action.IDLE)
        self.assertTrue(animation.has_clip(Action.WALK))

    def test_cached_pixels_remain_bounded_across_many_sizes_and_times(self):
        keys = [frame.cacheKey() for stage in self.effects.frames.values() for frame in stage]
        pixels = sum(frame.width() * frame.height() for stage in self.effects.frames.values() for frame in stage)
        self.assertLess(pixels * 4, 25_000_000)
        for index in range(500):
            self.effects.scene(index / 250, QRectF(0, 0, 7680, 2160), QPointF(500, 2000),
                               (80, 120, 180)[index % 3], 1, 6)
        self.assertEqual(keys, [frame.cacheKey() for stage in self.effects.frames.values() for frame in stage])
