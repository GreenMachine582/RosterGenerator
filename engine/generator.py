import logging
from collections import defaultdict
from typing import Dict, List, Tuple

from domain import Employee, Line, Roster

log = logging.getLogger(__name__)


class RosterGenerator:
    """
    Initial solution builder.

    Deterministic, line-centric, crew-bucket driven.

    Key model:
    - Employees are assigned to a LINE (bucket/crew)
    - A line's shift on a given day is derived from (pattern + line.offset)
    """

    def __init__(self, config, lines: List[Line], employees: List[Employee]):
        self.config = config
        self.lines_list: List[Line] = list(lines)
        self.lines: Dict[int, Line] = {l.line_id: l for l in lines}

        log.info(
            "Initialising RosterGenerator: %d lines, %d employees",
            len(lines),
            len(employees),
        )

        # Build employees_by_line with auto-assignment for line_id == 0
        self.employees_by_line, self.resolved_line_by_emp = self._build_employees_by_line(employees)

    def _is_crew_compatible(self, crew: List[Employee]) -> bool:
        """
        Enforce hard coworker constraints:
        - cant_work_with
        - can_only_work_with
        """
        crew_ids = {e.emp_id for e in crew}

        for e in crew:
            # cant_work_with: no excluded coworker may be in same crew
            if e.cant_work_with & (crew_ids - {e.emp_id}):
                return False

            # can_only_work_with: if set, everyone else in crew must be allowed
            if e.can_only_work_with:
                if not (crew_ids - {e.emp_id}).issubset(e.can_only_work_with):
                    return False

        return True

    def _build_employees_by_line(self, employees: List[Employee]) -> tuple[Dict[int, List[Employee]], Dict[str, int]]:
        """
        Deterministically assign employees with line_id == 0 to valid lines.

        Strategy:
        - Keep existing assignments (assigned_line_id in 1..N)
        - For unassigned employees (line_id == 0):
            assign to the line with the most remaining capacity (tie -> lowest line_id)
        - Enforce max_headcount strictly
        - Enforce hard coworker constraints during assignment
        """
        employees_by_line: Dict[int, List[Employee]] = defaultdict(list)
        resolved_line_by_emp: Dict[str, int] = {}

        # Seed pre-assigned
        for e in employees:
            if e.assigned_line_id and e.assigned_line_id in self.lines:
                employees_by_line[e.assigned_line_id].append(e)
                resolved_line_by_emp[e.emp_id] = e.assigned_line_id

        used = {lid: len(employees_by_line.get(lid, [])) for lid in self.lines}
        cap = {lid: self.lines[lid].max_headcount for lid in self.lines}

        log.info("Pre-assigned staff per line: %s", used)

        unassigned = [e for e in employees if e.emp_id not in resolved_line_by_emp]
        log.info("Employees requiring auto-assignment: %d", len(unassigned))

        for e in unassigned:
            candidates: List[Tuple[int, int]] = []

            # Identify if employee is compatible with each line's existing crew
            for lid in sorted(self.lines):
                remaining = cap[lid] - used[lid]
                if remaining <= 0:
                    continue

                tentative_crew = employees_by_line[lid] + [e]
                if not self._is_crew_compatible(tentative_crew):
                    continue

                candidates.append((remaining, lid))

            if not candidates:
                raise RuntimeError(
                    f"No valid line for {e.emp_id}: coworker constraints cannot be satisfied"
                )

            # Deterministic: most remaining capacity, then lowest line_id
            candidates.sort(key=lambda x: (-x[0], x[1]))
            _, chosen_line = candidates[0]

            employees_by_line[chosen_line].append(e)
            resolved_line_by_emp[e.emp_id] = chosen_line
            used[chosen_line] += 1

            log.debug("Resolved line for %s → %d", e.emp_id, chosen_line)

        log.info("Final staff distribution per line: %s", used)

        return dict(employees_by_line), resolved_line_by_emp

    def generate_initial(self) -> Roster:
        log.info("Generating initial roster (line crews)")

        roster = Roster(config=self.config, lines=self.lines_list)

        for line_id, line in self.lines.items():
            crew = self.employees_by_line.get(line_id, [])

            if len(crew) > line.max_headcount:
                raise RuntimeError(
                    f"Line {line_id} has {len(crew)} staff, expected max {line.max_headcount}"
                )

            roster.set_crew(line_id, [e.emp_id for e in crew])

        log.info("Initial roster generation complete (crews assigned)")
        return roster
