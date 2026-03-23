"""Semantic duplicate detection for documentation sections."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from menard.sections import get_section_content, list_sections, parse_markdown_section

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


@dataclass
class DuplicatePair:
    """A pair of semantically similar documentation sections."""

    source: str
    target: str
    similarity: float
    source_lines: tuple[int, int]
    target_lines: tuple[int, int]


def cosine_similarity(vec1: NDArray[np.floating], vec2: NDArray[np.floating]) -> float:
    """Compute cosine similarity between two vectors.

    Assumes vectors are already normalized (as fastembed outputs are).
    """
    import numpy as np

    return float(np.dot(vec1, vec2))


def find_duplicates(
    embeddings: dict[str, tuple[NDArray[np.floating], tuple[int, int]]],
    threshold: float = 0.8,
) -> list[DuplicatePair]:
    """Find section pairs with similarity above threshold.

    Args:
        embeddings: Dict mapping "file.md#Section" to (embedding_vector, (start_line, end_line))
        threshold: Minimum similarity score to report (default 0.8)

    Returns:
        List of DuplicatePair sorted by similarity descending
    """
    duplicates: list[DuplicatePair] = []
    keys = list(embeddings.keys())

    for i, key1 in enumerate(keys):
        vec1, lines1 = embeddings[key1]
        for key2 in keys[i + 1 :]:
            vec2, lines2 = embeddings[key2]
            sim = cosine_similarity(vec1, vec2)
            if sim >= threshold:
                duplicates.append(
                    DuplicatePair(
                        source=key1,
                        target=key2,
                        similarity=sim,
                        source_lines=lines1,
                        target_lines=lines2,
                    )
                )

    # Sort by similarity descending
    duplicates.sort(key=lambda x: x.similarity, reverse=True)
    return duplicates


def _get_doc_files(repo_root: Path, doc_paths: list[str]) -> list[Path]:
    """Get all doc files matching the glob patterns."""
    import pathspec

    files: list[Path] = []
    for pattern in doc_paths:
        if "**" in pattern or "*" in pattern:
            spec = pathspec.PathSpec.from_lines("gitwildmatch", [pattern])
            for path in repo_root.rglob("*"):
                if path.is_file() and spec.match_file(str(path.relative_to(repo_root))):
                    files.append(path)
        else:
            path = repo_root / pattern
            if path.exists() and path.is_file():
                files.append(path)
    return list(set(files))  # Dedupe


def embed_sections(
    repo_root: Path,
    doc_paths: list[str],
    model_name: str | None = None,
) -> dict[str, tuple[NDArray[np.floating], tuple[int, int]]]:
    """Embed all sections from documentation files.

    Args:
        repo_root: Repository root path
        doc_paths: List of glob patterns for doc files
        model_name: Optional model name (default: BAAI/bge-small-en-v1.5)

    Returns:
        Dict mapping "file.md#Section" to (embedding_vector, (start_line, end_line))
    """
    from fastembed import TextEmbedding

    model_name = model_name or "BAAI/bge-small-en-v1.5"

    # Collect all sections with their content
    sections: list[tuple[str, str, tuple[int, int]]] = []  # (key, content, lines)

    doc_files = _get_doc_files(repo_root, doc_paths)
    for doc_path in doc_files:
        rel_path = doc_path.relative_to(repo_root)
        for heading in list_sections(doc_path):
            content = get_section_content(doc_path, heading)
            line_range = parse_markdown_section(doc_path, heading)
            if content and line_range:
                key = f"{rel_path}#{heading}"
                sections.append((key, content, line_range))

    if not sections:
        return {}

    # Embed all sections
    model = TextEmbedding(model_name=model_name)
    texts = [content for _, content, _ in sections]
    embeddings_list = list(model.embed(texts))

    # Build result dict
    import numpy as np

    result: dict[str, tuple[NDArray[np.floating], tuple[int, int]]] = {}
    for (key, _, lines), embedding in zip(sections, embeddings_list, strict=True):
        result[key] = (np.array(embedding), lines)

    return result


# --- Caching ---


def _get_docs_hash(repo_root: Path, doc_paths: list[str]) -> str:
    """Get a hash representing the current state of doc files."""
    doc_files = _get_doc_files(repo_root, doc_paths)
    content_parts: list[str] = []

    for f in sorted(doc_files):
        try:
            stat = f.stat()
            content_parts.append(f"{f.relative_to(repo_root)}:{stat.st_mtime}")
        except Exception:
            continue

    combined = "\n".join(content_parts).encode()
    return hashlib.sha256(combined).hexdigest()[:16]


def _get_cache_path(repo_root: Path, model_name: str) -> tuple[Path, Path]:
    """Get cache file and state file paths for a model."""
    cache_dir = repo_root / ".menard"
    cache_dir.mkdir(exist_ok=True)

    # Hash model name for safe filename
    model_hash = hashlib.sha256(model_name.encode()).hexdigest()[:8]
    cache_file = cache_dir / f"embeddings_{model_hash}.json"
    state_file = cache_dir / f"embeddings_{model_hash}.state"

    return cache_file, state_file


def save_embeddings_cache(
    repo_root: Path,
    embeddings: dict[str, tuple[NDArray[np.floating], tuple[int, int]]],
    model_name: str,
    doc_paths: list[str] | None = None,
) -> None:
    """Save embeddings to cache."""

    cache_file, state_file = _get_cache_path(repo_root, model_name)

    try:
        # Save state hash
        doc_paths = doc_paths or ["**/*.md"]
        docs_hash = _get_docs_hash(repo_root, doc_paths)
        state_file.write_text(f"{model_name}:{docs_hash}")

        # Convert to JSON-serializable format
        data = {
            key: {"embedding": vec.tolist(), "lines": list(lines)}
            for key, (vec, lines) in embeddings.items()
        }

        with open(cache_file, "w") as f:
            json.dump(data, f)

    except Exception:
        # Silently fail - caching is optional
        pass


def load_embeddings_cache(
    repo_root: Path,
    model_name: str,
    doc_paths: list[str] | None = None,
) -> dict[str, tuple[NDArray[np.floating], tuple[int, int]]] | None:
    """Load embeddings from cache if valid.

    Returns None if cache is missing, stale, or for different model.
    """
    import numpy as np

    cache_file, state_file = _get_cache_path(repo_root, model_name)

    if not cache_file.exists() or not state_file.exists():
        return None

    try:
        # Check state
        doc_paths = doc_paths or ["**/*.md"]
        current_docs_hash = _get_docs_hash(repo_root, doc_paths)
        cached_state = state_file.read_text().strip()
        expected_state = f"{model_name}:{current_docs_hash}"

        if cached_state != expected_state:
            return None

        # Load cache
        with open(cache_file) as f:
            data = json.load(f)

        # Convert back to numpy
        result: dict[str, tuple[NDArray[np.floating], tuple[int, int]]] = {}
        for key, val in data.items():
            result[key] = (np.array(val["embedding"]), tuple(val["lines"]))

        return result

    except Exception:
        return None
