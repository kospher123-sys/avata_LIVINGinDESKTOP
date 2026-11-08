"""Entry point for the v0.2 prototype."""
import sys
from PySide6.QtWidgets import QApplication
from overlay import AvatarOverlay


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = AvatarOverlay()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
