"""Docsync link parsing and graph construction."""

import re
from pathlib import Path, PurePath

from docsync.config import DocsyncConfig


def parse_links(file_path: Path, repo_root: Path) -> list[str]:
    """Parse docsync links from a file's header. Returns list of relative paths."""
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = [f.readline() for _ in range(10)]
    except Exception:
        return []

    # Regex patterns for different comment styles
    patterns = [
        r"^#\s*docsync:\s*(.+)$",  # Python/Ruby/Shell
        r"^//\s*docsync:\s*(.+)$",  # JavaScript/C/Go/Rust
        r"^/\*\s*docsync:\s*(.+?)\s*\*/$",  # C-style block (single line)
        r"^<!--\s*docsync:\s*(.+?)\s*-->$",  # HTML/Markdown
        r"^--\s*docsync:\s*(.+)$",  # SQL/Lua
    ]

    found_links = []
    for line in lines:
        line = line.strip()
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                # Extract the paths part
                paths_str = match.group(1)
                # Split by comma and strip whitespace
                paths = [p.strip() for p in paths_str.split(",")]
                # Filter out empty strings
                paths = [p for p in paths if p]
                found_links.extend(paths)

    # If we found multiple docsync headers, that's an error
    # Count how many lines matched
    match_count = sum(1 for line in lines if any(re.match(pat, line.strip()) for pat in patterns))
    if match_count > 1:
        raise ValueError(f"Multiple docsync headers found in {file_path}")

    return found_links


def _match_globs(file_path: Path, patterns: list[str], base_path: Path) -> bool:
    """Check if file_path matches any of the glob patterns."""
    if not patterns:
        return False

    rel_path = file_path.relative_to(base_path)
    # Convert to PurePath for matching to handle ** correctly
    pure_path = PurePath(rel_path)

    for pattern in patterns:
        # PurePath.match() works from the right, so we need to handle ** patterns specially
        # For patterns with **, we'll use a simple implementation
        if "**" in pattern:
            # Convert pattern to regex-like matching
            # src/**/*.py should match src/foo.py, src/a/foo.py, src/a/b/foo.py, etc.
            parts = pattern.split("/")
            path_parts = pure_path.parts

            # Try to match the pattern parts against path parts
            if _match_pattern_parts(path_parts, parts):
                return True
        else:
            # For simple patterns without **, use match() which works fine
            if pure_path.match(pattern):
                return True
    return False


def _match_pattern_parts(path_parts: tuple[str, ...], pattern_parts: list[str]) -> bool:
    """Match path parts against pattern parts, handling ** wildcards."""
    if not pattern_parts:
        return not path_parts

    if not path_parts:
        return all(p == "**" for p in pattern_parts)

    # If first pattern is **, it can match 0 or more path parts
    if pattern_parts[0] == "**":
        # ** can match nothing (skip it)
        if _match_pattern_parts(path_parts, pattern_parts[1:]):
            return True
        # ** can match one or more parts
        return _match_pattern_parts(path_parts[1:], pattern_parts)

    # If first pattern is *, it matches any single part
    if pattern_parts[0] == "*":
        return _match_pattern_parts(path_parts[1:], pattern_parts[1:])

    # If first pattern has *, use fnmatch-style matching
    if "*" in pattern_parts[0] or "?" in pattern_parts[0]:
        import fnmatch

        if fnmatch.fnmatch(path_parts[0], pattern_parts[0]):
            return _match_pattern_parts(path_parts[1:], pattern_parts[1:])
        return False

    # Literal match
    if path_parts[0] == pattern_parts[0]:
        return _match_pattern_parts(path_parts[1:], pattern_parts[1:])

    return False


def build_docsync_graph(repo_root: Path, config: DocsyncConfig) -> dict[str, set[str]]:
    """
    Scan all files matching require_links and doc_paths globs.
    Return a dict mapping each file (relative path) to the set of files it links to.
    Links are bidirectional.
    """
    graph: dict[str, set[str]] = {}

    # Collect all files to scan
    files_to_scan: set[Path] = set()

    # Scan all files in repo_root recursively
    for file_path in repo_root.rglob("*"):
        if not file_path.is_file():
            continue

        # Skip if matches exempt patterns
        if _match_globs(file_path, config.exempt, repo_root):
            continue

        # Include if matches require_links or doc_paths
        if _match_globs(file_path, config.require_links + config.doc_paths, repo_root):
            files_to_scan.add(file_path)

    # Parse links from each file
    for file_path in files_to_scan:
        try:
            links = parse_links(file_path, repo_root)
        except ValueError as e:
            # Re-raise errors about multiple headers
            raise e

        if not links:
            continue

        rel_path = str(file_path.relative_to(repo_root))

        # Add links in both directions
        for link in links:
            # Normalize the link path
            link_abs = (repo_root / link).resolve()
            try:
                link_rel = str(link_abs.relative_to(repo_root.resolve()))
            except ValueError:
                # Link is outside repo, skip it
                continue

            # Add bidirectional links
            graph.setdefault(rel_path, set()).add(link_rel)
            graph.setdefault(link_rel, set()).add(rel_path)

    return graph


def get_linked_docs(file_path: str, graph: dict[str, set[str]], config: DocsyncConfig) -> set[str]:
    """
    Given a code file path, return all doc files linked to it (directly).
    A 'doc file' is any file matching the doc_paths globs.
    """
    linked = graph.get(file_path, set())

    # Filter to only doc files
    doc_files = set()
    for linked_file in linked:
        # Check if this file matches any doc_paths pattern using our custom matcher
        pure_path = PurePath(linked_file)

        for pattern in config.doc_paths:
            # Use our custom glob matcher for ** patterns
            if "**" in pattern:
                parts = pattern.split("/")
                path_parts = pure_path.parts
                if _match_pattern_parts(path_parts, parts):
                    doc_files.add(linked_file)
                    break
            else:
                # Simple patterns without ** can use match()
                if pure_path.match(pattern):
                    doc_files.add(linked_file)
                    break

    return doc_files
