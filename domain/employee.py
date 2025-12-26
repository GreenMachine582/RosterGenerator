from dataclasses import dataclass, field
from enum import Enum
from typing import FrozenSet


class Role(Enum):
    ICP = "ICP"
    PARAMEDIC = "PARAMEDIC"
    INTERN = "INTERN"


class JobTitle(Enum):
    PARA_SPEC = "PARA_SPEC"
    PARA = "PARA"
    MGR = "MGR"
    PARA_INTERN = "PARA_INTERN"


@dataclass(frozen=True)
class Employee:
    # Identity
    emp_id: str
    name: str
    line_id: int = 0

    # Professional classification
    role: Role = Role.PARAMEDIC
    title: JobTitle = JobTitle.PARA

    # Experience & capability
    years_experience: int = 0
    is_ecp: bool = False

    # Coworker relationships
    cant_work_with: FrozenSet[str] = field(default_factory=frozenset)
    can_only_work_with: FrozenSet[str] = field(default_factory=frozenset)
    should_work_with: FrozenSet[str] = field(default_factory=frozenset)
    should_not_work_with: FrozenSet[str] = field(default_factory=frozenset)

    # Line preferences
    assigned_line_id: int = 0
    preferred_lines: FrozenSet[int] = field(default_factory=frozenset)
    avoid_lines: FrozenSet[int] = field(default_factory=frozenset)

    def display_name(self) -> str:
        return f"{self.name} ({self.emp_id}) [{self.role}, {self.title} yrs:{self.years_experience}{'' if not self.is_ecp else ', ECP'}]"
