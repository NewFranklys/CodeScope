from app.analyzer.scanner import scan_repository


def test_scan_repository(tmp_path):
    source = tmp_path / "src"
    source.mkdir()

    python_file = source / "main.py"
    python_file.write_text(
        "print('hello')\nprint('world')\n",
        encoding="utf-8",
    )

    readme = tmp_path / "README.md"
    readme.write_text(
        "# Test project\n",
        encoding="utf-8",
    )

    node_modules = tmp_path / "node_modules"
    node_modules.mkdir()

    ignored_file = node_modules / "library.js"
    ignored_file.write_text(
        "console.log('ignore me');\n",
        encoding="utf-8",
    )

    result = scan_repository(str(tmp_path))

    assert result.files == 2
    assert result.lines == 3
    assert result.languages == {
        "Python": 1,
        "Markdown": 1,
    }