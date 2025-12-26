from dataclasses import dataclass
from typing import Dict, List, Set

from domain.shift import ShiftType


@dataclass
class ScoreBreakdown:
    total: float
    components: Dict[str, float]


class RosterScorer:
    """
    Objective function for Local Search.

    Model:
    - Employees are assigned to LINE crews
    - A line works a shift on a day via (pattern + offset)
    - All scoring is derived dynamically per (day, shift)
    """

    def __init__(self, employees: List[object], scoring_cfg: dict):
        self.employees_by_id = {e.emp_id: e for e in employees}

        # Coverage
        coverage = scoring_cfg.get("coverage", {})
        self.target_coverage = coverage.get("target_staff", 7)
        self.W_COVERAGE = coverage.get("weight", 1.0)

        # Line preferences
        line_prefs = scoring_cfg.get("line_preferences", {})
        self.W_PREFERRED_LINE = line_prefs.get("preferred_line", 1.0)
        self.W_AVOID_LINE = line_prefs.get("avoid_line", 1.0)

        # Coworkers
        coworkers = scoring_cfg.get("coworkers", {})
        self.W_SHOULD_WORK = coworkers.get("should_work_with", 1.0)
        self.W_SHOULD_NOT_WORK = coworkers.get("should_not_work_with", 1.0)

        # Synergy (future)
        self.synergy_cfg = scoring_cfg.get("synergy", {})

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score(self, roster) -> ScoreBreakdown:
        components = {
            "coworker_preferences": 0.0,
            "coverage_balance": 0.0,
            "line_preferences": 0.0,
            "synergy": 0.0,
        }

        for day in range(roster.days()):
            for shift in (ShiftType.DAY, ShiftType.NIGHT):
                total_staff = 0

                for line in roster.lines:
                    if roster.line_shift_on_day(day, line.line_id) != shift:
                        continue

                    crew = roster.get_crew(line.line_id)
                    if not crew:
                        continue

                    total_staff += len(crew)

                    components["coworker_preferences"] += self._score_coworkers(crew)
                    components["line_preferences"] += self._score_line_preferences(
                        crew, line.line_id
                    )
                    components["synergy"] += self._score_synergy(set(crew))

                components["coverage_balance"] += self._score_coverage(total_staff)

        total = sum(components.values())
        return ScoreBreakdown(total=total, components=components)

    # ------------------------------------------------------------------
    # Scoring primitives
    # ------------------------------------------------------------------

    def _score_coworkers(self, staff_ids: List[str]) -> float:
        s = 0.0
        staff_set = set(staff_ids)

        for emp_id in staff_set:
            emp = self.employees_by_id.get(emp_id)
            if not emp:
                continue

            s += self.W_SHOULD_WORK * len(emp.should_work_with & (staff_set - {emp_id}))
            s -= self.W_SHOULD_NOT_WORK * len(emp.should_not_work_with & (staff_set - {emp_id}))

        return s

    def _score_line_preferences(self, staff_ids: List[str], line_id: int) -> float:
        s = 0.0

        for emp_id in staff_ids:
            emp = self.employees_by_id.get(emp_id)
            if not emp:
                continue

            if line_id in emp.preferred_lines:
                s += self.W_PREFERRED_LINE

            if line_id in emp.avoid_lines:
                s -= self.W_AVOID_LINE

        return s

    def _score_coverage(self, actual: int) -> float:
        return -self.W_COVERAGE * abs(actual - self.target_coverage)

    def _score_synergy(self, staff_ids: Set[str]) -> float:
        """
        Placeholder for role/title/experience/ECP synergy.

        Returns 0.0 until weights/rules are defined.
        """
        staff = [self.employees_by_id[eid] for eid in staff_ids if eid in self.employees_by_id]
        if not staff:
            return 0.0

        # Available signals (for future use)
        roles = {e.role for e in staff}
        has_ecp = any(e.is_ecp for e in staff)
        experience = [e.years_experience for e in staff]

        _ = (roles, has_ecp, experience)  # intentionally unused for now
        return 0.0
