from dataclasses import dataclass


@dataclass
class FileAnalysis:
    path: str
    lines: int
    language: str


@dataclass
class RepositoryAnalysis:
    name: str
    files: int
    lines: int
    languages: dict[str, int]
    largest_files: list[FileAnalysis]