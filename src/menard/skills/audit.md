# menard audit

Analyze documentation for menard trackability, detect cross-document disagreements, and suggest improvements.

## When to Use

Use this skill when:
- Onboarding a new repo to menard (`menard init` → `menard audit`)
- Periodic health checks on documentation coverage
- After adding new docs that need links.toml entries
- When docs feel "messy" and need restructuring for trackability
- Checking for cross-document disagreements (README vs CLAUDE.md, etc.)

## Phases

The audit runs in three phases. By default, all phases run sequentially.

| Phase | Flag | Does What |
|-------|------|-----------|
| detect | `--phase=detect` | Find issues: coverage gaps, disagreements, orphaned docs |
| suggest | `--phase=suggest` | Generate fix recommendations |
| fix | `--phase=fix` | Apply deterministic patterns (pointer-over-prose, etc.) |

```bash
menard audit                    # Run all phases (default)
menard audit --phase=detect     # Stop after detection
menard audit --phase=suggest    # Stop after suggestions
menard audit --phase=fix        # Run full workflow including fixes
```

Each phase outputs usable results if stopped early.

## Dry Run

Preview scope and estimated effort before running:

```bash
menard audit --dry-run
```

Output:
```
Menard audit scope:
  Files: README.md, CLAUDE.md, docs/*.md (14 files)
  Links: .menard/links.toml (23 relationships)
  Code paths referenced: 31 files

  Phases: detect → suggest → fix
  Estimated: ~18k tokens

  Run without --dry-run to proceed.
```

## What This Skill Does

Score docs on **deterministic verifiability** — how well menard can track and enforce them.

### Scoring Signals

**Good structure (increase score):**
- Tables with file paths, commands, or config values (machine-parseable)
- Code blocks with actual commands or config snippets
- Sections with clear single-file scope (heading maps to one code file)
- Explicit source-of-truth pointers ("see X for canonical version")
- Short, factual assertions ("CLI entry point: `foo` → `bar:baz`")
- Already covered by `links.toml` entries
- Protected by `donttouch` rules where appropriate

**Poor structure (decrease score):**
- Long prose blocks with no code references or tables
- Sections referencing many code files without clear boundaries
- Implicit file references (mentions `auth.py` in prose but not in links.toml)
- Assertions that could be checked against code but aren't linked
- No heading structure (flat wall of text)
- Terminology inconsistencies
- **Cross-document disagreements** (see below)

## Workflow

### Phase 1: Detect

#### Step 1.1: Gather Context

```bash
# Check current menard configuration
cat pyproject.toml | grep -A 20 "\[tool.menard\]"

# See existing links
cat .menard/links.toml

# See existing protections
cat .menard/donttouch 2>/dev/null || echo "No donttouch file"

# Run coverage to see current state
menard coverage

# Find duplicate content (requires menard[brevity])
menard brevity --threshold 0.95 2>/dev/null || echo "Install menard[brevity] for duplicate detection"
```

#### Step 1.2: Scan Documentation

Read all docs matching `doc_paths` from config (typically `docs/**/*.md`, `README.md`).

**Critical:** Always include `README.md` in the audit scope, even if not explicitly listed in `doc_paths`. README is the primary user-facing entry point and must stay consistent with internal documentation.

**Required files (always audit):**
- `README.md` — User-facing entry point
- `CLAUDE.md` — AI-facing instructions (if exists)
- All files in `doc_paths` config

For each doc file, analyze:
1. **Structure**: Headings, tables, code blocks, prose ratio
2. **File references**: Backtick-quoted paths like `src/foo.py`
3. **Section scope**: Does each section map to identifiable code?
4. **Protected content**: License blocks, version pins, critical terminology

#### Step 1.3: Detect Cross-Document Disagreements

**This is critical.** Two docs making conflicting claims about the same thing is worse than missing documentation.

**Disagreement patterns to detect:**

| Pattern | Example | Impact |
|---------|---------|--------|
| Version/dependency conflicts | README says Python 3.10+, CLAUDE.md says 3.11+ | Users get wrong version |
| Command/flag conflicts | One doc shows `--output`, another shows `--fix-output` | Commands fail |
| Installation method conflicts | README says `pip install`, CLAUDE.md says `uv add` | Inconsistent onboarding |
| API signature conflicts | Different function signatures in different docs | Code doesn't work |
| Default value conflicts | "Default is 10" vs "Default is 100" | Unexpected behavior |

**Two-audience awareness:**

| Audience | Docs | Characteristics |
|----------|------|-----------------|
| Users | README, docs/, tutorials | Installation, quickstart, examples |
| AI agents | CLAUDE.md, context/, skills/ | Architecture, patterns, constraints |

Cross-audience disagreements are particularly high-impact: AI agents reading CLAUDE.md may generate code that contradicts what README promises to users.

**Detection approach:**
1. Extract claims from each doc (commands, versions, flags, defaults)
2. Group claims by topic (installation, CLI usage, configuration)
3. Compare claims within each group
4. Flag disagreements with specific file:line references

#### Step 1.4: Generate Report

Output per-file, per-section scores with specific issues:

```
# docs/api.md
  Overall: 6/10 (partially trackable)

  ## Authentication (8/10)
    ✓ Contains code examples
    ✓ References src/auth.py
    ⚠ src/auth.py not in links.toml — SUGGEST ADD

  ## Data Pipeline (3/10)
    ✗ 400 words of prose, no tables or code blocks
    ✗ References 7 code files, none in links.toml
    ✗ No clear single-file scope — consider splitting

  ## License (9/10)
    ✓ Short, assertable content
    ⚠ Not in donttouch — SUGGEST PROTECT

# Cross-Document Disagreements
  ✗ DISAGREEMENT: Installation method
    README.md:15 says: `pip install mypackage`
    CLAUDE.md:8 says: `uv add mypackage`
    → These contradict. Pick one source of truth.

  ✗ DISAGREEMENT: CLI flag
    docs/cli.md#Options says: `--output PATH`
    CLAUDE.md:42 says: `--fix-output PATH`
    → Verify against actual CLI: `mypackage --help`
```

**If `--phase=detect` was specified, stop here.**

---

### Phase 2: Suggest

#### Step 2.1: links.toml suggestions

Extract file path mentions from prose and suggest entries:

```toml
# SUGGESTED: Add to .menard/links.toml

[[link]]
code = "src/auth.py"
docs = ["docs/api.md#Authentication"]

[[link]]
code = "src/pipeline.py"
docs = ["docs/api.md#Data Pipeline"]
```

#### Step 2.2: donttouch suggestions

Detect protected content patterns:

```
# SUGGESTED: Add to .menard/donttouch

# License section should not change
README.md#License

# License identifier must exist
"Apache-2.0"

# Version pins
pyproject.toml: "python >= 3.10"
```

#### Step 2.3: Duplicate content suggestions

When `menard brevity` finds duplicates:

```
## Duplicate Content (from menard brevity)

INTENTIONAL (no action needed):
  README.md#License ↔ docs/index.md#License (1.00)
  → Standard pattern: docs site mirrors README

CONSIDER CONSOLIDATING:
  docs/api.md#Authentication ↔ docs/getting-started.md#Auth Setup (0.93)
  → Both explain the same auth flow
  → SUGGEST: Keep one, link to it from the other

SUGGEST: Add source-of-truth marker
  If README.md#Quick Start is canonical, add to the duplicate:
  "See [Quick Start](../README.md#quick-start) for the canonical version."
```

#### Step 2.4: Disagreement resolution suggestions

For each detected disagreement, suggest resolution:

```
## Disagreement Resolutions

DISAGREEMENT: Installation method (README.md:15 vs CLAUDE.md:8)
  SUGGEST: Verify canonical method, then:
  - If uv is canonical: Update README.md to use `uv add`
  - If pip is canonical: Update CLAUDE.md to allow pip
  - Consider: README for users (pip/pipx), CLAUDE.md for devs (uv)
    → If intentional split, document it explicitly

DISAGREEMENT: CLI flag (docs/cli.md vs CLAUDE.md)
  SUGGEST: Run `mypackage --help` to verify actual flag
  → Update the incorrect doc to match reality
  → Add links.toml entry to track CLI docs against code
```

#### Step 2.5: Restructuring suggestions

For low-scoring sections, suggest concrete improvements:

```
## Data Pipeline (score: 3/10)

SUGGEST: Split into per-file sections
This section references: src/pipeline.py, src/transform.py, src/loader.py

Proposed structure:
  ## Pipeline Overview (keep as brief intro)
  ## Transform Step → links to src/transform.py
  ## Loading Step → links to src/loader.py

SUGGEST: Convert prose to table
Current (78 words): "The pipeline supports several output formats..."
Proposed:
  | Format | Type | Handler |
  |--------|------|---------|
  | JSON | Output | `src/formats/json.py` |
  | CSV | Output | `src/formats/csv.py` |
```

**If `--phase=suggest` was specified, stop here.**

---

### Phase 3: Fix

Apply deterministic documentation patterns. For detailed guidance, see the `/compress` skill.

#### Step 3.1: Apply safe changes (auto)

**Safe to auto-apply:**
- `links.toml` additions (purely additive)
- `donttouch` additions (purely additive)

#### Step 3.2: Apply transformations (interactive)

**Require confirmation:**
- Restructuring changes (modify doc content)
- Section splits
- Prose-to-table conversions
- Disagreement resolutions
- Pointer-over-prose replacements

For each transformation, show before/after and ask for confirmation.

#### Step 3.3: Deterministic patterns

Apply patterns from the `/compress` skill:

1. **Pointer over prose** — Replace instructions with config references
2. **Auto-generate markers** — Add `<!-- BEGIN GENERATED -->` for repeated content
3. **Hook enforcement** — Suggest pre-commit hooks for rules currently only in prose
4. **Orphan cleanup** — Remove docs referencing non-existent files/hooks

---

## Output Formats

### Human-readable (default)
```bash
menard audit
```

### JSON (for programmatic use)
```bash
menard audit --format json
```

### Suggestions only
```bash
menard audit --suggest
```

### Apply safe changes
```bash
menard audit --apply
```

## Key Principles

1. **Heuristic, not AI-powered scoring** — Pattern matching: count tables, count prose length, grep for file paths, check links.toml coverage. Deterministic and fast.

2. **AI for restructuring suggestions** — The skill (Claude) adds value by proposing how to restructure prose into tables, how to split sections, etc.

3. **links.toml and donttouch suggestions are deterministic** — Inferred from file path mentions, heading structure, content patterns.

4. **Two-audience awareness** — If repo has both `docs/` and `CLAUDE.md`/`context/`, score them differently. AI-oriented docs should be denser, more structured.

5. **README is always in scope** — Even if not in `doc_paths`, README.md must be audited. It's the user-facing entry point.

6. **Disagreements are critical** — Cross-document disagreements are worse than missing docs. Detect and resolve them.

## Integration with menard init

Ideal onboarding flow:
```bash
menard init                    # Creates config, .menard/ directory
menard audit --dry-run         # Preview scope
menard audit --phase=detect    # "Here's what your docs look like"
menard audit --phase=suggest   # Get recommendations
menard audit --apply           # Auto-generate links.toml + donttouch
menard bootstrap               # Fill in convention-based links
menard install-hook            # Start enforcing
```
