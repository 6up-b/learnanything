#!/bin/bash
# Refactor step T1, reproducible: from a tree whose test files still import each other, move what they share
# into tests/<topic>_helpers.py. Resets tests/ to HEAD first (and deletes untracked files there), so run it
# only on a clean tree. Writes its plan and logs under fixtures-local/t1/ (gitignored).
#   pipeline.sh <ref-or-dir>   the ref (or a directory) to take tests/test_test_layout.py and
#                              tests/test_affected_tests.py from: the T1 commit
set -euo pipefail
TOOLS=$(cd "$(dirname "$0")" && pwd)
cd "$(git -C "$TOOLS" rev-parse --show-toplevel)"
mkdir -p fixtures-local/t1
git checkout -- tests
git ls-files --others --exclude-standard tests | xargs -r rm --
uv run python "$TOOLS/t1_move.py" apply | grep -v '^"\|^\[\|^\]\|^suspects\|^}'
# Names a helper only re-exports (an importer took them from the donor, which imported them): point the importer
# at the defining module instead, then prune what the move left unused.
old_helpers=(router_mixture_helpers followup_serve_helpers diagnosis_split_helpers split_live_helpers mobile_host_helpers)
uv run ruff check --select F401 --output-format json $(ls tests/*_helpers.py | grep -v -F "${old_helpers[@]/#/-e}") \
  > fixtures-local/t1/reexports.json || true
uv run python "$TOOLS/t1_redirect.py" > fixtures-local/t1/redirect.log
uv run ruff check --select F401 --output-format concise tests | grep -oE "^tests/[a-z0-9_]+\.py" | sort -u \
  > fixtures-local/t1/f401files.txt || true
[ -s fixtures-local/t1/f401files.txt ] && uv run ruff check --select F401 --fix $(cat fixtures-local/t1/f401files.txt) | tail -1
uv run python "$TOOLS/t1_patches.py"
uv run python "$TOOLS/t1_tidy.py"
if [ -d "$1" ]; then
  cp "$1/test_test_layout.py" "$1/test_affected_tests.py" tests/
else
  git checkout "$1" -- tests/test_test_layout.py tests/test_affected_tests.py
fi
uv run ruff check | tail -1
