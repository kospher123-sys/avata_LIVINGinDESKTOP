"""Native topmost repair without activation, with a foreground fullscreen exception."""
import ctypes
from ctypes import wintypes
import sys

from PySide6.QtWidgets import QApplication


class MonitorInfo(ctypes.Structure):
    _fields_ = [("size", wintypes.DWORD), ("monitor", wintypes.RECT),
                ("work", wintypes.RECT), ("flags", wintypes.DWORD)]


def covers_monitor(rect, monitor, maximized, bordered):
    return (not maximized and not bordered and rect[0] <= monitor[0] and rect[1] <= monitor[1]
            and rect[2] >= monitor[2] and rect[3] >= monitor[3])


class WindowsStack:
    def __init__(self):
        self.user = ctypes.WinDLL("user32", use_last_error=True)
        self.shell = ctypes.WinDLL("shell32", use_last_error=True)
        self.user.GetForegroundWindow.restype = wintypes.HWND
        self.user.GetShellWindow.restype = wintypes.HWND
        self.user.GetDesktopWindow.restype = wintypes.HWND
        self.user.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        self.user.IsZoomed.argtypes = [wintypes.HWND]
        self.user.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
        self.user.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                            ctypes.c_int, ctypes.c_int, wintypes.UINT]
        self.user.SetWindowPos.restype = wintypes.BOOL
        self.user.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
        self.user.MonitorFromWindow.restype = wintypes.HANDLE
        self.user.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MonitorInfo)]
        self.shell.SHQueryUserNotificationState.argtypes = [ctypes.POINTER(ctypes.c_int)]
        self.fullscreen_blocked = False

    def fullscreen(self, screen, own_handles):
        foreground = self.user.GetForegroundWindow()
        if not foreground or foreground in own_handles:
            return False
        if foreground in (self.user.GetShellWindow(), self.user.GetDesktopWindow()):
            return False
        monitor = self.user.MonitorFromWindow(foreground, 2)
        if monitor != self.user.MonitorFromWindow(own_handles[0], 2):
            return False
        state = ctypes.c_int()
        if self.shell.SHQueryUserNotificationState(ctypes.byref(state)) == 0 and state.value == 3:
            return True
        rect = wintypes.RECT()
        if not self.user.GetWindowRect(foreground, ctypes.byref(rect)):
            return False
        info = MonitorInfo()
        info.size = ctypes.sizeof(info)
        if not self.user.GetMonitorInfoW(monitor, ctypes.byref(info)):
            return False
        style = self.user.GetWindowLongW(foreground, -16)
        bordered = bool(style & (0x00C00000 | 0x00040000))
        bounds = info.monitor
        return covers_monitor((rect.left, rect.top, rect.right, rect.bottom),
                              (bounds.left, bounds.top, bounds.right, bounds.bottom),
                              bool(self.user.IsZoomed(foreground)), bordered)

    def restore(self, widgets, screen):
        visible = [widget for widget in widgets if widget is not None and widget.isVisible()]
        if not visible or screen is None:
            return
        handles = [int(widget.winId()) for widget in visible]
        self.fullscreen_blocked = self.fullscreen(screen, handles)
        insert_after = -2 if self.fullscreen_blocked else -1
        # NOSIZE | NOMOVE | NOACTIVATE | NOOWNERZORDER.
        for handle in handles:
            self.user.SetWindowPos(handle, insert_after, 0, 0, 0, 0, 0x0013 | 0x0200)


def native_stack():
    if sys.platform == "win32" and QApplication.platformName() == "windows":
        return WindowsStack()
    return None
