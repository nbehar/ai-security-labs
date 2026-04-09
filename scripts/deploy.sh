#!/bin/bash
# Deploy a Space to its HuggingFace remote
# Usage: ./scripts/deploy.sh owasp-top-10

set -e

SPACE=$1
if [ -z "$SPACE" ]; then
  echo "Usage: ./scripts/deploy.sh <space-name>"
  echo "Available spaces:"
  ls -1 spaces/
  exit 1
fi

SPACE_DIR="spaces/$SPACE"
if [ ! -d "$SPACE_DIR" ]; then
  echo "Error: Space not found: $SPACE_DIR"
  exit 1
fi

# Copy shared framework into space build context
echo "Building $SPACE..."
if [ -d "framework/static" ]; then
  cp -r framework/static/css/* "$SPACE_DIR/static/css/" 2>/dev/null || true
  # Don't overwrite space-specific JS — only copy core files
  cp framework/static/js/app-core.js "$SPACE_DIR/static/js/" 2>/dev/null || true
  cp framework/static/js/i18n-core.js "$SPACE_DIR/static/js/" 2>/dev/null || true
fi
if [ -f "framework/scanner.py" ]; then
  cp framework/scanner.py "$SPACE_DIR/" 2>/dev/null || true
fi

echo "Deploying $SPACE to HuggingFace..."
cd "$SPACE_DIR"

# Initialize git if needed (for first deploy)
if [ ! -d ".git" ]; then
  git init
  echo "Note: Add HF remote with: git remote add hf https://huggingface.co/spaces/nikobehar/<space-name>"
fi

git add -A
git commit -m "Deploy from ai-security-labs monorepo" 2>/dev/null || echo "No changes to commit"
git push hf main 2>/dev/null || echo "Push failed — check HF remote is configured"

echo "Done: $SPACE deployed."
