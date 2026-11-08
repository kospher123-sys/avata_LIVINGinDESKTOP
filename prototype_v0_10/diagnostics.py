"""Bounded local logs and exception records for windowed releases."""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys

from PySide6.QtCore import QStandardPaths, QtMsgType, qInstallMessageHandler
from PySide6.QtWidgets import QApplication, QMessageBox

logging.getLogger("aang").addHandler(logging.NullHandler())


def log_directory():
    return Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)) / "logs"


def configure_logging(directory=None):
    directory = Path(directory) if directory is not None else log_directory()
    directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("aang")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    handler = RotatingFileHandler(directory / "app.log", maxBytes=1024 * 1024, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)
    return logger


def install_error_handlers():
    logger = logging.getLogger("aang")
    handling = False

    def exception_hook(kind, value, traceback):
        nonlocal handling
        if issubclass(kind, KeyboardInterrupt):
            QApplication.instance().quit()
            return
        logger.critical("Unhandled exception", exc_info=(kind, value, traceback))
        if handling:
            return
        handling = True
        try:
            QMessageBox.critical(None, "아앙 실행 오류", "문제가 발생해 앱을 종료합니다.\n문제 기록 폴더의 app.log를 확인해 주세요.")
        finally:
            QApplication.instance().exit(1)

    def qt_message(kind, context, message):
        if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
            logger.warning("Qt: %s", message)

    sys.excepthook = exception_hook
    qInstallMessageHandler(qt_message)
