"""Live preview with explicit save and rollback on cancel or window close."""
from dataclasses import replace
from PySide6.QtCore import Qt, QTime, QTimer
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
                               QHBoxLayout, QLabel, QPushButton, QSlider, QSpinBox,
                               QTabWidget, QTimeEdit, QVBoxLayout, QWidget)

from settings import Preferences, automatic_height
from screens import screen_key, screen_label
from routine import routine_state
from avatar import Action


class SettingsDialog(QDialog):
    def __init__(self, overlay):
        super().__init__(overlay)
        self.overlay = overlay
        self._loading = False
        self.setWindowTitle("아앙 설정")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setMinimumWidth(430)
        layout = QVBoxLayout(self)
        title = QLabel("아앙과 편하게 지내기")
        title.setStyleSheet("font-size: 18px; font-weight: 600; margin-bottom: 10px")
        layout.addWidget(title)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        forms = []
        for name in ("화면·크기", "움직임", "생활 시간표", "동작 확인"):
            page = QWidget()
            page_layout = QVBoxLayout(page)
            form = QFormLayout()
            page_layout.addLayout(form)
            page_layout.addStretch()
            self.tabs.addTab(page, name)
            forms.append(form)
        display_form, movement_form, routine_form, preview_form = forms
        preview_hint = QLabel("앉기 → 앉아서 쉬기 → 일어서기를 한 번 보여줍니다.\n크기와 시간표 설정은 바뀌지 않습니다.")
        preview_hint.setWordWrap(True)
        preview_form.addRow(preview_hint)
        self.play_preview = QPushButton("전체 동작 한 번 보기")
        self.stop_preview = QPushButton("확인 종료")
        for button in (self.play_preview, self.stop_preview):
            button.setAutoDefault(False)
        self.play_preview.clicked.connect(self.overlay.start_motion_preview)
        self.stop_preview.clicked.connect(self.overlay.stop_motion_preview)
        preview_form.addRow(self.play_preview)
        preview_form.addRow(self.stop_preview)
        self.look_preview = QPushButton("둘러보기 한 번 보기")
        self.look_preview.setAutoDefault(False)
        self.look_preview.clicked.connect(self.overlay.preview_look)
        preview_form.addRow(self.look_preview)
        self.air_preview = QPushButton("공기 벤딩 한 번 보기")
        self.air_preview.setAutoDefault(False)
        self.air_preview.clicked.connect(self.overlay.preview_air_trick)
        preview_form.addRow(self.air_preview)
        self.preview_hint = QLabel()
        self.preview_hint.setWordWrap(True)
        preview_form.addRow(self.preview_hint)
        self.monitor = QComboBox()
        self.monitor.setMinimumContentsLength(28)
        display_form.addRow("머물 화면", self.monitor)
        self.auto_size = QCheckBox("화면 크기와 배율에 맞추기")
        display_form.addRow("크기 조절", self.auto_size)
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
        display_form.addRow("수동 높이", row)
        self.size_hint = QLabel()
        self.size_hint.setWordWrap(True)
        display_form.addRow(self.size_hint)
        self.speed = QSpinBox()
        self.speed.setRange(10, 150)
        self.speed.setSuffix(" px/초")
        movement_form.addRow("이동 속도", self.speed)
        self.auto_move = QCheckBox("스스로 걷고 쉬기")
        movement_form.addRow("자동 이동", self.auto_move)
        movement_hint = QLabel("자동 이동을 끄면 대기합니다.\n휴식 시간에는 생활 시간표에 따라 대기합니다.")
        movement_hint.setWordWrap(True)
        movement_form.addRow(movement_hint)
        self.routine_enabled = QCheckBox("생활 시간표 사용")
        routine_form.addRow("생활 패턴", self.routine_enabled)
        self.rest_start = QTimeEdit()
        self.rest_end = QTimeEdit()
        for editor in (self.rest_start, self.rest_end):
            editor.setDisplayFormat("HH:mm")
        self.rest_start_now = QPushButton("현재시간")
        self.rest_end_now = QPushButton("현재시간")
        for label, editor, button in (("휴식 시작", self.rest_start, self.rest_start_now),
                                      ("활동 재개", self.rest_end, self.rest_end_now)):
            time_row = QHBoxLayout()
            time_row.addWidget(editor, 1)
            time_row.addWidget(button)
            button.setAutoDefault(False)
            button.setToolTip("컴퓨터의 현재 시각으로 설정")
            button.clicked.connect(lambda checked=False, target=editor: target.setTime(QTime.currentTime()))
            routine_form.addRow(label, time_row)
        self.routine_hint = QLabel("휴식 중에는 대기합니다. 같은 시간으로 맞추면 항상 활동합니다.")
        self.routine_hint.setWordWrap(True)
        routine_form.addRow(self.routine_hint)
        self.reset_routine_button = QPushButton("시간표 초기화")
        self.reset_routine_button.setAutoDefault(False)
        self.reset_routine_button.setToolTip("시간표 꺼짐 · 휴식 22:00~07:00으로 복원")
        self.reset_routine_button.clicked.connect(self.reset_routine)
        routine_form.addRow(self.reset_routine_button)
        self.asset_status = QLabel()
        self.asset_status.setWordWrap(True)
        routine_form.addRow("휴식 모션", self.asset_status)
        reload_button = QPushButton("이미지 다시 불러오기")
        reload_button.setAutoDefault(False)
        reload_button.clicked.connect(self.overlay.reload_assets)
        routine_form.addRow(reload_button)
        self.status = QLabel()
        status_form = QFormLayout()
        status_form.addRow("지금 아앙은", self.status)
        layout.addLayout(status_form)
        hint = QLabel("변경하면 바로 미리보기에 반영됩니다.\n저장하면 다음 실행에도 유지되고, 취소하면 이전 설정으로 돌아갑니다.")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        buttons = QDialogButtonBox()
        self.reset_all_button = buttons.addButton("전체 설정 초기화", QDialogButtonBox.ButtonRole.ResetRole)
        self.reset_all_button.setAutoDefault(False)
        self.reset_all_button.setToolTip("모든 탭을 기본값으로 복원 · 저장 전 취소 가능")
        self.reset_all_button.clicked.connect(self.reset_all)
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
        self._original_mode = self.overlay.mode
        self.set_values(self.overlay.preferences)

    def set_values(self, prefs):
        self._loading = True
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

    def reset_routine(self):
        defaults = Preferences()
        self.set_values(replace(self.values(), routine_enabled=defaults.routine_enabled,
                               rest_start=defaults.rest_start, rest_end=defaults.rest_end))
        self.preview()

    def reset_all(self):
        self.set_values(Preferences())
        self.preview()

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
        animation = self.overlay.animation
        previewing = self.overlay.motion_preview.active
        can_play = (animation.has_clip(Action.REST) and not self.overlay.paused
                    and not self.overlay.user_hidden and self.overlay.display_screen is not None)
        self.play_preview.setEnabled(can_play and not previewing)
        self.stop_preview.setEnabled(previewing or self.overlay.air_trick.playing)
        self.air_preview.setEnabled(self.overlay.can_preview_air_trick())
        self.look_preview.setEnabled(animation.has_clip(Action.LOOK_AROUND) and not previewing
                                     and not self.overlay.idle_look.playing and not self.overlay.air_trick.playing
                                     and not self.overlay.paused
                                     and not self.overlay.user_hidden and self.overlay.display_screen is not None
                                     and self.overlay.rest_controller.phase is None)
        self.preview_hint.setText("완료하면 이전 동작 모드로 돌아갑니다. 휴식 시간이면 다시 앉아서 쉽니다."
                                  if can_play else "휴식 이미지를 준비하고, 캐릭터를 표시·재개한 뒤 사용할 수 있습니다.")
        if animation.has_clip(Action.REST):
            self.asset_status.setText(f"휴식 {len(animation.frames[Action.REST])}프레임 준비됨")
        else:
            self.asset_status.setText("휴식 이미지 준비 중 · 대기 동작 사용")
        if animation.warnings:
            self.asset_status.setText(self.asset_status.text() + " · 일부 이미지 확인 필요")
        self.asset_status.setToolTip("\n".join(animation.warnings))
        preferences = self.overlay.preview or self.overlay.preferences
        enabled = self.routine_enabled.isChecked() and self.auto_move.isChecked()
        self.rest_start.setEnabled(enabled)
        self.rest_end.setEnabled(enabled)
        self.rest_start_now.setEnabled(enabled)
        self.rest_end_now.setEnabled(enabled)
        labels = {"stopped": "자동 이동 꺼짐 · 대기", "free": "자유롭게 걷고 쉬는 중",
                  "rest": "휴식 시간 · 앉아서 쉬는 중" if animation.has_clip(Action.REST) else "휴식 시간 · 대기",
                  "active": "활동 시간 · 걷기와 대기"}
        if self.overlay.user_hidden:
            self.status.setText("숨김 · 트레이에서 다시 표시할 수 있어요")
        elif self.overlay.paused:
            self.status.setText("일시정지 · 트레이에서 재개할 수 있어요")
        elif previewing:
            self.status.setText("동작 확인 · " + {"sitting": "앉는 중", "resting": "앉아서 쉬는 중", "standing": "일어서는 중"}[self.overlay.motion_preview.stage])
        elif self.overlay.idle_look.playing:
            self.status.setText("둘러보는 중")
        elif self.overlay.mode != "auto":
            self.status.setText("임시 동작 · " + {"walk": "걷기", "idle": "대기", "rest": "휴식 모션 확인"}[self.overlay.mode])
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
