"""Transparent desktop sprite overlay; click-through by default."""
import math
import time

from PySide6.QtCore import QPoint, QRectF, Qt, QTimer
from PySide6.QtGui import QActionGroup, QPainter
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon, QWidget

from animation import ANCHOR, CANVAS, VISIBLE_HEIGHT, SpriteAnimation
from avatar import Action, Avatar


class AvatarOverlay(QWidget):
    def __init__(self, height=150):
        super().__init__()
        self.animation = SpriteAnimation()
        self.avatar = Avatar()
        self.mode = "auto"
        self.drag_offset = None
        self.click_through = True
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint
                            | Qt.WindowType.WindowStaysOnTopHint
                            | Qt.WindowType.Tool
                            | Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.display_screen = QApplication.primaryScreen()
        self.display_screen.availableGeometryChanged.connect(self._refresh_bounds)
        self.set_display_height(height)
        self.avatar.x = float(self.left)
        self.move(self.left, self.floor)
        self._setup_tray()
        self._last = time.monotonic()
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

    def set_display_height(self, height):
        self.display_height = height
        self.scale = height / VISIBLE_HEIGHT
        self.setFixedSize(math.ceil(CANVAS[0] * self.scale), math.ceil(CANVAS[1] * self.scale))
        self._refresh_bounds()

    def _refresh_bounds(self, *args):
        area = self.display_screen.availableGeometry()
        self.left = area.left()
        self.right = max(self.left, area.right() + 1 - self.width())
        # Align the common foot anchor, rather than the transparent canvas bottom.
        self.floor = round(area.bottom() - ANCHOR[1] * self.scale)
        self.avatar.x = max(self.left, min(self.avatar.x, self.right))
        self.move(round(self.avatar.x), self.floor)

    def _setup_tray(self):
        self.menu = QMenu()
        self.input_action = self.menu.addAction("드래그 모드 (클릭 통과 해제)")
        self.input_action.setCheckable(True)
        self.input_action.toggled.connect(self._set_interactive)
        modes = self.menu.addMenu("동작")
        self.mode_group = QActionGroup(self)
        for label, mode in (("자동", "auto"), ("대기", "idle"), ("걷기", "walk")):
            action = modes.addAction(label)
            action.setCheckable(True)
            action.setChecked(mode == "auto")
            self.mode_group.addAction(action)
            action.triggered.connect(lambda checked=False, value=mode: self.set_mode(value))
        sizes = self.menu.addMenu("캐릭터 높이")
        self.size_group = QActionGroup(self)
        for height in (120, 150, 180):
            action = sizes.addAction(f"{height}px")
            action.setCheckable(True)
            action.setChecked(height == self.display_height)
            self.size_group.addAction(action)
            action.triggered.connect(lambda checked=False, value=height: self.set_display_height(value))
        self.menu.addAction("방향 전환", self._turn)
        self.menu.addSeparator()
        self.menu.addAction("종료", QApplication.instance().quit)
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        self.tray.setToolTip("Avatar Living in Desktop — v0.3 아앙")
        self.tray.setContextMenu(self.menu)
        self.tray.show()

    def _turn(self):
        self.avatar.direction *= -1
        self.update()

    def set_mode(self, mode):
        self.mode = mode
        if mode != "auto":
            self.avatar.action = Action(mode)
        self.avatar.remaining = 4.0

    def _set_interactive(self, enabled):
        self.drag_offset = None
        self.click_through = not enabled
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, not enabled)
        self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, not enabled)
        self.show()

    def _tick(self):
        now = time.monotonic()
        dt = max(0.0, min(now - self._last, 0.1))
        self._last = now
        if self.drag_offset is None:
            if self.mode != "auto":
                self.avatar.action = Action(self.mode)
                self.avatar.remaining = 1.0
            self.avatar.update(dt, self.left, self.right)
            self.move(round(self.avatar.x), self.y())
        action = Action.IDLE if self.drag_offset is not None else self.avatar.action
        self.animation.advance(action, dt)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        # Mirror around the exact common anchor, including fractional scaling.
        if self.avatar.direction < 0:
            painter.translate(2 * ANCHOR[0] * self.scale, 0)
            painter.scale(-1, 1)
        painter.drawPixmap(QRectF(0, 0, CANVAS[0] * self.scale, CANVAS[1] * self.scale),
                           self.animation.pixmap, QRectF(0, 0, *CANVAS))
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset = event.globalPosition().toPoint() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_offset is not None:
            position = event.globalPosition().toPoint() - self.drag_offset
            area = self.display_screen.availableGeometry()
            x = max(self.left, min(position.x(), self.right))
            y = max(area.top(), min(position.y(), self.floor))
            self.avatar.x = float(x)
            self.move(QPoint(x, y))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset = None

    def contextMenuEvent(self, event):
        self.menu.exec(event.globalPos())
