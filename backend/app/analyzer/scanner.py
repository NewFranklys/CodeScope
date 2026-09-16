import json
import os
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from app.analyzer.ignores import DEFAULT_IGNORED_DIRECTORIES
from app.analyzer.models import RepositoryAnalysis


LANGUAGES_BY_EXTENSION = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".cs": "C#",
    ".c": "C",
    ".h": "C/C++",
    ".cpp": "C++",
    ".hpp": "C++",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sql": "SQL",
    ".sh": "Shell",
    ".ps1": "PowerShell",
    ".md": "Markdown",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".xml": "XML",
    ".txt": "Text",
}


def detect_language(file_path: Path) -> str | None:
    return LANGUAGES_BY_EXTENSION.get(file_path.suffix.lower())


def count_lines(file_path: Path) -> int:
    try:
        with file_path.open(
            "r",
            encoding="utf-8",
            errors="ignore",
        ) as file:
            return sum(1 for _ in file)
    except OSError:
        return 0


def scan_repository(repository_path: str) -> RepositoryAnalysis:
    path = Path(repository_path).resolve()

    if not path.exists():
        raise FileNotFoundError(
            f"Repository not found: {repository_path}"
        )

    if not path.is_dir():
        raise NotADirectoryError(
            f"Not a directory: {repository_path}"
        )

    total_files = 0
    total_lines = 0
    languages: Counter[str] = Counter()

    for root, directories, files in os.walk(path):
        directories[:] = [
            directory
            for directory in directories
            if directory not in DEFAULT_IGNORED_DIRECTORIES
        ]

        root_path = Path(root)

        for filename in files:
            file_path = root_path / filename

            total_files += 1

            language = detect_language(file_path)

            if language is None:
                continue

            languages[language] += 1
            total_lines += count_lines(file_path)

    return RepositoryAnalysis(
        name=path.name,
        files=total_files,
        lines=total_lines,
        languages=dict(languages.most_common()),
    )


if __name__ == "__main__":
    repository = input("Repository path: ").strip()

    analysis = scan_repository(repository)

    print(
        json.dumps(
            asdict(analysis),
            indent=2,
            ensure_ascii=False,
        )
    )