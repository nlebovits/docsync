"""Tests for graph.py."""

from pathlib import Path

import pytest

from docsync.config import DocsyncConfig
from docsync.graph import build_docsync_graph, get_linked_docs, parse_links


def test_parse_links_python_style(tmp_path: Path):
    """Test parsing Python-style comments."""
    file_path = tmp_path / "test.py"
    file_path.write_text("""# docsync: docs/guide.md, docs/api.md
def foo():
    pass
""")
    links = parse_links(file_path, tmp_path)
    assert links == ["docs/guide.md", "docs/api.md"]


def test_parse_links_javascript_style(tmp_path: Path):
    """Test parsing JavaScript-style comments."""
    file_path = tmp_path / "test.js"
    file_path.write_text("""// docsync: docs/frontend.md
function bar() {}
""")
    links = parse_links(file_path, tmp_path)
    assert links == ["docs/frontend.md"]


def test_parse_links_c_block_style(tmp_path: Path):
    """Test parsing C-style block comments."""
    file_path = tmp_path / "test.c"
    file_path.write_text("""/* docsync: docs/native.md */
int main() {}
""")
    links = parse_links(file_path, tmp_path)
    assert links == ["docs/native.md"]


def test_parse_links_markdown_style(tmp_path: Path):
    """Test parsing HTML/Markdown comments."""
    file_path = tmp_path / "test.md"
    file_path.write_text("""<!-- docsync: src/api.py, src/models.py -->
# Documentation
""")
    links = parse_links(file_path, tmp_path)
    assert links == ["src/api.py", "src/models.py"]


def test_parse_links_sql_style(tmp_path: Path):
    """Test parsing SQL-style comments."""
    file_path = tmp_path / "test.sql"
    file_path.write_text("""-- docsync: docs/schema.md
CREATE TABLE users (id INT);
""")
    links = parse_links(file_path, tmp_path)
    assert links == ["docs/schema.md"]


def test_parse_links_not_in_first_10_lines(tmp_path: Path):
    """Test that docsync header outside first 10 lines is ignored."""
    file_path = tmp_path / "test.py"
    # 10 lines of code, then the docsync header
    content = "\n".join(["# comment"] * 10) + "\n# docsync: docs/late.md\n"
    file_path.write_text(content)
    links = parse_links(file_path, tmp_path)
    assert links == []


def test_parse_links_whitespace_variations(tmp_path: Path):
    """Test various whitespace in path lists."""
    file_path = tmp_path / "test.py"
    file_path.write_text("""# docsync:  docs/a.md  ,  docs/b.md,docs/c.md
""")
    links = parse_links(file_path, tmp_path)
    assert links == ["docs/a.md", "docs/b.md", "docs/c.md"]


def test_parse_links_multiple_headers_raises_error(tmp_path: Path):
    """Test that multiple docsync headers raise an error."""
    file_path = tmp_path / "test.py"
    file_path.write_text("""# docsync: docs/a.md
# docsync: docs/b.md
def foo():
    pass
""")
    with pytest.raises(ValueError, match="Multiple docsync headers"):
        parse_links(file_path, tmp_path)


def test_parse_links_file_not_found(tmp_path: Path):
    """Test that missing file returns empty list."""
    file_path = tmp_path / "nonexistent.py"
    links = parse_links(file_path, tmp_path)
    assert links == []


def test_build_docsync_graph_bidirectional(tmp_path: Path):
    """Test that graph is bidirectional."""
    # Create files
    code_file = tmp_path / "src" / "auth.py"
    code_file.parent.mkdir(parents=True)
    code_file.write_text("# docsync: docs/auth.md\n")

    doc_file = tmp_path / "docs" / "auth.md"
    doc_file.parent.mkdir(parents=True)
    doc_file.write_text("<!-- docsync: src/auth.py -->\n")

    config = DocsyncConfig(require_links=["src/**/*.py"], doc_paths=["docs/**/*.md"])

    graph = build_docsync_graph(tmp_path, config)

    # Both directions should exist
    assert "src/auth.py" in graph
    assert "docs/auth.md" in graph["src/auth.py"]
    assert "docs/auth.md" in graph
    assert "src/auth.py" in graph["docs/auth.md"]


def test_build_docsync_graph_exempt_files(tmp_path: Path):
    """Test that exempt files are skipped."""
    # Create files
    code_file = tmp_path / "src" / "auth.py"
    code_file.parent.mkdir(parents=True)
    code_file.write_text("# docsync: docs/auth.md\n")

    test_file = tmp_path / "src" / "test_auth.py"
    test_file.write_text("# docsync: docs/testing.md\n")

    config = DocsyncConfig(require_links=["src/**/*.py"], exempt=["**/test_*.py"])

    graph = build_docsync_graph(tmp_path, config)

    # auth.py should be in graph
    assert "src/auth.py" in graph
    # test_auth.py should be skipped
    assert "src/test_auth.py" not in graph


def test_build_docsync_graph_multiple_links(tmp_path: Path):
    """Test file linking to multiple docs."""
    code_file = tmp_path / "src" / "api.py"
    code_file.parent.mkdir(parents=True)
    code_file.write_text("# docsync: docs/api.md, docs/guide.md\n")

    config = DocsyncConfig(require_links=["src/**/*.py"])
    graph = build_docsync_graph(tmp_path, config)

    assert "src/api.py" in graph
    assert "docs/api.md" in graph["src/api.py"]
    assert "docs/guide.md" in graph["src/api.py"]


def test_get_linked_docs_filters_to_doc_files_only(tmp_path: Path):
    """Test that get_linked_docs returns only doc files."""
    # Create files where code links to both code and docs
    file1 = tmp_path / "src" / "a.py"
    file1.parent.mkdir(parents=True)
    file1.write_text("# docsync: docs/guide.md, src/b.py\n")

    file2 = tmp_path / "src" / "b.py"
    file2.write_text("# docsync: src/a.py\n")

    doc_file = tmp_path / "docs" / "guide.md"
    doc_file.parent.mkdir(parents=True)
    doc_file.write_text("<!-- docsync: src/a.py -->\n")

    config = DocsyncConfig(require_links=["src/**/*.py"], doc_paths=["docs/**/*.md"])

    graph = build_docsync_graph(tmp_path, config)

    # src/a.py links to both src/b.py and docs/guide.md
    # But get_linked_docs should only return docs/guide.md
    linked_docs = get_linked_docs("src/a.py", graph, config)
    assert linked_docs == {"docs/guide.md"}
    assert "src/b.py" not in linked_docs


def test_get_linked_docs_no_links(tmp_path: Path):
    """Test get_linked_docs for file with no links."""
    config = DocsyncConfig()
    graph = {}
    linked_docs = get_linked_docs("src/orphan.py", graph, config)
    assert linked_docs == set()


def test_build_docsync_graph_link_outside_repo(tmp_path: Path):
    """Test that links outside repo are ignored."""
    code_file = tmp_path / "src" / "api.py"
    code_file.parent.mkdir(parents=True)
    # Link to absolute path outside repo
    code_file.write_text("# docsync: /tmp/external.md\n")

    config = DocsyncConfig(require_links=["src/**/*.py"])
    graph = build_docsync_graph(tmp_path, config)

    # The external link should be ignored
    assert "src/api.py" not in graph or "/tmp/external.md" not in graph["src/api.py"]
