"""Avatar state and movement logic. Independent of PySide6 rendering."""
from dataclasses import dataclass
from enum import Enum
import random


class Action(str, Enum):
    IDLE = "idle"
    WALK = "walk"
    REST = "rest"
    SIT_DOWN = "sit_down"
    STAND_UP = "stand_up"


@dataclass
class Avatar:
    x: float = 0.0
    direction: int = 1
    speed: float = 75.0  # pixels per second
    action: Action = Action.WALK
    remaining: float = 4.0

    def update(self, dt: float, left: float, right: float) -> None:
        dt = max(0.0, min(dt, 0.1))
        self.remaining -= dt
        if self.remaining <= 0:
            if self.action == Action.WALK:
                self.action = Action.IDLE
                self.remaining = random.uniform(1.0, 3.0)
            else:
                self.action = Action.WALK
                self.remaining = random.uniform(3.0, 7.0)
                if random.random() < 0.35:
                    self.direction *= -1

        if self.action == Action.WALK:
            self.x += self.speed * self.direction * dt

        if self.x >= right:
            self.x = right
            self.direction = -1
        elif self.x <= left:
            self.x = left
            self.direction = 1
