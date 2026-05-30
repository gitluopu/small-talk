#!/bin/bash
set -euo pipefail

OPEN_ISSUES=$(gh issue list --state open --json number --jq 'length')

if [ "$OPEN_ISSUES" -eq 0 ]; then
  echo "No open issues."
  exit 0
fi

echo "Found $OPEN_ISSUES open issue(s). Invoking small-talk agent..."

claude -p "拉取并评论 open issue" \
  --agent small-talk \
  --dangerously-skip-permissions
