# menard audit

Analyze documentation for menard trackability and cross-document disagreements.

## When to Use

- Onboarding a repo to menard
- Periodic health checks
- After adding new docs
- Checking for README vs CLAUDE.md disagreements

## Phases

| Phase | Flag | Does |
|-------|------|------|
| detect | `--phase=detect` | Find coverage gaps, disagreements, orphans |
| suggest | `--phase=suggest` | Generate fix recommendations |
| fix | `--phase=fix` | Apply deterministic patterns |

Default: all phases sequentially.

```bash
menard audit --dry-run  # Preview scope and token estimate
```

## Workflow

### Phase 1: Detect

#### 1.1 Gather Context

```bash
cat pyproject.toml | grep -A 20 "\[tool.menard\]"
cat .menard/links.toml
cat .menard/donttouch 2>/dev/null || echo "No donttouch"
menard coverage
menard brevity --threshold 0.95 2>/dev/null || echo "Install menard[brevity]"
```

#### 1.2 Scan Docs

**Always include:**
- `README.md` (user-facing entry)
- `CLAUDE.md` (AI-facing, if exists)
- All files in `doc_paths`

For each file, analyze:
1. Structure: headings, tables, code blocks, prose ratio
2. File references: backtick-quoted paths like `src/foo.py`
3. Section scope: does each section map to identifiable code?
4. Protected content: license blocks, version pins

#### 1.3 Detect Disagreements

**Critical.** Conflicting claims are worse than missing docs.

| Pattern | Example |
|---------|---------|
| Version conflicts | README: Python 3.10+, CLAUDE.md: 3.11+ |
| Command conflicts | `--output` vs `--fix-output` |
| Install conflicts | `pip install` vs `uv add` |
| Default conflicts | "Default is 10" vs "Default is 100" |

Detection:
1. Extract claims (commands, versions, flags, defaults)
2. Group by topic
3. Compare within groups
4. Flag with file:line references

#### 1.4 Output Report

```
# docs/api.md
  Overall: 6/10

  ## Authentication (8/10)
    ✓ Code examples
    ✓ References src/auth.py
    ⚠ Not in links.toml — SUGGEST ADD

  ## Data Pipeline (3/10)
    ✗ 400 words prose, no tables/code
    ✗ 7 file references, none linked

# Cross-Document Disagreements
  ✗ Installation method
    README.md:15: `pip install`
    CLAUDE.md:8: `uv add`
    → Pick one source of truth
```

**If `--phase=detect`: stop here.**

---

### Phase 2: Suggest

#### 2.1 links.toml

```toml
# SUGGESTED: Add to .menard/links.toml
[[link]]
code = "src/auth.py"
docs = ["docs/api.md#Authentication"]
```

#### 2.2 donttouch

```
# SUGGESTED: Add to .menard/donttouch
README.md#License
"Apache-2.0"
```

#### 2.3 Duplicate Resolution

```
INTENTIONAL (no action):
  README.md#License ↔ docs/index.md#License

CONSOLIDATE:
  docs/api.md#Auth ↔ docs/getting-started.md#Auth (0.93)
  → Keep one, link from other
```

#### 2.4 Disagreement Resolution

```
DISAGREEMENT: Installation
  SUGGEST: Verify canonical method, update non-canonical doc
  Or: document intentional split (README for users, CLAUDE.md for devs)
```

#### 2.5 Restructuring

```
## Data Pipeline (3/10)
  SUGGEST: Split into per-file sections
  SUGGEST: Convert prose to table
```

**If `--phase=suggest`: stop here.**

---

### Phase 3: Fix

#### 3.1 Auto-apply (safe)

- links.toml additions
- donttouch additions

#### 3.2 Interactive (requires confirmation)

- Restructuring
- Section splits
- Disagreement resolutions
- Pointer-over-prose replacements

## Scoring Rubric

| Score | Characteristics |
|-------|-----------------|
| 9-10 | Tables, code blocks, single-file scope, in links.toml |
| 7-8 | File references, some structure, missing links |
| 5-6 | Mix of structure and prose |
| 3-4 | Long prose, vague references |
| 1-2 | Pure narrative, untrackable |

**Good:** Tables, code blocks, explicit pointers, covered by links.toml
**Bad:** Long prose, multi-file scope, implicit references, disagreements

## Key Principles

1. Heuristic scoring—pattern matching, not AI judgment
2. AI value: restructuring suggestions (prose→table, section splits)
3. Two-audience awareness: user-facing docs vs AI-facing docs
4. README always in scope
5. Disagreements are critical failures
