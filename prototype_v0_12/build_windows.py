"""Build a folder release, with editable sprites outside the executable."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys


def main():
    if sys.platform != "win32":
        raise SystemExit("Windows에서 실행해 주세요.")
    source = Path(__file__).resolve().parent
    root = source.parent
    name = "AangOverlay-AIR_BLAST-V3"
    output = root / "dist" / name
    work = root / "build" / "air-blast-v3"
    work.mkdir(parents=True, exist_ok=True)
    # Keep unrelated programs on PATH out of PyInstaller's DLL discovery.
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join((str(Path(sys.executable).parent),
                                  str(Path(os.environ["SystemRoot"]) / "System32")))
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
                    "--onedir", "--windowed", "--name", output.name,
                    "--distpath", str(output.parent), "--workpath", str(work / "cache"),
                    "--specpath", str(work), str(source / "main.py")],
                   check=True, cwd=source, env=env)
    # Copy only runtime frames, not reference artwork, audits or user settings.
    assets = root / "assets/characters/aang"
    for action in ("idle", "walk", "rest", "sit_down", "stand_up"):
        folder = assets / action
        if folder.exists():
            target = output / "assets/characters/aang" / action
            target.mkdir(parents=True, exist_ok=True)
            for frame in folder.glob("*.png"):
                shutil.copy2(frame, target / frame.name)
    manifests = ("clips.json", "extra_clips.json")
    for manifest_name in manifests:
        manifest_path = assets / manifest_name
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for spec in manifest["clips"].values():
            for key in ("directory", "effect_directory"):
                if key not in spec:
                    continue
                folder = (assets / spec[key]).resolve()
                if not folder.is_relative_to(assets.resolve()):
                    raise ValueError("Unsafe asset directory")
                target = output / "assets/characters/aang" / folder.relative_to(assets.resolve())
                target.mkdir(parents=True, exist_ok=True)
                for frame in folder.glob("*.png"):
                    shutil.copy2(frame, target / frame.name)
            if "blast_effects" in spec:
                config = (assets / spec["blast_effects"]).resolve()
                if not config.is_relative_to(assets.resolve()) or not config.is_file():
                    raise ValueError("Unsafe or missing AIR_BLAST metadata")
                target = output / "assets/characters/aang" / config.parent.relative_to(assets.resolve())
                shutil.copytree(config.parent, target, dirs_exist_ok=True)
        shutil.copy2(manifest_path, output / "assets/characters/aang" / manifest_name)
    shutil.copy2(source / "README.md", output / "README.md")
    shutil.copy2(root / "docs/REST_ASSET_IMPORT.md", output / "REST_ASSET_IMPORT.md")
    executable = output / f"{output.name}.exe"
    check_args = [str(executable), "--check-package"]
    subprocess.run(check_args,
                   check=True, timeout=30, cwd=output)
    print(executable)


if __name__ == "__main__":
    main()
