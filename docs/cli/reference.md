# CLI Reference

## Setup

### init

```bash
menard init
```

Creates `.menard/links.toml` and adds `[tool.menard]` to `pyproject.toml`.

### bootstrap

```bash
menard bootstrap [--apply]
```

Auto-generate links from filename matching, content analysis, and import graphs.

Without `--apply`: preview. With `--apply`: write to `links.toml`.

---

## Validation

### validate-links

```bash
menard validate-links
```

Check that all link targets (code files, doc files, sections) exist.

### coverage

```bash
menard coverage [--format text|json]
```

Report % of `require_links` files with documentation.

```bash
$ menard coverage
Documentation Coverage: 85.0%
  Total code files: 20
  Documented: 17
```

---

## Staleness

### check

```bash
menard check [--all] [--format text|json] [--show-diff] [--diff-lines N]
```

| Option | Effect |
|--------|--------|
| (default) | Check staged files only |
| `--all` | Check all git-tracked files |
| `--show-diff` | Include code diff |
| `--diff-lines N` | Limit diff output (default: 30) |

Exit: `0` = fresh, `1` = stale.

```bash
$ menard check
❌ commit blocked

  docs/api.md#Authentication
    Code: src/auth.py
    Last code change: 2026-03-17 (abc1234)
    Commits since: abc1234 feat: add MFA support
    Changed: +mfa_verify, +mfa_setup, -legacy_auth
```

### list-stale

```bash
menard list-stale [--format text|paths|json] [--show-diff]
```

List ALL stale docs in the repo (not just staged).

`--format paths`: one file path per line (for scripting).

### affected-docs

```bash
menard affected-docs --files FILE1,FILE2,... [--format text|json]
```

Show which docs would need updating if these files changed.

---

## Information

### info

```bash
menard info FILE [--format text|json]
```

Show all links for a file (docs it links to, files that import it).

### list-protected

```bash
menard list-protected [--format text|json]
```

Show protected sections and literals from `.menard/donttouch`.

### skills

```bash
menard skills [--format text|json] [--copy NAME] [--force]
```

List available Claude Code skills. `--copy NAME` copies bundled skill to `.claude/skills/` for customization.

---

## Fix

### fix

```bash
menard fix
```

Interactive mode. For each stale doc:

- `u` - Update (open for editing)
- `m` - Mark reviewed (ephemeral)
- `i` - Ignore (permanent)
- `s` - Skip
- `q` - Quit

### fix-mark-reviewed

```bash
menard fix-mark-reviewed --code FILE --doc TARGET [--reviewed-by NAME]
```

Mark as reviewed. Valid until code changes again.

Use when: code change doesn't affect docs (logging, internal refactor).

### fix-ignore

```bash
menard fix-ignore --code FILE --doc TARGET
```

Add `ignore = true` to the link. Permanent until manually removed.

Use when: link is too broad, code is deprecated, docs intentionally diverged.

### clean-reviewed

```bash
menard clean-reviewed [--all]
```

Remove review records for deleted files. `--all` removes all reviews.

---

## Duplicate Detection

### brevity

```bash
menard brevity [--threshold N] [--format text|json] [--model NAME] [--no-cache]
```

Find semantically similar sections using local embeddings.

Requires: `uv add menard[brevity]`

| Threshold | Finds |
|-----------|-------|
| 0.95+ | Near-exact duplicates |
| 0.90 | High-confidence duplicates (recommended start) |
| 0.85 | More noise, more coverage |

```bash
$ menard brevity --threshold 0.95
README.md#License ↔ docs/index.md#License (1.00)
README.md#Quick Start ↔ docs/getting-started.md#Quick Start (0.96)
```

Some duplicates are intentional (README ↔ docs/index.md). Review in context.

Exclude via `brevity_exclude` in config.

---

## Utility

### clear-cache

```bash
menard clear-cache
```

Delete `.menard/cache/` (import graph cache).

---

## Fix Workflow

```
Code changed, docs flagged stale
    │
    ├─ Does doc need updating?
    │   ├─ Yes → Update doc, commit both
    │   └─ No → Why?
    │       ├─ Change doesn't affect docs → fix-mark-reviewed
    │       └─ Link shouldn't exist → fix-ignore
```

| Aspect | fix-mark-reviewed | fix-ignore |
|--------|-------------------|------------|
| Duration | Until next code change | Permanent |
| Stored in | `.menard/reviewed.state` | `.menard/links.toml` |
| Commit needed | No | Yes |
