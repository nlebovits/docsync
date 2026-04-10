# Configuration

## pyproject.toml

```toml
[tool.menard]
require_links = ["src/**/*.py"]  # Code files that must have doc links
doc_paths = ["docs/**/*.md"]     # Where to look for docs
exclude_docs = ["**/adr/**"]     # Exclude from bootstrap suggestions
transitive_depth = 1             # Import chain depth (0 = direct only)
brevity_exclude = ["*#License"]  # Exclude from duplicate detection
```

| Option | Effect |
|--------|--------|
| `require_links` | Files matching this glob show in coverage reports if unlinked |
| `doc_paths` | Where menard searches for documentation |
| `exclude_docs` | Prevents `menard bootstrap` from suggesting links (manual links still work) |
| `transitive_depth` | If A imports B and B changes, mark A's docs stale? (1=yes, 0=no) |
| `brevity_exclude` | Filter `menard brevity` results. Patterns: `CLAUDE.md`, `*#License`, `README.md#Quick Start` |

## links.toml

```toml
# .menard/links.toml

# Basic link
[[link]]
code = "src/auth.py"
docs = ["docs/api.md"]

# Section-level (recommended)
[[link]]
code = "src/auth.py"
docs = ["docs/api.md#Authentication"]

# Multiple targets
[[link]]
code = "src/models/user.py"
docs = [
  "docs/models.md#User Model",
  "docs/api.md#User Endpoints",
]

# Glob patterns
[[link]]
code = "src/models/*.py"
docs = ["docs/models.md"]

# Auto-generated docs (skip staleness, validate existence)
[[link]]
code = "src/cli.py"
docs = ["docs/reference/cli.md"]
auto_generated = true

# Permanently ignore staleness
[[link]]
code = "src/legacy.py"
docs = ["docs/legacy.md"]
ignore = true
```

Section-level links: when `src/auth.py` changes, only `#Authentication` needs updating—not the entire file.

## donttouch

```bash
# .menard/donttouch

# Sections (never mark stale)
README.md#License
docs/contributing.md#Code of Conduct

# Literals (warn if changed)
"Python 3.10+"
"Apache-2.0"
"#7730E1"
```

```bash
menard list-protected  # Show all protections
```

## Staleness Detection

menard checks two places:

1. **Staged content**: `git diff --cached` (same-commit workflow)
2. **Git history**: Compare last code commit to doc changes

```bash
# Code changed at abc1234, doc section lines 45-89
# If git diff shows no overlap with 45-89, doc is stale
```

Transitive staleness: if `src/auth.py` imports `src/crypto.py` and crypto changes, auth's docs may be stale (controlled by `transitive_depth`).

### Enriched Output

```bash
$ menard list-stale

  docs/api.md#Authentication
    Code: src/auth.py
    Last code change: 2026-03-17 (abc1234)
    Last doc update: 2026-03-10
    Commits since doc updated:
      abc1234 (2026-03-17) feat: add MFA support
    Changed: +2 symbols, -1 symbol
      Added: mfa_verify, mfa_setup
      Removed: legacy_auth
```

JSON output includes `line_range`, `symbols_added`, `symbols_removed`, `suggested_action`.

## Bootstrap

```bash
menard bootstrap         # Preview suggestions
menard bootstrap --apply # Apply to links.toml
```

Uses filename matching (`src/auth.py` → `docs/auth.md`), content analysis (grep for file references), and import graphs.

Exclude static docs (ADRs, plans) via `exclude_docs` config.

## Commands

| Command | Purpose |
|---------|---------|
| `menard check` | Pre-commit: validate links + check staged files |
| `menard check --all` | Check ALL files (not just staged) |
| `menard list-stale` | List all stale docs in repo |
| `menard fix` | Interactive: review/update/mark/ignore |
| `menard fix-mark-reviewed --code FILE --doc TARGET` | Mark reviewed (ephemeral, until next code change) |
| `menard fix-ignore --code FILE --doc TARGET` | Permanently ignore link |
| `menard validate-links` | Check all link targets exist |
| `menard coverage` | Show documentation coverage % |
| `menard clean-reviewed` | Remove orphaned review records |

All commands support `--format json`.
