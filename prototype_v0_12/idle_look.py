"""Occasional one-shot idle gesture; higher-priority actions may interrupt."""
import random


class IdleLook:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.playing = False
        self.elapsed = 0.0
        self.duration = 0.0
        self.dwell = 0.0
        self.cooldown = self.rng.uniform(20.0, 40.0)

    def start(self, duration):
        self.playing = True
        self.elapsed = 0.0
        self.duration = duration

    def cancel(self):
        if self.playing:
            self.cooldown = self.rng.uniform(20.0, 40.0)
        self.playing = False
        self.elapsed = 0.0
        self.dwell = 0.0

    def update(self, dt, eligible, available, duration):
        dt = max(0.0, dt)
        if not available:
            self.cancel()
            return False
        if self.playing:
            if not eligible:
                self.cancel()
                return False
            self.elapsed += dt
            if self.elapsed + 1e-9 >= self.duration:
                self.cancel()
                return False
            return True
        self.cooldown = max(0.0, self.cooldown - dt)
        self.dwell = self.dwell + dt if eligible else 0.0
        if eligible and self.cooldown == 0 and self.dwell >= .5:
            self.start(duration)
        return self.playing
