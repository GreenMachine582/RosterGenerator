import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from domain import Employee, JobTitle, Line, Role, Roster
from config import ProblemConfig


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _dump_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config(path: Path) -> ProblemConfig:
    raw = _load_json(path)
    return ProblemConfig(**raw)


def dump_config(path: Path, config: ProblemConfig):
    _dump_json(path, config.__dict__)


# ---------------------------------------------------------------------------
# Scoring config
# ---------------------------------------------------------------------------

def load_scoring_config(path: Path) -> dict:
    return _load_json(path)


# ---------------------------------------------------------------------------
# Lines
# ---------------------------------------------------------------------------

def load_lines(path: Path) -> List[Line]:
    raw = _load_json(path)
    return [Line(**row) for row in raw]


def dump_lines(path: Path, lines: List[Line]):
    _dump_json(path, [l.__dict__ for l in lines])


# ---------------------------------------------------------------------------
# Employees
# ---------------------------------------------------------------------------

def load_employees(path: Path) -> List[Employee]:
    raw = _load_json(path)
    employees: List[Employee] = []

    for row in raw:
        employees.append(
            Employee(
                emp_id=row["emp_id"],
                name=row["name"],

                role=Role(row.get("role", Role.PARAMEDIC.value)),
                title=JobTitle(row.get("title", JobTitle.PARA.value)),

                years_experience=row.get("years_experience", 0),
                is_ecp=row.get("is_ecp", False),

                cant_work_with=frozenset(row.get("cant_work_with", [])),
                can_only_work_with=frozenset(row.get("can_only_work_with", [])),
                should_work_with=frozenset(row.get("should_work_with", [])),
                should_not_work_with=frozenset(row.get("should_not_work_with", [])),

                assigned_line_id=row.get("line_id", 0),
                preferred_lines=frozenset(row.get("preferred_lines", [])),
                avoid_lines=frozenset(row.get("avoid_lines", [])),
            )
        )

    return employees


def dump_employees(path: Path, employees: List[Employee]):
    data = []

    for e in employees:
        data.append({
            "emp_id": e.emp_id,
            "name": e.name,
            "line_id": e.line_id,

            "role": e.role.value,
            "title": e.title.value,

            "years_experience": e.years_experience,
            "is_ecp": e.is_ecp,

            "cant_work_with": sorted(e.cant_work_with),
            "can_only_work_with": sorted(e.can_only_work_with),
            "should_work_with": sorted(e.should_work_with),
            "should_not_work_with": sorted(e.should_not_work_with),

            "preferred_lines": sorted(e.preferred_lines),
            "avoid_lines": sorted(e.avoid_lines),
        })

    _dump_json(path, data)


# ---------------------------------------------------------------------------
# Roster
# ---------------------------------------------------------------------------

def dump_roster(path: Path, roster: Roster):
    """
    Persist only the decision variables:
    - which employees belong to which line

    Shifts are derived at runtime and are NOT stored.
    """
    payload = {
        "meta": {
            "weeks": roster.config.weeks,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        },
        "lines": [
            {
                "line_id": line.line_id,
                "employees": roster.get_crew(line.line_id),
            }
            for line in roster.lines
        ],
    }

    _dump_json(path, payload)


def load_roster(path: Path, config: ProblemConfig, lines: List[Line]) -> Roster:
    """
    Load a roster snapshot:
    - Rehydrates line crews
    - Shift behaviour remains derived
    """
    raw = _load_json(path)

    roster = Roster(config=config, lines=lines)

    for entry in raw.get("lines", []):
        line_id = entry["line_id"]
        employees = entry.get("employees", [])
        roster.set_crew(line_id, employees)

    return roster
