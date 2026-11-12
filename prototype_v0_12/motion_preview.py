"""One rest cycle driven by the same animation/state ticks as normal use."""
from avatar import Action


class ActionShowcase:
    """One cycle of every loaded clip, in registration order."""
    def __init__(self):
        self.items = []
        self.index = 0
        self.elapsed = 0.0
        self.active = False

    @property
    def action(self):
        return self.items[self.index][0] if self.active else None

    def start(self, animation):
        self.items = [(action, animation.clip_duration(action)) for action, frames in animation.frames.items()
                      if frames and animation.has_clip(action) and animation.clip_duration(action) > 0]
        self.index = 0
        self.elapsed = 0.0
        self.active = bool(self.items)
        return self.active

    def advance(self, dt):
        if not self.active:
            return
        self.elapsed += max(0.0, dt)
        if self.elapsed + 1e-9 >= self.items[self.index][1]:
            self.index += 1
            self.elapsed = 0.0
            self.active = self.index < len(self.items)

    def cancel(self):
        self.active = False
        self.elapsed = 0.0


class MotionPreview:
    def __init__(self):
        self.active = False
        self.stage = ""
        self.elapsed = 0.0
        self.rest_duration = 0.0

    def start(self, rest_duration):
        self.active = True
        self.stage = "sitting"
        self.elapsed = 0.0
        self.rest_duration = rest_duration

    @property
    def wants_rest(self):
        return self.stage in ("sitting", "resting")

    def advance(self, phase, dt):
        if not self.active:
            return
        if self.stage == "sitting" and phase == Action.REST:
            self.stage = "resting"
            self.elapsed = 0.0
        elif self.stage == "resting":
            self.elapsed += max(0.0, dt)
            if self.elapsed + 1e-9 >= self.rest_duration:
                self.stage = "standing"
        elif self.stage == "standing" and phase is None:
            self.cancel()

    def cancel(self):
        self.active = False
        self.stage = ""
        self.elapsed = 0.0
