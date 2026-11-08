"""Rest transitions pause movement; optional clips may be omitted."""
from avatar import Action


class RestController:
    def __init__(self, sit_duration=0.0, stand_duration=0.0):
        self.sit_duration = sit_duration
        self.stand_duration = stand_duration
        self.reset()

    def reset(self):
        self.phase = None
        self.requested = False
        self.elapsed = 0.0

    def update(self, wants_rest, dt):
        if wants_rest != self.requested:
            self.requested = wants_rest
            self.elapsed = 0.0
            if wants_rest:
                self.phase = Action.SIT_DOWN if self.sit_duration > 0 else Action.REST
            else:
                self.phase = Action.STAND_UP if self.stand_duration > 0 else None
        elif self.phase in (Action.SIT_DOWN, Action.STAND_UP):
            self.elapsed += max(0.0, dt)
            duration = self.sit_duration if self.phase == Action.SIT_DOWN else self.stand_duration
            if self.elapsed + 1e-9 >= duration:
                self.phase = Action.REST if self.requested else None
                self.elapsed = 0.0
        return self.phase
