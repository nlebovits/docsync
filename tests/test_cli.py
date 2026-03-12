"""Tests for cli.py."""

from pathlib import Path

from docsync.cli import cmd_add_link, cmd_bootstrap, cmd_check, cmd_init


def test_init_creates_config(tmp_path: Path, monkeypatch):
    """Test that init creates pyproject.toml config section."""
    monkeypatch.chdir(tmp_path)

    # Create pyproject.toml without docsync section
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'test'\n")

    # Create .git directory
    (tmp_path / ".git").mkdir()

    # Mock args
    from argparse import Namespace

    args = Namespace()

    result = cmd_init(args)

    assert result == 0
    content = pyproject.read_text()
    assert "[tool.docsync]" in content
    assert "mode" in content


def test_init_idempotent(tmp_path: Path, monkeypatch):
    """Test that init is idempotent."""
    monkeypatch.chdir(tmp_path)

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'test'\n[tool.docsync]\nmode = 'warn'\n")

    (tmp_path / ".git").mkdir()

    from argparse import Namespace

    args = Namespace()

    result = cmd_init(args)

    assert result == 0
    # Config should not be duplicated
    content = pyproject.read_text()
    assert content.count("[tool.docsync]") == 1


def test_init_creates_hook(tmp_path: Path, monkeypatch):
    """Test that init creates git hook."""
    monkeypatch.chdir(tmp_path)

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'test'\n")

    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    from argparse import Namespace

    args = Namespace()

    cmd_init(args)

    hook_file = git_dir / "hooks" / "pre-commit"
    assert hook_file.exists()
    assert "docsync check" in hook_file.read_text()


def test_check_passes(tmp_path: Path, monkeypatch):
    """Test that check command passes with valid setup."""
    monkeypatch.chdir(tmp_path)

    src = tmp_path / "src"
    src.mkdir()
    code = src / "code.py"
    code.write_text("# docsync: docs/doc.md\n")

    docs = tmp_path / "docs"
    docs.mkdir()
    doc = docs / "doc.md"
    doc.write_text("<!-- docsync: src/code.py -->\n")

    config = tmp_path / "pyproject.toml"
    config.write_text("""
[tool.docsync]
require_links = ["src/**/*.py"]
doc_paths = ["docs/**/*.md"]
""")

    from argparse import Namespace

    args = Namespace(staged_files="src/code.py,docs/doc.md")

    result = cmd_check(args)

    assert result == 0


def test_check_fails(tmp_path: Path, monkeypatch):
    """Test that check command fails with missing docs."""
    monkeypatch.chdir(tmp_path)

    src = tmp_path / "src"
    src.mkdir()
    code = src / "code.py"
    code.write_text("# docsync: docs/doc.md\n")

    docs = tmp_path / "docs"
    docs.mkdir()
    doc = docs / "doc.md"
    doc.write_text("<!-- docsync: src/code.py -->\n")

    config = tmp_path / "pyproject.toml"
    config.write_text("""
[tool.docsync]
require_links = ["src/**/*.py"]
doc_paths = ["docs/**/*.md"]
""")

    from argparse import Namespace

    args = Namespace(staged_files="src/code.py")  # Doc not staged

    result = cmd_check(args)

    assert result == 1


def test_add_link_creates_headers(tmp_path: Path, monkeypatch):
    """Test that add-link creates headers in both files."""
    monkeypatch.chdir(tmp_path)

    src = tmp_path / "src"
    src.mkdir()
    code = src / "code.py"
    code.write_text("def foo(): pass\n")

    docs = tmp_path / "docs"
    docs.mkdir()
    doc = docs / "doc.md"
    doc.write_text("# Documentation\n")

    from argparse import Namespace

    args = Namespace(code_file="src/code.py", doc_file="docs/doc.md")

    result = cmd_add_link(args)

    assert result == 0
    assert "docsync: docs/doc.md" in code.read_text()
    assert "docsync: src/code.py" in doc.read_text()


def test_add_link_appends_to_existing(tmp_path: Path, monkeypatch):
    """Test that add-link appends to existing headers."""
    monkeypatch.chdir(tmp_path)

    src = tmp_path / "src"
    src.mkdir()
    code = src / "code.py"
    code.write_text("# docsync: docs/other.md\ndef foo(): pass\n")

    docs = tmp_path / "docs"
    docs.mkdir()
    doc = docs / "doc.md"
    doc.write_text("# Documentation\n")

    from argparse import Namespace

    args = Namespace(code_file="src/code.py", doc_file="docs/doc.md")

    cmd_add_link(args)

    content = code.read_text()
    assert "docs/other.md" in content
    assert "docs/doc.md" in content


def test_add_link_correct_comment_syntax(tmp_path: Path, monkeypatch):
    """Test that add-link uses correct comment syntax per file type."""
    monkeypatch.chdir(tmp_path)

    # JavaScript file
    js_file = tmp_path / "script.js"
    js_file.write_text("console.log('hello');\n")

    # Markdown file
    md_file = tmp_path / "doc.md"
    md_file.write_text("# Docs\n")

    from argparse import Namespace

    args = Namespace(code_file="script.js", doc_file="doc.md")

    cmd_add_link(args)

    assert "// docsync:" in js_file.read_text()
    assert "<!-- docsync:" in md_file.read_text()


def test_bootstrap_finds_matches(tmp_path: Path, monkeypatch):
    """Test that bootstrap finds matching docs based on heuristics."""
    monkeypatch.chdir(tmp_path)

    src = tmp_path / "src"
    src.mkdir()
    (src / "auth.py").write_text("def auth(): pass\n")

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "authentication.md").write_text("# Auth\n")

    config = tmp_path / "pyproject.toml"
    config.write_text("""
[tool.docsync]
require_links = ["src/**/*.py"]
doc_paths = ["docs/**/*.md"]
""")

    from argparse import Namespace

    args = Namespace(apply=False)

    result = cmd_bootstrap(args)

    assert result == 0


def test_bootstrap_apply(tmp_path: Path, monkeypatch):
    """Test that bootstrap --apply modifies files."""
    monkeypatch.chdir(tmp_path)

    src = tmp_path / "src"
    src.mkdir()
    auth_file = src / "auth.py"
    auth_file.write_text("def auth(): pass\n")

    docs = tmp_path / "docs"
    docs.mkdir()
    doc_file = docs / "auth.md"
    doc_file.write_text("# Auth\n")

    config = tmp_path / "pyproject.toml"
    config.write_text("""
[tool.docsync]
require_links = ["src/**/*.py"]
doc_paths = ["docs/**/*.md"]
""")

    from argparse import Namespace

    args = Namespace(apply=True)

    cmd_bootstrap(args)

    # Files should now have docsync headers
    assert "docsync:" in auth_file.read_text()
    assert "docsync:" in doc_file.read_text()


def test_add_link_already_linked(tmp_path: Path, monkeypatch, capsys):
    """Test that add-link reports when link already exists."""
    monkeypatch.chdir(tmp_path)

    src = tmp_path / "src"
    src.mkdir()
    code = src / "code.py"
    code.write_text("# docsync: docs/doc.md\n")

    docs = tmp_path / "docs"
    docs.mkdir()
    doc = docs / "doc.md"
    doc.write_text("<!-- docsync: src/code.py -->\n")

    from argparse import Namespace

    args = Namespace(code_file="src/code.py", doc_file="docs/doc.md")

    result = cmd_add_link(args)

    assert result == 0
    captured = capsys.readouterr()
    assert "already exists" in captured.out


def test_add_link_missing_file(tmp_path: Path, monkeypatch):
    """Test that add-link fails when file doesn't exist."""
    monkeypatch.chdir(tmp_path)

    from argparse import Namespace

    args = Namespace(code_file="missing.py", doc_file="doc.md")

    result = cmd_add_link(args)

    assert result == 1
