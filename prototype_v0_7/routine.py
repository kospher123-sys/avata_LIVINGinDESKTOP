"""Local-clock schedule; supports overnight rest periods."""
from datetime import datetime


def is_rest_time(minute, start, end):
    if start == end:
        return False  # Equal endpoints disable the rest interval.
    if start < end:
        return start <= minute < end
    return minute >= start or minute < end


def routine_state(preferences, now=None):
    if not preferences.auto_move:
        return "stopped"
    if not preferences.routine_enabled:
        return "free"
    now = now if now is not None else datetime.now().astimezone()
    minute = now.hour * 60 + now.minute
    return "rest" if is_rest_time(minute, preferences.rest_start, preferences.rest_end) else "active"
