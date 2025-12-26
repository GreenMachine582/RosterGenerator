import logging
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from domain import Roster, ShiftType
from engine.validator import RosterValidator
from engine.scorer import RosterScorer, ScoreBreakdown

log = logging.getLogger(__name__)

Date = int
LineId = int
EmpId = str
ShiftKey = Tuple[Date, ShiftType]


@dataclass
class OptimizerConfig:
    max_iterations: int = 50_000
    no_improve_limit: int = 5_000
    random_seed: int = 42

    # neighbourhood controls
    moves_per_iteration: int = 1          # attempt N candidate moves per iteration
    sample_shifts: int = 50               # how many shift buckets to sample per iteration

    log_every: int = 500


@dataclass
class Move:
    """
    Swap one employee between two line crews.

    Note:
    - The crew buckets are global (line assignment), not per-day.
    - day/shift are used only for *context* (fast validation / future heuristics),
      because only lines active on that day/shift need checking in validate_shift().
    """
    day: int
    shift: ShiftType
    line_a: int
    line_b: int
    emp_a: str
    emp_b: str


class LocalSearchOptimizer:
    """
    Constraint-aware greedy local search (hill climbing) over LINE CREWS.

    Model:
    - roster.crew_by_line[line_id] holds the assigned employee IDs for that line
    - a line's shift on a day is derived via pattern+offset (Roster APIs)
    """

    def __init__(
        self,
        *,
        validator: RosterValidator,
        scorer: RosterScorer,
        employees_by_id: Dict[str, object],
        config: OptimizerConfig,
    ):
        self.validator = validator
        self.scorer = scorer
        self.employees_by_id = employees_by_id
        self.cfg = config
        self.rng = random.Random(config.random_seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def optimise(self, roster: Roster) -> Tuple[Roster, List[object], ScoreBreakdown]:
        log.info("Starting local search optimisation (crew swaps)")

        working = roster.copy()
        best_roster = working.copy()
        best_score = self.scorer.score(best_roster)

        log.info("Initial score: %s", best_score.total)

        # If starting roster is invalid, we still attempt repair.
        initial_issues = self.validator.validate(best_roster, self.employees_by_id)
        if initial_issues:
            log.warning("Initial roster has %d validation issues", len(initial_issues))

        no_improve = 0
        shift_keys = self._all_shift_keys(working)

        for it in range(1, self.cfg.max_iterations + 1):
            if no_improve >= self.cfg.no_improve_limit:
                log.info(
                    "Stopping early at iteration %d (no improvement for %d iters)",
                    it,
                    no_improve,
                )
                break

            improved = False

            sampled = list(shift_keys)
            self.rng.shuffle(sampled)
            sampled = sampled[: min(self.cfg.sample_shifts, len(sampled))]

            for _ in range(self.cfg.moves_per_iteration):
                move = self._propose_swap_move(working, sampled)
                if not move:
                    continue

                self._apply_swap_crews(working, move)

                # Fast check: validate only the sampled (day,shift) context
                # (checks only lines active at that moment if your validate_shift is implemented that way).
                if not self.validator.validate_shift(
                    roster=working,
                    employees_by_id=self.employees_by_id,
                    day=move.day,
                    shift=move.shift,
                ):
                    self._apply_swap_crews(working, move)  # revert
                    continue

                # Full objective (can be optimized later with incremental scoring)
                candidate_score = self.scorer.score(working)

                if candidate_score.total > best_score.total:
                    best_score = candidate_score
                    best_roster = working.copy()
                    improved = True

                    log.debug(
                        "Improved @ iter %d: score=%s via %s",
                        it,
                        best_score.total,
                        move,
                    )
                else:
                    self._apply_swap_crews(working, move)  # revert

            no_improve = 0 if improved else (no_improve + 1)

            if it % self.cfg.log_every == 0:
                log.info(
                    "Iter %d | best=%s | no_improve=%d",
                    it,
                    best_score.total,
                    no_improve,
                )

        final_issues = self.validator.validate(best_roster, self.employees_by_id)

        log.info(
            "Optimisation complete | final_score=%s | issues=%d",
            best_score.total,
            len(final_issues),
        )

        return best_roster, final_issues, best_score

    # ------------------------------------------------------------------
    # Neighbourhood: swap between line crews (global)
    # ------------------------------------------------------------------

    def _propose_swap_move(
        self,
        roster: Roster,
        sampled_shift_keys: Sequence[ShiftKey],
    ) -> Optional[Move]:
        """
        Propose a swap between two line crews.

        We use (day,shift) only to:
        - bias toward swapping between lines that are working in that context
        - provide a context for validate_shift() to run quickly
        """
        line_ids = list(roster.lines_by_id.keys())
        if len(line_ids) < 2:
            return None

        for (day, shift) in sampled_shift_keys:
            # Prefer lines that are active on this (day,shift) to make validate_shift meaningful.
            active_lines = [
                lid for lid in line_ids
                if roster.line_shift_on_day(day, lid) == shift
                and roster.get_crew(lid)
            ]

            # If not enough active lines, fall back to any populated lines
            if len(active_lines) < 2:
                active_lines = [lid for lid in line_ids if roster.get_crew(lid)]

            if len(active_lines) < 2:
                continue

            line_a, line_b = self.rng.sample(active_lines, 2)
            crew_a = roster.get_crew(line_a)
            crew_b = roster.get_crew(line_b)

            emp_a = self.rng.choice(crew_a)
            emp_b = self.rng.choice(crew_b)

            empA = self.employees_by_id.get(emp_a)
            empB = self.employees_by_id.get(emp_b)
            if not empA or not empB:
                continue

            # --------------------------------------------------------------
            # HARD CONSTRAINT: assigned_line_id
            # --------------------------------------------------------------
            if empA.assigned_line_id and empA.assigned_line_id != line_a:
                continue
            if empB.assigned_line_id and empB.assigned_line_id != line_b:
                continue

            # Would the swap violate assignment locks?
            if empA.assigned_line_id and empA.assigned_line_id != line_b:
                continue
            if empB.assigned_line_id and empB.assigned_line_id != line_a:
                continue

            # --------------------------------------------------------------
            # Soft preference bias
            # --------------------------------------------------------------
            if line_b in empA.avoid_lines and line_a not in empA.preferred_lines:
                continue
            if line_a in empB.avoid_lines and line_b not in empB.preferred_lines:
                continue

            return Move(day, shift, line_a, line_b, emp_a, emp_b)

        return None

    def _apply_swap_crews(self, roster: Roster, move: Move) -> None:
        """
        Swap employees between two line crews (global buckets).
        Swapping twice reverts.
        """
        crew_a = roster.get_crew(move.line_a)
        crew_b = roster.get_crew(move.line_b)

        if move.emp_a not in crew_a or move.emp_b not in crew_b:
            return

        ia = crew_a.index(move.emp_a)
        ib = crew_b.index(move.emp_b)

        crew_a[ia], crew_b[ib] = crew_b[ib], crew_a[ia]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _all_shift_keys(self, roster: Roster) -> List[ShiftKey]:
        return [
            (day, shift)
            for day in range(roster.days())
            for shift in (ShiftType.DAY, ShiftType.NIGHT)
        ]
