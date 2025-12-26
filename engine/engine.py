from pathlib import Path
from typing import List, Tuple

from domain import Roster, Employee, Line

from engine.generator import RosterGenerator
from engine.validator import RosterValidator
from engine.scorer import RosterScorer, ScoreBreakdown
from engine.optimiser import LocalSearchOptimizer, OptimizerConfig
from persistence.json_io import load_scoring_config

scoring_cfg = load_scoring_config(Path("data/scoring.json"))


class RosterEngine:
    """
    Constraint Programming / Local Search façade.

    Pipeline:
    - Build initial roster (deterministic)
    - Optimise via constraint-aware local search
    - Return best roster + issues + score
    """

    def __init__(self, config, lines: List[Line], employees: List[Employee]):
        self.config = config
        self.lines = lines
        self.employees = employees
        self.employees_by_id = {e.emp_id: e for e in employees}

        self.generator = RosterGenerator(config, lines, employees)
        self.validator = RosterValidator()
        self.scorer = RosterScorer(employees, scoring_cfg)

        self.optimiser = LocalSearchOptimizer(
            validator=self.validator,
            scorer=self.scorer,
            employees_by_id=self.employees_by_id,
            config=OptimizerConfig(
                max_iterations=50_000,
                no_improve_limit=5_000,
                random_seed=config.seed,
            ),
        )

    def run_once(self) -> Tuple[Roster, list, ScoreBreakdown]:
        roster = self.generator.generate_initial()
        roster, issues, score = self.optimiser.optimise(roster)
        return roster, issues, score
