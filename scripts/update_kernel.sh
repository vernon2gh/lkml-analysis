#!/bin/bash
# Update Linux kernel mainline to latest.
# Usage: ./update_kernel.sh
# Kernel repo: ~/linux

set -e
LINUX_DIR="${LINUX_DIR:-$HOME/linux}"

echo "==> Updating Linux kernel mainline..."
cd "$LINUX_DIR"

BEFORE=$(git log --oneline -1)
git fetch origin
git pull origin master
AFTER=$(git log --oneline -1)

echo "    Before: $BEFORE"
echo "    After:  $AFTER"

if [ "$BEFORE" = "$AFTER" ]; then
    echo "    Already up to date."
else
    NEW=$(git log --oneline "${BEFORE%% *}..HEAD" | wc -l)
    echo "    $NEW new commits pulled."
fi
