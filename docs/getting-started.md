# Getting Started

## Install

```bash
uv add menard
```

## Initialize

```bash
menard init
# ✓ Created .menard/links.toml
# ✓ Added [tool.menard] to pyproject.toml
```

## Create Links

```toml
# .menard/links.toml
[[link]]
code = "src/auth.py"
docs = ["docs/api.md#Authentication"]
```

Or auto-generate:

```bash
menard bootstrap --apply
```

## Pre-Commit Setup

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: menard-check
        name: menard-check
        entry: uv run menard check
        language: system
        pass_filenames: false
        always_run: true
```

```bash
pre-commit install
```

Now commits block if docs are stale:

```bash
git commit -m "refactor auth"
# ❌ Blocked: docs/api.md#Authentication unchanged since src/auth.py changed
```

## Typical Workflow

```bash
menard init                  # Create config
menard bootstrap --apply     # Auto-generate links
menard coverage              # Check coverage %
menard validate-links        # Verify link targets exist
pre-commit install           # Enable hook
```

In Claude Code:

```
> Audit my documentation and apply the suggestions
```

## Example Session

```bash
$ menard coverage
Documentation Coverage: 0.0%
  Total code files: 60
  Documented: 0

$ menard bootstrap --apply
Found 8 suggested links
Applied to .menard/links.toml

$ menard coverage
Documentation Coverage: 26.7%
  Total code files: 60
  Documented: 16

$ git add src/cli.py
$ git commit -m "feat: add --verbose flag"
# ❌ Blocked: docs/reference/cli.md stale

$ git add docs/reference/cli.md
$ git commit -m "feat: add --verbose flag"
# ✓ menard check passed
```
