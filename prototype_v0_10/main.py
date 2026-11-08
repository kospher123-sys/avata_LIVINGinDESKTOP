"""v0.10: user-supplied rest clips with native canvas and frame timing."""
import argparse
import logging
import sys

from PySide6.QtCore import QTimer, qInstallMessageHandler
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox
from overlay import AvatarOverlay
from single_instance import SingleInstance
from diagnostics import configure_logging, install_error_handlers


def main():
    parser = argparse.ArgumentParser(description="아앙 데스크톱 아바타")
    parser.add_argument("--settings", action="store_true", help="설정 창 열기")
    parser.add_argument("--preview-rest", action="store_true", help="저장된 시간표를 바꾸지 않고 휴식 모션 확인")
    parser.add_argument("--quit-after", type=float, default=0, help="실행 검사: 지정 초 뒤 종료")
    args = parser.parse_args()
    app = QApplication(sys.argv)
    app.setFont(QFont("Malgun Gothic", 10))
    app.setOrganizationName("AvatarLivingInDesktop")
    app.setApplicationName("AangOverlay")
    app.setQuitOnLastWindowClosed(False)
    instance = None
    try:
        instance = SingleInstance()
        if not instance.acquire():
            return 0
        logger = configure_logging()
        install_error_handlers()
        logger.info("Starting v0.10; packaged=%s", getattr(sys, "frozen", False))
        window = AvatarOverlay()
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
