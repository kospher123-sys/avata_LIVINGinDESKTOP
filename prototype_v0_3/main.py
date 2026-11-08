"""Run the v0.3 Aang sprite overlay from any working directory."""
import argparse
import sys

from PySide6.QtWidgets import QApplication, QMessageBox
from overlay import AvatarOverlay


def main():
    parser = argparse.ArgumentParser(description="아앙 데스크톱 오버레이")
    parser.add_argument("--height", type=int, choices=(120, 150, 180), default=150,
                        help="캐릭터 표시 높이 (기본: 150px)")
    args = parser.parse_args()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    try:
        window = AvatarOverlay(height=args.height)
    except ValueError as error:
        QMessageBox.critical(None, "아앙 이미지 로드 실패", str(error))
        return 1
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
