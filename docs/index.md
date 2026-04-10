<p align="center">
  <img src="assets/menard-logo/profile.png" alt="menard logo" width="200">
</p>

# menard

Block commits when docs are stale. Define code→doc relationships in `.menard/links.toml`. menard uses git diffs to detect drift at the section level.

## Install

```bash
uv add menard
menard init
```

## Core Features

| Feature | Command | Description |
|---------|---------|-------------|
| Staleness detection | `menard check` | Block commits if linked docs are stale |
| Coverage reporting | `menard coverage` | % of code files with doc links |
| Protected content | `.menard/donttouch` | Warn on changes to literals/sections |
| Duplicate detection | `menard brevity` | Find similar sections via embeddings |
| Audit skill | `/audit` | Score docs on trackability |

## How It Works

```toml
# .menard/links.toml
[[link]]
code = "src/auth.py"
docs = ["docs/api.md#Authentication"]
```

When `src/auth.py` changes, menard checks if `docs/api.md#Authentication` was updated. If not, commit is blocked.

Section-level tracking: changes to one section won't trigger full doc rewrites.

## Output

All commands support `--format json` for agent consumption:

```json
{
  "stale": [{
    "code_file": "src/auth.py",
    "doc_target": {
      "file": "docs/api.md",
      "section": "Authentication",
      "line_range": [45, 89]
    },
    "suggested_action": "update"
  }]
}
```

## License

Apache-2.0
