"""Validated, cached sprite frames and elapsed-time animation playback."""
from pathlib import Path

from PySide6.QtGui import QImage, QPixmap

from avatar import Action


ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets/characters/aang"
CANVAS = (296, 444)
ANCHOR = (148, 419)
# Union of the supplied frames' visible bounds: y=24 through y=419.
VISIBLE_HEIGHT = 396
DURATIONS = {Action.IDLE: 0.320, Action.WALK: 0.120}


class SpriteAnimation:
    def __init__(self, root=ASSET_ROOT):
        self.frames = {}
        for action, count in ((Action.IDLE, 4), (Action.WALK, 6)):
            frames = []
            for index in range(1, count + 1):
                path = Path(root) / action.value / f"{action.value}_{index:02}.png"
                image = QImage(str(path))
                if image.isNull() or (image.width(), image.height()) != CANVAS or not image.hasAlphaChannel():
                    raise ValueError(f"Invalid RGBA sprite (expected 296x444): {path}")
                frames.append(QPixmap.fromImage(image))
            self.frames[action] = frames
        self.action = Action.IDLE
        self.elapsed = 0.0

    def advance(self, action, dt):
        if action != self.action:
            self.action = action
            self.elapsed = 0.0
        else:
            self.elapsed = (self.elapsed + max(0.0, dt)) % (DURATIONS[action] * len(self.frames[action]))

    @property
    def index(self):
        return int(self.elapsed / DURATIONS[self.action]) % len(self.frames[self.action])

    @property
    def pixmap(self):
        return self.frames[self.action][self.index]
