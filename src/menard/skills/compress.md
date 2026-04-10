# menard compress

Transform documentation from prose that drifts to pointers that stay current.

Target: ~50% line reduction.

## When to Use

- Docs have known issues (ran `/audit --phase=detect`)
- Docs feel bloated
- Same info in multiple places
- Rules in prose keep getting violated

## Patterns

### 1. Pointer Over Prose

```markdown
# Drifts
Run ruff before committing. Use `uv run ruff check --fix .`

# Stays current
**Code quality handled by pre-commit.** See `.pre-commit-config.yaml`.
```

**Signals:** Prose describes a command in a config file, duplicates `--help`, explains code-defined behavior.

**Transform:** Find canonical source → replace with pointer → add links.toml entry.

### 2. Auto-Generate Repeated Content

```markdown
<!-- BEGIN GENERATED: test-markers -->
| Marker | Description |
|--------|-------------|
| `@pytest.mark.slow` | Tests taking >5s |
<!-- END GENERATED: test-markers -->
```

**Signals:** Same table in multiple docs, content derived from config, `menard brevity` shows high similarity.

**Transform:** Create generation script → wrap in markers → add to CI.

### 3. Enforce With Hooks

```yaml
# Prose (ignored): "Never use fetch_arrow_table()"
# Hook (enforced):
- id: duckdb-antipatterns
  entry: bash -c 'grep -rn "\.fetch_arrow_table()" && exit 1 || exit 0'
```

**Signals:** "never do X", "always do Y", rule violations despite docs.

**Transform:** Convert to grep/AST check → add to pre-commit → update prose to "Enforced by pre-commit."

### 4. Remove Orphans

Docs referencing things that don't exist:
- Hooks not in `.pre-commit-config.yaml`
- Deleted files
- Changed config values

**Detection:**
```bash
grep -roh '`[^`]*\.\(py\|toml\|yaml\)`' docs/ | sort -u | while read f; do
  clean=$(echo "$f" | tr -d '`')
  [ ! -f "$clean" ] && echo "ORPHAN: $f"
done
```

## Workflow

### 1. Inventory

```bash
wc -l README.md CLAUDE.md docs/**/*.md
```

### 2. Find Candidates

```bash
# Pointer candidates
grep -rn "Run \`" docs/
grep -rn "Use \`" docs/

# Auto-generate candidates
menard brevity --threshold 0.90

# Hook candidates
grep -rni "never \|always \|must \|don't " docs/

# Orphans
grep -roh '`[^`]*\.\(py\|toml\|yaml\)`' docs/ | sort -u | while read f; do
  clean=$(echo "$f" | tr -d '`')
  [ ! -f "$clean" ] && echo "ORPHAN: $f"
done
```

### 3. Transform

For each candidate:
1. **Pointer:** Find source → write pointer → add links.toml
2. **Auto-generate:** Create script → add markers → add to CI
3. **Hook:** Write check → add to pre-commit → update prose
4. **Orphan:** Verify safe → delete or update

### 4. Verify

```bash
menard check
pre-commit run --all-files
menard audit --phase=detect
```

## Metrics

```
Before: 341 lines
After:  163 lines
Reduction: 52%

  Pointer over prose:    -89 lines (12 replacements)
  Auto-generate markers: -45 lines (3 tables)
  Hook enforcement:      -28 lines (4 rules)
  Orphan removal:        -16 lines (2 sections)
```

## Key Principles

1. Pointers don't drift—config references stay correct when config changes
2. Generated content has one source—change once, update everywhere
3. Hooks are self-documenting—failure beats ignored prose
4. Less is more maintainable—smaller surface = less drift
5. Track compression as metric—target ~50%
