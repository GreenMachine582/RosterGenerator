from dataclasses import dataclass, field
import os

from domain import ShiftPattern


@dataclass
class ProblemConfig:
    """
    Global configuration for a roster generation run.
    """
    weeks: int = int(os.getenv("ROSTER_WEEKS", 9))
    lines: int = int(os.getenv("ROSTER_LINES", 9))
    seed: int = int(os.getenv("OPT_RANDOM_SEED", 42))

    pattern: ShiftPattern = field(default_factory=ShiftPattern)

    def total_days(self) -> int:
        return self.weeks * 7
