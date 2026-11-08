"""One rest cycle driven by the same animation/state ticks as normal use."""
from avatar import Action


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
