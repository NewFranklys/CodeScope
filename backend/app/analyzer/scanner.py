import os
from pathlib import Path

from app.analyzer.ignores import DEFAULT_IGNORED_DIRECTORIES


def count_files(repository_path: str) -> int:
    path = Path(repository_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Repository not found: {repository_path}"
        )

    if not path.is_dir():
        raise NotADirectoryError(
            f"Not a directory: {repository_path}"
        )

    total_files = 0

    for root, directories, files in os.walk(path):
        directories[:] = [
            directory
            for directory in directories
            if directory not in DEFAULT_IGNORED_DIRECTORIES
        ]

        total_files += len(files)

    return total_files


if __name__ == "__main__":
    repository = input("Repository path: ").strip()

    total = count_files(repository)

    print(f"Files found: {total}")