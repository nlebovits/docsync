# Agent Skills

menard ships Claude Code skills for documentation management.

## List Skills

```bash
menard skills              # List all
menard skills --copy audit # Copy to .claude/skills/ for customization
```

Skills are **bundled** (shipped with menard) or **local** (in `.claude/skills/`). Local overrides bundled.

---

## Audit

Score docs on **deterministic verifiability**—how well menard can track them.

### Phases

| Phase | Flag | Does |
|-------|------|------|
| detect | `--phase=detect` | Find coverage gaps, disagreements, orphans |
| suggest | `--phase=suggest` | Generate fix recommendations |
| fix | `--phase=fix` | Apply deterministic patterns |

```bash
menard audit                    # All phases
menard audit --phase=detect     # Stop after detection
menard audit --dry-run          # Preview scope
```

### Scoring

| Score | Meaning |
|-------|---------|
| 9-10 | Tables, code blocks, single-file scope, in links.toml |
| 7-8 | File references present, could use more links |
| 5-6 | Mix of structure and prose, missing links.toml entries |
| 3-4 | Long prose, vague references |
| 1-2 | Pure narrative, untrackable |

### Cross-Document Disagreements

The audit detects conflicting claims:

| Pattern | Example |
|---------|---------|
| Version conflicts | README: 3.10+, CLAUDE.md: 3.11+ |
| Command conflicts | `--output` vs `--fix-output` |
| Install conflicts | `pip install` vs `uv add` |

### Output

```
# docs/api.md
  Overall: 6/10

  ## Authentication (8/10)
    ✓ Contains code examples
    ⚠ src/auth.py not in links.toml — SUGGEST ADD

  ## Data Pipeline (3/10)
    ✗ 400 words prose, no code blocks
    ✗ References 7 files, none linked

# Cross-Document Disagreements
  ✗ README.md:15 says `pip install`
    CLAUDE.md:8 says `uv add`
```

### Usage

```
> Audit my documentation
> Run menard audit --phase=detect only
```

---

## Compress

Transform docs from **prose that drifts** to **pointers that stay current**.

Target: ~50% line reduction.

### Patterns

**Pointer over prose:**

```markdown
# Drifts
Run ruff before committing. Use `uv run ruff check --fix .`

# Stays current
**Code quality handled by pre-commit.** See `.pre-commit-config.yaml`.
```

**Auto-generate repeated content:**

```markdown
<!-- BEGIN GENERATED: test-markers -->
| Marker | Description |
|--------|-------------|
| `@pytest.mark.slow` | Tests taking >5s |
<!-- END GENERATED: test-markers -->
```

**Enforce with hooks, not prose:**

```yaml
# Prose (ignored): "Never use fetch_arrow_table()"
# Hook (enforced):
- id: duckdb-antipatterns
  entry: bash -c 'grep -rn "\.fetch_arrow_table()" && exit 1 || exit 0'
```

### Usage

```
> Run the compress skill on my documentation
> Apply pointer-over-prose pattern to CLAUDE.md
```

---

## Integration

```bash
menard audit --phase=detect    # Find problems
menard audit --phase=suggest   # Get recommendations
# Then:
menard audit --phase=fix       # Auto-apply
# Or:
/compress                      # Manual pattern-by-pattern
```
