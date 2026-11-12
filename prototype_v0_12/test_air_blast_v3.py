"""V3 natural-length rendering, independent layers and motion-preserving drag."""
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt
from PySide6.QtGui import QImage, QPainter

from air_blast_v3 import AirBlastV3Effects
from animation import ASSET_ROOT, SpriteAnimation
from avatar import Action
from overlay import AvatarOverlay
from settings import SettingsStore
import test_settings


class PointerEvent:
    def __init__(self, x, y):
        self.position = QPointF(x, y)

    def button(self):
        return Qt.MouseButton.LeftButton

    def globalPosition(self):
        return self.position

    def accept(self):
        pass


class AirBlastV3Tests(unittest.TestCase):
    setUp = test_settings.SettingsTests.setUp
    tearDown = test_settings.SettingsTests.tearDown

    def window(self):
        window = AvatarOverlay(SettingsStore(self.path), review_v3=True)
        window.timer.stop()
        self.windows.append(window)
        return window

    @classmethod
    def setUpClass(cls):
        cls.animation = SpriteAnimation(review_v3=True)

    def tick(self, window, dt=.02):
        with patch("overlay.time.monotonic", return_value=window._last + dt):
            window._tick()

    def test_explicit_variant_keeps_character_and_stable_mapping(self):
        stable = SpriteAnimation()
        candidate = self.animation
        self.assertIsInstance(candidate.blast_effects, AirBlastV3Effects)
        self.assertIsInstance(stable.blast_effects, AirBlastV3Effects)
        self.assertFalse(candidate.warnings)
        self.assertEqual(len(candidate.frames[Action.AIR_BLAST]), 12)
        for old, new in zip(stable.frames[Action.AIR_BLAST], candidate.frames[Action.AIR_BLAST]):
            self.assertEqual(old.toImage(), new.toImage())
        self.assertEqual({k: len(v) for k, v in candidate.blast_effects.frames.items()},
                         {"cast": 4, "projectile": 6, "dissipate": 4, "backdraft": 6, "flow_field": 8})

    def test_first_frame_has_full_valid_length_and_wide_tail_is_blank(self):
        effects = self.animation.blast_effects
        effects.reset()
        scene = effects.scene(.760, QRectF(0, 0, 2560, 1400), QPointF(300, 1300), 120, 1, 6)
        self.assertEqual(scene.flow_index, 0)
        self.assertAlmostEqual(scene.flow_rect.width(), (1992 - 70) * .4)
        self.assertAlmostEqual(scene.front.width(), 768.8)
        self.assertLess(scene.world_rect(scene.front).right(), scene.area.right())
        self.assertEqual(scene.flow_rect.left(), 0)
        self.assertEqual(scene.projectile_rect.left(), 0)

    def test_narrow_screen_clips_without_scaling_source(self):
        effects = self.animation.blast_effects
        effects.reset()
        scene = effects.scene(.760, QRectF(0, 0, 400, 900), QPointF(300, 800), 120, 1, 6)
        self.assertLess(scene.front.width(), scene.flow_rect.width())
        self.assertAlmostEqual(scene.world_rect(scene.front).right(), 400)
        self.assertAlmostEqual(scene.flow_rect.width(), 768.8)

    def test_all_eight_widths_and_short_candidate_are_preserved(self):
        effects = self.animation.blast_effects
        effects.reset()
        widths = []
        for i in range(9):
            scene = effects.scene(.760 + i * .060, QRectF(0, 0, 2560, 1400),
                                  QPointF(300, 1300), 120, 1, 6)
            self.assertEqual(scene.flow_index, i % 8)
            source = effects.source_rects["flow_field"][i % 8]
            self.assertAlmostEqual(scene.flow_rect.width() / source.width(), .4)
            self.assertAlmostEqual(scene.flow_rect.height() / source.height(), .4)
            widths.append(scene.flow_rect.width())
        self.assertAlmostEqual(widths[7], 584.8)
        self.assertLess(widths[7], widths[0] * .8)
        self.assertEqual(widths[0], widths[8])

    def test_independent_clocks_positions_and_reversed_frame_periods(self):
        effects = self.animation.blast_effects
        effects.reset()
        area, ground = QRectF(0, 0, 2560, 1400), QPointF(300, 1300)
        scene = effects.scene(.760 + .065, area, ground, 120, 1, 6)
        self.assertEqual((scene.flow_index, scene.projectile_index), (1, 0))
        self.assertAlmostEqual(scene.projectile_rect.left(), .065 * 6 * 120)
        effects.clocks.projectile_elapsed += .14
        changed = effects.scene(.760 + .065, area, ground, 120, 1, 6)
        self.assertEqual(changed.flow_index, scene.flow_index)
        self.assertEqual(changed.projectile_index, 2)
        with patch.object(effects, "flow_frame_time", .07), patch.object(effects, "projectile_frame_time", .06):
            effects.reset()
            scene = effects.scene(.760 + .065, area, ground, 120, 1, 6)
            self.assertEqual((scene.flow_index, scene.projectile_index), (0, 1))

    def test_one_flow_draw_uniform_scale_and_no_front_tiling(self):
        effects = self.animation.blast_effects
        effects.reset()
        scene = effects.scene(.8, QRectF(0, 0, 3000, 1000), QPointF(100, 900), 120, 1, 6)
        image = QImage(3000, 1000, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        # The inherited tiling helper is used exclusively for the small rear intake.
        with patch.object(effects, "_draw_tiles") as tiled:
            effects.paint(painter, scene)
            self.assertEqual(tiled.call_count, 1)
            self.assertEqual(tiled.call_args.args[2], scene.rear)
        painter.end()
        front = scene.world_rect(scene.front)
        x = int(front.right()) + 3
        self.assertTrue(all(image.pixelColor(x, y).alpha() == 0
                            for y in range(int(front.top()), int(front.bottom()))))

    def test_mirror_and_size_keep_palm_and_natural_end(self):
        effects = self.animation.blast_effects
        for height in (80, 120, 180):
            for direction in (-1, 1):
                effects.reset()
                scene = effects.scene(.760, QRectF(-1600, -200, 3200, 1400),
                                      QPointF(0, 1000), height, direction, 6)
                self.assertAlmostEqual(scene.palm.x(), direction * 186 * height / 606)
                self.assertAlmostEqual(scene.flow_rect.width(), 768.8 * height / 120)
                edge = scene.world_rect(scene.front).right() if direction > 0 else scene.world_rect(scene.front).left()
                self.assertAlmostEqual(edge, scene.palm.x() + direction * scene.front.width())

    def test_dissipate_moves_forward_then_clears_clocks(self):
        effects = self.animation.blast_effects
        effects.reset()
        area, ground = QRectF(0, 0, 2560, 1400), QPointF(300, 1300)
        last_position = -1
        for time in (1.59, 1.60, 1.69, 1.78):
            scene = effects.scene(time, area, ground, 120, 1, 8)
            self.assertGreater(scene.projectile_rect.x(), last_position)
            last_position = scene.projectile_rect.x()
        scene = effects.scene(1.90, area, ground, 120, 1, 11)
        self.assertEqual(scene.dissipate_index, 3)
        self.assertTrue(scene.projectile_rect.isEmpty())
        scene = effects.scene(1.96, area, ground, 120, 1, 11)
        self.assertTrue(scene.front.isEmpty())
        self.assertEqual(effects.clocks.flow_elapsed, 0)
        self.assertEqual(effects.clocks.projectile_position_heights, 0)

    @patch("overlay.routine_state", return_value="active")
    def test_cancel_recast_and_missing_candidate_fall_back(self, _):
        window = self.window()
        window.set_mode("idle")
        for _ in range(2):
            self.assertTrue(window.preview_air_blast())
            for _ in range(43):
                self.tick(window)
            self.assertGreater(window.animation.blast_effects.clocks.flow_elapsed, 0)
            window.stop_motion_preview()
            self.assertEqual(window.animation.blast_effects.clocks.flow_elapsed, 0)
            self.assertIsNone(window.blast_window.scene)
        root = Path(self.directory.name) / "aang"
        for name in ("idle", "walk", "air_trick", "frames_look_around", "air_blast_v3"):
            shutil.copytree(ASSET_ROOT / name, root / name)
        for name in ("extra_clips.json",):
            shutil.copy2(ASSET_ROOT / name, root / name)
        (root / "air_blast_v3/frames/flow_field/air_blast_flow_field_effect_08.png").unlink()
        animation = SpriteAnimation(root, review_v3=True)
        self.assertTrue(animation.warnings)
        self.assertFalse(animation.has_clip(Action.AIR_BLAST))
        self.assertNotIsInstance(animation.blast_effects, AirBlastV3Effects)

    @patch("overlay.routine_state", return_value="active")
    def test_drag_keeps_blast_running_and_moves_emitter_without_restart(self, _):
        window = self.window()
        window.set_mode("idle")
        window._set_interactive(True)
        window.preview_air_blast()
        for _ in range(43):
            self.tick(window)
        old = window.blast_window.scene
        elapsed = window.animation.elapsed
        cursor = QPointF(window.x() + 35, window.y() + 50)
        window.mousePressEvent(PointerEvent(cursor.x(), cursor.y()))
        window.mouseMoveEvent(PointerEvent(cursor.x() + 100, cursor.y() - 50))
        self.assertEqual(window.animation.elapsed, elapsed)
        self.assertAlmostEqual(window.blast_window.scene.palm.x() - old.palm.x(), 100)
        self.assertAlmostEqual(window.blast_window.scene.palm.y() - old.palm.y(), -50)
        self.tick(window)
        self.assertEqual(window.animation.action, Action.AIR_BLAST)
        self.assertGreater(window.animation.elapsed, elapsed)
        for _ in range(65):
            self.tick(window)
        self.assertEqual(window.animation.action, Action.IDLE)
        self.assertIsNone(window.blast_window.scene)
        window.mouseReleaseEvent(PointerEvent(cursor.x() + 100, cursor.y() - 50))
        self.assertIsNone(window.drag_offset)

    @patch("overlay.routine_state", return_value="active")
    def test_mode_change_while_dragging_cancels_one_shot(self, _):
        window = self.window()
        window.set_mode("idle")
        self.assertTrue(window.preview_look())
        self.tick(window)
        window.drag_offset = QPoint(10, 10)
        window.set_mode("walk")
        self.tick(window)
        self.assertFalse(window.idle_look.playing)
        self.assertEqual(window.animation.action, Action.WALK)

    @patch("overlay.routine_state", return_value="active")
    def test_drag_keeps_walk_look_trick_and_rest_sequences(self, _):
        window = self.window()
        window.set_mode("walk")
        self.tick(window)
        window.drag_offset = QPoint(10, 10)
        x, remaining = window.avatar.x, window.avatar.remaining
        for _ in range(10):
            self.tick(window)
        self.assertEqual(window.animation.action, Action.WALK)
        self.assertEqual(window.avatar.x, x)
        self.assertEqual(window.avatar.remaining, remaining)
        self.assertGreater(window.animation.elapsed, 0)
        window.drag_offset = None
        window.set_mode("idle")
        for start, action in ((window.preview_look, Action.LOOK_AROUND),
                              (window.preview_air_trick, Action.AIR_TRICK),
                              (window.start_motion_preview, Action.SIT_DOWN)):
            window.stop_motion_preview()
            window.idle_look.cancel()
            self.assertTrue(start())
            self.tick(window)
            window.drag_offset = QPoint(10, 10)
            elapsed = window.animation.elapsed
            self.tick(window)
            self.assertEqual(window.animation.action, action)
            self.assertGreater(window.animation.elapsed, elapsed)
            window.drag_offset = None
