#!/bin/bash
#
# Create testbed repository for docsync integration testing
# This script is idempotent - it removes and recreates the testbed each time
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TESTBED="$PROJECT_ROOT/testbed"

echo "Creating testbed at: $TESTBED"

# Remove existing testbed
if [ -d "$TESTBED" ]; then
    echo "Removing existing testbed..."
    rm -rf "$TESTBED"
fi

# Create testbed directory
mkdir -p "$TESTBED"
cd "$TESTBED"

# Initialize git repo
git init
git config user.name "Docsync Test"
git config user.email "test@docsync.test"

# Create pyproject.toml with docsync config
cat > pyproject.toml << 'EOF'
[project]
name = "testbed"
version = "0.1.0"

[tool.docsync]
mode = "block"
transitive_depth = 1
enforce_symmetry = true

require_links = [
    "src/api/**/*.py",
    "src/models/**/*.py",
    "src/core/**/*.py",
    "src/workers/**/*.py",
]

exempt = [
    "**/__init__.py",
    "**/*_test.py",
    "**/test_*.py",
    "**/conftest.py",
]

doc_paths = [
    "docs/**/*.md",
    "README.md",
]
EOF

# Create directory structure
mkdir -p src/api src/models src/core src/workers docs

# Create __init__.py files
touch src/__init__.py
touch src/api/__init__.py
touch src/models/__init__.py
touch src/core/__init__.py
touch src/workers/__init__.py

# Create src/core/permissions.py (leaf node - no imports)
cat > src/core/permissions.py << 'EOF'
# docsync: docs/permissions.md
"""Permission checking module."""


def check_permission(user: str, action: str) -> bool:
    """Check if user has permission for action."""
    # Simplified permission logic
    return user != "guest"
EOF

# Create src/core/cache.py (leaf node - no imports, no dependents)
cat > src/core/cache.py << 'EOF'
# docsync: docs/architecture.md
"""Caching module."""


class Cache:
    """Simple cache implementation."""

    def __init__(self):
        self._data = {}

    def get(self, key: str):
        """Get value from cache."""
        return self._data.get(key)

    def set(self, key: str, value):
        """Set value in cache."""
        self._data[key] = value
EOF

# Create src/models/user.py (imports from core.permissions)
cat > src/models/user.py << 'EOF'
# docsync: docs/models.md
"""User model."""

from src.core.permissions import check_permission


class User:
    """User class."""

    def __init__(self, username: str):
        self.username = username

    def can(self, action: str) -> bool:
        """Check if user can perform action."""
        return check_permission(self.username, action)
EOF

# Create src/api/auth.py (imports from core.permissions)
cat > src/api/auth.py << 'EOF'
# docsync: docs/authentication.md
"""Authentication module."""

from src.core.permissions import check_permission


def authenticate(username: str, password: str) -> bool:
    """Authenticate a user."""
    # Simplified for testing
    return check_permission(username, "login")


def verify_token(token: str) -> dict:
    """Verify a JWT token."""
    return {"user": "test", "valid": True}
EOF

# Create src/api/users.py (NO docsync header - orphaned code)
# Imports from models.user and core.permissions
cat > src/api/users.py << 'EOF'
"""User API endpoints."""

from src.core.permissions import check_permission
from src.models.user import User


def get_user(username: str) -> User:
    """Get user by username."""
    return User(username)


def list_users() -> list[User]:
    """List all users."""
    return [User("admin"), User("user")]
EOF

# Create src/api/routes.py (imports from api.auth and api.users)
cat > src/api/routes.py << 'EOF'
# docsync: docs/api-guide.md
"""API route definitions."""

from src.api.auth import authenticate, verify_token
from src.api.users import get_user


def login_route(request: dict) -> dict:
    """Handle login."""
    auth = authenticate(request["username"], request["password"])
    return {"authenticated": auth}


def user_route(request: dict) -> dict:
    """Handle user lookup."""
    token = verify_token(request["token"])
    return get_user(token["user"])
EOF

# Create src/api/middleware.py (imports from api.auth)
cat > src/api/middleware.py << 'EOF'
# docsync: docs/api-guide.md
"""API middleware."""

from src.api.auth import verify_token


def auth_middleware(request: dict) -> bool:
    """Verify authentication for request."""
    token = request.get("token")
    if not token:
        return False
    result = verify_token(token)
    return result.get("valid", False)
EOF

# Create src/workers/email_worker.py (imports from models.user and api.auth)
cat > src/workers/email_worker.py << 'EOF'
# docsync: docs/workers.md
"""Email worker for background jobs."""

from src.api.auth import verify_token
from src.models.user import User


def send_email(user: User, subject: str, body: str) -> bool:
    """Send email to user."""
    # Simplified email sending
    print(f"Sending to {user.username}: {subject}")
    return True


def send_notification(token: str, message: str) -> bool:
    """Send notification to authenticated user."""
    result = verify_token(token)
    if result.get("valid"):
        user = User(result["user"])
        return send_email(user, "Notification", message)
    return False
EOF

# Create docs/authentication.md (links back to src/api/auth.py)
cat > docs/authentication.md << 'EOF'
<!-- docsync: src/api/auth.py -->
# Authentication

This module handles user authentication and token verification.

## Functions

- `authenticate(username, password)`: Authenticates a user
- `verify_token(token)`: Verifies a JWT token
EOF

# Create docs/api-guide.md (links to src/api/routes.py and src/api/middleware.py)
cat > docs/api-guide.md << 'EOF'
<!-- docsync: src/api/routes.py, src/api/middleware.py -->
# API Guide

This document describes the API routes and middleware.

## Routes

- `/login`: User login endpoint
- `/user`: Get user information

## Middleware

- `auth_middleware`: Verifies authentication for requests
EOF

# Create docs/permissions.md (links back to src/core/permissions.py)
cat > docs/permissions.md << 'EOF'
<!-- docsync: src/core/permissions.py -->
# Permissions

Permission checking system.

## Functions

- `check_permission(user, action)`: Check if user has permission
EOF

# Create docs/architecture.md (links to src/core/cache.py)
cat > docs/architecture.md << 'EOF'
<!-- docsync: src/core/cache.py -->
# Architecture

System architecture overview.

## Caching

The system uses an in-memory cache for performance.
EOF

# Create docs/models.md (links to src/models/user.py)
cat > docs/models.md << 'EOF'
<!-- docsync: src/models/user.py -->
# Data Models

Data model documentation.

## User Model

Represents a user in the system.
EOF

# Create docs/workers.md (links to src/workers/email_worker.py)
cat > docs/workers.md << 'EOF'
<!-- docsync: src/workers/email_worker.py -->
# Background Workers

Background job workers.

## Email Worker

Handles email sending in the background.
EOF

# Create docs/stale-guide.md (orphaned doc - links to non-existent file)
cat > docs/stale-guide.md << 'EOF'
<!-- docsync: src/api/old_module.py -->
# Old Module Guide

Documentation for a module that no longer exists.
EOF

# Create docs/asymmetric-doc.md (asymmetric link - permissions.py doesn't link back)
cat > docs/asymmetric-doc.md << 'EOF'
<!-- docsync: src/core/permissions.py -->
# Asymmetric Documentation

This doc links to permissions.py, but permissions.py doesn't link back.
EOF

# Create README.md (links to src/api/routes.py)
cat > README.md << 'EOF'
<!-- docsync: src/api/routes.py -->
# Testbed Project

This is a test project for docsync integration testing.
EOF

# Make initial commit
git add -A
git commit -m "Initial commit: testbed setup"

# Modify src/core/permissions.py (to create staleness)
# Add a new function without updating the doc
cat >> src/core/permissions.py << 'EOF'


def check_admin(user: str) -> bool:
    """Check if user is admin."""
    return user == "admin"
EOF

# Commit the change (docs/permissions.md is now stale)
git add src/core/permissions.py
git commit -m "Add check_admin function to permissions.py"

echo ""
echo "✓ Testbed created successfully at: $TESTBED"
echo ""
echo "File structure:"
echo "  - src/core/permissions.py (leaf, modified in 2nd commit)"
echo "  - src/core/cache.py (leaf, no dependents)"
echo "  - src/models/user.py (imports permissions.py)"
echo "  - src/api/auth.py (imports permissions.py)"
echo "  - src/api/users.py (NO DOCSYNC HEADER - orphaned)"
echo "  - src/api/routes.py (imports auth.py, users.py)"
echo "  - src/api/middleware.py (imports auth.py)"
echo "  - src/workers/email_worker.py (imports auth.py, user.py)"
echo ""
echo "Dependency chain:"
echo "  permissions.py ← auth.py, users.py, user.py"
echo "                ← routes.py, middleware.py, email_worker.py (depth 2)"
echo ""
echo "Special cases:"
echo "  - docs/stale-guide.md: orphaned doc (links to missing file)"
echo "  - src/api/users.py: orphaned code (no docsync header)"
echo "  - docs/asymmetric-doc.md: asymmetric link"
echo "  - docs/permissions.md: stale (permissions.py modified after)"
echo ""
