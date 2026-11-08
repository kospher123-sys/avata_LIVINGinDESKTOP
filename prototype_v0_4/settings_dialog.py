"""Live preview with explicit save and rollback on cancel or window close."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QFormLayout,
                               QHBoxLayout, QLabel, QSlider, QSpinBox, QVBoxLayout)

from settings import Preferences, automatic_height


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
        self.reload()

    def reload(self):
        self._loading = True
        self._original_mode = self.overlay.mode
        prefs = self.overlay.preferences
        self.height.setValue(prefs.height)
        self.speed.setValue(prefs.speed)
        self.auto_move.setChecked(prefs.auto_move)
        self.auto_size.setChecked(prefs.auto_size)
        self.update_hint()
        self._loading = False

    def values(self):
        return Preferences(self.height.value(), self.auto_size.isChecked(),
                           self.speed.value(), self.auto_move.isChecked())

    def preview(self, *args):
        if not self._loading:
            self.overlay.preview_preferences(self.values())

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
        size = automatic_height(self.overlay.display_screen.geometry().height())
        self.size_hint.setText(f"현재 화면의 자동 높이: {size}px · 수동 기본값: 120px")

    def save(self):
        if self.overlay.save_preferences(self.values()):
            self.accept()
