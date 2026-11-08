"""v0.6 desktop overlay with optional local-clock daily routine."""
import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox
from overlay import AvatarOverlay


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Malgun Gothic", 10))
    app.setOrganizationName("AvatarLivingInDesktop")
    app.setApplicationName("AangOverlay")
    app.setQuitOnLastWindowClosed(False)
    try:
        window = AvatarOverlay()
    except (ValueError, OSError) as error:
        QMessageBox.critical(None, "아앙 실행 실패", str(error))
        return 1
    window.show()
    if "--settings" in sys.argv:
        window.open_settings()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
