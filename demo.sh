#!/bin/bash
set -e

cd testbed
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                 DOCSYNC DEMONSTRATION                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo

echo "📊 1. COVERAGE REPORT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docsync coverage
echo

echo "🔍 2. PRE-COMMIT HOOK - BLOCKED (missing doc)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Staging: src/core/cache.py (without docs/architecture.md)"
git reset --quiet 2>/dev/null || true
git add src/core/cache.py
echo "Running: docsync check"
docsync check || echo "❌ Commit blocked (exit code: $?)"
git reset --quiet
echo

echo "✅ 3. PRE-COMMIT HOOK - PASSED (both files staged)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Staging: src/core/cache.py + docs/architecture.md"
git add src/core/cache.py docs/architecture.md
echo "Running: docsync check"
docsync check
git reset --quiet
echo

echo "🔗 4. BOOTSTRAP - Find missing links"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docsync bootstrap | head -20

