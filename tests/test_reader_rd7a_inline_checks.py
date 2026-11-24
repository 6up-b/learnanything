"""Inline cold checks in the Reader (spec §12.6; mvp-0.69): the administration protocol end to end through the
sidecar, the protection set, the lock shared with Today, exposure written at once, submission through the attempt
service (a grader fake), abandon, crash recovery at each transition, the owner's three rulings, and the projection a
whole-vault rebuild reproduces. No model is called but the grader fake."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from learnloop.curriculum import commitments as C
from learnloop.db.repositories import Repository
from learnloop.intent import inline_administration as IA
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from tests.approach_map_fakes import EXPECTED, ITEM, LO
from tests.hint_fakes import hint_vault
from tests.workbench_help_fakes import call

ANSWER = "F(x) = x^2 on [0, 1], so P(X <= 1/2) = 1/4."


@pytest.fixture(autouse=True)
def grader(monkeypatch):
    """A blind grader fake behind the sidecar's grading provider (the attempt service grades as for any answer)."""

    import learnloop_sidecar.handlers.practice as practice
    from tests.split_live_helpers import ReadyRuntime
    from tests.stuck_prompt_helpers import StuckFake

    client = StuckFake()
    monkeypatch.setattr(practice, "ready_grading_provider", lambda vault, override=None: ("fake", ReadyRuntime(), client))
    return client


def _sidecar(tmp_path, name: str = "vault"):
    paths = hint_vault(tmp_path, name=name)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.post_attempt_worker.autostart = False
    session = call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    repository = Repository.attach(paths.sqlite_path)
    return paths, ctx, session, repository


def _due_check(repository: Repository, *, key: str = "rd7a") -> str:
    yesterday = (datetime.now(UTC) - timedelta(days=1)).date().isoformat()
    return C.create_commitment(
        repository, action="test_me_later", intent_text="check the CDF later",
        targets=[{"target_kind": "legacy_practice_item", "target_ref": ITEM, "role": "required"}],
        depth_preset="keep_in_touch", client_idempotency_key=key, due_hint=yesterday).id


def _rows(paths, sql: str, params: tuple = ()) -> list[tuple]:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        return [tuple(row) for row in connection.execute(sql, params)]


VISIBLE = {"windows": [
    {"windowId": "w_pad", "kind": "pad_stack", "padBlockIds": ["b1", "b2"]},
    {"windowId": "w_thread", "kind": "thread", "exchangeIds": ["qe_1"]},
], "companionOpen": True, "companionExchangeIds": ["qe_2"], "previewWindowIds": ["w_pad"]}


def _begin(ctx, session, commitment, *, request_id="req_1", visible=None):
    return call(ctx, "check.begin_inline", {"requestId": request_id, "commitmentId": commitment, "sessionId": session,
                                           "visible": VISIBLE if visible is None else visible})


def _submit(ctx, token, *, submission_id="sub_1", answer=ANSWER):
    return call(ctx, "check.submit_inline", {"administrationToken": token, "submissionId": submission_id,
                                            "answerMd": answer})


# -- the RPCs ---------------------------------------------------------------------------------------------------------

def test_the_rpcs_are_registered_desktop_only_and_refuse_extra_fields():
    from learnloop_mobile.allowlist import ALLOWLIST
    from learnloop_sidecar import handlers  # noqa: F401 - populates the registry
    from learnloop_sidecar.handlers import inline_checks as H
    from learnloop_sidecar.registry import METHOD_REGISTRY

    assert H.INLINE_CHECK_RPCS == ("checks.due_for", "check.begin_inline", "check.protect_more", "check.expose",
                                   "check.submit_inline", "check.abandon_inline", "check.open_inline")
    for name in H.INLINE_CHECK_RPCS:
        assert name in METHOD_REGISTRY and name not in ALLOWLIST
    with pytest.raises(ValueError):
        H.BeginInlineInput.model_validate({"requestId": "r", "commitmentId": "c", "sessionId": "s", "extra": 1})
    with pytest.raises(ValueError):
        H.ExposeInput.model_validate({"administrationToken": "t", "ref": {}, "kind": "peeked"})


def test_below_the_tag_every_check_rpc_refuses_and_today_ignores_the_lock(tmp_path):
    from learnloop.algorithm_versions import SUCCESSOR_CHAIN
    from tests.helpers import set_algorithm_version

    paths, ctx, session, repository = _sidecar(tmp_path)
    set_algorithm_version(paths, SUCCESSOR_CHAIN[-2])
    ctx.load(paths.root)
    commitment = _due_check(repository)
    with pytest.raises(SidecarError) as refused:
        _begin(ctx, session, commitment)
    assert refused.value.code == IA.BELOW_TAG
    with pytest.raises(SidecarError) as reopened:
        call(ctx, "check.open_inline", {})
    assert reopened.value.code == IA.BELOW_TAG


# -- opening: protection before the prompt ----------------------------------------------------------------------------

def test_begin_serves_todays_item_with_its_frozen_contract_and_records_the_veils_before_the_prompt(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    card = _begin(ctx, session, commitment)
    assert card["itemRef"] == ITEM and card["cold"] is True and card["contractHash"]
    assert card["prompt"]["assessmentContractVersionId"] == card["contractHash"]
    # Every note-bearing surface is veiled by default: the pad and thread windows whole, the companion, the preview.
    kinds = sorted((ref["kind"], ref.get("window_id")) for ref in card["protection"]["veiled"])
    assert kinds == [("companion", None), ("preview", "w_pad"), ("window", "w_pad"), ("window", "w_thread")]
    assert card["protection"]["method"] == IA.METHOD
    assert _rows(paths, "SELECT state, surface, cold, practice_item_id FROM check_administrations") == [
        ("open", IA.SURFACE, 1, ITEM)]
    assert _rows(paths, "SELECT seq, kind FROM check_veil_sets") == [(1, "begin")]
    # The same request again is the same administration (a retry after a lost reply).
    again = _begin(ctx, session, commitment)
    assert again["administrationToken"] == card["administrationToken"]
    assert _rows(paths, "SELECT COUNT(*) FROM check_administrations") == [(1,)]


def test_no_prompt_leaves_when_the_veils_cannot_be_recorded(tmp_path, monkeypatch):
    from learnloop.db.stores import check_administrations as store

    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)

    def fail(*_args, **_kwargs):
        raise sqlite3.OperationalError("disk full")

    monkeypatch.setattr(store, "insert_veil_set", fail)
    with pytest.raises(Exception):
        _begin(ctx, session, commitment)
    # One transaction: no administration without its veils, so nothing holds the lock and no card can reopen.
    assert _rows(paths, "SELECT COUNT(*) FROM check_administrations") == [(0,)]


def test_the_protection_set_veils_covered_passages_and_every_note_bearing_surface(tmp_path, monkeypatch):
    paths, _ctx, _session, repository = _sidecar(tmp_path)
    from learnloop.vault.loader import load_vault


    class Sections:
        def __init__(self, _repository):
            pass

        def section_of(self, extraction_id, span_id):
            return {"s1": "sec_cdf", "s2": "sec_other"}.get(span_id)

    import learnloop.intent.inline_checks as inline_checks

    monkeypatch.setattr(inline_checks, "_Sections", Sections)
    opened = IA.Opened(commitment_id="cm", practice_item_id=ITEM, cold=True, candidates=(ITEM,),
                       learning_object_ids=(LO,), provenance={})
    visible = {
        "windows": [
            {"window_id": "w_book", "kind": "source", "extraction_id": "ext_book", "span_ids": ["s1", "s2"],
             "note_ids": ["n1"], "figures": [{"figure_id": "f1", "span_id": "s1"}, {"figure_id": "f2", "span_id": "s2"}]},
            {"window_id": "w_lesson", "kind": "lesson"}, {"window_id": "w_ink", "kind": "ink", "pad_block_ids": ["i1"]},
        ],
        "preview_window_ids": ["w_book", "w_other"],
        "search_rows": [{"kind": "span", "extraction_id": "ext_book", "span_id": "s1"},
                        {"kind": "span", "extraction_id": "ext_book", "span_id": "s2"}, {"kind": "pad", "ref_id": "b9"}],
    }
    method, veiled = IA.protection(load_vault(paths.root), repository, opened, visible,
                                   lambda los: {("ext_book", "sec_cdf")})
    assert method == IA.METHOD
    found = sorted((ref["group"], ref["kind"], ref.get("span_id") or ref.get("figure_id") or ref.get("note_id")
                    or ref.get("window_id") or ref.get("ref_id")) for ref in veiled)
    assert found == sorted([
        ("source passages", "span", "s1"), ("figures", "figure", "f1"), ("notes", "note", "n1"),
        ("lessons", "window", "w_lesson"), ("pads", "window", "w_ink"), ("previews", "preview", "w_book"),
        ("search results", "search_row", "s1"), ("search results", "search_row", "b9"),
    ])
    # Coverage unreadable: every visible source passage is veiled instead (fail closed).
    method, veiled = IA.protection(load_vault(paths.root), repository, opened, visible, lambda los: None)
    assert method == IA.METHOD_WHOLE_SOURCES
    assert {ref["span_id"] for ref in veiled if ref["kind"] == "span"} == {"s1", "s2"}


def test_protect_more_veils_only_what_is_new(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    token = _begin(ctx, session, _due_check(repository))["administrationToken"]
    more = call(ctx, "check.protect_more", {"administrationToken": token, "visible": {
        "windows": [*VISIBLE["windows"], {"windowId": "w_new", "kind": "pad_stack"}]}})
    assert [(ref["kind"], ref["window_id"]) for ref in more["veilAdditions"]] == [("window", "w_new")]
    assert _rows(paths, "SELECT seq, kind FROM check_veil_sets ORDER BY seq") == [(1, "begin"), (2, "more")]


# -- the lock shared with Today -------------------------------------------------------------------------------------

def test_one_administration_at_a_time_and_today_honours_it(tmp_path):
    from learnloop.clock import SystemClock
    from learnloop.intent.checks import BEING_ANSWERED_BANNER, served_check
    from learnloop.intent.inline_checks import due_checks
    from learnloop.scheduling.intent.serving import intent_serving
    from learnloop.vault.loader import load_vault

    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    vault = load_vault(paths.root)
    view = served_check(vault, repository, ITEM, now=SystemClock().now())
    assert view is not None and view["cold"] is True and "being_answered_in" not in view
    token = _begin(ctx, session, commitment)["administrationToken"]
    # Two administrations never overlap.
    with pytest.raises(SidecarError) as second:
        _begin(ctx, session, commitment, request_id="req_2")
    assert second.value.code == "administration_open"
    assert second.value.details["administration_token"] == token
    # Today: the check is "being answered in the Reader", its item is not the check in a build, and the band knows.
    view = served_check(vault, repository, ITEM, now=SystemClock().now())
    assert view["being_answered_in"] == "reader" and view["banner"] == BEING_ANSWERED_BANNER and view["cold"] is False
    serving = intent_serving(vault, repository, now=SystemClock().now(), force=True)
    assert serving.locked == frozenset({commitment})

    class Entry:
        practice_item_id = ITEM

    kept, chosen = serving.pick_checks([Entry()])
    assert kept == [] and chosen == []
    assert [row["being_answered"] for row in due_checks(vault, repository)] == [True]
    call(ctx, "check.abandon_inline", {"administrationToken": token})
    assert served_check(vault, repository, ITEM, now=SystemClock().now())["cold"] is True
    assert intent_serving(vault, repository, now=SystemClock().now(), force=True).locked == frozenset()


def test_a_check_with_an_answer_being_written_in_today_is_not_opened_here(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    call(ctx, "update_session_checkpoint", {"sessionId": session, "currentPracticeItemId": ITEM,
                                          "currentAnswer": "F(x) = x^2"})
    with pytest.raises(SidecarError) as refused:
        _begin(ctx, session, commitment)
    assert refused.value.code == "being_answered_in_today"


# -- exposure (owner ruling Q1) ---------------------------------------------------------------------------------------

def _seed_block(ctx, text: str) -> dict:
    """A pad block of the learner's own words; the veil a window of it would get, as a ref."""

    call(ctx, "pad.apply", {"clientId": "c", "seq": 1, "padId": "pad_n", "ops": [
        {"op": "create_pad", "kind": "named", "title": "notes"},
        {"op": "insert_block", "blockId": "b1", "versionId": "v1", "kind": "text", "provenance": "learner",
         "positionKey": "a0", "bodyMd": text}]})
    return {"kind": "window", "window_id": "w_pad", "pad_block_ids": ["b1"]}


def test_opening_a_veil_that_states_the_answer_primes_the_item_and_the_answer_is_practice(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    ref = _seed_block(ctx, EXPECTED)
    token = _begin(ctx, session, commitment)["administrationToken"]
    status = call(ctx, "check.expose", {"administrationToken": token, "ref": ref, "kind": "opened_veil"})["protectionStatus"]
    # Persisted at once, before any answer: a source review sized by the overlap with the key.
    reveals = _rows(paths, "SELECT practice_item_id, source_kind, amount, basis FROM reveal_events")
    assert [(item, kind, basis) for item, kind, _amount, basis in reveals] == [(ITEM, "source_review", IA.OPENED_BASIS)]
    assert reveals[0][2] > 0
    assert status["coldNow"] is False
    reply = _submit(ctx, token)
    assert (reply["cold"], reply["reason"]) == (False, "primed")
    assert C.resolve_disposition(repository, commitment) == "one_check_pending"  # the duty stays


def test_opening_a_veil_that_says_nothing_of_the_answer_leaves_it_cold(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    ref = _seed_block(ctx, "Remember to buy milk on Tuesday.")
    token = _begin(ctx, session, commitment)["administrationToken"]
    status = call(ctx, "check.expose", {"administrationToken": token, "ref": ref, "kind": "opened_veil"})["protectionStatus"]
    assert _rows(paths, "SELECT COUNT(*) FROM reveal_events") == [(0,)]  # a zero overlap writes nothing
    assert status["coldNow"] is True
    call(ctx, "check.expose", {"administrationToken": token, "ref": {"kind": "window", "window_id": "w_x"},
                               "kind": "navigated"})
    assert _rows(paths, "SELECT COUNT(*) FROM reveal_events") == [(0,)]  # navigating is no exposure
    reply = _submit(ctx, token)
    assert (reply["cold"], reply["reason"]) == (True, "on_your_own")
    assert C.resolve_disposition(repository, commitment) == "satisfied"
    opened = _rows(paths, "SELECT opened_json FROM check_veil_sets WHERE kind = 'close'")
    assert "w_pad" in opened[0][0]


def test_opening_a_notes_veil_reads_no_note_and_says_so_in_the_receipt(tmp_path):
    # A note is never evidence (curriculum C2's fence): the administration names the notes the client showed (their
    # ids), never reads their words, and records an opened note as opened and unmeasured.
    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    token = _begin(ctx, session, commitment)["administrationToken"]
    ref = {"group": "notes", "kind": "note", "window_id": "w_book", "note_id": "note_1"}
    status = call(ctx, "check.expose", {"administrationToken": token, "ref": ref, "kind": "opened_veil"})["protectionStatus"]
    assert _rows(paths, "SELECT COUNT(*) FROM reveal_events") == [(0,)]
    assert status["coldNow"] is True
    [event] = [event for event in status["exposure"] if event["kind"] == "opened_veil"]
    assert event["unmeasured_notes"] == ["note_1"] and set(event["amounts"].values()) <= {0.0}


def test_an_answer_after_a_notes_veil_was_opened_is_practice_and_says_why(tmp_path):
    # Whether an unread note gave the answer away cannot be told, so the answer errs toward practice: it is submitted
    # declared primed (the attempt row's primed flag, which a rebuild reads), with no note read and no reveal row,
    # and the reply's sub-reason says a note was opened (an orchestrator interim the owner is still to confirm).
    from learnloop.substrate.replay import rebuild_derived_state
    from learnloop.vault.loader import load_vault

    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    token = _begin(ctx, session, commitment)["administrationToken"]
    call(ctx, "check.expose", {"administrationToken": token, "kind": "opened_veil",
                               "ref": {"group": "notes", "kind": "note", "window_id": "w_book", "note_id": "note_1"}})
    reply = _submit(ctx, token)
    assert (reply["cold"], reply["reason"], reply["primed_by"]) == (False, "primed", "unmeasured_note")
    assert _rows(paths, "SELECT primed FROM practice_attempts WHERE id = ?", (reply["attemptId"],)) == [(1,)]
    assert _rows(paths, "SELECT COUNT(*) FROM reveal_events") == [(0,)]
    assert C.resolve_disposition(repository, commitment) == "one_check_pending"

    def projection() -> dict[str, Any]:
        mastery = {lo: (round(state.logit_mean, 9), round(state.logit_variance, 9), state.evidence_count)
                   for lo, state in repository.mastery_states().items()}
        return {"mastery": mastery, "primed": _rows(paths, "SELECT id, primed FROM practice_attempts ORDER BY id")}

    live = projection()
    rebuild_derived_state(load_vault(paths.root), repository)
    assert projection() == live


# -- submitting, settling, competing surfaces (owner ruling Q3) -------------------------------------------------------

def test_submit_records_one_attempt_on_the_reader_surface_settles_and_is_idempotent(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    token = _begin(ctx, session, commitment)["administrationToken"]
    first = _submit(ctx, token)
    assert (first["cold"], first["reason"]) == (True, "on_your_own")
    attempt_id = first["attemptId"]
    assert _rows(paths, "SELECT entry_surface, submission_id FROM practice_attempts WHERE id = ?", (attempt_id,)) == [
        (IA.SURFACE, "inline:sub_1")]
    assert _rows(paths, "SELECT state, attempt_id, submission_id FROM check_administrations") == [
        ("submitted", attempt_id, "sub_1")]
    again = _submit(ctx, token)
    assert again["attemptId"] == attempt_id and (again["cold"], again["reason"]) == (True, "on_your_own")
    assert _rows(paths, "SELECT COUNT(*) FROM practice_attempts WHERE practice_item_id = ?", (ITEM,))[0][0] == 1
    with pytest.raises(SidecarError) as other:
        _submit(ctx, token, submission_id="sub_2")
    assert other.value.code == "already_submitted"


def test_a_later_answer_after_today_settled_the_check_is_practice_and_ordinary_evidence(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    token = _begin(ctx, session, commitment)["administrationToken"]
    # Today answered first (a deep link; the lock is a courtesy, the first settling attempt wins).
    today = call(ctx, "submit_attempt", {"sessionId": session, "practiceItemId": ITEM, "answerMd": ANSWER,
                                         "attemptType": "independent_attempt", "submissionId": "today_1"})
    from learnloop.intent.checks import settle_answered_checks
    from learnloop.vault.loader import load_vault

    assert settle_answered_checks(load_vault(paths.root), repository) == [commitment]
    reply = _submit(ctx, token)
    assert (reply["cold"], reply["reason"]) == (False, "already_answered")
    assert reply["attemptId"] != today["attemptId"]
    assert _rows(paths, "SELECT primed FROM practice_attempts WHERE id = ?", (reply["attemptId"],)) == [(0,)]


def test_parity_with_check_once_in_today(tmp_path):
    """The same item, contract and answer give the same attempt, grade and settlement on either surface."""

    from learnloop.intent.checks import settle_answered_checks
    from learnloop.vault.loader import load_vault

    def record(paths, repository, attempt_id):
        row = _rows(paths, "SELECT practice_item_id, rubric_score, correctness, error_type, attempt_type, primed, "
                           "hints_used, learner_answer_md FROM practice_attempts WHERE id = ?", (attempt_id,))
        contracts = _rows(paths, "SELECT DISTINCT v.contract_hash FROM grading_evidence g JOIN assessment_contract_versions v "
                                 "ON v.id = g.assessment_contract_version_id WHERE g.attempt_id = ?", (attempt_id,))
        return row[0], contracts

    paths_a, ctx_a, session_a, repo_a = _sidecar(tmp_path, name="today")
    commitment_a = _due_check(repo_a)
    served = call(ctx_a, "get_practice_item", {"practiceItemId": ITEM, "sessionId": session_a})
    today = call(ctx_a, "submit_attempt", {"sessionId": session_a, "practiceItemId": ITEM, "answerMd": ANSWER,
                                           "attemptType": "independent_attempt", "submissionId": "s",
                                           "assessmentContractVersionId": served["assessmentContractVersionId"]})
    settle_answered_checks(load_vault(paths_a.root), repo_a)
    paths_b, ctx_b, session_b, repo_b = _sidecar(tmp_path, name="reader")
    commitment_b = _due_check(repo_b)
    token = _begin(ctx_b, session_b, commitment_b)["administrationToken"]
    inline = _submit(ctx_b, token)
    assert record(paths_a, repo_a, today["attemptId"]) == record(paths_b, repo_b, inline["attemptId"])
    assert record(paths_b, repo_b, inline["attemptId"])[1]  # graded under a frozen contract on both
    assert C.resolve_disposition(repo_a, commitment_a) == C.resolve_disposition(repo_b, commitment_b) == "satisfied"


# -- abandon and crash recovery ------------------------------------------------------------------------------------

def test_not_now_closes_with_no_attempt_and_the_duty_stays(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    token = _begin(ctx, session, commitment)["administrationToken"]
    call(ctx, "check.abandon_inline", {"administrationToken": token})
    assert _rows(paths, "SELECT state FROM check_administrations") == [("abandoned",)]
    assert _rows(paths, "SELECT kind FROM check_veil_sets ORDER BY seq") == [("begin",), ("close",)]
    assert _rows(paths, "SELECT COUNT(*) FROM practice_attempts WHERE practice_item_id = ?", (ITEM,))[0][0] == 0
    assert C.resolve_disposition(repository, commitment) == "one_check_pending"
    call(ctx, "check.abandon_inline", {"administrationToken": token})  # again: nothing more
    with pytest.raises(SidecarError) as closed:
        _submit(ctx, token)
    assert closed.value.code == "administration_closed"


def test_a_restart_reopens_the_open_card_with_its_veils(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    token = _begin(ctx, session, _due_check(repository))["administrationToken"]
    restarted = SidecarContext()
    restarted.load(paths.root)
    card = call(restarted, "check.open_inline", {})["administration"]
    assert card["administrationToken"] == token and card["itemRef"] == ITEM
    assert {ref["window_id"] for ref in card["protection"]["veiled"] if ref["kind"] == "window"} == {"w_pad", "w_thread"}


def test_a_crash_after_the_attempt_and_before_the_close_is_recovered_with_that_attempt(tmp_path, monkeypatch):
    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    token = _begin(ctx, session, commitment)["administrationToken"]

    def crash(*_args, **_kwargs):
        raise RuntimeError("the process stopped")

    monkeypatch.setattr(IA, "finish_submit", crash)
    with pytest.raises(Exception):
        _submit(ctx, token)
    monkeypatch.undo()
    assert _rows(paths, "SELECT state, submission_id FROM check_administrations") == [("open", "sub_1")]
    restarted = SidecarContext()
    restarted.load(paths.root)
    assert call(restarted, "check.open_inline", {})["administration"] is None
    attempt = _rows(paths, "SELECT id FROM practice_attempts WHERE submission_id = 'inline:sub_1'")[0][0]
    assert _rows(paths, "SELECT state, attempt_id FROM check_administrations") == [("submitted", attempt)]
    assert C.resolve_disposition(repository, commitment) == "satisfied"


def test_a_crash_after_the_submission_was_named_and_before_the_attempt_retries_to_one_attempt(tmp_path, monkeypatch):
    import learnloop_sidecar.handlers.practice as practice

    paths, ctx, session, repository = _sidecar(tmp_path)
    token = _begin(ctx, session, _due_check(repository))["administrationToken"]
    real = practice.submit_attempt_on

    def crash(*_args, **_kwargs):
        raise RuntimeError("the process stopped")

    monkeypatch.setattr(practice, "submit_attempt_on", crash)
    with pytest.raises(Exception):
        _submit(ctx, token)
    # No attempt: the restart read keeps the card open (nothing reached the attempt service).
    assert call(ctx, "check.open_inline", {})["administration"]["administrationToken"] == token
    monkeypatch.setattr(practice, "submit_attempt_on", real)
    reply = _submit(ctx, token)
    assert reply["cold"] is True
    assert _rows(paths, "SELECT COUNT(*) FROM practice_attempts WHERE practice_item_id = ?", (ITEM,))[0][0] == 1


def test_a_check_settled_elsewhere_while_open_is_closed_superseded_on_the_next_read(tmp_path):
    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    _begin(ctx, session, commitment)
    C.stop_commitment(repository, commitment_id=commitment) if hasattr(C, "stop_commitment") else C.satisfy_single_check(
        repository, commitment_id=commitment, administration_id="elsewhere")
    assert call(ctx, "check.open_inline", {})["administration"] is None
    assert _rows(paths, "SELECT state FROM check_administrations") == [("superseded",)]


# -- replay -----------------------------------------------------------------------------------------------------------

def test_the_projection_after_an_inline_answer_equals_a_whole_vault_rebuild(tmp_path):
    from learnloop.substrate.replay import rebuild_derived_state
    from learnloop.vault.loader import load_vault

    paths, ctx, session, repository = _sidecar(tmp_path)
    commitment = _due_check(repository)
    ref = _seed_block(ctx, EXPECTED)
    token = _begin(ctx, session, commitment)["administrationToken"]
    call(ctx, "check.expose", {"administrationToken": token, "ref": ref, "kind": "opened_veil"})
    _submit(ctx, token)

    def projection() -> dict[str, Any]:
        mastery = {lo: (round(state.logit_mean, 9), round(state.logit_variance, 9), state.evidence_count)
                   for lo, state in repository.mastery_states().items()}
        facets = sorted((cell.facet_id, cell.capability, round(cell.direct_positive_mass, 9),
                         round(cell.direct_negative_mass, 9), round(cell.certification_credit, 9))
                        for cell in repository.facet_capability_evidence_all())
        return {"mastery": mastery, "facets": facets,
                "administrations": _rows(paths, "SELECT administration_token, state FROM check_administrations"),
                "veil_sets": _rows(paths, "SELECT veil_set_id FROM check_veil_sets ORDER BY seq")}

    live = projection()
    rebuild_derived_state(load_vault(paths.root), repository)
    assert projection() == live
