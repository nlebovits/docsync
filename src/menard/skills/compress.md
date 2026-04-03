# menard compress

Make documentation deterministically maintainable by replacing prose with pointers, auto-generating repeated content, and enforcing rules with hooks instead of prose.

## When to Use

Use this skill when:
- You already know your docs have issues (ran `/audit --phase=detect`)
- Docs feel bloated and you want to reduce drift surface area
- You're seeing the same information in multiple places
- Rules exist only in prose and keep getting violated
- You want to compress docs by ~50% while improving maintainability

## What This Skill Does

Transform documentation from **prose that drifts** to **pointers that stay current**.

Target: ~50% line reduction by replacing prose with deterministic references.

## Patterns

### 1. Pointer Over Prose

Instead of writing instructions, point to the source of truth:

```markdown
# Prose (drifts)
Run ruff before committing. Use `uv run ruff check --fix .`

# Pointer (stays current)
**Code quality handled by pre-commit.** See `.pre-commit-config.yaml`.
```

**Detection signals:**
- Prose describes a command that exists in a config file
- Prose duplicates what `--help` would show
- Prose explains behavior that's defined in code

**Transformation:**
1. Find the canonical source (config file, CLI help, code)
2. Replace prose with pointer: "See `{file}` for {what}"
3. Add `links.toml` entry if the pointer references code

### 2. Auto-Generate Repeated Content

Use markers for content that appears in multiple places:

```markdown
<!-- BEGIN GENERATED: test-markers -->
| Marker | Description |
|--------|-------------|
| `@pytest.mark.slow` | Tests taking >5s |
| `@pytest.mark.integration` | Requires external services |
<!-- END GENERATED: test-markers -->
```

**Detection signals:**
- Same table/list appears in multiple docs
- Content is derived from config (pyproject.toml markers, CLI options)
- `menard brevity` shows high similarity between sections

**Transformation:**
1. Identify the canonical source (usually config or code)
2. Create a generation script (`scripts/doc_sync.py` or similar)
3. Wrap duplicated content in `<!-- BEGIN/END GENERATED -->` markers
4. Add generation script to CI or pre-commit

**Example generation script:**
```python
# scripts/doc_sync.py
import tomllib
from pathlib import Path

def generate_test_markers():
    config = tomllib.loads(Path("pyproject.toml").read_text())
    markers = config["tool"]["pytest"]["ini_options"].get("markers", [])

    lines = ["| Marker | Description |", "|--------|-------------|"]
    for marker in markers:
        name, desc = marker.split(":", 1)
        lines.append(f"| `@pytest.mark.{name.strip()}` | {desc.strip()} |")

    return "\n".join(lines)

def update_docs():
    for doc in Path("docs").glob("**/*.md"):
        content = doc.read_text()
        # Replace content between markers
        # ...
```

### 3. Enforce With Hooks, Not Prose

```yaml
# Prose-only rule (ignored)
"Never use fetch_arrow_table() - it crashes on large datasets"

# Pre-commit hook (enforced)
- id: duckdb-antipatterns
  name: Check for DuckDB antipatterns
  entry: bash -c 'grep -rn "\.fetch_arrow_table()" --include="*.py" && exit 1 || exit 0'
  language: system
  pass_filenames: false
```

**Detection signals:**
- Prose says "never do X" or "always do Y"
- Prose describes a pattern that could be grep'd
- Rules keep getting violated despite documentation

**Transformation:**
1. Convert the rule to a grep pattern or AST check
2. Add to `.pre-commit-config.yaml`
3. Replace prose with: "Enforced by pre-commit. See `.pre-commit-config.yaml`."
4. Optionally keep a brief "why" explanation

**Common hook patterns:**
```yaml
# Forbidden imports
- id: no-forbidden-imports
  entry: bash -c 'grep -rn "from deprecated_module import" --include="*.py" && exit 1 || exit 0'

# Required headers
- id: license-headers
  entry: bash -c 'head -1 "$@" | grep -q "# Copyright" || exit 1'

# File naming conventions
- id: test-file-naming
  entry: bash -c 'find tests -name "*.py" ! -name "test_*.py" ! -name "conftest.py" ! -name "__init__.py" | grep . && exit 1 || exit 0'
```

### 4. Audit for Orphaned Docs

Detect and remove documentation that references things that no longer exist:

**Orphan patterns:**
| Pattern | Detection | Action |
|---------|-----------|--------|
| Hook that doesn't exist | Doc mentions `.pre-commit-config.yaml` hook that's not there | Remove doc or add hook |
| File that was deleted | Doc references `src/old_module.py` that doesn't exist | Remove or update reference |
| Config that changed | Doc says "default is 10" but config shows 100 | Update doc |
| Feature that was removed | Entire section about deprecated feature | Remove section |

**Detection approach:**
```bash
# Find file references in docs
grep -roh '`[a-zA-Z0-9_/.-]*\.\(py\|toml\|yaml\|json\)`' docs/ | sort -u > doc_refs.txt

# Check which don't exist
while read ref; do
  ref_clean=$(echo "$ref" | tr -d '`')
  [ ! -f "$ref_clean" ] && echo "ORPHAN: $ref"
done < doc_refs.txt
```

### 5. Compression Metrics

Track your progress:

```
Documentation Compression Report
================================
Before: 341 lines across 5 files
After:  163 lines across 5 files
Reduction: 52%

Changes by pattern:
  Pointer over prose:     -89 lines (12 replacements)
  Auto-generate markers:  -45 lines (3 tables consolidated)
  Hook enforcement:       -28 lines (4 rules moved to pre-commit)
  Orphan removal:         -16 lines (2 sections removed)

New artifacts:
  scripts/doc_sync.py     (generates 3 tables)
  .pre-commit-config.yaml (4 new hooks)
  .menard/links.toml      (8 new entries)
```

## Workflow

### Step 1: Inventory

List all docs and their current state:

```bash
# Count lines per doc
wc -l README.md CLAUDE.md docs/**/*.md

# Find prose-heavy sections (high word count, low code block count)
# (This is heuristic - the audit skill does this more precisely)
```

### Step 2: Identify Candidates

For each pattern, find candidates:

**Pointer candidates:**
```bash
# Find command mentions that might be in configs
grep -rn "Run \`" docs/
grep -rn "Use \`" docs/
grep -rn "Execute \`" docs/
```

**Auto-generate candidates:**
```bash
# Find tables that might be derived from config
grep -rn "^\|" docs/ | head -20

# Find duplicates
menard brevity --threshold 0.90
```

**Hook candidates:**
```bash
# Find "never" and "always" rules
grep -rni "never " docs/
grep -rni "always " docs/
grep -rni "must " docs/
grep -rni "don't " docs/
```

**Orphan candidates:**
```bash
# Find file references and check existence
grep -roh '`[^`]*\.\(py\|toml\|yaml\)`' docs/ | sort -u | while read f; do
  clean=$(echo "$f" | tr -d '`')
  [ ! -f "$clean" ] && echo "ORPHAN: $f"
done
```

### Step 3: Transform

For each candidate, apply the appropriate transformation:

1. **Pointer:** Find source of truth → write pointer → add links.toml entry
2. **Auto-generate:** Create script → add markers → run script → add to CI
3. **Hook:** Write grep/AST check → add to pre-commit → update prose
4. **Orphan:** Verify removal is safe → delete or update

### Step 4: Verify

After transformations:

```bash
# Verify links still work
menard check

# Verify hooks pass
pre-commit run --all-files

# Verify generated content is current
python scripts/doc_sync.py --check  # exits non-zero if out of date

# Re-run audit to see improvement
menard audit --phase=detect
```

## Integration with Audit

The `/audit` skill detects issues; `/compress` fixes them.

Typical flow:
```bash
menard audit --phase=detect    # Find problems
menard audit --phase=suggest   # Get recommendations
# Then either:
menard audit --phase=fix       # Let audit apply fixes
# Or:
/compress                      # Use this skill for manual, pattern-by-pattern fixes
```

Use `/compress` when you want more control over which patterns to apply.

## Key Principles

1. **Pointers don't drift** — A pointer to `.pre-commit-config.yaml` stays correct even when the config changes. Prose describing the config drifts.

2. **Generated content has one source** — If a table appears in 3 places, generate it from config. Change config → all 3 update.

3. **Hooks are self-documenting** — A pre-commit hook that fails is better documentation than prose that's ignored.

4. **Less is more maintainable** — 163 lines of pointers beats 341 lines of prose. Smaller surface area = less drift.

5. **Compression is a metric** — Track lines before/after. Target ~50% reduction on first pass.
