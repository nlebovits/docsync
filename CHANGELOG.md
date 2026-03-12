## v0.1.0 (2026-03-12)

### Features

- **Initial Release**: docsync with agent-native UX and caching
  - Bidirectional linking between code and documentation
  - Import-aware staleness detection
  - Pre-commit enforcement
  - SHA-based caching for import graphs
  - Agent-native commands (JSON output, batch operations)
  - Deferral system for temporary bypasses
  - Coverage tracking

- **Testing & CI/CD**
  - Comprehensive test suite (122 tests, 74% coverage)
  - GitHub Actions CI (Python 3.11 & 3.12)
  - Dependabot for dependency updates (grouped PRs)
  - Pre-commit hooks (ruff, pytest, commitizen)

- **Semantic Versioning**
  - Commitizen for conventional commits
  - Automated changelog generation
  - Version management across project files

### Bug Fixes

- Ruff formatter and linting compliance
