from dataclasses import dataclass, field
from typing import Dict, List, Set

from domain.shift import ShiftType


@dataclass
class ValidationIssue:
    severity: str  # "ERROR" | "WARN"
    message: str
    context: Dict[str, object] = field(default_factory=dict)


class RosterValidator:
    """
    Hard constraints (CP constraints).

    Model:
    - Employees are assigned to LINE crews
    - A line works a shift on a given day via (pattern + offset)
    - Validation derives per-shift participation dynamically
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(self, roster, employees_by_id: Dict[str, object]) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        days = roster.days()

        for day in range(days):
            for shift in (ShiftType.DAY, ShiftType.NIGHT):
                ok, shift_issues = self._validate_shift_collect(
                    roster, employees_by_id, day, shift
                )
                if not ok:
                    issues.extend(shift_issues)

        return issues

    def validate_shift(
        self,
        roster,
        employees_by_id: Dict[str, object],
        day: int,
        shift: ShiftType,
    ) -> bool:
        ok, _ = self._validate_shift_collect(roster, employees_by_id, day, shift)
        return ok

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _validate_shift_collect(
        self,
        roster,
        employees_by_id: Dict[str, object],
        day: int,
        shift: ShiftType,
    ):
        """
        Validate a single (day, shift) slice.

        Derived model:
        - Find all lines active on this shift
        - Build crews dynamically
        """
        issues: List[ValidationIssue] = []

        # ------------------------------------------------------------------
        # 1. Build working crews for this (day, shift)
        # ------------------------------------------------------------------
        crews_by_line: Dict[int, List[str]] = {}
        staff_seen: Set[str] = set()

        for line in roster.lines:
            line_shift = roster.line_shift_on_day(day, line.line_id)
            if line_shift != shift:
                continue

            crew = roster.get_crew(line.line_id)
            crews_by_line[line.line_id] = crew

            # Ensure no employee appears on multiple lines in same shift
            for emp_id in crew:
                if emp_id in staff_seen:
                    issues.append(
                        ValidationIssue(
                            severity="ERROR",
                            message="Employee assigned to multiple lines in same shift",
                            context={
                                "day": day,
                                "shift": shift.value,
                                "emp_id": emp_id,
                            },
                        )
                    )
                staff_seen.add(emp_id)

        # ------------------------------------------------------------------
        # 2. Enforce coworker constraints within each active crew
        # ------------------------------------------------------------------
        for line_id, crew in crews_by_line.items():
            crew_set = set(crew)

            for emp_id in crew:
                emp = employees_by_id.get(emp_id)
                if not emp:
                    continue

                others = crew_set - {emp_id}

                # --- cant_work_with (hard exclusion)
                conflict = emp.cant_work_with & others
                if conflict:
                    issues.append(
                        ValidationIssue(
                            severity="ERROR",
                            message="cant_work_with violation",
                            context={
                                "day": day,
                                "shift": shift.value,
                                "line_id": line_id,
                                "emp_id": emp_id,
                                "conflict_with": sorted(conflict),
                            },
                        )
                    )

                # --- can_only_work_with (hard inclusion)
                if emp.can_only_work_with:
                    illegal = others - emp.can_only_work_with
                    if illegal:
                        issues.append(
                            ValidationIssue(
                                severity="ERROR",
                                message="can_only_work_with violation",
                                context={
                                    "day": day,
                                    "shift": shift.value,
                                    "line_id": line_id,
                                    "emp_id": emp_id,
                                    "illegal_with": sorted(illegal),
                                },
                            )
                        )

        return (len(issues) == 0), issues
