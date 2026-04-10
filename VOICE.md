# Documentation Voice Guide

Rules for writing concise, readable technical documentation. Derived from pystac-client, antimeridian, caveman, obstore, and claudechic patterns.

## Structure Rules

1. **Flat hierarchy.** 5-7 top-level sections max for simple tools. Complex libraries can have more pages but organize into clear buckets (User Guide, Examples, API, Advanced).
2. **Problem-first.** Lead with "What problem does this solve?" in one sentence.
3. **Install in viewport.** Copy-paste command visible without scrolling.
4. **Code leads, prose follows.** One sentence of context, then code block.
5. **Separate happy path from edge cases.** Failure modes get their own page.
6. **No "Overview" page.** Homepage IS the introduction.
7. **API reference is generated.** Never hand-write what autodoc handles.
8. **Link every function name.** Reference links to API docs inline, not in separate "see also" sections.
9. **Parallel examples.** Show sync/async, Python/CLI, or alternative approaches side-by-side.

## Voice Rules

1. **Sentence length: 12-18 words.** One clause per sentence. Break compounds.
2. **Use "you" for instructions.** Not "the user", "one should", or passive voice.
3. **Use "we" for walkthroughs.** "Let's start with..." guides the reader.
4. **Start instructions with imperatives.** "Create", "Use", "Run"—not "You can create".
5. **Define terms parenthetically.** `WGS84 (the coordinate system used by GeoJSON)`
6. **One sentence before code.** Never "Here is an example of how you would..."
7. **Treat readers as competent.** Skip obvious explanations. Don't hand-hold.
8. **Be honest about limitations.** "Not mature yet. Expect bugs." builds trust. Overselling erodes it.
9. **FAQ as documentation.** Question-answer format works. Conversational tone permitted.

## Kill List (Caveman-Style)

Delete these unconditionally:

**Pleasantries:**
- "I'd be happy to help"
- "Great question!"
- "It might be worth considering"
- "You may want to"
- "It's important to note that"

**Hedge words:**
- "basically", "essentially", "actually", "really", "very"
- "In order to" → "To"
- "is able to" → "can"
- "in the event that" → "if"

**Bloat patterns:**
- "As you can see from the example above" → delete
- "Let's take a look at how to" → delete, just show code
- "The following example demonstrates" → ":"

## Preserve List

Never compress:
- Code blocks (exact syntax matters)
- Technical terms (polymorphism stays polymorphism)
- URLs and paths
- Version numbers
- CLI flags and arguments

## Intensity Levels

**Standard (default):** Drop filler, keep grammar. Professional but concise.
```
Normal: "The reason your component re-renders is because you're creating a new object reference each time."
Standard: "Component re-renders because you create a new object reference each render."
```

**Terse:** Drop articles, use fragments. Telegraphic.
```
Normal: "The reason your component re-renders is because you're creating a new object reference each time."
Terse: "New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`."
```

## Warning/Caveat Format

Direct statement + consequence. No hedging.

```
Bad:  "It's worth noting that this might potentially cause issues with..."
Good: "This polygon is invalid GeoJSON—most renderers display it incorrectly."
```

## Section Patterns

**Getting Started:**
```markdown
## Install

pip install mypackage

## Quick Start

Create a client:

[code block]

Fetch data:

[code block]
```

**API Reference intro:**
```markdown
## API

Full reference: [link to autodoc]

Common methods:

- `client.search()` - Find items matching criteria
- `client.get()` - Fetch single item by ID
```

**Failure Modes page:**
```markdown
## When Things Break

### Invalid Input

[code showing error]

Fix: Validate input before calling. Use `validate()` helper.

### Network Timeout

[code showing error]

Fix: Pass `timeout=30` or use retry middleware.
```

## Metrics

Target these compression ratios:
- Explanatory prose: 50-70% reduction vs verbose default
- Code examples: 0% reduction (preserve exactly)
- Warnings/caveats: 30-40% reduction
- API reference: 20-30% reduction

## Anti-Patterns

Avoid these documentation smells:

1. **"Chapter 3.2.1.4" nesting** — flatten or split into pages
2. **Prose explaining obvious code** — let code speak
3. **"See also" sections longer than content** — delete or consolidate
4. **Prerequisites before install** — install first, prerequisites inline
5. **Changelog in docs** — link to CHANGELOG.md
6. **Overselling** — readers distrust hype; understate, then deliver
7. **Hand-holding competent users** — skip "click the button labeled X"

## Scaling Guidelines

**Small tool (single purpose):** 
- Single page or 5-7 sections
- FAQ format works well
- claudechic style: honest, terse, assumes competence

**Medium library (multiple features):**
- Getting Started + Examples + API Reference
- antimeridian style: problem-first, dedicated failure modes page

**Large library (complex ecosystem):**
- Clear buckets: User Guide, Examples, API, Advanced, Troubleshooting
- obstore style: extensive but organized, every function linked
- Homepage still leads with install + one-sentence value prop
