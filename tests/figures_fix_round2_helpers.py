"""What other test files use from ``tests/test_figures_fix_round2.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import re

from learnloop.diagnosis.text_gaps.jobs import process_next_gap_job


def _job_rows(repository):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT source_kind, source_id, state, last_error FROM learner_text_gap_jobs ORDER BY created_at, id")]


def _drain(root, repository, clients):
    outcomes = []
    while (outcome := process_next_gap_job(root, repository, owner="t", clients=clients)) is not None:
        outcomes.append(outcome)
    return outcomes


def _gaps_switch(paths, enabled: bool) -> None:
    config = paths.root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    value = "true" if enabled else "false"
    section = re.search(r"(?ms)^\[learner_text_gaps\]\n(.*?)(?=^\[|\Z)", text)
    if section is None:
        text = text.rstrip("\n") + f"\n\n[learner_text_gaps]\nenabled = {value}\n"
    elif re.search(r"(?m)^enabled = ", section.group(1)):
        body = re.sub(r"(?m)^enabled = \w+", f"enabled = {value}", section.group(1), count=1)
        text = text[:section.start(1)] + body + text[section.end(1):]
    else:
        text = text[:section.start(1)] + f"enabled = {value}\n" + text[section.start(1):]
    config.write_text(text, encoding="utf-8")
