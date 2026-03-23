"""Reviewed state storage for docsync fix command."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Review:
    """A review marking a doc as up-to-date at a specific code commit."""

    code_file: str
    doc_target: str
    reviewed_at: str  # ISO format
    code_commit_at_review: str
    reviewed_by: str = "user"


def _get_reviews_path(repo_root: Path) -> Path:
    """Get path to reviewed.json file."""
    return repo_root / ".docsync" / "reviewed.json"


def load_reviews(repo_root: Path) -> list[Review]:
    """Load reviews from .docsync/reviewed.json. Returns empty list if missing."""
    reviews_path = _get_reviews_path(repo_root)
    if not reviews_path.exists():
        return []

    data = json.loads(reviews_path.read_text())
    return [Review(**r) for r in data.get("reviews", [])]


def save_review(repo_root: Path, review: Review) -> None:
    """Save a review to .docsync/reviewed.json, replacing any existing review for same code+doc."""
    reviews_path = _get_reviews_path(repo_root)

    # Load existing reviews
    existing = load_reviews(repo_root)

    # Remove any existing review for same code_file + doc_target
    existing = [
        r
        for r in existing
        if not (r.code_file == review.code_file and r.doc_target == review.doc_target)
    ]

    # Append new review
    existing.append(review)

    # Write back
    data = {"reviews": [asdict(r) for r in existing]}
    reviews_path.write_text(json.dumps(data, indent=2))


def is_review_valid(review: Review, current_commit: str) -> bool:
    """Check if a review is still valid (code hasn't changed since review)."""
    return review.code_commit_at_review == current_commit


def find_review(reviews: list[Review], code_file: str, doc_target: str) -> Review | None:
    """Find a review for a specific code_file + doc_target pair."""
    for review in reviews:
        if review.code_file == code_file and review.doc_target == doc_target:
            return review
    return None


def clean_reviews(repo_root: Path, remove_all: bool = False) -> int:
    """Remove orphaned reviews (code files that no longer exist).

    Args:
        repo_root: Repository root path
        remove_all: If True, remove all reviews regardless of file existence

    Returns:
        Number of reviews removed
    """
    reviews_path = _get_reviews_path(repo_root)
    if not reviews_path.exists():
        return 0

    reviews = load_reviews(repo_root)
    if not reviews:
        return 0

    if remove_all:
        reviews_path.unlink()
        return len(reviews)

    # Keep only reviews where code file exists
    kept = [r for r in reviews if (repo_root / r.code_file).exists()]
    removed = len(reviews) - len(kept)

    if removed > 0:
        if kept:
            data = {"reviews": [asdict(r) for r in kept]}
            reviews_path.write_text(json.dumps(data, indent=2))
        else:
            reviews_path.unlink()

    return removed
