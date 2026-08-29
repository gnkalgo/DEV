#!/usr/bin/env bash
# Push the current feature branch to GitHub (run from a machine with GitHub access).
set -euo pipefail

BRANCH="${BRANCH:-cursor/gnkalgo-platform-1a67}"
REMOTE="${REMOTE:-origin}"

cd "$(git rev-parse --show-toplevel)"

echo "==> Pushing ${BRANCH} to ${REMOTE}"
git push -u "${REMOTE}" "${BRANCH}"

echo "==> PR compare:"
echo "https://github.com/riyazgagguturi-design/gnkalgo_Dev/compare/main...${BRANCH}?expand=1"
