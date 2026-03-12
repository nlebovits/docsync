"""Tests for coverage.py."""

from pathlib import Path
from unittest.mock import patch

import pytest

from docsync.coverage import generate_coverage


def test_coverage_percentage_calculation(tmp_path: Path):
    """Test coverage percentage calculation."""
    src = tmp_path / "src"
    src.mkdir()

    # Create 3 files: 2 with links, 1 without
    (src / "a.py").write_text("# docsync: docs/a.md\n")
    (src / "b.py").write_text("# docsync: docs/b.md\n")
    (src / "c.py").write_text("# No link\n")

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("<!-- docsync: src/a.py -->\n")
    (docs / "b.md").write_text("<!-- docsync: src/b.py -->\n")

    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("""
[tool.docsync]
require_links = ["src/**/*.py"]
doc_paths = ["docs/**/*.md"]
""")

    report = generate_coverage(tmp_path)

    assert report.total_required == 3
    assert report.linked == 2
    assert report.coverage_pct == pytest.approx(66.7, abs=0.1)


def test_orphaned_doc_detection(tmp_path: Path):
    """Test detection of docs linking to non-existent code."""
    docs = tmp_path / "docs"
    docs.mkdir()

    # Doc linking to non-existent file
    stale_doc = docs / "stale.md"
    stale_doc.write_text("<!-- docsync: src/missing.py -->\n")

    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("""
[tool.docsync]
doc_paths = ["docs/**/*.md"]
""")

    report = generate_coverage(tmp_path)

    assert len(report.orphaned_docs) == 1
    assert "docs/stale.md → src/missing.py" in report.orphaned_docs


def test_orphaned_code_detection(tmp_path: Path):
    """Test detection of required code files with no doc links."""
    src = tmp_path / "src"
    src.mkdir()

    # Code with link
    (src / "linked.py").write_text("# docsync: docs/linked.md\n")

    # Code without link
    (src / "orphan.py").write_text("# No link\n")

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "linked.md").write_text("<!-- docsync: src/linked.py -->\n")

    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("""
[tool.docsync]
require_links = ["src/**/*.py"]
doc_paths = ["docs/**/*.md"]
""")

    report = generate_coverage(tmp_path)

    assert "src/orphan.py" in report.orphaned_code


def test_asymmetric_link_detection(tmp_path: Path):
    """Test detection of asymmetric links."""
    src = tmp_path / "src"
    src.mkdir()
    docs = tmp_path / "docs"
    docs.mkdir()

    # Symmetric link: both sides link to each other
    (src / "symmetric.py").write_text("# docsync: docs/symmetric.md\n")
    (docs / "symmetric.md").write_text("<!-- docsync: src/symmetric.py -->\n")

    # Asymmetric link: only code links to doc, doc doesn't link back
    (src / "asymmetric.py").write_text("# docsync: docs/asymmetric.md\n")
    (docs / "asymmetric.md").write_text("# No link back\n")

    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("""
[tool.docsync]
enforce_symmetry = true
require_links = ["src/**/*.py"]
doc_paths = ["docs/**/*.md"]
""")

    report = generate_coverage(tmp_path)

    # Should detect the asymmetric link
    assert len(report.asymmetric_links) == 1
    file_a, file_b, direction = report.asymmetric_links[0]
    assert file_a == "src/asymmetric.py"
    assert file_b == "docs/asymmetric.md"
    assert direction == "docs/asymmetric.md → src/asymmetric.py"


def test_asymmetric_disabled(tmp_path: Path):
    """Test that asymmetric detection is disabled when enforce_symmetry=false."""
    src = tmp_path / "src"
    src.mkdir()
    docs = tmp_path / "docs"
    docs.mkdir()

    # Asymmetric link
    (src / "asymmetric.py").write_text("# docsync: docs/asymmetric.md\n")
    (docs / "asymmetric.md").write_text("# No link back\n")

    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("""
[tool.docsync]
enforce_symmetry = false
require_links = ["src/**/*.py"]
doc_paths = ["docs/**/*.md"]
""")

    report = generate_coverage(tmp_path)

    # Should not report asymmetric links
    assert report.asymmetric_links == []


def test_stale_docs(tmp_path: Path):
    """Test staleness detection with mocked git timestamps."""
    src = tmp_path / "src"
    src.mkdir()
    docs = tmp_path / "docs"
    docs.mkdir()

    (src / "code.py").write_text("# docsync: docs/doc.md\n")
    (docs / "doc.md").write_text("<!-- docsync: src/code.py -->\n")

    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("""
[tool.docsync]
require_links = ["src/**/*.py"]
doc_paths = ["docs/**/*.md"]
""")

    # Mock git timestamps: code.py modified at time 1000, doc.md modified at time 500
    def mock_get_last_commit_time(repo_root, file_path):
        if file_path == "src/code.py":
            return 1000
        elif file_path == "docs/doc.md":
            return 500
        return None

    with patch("docsync.coverage._get_last_commit_time", side_effect=mock_get_last_commit_time):
        report = generate_coverage(tmp_path)

    # doc.md should be stale because code.py is newer
    assert len(report.stale_docs) == 1
    # stale_docs is now (doc, code, doc_ts, code_ts, days_stale)
    doc, code, doc_ts, code_ts, days_stale = report.stale_docs[0]
    assert doc == "docs/doc.md"
    assert code == "src/code.py"
    assert doc_ts == 500
    assert code_ts == 1000
    assert days_stale == (1000 - 500) // 86400  # 0 days (less than 1 day difference)


def test_stale_docs_no_git_history(tmp_path: Path):
    """Test that files with no git history are not flagged as stale."""
    src = tmp_path / "src"
    src.mkdir()
    docs = tmp_path / "docs"
    docs.mkdir()

    (src / "code.py").write_text("# docsync: docs/doc.md\n")
    (docs / "doc.md").write_text("<!-- docsync: src/code.py -->\n")

    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("""
[tool.docsync]
require_links = ["src/**/*.py"]
doc_paths = ["docs/**/*.md"]
""")

    # Mock git timestamps: return None (no git history)
    with patch("docsync.coverage._get_last_commit_time", return_value=None):
        report = generate_coverage(tmp_path)

    # Should not flag anything as stale
    assert report.stale_docs == []


def test_markdown_output_well_formed(tmp_path: Path):
    """Test that markdown output is well-formed."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "code.py").write_text("# docsync: docs/doc.md\n")

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "doc.md").write_text("<!-- docsync: src/code.py -->\n")

    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("""
[tool.docsync]
require_links = ["src/**/*.py"]
doc_paths = ["docs/**/*.md"]
""")

    report = generate_coverage(tmp_path)

    # Check markdown structure
    assert "## docsync Coverage Report" in report.markdown
    assert "| Metric | Value |" in report.markdown
    assert "| Required files |" in report.markdown
    assert "| Coverage |" in report.markdown


def test_coverage_100_percent(tmp_path: Path):
    """Test 100% coverage scenario."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "code.py").write_text("# docsync: docs/doc.md\n")

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "doc.md").write_text("<!-- docsync: src/code.py -->\n")

    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("""
[tool.docsync]
require_links = ["src/**/*.py"]
doc_paths = ["docs/**/*.md"]
""")

    report = generate_coverage(tmp_path)

    assert report.coverage_pct == 100.0
    assert report.orphaned_code == []


def test_coverage_no_required_files(tmp_path: Path):
    """Test coverage when no files match require_links."""
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("""
[tool.docsync]
require_links = ["src/**/*.py"]
doc_paths = ["docs/**/*.md"]
""")

    report = generate_coverage(tmp_path)

    # Should handle gracefully
    assert report.total_required == 0
    assert report.coverage_pct == 100.0
