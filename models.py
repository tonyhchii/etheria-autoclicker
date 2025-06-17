from dataclasses import dataclass, field
from typing import List

@dataclass
class Step:
    def __init__(self, x, y, radius, delay_min, delay_max, name ="Step"):
        self.name = name
        self.x = x
        self.y = y
        self.radius = radius
        self.delay_min = delay_min
        self.delay_max = delay_max

    def to_dict(self):
        return {
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "radius": self.radius,
            "delay_min": self.delay_min,
            "delay_max": self.delay_max
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            x=data["x"],
            y=data["y"],
            radius=data["radius"],
            delay_min=data["delay_min"],
            delay_max=data["delay_max"]
        )

@dataclass
class Config:
    def __init__(self, name):
        self.name = name
        self.steps: List[Step] = []

    def to_dict(self):
        return {
            "name": self.name,
            "steps": [step.to_dict() for step in self.steps]
        }

    @classmethod
    def from_dict(cls, data):
        cfg = cls(data["name"])
        cfg.steps = [Step.from_dict(step_data) for step_data in data.get("steps", [])]
        return cfg