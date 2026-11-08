"""Build a folder release, with editable sprites outside the executable."""
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    if sys.platform != "win32":
        raise SystemExit("Windows에서 실행해 주세요.")
    source = Path(__file__).resolve().parent
    root = source.parent
    output = root / "dist" / "AangOverlay-v0.9"
    work = root / "build" / "v0.9"
    work.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
                    "--onedir", "--windowed", "--name", output.name,
                    "--distpath", str(output.parent), "--workpath", str(work / "cache"),
                    "--specpath", str(work), str(source / "main.py")], check=True, cwd=source)
    # Copy only runtime frames, not reference artwork, audits or user settings.
    assets = root / "assets/characters/aang"
    for action in ("idle", "walk", "rest", "sit_down", "stand_up"):
        folder = assets / action
        if folder.exists():
            target = output / "assets/characters/aang" / action
            target.mkdir(parents=True, exist_ok=True)
            for frame in folder.glob("*.png"):
                shutil.copy2(frame, target / frame.name)
    shutil.copy2(source / "README.md", output / "README.md")
    shutil.copy2(root / "docs/REST_ASSET_IMPORT.md", output / "REST_ASSET_IMPORT.md")
    print(output / f"{output.name}.exe")


if __name__ == "__main__":
    main()
