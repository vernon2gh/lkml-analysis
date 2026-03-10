#!/bin/bash
# Apply a kernel patch series to a test branch for deeper code analysis.
#
# Usage:
#   ./apply_patches.sh <message-id> [branch-name]
#
# Environment:
#   MAILDIR    - path to the subsystem maildir (required, or falls back to mm default)
#   LINUX_DIR  - path to kernel repo (default: ~/linux)
#
# Examples:
#   MAILDIR=~/Mail/lei/sched ./apply_patches.sh "20260302123456.12345-0-author@example.com"
#   MAILDIR=~/Mail/lei/mm ./apply_patches.sh "20260302123456.12345-0-author@example.com" test/mm-ampress

set -e

MSGID="${1:?Usage: $0 <message-id> [branch-name]}"
LINUX_DIR="${LINUX_DIR:-$HOME/linux}"
MAILDIR="${MAILDIR:-$HOME/Mail/lei/mm}"
DATE_TAG=$(date +%Y-%m)

# Derive subsystem name from maildir path for the default branch name
SUBSYS=$(basename "$MAILDIR")
BRANCH="${2:-analysis/${SUBSYS}-${DATE_TAG}}"
MBOX_TMP=$(mktemp /tmp/patches-XXXXXX.mbox)

echo "==> Linux repo: $LINUX_DIR"
echo "==> Maildir:    $MAILDIR"
echo "==> Branch:     $BRANCH"
echo "==> Message-ID: $MSGID"

# Step 1: Update mainline
echo ""
echo "==> Updating mainline (git fetch)..."
cd "$LINUX_DIR"
git fetch origin --quiet
echo "    Latest: $(git log --oneline -1 origin/master)"

# Step 2: Create / reset test branch
echo ""
echo "==> Creating branch '$BRANCH' from origin/master..."
if git show-ref --quiet "refs/heads/$BRANCH"; then
    echo "    Branch exists, deleting and recreating..."
    git branch -D "$BRANCH"
fi
git checkout -b "$BRANCH" origin/master --quiet
echo "    Done."

# Step 3: Export patch series via lei
echo ""
echo "==> Exporting patch series via lei..."
lei q -f mbox -o "$MBOX_TMP" "m:$MSGID or rt:$MSGID" 2>/dev/null || \
    lei q -f mbox -o "$MBOX_TMP" "s:$(echo $MSGID | cut -d@ -f1)" 2>/dev/null || true

if [ ! -s "$MBOX_TMP" ]; then
    echo "    lei export failed or empty, trying direct maildir search..."
    grep -rl "$MSGID" "$MAILDIR/cur" "$MAILDIR/new" 2>/dev/null | head -1 | \
        xargs -I{} formail -s sh -c 'cat >> '"$MBOX_TMP" 2>/dev/null || true
fi

if [ ! -s "$MBOX_TMP" ]; then
    echo "    ERROR: Could not find patches for Message-ID: $MSGID"
    echo "    Try running: lei q -f mbox 'm:$MSGID'"
    git checkout master --quiet
    git branch -D "$BRANCH" 2>/dev/null || true
    rm -f "$MBOX_TMP"
    exit 1
fi

PATCH_COUNT=$(grep -c '^From ' "$MBOX_TMP" 2>/dev/null || echo 0)
echo "    Found $PATCH_COUNT emails in mbox."

# Step 4: Apply patches
echo ""
echo "==> Applying patches with git am..."
git am --keep-cr --scissors "$MBOX_TMP" 2>&1 | grep -v "^Applying:" || \
    git am --abort 2>/dev/null || true

echo ""
echo "==> Applied patches:"
git log --oneline "origin/master..HEAD"

rm -f "$MBOX_TMP"
echo ""
echo "==> Done! Branch '$BRANCH' is ready."
echo "    To cleanup: git checkout master && git branch -D '$BRANCH'"
