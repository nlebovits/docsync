"""Tests for hook.py."""

from pathlib import Path

from docsync.hook import run_hook


def test_hook_happy_path(tmp_path: Path):
    """Test that hook passes when code and linked doc are both staged."""
    # Create files
    src = tmp_path / "src"
    src.mkdir()
    code = src / "auth.py"
    code.write_text("# docsync: docs/auth.md\ndef foo(): pass\n")

    docs = tmp_path / "docs"
    docs.mkdir()
    doc = docs / "auth.md"
    doc.write_text("<!-- docsync: src/auth.py -->\n# Auth\n")

    # Create config
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("""
[tool.docsync]
require_links = ["src/**/*.py"]
doc_paths = ["docs/**/*.md"]
""")

    # Both files staged
    staged = ["src/auth.py", "docs/auth.md"]

    result = run_hook(tmp_path, staged_files=staged)

    assert result.passed
    assert result.direct_missing == {}
    assert result.transitive_missing == {}
    assert "✓" in result.message


def test_hook_direct_block(tmp_path: Path):
    """Test that hook fails when code is staged but linked doc is not."""
    # Create files
    src = tmp_path / "src"
    src.mkdir()
    code = src / "auth.py"
    code.write_text("# docsync: docs/auth.md\ndef foo(): pass\n")

    docs = tmp_path / "docs"
    docs.mkdir()
    doc = docs / "auth.md"
    doc.write_text("<!-- docsync: src/auth.py -->\n# Auth\n")

    # Create config
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("""
[tool.docsync]
require_links = ["src/**/*.py"]
doc_paths = ["docs/**/*.md"]
""")

    # Only code file staged
    staged = ["src/auth.py"]

    result = run_hook(tmp_path, staged_files=staged)

    assert not result.passed
    assert "src/auth.py" in result.direct_missing
    assert "docs/auth.md" in result.direct_missing["src/auth.py"]
    assert "commit blocked" in result.message
    assert "docs/auth.md (not staged)" in result.message


def test_hook_multiple_code_files(tmp_path: Path):
    """Test multiple code files with missing docs."""
    src = tmp_path / "src"
    src.mkdir()

    code1 = src / "auth.py"
    code1.write_text("# docsync: docs/auth.md\n")

    code2 = src / "users.py"
    code2.write_text("# docsync: docs/users.md\n")

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "auth.md").write_text("<!-- docsync: src/auth.py -->\n")
    (docs / "users.md").write_text("<!-- docsync: src/users.py -->\n")

    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("""
[tool.docsync]
require_links = ["src/**/*.py"]
doc_paths = ["docs/**/*.md"]
""")

    # Both code files staged, no docs
    staged = ["src/auth.py", "src/users.py"]

    result = run_hook(tmp_path, staged_files=staged)

    assert not result.passed
    assert "src/auth.py" in result.direct_missing
    assert "src/users.py" in result.direct_missing
    assert "docs/auth.md" in result.direct_missing["src/auth.py"]
    assert "docs/users.md" in result.direct_missing["src/users.py"]


def test_hook_transitive_depth_1(tmp_path: Path):
    """Test transitive dependencies at depth 1."""
    src = tmp_path / "src"
    src.mkdir()

    # Create dependency chain: permissions.py ← auth.py
    permissions = src / "permissions.py"
    permissions.write_text("# docsync: docs/permissions.md\ndef check(): pass\n")

    auth = src / "auth.py"
    auth.write_text("# docsync: docs/auth.md\nfrom permissions import check\ndef auth(): pass\n")

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "permissions.md").write_text("<!-- docsync: src/permissions.py -->\n")
    (docs / "auth.md").write_text("<!-- docsync: src/auth.py -->\n")

    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("""
[tool.docsync]
transitive_depth = 1
require_links = ["src/**/*.py"]
doc_paths = ["docs/**/*.md"]
""")

    # Only permissions.py staged (not its doc, not auth.py's doc)
    staged = ["src/permissions.py"]

    result = run_hook(tmp_path, staged_files=staged)

    assert not result.passed
    # Direct: permissions.md not staged
    assert "src/permissions.py" in result.direct_missing
    assert "docs/permissions.md" in result.direct_missing["src/permissions.py"]
    # Transitive: auth.py depends on permissions.py, and auth.md not staged
    assert "src/permissions.py" in result.transitive_missing
    assert "src/auth.py" in result.transitive_missing["src/permissions.py"]
    assert "docs/auth.md" in result.transitive_missing["src/permissions.py"]["src/auth.py"]


def test_hook_transitive_depth_0(tmp_path: Path):
    """Test that transitive_depth=0 disables transitive checking."""
    src = tmp_path / "src"
    src.mkdir()

    permissions = src / "permissions.py"
    permissions.write_text("# docsync: docs/permissions.md\ndef check(): pass\n")

    auth = src / "auth.py"
    auth.write_text("# docsync: docs/auth.md\nfrom permissions import check\n")

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "permissions.md").write_text("<!-- docsync: src/permissions.py -->\n")
    (docs / "auth.md").write_text("<!-- docsync: src/auth.py -->\n")

    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("""
[tool.docsync]
transitive_depth = 0
require_links = ["src/**/*.py"]
doc_paths = ["docs/**/*.md"]
""")

    staged = ["src/permissions.py"]

    result = run_hook(tmp_path, staged_files=staged)

    # Should only flag direct missing, not transitive
    assert not result.passed
    assert "src/permissions.py" in result.direct_missing
    assert result.transitive_missing == {}


def test_hook_transitive_depth_2(tmp_path: Path):
    """Test transitive dependencies at depth 2."""
    src = tmp_path / "src"
    src.mkdir()

    # Chain: core.py ← api.py ← routes.py
    core = src / "core.py"
    core.write_text("# docsync: docs/core.md\nx = 1\n")

    api = src / "api.py"
    api.write_text("# docsync: docs/api.md\nfrom core import x\n")

    routes = src / "routes.py"
    routes.write_text("# docsync: docs/routes.md\nfrom api import x\n")

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "core.md").write_text("<!-- docsync: src/core.py -->\n")
    (docs / "api.md").write_text("<!-- docsync: src/api.py -->\n")
    (docs / "routes.md").write_text("<!-- docsync: src/routes.py -->\n")

    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("""
[tool.docsync]
transitive_depth = 2
require_links = ["src/**/*.py"]
doc_paths = ["docs/**/*.md"]
""")

    # Only core.py staged
    staged = ["src/core.py"]

    result = run_hook(tmp_path, staged_files=staged)

    assert not result.passed
    # Transitive should include both api.py (depth 1) and routes.py (depth 2)
    assert "src/core.py" in result.transitive_missing
    assert "src/api.py" in result.transitive_missing["src/core.py"]
    assert "src/routes.py" in result.transitive_missing["src/core.py"]


def test_hook_warn_mode(tmp_path: Path):
    """Test that warn mode passes even with missing docs."""
    src = tmp_path / "src"
    src.mkdir()
    code = src / "auth.py"
    code.write_text("# docsync: docs/auth.md\n")

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "auth.md").write_text("<!-- docsync: src/auth.py -->\n")

    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("""
[tool.docsync]
mode = "warn"
require_links = ["src/**/*.py"]
doc_paths = ["docs/**/*.md"]
""")

    staged = ["src/auth.py"]

    result = run_hook(tmp_path, staged_files=staged)

    # Should pass but still list missing docs
    assert result.passed
    assert "src/auth.py" in result.direct_missing
    assert "commit warning" in result.message


def test_hook_doc_staged_without_code(tmp_path: Path):
    """Test that doc file staged without code doesn't cause error."""
    src = tmp_path / "src"
    src.mkdir()
    code = src / "auth.py"
    code.write_text("# docsync: docs/auth.md\n")

    docs = tmp_path / "docs"
    docs.mkdir()
    doc = docs / "auth.md"
    doc.write_text("<!-- docsync: src/auth.py -->\n")

    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("""
[tool.docsync]
require_links = ["src/**/*.py"]
doc_paths = ["docs/**/*.md"]
""")

    # Only doc staged
    staged = ["docs/auth.md"]

    result = run_hook(tmp_path, staged_files=staged)

    # Should pass (we only check code→doc direction)
    assert result.passed


def test_hook_file_not_in_require_links(tmp_path: Path):
    """Test that files not matching require_links are not checked."""
    src = tmp_path / "src"
    src.mkdir()

    # This file doesn't match require_links but has a docsync header
    other = src / "other.txt"
    other.write_text("# docsync: docs/other.md\n")

    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("""
[tool.docsync]
require_links = ["src/**/*.py"]
doc_paths = ["docs/**/*.md"]
""")

    staged = ["src/other.txt"]

    result = run_hook(tmp_path, staged_files=staged)

    # Should pass (other.txt not in require_links)
    assert result.passed


def test_hook_exempt_file(tmp_path: Path):
    """Test that exempt files are not checked."""
    src = tmp_path / "src"
    src.mkdir()

    test_file = src / "test_auth.py"
    test_file.write_text("# docsync: docs/testing.md\n")

    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("""
[tool.docsync]
require_links = ["src/**/*.py"]
exempt = ["**/test_*.py"]
doc_paths = ["docs/**/*.md"]
""")

    staged = ["src/test_auth.py"]

    result = run_hook(tmp_path, staged_files=staged)

    # Should pass (test files are exempt)
    assert result.passed


def test_hook_no_staged_files(tmp_path: Path):
    """Test hook with no staged files."""
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("""
[tool.docsync]
require_links = ["src/**/*.py"]
""")

    result = run_hook(tmp_path, staged_files=[])

    assert result.passed
    assert "✓" in result.message
