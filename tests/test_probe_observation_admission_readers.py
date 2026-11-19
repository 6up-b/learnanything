"""Every reader of a probe observation's admission flags is listed with the reading it uses.

A probe observation's ``updates_belief`` and ``eligible_for_completion`` are a receipt of how its answer was
recorded. From mvp-0.61 the episode reads a stored row through ``probe_episodes.effective_episode_observations``
(an exposed answer recorded below the tag updates no belief and qualifies nothing; refactor bug ledger G3-1, T61-1 to
T61-3), so a new reader of the stored flags can quietly bring an exposed answer back into a current decision. This test
finds every line under ``src/`` that names either field and fails on a file not listed below, or on a count that
changed, so a new reader is reviewed before it lands (the pattern of ``tests/test_sqlite_file_copies.py``). The record
``docs/reviews/algorithm-mvp-0.61.md`` ("Adversarial review and fix round") lists the same readers.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
FIELD = re.compile(r"\b(?:eligible_for_completion|updates_belief)\b")

_STORAGE = "storage: writes or decodes the stored row (the receipt), no decision reads it here"
_EFFECTIVE = "reads the episode's effective view (effective_episode_observations), so an exposure counts as no update"

#: file -> (lines naming a field, the reading it uses and why).
READERS: dict[str, tuple[int, str]] = {
    "src/learnloop/adaptive_difficulty/column_classes.py": (1, "metadata: the column inventory, no reading"),
    "src/learnloop/db/records.py": (4, _STORAGE),
    "src/learnloop/db/repositories.py": (
        1, "stored session count (held excluded); read below the tag only, through "
           "probe_episodes.effective_qualifying_total, which re-reads each row at the tag"),
    "src/learnloop/db/stores/probes.py": (
        8, "storage, and the stored qualifying counts and attempt ids that effective_qualifying_total reads below and "
           "re-reads at the tag"),
    "src/learnloop/held_grades.py": (3, "the held-grade overlay beneath the effective view (a held grade updates nothing)"),
    "src/learnloop/diagnosis/probe_episodes.py": (9, "defines the effective view, its posterior and its counts"),
    "src/learnloop/diagnosis/probe_evidence.py": (4, "the live writer: sets the flags it records (the receipt)"),
    "src/learnloop/diagnosis/probe_completion.py": (3, _EFFECTIVE),
    "src/learnloop/diagnosis/probe_blocks.py": (2, _EFFECTIVE),
    "src/learnloop/diagnosis/calibration_sessions.py": (1, _EFFECTIVE),
    "src/learnloop/diagnosis/diagnostic_pack.py": (
        3, "the baseline projection: the effective view with the vault, the repository's rows without one"),
    "src/learnloop/diagnosis/probe_audit.py": (
        3, "the EIG calibration sample and the replication report read the effective view; the determinism "
           "report verifies each recorded transition against its own receipt on purpose"),
    "src/learnloop_sidecar/handlers/inspector.py": (2, "shows the effective flags, the exposure reason and the recorded entropies"),
}


def _current() -> Counter[str]:
    found: Counter[str] = Counter()
    for root in ("src",):
        for path in sorted((REPOSITORY / root).rglob("*.py")):
            relative = path.relative_to(REPOSITORY).as_posix()
            for line in path.read_text(encoding="utf-8").splitlines():
                if FIELD.search(line):
                    found[relative] += 1
    return found


def test_every_reader_of_the_admission_flags_is_listed() -> None:
    current = _current()
    listed = {path: count for path, (count, _reason) in READERS.items()}
    unlisted = sorted(set(current) - set(listed))
    stale = sorted(set(listed) - set(current))
    changed = sorted(path for path in set(current) & set(listed) if current[path] != listed[path])
    assert not unlisted, f"new readers of the probe observation's admission flags (list them, with their reading): {unlisted}"
    assert not stale, f"listed readers that no longer name the flags (remove them): {stale}"
    assert not changed, {path: (listed[path], current[path]) for path in changed}


def test_every_listed_reader_says_which_reading_it_uses() -> None:
    assert all(reason.strip() for _count, reason in READERS.values())
