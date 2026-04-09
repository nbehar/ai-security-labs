#!/bin/bash
# Deploy a Space to its HuggingFace remote
# Usage: ./scripts/deploy.sh owasp-top-10
#
# This script copies the shared framework into the Space's build context
# before pushing to HF. Space-specific files are never overwritten.

set -e

SPACE=$1
if [ -z "$SPACE" ]; then
  echo "Usage: ./scripts/deploy.sh <space-name>"
  echo ""
  echo "Available spaces:"
  ls -1 spaces/
  exit 1
fi

SPACE_DIR="spaces/$SPACE"
if [ ! -d "$SPACE_DIR" ]; then
  echo "Error: Space not found: $SPACE_DIR"
  exit 1
fi

echo "=== Building $SPACE ==="

# 1. Copy shared CSS (always overwrite — framework is source of truth)
if [ -f "framework/static/css/styles.css" ]; then
  mkdir -p "$SPACE_DIR/static/css"
  cp framework/static/css/styles.css "$SPACE_DIR/static/css/styles.css"
  echo "  Copied: framework CSS"
fi

# 2. Copy shared JS core (don't overwrite space-specific app.js)
if [ -d "framework/static/js" ]; then
  mkdir -p "$SPACE_DIR/static/js"
  cp framework/static/js/core.js "$SPACE_DIR/static/js/core.js" 2>/dev/null && echo "  Copied: core.js" || true
fi

# 3. Copy shared Python modules
for pyfile in framework/scoring.py framework/groq_client.py framework/scanner.py; do
  if [ -f "$pyfile" ]; then
    cp "$pyfile" "$SPACE_DIR/$(basename $pyfile)"
    echo "  Copied: $(basename $pyfile)"
  fi
done

echo ""
echo "=== Deploying $SPACE to HuggingFace ==="
cd "$SPACE_DIR"

# Initialize git if needed
if [ ! -d ".git" ]; then
  git init
  git config user.name "Nikolas"
  git config user.email "nbehar@users.noreply.github.com"
  echo "Note: Add HF remote with:"
  echo "  git remote add hf https://huggingface.co/spaces/nikobehar/<space-name>"
fi

git add -A
git commit -m "Deploy from ai-security-labs monorepo ($(date +%Y-%m-%d))" 2>/dev/null || echo "No changes to commit"
git push hf main 2>/dev/null || echo "Push failed — check HF remote is configured"

echo ""
echo "Done: $SPACE deployed."
