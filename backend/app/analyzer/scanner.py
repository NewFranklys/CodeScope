import json
import os
import re
import subprocess
from collections import Counter
from pathlib import Path

from app.analyzer.ignores import DEFAULT_IGNORED_DIRECTORIES
from app.analyzer.models import (
    DependencyManifest,
    FileAnalysis,
    GitInsights,
    Hotspot,
    RepositoryAnalysis,
    TodoItem,
)


LANGUAGES_BY_EXTENSION = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".cs": "C#",
    ".c": "C",
    ".h": "C/C++",
    ".cpp": "C++",
    ".cc": "C++",
    ".hpp": "C++",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    ".sql": "SQL",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".ps1": "PowerShell",
    ".md": "Markdown",
    ".mdx": "MDX",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".xml": "XML",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".dart": "Dart",
    ".lua": "Lua",
    ".r": "R",
    ".txt": "Text",
}

LANGUAGES_BY_FILENAME = {
    "Dockerfile": "Dockerfile",
    "Makefile": "Makefile",
    "Gemfile": "Ruby",
}

DEPENDENCY_MANIFESTS = {
    "package.json": "npm",
    "requirements.txt": "pip",
    "pyproject.toml": "Python",
    "Pipfile": "pipenv",
    "poetry.lock": "Poetry",
    "Cargo.toml": "Cargo",
    "go.mod": "Go modules",
    "composer.json": "Composer",
    "Gemfile": "Bundler",
    "pom.xml": "Maven",
    "build.gradle": "Gradle",
    "build.gradle.kts": "Gradle",
}

TODO_PATTERN = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b[:\s-]*(.*)", re.IGNORECASE)
MAX_TEXT_FILE_BYTES = 5 * 1024 * 1024
MAX_TODOS = 500
MAX_FILE_INDEX = 2000


def detect_language(file_path: Path) -> str | None:
    return LANGUAGES_BY_FILENAME.get(file_path.name) or LANGUAGES_BY_EXTENSION.get(
        file_path.suffix.lower()
    )


def _read_text(file_path: Path) -> str:
    try:
        if file_path.stat().st_size > MAX_TEXT_FILE_BYTES:
            return ""
        return file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _analyze_text(path: Path, relative_path: str) -> tuple[int, list[TodoItem]]:
    text = _read_text(path)
    if not text:
        return 0, []

    lines = text.splitlines()
    todos: list[TodoItem] = []

    for line_number, line in enumerate(lines, start=1):
        match = TODO_PATTERN.search(line)
        if not match:
            continue
        todos.append(
            TodoItem(
                path=relative_path,
                line=line_number,
                tag=match.group(1).upper(),
                text=match.group(2).strip()[:240],
            )
        )

    return len(lines), todos


def _count_manifest_dependencies(file_path: Path, kind: str) -> int | None:
    try:
        if kind == "npm":
            data = json.loads(_read_text(file_path) or "{}")
            sections = (
                "dependencies",
                "devDependencies",
                "peerDependencies",
                "optionalDependencies",
            )
            return sum(len(data.get(section, {})) for section in sections)

        if kind == "pip":
            lines = _read_text(file_path).splitlines()
            return sum(
                1
                for line in lines
                if line.strip()
                and not line.lstrip().startswith(("#", "-r", "--requirement"))
            )

        if kind == "Go modules":
            text = _read_text(file_path)
            block = False
            count = 0
            for raw_line in text.splitlines():
                line = raw_line.strip()
                if line == "require (":
                    block = True
                    continue
                if block and line == ")":
                    block = False
                    continue
                if block and line and not line.startswith("//"):
                    count += 1
                elif line.startswith("require ") and not line.endswith("("):
                    count += 1
            return count

        if kind in {"Python", "Cargo"}:
            try:
                import tomllib
            except ImportError:  # pragma: no cover
                return None

            data = tomllib.loads(_read_text(file_path))
            if kind == "Python":
                project = data.get("project", {})
                count = len(project.get("dependencies", []))
                count += sum(
                    len(values)
                    for values in project.get("optional-dependencies", {}).values()
                )
                poetry = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
                count += len([name for name in poetry if name.lower() != "python"])
                return count

            count = 0
            for section in ("dependencies", "dev-dependencies", "build-dependencies"):
                count += len(data.get(section, {}))
            return count

        if kind == "Composer":
            data = json.loads(_read_text(file_path) or "{}")
            return len(data.get("require", {})) + len(data.get("require-dev", {}))
    except (OSError, ValueError, TypeError):
        return None

    return None


def _run_git(path: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), *args],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _git_insights(path: Path) -> GitInsights | None:
    inside = _run_git(path, "rev-parse", "--is-inside-work-tree")
    if inside != "true":
        return None

    branch = _run_git(path, "branch", "--show-current") or None
    commits_raw = _run_git(path, "rev-list", "--count", "HEAD")
    status = _run_git(path, "status", "--porcelain")
    tracked = _run_git(path, "ls-files")

    return GitInsights(
        branch=branch,
        commits=int(commits_raw) if commits_raw and commits_raw.isdigit() else 0,
        changed_files=len(status.splitlines()) if status else 0,
        tracked_files=len(tracked.splitlines()) if tracked else 0,
    )


def scan_repository(repository_path: str) -> RepositoryAnalysis:
    path = Path(repository_path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"Repository not found: {repository_path}")
    if not path.is_dir():
        raise NotADirectoryError(f"Not a directory: {repository_path}")

    total_files = 0
    total_directories = 0
    total_lines = 0
    total_size_bytes = 0
    languages: Counter[str] = Counter()
    language_lines: Counter[str] = Counter()
    analyzed_files: list[FileAnalysis] = []
    todos: list[TodoItem] = []
    dependency_manifests: list[DependencyManifest] = []
    files_index: list[str] = []
    files_index_truncated = False

    for root, directories, files in os.walk(path):
        directories[:] = sorted(
            directory
            for directory in directories
            if directory not in DEFAULT_IGNORED_DIRECTORIES
        )
        total_directories += len(directories)
        root_path = Path(root)

        for filename in sorted(files):
            file_path = root_path / filename
            relative_path = file_path.relative_to(path).as_posix()
            total_files += 1

            if len(files_index) < MAX_FILE_INDEX:
                files_index.append(relative_path)
            else:
                files_index_truncated = True

            try:
                size_bytes = file_path.stat().st_size
            except OSError:
                size_bytes = 0
            total_size_bytes += size_bytes

            manifest_kind = DEPENDENCY_MANIFESTS.get(filename)
            if manifest_kind:
                dependency_manifests.append(
                    DependencyManifest(
                        path=relative_path,
                        kind=manifest_kind,
                        dependencies=_count_manifest_dependencies(file_path, manifest_kind),
                    )
                )

            language = detect_language(file_path)
            if language is None:
                continue

            line_count, file_todos = _analyze_text(file_path, relative_path)
            languages[language] += 1
            language_lines[language] += line_count
            total_lines += line_count

            if len(todos) < MAX_TODOS:
                remaining = MAX_TODOS - len(todos)
                todos.extend(file_todos[:remaining])

            analyzed_files.append(
                FileAnalysis(
                    path=relative_path,
                    lines=line_count,
                    language=language,
                    size_bytes=size_bytes,
                    todos=len(file_todos),
                )
            )

    largest_files = sorted(
        analyzed_files,
        key=lambda file: (file.lines, file.size_bytes),
        reverse=True,
    )[:12]

    hotspots = [
        Hotspot(
            path=file.path,
            language=file.language,
            lines=file.lines,
            todos=file.todos,
            score=file.lines + (file.todos * 40),
        )
        for file in analyzed_files
        if file.lines or file.todos
    ]
    hotspots.sort(key=lambda item: item.score, reverse=True)

    return RepositoryAnalysis(
        name=path.name,
        path=str(path),
        files=total_files,
        analyzed_files=len(analyzed_files),
        directories=total_directories,
        lines=total_lines,
        size_bytes=total_size_bytes,
        languages=dict(languages.most_common()),
        language_lines=dict(language_lines.most_common()),
        largest_files=largest_files,
        todos=todos,
        dependency_manifests=dependency_manifests,
        git=_git_insights(path),
        hotspots=hotspots[:10],
        files_index=files_index,
        files_index_truncated=files_index_truncated,
    )
