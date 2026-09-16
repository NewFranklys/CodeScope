from pathlib import Path


def count_files(repository_path: str) -> int:
    path = Path(repository_path)

    if not path.exists():
        raise FileNotFoundError(f"Repository not found: {repository_path}")

    if not path.is_dir():
        raise NotADirectoryError(f"Not a directory: {repository_path}")

    total_files = 0

    for item in path.rglob("*"):
        if item.is_file():
            total_files += 1

    return total_files


if __name__ == "__main__":
    repository = input("Repository path: ")

    total = count_files(repository)

    print(f"Files found: {total}")