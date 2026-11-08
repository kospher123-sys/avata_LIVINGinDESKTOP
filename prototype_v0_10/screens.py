"""Screen identity and selection, independent of window placement."""
import json


def screen_key(screen):
    serial = screen.serialNumber()
    if serial:
        return json.dumps([screen.manufacturer(), screen.model(), serial], ensure_ascii=False)
    return screen.name()


def select_screen(screens, preferred, primary):
    for screen in screens:
        if preferred and screen_key(screen) == preferred:
            return screen
    return primary if primary in screens else next(iter(screens), None)


def screen_label(screen, primary=False):
    geometry = screen.geometry()
    ratio = screen.devicePixelRatio()
    width, height = round(geometry.width() * ratio), round(geometry.height() * ratio)
    suffix = " · 기본" if primary else ""
    return f"{screen.name()} · {width}×{height} · {round(ratio * 100)}%{suffix}"
