from enum import Enum
from dataclasses import dataclass
from typing import Tuple

class ShiftType(str, Enum):
    DAY = "D"
    NIGHT = "N"
    OFF = "OFF"

@dataclass(frozen=True)
class ShiftPattern:
    cycle: Tuple[ShiftType, ...] = (
        ShiftType.DAY,
        ShiftType.DAY,
        ShiftType.NIGHT,
        ShiftType.NIGHT,
        ShiftType.OFF,
        ShiftType.OFF,
        ShiftType.OFF,
        ShiftType.OFF,
        ShiftType.OFF,
    )

    def shift_on_day(self, day_index: int, offset: int) -> ShiftType:
        return self.cycle[(day_index + offset) % len(self.cycle)]
