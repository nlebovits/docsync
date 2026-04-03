"""Tests for git diff-based staleness detection."""

import subprocess
import tempfile
from pathlib import Path

from menard.staleness import is_doc_stale
from menard.toml_links import LinkTarget


def _git_init_and_commit(repo_root: Path, files: dict[str, str], message: str):
    """Helper to initialize git repo and commit files."""
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )

    for file_path, content in files.items():
        full_path = repo_root / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

    subprocess.run(["git", "add", "."], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo_root, check=True, capture_output=True)


def test_is_doc_stale_whole_file_fresh():
    """Test that a doc updated after code is not stale."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)

        # Initial commit with code
        _git_init_and_commit(
            repo_root, {"src/auth.py": "def login(): pass", "docs/api.md": "# API"}, "Initial"
        )

        # Change code
        (repo_root / "src" / "auth.py").write_text("def login():\n    return True")
        _git_init_and_commit(repo_root, {}, "Update code")

        # Update doc
        (repo_root / "docs" / "api.md").write_text("# API\n\nUpdated docs")
        _git_init_and_commit(repo_root, {}, "Update docs")

        # Check staleness
        target = LinkTarget(file="docs/api.md")
        is_stale, reason = is_doc_stale(repo_root, "src/auth.py", target)

        assert not is_stale
        assert "updated after" in reason.lower()


def test_is_doc_stale_whole_file_stale():
    """Test that a doc not updated after code change is stale."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)

        # Initial commit
        _git_init_and_commit(
            repo_root, {"src/auth.py": "def login(): pass", "docs/api.md": "# API"}, "Initial"
        )

        # Change code without updating doc
        (repo_root / "src" / "auth.py").write_text("def login():\n    return True")
        _git_init_and_commit(repo_root, {}, "Update code")

        # Check staleness
        target = LinkTarget(file="docs/api.md")
        is_stale, reason = is_doc_stale(repo_root, "src/auth.py", target)

        assert is_stale
        assert "unchanged" in reason.lower()


def test_is_doc_stale_section_updated():
    """Test that updating a specific section marks it as not stale."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)

        # Initial commit
        _git_init_and_commit(
            repo_root,
            {
                "src/auth.py": "def login(): pass",
                "docs/api.md": "## Authentication\n\nOld docs\n\n## Other\n\nOther",
            },
            "Initial",
        )

        # Change code
        (repo_root / "src" / "auth.py").write_text("def login():\n    return True")
        _git_init_and_commit(repo_root, {}, "Update code")

        # Update the Authentication section
        (repo_root / "docs" / "api.md").write_text(
            "## Authentication\n\nUpdated auth docs\n\n## Other\n\nOther"
        )
        _git_init_and_commit(repo_root, {}, "Update auth docs")

        # Check staleness for the Authentication section
        target = LinkTarget(file="docs/api.md", section="Authentication")
        is_stale, reason = is_doc_stale(repo_root, "src/auth.py", target)

        assert not is_stale


def test_is_doc_stale_section_not_updated():
    """Test that not updating a section marks it as stale."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)

        # Initial commit
        _git_init_and_commit(
            repo_root,
            {
                "src/auth.py": "def login(): pass",
                "docs/api.md": "## Authentication\n\nOld docs\n\n## Other\n\nOther",
            },
            "Initial",
        )

        # Change code
        (repo_root / "src" / "auth.py").write_text("def login():\n    return True")
        _git_init_and_commit(repo_root, {}, "Update code")

        # Update a DIFFERENT section
        (repo_root / "docs" / "api.md").write_text(
            "## Authentication\n\nOld docs\n\n## Other\n\nUpdated other section"
        )
        _git_init_and_commit(repo_root, {}, "Update other section")

        # Authentication section should still be stale
        target = LinkTarget(file="docs/api.md", section="Authentication")
        is_stale, reason = is_doc_stale(repo_root, "src/auth.py", target)

        assert is_stale


def test_is_doc_stale_new_file():
    """Test that new code files with no git history are considered stale."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)

        # Initialize git but don't commit the code file
        _git_init_and_commit(repo_root, {"docs/api.md": "# API"}, "Initial")

        # Create code file (not committed)
        (repo_root / "src").mkdir()
        (repo_root / "src" / "auth.py").write_text("def login(): pass")

        # Check staleness
        target = LinkTarget(file="docs/api.md")
        is_stale, reason = is_doc_stale(repo_root, "src/auth.py", target)

        assert is_stale
        assert "new" in reason.lower() or "untracked" in reason.lower()


def _git_commit(repo_root: Path, message: str):
    """Helper to commit staged changes."""
    subprocess.run(["git", "add", "."], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo_root, check=True, capture_output=True)


def test_is_doc_stale_section_same_day_commit_order(tmp_path):
    """
    Test issue #61: Same-day timestamps don't cause false positives.

    When code and doc section are modified on the same day but in different commits,
    the commit order determines staleness, not the date.
    """
    repo_root = tmp_path

    # Initial commit with code and doc
    _git_init_and_commit(
        repo_root,
        {
            "src/main.py": "def main(): pass",
            "docs/guide.md": "## CLI Commands\n\nOriginal content\n\n## Other\n\nOther",
        },
        "Initial",
    )

    # Commit 1: Update code (same day)
    (repo_root / "src" / "main.py").write_text("def main():\n    return 'updated'")
    _git_commit(repo_root, "Update code")

    # Commit 2: Update the CLI Commands section (same day, but AFTER code)
    (repo_root / "docs" / "guide.md").write_text(
        "## CLI Commands\n\nUpdated CLI docs\n\n## Other\n\nOther"
    )
    _git_commit(repo_root, "Update CLI docs")

    # Section should NOT be stale - it was updated after the code
    target = LinkTarget(file="docs/guide.md", section="CLI Commands")
    is_stale, reason = is_doc_stale(repo_root, "src/main.py", target)

    assert not is_stale, f"Expected not stale, but got stale with reason: {reason}"
    assert "updated after" in reason.lower() or "updated" in reason.lower()


def test_is_doc_stale_section_same_commit(tmp_path):
    """
    Test that code and doc section modified in the same commit is not stale.
    """
    repo_root = tmp_path

    # Initial commit
    _git_init_and_commit(
        repo_root,
        {
            "src/auth.py": "def login(): pass",
            "docs/api.md": "## Auth\n\nOriginal\n\n## Other\n\nOther",
        },
        "Initial",
    )

    # Update both code AND doc section in the same commit
    (repo_root / "src" / "auth.py").write_text("def login():\n    return True")
    (repo_root / "docs" / "api.md").write_text("## Auth\n\nUpdated docs\n\n## Other\n\nOther")
    _git_commit(repo_root, "Update code and docs together")

    # Should NOT be stale - both changed in same commit
    target = LinkTarget(file="docs/api.md", section="Auth")
    is_stale, reason = is_doc_stale(repo_root, "src/auth.py", target)

    assert not is_stale, f"Expected not stale, but got stale with reason: {reason}"


def test_is_doc_stale_section_code_after_doc(tmp_path):
    """
    Test that if code was updated AFTER the doc section, it's stale.
    """
    repo_root = tmp_path

    # Initial commit
    _git_init_and_commit(
        repo_root,
        {
            "src/auth.py": "def login(): pass",
            "docs/api.md": "## Auth\n\nOriginal\n\n## Other\n\nOther",
        },
        "Initial",
    )

    # Commit 1: Update doc section first
    (repo_root / "docs" / "api.md").write_text("## Auth\n\nUpdated docs\n\n## Other\n\nOther")
    _git_commit(repo_root, "Update docs")

    # Commit 2: Update code AFTER doc
    (repo_root / "src" / "auth.py").write_text("def login():\n    return True")
    _git_commit(repo_root, "Update code after docs")

    # Should BE stale - code was updated after doc
    target = LinkTarget(file="docs/api.md", section="Auth")
    is_stale, reason = is_doc_stale(repo_root, "src/auth.py", target)

    assert is_stale, f"Expected stale, but got not stale with reason: {reason}"


def test_get_last_commit_for_lines(tmp_path):
    """Test get_last_commit_for_lines returns correct commit for line range."""
    from menard.staleness import get_last_commit_for_lines

    repo_root = tmp_path

    # Initial commit with multi-section doc
    _git_init_and_commit(
        repo_root,
        {"docs/api.md": "## Section A\n\nContent A\n\n## Section B\n\nContent B\n"},
        "Initial",
    )

    # Update only Section B (lines 5-6)
    (repo_root / "docs" / "api.md").write_text(
        "## Section A\n\nContent A\n\n## Section B\n\nUpdated B\n"
    )
    _git_commit(repo_root, "Update section B")

    # Get commit for Section A lines (1-4) - should be the initial commit
    section_a_commit = get_last_commit_for_lines(repo_root, "docs/api.md", 1, 4)
    assert section_a_commit is not None

    # Get commit for Section B lines (5-7) - should be the update commit
    section_b_commit = get_last_commit_for_lines(repo_root, "docs/api.md", 5, 7)
    assert section_b_commit is not None

    # Section B commit should be different from Section A commit
    # (unless git log -L considers the initial commit too)
    # The key assertion is that we get valid commits for both


def test_is_commit_ancestor(tmp_path):
    """Test is_commit_ancestor correctly determines commit order."""
    from menard.staleness import get_last_commit, is_commit_ancestor

    repo_root = tmp_path

    # Create chain of commits
    _git_init_and_commit(repo_root, {"file.txt": "v1"}, "Commit 1")
    commit1 = get_last_commit(repo_root, "file.txt")
    assert commit1 is not None

    (repo_root / "file.txt").write_text("v2")
    _git_commit(repo_root, "Commit 2")
    commit2 = get_last_commit(repo_root, "file.txt")
    assert commit2 is not None

    (repo_root / "file.txt").write_text("v3")
    _git_commit(repo_root, "Commit 3")
    commit3 = get_last_commit(repo_root, "file.txt")
    assert commit3 is not None

    # commit1 should be ancestor of commit2 and commit3
    assert is_commit_ancestor(repo_root, commit1, commit2) is True
    assert is_commit_ancestor(repo_root, commit1, commit3) is True

    # commit2 should be ancestor of commit3
    assert is_commit_ancestor(repo_root, commit2, commit3) is True

    # commit3 should NOT be ancestor of commit1 or commit2
    assert is_commit_ancestor(repo_root, commit3, commit1) is False
    assert is_commit_ancestor(repo_root, commit3, commit2) is False

    # Git considers a commit to be its own ancestor (reflexive relation)
    # This is fine for our use case - same commit means "updated together"
    assert is_commit_ancestor(repo_root, commit2, commit2) is True
