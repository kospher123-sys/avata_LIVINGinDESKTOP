"""Native Windows wake hints plus a timer-gap fallback."""
import sys

WM_POWERBROADCAST = 0x0218
RESUME_EVENTS = {0x0006, 0x0007, 0x0012}


def is_resume_message(message_id, event):
    return message_id == WM_POWERBROADCAST and event in RESUME_EVENTS


def is_native_resume(event_type, pointer):
    if sys.platform != "win32" or bytes(event_type) not in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
        return False
    import ctypes
    from ctypes import wintypes
    message = ctypes.cast(int(pointer), ctypes.POINTER(wintypes.MSG)).contents
    return is_resume_message(message.message, message.wParam)


class GapDetector:
    def __init__(self, threshold=10):
        self.threshold = threshold
        self.last = None

    def check(self, now):
        previous = self.last
        self.last = now
        return previous is not None and (now - previous > self.threshold or now < previous)
