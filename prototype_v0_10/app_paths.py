"""Keep editable runtime artwork beside the packaged executable."""
from pathlib import Path
import sys


def asset_root():
    base = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]
    return base / "assets/characters/aang"
