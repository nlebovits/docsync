<p align="center">
  <img src=".github/branding/profile.png" alt="menard logo" width="200">
</p>

<p align="center">
  <a href="https://github.com/nlebovits/menard/actions/workflows/ci.yml"><img src="https://github.com/nlebovits/menard/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://codecov.io/gh/nlebovits/menard"><img src="https://codecov.io/gh/nlebovits/menard/branch/main/graph/badge.svg" alt="codecov"></a>
  <a href="https://pypi.org/project/menard/"><img src="https://img.shields.io/pypi/v/menard" alt="PyPI"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+"></a>
  <a href="https://github.com/nlebovits/menard/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
</p>

**menard** blocks commits when docs are stale. Define code→doc relationships, and menard uses git diffs to detect drift.

**[Docs](https://nlebovits.github.io/menard/)** · **[Getting Started](https://nlebovits.github.io/menard/getting-started/)** · **[CLI](https://nlebovits.github.io/menard/cli/reference/)**

## Install

```bash
uv add menard
menard init
```

## What It Does

### Track Doc Drift

```toml
# .menard/links.toml
[[link]]
code = "src/auth.py"
docs = ["docs/api.md#Authentication"]
```

```bash
git commit -m "refactor auth"
# ❌ Blocked: docs/api.md#Authentication unchanged since src/auth.py changed
```

### Protect Critical Content

```bash
# .menard/donttouch
README.md#License
"Python 3.10+"
```

Changes to protected literals trigger warnings.

### Find Duplicates

```bash
menard brevity --threshold 0.95
# README.md#License ↔ docs/index.md#License (1.00)
```

Local embeddings. No API keys.

### Audit Trackability

```
> Audit my documentation
```

The [audit skill](https://nlebovits.github.io/menard/skills/) scores docs on deterministic verifiability.

## Quick Start

```bash
menard init                    # Create .menard/
menard bootstrap --apply       # Auto-generate links
menard coverage                # Check coverage %
pre-commit install             # Enable pre-commit hook
```

Pre-commit setup: [docs/getting-started](https://nlebovits.github.io/menard/getting-started/#pre-commit-setup)

## License

Apache-2.0 · [Contributing](https://nlebovits.github.io/menard/contributing/)
