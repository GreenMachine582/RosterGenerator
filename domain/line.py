from dataclasses import dataclass

@dataclass(frozen=True)
class Line:
    line_id: int
    offset: int               # rotation offset
    max_headcount: int
