"""Validated, cached sprite frames and elapsed-time animation playback."""
from pathlib import Path
import bisect
import json
import math

from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage, QPainter, QPixmap

from avatar import Action
from app_paths import asset_root


ASSET_ROOT = asset_root()
CANVAS = (296, 444)
ANCHOR = (148, 419)
# Union of the supplied frames' visible bounds: y=24 through y=419.
VISIBLE_HEIGHT = 396
DURATIONS = {Action.IDLE: 0.320, Action.WALK: 0.120, Action.REST: 0.500,
             Action.SIT_DOWN: 0.150, Action.STAND_UP: 0.150}
DURATIONS[Action.LOOK_AROUND] = 0.400
TRANSITIONS = (Action.SIT_DOWN, Action.STAND_UP, Action.LOOK_AROUND, Action.AIR_IDLE_TRICK)


class SpriteAnimation:
    def __init__(self, root=ASSET_ROOT):
        self.root = Path(root)
        self.warnings = []
        self.frames = {}
        self.frame_times = {}
        self.render_rects = {}
        for action, count in ((Action.IDLE, 4), (Action.WALK, 6)):
            frames = []
            for index in range(1, count + 1):
                path = Path(root) / action.value / f"{action.value}_{index:02}.png"
                frames.append(self._load_frame(path))
            self.frames[action] = frames
        for action in (Action.REST, Action.SIT_DOWN, Action.STAND_UP, Action.LOOK_AROUND):
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
        self._load_manifest()
        self._load_manifest("extra_clips.json")

    def _load_manifest(self, filename="clips.json"):
        path = self.root / filename
        if not path.exists():
            return
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(manifest, dict) or manifest.get("version") != 1 or not isinstance(manifest.get("clips"), dict):
                raise ValueError("clips.json version/clips 규격을 확인하세요.")
        except (OSError, ValueError, TypeError) as error:
            self.warnings.append(str(error))
            return
        for name, spec in manifest["clips"].items():
            try:
                action = Action(name)
                directory = (self.root / spec["directory"]).resolve()
                if not directory.is_relative_to(self.root.resolve()):
                    raise ValueError("이미지 폴더는 캐릭터 폴더 내부여야 합니다.")
                prefix = spec["prefix"]
                if not isinstance(prefix, str) or not prefix.replace('_', '').isalnum():
                    raise ValueError("잘못된 프레임 접두사")
                canvas = tuple(spec["canvas"])
                if len(canvas) != 2 or any(type(n) is not int or not 1 <= n <= 4096 for n in canvas):
                    raise ValueError("잘못된 캔버스 크기")
                anchor = tuple(spec["anchor"])
                if len(anchor) != 2 or any(type(n) not in (int, float) or not math.isfinite(n) or not 0 <= n < limit for n, limit in zip(anchor, canvas)):
                    raise ValueError("잘못된 기준점")
                height = spec["standing_height"]
                if type(height) not in (int, float) or not math.isfinite(height) or not 1 <= height <= canvas[1]:
                    raise ValueError("잘못된 서기 기준 높이")
                paths = sorted(directory.glob("*.png"))
                expected = [f"{prefix}_{index:02}.png" for index in range(1, len(paths) + 1)]
                if not 1 <= len(paths) <= 32 or [p.name for p in paths] != expected:
                    raise ValueError("01부터 연속된 프레임이 필요합니다.")
                times = spec["durations_ms"]
                if not isinstance(times, list) or len(times) != len(paths) or any(type(n) not in (int, float) or not math.isfinite(n) or not 20 <= n <= 10000 for n in times):
                    raise ValueError("프레임 수와 재생 시간이 일치해야 합니다 (20~10000ms).")
                frames = [self._load_frame(p, canvas) for p in paths]
                if action == Action.AIR_IDLE_TRICK:
                    effects = (self.root / spec["effect_directory"]).resolve()
                    if not effects.is_relative_to(self.root.resolve()):
                        raise ValueError("효과 폴더는 캐릭터 폴더 내부여야 합니다.")
                    for path, sprite in zip(paths, frames):
                        effect = self._load_frame(effects / path.name, canvas, allow_empty=True)
                        with QPainter(sprite) as painter:
                            painter.drawPixmap(0, 0, effect)
                ratio = VISIBLE_HEIGHT / height
                anchors = spec.get("anchors", [anchor] * len(paths))
                if not isinstance(anchors, list) or len(anchors) != len(paths):
                    raise ValueError("프레임별 기준점 수를 확인하세요.")
                rects = []
                for point in anchors:
                    if not isinstance(point, (list, tuple)) or len(point) != 2 or any(type(n) not in (int, float) or not math.isfinite(n) or not 0 <= n < limit for n, limit in zip(point, canvas)):
                        raise ValueError("잘못된 프레임별 기준점")
                    rects.append(QRectF(ANCHOR[0] - point[0] * ratio, ANCHOR[1] - point[1] * ratio,
                                        canvas[0] * ratio, canvas[1] * ratio))
                self.frames[action] = frames
                self.frame_times[action] = [n / 1000 for n in times]
                self.render_rects[action] = rects
            except (OSError, ValueError, TypeError, KeyError) as error:
                self.warnings.append(f"{name}: {error}")

    @staticmethod
    def _load_frame(path, canvas=CANVAS, allow_empty=False):
        image = QImage(str(path))
        if image.isNull() or (image.width(), image.height()) != tuple(canvas) or not image.hasAlphaChannel():
            raise ValueError(f"투명 PNG {canvas[0]}×{canvas[1]} 규격을 확인하세요: {path}")
        # An alpha channel alone also exists in fully opaque or fully empty files.
        alpha = image.convertToFormat(QImage.Format.Format_RGBA8888)
        values = bytes(alpha.constBits())[3::4]
        if min(values) == 255 or (not allow_empty and max(values) == 0):
            raise ValueError(f"캐릭터와 투명 배경이 모두 필요합니다: {path}")
        return QPixmap.fromImage(image)

    def has_clip(self, action):
        return action in self.frames

    def clip_duration(self, action):
        if action in self.frame_times:
            return sum(self.frame_times[action])
        return len(self.frames.get(action, [])) * DURATIONS.get(action, 0.0)

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
        if self.action in self.frame_times:
            total = 0.0
            boundaries = []
            for duration in self.frame_times[self.action]:
                total += duration
                boundaries.append(total)
            index = bisect.bisect_right(boundaries, self.elapsed + 1e-9)
        else:
            index = int(self.elapsed / DURATIONS[self.action])
        return min(index, count - 1) if self.action in TRANSITIONS else index % count

    @property
    def pixmap(self):
        return self.frames[self.action][self.index]

    @property
    def render_rect(self):
        rects = self.render_rects.get(self.action)
        return rects[self.index] if rects else QRectF(0, 0, *CANVAS)
