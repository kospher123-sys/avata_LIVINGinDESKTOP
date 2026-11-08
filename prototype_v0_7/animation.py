"""Validated, cached sprite frames and elapsed-time animation playback."""
from pathlib import Path

from PySide6.QtGui import QImage, QPixmap

from avatar import Action


ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets/characters/aang"
CANVAS = (296, 444)
ANCHOR = (148, 419)
# Union of the supplied frames' visible bounds: y=24 through y=419.
VISIBLE_HEIGHT = 396
DURATIONS = {Action.IDLE: 0.320, Action.WALK: 0.120, Action.REST: 0.500,
             Action.SIT_DOWN: 0.150, Action.STAND_UP: 0.150}
TRANSITIONS = (Action.SIT_DOWN, Action.STAND_UP)


class SpriteAnimation:
    def __init__(self, root=ASSET_ROOT):
        self.root = Path(root)
        self.warnings = []
        self.frames = {}
        for action, count in ((Action.IDLE, 4), (Action.WALK, 6)):
            frames = []
            for index in range(1, count + 1):
                path = Path(root) / action.value / f"{action.value}_{index:02}.png"
                frames.append(self._load_frame(path))
            self.frames[action] = frames
        for action in (Action.REST, *TRANSITIONS):
            paths = sorted((self.root / action.value).glob("*.png"))
            if not paths:
                continue
            expected = [f"{action.value}_{index:02}.png" for index in range(1, len(paths) + 1)]
            try:
                if len(paths) > 32 or [path.name for path in paths] != expected:
                    raise ValueError(f"{action.value}: 01부터 연속된 PNG 이름이 필요합니다 (최대 32장).")
                self.frames[action] = [self._load_frame(path) for path in paths]
            except ValueError as error:
                self.warnings.append(str(error))
        self.action = Action.IDLE
        self.elapsed = 0.0

    @staticmethod
    def _load_frame(path):
        image = QImage(str(path))
        if image.isNull() or (image.width(), image.height()) != CANVAS or not image.hasAlphaChannel():
            raise ValueError(f"투명 PNG 296×444 규격을 확인하세요: {path}")
        # An alpha channel alone also exists in fully opaque or fully empty files.
        alpha = image.convertToFormat(QImage.Format.Format_RGBA8888)
        values = bytes(alpha.constBits())[3::4]
        if min(values) == 255 or max(values) == 0:
            raise ValueError(f"캐릭터와 투명 배경이 모두 필요합니다: {path}")
        return QPixmap.fromImage(image)

    def has_clip(self, action):
        return action in self.frames

    def clip_duration(self, action):
        return len(self.frames.get(action, [])) * DURATIONS[action]

    def advance(self, action, dt):
        if action not in self.frames:
            action = Action.IDLE
        if action != self.action:
            self.action = action
            self.elapsed = 0.0
        else:
            elapsed = self.elapsed + max(0.0, dt)
            duration = self.clip_duration(action)
            self.elapsed = min(elapsed, duration) if action in TRANSITIONS else elapsed % duration

    @property
    def index(self):
        count = len(self.frames[self.action])
        index = int(self.elapsed / DURATIONS[self.action])
        return min(index, count - 1) if self.action in TRANSITIONS else index % count

    @property
    def pixmap(self):
        return self.frames[self.action][self.index]
