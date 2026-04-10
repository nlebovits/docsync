# Contributing

## Setup

```bash
git clone https://github.com/nlebovits/menard.git
cd menard
uv sync --all-extras
uv run pre-commit install
```

## Test

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
```

## Standards

| Area | Standard |
|------|----------|
| Commits | [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`) |
| Versioning | `uv run cz bump` |
| Style | ruff (line length: 100) |

## Code of Conduct

Be respectful. Harassment not tolerated.

## License

Apache-2.0
