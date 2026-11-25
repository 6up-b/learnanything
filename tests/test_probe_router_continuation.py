"""The probe router's continuation (G2 review R8, R9; ``learnloop.daily_plan.probe_continuation``): one router decision
per next observation of a router-owned episode, drawn and logged with its exact served distribution, consumed by every
door through the pin it commits, or a stop that completes the episode with ``router_stop``.

Each case starts from a learner-lane probe the router selected (the probe coin fixed to ask) and the learner accepted
and answered, on a learning object with a second instrument (``tests/probe_router_owned_helpers.py``).
"""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from learnloop.daily_plan import probe_continuation as PCN
from learnloop.diagnosis.probe_authority import router_selected_presentation
from learnloop.diagnosis.probe_completion import ROUTER_STOP
from learnloop.router.plan_log import PROBE_CONTINUATION_SURFACE, PROBE_REF, CONTINUATION_STOP_REF
from learnloop.router_objective import probe_coin as PC

from tests.probe_block_end_helpers import _submit
from tests.probe_router_authority_helpers import call, sidecar
from tests.probe_router_owned_helpers import SECOND, answer_the_pin, grading_ready, selected, sentinels


def _answered(tmp_path, monkeypatch, *, u: float):
    """The routed first probe answered (its block closed, the episode in progress); the continuation's coin then reads
    ``u`` (the stop coin's rate is 0.2: below it the coin asks the next probe)."""

    case = selected(tmp_path, monkeypatch)
    answer_the_pin(case, monkeypatch)
    case.episode_id = case.offer["episodeId"]
    assert case.repository.probe_episode(case.episode_id).status == "in_progress"
    monkeypatch.setattr(PC, "draw_uniform", lambda _seed: u)
    return case


def _continuations(case) -> list[dict]:
    with case.repository.connection() as connection:
        rows = [dict(row) for row in connection.execute(
            "SELECT * FROM router_decisions WHERE surface = ? ORDER BY created_at, id", (PROBE_CONTINUATION_SURFACE,))]
    for row in rows:
        row["detail"] = json.loads(row.pop("detail_json"))
        row["candidates"] = json.loads(row.pop("candidates_json"))
    return rows


def _job(case) -> None:
    case.ctx.post_attempt_worker.run_pending("probe_router")


def test_the_router_decides_the_next_observation_once_with_its_exact_served_distribution(tmp_path, monkeypatch):
    case = _answered(tmp_path, monkeypatch, u=0.0)
    assert [r["episode_id"] for r in PCN.requested(case.vault, case.repository)] == [case.episode_id]
    _job(case)
    (decision,) = _continuations(case)
    assert (decision["chosen_ref"], decision["propensity"], decision["propensity_kind"]) == (PROBE_REF, 0.2, "exact")
    assert decision["detail"]["served_pi"] == {PROBE_REF: 0.2, CONTINUATION_STOP_REF: 0.8}
    assert {c["ref"]: c["propensity"] for c in decision["candidates"]} == {PROBE_REF: 0.2, CONTINUATION_STOP_REF: 0.8}
    assert decision["receipt_key"] == f"plan_interrupt:probe_continuation:{case.episode_id}:1:0"
    assert decision["detail"]["next_item"] == SECOND and decision["detail"]["probe_coin"]
    with case.repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM policy_experiment_assignments WHERE unit_id = ?",
                                  (decision["id"],)).fetchone()[0] == 1
        objective = connection.execute("SELECT arm, learning_object_id FROM decision_objectives WHERE decision_id = ?",
                                       (decision["id"],)).fetchone()
    assert objective["arm"] == "insert"
    # The next presentation is committed now, pinned with the decision; nothing is decided twice.
    standing = case.repository.active_probe_presentation(case.episode_id)
    assert standing.practice_item_id == SECOND
    assert standing.selection_components["causal_probe"]["router_decision_id"] == decision["id"]
    assert router_selected_presentation(case.repository, standing)
    assert PCN.requested(case.vault, case.repository) == []
    _job(case)
    assert len(_continuations(case)) == 1


def test_a_flat_instrument_the_router_asks_is_admitted_and_served_first_whatever_its_eig(tmp_path, monkeypatch):
    from learnloop.diagnosis import probe_episodes
    from learnloop.scheduling import scheduler

    from tests.voi_stopping_helpers import _build

    case = _answered(tmp_path, monkeypatch, u=0.0)
    real = probe_episodes.eligible_instruments

    def flat(*args, **kwargs):
        # Every instrument's conditionals are the same under each hypothesis: no information gain at all.
        return [replace(entry, expected_information_gain=0.0, predictive_eig=0.0, predictive_information_rate=0.0)
                for entry in real(*args, **kwargs)]

    monkeypatch.setattr(probe_episodes, "eligible_instruments", flat)
    monkeypatch.setattr(scheduler, "eligible_instruments", flat)
    _job(case)
    (decision,) = _continuations(case)
    assert decision["chosen_ref"] == PROBE_REF and decision["detail"]["eligibility"]["next_item_eig"] == 0.0
    queue = _build(case.vault, case.repository)
    assert queue and queue[0].practice_item_id == SECOND
    assert queue[0].components.get("router_pinned_probe") == 1.0 and not queue[0].components.get("probe_eig")
    served = call(case.ctx, "get_probe_contract", {"practiceItemId": SECOND, "sessionId": "sess"})
    assert served["active"] is True


def test_the_continuation_answer_closes_its_block_by_its_pin_and_no_legacy_worth_gate_is_asked(tmp_path, monkeypatch):
    case = _answered(tmp_path, monkeypatch, u=0.0)
    sentinels(monkeypatch)
    _job(case)
    served = call(case.ctx, "get_probe_contract", {"practiceItemId": SECOND, "sessionId": "sess"})
    assert served["active"] is True
    result = _submit(case.vault, case.repository, item_id=SECOND, presentation_id=served["presentationId"], score=0)
    assert result.probe_block_end is not None
    # No instrument is left: the episode parks with one generation need (it is never left waiting on a decision no
    # run can make), and the next job leaves it alone.
    assert case.repository.probe_episode(case.episode_id).status == "pending_items"
    assert PCN.requested(case.vault, case.repository) == []


def test_a_router_stop_completes_the_episode_with_its_own_reason(tmp_path, monkeypatch):
    case = _answered(tmp_path, monkeypatch, u=0.9)
    _job(case)
    (decision,) = _continuations(case)
    assert (decision["chosen_ref"], decision["propensity"]) == (CONTINUATION_STOP_REF, 0.8)
    episode = case.repository.probe_episode(case.episode_id)
    assert (episode.status, episode.completion_reason) == ("complete", ROUTER_STOP)
    with case.repository.connection() as connection:
        detail = connection.execute("SELECT completion_detail_json FROM probe_episodes WHERE id = ?",
                                    (case.episode_id,)).fetchone()[0]
    assert json.loads(detail)["router_decision_id"] == decision["id"]
    assert case.repository.active_probe_presentation(case.episode_id) is None
    with case.repository.connection() as connection:
        assert connection.execute("SELECT arm FROM decision_objectives WHERE decision_id = ?",
                                  (decision["id"],)).fetchone()[0] == "stop"
    refused = call(case.ctx, "get_probe_contract", {"practiceItemId": SECOND, "sessionId": "sess"})
    assert refused["active"] is False


def test_until_the_router_decides_no_door_commits_an_instrument(tmp_path, monkeypatch):
    from tests.voi_stopping_helpers import _build

    case = _answered(tmp_path, monkeypatch, u=0.0)
    queue = _build(case.vault, case.repository)
    # Not a probe this build: no EIG admits it and no pin names it (an instrument that is not a diagnostic surface
    # stays ordinary practice, as any item outside a probe), and nothing is precommitted.
    (second,) = [item for item in queue if item.practice_item_id == SECOND]
    assert not second.components.get("probe_eig") and not second.components.get("router_pinned_probe")
    assert case.repository.active_probe_presentation(case.episode_id) is None
    pending = call(case.ctx, "get_probe_contract", {"practiceItemId": SECOND, "sessionId": "sess"})
    assert (pending["active"], pending["reason"]) == (False, "router_decision_pending")
    assert case.repository.active_probe_presentation(case.episode_id) is None and _continuations(case) == []


def test_a_pin_that_ended_unanswered_opens_a_new_boundary(tmp_path, monkeypatch):
    case = _answered(tmp_path, monkeypatch, u=0.0)
    _job(case)
    standing = case.repository.active_probe_presentation(case.episode_id)
    case.repository.end_probe_presentation(standing.id, end_reason="expired")
    (waiting,) = PCN.requested(case.vault, case.repository)
    assert (waiting["observations"], waiting["redraw"]) == (1, 1)
    _job(case)
    first, second = _continuations(case)
    assert second["receipt_key"].endswith(":1:1") and second["id"] != first["id"]


def test_a_restart_resumes_a_waiting_continuation(tmp_path, monkeypatch):
    case = _answered(tmp_path, monkeypatch, u=0.0)
    restarted = sidecar(case.root)
    woken: list[str] = []
    monkeypatch.setattr(restarted.post_attempt_worker, "request_probe_router", lambda: woken.append("probe_router"))
    restarted.resume_post_attempt_jobs()
    assert woken == ["probe_router"]
    restarted.post_attempt_worker.run_pending("probe_router")
    assert len(_continuations(case)) == 1


def test_below_the_tag_no_episode_waits_on_the_router(tmp_path):
    from tests.probe_router_authority_helpers import TAG, divergent_factor

    case = divergent_factor(tmp_path, version=TAG)
    assert PCN.requested(case.vault, case.repository) == []


#: The activity substrate's catalog a vault's first rebuild backfills for rows it never recorded
#: (``tests/test_replay_writes_no_ledger.py``, ``FIRST_REBUILD_BACKFILL``).
_CATALOG_BACKFILL = frozenset({"activity_cards", "activity_card_versions", "activity_families",
                               "activity_family_versions", "activity_surfaces"})


def test_a_rebuild_after_a_router_stop_reproduces_the_live_rows_and_writes_no_ledger(tmp_path, monkeypatch):
    """G2-R36: the live rows (every table: decisions, assignments, presentations, episodes, receipts, ledgers and
    derived rows) are snapshotted before the first rebuild, and each rebuild is compared with them row by row, so a
    rebuild that changed a row and then stabilized fails. A rebuild adds its own receipt; the first may also
    materialize a derived projection the live path had not built yet (a derived table empty live) and add the
    activity catalog's backfill beside the rows live wrote (``tests/test_replay_writes_no_ledger.py``'s first-rebuild
    rule); the second must reproduce the first exactly. Every row live wrote stays as it was."""

    from learnloop.db.table_roles import TABLE_ROLES, TableRole
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
    from learnloop.vault.loader import load_vault

    case = _answered(tmp_path, monkeypatch, u=0.9)
    _job(case)

    def snapshot() -> dict[str, list[str]]:
        with case.repository.connection() as connection:
            present = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
            return {name: sorted(json.dumps(dict(row), sort_keys=True, default=str)
                                 for row in connection.execute(f'SELECT * FROM "{name}"'))
                    for name in sorted(TABLE_ROLES) if name in present}

    live = snapshot()
    for table in ("router_decisions", "policy_experiment_assignments", "probe_presentations", "probe_episodes",
                  "causal_probe_decision_receipts", "decision_objectives"):
        assert live.get(table), f"the live history has {table} rows"
    vault = load_vault(case.root)
    rebuild_all_derived_state(vault, case.repository)
    first = snapshot()
    rebuild_all_derived_state(vault, case.repository)
    second = snapshot()
    for rebuilt, receipts in ((first, 1), (second, 2)):
        added = set(rebuilt.pop("derived_state_rebuilds")) - set(live.get("derived_state_rebuilds", []))
        assert len(added) == receipts  # its own receipt
        changed = sorted(name for name in rebuilt if rebuilt[name] != live.get(name, []))
        materialized = sorted(name for name in changed
                              if (not live.get(name) and TABLE_ROLES[name] == TableRole.DERIVED)
                              or (name in _CATALOG_BACKFILL and set(live.get(name, [])) <= set(rebuilt[name])))
        assert [name for name in changed if name not in materialized] == []
    assert second == first
    episode = case.repository.probe_episode(case.episode_id)
    assert (episode.status, episode.completion_reason) == ("complete", ROUTER_STOP)


@pytest.mark.parametrize("u", [0.0, 0.9])
def test_the_decision_revalues_from_its_stored_row_alone(tmp_path, monkeypatch, u):
    from learnloop.daily_plan import learner_probe

    case = _answered(tmp_path, monkeypatch, u=u)
    _job(case)
    (decision,) = _continuations(case)
    replayed = learner_probe.revalue(decision["detail"]["valuation"]["frozen"]["replay"])
    assert replayed.record["values"] == decision["detail"]["evaluation"]["values"]
    grading_ready(monkeypatch)


def test_no_router_decisions_measurement_takes_a_probe_instrument_as_its_check(tmp_path, monkeypatch):
    from tests.causal_orchestrator_helpers import PROBE_ITEM

    case = _answered(tmp_path, monkeypatch, u=0.0)
    _job(case)
    with case.repository.connection() as connection:
        checks = {row[0] for row in connection.execute(
            "SELECT practice_item_id FROM decision_objectives WHERE practice_item_id IS NOT NULL")}
    # The learner lane's decision and the continuation each arranged a "Check once" on the learning object; neither
    # took an item a probe administers, so neither holds the router's next instrument back.
    assert not checks & {PROBE_ITEM, SECOND}


def _pending_check_on(case, item_id: str) -> str:
    """A "Check once" already pending on ``item_id`` (an ordinary-mode, card-bound item), dated past the window."""

    from datetime import timedelta

    from learnloop.clock import SystemClock
    from learnloop.curriculum import commitments as C
    from learnloop.daily_plan import measurement as M

    now = SystemClock().now()
    commitment = C.create_commitment(
        case.repository, action="test_me_later", intent_text="one question on your own, later, to see what stuck",
        targets=[{"target_kind": "legacy_practice_item", "target_ref": item_id, "role": "required"}],
        depth_preset=M.CHECK_DEPTH_PRESET, client_idempotency_key=f"test:check:{item_id}",
        due_hint=(now + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ"), reason="decision_measurement",
        provenance={"via": M.VIA, "decision_id": "dec_other", "learning_object_id": case.offer.get("learningObjectId")})
    return commitment.id


def test_a_probe_decisions_measurement_never_shares_a_check_on_its_instrument(tmp_path, monkeypatch):
    """G2-R29: a pending "Check once" on the last fresh instrument is not shared as the continuation's measurement
    (sharing made that instrument the decision's check)."""

    from learnloop.daily_plan import measurement as M

    case = _answered(tmp_path, monkeypatch, u=0.0)
    held = _pending_check_on(case, SECOND)
    real = M._pending_checks
    # The check on the instrument is the first one pending (the learner lane's own check, on another item, after it).
    monkeypatch.setattr(M, "_pending_checks", lambda serving, item_ids: sorted(
        real(serving, item_ids), key=lambda check: check.commitment_id != held))
    _job(case)
    (decision,) = _continuations(case)
    with case.repository.connection() as connection:
        objective = dict(connection.execute("SELECT * FROM decision_objectives WHERE decision_id = ?",
                                            (decision["id"],)).fetchone())
    assert objective["commitment_id"] != held and objective["practice_item_id"] != SECOND


def test_a_replacement_check_keeps_the_decisions_instrument_exclusions(tmp_path, monkeypatch):
    """G2-R29: the replacement an unread answer leaves carries the probe decision's exclusions through a check this
    settlement made for another decision (``fresh``) and through a new pick."""

    from learnloop.clock import SystemClock
    from learnloop.daily_plan import measurement as M
    from learnloop.router.plan_log import LEARNER_PROBE_SURFACE

    case = _answered(tmp_path, monkeypatch, u=0.0)
    lo = case.vault.practice_items[SECOND].learning_object_id
    row = {"decision_surface": LEARNER_PROBE_SURFACE, "learning_object_id": lo,
           "decision_receipt_key": f"plan_interrupt:learner_probe:{case.factor}"}
    exclude = M.decision_exclusions(case.vault, case.repository, row)
    assert SECOND in exclude
    fresh = {lo: M._Arrangement(M.ARRANGED, commitment_id="cm_other", practice_item_id=SECOND)}
    arranged = M._replacement_check(case.vault, case.repository, "dec_probe", lo, answered_item=None, serving=None,
                                    now=SystemClock().now(), clock=None, fresh=fresh, exclude=exclude)
    assert arranged.commitment_id != "cm_other" and arranged.practice_item_id not in exclude


# -- G2-R26: one resolver for "Continue", read by the desktop and the terminal client --------------------------------


def _next(case, **params) -> dict:
    return call(case.ctx, "get_next_probe_item", {"learningObjectId": case.vault.practice_items[SECOND]
                                                  .learning_object_id, **params})


def test_continue_opens_the_routers_question_on_both_sides_of_its_decision(tmp_path, monkeypatch):
    case = _answered(tmp_path, monkeypatch, u=0.0)
    # Before the router's job decides: pending, and no other instrument is offered or committed.
    before = _next(case)
    assert (before["active"], before["routerState"], before["practiceItemId"]) == (False, "pending", None)
    assert case.repository.active_probe_presentation(case.episode_id) is None
    _job(case)
    standing = case.repository.active_probe_presentation(case.episode_id)
    after = _next(case)
    assert (after["active"], after["routerState"]) == (True, "standing")
    assert (after["practiceItemId"], after["presentationId"]) == (SECOND, standing.id)
    # Opening it serves that exact presentation.
    served = call(case.ctx, "get_probe_contract", {"practiceItemId": SECOND, "sessionId": "sess"})
    assert served["active"] is True and served["presentationId"] == standing.id


def test_continue_after_a_router_stop_reports_the_transition(tmp_path, monkeypatch):
    case = _answered(tmp_path, monkeypatch, u=0.9)
    _job(case)
    done = _next(case, episodeId=case.episode_id)
    assert (done["active"], done["routerState"], done["episodeStatus"]) == (False, "completed", "complete")


def test_the_resolver_retires_a_pin_that_became_protected(tmp_path, monkeypatch):
    from learnloop.diagnosis import probe_episodes

    case = _answered(tmp_path, monkeypatch, u=0.0)
    _job(case)
    standing = case.repository.active_probe_presentation(case.episode_id)
    real = probe_episodes.item_refusals
    monkeypatch.setattr(probe_episodes, "item_refusals", lambda vault, repository, items: {
        **real(vault, repository, items), **{item.id: "protected_exam_material" for item in items if item.id == SECOND}})
    retired = _next(case)
    assert (retired["active"], retired["routerState"]) == (False, "pending")
    assert case.repository.probe_presentation(standing.id).status == "ended"
    assert case.repository.active_probe_presentation(case.episode_id) is None


def test_the_terminal_client_serves_the_routers_standing_question(tmp_path, monkeypatch):
    pytest.importorskip("textual")  # the TUI needs the optional `tui` extra
    from types import SimpleNamespace

    from learnloop.ai import routing
    from learnloop.tui.screens.practice import PracticeScreen

    case = _answered(tmp_path, monkeypatch, u=0.0)
    monkeypatch.setattr(routing, "ready_client_for_task", lambda *_a, **_k: SimpleNamespace(
        runtime=SimpleNamespace(ready=True), client=object()))
    state = SimpleNamespace(vault=case.vault, repository=case.repository)
    lo = case.vault.practice_items[SECOND].learning_object_id
    pending = PracticeScreen(state, SimpleNamespace(practice_item_id=SECOND, learning_object_id=lo))
    # Before the decision nothing is committed: the screen is ordinary practice, as the desktop's door answers.
    assert pending.probe_presentation_id is None and case.repository.active_probe_presentation(case.episode_id) is None
    _job(case)
    standing = case.repository.active_probe_presentation(case.episode_id)
    screen = PracticeScreen(state, SimpleNamespace(practice_item_id=SECOND, learning_object_id=lo))
    assert screen.probe_presentation_id == standing.id and screen.probe_contract
    assert case.repository.probe_presentation(standing.id).status == "served"
