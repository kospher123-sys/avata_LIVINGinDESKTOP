"""Provisional V3 effects with one natural-length FLOW_FIELD per frame."""
from dataclasses import dataclass
import json
from pathlib import Path

from PySide6.QtCore import QPointF, QRect, QRectF, Qt
from PySide6.QtGui import QImage, QPainter

from air_blast import EffectAssetChecks, BlastScene


@dataclass
class LayerClocks:
    flow_elapsed: float = 0.0
    projectile_elapsed: float = 0.0
    projectile_position_heights: float = 0.0


@dataclass(frozen=True)
class StreakDraw:
    stage: str
    index: int
    rect: QRectF
    elapsed: float


@dataclass(frozen=True)
class BlastV3Scene(BlastScene):
    flow_index: int
    projectile_index: int
    dissipate_index: int
    flow_rect: QRectF
    projectile_rect: QRectF
    flow_time: float
    projectile_time: float
    streaks: tuple = ()


class AirBlastV3Effects(EffectAssetChecks):
    def __init__(self, path, load_frame, canvas, anchor, standing_height, frame_times):
        self.path = Path(path)
        config = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(config, dict) or config.get("version") != 3:
            raise ValueError("AIR_BLAST V3 메타데이터 버전을 확인하세요.")
        self.anchor = anchor
        self.standing_height = standing_height
        self.launch = self._number(config, "launch_ms", 0, 5000) / 1000
        if len(frame_times) != 12 or abs(self.launch - sum(frame_times[:6])) > 1e-6:
            raise ValueError("AIR_BLAST V3 발사는 RELEASE 03과 일치해야 합니다.")
        self.flow = self._number(config, "flow_ms", 100, 1400) / 1000
        self.fade = self._number(config, "fade_ms", 100, 1000) / 1000
        if not 1 <= self.flow + self.fade <= 1.5:
            raise ValueError("AIR_BLAST V3 전방 효과 시간은 1~1.5초여야 합니다.")
        palms = config["palms"]
        if not isinstance(palms, list) or len(palms) != 2:
            raise ValueError("기존 캐릭터의 양손 좌표가 필요합니다.")
        for point in palms:
            self._point(point, canvas)
        offset = config["palm_offset"]
        self._point(offset, (100, 100), lower=-100)
        self.palm = (max(p[0] for p in palms) + offset[0], sum(p[1] for p in palms) / 2 + offset[1])
        self.body_bounds = config["body_bounds"]
        if not isinstance(self.body_bounds, list) or len(self.body_bounds) != 12:
            raise ValueError("기존 캐릭터 12자세의 윤곽 정보가 필요합니다.")
        for bounds in self.body_bounds:
            if not isinstance(bounds, list) or len(bounds) != 4:
                raise ValueError("잘못된 캐릭터 윤곽 정보")
            self._point(bounds[:2], canvas)
            self._point(bounds[2:], canvas)
            if bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
                raise ValueError("잘못된 캐릭터 윤곽 범위")
        self.flow_scale = self._number(config, "flow_scale_at_120", .1, 1)
        self.effect_scale = self._number(config, "effect_scale_at_120", .1, 2)
        self.cast_scale = self._number(config, "cast_scale_at_120", .1, 2)
        self.dissipate_scale = self._number(config, "dissipate_scale_at_120", .1, 2)
        self.flow_frame_time = self._number(config, "flow_frame_ms", 20, 200) / 1000
        self.projectile_frame_time = self._number(config, "projectile_frame_ms", 20, 200) / 1000
        self.flow_opacity = self._number(config, "flow_opacity", 0, 1)
        self.speed = self._number(config, "projectile_heights_per_second", 1, 30)
        self.rear_width = self._number(config, "backdraft_width_heights", .1, 2)
        self.rear_opacity = self._number(config, "backdraft_opacity", 0, 1)
        self.projectiles = config["projectiles"]
        if not isinstance(self.projectiles, list) or not 2 <= len(self.projectiles) <= 8:
            raise ValueError("전경 칼바람 인스턴스는 2~8개가 필요합니다.")
        for item in self.projectiles:
            for key, low, high in (("delay_ms", 0, 300), ("start_heights", 0, 5),
                                   ("y_heights", -.5, .5), ("scale", .1, 1),
                                   ("speed", 1, 30), ("phase", 0, 5)):
                self._number(item, key, low, high)
            if type(item["phase"]) is not int:
                raise ValueError("잘못된 칼바람 위상")
        self.frames = {}
        self.source_rects = {}
        for stage, count in (("cast", 4), ("projectile", 6), ("dissipate", 4),
                             ("backdraft", 6), ("flow_field", 8)):
            records = config["frames"][stage]
            if not isinstance(records, list) or len(records) != count:
                raise ValueError(f"AIR_BLAST V3 {stage} 프레임 수를 확인하세요.")
            expected_canvas = (2048, 512) if stage == "flow_field" else (576, 704)
            expected_anchor = [0, 256] if stage == "flow_field" else [288, 352]
            self.frames[stage] = []
            self.source_rects[stage] = []
            for index, record in enumerate(records):
                if record["canvas"] != list(expected_canvas) or record["anchor"] != expected_anchor:
                    raise ValueError(f"AIR_BLAST V3 {stage} 캔버스와 배치 기준을 확인하세요.")
                source = (self.path.parent / record["file"]).resolve()
                expected_name = f"air_blast_{stage}_effect_{index + 1:02}.png"
                if not source.is_relative_to(self.path.parent.resolve()) or source.name != expected_name:
                    raise ValueError("잘못된 AIR_BLAST V3 프레임 경로 또는 순서")
                empty = stage == "dissipate" and index == 3
                image = load_frame(source, expected_canvas, allow_empty=empty)
                bounds = record["bbox"]
                if bounds is None:
                    if not empty:
                        raise ValueError("마지막 소멸 프레임만 비어 있을 수 있습니다.")
                    rgba = image.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
                    values = bytes(rgba.constBits())[3::4]
                    if max(values) != 0:
                        raise ValueError("소멸 04는 완전 투명해야 합니다.")
                    rectangle = QRect()
                else:
                    if (empty or not isinstance(bounds, list) or len(bounds) != 4
                            or any(type(n) is not int for n in bounds)
                            or not 0 <= bounds[0] < bounds[2] <= expected_canvas[0]
                            or not 0 <= bounds[1] < bounds[3] <= expected_canvas[1]):
                        raise ValueError("잘못된 AIR_BLAST V3 가시 영역")
                    rectangle = QRect(bounds[0], bounds[1], bounds[2] - bounds[0], bounds[3] - bounds[1])
                self.frames[stage].append(image.copy(rectangle) if not rectangle.isEmpty()
                                          else image.copy(QRect(0, 0, 1, 1)))
                self.source_rects[stage].append(QRectF(rectangle))
        self.reset()

    def reset(self):
        self.clocks = LayerClocks()
        self._last_elapsed = None
        self._last_active_time = 0.0

    def _advance_clocks(self, elapsed):
        if self._last_elapsed is not None and elapsed < self._last_elapsed:
            self.reset()
        active_time = max(0.0, min(elapsed - self.launch, self.flow + self.fade))
        delta = max(0.0, active_time - self._last_active_time)
        self.clocks.flow_elapsed += delta
        self.clocks.projectile_elapsed += delta
        self.clocks.projectile_position_heights += delta * self.speed
        self._last_active_time = active_time
        self._last_elapsed = elapsed

    @staticmethod
    def _target(source, scale, x=0.0, anchor_y=352):
        return QRectF(x, (source.top() - anchor_y) * scale, source.width() * scale, source.height() * scale)

    def scene(self, elapsed, area, ground, character_height, direction, character_index):
        area = QRectF(area)
        ratio = character_height / self.standing_height
        direction = 1 if direction > 0 else -1
        palm = QPointF(ground.x() + direction * (self.palm[0] - self.anchor[0]) * ratio,
                       ground.y() + (self.palm[1] - self.anchor[1]) * ratio)
        front_time = elapsed - self.launch
        if abs(front_time) < 1e-9:
            front_time = 0.0
        if elapsed >= self.launch + self.flow + self.fade:
            self.reset()
        else:
            self._advance_clocks(elapsed)
        flow_index = int(self.clocks.flow_elapsed / self.flow_frame_time + 1e-9) % 8
        projectile_index = int(self.clocks.projectile_elapsed / self.projectile_frame_time + 1e-9) % 6
        dissipate_index = min(3, max(0, int((front_time - self.flow) / self.fade * 4)))
        display_scale = character_height / 120
        flow_rect = self._target(self.source_rects["flow_field"][flow_index],
                                 self.flow_scale * display_scale, anchor_y=256)
        stage = "dissipate" if front_time >= self.flow else "projectile"
        index = dissipate_index if stage == "dissipate" else projectile_index
        scale = self.dissipate_scale if stage == "dissipate" else self.effect_scale
        position = self.clocks.projectile_position_heights * character_height
        projectile_rect = self._target(self.source_rects[stage][index], scale * display_scale, position)
        streaks = []
        natural_length = max(rect.width() for rect in self.source_rects["flow_field"]) * self.flow_scale * display_scale
        for item in self.projectiles:
            delay = item["delay_ms"] / 1000
            age = self.clocks.projectile_elapsed - delay
            if age < 0 or not 0 <= front_time < self.flow + self.fade:
                continue
            fade_start = self.flow + delay * .25
            fading = front_time >= fade_start
            image_stage = "dissipate" if fading else "projectile"
            image_index = (min(3, int((front_time - fade_start) / (self.flow + self.fade - fade_start) * 4))
                           if fading else (int(age / self.projectile_frame_time + 1e-9) + item["phase"]) % 6)
            width = max(rect.width() for rect in self.source_rects["projectile"]) * item["scale"] * display_scale
            span = natural_length + width
            distance = item["start_heights"] * character_height + age * item["speed"] * character_height
            if fading:
                at_fade = item["start_heights"] * character_height + (fade_start - delay) * item["speed"] * character_height
                x = (at_fade + width) % span - width + (front_time - fade_start) * item["speed"] * character_height
            else:
                x = (distance + width) % span - width
            image_scale = item["scale"] * (self.dissipate_scale / self.effect_scale if fading else 1) * display_scale
            rectangle = self._target(self.source_rects[image_stage][image_index], image_scale, x)
            rectangle.translate(0, item["y_heights"] * character_height)
            streaks.append(StreakDraw(image_stage, image_index, rectangle, age))
        front = QRectF()
        if 0 <= front_time < self.flow + self.fade:
            extent = area.right() - palm.x() if direction > 0 else palm.x() - area.left()
            band = flow_rect.united(projectile_rect) if not projectile_rect.isEmpty() else flow_rect
            for streak in streaks:
                if not streak.rect.isEmpty():
                    band = band.united(streak.rect)
            front = QRectF(0, band.top(), min(flow_rect.width(), max(0.0, extent)), band.height())
        rear = QRectF()
        if 0 <= elapsed < self.launch + self.flow:
            back = self.body_bounds[min(character_index, 11)][0]
            width = character_height * self.rear_width
            height = width * max(image.height() / image.width() for image in self.frames["backdraft"])
            rear = QRectF((back - self.palm[0]) * ratio - width - 1,
                          (self.anchor[1] - self.standing_height * .42 - self.palm[1]) * ratio - height / 2,
                          width, height)
        return BlastV3Scene(area, palm, direction, ratio, elapsed, front_time, front, rear,
                            flow_index, projectile_index, dissipate_index, flow_rect, projectile_rect,
                            self.clocks.flow_elapsed, self.clocks.projectile_elapsed, tuple(streaks))

    def paint(self, painter, scene):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setClipRect(scene.area, Qt.ClipOperation.IntersectClip)
        painter.translate(scene.palm)
        painter.scale(scene.direction, 1)
        height = scene.ratio * self.standing_height
        if not scene.rear.isEmpty():
            image = self.frames["backdraft"][int(scene.elapsed / .07) % 6]
            rear_height = scene.rear.width() * image.height() / image.width()
            self._draw_tiles(painter, [image], scene.rear, scene.rear.width(), rear_height,
                             scene.rear.center().y() - rear_height / 2,
                             scene.elapsed * height * 3, self.rear_opacity, scene.rear.width())
        if not scene.front.isEmpty():
            fade = max(0.0, min(1.0, 1 - (scene.front_elapsed - self.flow) / self.fade))
            painter.save()
            painter.setClipRect(scene.front, Qt.ClipOperation.IntersectClip)
            # FLOW_FIELD is drawn exactly once with uniform scaling and its own clock.
            image = self.frames["flow_field"][scene.flow_index]
            painter.setOpacity(self.flow_opacity * fade)
            painter.drawPixmap(scene.flow_rect, image, QRectF(image.rect()))
            for streak in scene.streaks:
                if streak.rect.isEmpty():
                    continue
                image = self.frames[streak.stage][streak.index]
                painter.setOpacity(1.0)
                painter.drawPixmap(streak.rect, image, QRectF(image.rect()))
            if scene.front_elapsed < .12:
                index = min(3, int(scene.front_elapsed / .03))
                image = self.frames["cast"][index]
                target = self._target(self.source_rects["cast"][index], self.cast_scale * height / 120)
                painter.drawPixmap(target, image, QRectF(image.rect()))
            painter.restore()
        painter.restore()
