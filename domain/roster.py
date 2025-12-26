from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from .shift import ShiftType
from .line import Line


@dataclass
class Roster:
    config: object
    lines: List[Line]

    # line_id -> list[emp_id] (crew bucket)
    crew_by_line: Dict[int, List[str]] = field(default_factory=dict)

    # cached lookup
    lines_by_id: Dict[int, Line] = field(init=False)

    def __post_init__(self) -> None:
        self.lines_by_id = {l.line_id: l for l in self.lines}
        # ensure all line buckets exist
        for line_id in self.lines_by_id:
            self.crew_by_line.setdefault(line_id, [])

    def days(self) -> int:
        return self.config.weeks * 7

    # ------------------------------------------------------------------
    # Crew management
    # ------------------------------------------------------------------

    def get_crew(self, line_id: int) -> List[str]:
        return self.crew_by_line.setdefault(line_id, [])

    def set_crew(self, line_id: int, emp_ids: List[str]) -> None:
        self.crew_by_line[line_id] = list(emp_ids)

    def add_to_line(self, line_id: int, emp_id: str) -> None:
        crew = self.get_crew(line_id)
        if emp_id not in crew:
            crew.append(emp_id)

    def remove_from_line(self, line_id: int, emp_id: str) -> None:
        crew = self.get_crew(line_id)
        if emp_id in crew:
            crew.remove(emp_id)

    # ------------------------------------------------------------------
    # Shift hooks / APIs
    # ------------------------------------------------------------------

    def line_shift_on_day(self, day: int, line_id: int) -> ShiftType:
        line = self.lines_by_id[line_id]
        return self.config.pattern.shift_on_day(day, line.offset)

    def employees_on_shift(self, day: int, shift: ShiftType) -> Dict[int, List[str]]:
        """
        Returns: {line_id: [emp_id, ...]} for lines working this shift.
        """
        out: Dict[int, List[str]] = {}
        for line_id in self.lines_by_id:
            s = self.line_shift_on_day(day, line_id)
            if s == shift:
                out[line_id] = list(self.get_crew(line_id))
        return out

    def employees_working(self, day: int) -> Dict[ShiftType, Dict[int, List[str]]]:
        """
        Returns both day & night allocations for a date:
          {ShiftType.DAY: {line_id: [...]}, ShiftType.NIGHT: {...}}
        """
        return {
            ShiftType.DAY: self.employees_on_shift(day, ShiftType.DAY),
            ShiftType.NIGHT: self.employees_on_shift(day, ShiftType.NIGHT),
        }

    def all_employees_working_ids(self, day: int, shift: ShiftType) -> Set[str]:
        """
        Flattened set of all employees working on that shift (across lines).
        """
        buckets = self.employees_on_shift(day, shift)
        out: Set[str] = set()
        for crew in buckets.values():
            out.update(crew)
        return out

    def total_staff_on_shift(self, day: int, shift: ShiftType) -> int:
        total = 0
        for crew in self.employees_on_shift(day, shift).values():
            total += len(crew)
        return total

    def copy(self) -> "Roster":
        new = Roster(self.config, self.lines)
        new.crew_by_line = {lid: list(crew) for lid, crew in self.crew_by_line.items()}
        return new
