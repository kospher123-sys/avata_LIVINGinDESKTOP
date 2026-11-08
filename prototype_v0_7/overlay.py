"""Transparent desktop sprite overlay; click-through by default."""
import math
import time

from PySide6.QtCore import QPoint, QRectF, Qt, QTimer
from PySide6.QtGui import QActionGroup, QPainter
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QStyle, QSystemTrayIcon, QWidget

from animation import ANCHOR, CANVAS, VISIBLE_HEIGHT, SpriteAnimation
from avatar import Action, Avatar
from settings import SettingsStore, automatic_height
from settings_dialog import SettingsDialog
from screens import select_screen
from routine import routine_state
from rest_controller import RestController


class AvatarOverlay(QWidget):
    def __init__(self, store=None):
        super().__init__()
        self.store = store if store is not None else SettingsStore()
        self.preferences = self.store.load()
        self.preview = None
        self.settings_dialog = None
        self.animation = SpriteAnimation()
        self.rest_controller = self._make_rest_controller()
        self.avatar = Avatar()
        self.mode = "auto"
        self.drag_offset = None
        self.click_through = True
        self._routine_state = None
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint
                            | Qt.WindowType.WindowStaysOnTopHint
                            | Qt.WindowType.Tool
                            | Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.display_screen = None
        app = QApplication.instance()
        app.screenAdded.connect(self._screens_changed)
        app.screenRemoved.connect(self._screen_removed)
        app.primaryScreenChanged.connect(self._screens_changed)
        self.apply_preferences()
        self.avatar.x = float(self.left)
        self.move(self.left, self.floor)
        self._setup_tray()
        self._last = time.monotonic()
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

    def _make_rest_controller(self):
        if not self.animation.has_clip(Action.REST):
            return RestController()
        return RestController(self.animation.clip_duration(Action.SIT_DOWN),
                              self.animation.clip_duration(Action.STAND_UP))

    def reload_assets(self):
        try:
            replacement = SpriteAnimation(self.animation.root)
        except ValueError as error:
            QMessageBox.warning(self.settings_dialog, "이미지 불러오기 실패", str(error))
            return False
        self.animation = replacement
        self.rest_controller = self._make_rest_controller()
        self._routine_state = None
        if self.settings_dialog is not None:
            self.settings_dialog.update_status()
        message = ("일부 휴식 이미지의 규격을 확인해 주세요. 사용 가능한 동작으로 표시합니다."
                   if replacement.warnings else "이미지를 다시 불러왔습니다.")
        self.tray.showMessage("아앙", message)
        return True

    def _bind_screen(self, screen):
        if screen is self.display_screen:
            return False
        if self.display_screen is not None:
            for signal in ("availableGeometryChanged", "geometryChanged", "logicalDotsPerInchChanged"):
                try:
                    getattr(self.display_screen, signal).disconnect(self._screen_changed)
                except (RuntimeError, TypeError):
                    pass
        self.display_screen = screen
        if screen is not None:
            for signal in ("availableGeometryChanged", "geometryChanged", "logicalDotsPerInchChanged"):
                getattr(screen, signal).connect(self._screen_changed)
            self.setScreen(screen)
        return True

    def _screen_removed(self, screen):
        self._screens_changed(excluded=screen)

    def _screens_changed(self, *args, excluded=None):
        self.apply_preferences(excluded=excluded)
        if self.settings_dialog is not None:
            self.settings_dialog.refresh_screens(excluded=excluded)
            self.settings_dialog.update_hint()

    def _screen_changed(self, *args):
        self.apply_preferences()
        if self.display_screen is not None:
            self._refresh_bounds()
        if self.settings_dialog is not None:
            self.settings_dialog.update_hint()

    def apply_preferences(self, excluded=None):
        preferences = self.preview or self.preferences
        screens = [screen for screen in QApplication.screens() if screen is not excluded]
        target = select_screen(screens, preferences.monitor, QApplication.primaryScreen())
        changed_screen = self._bind_screen(target)
        if target is None:
            self.hide()
            return
        height = (automatic_height(self.display_screen.geometry().height())
                  if preferences.auto_size else preferences.height)
        self.avatar.speed = preferences.speed
        if getattr(self, "display_height", None) != height:
            self.set_display_height(height)
        elif changed_screen:
            self._refresh_bounds()
        if changed_screen and hasattr(self, "timer"):
            self.show()
        if not preferences.auto_move:
            self.avatar.action = Action.IDLE

    def preview_preferences(self, preferences):
        previous = self.preview or self.preferences
        self.preview = preferences
        if self.mode != "auto":
            self.set_mode("auto")
        if preferences.auto_move and not previous.auto_move:
            self.avatar.action = Action.WALK
            self.avatar.remaining = 4.0
        self.apply_preferences()

    def cancel_preview(self):
        previous = self.preview or self.preferences
        self.preview = None
        if self.preferences.auto_move and not previous.auto_move:
            self.avatar.action = Action.WALK
            self.avatar.remaining = 4.0
        self.apply_preferences()

    def save_preferences(self, preferences):
        try:
            self.store.save(preferences)
        except OSError as error:
            QMessageBox.warning(self.settings_dialog, "설정 저장 실패", str(error))
            return False
        self.preferences = preferences
        self.preview = None
        self.mode = "auto"
        for action in self.mode_group.actions():
            action.setChecked(action.data() == "auto")
        self.avatar.remaining = 4.0
        self.apply_preferences()
        return True

    def open_settings(self):
        if self.settings_dialog is None:
            self.settings_dialog = SettingsDialog(self)
        if not self.settings_dialog.isVisible():
            self.settings_dialog.reload()
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()

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
        self.menu.addAction("설정…", self.open_settings)
        self.menu.addAction("이미지 다시 불러오기", self.reload_assets)
        self.menu.addSeparator()
        self.input_action = self.menu.addAction("드래그 모드 (클릭 통과 해제)")
        self.input_action.setCheckable(True)
        self.input_action.toggled.connect(self._set_interactive)
        modes = self.menu.addMenu("동작")
        self.mode_group = QActionGroup(self)
        for label, mode in (("자동", "auto"), ("대기", "idle"), ("걷기", "walk"), ("휴식 모션 확인", "rest")):
            action = modes.addAction(label)
            action.setCheckable(True)
            action.setChecked(mode == "auto")
            action.setData(mode)
            self.mode_group.addAction(action)
            action.triggered.connect(lambda checked=False, value=mode: self.set_mode(value))
        self.menu.addAction("방향 전환", self._turn)
        self.menu.addSeparator()
        self.menu.addAction("종료", QApplication.instance().quit)
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        self.tray.setToolTip("Avatar Living in Desktop — v0.7 아앙")
        self.tray.setContextMenu(self.menu)
        self.tray.show()

    def _turn(self):
        self.avatar.direction *= -1
        self.update()

    def set_mode(self, mode):
        self.mode = mode
        if mode != "auto":
            self.avatar.action = Action.IDLE if mode == "rest" else Action(mode)
        self.avatar.remaining = 4.0

    def _set_interactive(self, enabled):
        self.drag_offset = None
        self.click_through = not enabled
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, not enabled)
        self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, not enabled)
        self.show()

    def _tick(self):
        if self.display_screen is None:
            self._last = time.monotonic()
            return
        now = time.monotonic()
        dt = max(0.0, min(now - self._last, 0.1))
        self._last = now
        motion = None
        if self.drag_offset is None:
            state = routine_state(self.preview or self.preferences)
            previous_motion = self.rest_controller.phase
            if self.mode in ("idle", "walk"):
                self.rest_controller.reset()
            else:
                motion = self.rest_controller.update(self.mode == "rest" or (self.mode == "auto" and state == "rest"), dt)
            if motion is not None or (self.mode == "auto" and state == "stopped"):
                self.avatar.action = Action.IDLE
                self.avatar.remaining = 1.0
            elif self.mode != "auto":
                self.avatar.action = Action(self.mode)
                self.avatar.remaining = 1.0
            elif previous_motion is not None or self._routine_state in ("rest", "stopped"):
                self.avatar.action = Action.WALK
                self.avatar.remaining = 4.0
            self._routine_state = state
            if motion is None:
                self.avatar.update(dt, self.left, self.right)
            self.move(round(self.avatar.x), self.y())
        else:
            self.rest_controller.reset()
        action = Action.IDLE if self.drag_offset is not None else (motion or self.avatar.action)
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
