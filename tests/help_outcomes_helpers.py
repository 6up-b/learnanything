"""What other test files use from ``tests/test_help_outcomes.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
from contextlib import closing
from pathlib import Path

from learnloop.db.connection import connect
from learnloop.db.stores.help_assists import insert_assist
from learnloop.db.stores.judgments import append_judgment
from learnloop.workbench.help_outcomes import item_facets_of

from tests.approach_map_fakes import EXPECTED, ITEM, add_attempt
from tests.workbench_help_fakes import open_problem, sidecar


FACET = "recall"


def _at(minutes: int) -> str:
    hour, minute = divmod(minutes, 60)
    return f"2026-10-20T{10 + hour:02d}:{minute:02d}:00Z"


def _row(assist_id: str, session: str, kind: str, minutes: int, **values):
    row = {"id": assist_id, "surface": "workbench", "assist_kind": kind, "practice_item_id": ITEM,
           "practice_item_hash": "h", "workbench_session_id": session, "chooser": "none", "shown": 1,
           "counted_by": "server" if kind in ("check", "hint") else None, "requested_at": _at(minutes),
           "shown_at": _at(minutes)}
    row.update(values)
    return row


def _verdicts(*valid: str, questionable: str | None = None, hashes: dict[str, str] | None = None) -> str:
    hashes = hashes or {}
    rows = [{"chain_id": chain, "verdict": "valid", "hash": hashes.get(chain, f"h_{chain}")} for chain in valid]
    if questionable:
        rows.append({"chain_id": questionable, "verdict": "questionable",
                     "hash": hashes.get(questionable, f"h_{questionable}")})
    return json.dumps(rows)


def _snapshot(*chains: str, hashes: dict[str, str] | None = None) -> str:
    """A row's ``step_snapshot_json`` as the workbench writes it (ids, hashes)."""

    hashes = hashes or {}
    return json.dumps([{"chain_id": chain, "number": index, "hash": hashes.get(chain, f"h_{chain}")}
                       for index, chain in enumerate(chains, start=1)])


def _insert(paths, rows) -> None:
    with closing(connect(paths.sqlite_path)) as connection:
        for row in rows:
            insert_assist(connection, row)
        connection.commit()


def _world(tmp_path: Path):
    """One problem: a check (step 2 questionable, an invalid-algebra guess), a
    level-3 worked-parallel hint, a later check where step 2 now holds; a
    second hint followed by another hint before the next check; a third hint
    with no later check. The problem is submitted correct; an independent
    attempt on the facet follows an hour later."""

    paths, ctx, _session = sidecar(tmp_path)
    wb, chains = open_problem(ctx)
    one, two = chains
    add_attempt(paths.sqlite_path, "att_wb", correctness=1.0, created_at="2026-10-20T11:00:00+00:00")
    add_attempt(paths.sqlite_path, "att_later", correctness=1.0, created_at="2026-10-20T12:00:00+00:00")
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE practice_attempts SET hints_used = 2 WHERE id = 'att_wb'")
        connection.execute("UPDATE workbench_sessions SET attempt_id = 'att_wb', status = 'submitted' WHERE id = ?",
                           (wb,))
        connection.commit()
    # Step 2 is rewritten after the first hint (its hash changes), so the
    # second check's valid step 2 is new since that hint's delivery.
    edited = {two: "h_two_edited"}
    _insert(paths, [
        _row("ha_c1", wb, "check", 0, step_verdicts_json=_verdicts(one, questionable=two),
             step_snapshot_json=_snapshot(one, two), first_questionable_step_id=two,
             error_kind_guess="invalid_algebra"),
        _row("ha_h1", wb, "hint", 1, hint_kind="worked_parallel", level=3, strategy="cdf_first",
             attempt_id="att_wb", about_step_id=two, step_snapshot_json=_snapshot(one, two)),
        _row("ha_c2", wb, "check", 2, step_verdicts_json=_verdicts(one, two, hashes=edited),
             step_snapshot_json=_snapshot(one, two, hashes=edited)),
        _row("ha_h2", wb, "hint", 3, hint_kind="waypoint", level=3, strategy="P = 1/4 at the edge",
             attempt_id="att_wb", step_snapshot_json=_snapshot(one, two, hashes=edited)),
        _row("ha_h3", wb, "hint", 4, hint_kind="next_step", level=2, attempt_id="att_wb",
             step_snapshot_json=_snapshot(one, two, hashes=edited)),
        _row("ha_c3", wb, "check", 5, step_verdicts_json=_verdicts(one, two, hashes=edited),
             step_snapshot_json=_snapshot(one, two, hashes=edited)),
        _row("ha_h4", wb, "hint", 6, hint_kind="localize", level=2, attempt_id="att_wb",
             step_snapshot_json=_snapshot(one, two, hashes=edited)),
    ])
    with closing(connect(paths.sqlite_path)) as connection:
        append_judgment(connection, task="hint_fit", left_kind="help_assist", left_id="ha_h3", judge="learner_card",
                        input_hash="x", verdict="different", rationale=json.dumps({"shortcut": "too_big"}),
                        created_at=_at(4))
        connection.execute(
            "INSERT INTO attempt_diagnoses (id, attempt_id, diagnosis_prompt_version, mode, history_mode, status, "
            "proposal_json, created_at) VALUES ('dg_1', 'att_wb', 'v', 'live', 'full', 'completed', ?, ?)",
            (json.dumps({"analysis_md": f"They wrote {EXPECTED}", "event_diagnoses": [
                {"event_index": 0, "causal_class": "learner_state", "operation": "apply_cdf_boundary",
                 "misconception_statement": "adds one to a probability",
                 "registry_match": {"kind": "durable", "id": "mc_cdf_plus_one"}}]}), "2026-10-20T11:00:30Z"))
        connection.commit()
    return paths, ctx, wb


def _facets(paths):
    from learnloop.vault.loader import load_vault

    return item_facets_of(load_vault(paths.root))


def _vault(paths):
    from learnloop.vault.loader import load_vault

    return load_vault(paths.root)


def _only(result, help_: str, kind: str | None = None):
    [found] = [entry for entry in result.helps if entry.help == help_ and (kind is None or entry.kind == kind)]
    return found


def _grading(paths, attempt_id: str, *, points: float, at: str, revision: int, superseded_at: str | None = None,
             contract: str | None = "acv_1") -> None:
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO grading_evidence (id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, "
            "superseded_at, grading_revision, assessment_contract_version_id) VALUES (?, ?, 'c1', ?, 1, ?, ?, ?, ?)",
            (f"ge_{attempt_id}_{revision}", attempt_id, points, at, superseded_at, revision, contract))
        connection.commit()
