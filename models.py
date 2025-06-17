from dataclasses import dataclass, field
from typing import List

@dataclass
class Step:
    x: int
    y: int
    radius: int
    delay_min: float
    delay_max: float

@dataclass
class Config:
    name: str
    steps: List[Step] = field(default_factory=list)
