import shutil
import subprocess

import pytest

from app.analyzer.scanner import scan_repository


def test_scan_repository_collects_v1_metrics(tmp_path):
    source = tmp_path / "src"
    source.mkdir()

    python_file = source / "main.py"
    python_file.write_text(
        "# TODO: split this function\nprint('hello')\nprint('world')\n",
        encoding="utf-8",
    )

    readme = tmp_path / "README.md"
    readme.write_text("# Test project\n", encoding="utf-8")

    package_json = tmp_path / "package.json"
    package_json.write_text(
        '{"dependencies":{"react":"1"},"devDependencies":{"vite":"1"}}',
        encoding="utf-8",
    )

    node_modules = tmp_path / "node_modules"
    node_modules.mkdir()
    (node_modules / "library.js").write_text(
        "console.log('ignore me');\n",
        encoding="utf-8",
    )

    result = scan_repository(str(tmp_path))

    assert result.files == 3
    assert result.analyzed_files == 3
    assert result.lines == 5
    assert result.languages == {"Python": 1, "Markdown": 1, "JSON": 1}
    assert result.language_lines["Python"] == 3
    assert result.todos[0].tag == "TODO"
    assert result.todos[0].path == "src/main.py"
    assert result.dependency_manifests[0].kind == "npm"
    assert result.dependency_manifests[0].dependencies == 2
    assert "src/main.py" in result.files_index
    assert result.hotspots[0].path == "src/main.py"


def test_repository_not_found():
    with pytest.raises(FileNotFoundError):
        scan_repository("Z:/this-path-should-not-exist/codescope")


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_git_insights(tmp_path):
    subprocess.run(
        ["git", "init", "-b", "main", str(tmp_path)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "CodeScope Test"],
        check=True,
    )
    (tmp_path / "main.py").write_text("print('hello')\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "main.py"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "initial"],
        check=True,
        capture_output=True,
    )

    result = scan_repository(str(tmp_path))

    assert result.git is not None
    assert result.git.branch == "main"
    assert result.git.commits == 1
    assert result.git.tracked_files == 1
    assert result.git.changed_files == 0
