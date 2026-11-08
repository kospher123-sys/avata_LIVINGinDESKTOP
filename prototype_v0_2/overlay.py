"""Always-on-top transparent window with a procedural fallback avatar."""
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu, QStyle

from avatar import Action, Avatar


class AvatarOverlay(QWidget):
    WIDTH = 90
    HEIGHT = 120

    def __init__(self):
        super().__init__()
        self.avatar = Avatar()
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.screen = QApplication.primaryScreen()
        self.screen.availableGeometryChanged.connect(self._refresh_bounds)
        self._refresh_bounds()
        self.avatar.x = float(self.left)
        self.move(self.left, self.floor)

        self._setup_tray()
        self._last = time.monotonic()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(33)

    def _refresh_bounds(self, *args):
        area = self.screen.availableGeometry()
        self.left = area.left()
        self.right = max(self.left, area.right() - self.WIDTH + 1)
        self.floor = area.bottom() - self.HEIGHT + 1
        if hasattr(self, "avatar"):
            self.avatar.x = max(self.left, min(self.avatar.x, self.right))
            self.move(round(self.avatar.x), self.floor)

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray.setIcon(icon)
        self.tray.setToolTip("Avatar Living in Desktop — v0.2")
        menu = QMenu()
        menu.addAction("종료", QApplication.instance().quit)
        self.tray.setContextMenu(menu)
        self.tray.show()

    def _tick(self):
        now = time.monotonic()
        dt = now - self._last
        self._last = now
        self.avatar.update(dt, self.left, self.right)
        self.move(round(self.avatar.x), self.floor)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.avatar.direction < 0:
            painter.translate(self.width(), 0)
            painter.scale(-1, 1)

        walking = self.avatar.action == Action.WALK
        # Visual cue: walking feet alternate; idle feet stay still.
        phase = int(time.monotonic() * 6) % 2 if walking else 0
        painter.setPen(QPen(QColor("#253047"), 2))
        painter.setBrush(QColor("#638DC8"))
        painter.drawRoundedRect(25, 58, 40, 44, 12, 12)
        painter.setBrush(QColor("#253047"))
        painter.drawRoundedRect(29, 96 + (3 if phase else 0), 12, 16, 4, 4)
        painter.drawRoundedRect(49, 96 + (0 if phase else 3) if walking else 96, 12, 16, 4, 4)

        painter.setBrush(QColor("#F4C59A"))
        painter.drawEllipse(18, 8, 54, 60)
        painter.setBrush(QColor("#463327"))
        painter.drawPie(17, 3, 56, 48, 0, 180 * 16)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#202020"))
        painter.drawEllipse(39, 39, 5, 6)
        painter.drawEllipse(57, 39, 5, 6)
        painter.end()
