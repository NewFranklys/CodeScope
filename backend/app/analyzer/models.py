from dataclasses import dataclass


@dataclass
class TodoItem:
    path: str
    line: int
    tag: str
    text: str


@dataclass
class FileAnalysis:
    path: str
    lines: int
    language: str
    size_bytes: int
    todos: int


@dataclass
class DependencyManifest:
    path: str
    kind: str
    dependencies: int | None


@dataclass
class GitInsights:
    branch: str | None
    commits: int
    changed_files: int
    tracked_files: int


@dataclass
class Hotspot:
    path: str
    language: str
    lines: int
    todos: int
    score: int


@dataclass
class RepositoryAnalysis:
    name: str
    path: str
    files: int
    analyzed_files: int
    directories: int
    lines: int
    size_bytes: int
    languages: dict[str, int]
    language_lines: dict[str, int]
    largest_files: list[FileAnalysis]
    todos: list[TodoItem]
    dependency_manifests: list[DependencyManifest]
    git: GitInsights | None
    hotspots: list[Hotspot]
    files_index: list[str]
    files_index_truncated: bool
