"""Live preview with explicit save and rollback on cancel or window close."""
from PySide6.QtCore import Qt, QTime, QTimer
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
                               QHBoxLayout, QLabel, QSlider, QSpinBox, QTimeEdit, QVBoxLayout)

from settings import Preferences, automatic_height
from screens import screen_key, screen_label
from routine import routine_state


class SettingsDialog(QDialog):
    def __init__(self, overlay):
        super().__init__(overlay)
        self.overlay = overlay
        self._loading = False
        self.setWindowTitle("아앙 설정")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setMinimumWidth(380)
        layout = QVBoxLayout(self)
        title = QLabel("아앙과 편하게 지내기")
        title.setStyleSheet("font-size: 18px; font-weight: 600; margin-bottom: 10px")
        layout.addWidget(title)
        form = QFormLayout()
        self.monitor = QComboBox()
        self.monitor.setMinimumContentsLength(28)
        form.addRow("머물 화면", self.monitor)
        self.auto_size = QCheckBox("화면 크기와 배율에 맞추기")
        form.addRow("크기 조절", self.auto_size)
        row = QHBoxLayout()
        self.height_slider = QSlider(Qt.Orientation.Horizontal)
        self.height_slider.setRange(80, 240)
        self.height = QSpinBox()
        self.height.setRange(80, 240)
        self.height.setSuffix(" px")
        self.height_slider.valueChanged.connect(self.height.setValue)
        self.height.valueChanged.connect(self.height_slider.setValue)
        row.addWidget(self.height_slider)
        row.addWidget(self.height)
        form.addRow("수동 높이", row)
        self.size_hint = QLabel()
        self.size_hint.setWordWrap(True)
        form.addRow(self.size_hint)
        self.speed = QSpinBox()
        self.speed.setRange(10, 150)
        self.speed.setSuffix(" px/초")
        form.addRow("이동 속도", self.speed)
        self.auto_move = QCheckBox("스스로 걷고 쉬기")
        form.addRow("자동 이동", self.auto_move)
        self.routine_enabled = QCheckBox("생활 시간표 사용")
        form.addRow("생활 패턴", self.routine_enabled)
        self.rest_start = QTimeEdit()
        self.rest_end = QTimeEdit()
        for editor in (self.rest_start, self.rest_end):
            editor.setDisplayFormat("HH:mm")
        form.addRow("휴식 시작", self.rest_start)
        form.addRow("활동 재개", self.rest_end)
        self.routine_hint = QLabel("휴식 중에는 대기합니다. 같은 시간으로 맞추면 항상 활동합니다.")
        self.routine_hint.setWordWrap(True)
        form.addRow(self.routine_hint)
        self.status = QLabel()
        form.addRow("지금 아앙은", self.status)
        layout.addLayout(form)
        hint = QLabel("변경하면 바로 미리보기에 반영됩니다.\n저장하면 다음 실행에도 유지되고, 취소하면 이전 설정으로 돌아갑니다.")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        buttons = QDialogButtonBox()
        buttons.addButton("저장", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton("취소", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.auto_size.toggled.connect(self.update_hint)
        self.height.valueChanged.connect(self.preview)
        self.speed.valueChanged.connect(self.preview)
        self.auto_size.toggled.connect(self.preview)
        self.auto_move.toggled.connect(self.preview)
        self.monitor.currentIndexChanged.connect(self.preview)
        self.routine_enabled.toggled.connect(self.preview)
        self.rest_start.timeChanged.connect(self.preview)
        self.rest_end.timeChanged.connect(self.preview)
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)
        self.reload()

    def reload(self):
        self._loading = True
        self._original_mode = self.overlay.mode
        prefs = self.overlay.preferences
        self.refresh_screens(preferred=prefs.monitor)
        self.height.setValue(prefs.height)
        self.speed.setValue(prefs.speed)
        self.auto_move.setChecked(prefs.auto_move)
        self.auto_size.setChecked(prefs.auto_size)
        self.routine_enabled.setChecked(prefs.routine_enabled)
        self.rest_start.setTime(QTime(prefs.rest_start // 60, prefs.rest_start % 60))
        self.rest_end.setTime(QTime(prefs.rest_end // 60, prefs.rest_end % 60))
        self.update_hint()
        self._loading = False
        self.update_status()

    def values(self):
        return Preferences(self.height.value(), self.auto_size.isChecked(),
                           self.speed.value(), self.auto_move.isChecked(), self.monitor.currentData() or "",
                           self.routine_enabled.isChecked(),
                           self.rest_start.time().hour() * 60 + self.rest_start.time().minute(),
                           self.rest_end.time().hour() * 60 + self.rest_end.time().minute())

    def refresh_screens(self, preferred=None, excluded=None):
        loading = self._loading
        self._loading = True
        key = self.monitor.currentData() if preferred is None else preferred
        self.monitor.clear()
        self.monitor.addItem("기본 화면 따라가기", "")
        for screen in QApplication.screens():
            if screen is not excluded:
                self.monitor.addItem(screen_label(screen, screen is QApplication.primaryScreen()), screen_key(screen))
        index = self.monitor.findData(key or "")
        if index < 0:
            self.monitor.addItem("저장된 화면 (연결 안 됨 · 기본 화면 사용)", key)
            index = self.monitor.count() - 1
        self.monitor.setCurrentIndex(index)
        self._loading = loading

    def preview(self, *args):
        if not self._loading:
            self.overlay.preview_preferences(self.values())
            self.update_hint()
            self.update_status()

    def update_status(self):
        preferences = self.overlay.preview or self.overlay.preferences
        enabled = self.routine_enabled.isChecked() and self.auto_move.isChecked()
        self.rest_start.setEnabled(enabled)
        self.rest_end.setEnabled(enabled)
        labels = {"stopped": "자동 이동 꺼짐 · 대기", "free": "자유롭게 걷고 쉬는 중",
                  "rest": "휴식 시간 · 대기", "active": "활동 시간 · 걷기와 대기"}
        if self.overlay.mode != "auto":
            self.status.setText("임시 동작 · " + ("걷기" if self.overlay.mode == "walk" else "대기"))
        else:
            self.status.setText(labels[routine_state(preferences)])

    def reject(self):
        self.overlay.cancel_preview()
        self.overlay.set_mode(self._original_mode)
        for action in self.overlay.mode_group.actions():
            action.setChecked(action.data() == self._original_mode)
        super().reject()

    def update_hint(self):
        automatic = self.auto_size.isChecked()
        self.height.setEnabled(not automatic)
        self.height_slider.setEnabled(not automatic)
        screen = self.overlay.display_screen
        if screen is None:
            self.size_hint.setText("연결된 화면을 기다리고 있습니다.")
        else:
            size = automatic_height(screen.geometry().height())
            self.size_hint.setText(f"현재 화면의 자동 높이: {size}px · 수동 기본값: 120px")

    def save(self):
        if self.overlay.save_preferences(self.values()):
            self.accept()
