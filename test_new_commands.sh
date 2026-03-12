#!/bin/bash
# Test script for new docsync commands

set -e

echo "=== Testing New Docsync Commands ==="
echo

# Create a test repo
TEST_DIR=$(mktemp -d)
cd "$TEST_DIR"
git init
git config user.email "test@example.com"
git config user.name "Test User"

# Create pyproject.toml
cat > pyproject.toml << 'EOF'
[tool.docsync]
require_links = ["src/**/*.py"]
EOF

# Create test files
mkdir -p src docs
cat > src/auth.py << 'EOF'
# docsync: docs/auth.md
def authenticate(user, password):
    """Authenticate a user."""
    return True
EOF

cat > docs/auth.md << 'EOF'
<!-- docsync: src/auth.py -->
# Authentication

This is the authentication documentation.
EOF

cat > src/user.py << 'EOF'
# docsync: docs/user.md
def get_user(user_id):
    """Get user by ID."""
    return {"id": user_id}
EOF

cat > docs/user.md << 'EOF'
<!-- docsync: src/user.py -->
# User Management

This is the user documentation.
EOF

# Add and commit
git add .
git commit -m "Initial commit"

# Make a code change without updating docs
sleep 2
cat >> src/auth.py << 'EOF'

def logout(user):
    """Logout a user."""
    return True
EOF
git add src/auth.py
git commit -m "Add logout function"

echo "Test 1: docsync list-stale (text format)"
docsync list-stale || true
echo

echo "Test 2: docsync list-stale (paths format)"
docsync list-stale --format paths || true
echo

echo "Test 3: docsync list-stale (json format)"
docsync list-stale --format json || true
echo

echo "Test 4: docsync affected-docs"
docsync affected-docs --files "src/auth.py" || true
echo

echo "Test 5: docsync info"
docsync info src/auth.py || true
echo

echo "Test 6: docsync info (json)"
docsync info src/auth.py --format json || true
echo

echo "Test 7: docsync explain-changes"
docsync explain-changes src/auth.py || true
echo

echo "Test 8: docsync defer"
docsync defer src/auth.py --message "Testing defer" || true
echo

echo "Test 9: docsync list-deferred"
docsync list-deferred || true
echo

echo "Test 10: docsync check --format json"
timeout 5 docsync check --format json || echo "Command completed or timed out"
echo

echo "Test 11: docsync check --create-todo"
timeout 5 docsync check --create-todo || echo "Command completed or timed out"
if [ -f .docsync-todo.json ]; then
    echo "✓ .docsync-todo.json created:"
    cat .docsync-todo.json
else
    echo "✗ .docsync-todo.json not created"
fi
echo

echo "Test 12: docsync coverage --format json"
docsync coverage --format json || true
echo

# Cleanup
cd /
rm -rf "$TEST_DIR"

echo "=== All tests completed ==="
