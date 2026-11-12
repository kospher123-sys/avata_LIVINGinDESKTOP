"""Avatar runtime with one active AIR_BLAST V3 implementation."""
import argparse
import logging
from pathlib import Path
import sys
import tempfile

from PySide6.QtCore import QTimer, qInstallMessageHandler
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox
from animation import SpriteAnimation
from avatar import Action
from overlay import AvatarOverlay
from single_instance import SingleInstance
from diagnostics import configure_logging, install_error_handlers
from settings import SettingsStore
from air_blast_v3 import AirBlastV3Effects


def check_package(app, native_preview=False, review_v3=False):
    animation = SpriteAnimation(review_v3=review_v3)
    has_air_clips = all(animation.has_clip(action) for action in (Action.AIR_TRICK, Action.AIR_BLAST))
    if not has_air_clips or animation.blast_effects is None or animation.warnings:
        return 1
    if not isinstance(animation.blast_effects, AirBlastV3Effects):
        return 1
    if not native_preview:
        return 0
    # A private test session can replay the built package alongside the user's app.
    with tempfile.TemporaryDirectory() as directory:
        window = AvatarOverlay(SettingsStore(Path(directory) / "settings.ini"), review_v3=review_v3)
        window.set_mode("idle")
        seen = set()
        firing_frame = []
        original_paint = window.animation.blast_effects.paint

        def observe_paint(painter, scene):
            original_paint(painter, scene)
            if not scene.front.isEmpty() and not firing_frame:
                firing_frame.append(window.animation.index)

        def observe_frame():
            if window.animation.action == Action.AIR_BLAST:
                seen.add(window.animation.index)
            elif seen == set(range(12)):
                app.quit()

        window.animation.blast_effects.paint = observe_paint
        window.timer.timeout.connect(observe_frame)
        try:
            if not window.preview_air_blast():
                return 1
            QTimer.singleShot(3000, app.quit)
            app.exec()
            passed = (seen == set(range(12)) and firing_frame == [6]
                      and window.animation.action == Action.IDLE and window.blast_window.scene is None)
            return 0 if passed else 1
        finally:
            window.shutdown()
            window.close()


def main():
    parser = argparse.ArgumentParser(description="아앙 데스크톱 아바타")
    parser.add_argument("--settings", action="store_true", help="설정 창 열기")
    parser.add_argument("--preview-rest", action="store_true", help="저장된 시간표를 바꾸지 않고 휴식 모션 확인")
    parser.add_argument("--preview-once", action="store_true", help="휴식 동작 한 번 재생")
    parser.add_argument("--preview-air-blast", action="store_true", help="AIR_BLAST 동작 한 번 재생")
    parser.add_argument("--air-blast-v3-review", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--quit-after", type=float, default=0, help="실행 검사: 지정 초 뒤 종료")
    parser.add_argument("--check-package", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    offscreen_check = args.check_package and not args.preview_air_blast
    app = QApplication([sys.argv[0], "-platform", "offscreen"] if offscreen_check else sys.argv)
    app.setQuitOnLastWindowClosed(False)
    if args.check_package:
        return check_package(app, args.preview_air_blast, args.air_blast_v3_review)
    app.setFont(QFont("Malgun Gothic", 10))
    app.setOrganizationName("AvatarLivingInDesktop")
    app.setApplicationName("AangOverlay")
    instance = None
    try:
        instance = SingleInstance()
        if not instance.acquire():
            return 0
        logger = configure_logging()
        install_error_handlers()
        logger.info("Starting AIR_BLAST V3; packaged=%s", getattr(sys, "frozen", False))
        window = AvatarOverlay()
        logger.info("AIR_BLAST active=%s resources=%s",
                    window.animation.active_versions.get(Action.AIR_BLAST),
                    getattr(window.animation.blast_effects, "path", None))
        for warning in window.animation.warnings:
            logger.warning("Optional image: %s", warning)
    except (ValueError, OSError) as error:
        logging.getLogger("aang").exception("Startup failed")
        QMessageBox.critical(None, "아앙 실행 실패", str(error))
        if instance is not None:
            instance.close()
        return 1
    instance.activated.connect(window.open_settings)
    app.aboutToQuit.connect(instance.close)
    app.aboutToQuit.connect(window.shutdown)
    window.sync_runtime()
    if args.preview_rest:
        window.set_mode("rest")
    if args.preview_once:
        window.start_motion_preview()
    if args.preview_air_blast:
        window.set_mode("idle")
        window.preview_air_blast()
    if args.settings:
        window.open_settings()
    if args.quit_after > 0:
        QTimer.singleShot(max(1, round(args.quit_after * 1000)), app.quit)
    try:
        return app.exec()
    finally:
        logger.info("Shutdown complete")
        qInstallMessageHandler(None)
        instance.close()


if __name__ == "__main__":
    sys.exit(main())
