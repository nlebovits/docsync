#!/bin/bash
set -e

TEST_DIR=$(mktemp -d)
cd "$TEST_DIR"

# Initialize git repo
git init
git config user.email "test@example.com"
git config user.name "Test User"

# Create test files
mkdir -p src docs
cat > src/a.py << 'PY'
import b
def foo():
    pass
PY

cat > src/b.py << 'PY'
def bar():
    pass
PY

git add .
git commit -m "Initial"

# First run - should build cache
echo "=== First run (cache miss) ==="
time docsync info src/a.py 2>&1 | head -5

# Check cache was created
if [ -f .docsync/import_graph.json ]; then
    echo "✓ Cache file created"
    ls -lh .docsync/
else
    echo "✗ Cache file not created"
fi

# Second run - should use cache (much faster)
echo -e "\n=== Second run (cache hit) ==="
time docsync info src/a.py 2>&1 | head -5

# Clear cache
echo -e "\n=== Clearing cache ==="
docsync clear-cache

# Third run - cache miss again
echo -e "\n=== Third run (cache miss after clear) ==="
time docsync info src/a.py 2>&1 | head -5

cd /
rm -rf "$TEST_DIR"
echo -e "\n✓ Cache test completed"
