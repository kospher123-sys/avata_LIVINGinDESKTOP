"""Validated preferences stored outside the repository."""
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QSettings, QStandardPaths


@dataclass
class Preferences:
    height: int = 120
    auto_size: bool = False
    speed: int = 75
    auto_move: bool = True
    monitor: str = ""


def automatic_height(logical_screen_height):
    # Qt screen geometry already accounts for Windows display scaling.
    return max(80, min(240, round(logical_screen_height * 120 / 900)))


class SettingsStore:
    def __init__(self, path=None):
        if path is None:
            directory = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation))
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / "settings.ini"
        self.path = Path(path)
        self.settings = QSettings(str(self.path), QSettings.Format.IniFormat)

    def load(self):
        def number(key, default, low, high):
            try:
                return max(low, min(high, int(self.settings.value(key, default))))
            except (TypeError, ValueError, OverflowError):
                return default

        def boolean(key, default):
            value = str(self.settings.value(key, default)).lower()
            return {"true": True, "false": False, "1": True, "0": False}.get(value, default)

        return Preferences(number("height", 120, 80, 240), boolean("auto_size", False),
                           number("speed", 75, 10, 150), boolean("auto_move", True),
                           str(self.settings.value("monitor", "")))

    def save(self, preferences):
        for key, value in vars(preferences).items():
            self.settings.setValue(key, value)
        self.settings.sync()
        if self.settings.status() != QSettings.Status.NoError:
            raise OSError(f"설정을 저장할 수 없습니다: {self.path}")
