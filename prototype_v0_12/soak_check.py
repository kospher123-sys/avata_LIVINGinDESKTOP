"""Bounded real-time Qt/resource sampling without changing user preferences."""
import argparse
import json
import os
from pathlib import Path
import statistics
import sys
import tempfile
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=600)
    parser.add_argument("--output", type=Path, default=Path("reports/soak-v0.9.json"))
    args = parser.parse_args()
    if args.seconds < 5:
        parser.error("--seconds must be at least 5")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    import psutil
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication
    from overlay import AvatarOverlay
    from settings import SettingsStore
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    process = psutil.Process()
    samples = []
    checks = []
    errors = []
    def failure(kind, value, traceback):
        errors.append(f"{kind.__name__}: {value}")
        app.quit()
    sys.excepthook = failure
    started = time.monotonic()
    with tempfile.TemporaryDirectory() as directory:
        window = AvatarOverlay(SettingsStore(Path(directory) / "settings.ini"))
        window.sync_runtime()
        process.cpu_percent()
        previous_stage = None

        def sample():
            nonlocal previous_stage
            elapsed = time.monotonic() - started
            stage = int(elapsed // 10) % 4
            if stage != previous_stage:
                window.set_hidden(stage == 2)
                window.set_paused(stage == 1)
                if stage == 3:
                    window.recover_runtime()
                    window.open_settings()
                    window.settings_dialog.reject()
                previous_stage = stage
            checks.append(window.left <= window.avatar.x <= window.right)
            checks.append(window.isVisible() == (not window.user_hidden))
            checks.append(window.timer.isActive() == (not window.paused and not window.user_hidden))
            samples.append({"seconds": round(elapsed, 2), "rss_mb": round(process.memory_info().rss / 1024**2, 2),
                            "cpu_percent": process.cpu_percent(),
                            "handles": process.num_handles() if hasattr(process, "num_handles") else None,
                            "stage": stage})
            if elapsed >= args.seconds:
                app.quit()

        timer = QTimer()
        timer.timeout.connect(sample)
        timer.start(1000)
        QTimer.singleShot((args.seconds + 3) * 1000, app.quit)
        app.exec()
        timer.stop()
        window.shutdown()
        window.close()
    warm = samples[min(10, len(samples) // 2):]
    report = {"duration_seconds": round(time.monotonic() - started, 2), "platform": "Qt offscreen",
              "checks_passed": all(checks) and bool(samples) and not errors,
              "errors": errors,
              "cpu_mean_percent": round(statistics.mean(item["cpu_percent"] for item in warm), 2) if warm else None,
              "rss_min_mb": min((item["rss_mb"] for item in warm), default=None),
              "rss_max_mb": max((item["rss_mb"] for item in warm), default=None),
              "rss_change_mb": round(warm[-1]["rss_mb"] - warm[0]["rss_mb"], 2) if warm else None, "samples": samples,
              "limits": "Short offscreen sample; not a full-day desktop, sleep/resume or leak certification."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "samples"}))
    return 0 if report["checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
