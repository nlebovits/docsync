#!/bin/bash
set -e

TEST_DIR=$(mktemp -d)
cd "$TEST_DIR"

# Initialize git repo
git init -q
git config user.email "test@example.com"
git config user.name "Test User"

# Create test files
mkdir -p src docs
cat > pyproject.toml << 'TOML'
[tool.docsync]
require_links = ["src/**/*.py"]
TOML

cat > src/a.py << 'PY'
# docsync: docs/a.md
import b
def foo():
    pass
PY

cat > src/b.py << 'PY'
# docsync: docs/b.md  
def bar():
    pass
PY

cat > docs/a.md << 'MD'
<!-- docsync: src/a.py -->
# A
MD

cat > docs/b.md << 'MD'
<!-- docsync: src/b.py -->
# B
MD

git add .
git commit -q -m "Initial"

# First run - should build cache
echo "=== First run (building cache) ==="
echo -n "Time: "
time -p docsync info src/a.py > /dev/null 2>&1

# Check cache was created
if [ -f .docsync/import_graph.json ]; then
    echo "✓ Cache created: .docsync/import_graph.json"
    echo "  Size: $(wc -c < .docsync/import_graph.json) bytes"
fi

# Second run - should use cache
echo -e "\n=== Second run (using cache) ==="
echo -n "Time: "
time -p docsync info src/a.py > /dev/null 2>&1

# Modify a file to invalidate cache
echo -e "\n=== Modifying file (invalidates cache) ==="
echo "# comment" >> src/b.py
git add src/b.py
git commit -q -m "Update b.py"

echo -n "Time: "
time -p docsync info src/a.py > /dev/null 2>&1

cd /
rm -rf "$TEST_DIR"
echo -e "\n✓ Cache test completed successfully"
