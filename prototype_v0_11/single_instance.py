"""Per-user process lock and activation notification for duplicate launches."""
import hashlib
from pathlib import Path

from PySide6.QtCore import QObject, QLockFile, QStandardPaths, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket


class SingleInstance(QObject):
    activated = Signal()

    def __init__(self, directory=None):
        super().__init__()
        if directory is None:
            directory = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
        directory = Path(directory).resolve()
        directory.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(str(directory).casefold().encode()).hexdigest()[:24]
        self.name = f"AangOverlay-{digest}"
        self.lock = QLockFile(str(directory / "instance.lock"))
        self.lock.setStaleLockTime(0)
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self._activate)
        self.primary = False

    def acquire(self):
        if not self.lock.tryLock(0):
            if self.lock.error() != QLockFile.LockError.LockFailedError:
                raise OSError("실행 상태를 확인할 수 없습니다. 사용자 폴더의 쓰기 권한을 확인해 주세요.")
            socket = QLocalSocket()
            socket.connectToServer(self.name)
            socket.waitForConnected(1000)
            socket.disconnectFromServer()
            return False
        # Only the lock owner may remove a stale local-server endpoint.
        QLocalServer.removeServer(self.name)
        if not self.server.listen(self.name):
            self.lock.unlock()
            raise OSError("실행 중인 앱을 연결할 수 없습니다: " + self.server.errorString())
        self.primary = True
        return True

    def _activate(self):
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            socket.disconnectFromServer()
            socket.deleteLater()
            self.activated.emit()

    def close(self):
        if self.primary:
            self.server.close()
            self.lock.unlock()
            self.primary = False
