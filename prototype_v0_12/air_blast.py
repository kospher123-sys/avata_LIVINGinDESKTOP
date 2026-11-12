"""Screen-bounded, time-based AIR_BLAST effects using the reviewed PNG layers."""
from dataclasses import dataclass
import math

from PySide6.QtCore import QPointF, QRectF, Qt
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


class EffectAssetChecks:
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
