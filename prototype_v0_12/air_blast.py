"""Screen-bounded, time-based AIR_BLAST effects using the reviewed PNG layers."""
from dataclasses import dataclass
import json
import math
from pathlib import Path

from PySide6.QtCore import QPointF, QRect, QRectF, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget


@dataclass(frozen=True)
class BlastScene:
    area: QRectF
    palm: QPointF
    direction: int
    ratio: float
    elapsed: float
    front_elapsed: float
    front: QRectF
    rear: QRectF

    def world_rect(self, rect):
        x = rect.left() if self.direction > 0 else -rect.right()
        return QRectF(self.palm.x() + x, self.palm.y() + rect.top(), rect.width(), rect.height())

    @property
    def bounds(self):
        result = self.world_rect(self.rear)
        if not self.front.isEmpty():
            result = result.united(self.world_rect(self.front))
        return result.intersected(self.area)


class AirBlastEffects:
    def __init__(self, path, load_frame, canvas, anchor, standing_height, frame_times):
        self.path = Path(path)
        config = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(config, dict) or config.get("version") != 1:
            raise ValueError("AIR_BLAST 효과 메타데이터 버전을 확인하세요.")
        self.anchor = anchor
        self.standing_height = standing_height
        self.launch = self._number(config, "launch_ms", 0, 5000) / 1000
        # RELEASE 03 must be the first frame displaying the full-width effect.
        if len(frame_times) != 12 or abs(self.launch - sum(frame_times[:6])) > 1e-6:
            raise ValueError("AIR_BLAST 발사 시점과 RELEASE 03이 일치해야 합니다.")
        self.flow = self._number(config, "flow_ms", 100, 1400) / 1000
        self.fade = self._number(config, "fade_ms", 100, 1000) / 1000
        if not 1 <= self.flow + self.fade <= 1.5:
            raise ValueError("AIR_BLAST 전방 효과 재생 시간은 1~1.5초여야 합니다.")
        palms = config["palms"]
        if not isinstance(palms, list) or len(palms) != 2:
            raise ValueError("AIR_BLAST 양손 좌표가 필요합니다.")
        for point in palms:
            self._point(point, canvas)
        offset = config["palm_offset"]
        self._point(offset, (100, 100), lower=-100)
        self.palm = (max(p[0] for p in palms) + offset[0], sum(p[1] for p in palms) / 2 + offset[1])
        self.body_bounds = config["body_bounds"]
        if not isinstance(self.body_bounds, list) or len(self.body_bounds) != 12:
            raise ValueError("AIR_BLAST 캐릭터 윤곽 좌표가 필요합니다.")
        for bounds in self.body_bounds:
            if not isinstance(bounds, list) or len(bounds) != 4:
                raise ValueError("잘못된 캐릭터 윤곽 좌표")
            self._point(bounds[:2], canvas)
            self._point(bounds[2:], canvas)
            if bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
                raise ValueError("잘못된 캐릭터 윤곽 범위")
        self.forward_scale = self._number(config, "forward_source_scale", .1, 10)
        self.speed = self._number(config, "speed_heights_per_second", 1, 30)
        self.density = self._number(config, "density", .5, 2)
        self.rear_width = self._number(config, "backdraft_width_heights", .7, .9)
        self.rear_opacity = self._number(config, "backdraft_opacity", .1, .6)
        self.frames = {}
        self.source_rects = {}
        for stage, count in (("cast", 4), ("projectile", 6), ("dissipate", 4), ("backdraft", 6)):
            records = config["frames"][stage]
            if not isinstance(records, list) or len(records) != count:
                raise ValueError(f"AIR_BLAST {stage} 프레임 수를 확인하세요.")
            images = []
            rectangles = []
            union = QRect()
            for record in records:
                source = (self.path.parent / record["file"]).resolve()
                if not source.is_relative_to(self.path.parent.resolve()):
                    raise ValueError("AIR_BLAST 효과 경로가 자산 폴더를 벗어납니다.")
                bounds = record["bbox"]
                if (not isinstance(bounds, list) or len(bounds) != 4
                        or any(type(n) is not int for n in bounds)
                        or not 0 <= bounds[0] < bounds[2] <= 640
                        or not 0 <= bounds[1] < bounds[3] <= 288):
                    raise ValueError("잘못된 AIR_BLAST 효과 영역")
                rectangle = QRect(bounds[0], bounds[1], bounds[2] - bounds[0], bounds[3] - bounds[1])
                rectangles.append(rectangle)
                union = union.united(rectangle)
                images.append(load_frame(source, (640, 288)))
                self._number(record, "duration_ms", 20, 1000)
            # Cache only the shared visible region, preserving frame registration.
            self.frames[stage] = [image.copy(rectangle if stage == "backdraft" else union)
                                  for image, rectangle in zip(images, rectangles)]
            self.source_rects[stage] = QRectF(union)

    @staticmethod
    def _number(config, key, minimum, maximum):
        value = config[key]
        if type(value) not in (int, float) or not math.isfinite(value) or not minimum <= value <= maximum:
            raise ValueError(f"잘못된 AIR_BLAST 설정: {key}")
        return value

    @staticmethod
    def _point(point, limits, lower=0):
        if (not isinstance(point, list) or len(point) != 2
                or any(type(n) not in (int, float) or not math.isfinite(n) or not lower <= n <= limit
                       for n, limit in zip(point, limits))):
            raise ValueError("잘못된 AIR_BLAST 좌표")

    def scene(self, elapsed, area, ground, character_height, direction, character_index):
        # QScreen supplies QRect with inclusive right/bottom coordinates.
        area = QRectF(area)
        ratio = character_height / self.standing_height
        direction = 1 if direction > 0 else -1
        palm = QPointF(ground.x() + direction * (self.palm[0] - self.anchor[0]) * ratio,
                       ground.y() + (self.palm[1] - self.anchor[1]) * ratio)
        front_elapsed = elapsed - self.launch
        if abs(front_elapsed) < 1e-9:
            front_elapsed = 0.0
        front = QRectF()
        if 0 <= front_elapsed < self.flow + self.fade:
            extent = area.right() - palm.x() if direction > 0 else palm.x() - area.left()
            source = self.source_rects["projectile"]
            front = QRectF(0, (source.top() - 144) * ratio * self.forward_scale,
                           max(0.0, extent), source.height() * ratio * self.forward_scale)
        rear = QRectF()
        if 0 <= elapsed < self.launch + self.flow:
            back = self.body_bounds[min(character_index, 11)][0]
            width = character_height * self.rear_width
            height = width * max(image.height() / image.width() for image in self.frames["backdraft"])
            rear = QRectF((back - self.palm[0]) * ratio - width - 1,
                          (self.anchor[1] - self.standing_height * .42 - self.palm[1]) * ratio - height / 2,
                          width, height)
        return BlastScene(area, palm, direction, ratio, elapsed, front_elapsed, front, rear)

    @staticmethod
    def _draw_tiles(painter, images, clip, width, height, y, phase, opacity, spacing, frame_index=0):
        if clip.isEmpty():
            return
        painter.save()
        painter.setClipRect(clip, Qt.ClipOperation.IntersectClip)
        painter.setOpacity(opacity)
        x = clip.left() - width + phase % spacing
        tile_index = -math.floor(phase / spacing)
        while x < clip.right():
            image = images[(frame_index + tile_index) % len(images)]
            painter.drawPixmap(QRectF(x, y, width, height), image, QRectF(image.rect()))
            x += spacing
            tile_index += 1
        painter.restore()

    def paint(self, painter, scene):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setClipRect(scene.area, Qt.ClipOperation.IntersectClip)
        painter.translate(scene.palm)
        painter.scale(scene.direction, 1)
        height = scene.ratio * self.standing_height
        if not scene.rear.isEmpty():
            image = self.frames["backdraft"][int(scene.elapsed / .06) % 6]
            rear_height = scene.rear.width() * image.height() / image.width()
            self._draw_tiles(painter, [image], scene.rear, scene.rear.width(), rear_height,
                             scene.rear.center().y() - rear_height / 2, scene.elapsed * height * 3,
                             self.rear_opacity, scene.rear.width())
        if not scene.front.isEmpty():
            time = scene.front_elapsed
            stage = "projectile"
            index = int(time / .045) % 6
            opacity = 1.0
            if time >= self.flow:
                stage = "dissipate"
                index = min(3, int((time - self.flow) / self.fade * 4))
                opacity = max(0.0, 1 - (time - self.flow) / self.fade)
            source = self.source_rects[stage]
            width = source.width() * scene.ratio * self.forward_scale
            tile_height = source.height() * scene.ratio * self.forward_scale
            y = (source.top() - 144) * scene.ratio * self.forward_scale
            speed = height * self.speed
            spacing = width * .82 / self.density
            self._draw_tiles(painter, self.frames[stage], scene.front, width, tile_height, y,
                             time * speed, opacity * .85, spacing, index)
            # A second, lighter layer travels faster and breaks identical tile phases.
            self._draw_tiles(painter, self.frames["projectile"], scene.front,
                             width * .55, tile_height * .55, y + tile_height * .22,
                             time * speed * 1.7 + spacing * .37, opacity * .3, spacing * .7, index + 3)
            if time < .12:
                image = self.frames["cast"][min(3, int(time / .03))]
                source = self.source_rects["cast"]
                target = QRectF(0, -source.height() * scene.ratio / 2,
                                source.width() * scene.ratio, source.height() * scene.ratio)
                painter.save()
                painter.setClipRect(scene.front, Qt.ClipOperation.IntersectClip)
                painter.drawPixmap(target, image, QRectF(image.rect()))
                painter.restore()
        painter.restore()


class AirBlastEffectWindow(QWidget):
    """An input-transparent effect window, bounded to the selected work area."""
    def __init__(self, owner):
        super().__init__(owner, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint
                         | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowTransparentForInput
                         | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.renderer = None
        self.scene = None

    def present(self, renderer=None, scene=None):
        if scene is None or scene.bounds.isEmpty():
            self.scene = None
            self.renderer = None
            self.hide()
            return
        self.renderer = renderer
        self.scene = scene
        bounds = scene.bounds.toAlignedRect().intersected(scene.area.toAlignedRect())
        self.setGeometry(bounds)
        self.show()
        self.update()

    def paintEvent(self, event):
        if self.scene is None:
            return
        painter = QPainter(self)
        painter.translate(-self.x(), -self.y())
        self.renderer.paint(painter, self.scene)
        painter.end()
