"""FG1d: the marks panel's read takes the causes the feedback bundle already computed.

FG1c's panel recomputed ``claim_checked_feedback`` on every desktop feedback open with no factor
to list, and opened a connection per repository read; together 62 to 89 ms per open on a synthetic
vault. The panel is now read on one pinned connection from the bundle's causes. These tests hold
it to the same bytes as the recomputing read: the same panel, seed and order, and the same
exposure row after it.
"""

from __future__ import annotations

import json

from learnloop.diagnosis import causal_attribution
from learnloop.followup_run import marks as panel
from learnloop.followup_serve import workflow as wf
from learnloop_sidecar.dto import to_camel

from tests.test_followup_fg1d_probe_shadow import desk  # noqa: F401 - the fixture
from tests.test_followup_rival_factor import _call, _generate, _miss


def _journey(desk):
    """A miss with a factor, its generated probe answered, beside the vault's seeded attempts."""

    miss_id = _miss(desk, "")
    _generate(desk)
    desk.ctx.reload(maintenance=False)
    vault, repository = desk.ctx.require_vault()
    row = wf.attempt_workflow(repository, miss_id)
    _call(desk.ctx, "followup_next", {"attemptId": miss_id})
    _call(desk.ctx, "open_queue_item", {"practiceItemId": row["practice_item_id"]})
    contract = _call(desk.ctx, "get_probe_contract", {"practiceItemId": row["practice_item_id"]})
    probe = _call(desk.ctx, "submit_attempt", {
        "sessionId": desk.session, "practiceItemId": row["practice_item_id"], "answerMd": "An answer.",
        "attemptType": "diagnostic_probe", "latencySeconds": 40, "probePresentationId": contract["presentationId"],
    })
    with repository.connection() as connection:
        attempts = [value[0] for value in connection.execute("SELECT id FROM practice_attempts ORDER BY created_at, id")]
    return vault, repository, miss_id, probe.get("attemptId") or probe["attempt_id"], attempts


def _recomputed(vault, repository, attempt_id):
    """The panel as FG1c read it: every cause read here, unpinned."""

    view = panel.bundle_view(vault, repository, attempt_id)
    return None if view is None else to_camel(view)


def test_every_panel_is_byte_identical_to_the_recomputing_read(desk):
    vault, repository, miss_id, probe_id, attempts = _journey(desk)
    shown = {}
    for attempt_id in attempts:
        bundle = _call(desk.ctx, "get_feedback", {"attemptId": attempt_id, "recordOpen": False})
        got = bundle.get("hypothesisMarks")
        assert json.dumps(got, sort_keys=True) == json.dumps(_recomputed(vault, repository, attempt_id), sort_keys=True)
        shown[attempt_id] = got
    # Each kind is here: the miss's factor list, the probe answer's (the miss's), and an attempt with
    # no factor whose list is its claim-checked causes, and one with nothing to mark.
    assert shown[miss_id] and shown[probe_id]["surface"] == "marks_probe_feedback"
    assert shown[probe_id]["hypotheses"] == shown[miss_id]["hypotheses"]
    no_factor = [a for a in attempts if shown[a] and a not in (miss_id, probe_id)
                 and not panel.markable_list(vault, repository, a).factor_id]
    assert no_factor
    assert any(shown[a] is None for a in attempts)


def test_the_bundles_causes_are_read_once(desk, monkeypatch):
    vault, repository, miss_id, probe_id, attempts = _journey(desk)
    calls = []
    real = causal_attribution.claim_checked_feedback

    def counting(*args, **kwargs):
        calls.append(args[2] if len(args) > 2 else kwargs.get("attempt_id"))
        return real(*args, **kwargs)

    monkeypatch.setattr(causal_attribution, "claim_checked_feedback", counting)
    for attempt_id in attempts:
        if attempt_id == probe_id:
            continue
        calls.clear()
        _call(desk.ctx, "get_feedback", {"attemptId": attempt_id, "recordOpen": False})
        # The bundle's own read; the panel takes its causes and reads none.
        assert calls.count(attempt_id) == 1, (attempt_id, calls)


def test_the_exposure_after_the_panel_is_the_one_the_recomputing_read_gives(desk):
    vault, repository, miss_id, _probe_id, attempts = _journey(desk)
    for attempt_id in attempts:
        marks = _call(desk.ctx, "get_feedback", {"attemptId": attempt_id, "recordOpen": False}).get("hypothesisMarks")
        if not marks or marks["attemptId"] != attempt_id:
            continue
        ids = [row["hypothesisVersionId"] for row in marks["hypotheses"]]
        assert _call(desk.ctx, "record_hypothesis_exposure", {
            "attemptId": attempt_id, "surface": marks["surface"], "hypothesisVersionIds": ids})["recorded"]
        listed = panel.markable_list(vault, repository, attempt_id)
        with repository.connection() as connection:
            row = connection.execute("SELECT * FROM hypothesis_list_exposures ORDER BY rowid DESC LIMIT 1").fetchone()
        assert json.loads(row["hypothesis_version_ids_json"]) == ids == listed.order
        assert row["order_seed"] == marks["orderSeed"] == listed.order_seed


def test_a_held_miss_still_shows_no_panel(desk):
    """The causes are taken before the hold blanks them; the hold still keeps the panel off."""

    miss_id = _miss(desk, "")
    vault, repository = desk.ctx.require_vault()
    assert wf.attempt_workflow(repository, miss_id)["feedback_held"]
    bundle = _call(desk.ctx, "get_feedback", {"attemptId": miss_id, "recordOpen": False})
    assert bundle["followup"]["held"] is True and bundle["causalFeedback"] is None
    assert "hypothesisMarks" not in bundle
