from pathlib import Path

from env import load_env
from logging_config import setup_logging

from engine import RosterEngine
from persistence.json_io import (
    load_config,
    load_lines,
    load_employees,
    dump_roster,
)
from persistence.excel_export import export_roster_to_excel


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"


def main() -> None:
    # Load environment
    load_env(BASE_DIR / ".env")

    # Initialise logging
    setup_logging()

    # Load inputs
    config = load_config(DATA_DIR / "config.json")
    lines = load_lines(DATA_DIR / "lines.json")
    employees = load_employees(DATA_DIR / "employees.json")

    engine = RosterEngine(config, lines, employees)
    roster, issues, score = engine.run_once()

    if issues:
        for issue in issues:
            print(issue.severity, issue.message, issue.context)
    else:
        print("Roster valid")

    print("Score:", score.total)

    dump_roster(DATA_DIR / "roster_2025_q1.json", roster)

    export_roster_to_excel(
        roster=roster,
        employees=employees,
        resolved_line_by_emp=engine.generator.resolved_line_by_emp,
        template_path=DATA_DIR / "roster_template.xlsx",
        output_path=DATA_DIR / "roster_2025_q1.xlsx",
    )


if __name__ == "__main__":
    main()
