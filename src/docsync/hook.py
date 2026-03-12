"""Pre-commit hook entry point."""

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from docsync.config import DocsyncConfig, load_config
from docsync.graph import build_docsync_graph, get_linked_docs
from docsync.imports import build_import_graph, get_dependents


@dataclass
class HookResult:
    """Result of running the hook."""

    passed: bool
    direct_missing: dict[str, set[str]]  # code_file → set of unstaged doc files
    transitive_missing: dict[
        str, dict[str, set[str]]
    ]  # code_file → {dependent_file → set of unstaged doc files}
    message: str  # formatted output message


def run_hook(repo_root: Path, staged_files: list[str] | None = None) -> HookResult:
    """
    Main hook logic.

    If staged_files is None, reads from git diff --cached --name-only.
    If provided (for testing), uses the given list.

    Returns a HookResult with pass/fail and structured information about
    what's missing.
    """
    # Load config
    config = load_config(repo_root)
    if config is None:
        # Not configured - pass with message
        return HookResult(
            passed=True,
            direct_missing={},
            transitive_missing={},
            message="docsync: not configured (skipping checks)",
        )

    # Get staged files
    if staged_files is None:
        staged_files = _get_staged_files(repo_root)

    staged_set = set(staged_files)

    # Build both graphs
    docsync_graph = build_docsync_graph(repo_root, config)
    import_graph = build_import_graph(repo_root)

    # Track missing docs
    direct_missing: dict[str, set[str]] = {}
    transitive_missing: dict[str, dict[str, set[str]]] = {}

    # Check each staged file
    for staged_file in staged_files:
        # Skip if this is a doc file (we only check code → doc direction)
        if _is_doc_file(staged_file, config):
            continue

        # Skip if not in require_links globs (and not already in docsync_graph)
        if staged_file not in docsync_graph and not _matches_require_links(
            staged_file, config, repo_root
        ):
            continue

        # Check direct doc dependencies
        direct_docs = get_linked_docs(staged_file, docsync_graph, config)
        unstaged_direct = direct_docs - staged_set
        if unstaged_direct:
            direct_missing[staged_file] = unstaged_direct

        # Check transitive dependencies (if enabled)
        if config.transitive_depth > 0:
            dependents = get_dependents(staged_file, import_graph, config.transitive_depth)
            for dependent in dependents:
                dep_docs = get_linked_docs(dependent, docsync_graph, config)
                unstaged_dep_docs = dep_docs - staged_set
                if unstaged_dep_docs:
                    transitive_missing.setdefault(staged_file, {})[dependent] = unstaged_dep_docs

    # Determine pass/fail
    has_missing = bool(direct_missing or transitive_missing)
    passed = not has_missing or config.mode == "warn"

    # Format message
    message = _format_message(config, direct_missing, transitive_missing, passed)

    return HookResult(
        passed=passed,
        direct_missing=direct_missing,
        transitive_missing=transitive_missing,
        message=message,
    )


def _get_staged_files(repo_root: Path) -> list[str]:
    """Get list of staged files from git."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        files = result.stdout.strip().split("\n")
        return [f for f in files if f]  # Filter out empty strings
    except subprocess.CalledProcessError as e:
        print(f"Error getting staged files: {e}", file=sys.stderr)
        return []


def _is_doc_file(file_path: str, config: DocsyncConfig) -> bool:
    """Check if a file matches any doc_paths pattern."""
    from pathlib import PurePath

    from docsync.graph import _match_pattern_parts

    pure_path = PurePath(file_path)

    for pattern in config.doc_paths:
        if "**" in pattern:
            parts = pattern.split("/")
            path_parts = pure_path.parts
            if _match_pattern_parts(path_parts, parts):
                return True
        else:
            if pure_path.match(pattern):
                return True

    return False


def _matches_require_links(file_path: str, config: DocsyncConfig, repo_root: Path) -> bool:
    """Check if a file matches any require_links pattern."""

    from docsync.graph import _match_globs

    file = repo_root / file_path
    return _match_globs(file, config.require_links, repo_root)


def _format_message(
    config: DocsyncConfig,
    direct_missing: dict[str, set[str]],
    transitive_missing: dict[str, dict[str, set[str]]],
    passed: bool,
) -> str:
    """Format the output message."""
    if not direct_missing and not transitive_missing:
        return "docsync: all linked docs are staged. ✓"

    lines = []

    # Header
    if config.mode == "warn":
        lines.append("docsync: commit warning\n")
    else:
        lines.append("docsync: commit blocked\n")

    # Direct doc dependencies
    if direct_missing:
        lines.append("Direct doc dependencies:")
        for code_file, docs in sorted(direct_missing.items()):
            lines.append(f"  {code_file}")
            for doc in sorted(docs):
                lines.append(f"    → {doc} (not staged)")
        lines.append("")

    # Transitive doc dependencies
    if transitive_missing:
        lines.append("Transitive doc dependencies (via import graph):")
        for code_file, dependents in sorted(transitive_missing.items()):
            lines.append(f"  {code_file} changed, which affects:")
            for dependent, docs in sorted(dependents.items()):
                lines.append(f"    {dependent} (imports {code_file})")
                for doc in sorted(docs):
                    lines.append(f"      → {doc} (not staged)")
        lines.append("")

    # Footer
    if not passed:
        lines.append("Update the docs and stage them, or use --no-verify to force.")

    return "\n".join(lines)


def main() -> int:
    """Entry point for pre-commit hook."""
    repo_root = Path.cwd()
    result = run_hook(repo_root)
    print(result.message)
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
