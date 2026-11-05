"""FG1d: a generated probe's answer, live against replay.

The desktop submits a generated probe's answer with its ``probePresentationId``
(``PracticeScreen.tsx``). That answer's calibrated grade interpretation is written by
the probe-episode path, after the attempt's own canonical projection had run, so live
banked the answer with zero reliable mass (the probe item's ``method_selection`` cells
at alpha 1, beta 1, raw mass 0) while replay, reading the interpretation off the
ledger, banked 0.3678. A later projection (the diagnosis job, the next attempt, a
rebuild) hid it. ``rebuild --shadow`` now reads 0/0/0 straight after the answer, on
every door the answer can come through.

The clock is frozen at a whole second: a live write at a sub-second instant against
replay's whole second is R14, a known difference of its own, and not this one.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from learnloop.algorithm_versions import FOLLOWUP_SERVE_ALGORITHM_VERSION, INTERVAL_FACTOR_ALGORITHM_VERSION
from learnloop.clock import SystemClock
from learnloop.diagnosis.split.jobs import drain
from learnloop.followup_serve import workflow as wf
from learnloop.substrate.replay import rebuild_derived_state
from learnloop.substrate.shadow_rebuild import shadow_rebuild
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext

from tests.followup_serve_helpers import BlindRivalClient, live_shape_vault
from tests.test_followup_rival_factor import _Ready, _call, _generate, _miss

ZERO = {"mastery": 0, "facet": 0, "schedule": 0}
INSTANT = datetime(2026, 11, 4, 15, 0, 0, tzinfo=UTC)


def _summary(result):
    assert result.live_database_unchanged
    return result.learner_state_diff["summary"]


@pytest.fixture(params=[FOLLOWUP_SERVE_ALGORITHM_VERSION, INTERVAL_FACTOR_ALGORITHM_VERSION])
def desk(tmp_path, monkeypatch, request):
    # FG1's tag and RO1's successor: neither changes the fold, so the answer holds at both.
    monkeypatch.setattr(SystemClock, "now", lambda self: INSTANT)
    paths, vault, repository = live_shape_vault(tmp_path, version=request.param)
    # The seeded vault predates the tag: rebuild it, as the owner does after an upgrade, so the
    # shadow starts at 0/0/0 and whatever it reads afterwards is the journey's.
    rebuild_derived_state(vault, repository)
    assert _summary(shadow_rebuild(load_vault(paths.root))) == ZERO
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.post_attempt_worker.autostart = False
    client = BlindRivalClient()
    monkeypatch.setattr("learnloop_sidecar.handlers.practice.ready_grading_provider",
                        lambda *_a, **_k: ("fake", _Ready(), client))
    session = _call(ctx, "start_session", {"available_minutes": 30})
    return SimpleNamespace(ctx=ctx, client=client, session=session.get("sessionId") or session["session_id"], paths=paths)


def _probe_cells(repository, item_id):
    return [row for row in repository.canonical_facet_recall_states() if row.practice_item_id == item_id]


def _answer_generated_probe(desk, *, door: str, with_presentation: bool = True):
    attempt_id = _miss(desk, "")
    _generate(desk)
    desk.ctx.reload(maintenance=False)
    vault, repository = desk.ctx.require_vault()
    row = wf.attempt_workflow(repository, attempt_id)
    assert row["state"] == wf.READY and row["practice_item_id"]
    if door == "exam":
        # As an exam sitting's pipeline opens one: origin exam, nothing held.
        with repository.connection() as connection:
            connection.execute("UPDATE followup_workflows SET origin = 'exam', feedback_held = 0 WHERE id = ?",
                               (row["id"],))
    if door == "show_anyway":
        assert _call(desk.ctx, "followup_show_anyway", {"attemptId": attempt_id})["released"] is True
    _call(desk.ctx, "followup_next", {"attemptId": attempt_id})
    _call(desk.ctx, "open_queue_item", {"practiceItemId": row["practice_item_id"]})
    contract = _call(desk.ctx, "get_probe_contract", {"practiceItemId": row["practice_item_id"]})
    _call(desk.ctx, "submit_attempt", {
        "sessionId": desk.session, "practiceItemId": row["practice_item_id"], "answerMd": "An answer.",
        "attemptType": "diagnostic_probe", "latencySeconds": 40,
        "probePresentationId": contract["presentationId"] if with_presentation else None,
    })
    return attempt_id, row, vault, repository


@pytest.mark.parametrize("door", ["held", "show_anyway", "exam"])
def test_a_generated_probes_answer_on_its_presentation_reads_zero_in_the_shadow(desk, door):
    _attempt_id, row, _vault, repository = _answer_generated_probe(desk, door=door)
    # The answer is evidence from the first serve (FG1 §4.1): its cells carry mass now, not after
    # some later projection.
    cells = _probe_cells(repository, row["practice_item_id"])
    assert cells and all(cell.raw_coverage_mass > 0 for cell in cells), cells
    assert _summary(shadow_rebuild(load_vault(desk.paths.root))) == ZERO
    observation = repository.causal_discriminating_observations(factor_id=row["factor_id"])
    assert observation and observation[0]["admissible_as_independent"] == (0 if door == "show_anyway" else 1)
    assert wf.get(repository, row["id"])["state"] == wf.SETTLED


def test_the_diagnosis_job_after_the_answer_changes_nothing_further(desk):
    _attempt_id, row, vault, repository = _answer_generated_probe(desk, door="held")
    before = _probe_cells(repository, row["practice_item_id"])
    drain(vault, repository, client_factory=lambda: desk.client, embedding_factory=lambda: None)
    assert _probe_cells(repository, row["practice_item_id"]) == before
    assert _summary(shadow_rebuild(load_vault(desk.paths.root))) == ZERO


def _canonical_cells(repository):
    """Both canonical belief tables by value: the shadow compares the recall cells only."""

    def values(row):
        return {key: value for key, value in asdict(row).items() if key not in ("id", "created_at", "updated_at")}

    recall = sorted(repr(sorted(values(row).items())) for row in repository.canonical_facet_recall_states())
    capability = sorted(repr(sorted(values(row).items())) for row in repository.facet_capability_evidence_all())
    return recall, capability


def test_the_capability_cell_the_answer_feeds_agrees_with_a_rebuild_too(desk):
    """The same stale fold left the probe's (facet, method_selection) capability cell at zero mass;
    ``rebuild --shadow`` doesn't compare that table, so a real rebuild does here."""

    _attempt_id, row, _vault, repository = _answer_generated_probe(desk, door="held")
    live = _canonical_cells(repository)
    rebuild_derived_state(load_vault(desk.paths.root), repository)
    assert _canonical_cells(repository) == live


def test_an_answer_without_its_presentation_is_incidental_on_both_sides(desk):
    """No presentation, no probe observation and no interpretation: the answer is incidental
    evidence with zero reliable mass, live and in replay alike."""

    _attempt_id, row, _vault, repository = _answer_generated_probe(desk, door="held", with_presentation=False)
    assert all(cell.raw_coverage_mass == 0 for cell in _probe_cells(repository, row["practice_item_id"]))
    assert _summary(shadow_rebuild(load_vault(desk.paths.root))) == ZERO
