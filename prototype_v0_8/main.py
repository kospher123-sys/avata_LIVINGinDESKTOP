"""v0.8 desktop overlay with single-instance control."""
import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox
from overlay import AvatarOverlay
from single_instance import SingleInstance


def main():
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
        window = AvatarOverlay()
    except (ValueError, OSError) as error:
        QMessageBox.critical(None, "아앙 실행 실패", str(error))
        if instance is not None:
            instance.close()
        return 1
    instance.activated.connect(window.open_settings)
    app.aboutToQuit.connect(instance.close)
    window.sync_runtime()
    if "--settings" in sys.argv:
        window.open_settings()
    try:
        return app.exec()
    finally:
        instance.close()


if __name__ == "__main__":
    sys.exit(main())
