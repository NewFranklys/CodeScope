from dataclasses import dataclass


@dataclass
class RepositoryAnalysis:
    name: str
    files: int
    lines: int
    languages: dict[str, int]