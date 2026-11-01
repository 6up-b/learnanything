"""Reader workbench RW6b part 2: the session narrative (spec_reader_workbench_v1
§9.2, §9.5, §9.6; UX §4.8, W14; G25; docs/reviews/reader-rw6b-p2-digest-card.md).

* Written once per session, in the background, from the session's typed
  summary only (the digest row's ``summary_json``: no learner text), on route
  ``reader_digest`` through the routed, capped, receipted path.
* Code validates the citations against the summary and the 120-word bound;
  an invalid narrative is dropped, why is recorded, and it is never paid for
  again.
* ``digest.narrative_enabled`` / ``digest.enabled`` off: no route call and no
  narrative in any payload (part 1 exactly).
* W14 states: landed, failed (dropped), capped, unreachable (plan down, no
  price, no route), pending.
* Never evidence: rebuild --shadow stays 0/0/0 with a narrative present; a
  narrative written meanwhile never supersedes part 1's plan.

Fakes only; no model call anywhere.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.execution import report_call_usage
from learnloop.ai.isolation import TOOL_FREE
from learnloop.ai.spend import SpendLimitExceeded
from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, STRUCTURED_COMPLETION
from learnloop.db.stores import reader_digests as RDG
from learnloop.instructional import reader_digest as RN
from learnloop.reader import reader_sessions as RS
from learnloop.vault.loader import load_vault
from tests.recap_fixtures import EXT, ask, at, call
from tests.recap_fixtures import context as _plain_context
from tests.structured_ai import StructuredClientFake
from tests.test_reader_followups import FakeSearch, _candidate, _now, _plan, _seeded

QUESTION = "WHY_THREE_FACTORS_8812"
ANSWER_TEXT = "U Sigma V^T"


def payload_of(prompt: str) -> dict[str, Any]:
    return json.loads(prompt[prompt.index("{", prompt.index("prompt_version")):])


class NarrativeFake(StructuredClientFake):
    """``reader_digest``: cites the summary's first citable id unless told otherwise."""

    provider_name = "fake_digest"
    provider_type = "codex_sdk"
    model = "fake-digest-model"

    def __init__(self, *, text: str = "You worked one problem with the book open and asked why there are three "
                                      "factors.", cite: list[str] | None = None, fail: Exception | None = None,
                 provider_type: str = "codex_sdk") -> None:
        self.text = text
        self.cite = cite
        self.fail = fail
        self.provider_type = provider_type
        self.payloads: list[dict[str, Any]] = []
        self.prompts: list[str] = []

    def supports(self, capability: str) -> bool:
        return capability in {STRUCTURED_COMPLETION, BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, TOOL_FREE}

    def complete(self, request: Any) -> Any:
        payload = payload_of(request.prompt)
        self.payloads.append(payload)
        self.prompts.append(request.prompt)
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 80,
                           "resolved_model": self.model})
        if self.fail is not None:
            raise self.fail
        cited = self.cite if self.cite is not None else payload["citable_event_ids"][:1]
        return request.result_model.model_validate({"narrative": self.text, "cited_event_ids": cited})

    @property
    def calls(self) -> int:
        return len(self.payloads)


def context(root, *, reader_digest_client=None):
    ctx = _plain_context(root)
    ctx.reader_digest_client = reader_digest_client
    return ctx


def _session_with_question(tmp_path, *, config: str | None = None):
    vault, repo, _session = _seeded(tmp_path, config=config)
    ask(vault, repo, QUESTION, 5)
    session = RS.sessions_for_source(repo, EXT)[0]
    row = _plan(vault, repo, session, FakeSearch([_candidate("pi_svd_define_002", 0.99, 0.01, 1.0)]))
    return vault, repo, row


def _row(repo, digest_id: str) -> dict[str, Any]:
    with repo.connection() as connection:
        return RDG.digest(connection, digest_id)


def _verdicts(repo, digest_id: str) -> list[dict[str, Any]]:
    with repo.connection() as connection:
        return [dict(r) for r in connection.execute(
            "SELECT verdict, judge, judge_model, prompt_version, rationale FROM judgment_ledger "
            "WHERE task = ? AND left_id = ? ORDER BY created_at", (RN.LEDGER_TASK, digest_id))]


# -- generation, once, from the typed summary only ---------------------------------------------


def test_the_narrative_is_written_once_from_the_typed_summary_with_valid_citations(tmp_path):
    vault, repo, row = _session_with_question(tmp_path)
    fake = NarrativeFake()
    result = RN.narrate_digest(vault, repo, row["id"], client=fake, now=_now(), clock=at(300))
    assert result.status == "narrated" and fake.calls == 1
    stored = _row(repo, row["id"])
    assert stored["narrative_md"] == fake.text
    assert stored["cited_event_ids"] and set(stored["cited_event_ids"]) <= RN.citable_ids(stored["summary"])
    assert stored["model"] == "fake-digest-model" and stored["prompt_version"] == RN.prompt_version(vault)
    [verdict] = _verdicts(repo, row["id"])
    assert verdict["verdict"] == "kept" and verdict["judge"] == "verifier"
    # Receipted: the routed, capped path wrote its receipt.
    with repo.connection() as connection:
        purposes = {r[0] for r in connection.execute(
            "SELECT purpose FROM model_call_receipts WHERE owner_kind = ?", (RN.OWNER_KIND,))}
    assert purposes == {RN.PURPOSE}
    # Once per session: a second narration makes no call.
    again = RN.narrate_digest(vault, repo, row["id"], client=fake, now=_now(), clock=at(301))
    assert again.status == "already" and fake.calls == 1
    # The part 1 row is otherwise untouched (its planning clock included).
    assert RDG.without_narrative(stored) == RDG.without_narrative(row)


def test_the_prompt_carries_the_typed_summary_and_never_the_learners_words(tmp_path):
    # With the learner-blindness relax's quotes off (on, the learner's own
    # inquiry words may travel: tests/test_learner_blindness_relax.py).
    vault, repo, row = _session_with_question(tmp_path, config="[digest]\nnarrative_quotes_inquiry = false\n")
    vault = load_vault(vault.root)
    fake = NarrativeFake()
    RN.narrate_digest(vault, repo, row["id"], client=fake, now=_now(), clock=at(300))
    [payload] = fake.payloads
    assert payload["summary"] == json.loads(json.dumps(row["summary"]))
    assert payload["max_words"] == RN.MAX_WORDS
    assert set(payload["citable_event_ids"]) == RN.citable_ids(row["summary"])
    # The question's id is citable; the learner's words (question, answer) never travel.
    assert QUESTION not in fake.prompts[0] and ANSWER_TEXT not in fake.prompts[0]
    assert "titles" in payload and set(payload["titles"]) == {"learning_objects", "sections"}


def test_citable_ids_are_the_summarys_event_ids():
    summary = {
        "inquiries": {"opened": [{"root_exchange_id": "ex1", "question_event_id": "q1"}],
                      "resolved": [], "still_open": [{"root_exchange_id": "ex1", "question_event_id": "q1"}]},
        "inquiry_exchanges": ["ex1", "ex2"],
        "workbench": [{"session_id": "wb1", "attempt_id": "att1"}],
        "observations": [{"source_event_ids": ["ev9"], "root_exchange_id": "ex1"}],
        "predictions_missed": [{"source_event_ids": ["ev10"]}],
        "gaps_named": [{"gap_id": "gap1", "source_id": "q1"}],
        "claims_needing_independent_check": [{"facet_id": "recall", "attempt_ids": ["att1", "att2"]}],
        "sections_read": [{"section_id": "sec1"}],
    }
    assert RN.citable_ids(summary) == {"ex1", "q1", "ex2", "wb1", "att1", "ev9", "ev10", "gap1", "att2"}
    assert "sec1" not in RN.citable_ids(summary)  # a section is not an event


# -- the checks: citations and the word bound --------------------------------------------------


def _answer(text: str, cited: list[str]) -> RN.ReaderDigestNarrativeV1:
    return RN.ReaderDigestNarrativeV1(narrative=text, cited_event_ids=cited)


def test_the_word_bound_is_120_words():
    summary = {"inquiry_exchanges": ["ex1"]}
    assert RN.validate_narrative(_answer(" ".join(["word"] * 120), ["ex1"]), summary) == []
    assert RN.validate_narrative(_answer(" ".join(["word"] * 121), ["ex1"]), summary) == ["over_word_cap:121"]


def test_a_citation_outside_the_summary_or_none_at_all_is_refused():
    summary = {"inquiry_exchanges": ["ex1"]}
    assert RN.validate_narrative(_answer("Fine.", ["ex1", "bogus"]), summary) == ["unknown_citations:bogus"]
    assert RN.validate_narrative(_answer("Fine.", []), summary) == ["no_citations"]
    assert RN.validate_narrative(_answer("   ", ["ex1"]), summary) == ["empty"]


def test_the_wells_evidence_markers_never_appear_in_a_narrative():
    summary = {"inquiry_exchanges": ["ex1"]}
    assert RN.validate_narrative(_answer("You ● demonstrated it.", ["ex1"]), summary) == ["evidence_marker"]


def test_an_invalid_citation_drops_the_narrative_records_why_and_is_never_paid_again(tmp_path):
    vault, repo, row = _session_with_question(tmp_path)
    fake = NarrativeFake(cite=["evt_bogus"])
    result = RN.narrate_digest(vault, repo, row["id"], client=fake, now=_now(), clock=at(300))
    assert result.status == "dropped" and result.reasons == ["unknown_citations:evt_bogus"]
    stored = _row(repo, row["id"])
    assert stored["narrative_md"] is None and stored["prompt_version"] == RN.prompt_version(vault)
    [verdict] = _verdicts(repo, row["id"])
    assert verdict["verdict"] == "dropped"
    assert json.loads(verdict["rationale"])["reasons"] == ["unknown_citations:evt_bogus"]
    assert RN.narrate_digest(vault, repo, row["id"], client=fake, now=_now()).status == "already"
    assert fake.calls == 1
    view = RN.narrative_view(vault, repo, extraction_id=EXT, session_key=row["session_key"], now=_now(),
                             client=fake)
    assert view["state"] == "failed" and "text" not in view


def test_an_overlong_narrative_is_dropped(tmp_path):
    vault, repo, row = _session_with_question(tmp_path)
    fake = NarrativeFake(text=" ".join(["read"] * 121))
    result = RN.narrate_digest(vault, repo, row["id"], client=fake, now=_now(), clock=at(300))
    assert result.status == "dropped" and result.reasons == ["over_word_cap:121"]
    assert _row(repo, row["id"])["narrative_md"] is None


def test_a_session_on_exam_material_is_never_sent(tmp_path, monkeypatch):
    from learnloop.content.sources import exam_material as EM

    vault, repo, row = _session_with_question(tmp_path)
    monkeypatch.setattr(EM, "exam_withheld", lambda _v, _r, keys: frozenset(tuple(k) for k in keys))
    fake = NarrativeFake()
    result = RN.narrate_digest(vault, repo, row["id"], client=fake, now=_now(), clock=at(300))
    assert result.status == "dropped" and result.reasons == ["exam_material"] and fake.calls == 0


# -- the switches ----------------------------------------------------------------------------------


@pytest.mark.parametrize("config", ["[digest]\nnarrative_enabled = false\n", "[digest]\nenabled = false\n"])
def test_switched_off_there_is_no_route_call_and_no_narrative_anywhere(tmp_path, config):
    vault, repo, row = _session_with_question(tmp_path, config=config)
    vault = load_vault(vault.root)
    fake = NarrativeFake()
    assert RN.narrate_digest(vault, repo, row["id"], client=fake, now=_now()).status == "disabled"
    assert RN.narrate_waiting(vault, repo, now=_now(), client=fake) == []
    assert RN.digests_waiting(vault, repo, now=_now(), client=fake) == []
    assert fake.calls == 0
    assert RN.narrative_view(vault, repo, extraction_id=EXT, session_key=row["session_key"], now=_now(),
                             client=fake) is None
    ctx = context(vault.root, reader_digest_client=fake)
    try:
        card = call(ctx, "reader.recap", {"extractionId": EXT, "visitId": "v_now"})["recap"]
        assert "narrative" not in card and "comingUp" in card
        wrap = call(ctx, "reader.wrap_up", {"extractionId": EXT})
        assert "narrative" not in wrap and "comingUp" in wrap
    finally:
        ctx.close()
    assert fake.calls == 0


# -- W14's states: capped, unreachable (plan down, no price), pending ---------------------------


def test_a_metered_route_past_todays_cap_is_capped_and_sends_nothing(tmp_path):
    vault, repo, row = _session_with_question(
        tmp_path, config="[digest]\nprice_per_million = 1.0\nmax_daily_cost_usd = 0.0\n")
    vault = load_vault(vault.root)
    fake = NarrativeFake(provider_type="openrouter")
    result = RN.narrate_digest(vault, repo, row["id"], client=fake, now=_now(), clock=at(300))
    assert result.status == "capped" and fake.calls == 0
    assert _row(repo, row["id"])["prompt_version"] is None  # retried later, never "once" spent
    view = RN.narrative_view(vault, repo, extraction_id=EXT, session_key=row["session_key"], now=_now(),
                             client=fake)
    assert view["state"] == "capped" and "$0.00" in view["message"]
    assert RN.digests_waiting(vault, repo, now=_now(), client=fake) == []  # no idle job


def test_a_spend_stop_inside_the_call_is_capped(tmp_path):
    vault, repo, row = _session_with_question(tmp_path)
    fake = NarrativeFake(fail=SpendLimitExceeded("max_calls reached"))
    result = RN.narrate_digest(vault, repo, row["id"], client=fake, now=_now(), clock=at(300))
    assert result.status == "capped" and _row(repo, row["id"])["prompt_version"] is None
    view = RN.narrative_view(vault, repo, extraction_id=EXT, session_key=row["session_key"], now=_now(),
                             client=fake)
    assert view["state"] == "capped"


def test_an_unpriced_metered_route_is_refused_before_sending(tmp_path):
    vault, repo, row = _session_with_question(tmp_path)
    fake = NarrativeFake(provider_type="openrouter")
    result = RN.narrate_digest(vault, repo, row["id"], client=fake, now=_now(), clock=at(300))
    assert result.status == "unpriced" and fake.calls == 0
    view = RN.narrative_view(vault, repo, extraction_id=EXT, session_key=row["session_key"], now=_now(),
                             client=fake)
    assert view["state"] == "unreachable" and "digest.price_per_million" in view["message"]


def test_the_plan_down_means_no_narrative_and_no_other_provider(tmp_path, monkeypatch):
    from learnloop.practice_index.paid import PaidRoute

    vault, repo, row = _session_with_question(tmp_path)
    monkeypatch.delenv(RN.MODELS_ENV, raising=False)
    planned = PaidRoute(RN.ROUTE_TASK, "chatgpt", "chatgpt_plan", "gpt-plan", "subscription")
    monkeypatch.setattr(RN, "plan_route", lambda *_a, **_k: planned)
    resolved: list[Any] = []

    def plan_down(_vault, route):
        resolved.append(route)
        return None, "The ChatGPT plan is unavailable (signed out)."

    monkeypatch.setattr(RN, "resolve_client", plan_down)
    result = RN.narrate_digest(vault, repo, row["id"], now=_now(), clock=at(300))
    assert result.status == "unavailable" and "signed out" in (result.reason or "")
    assert [route.provider for route in resolved] == ["chatgpt"]  # pinned to the plan, never re-routed
    assert _row(repo, row["id"])["prompt_version"] is None
    view = RN.narrative_view(vault, repo, extraction_id=EXT, session_key=row["session_key"], now=_now())
    assert view["state"] == "unreachable" and "signed out" in view["message"]
    with repo.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM model_call_receipts WHERE owner_kind = ?",
                                  (RN.OWNER_KIND,)).fetchone()[0] == 0


def test_a_provider_failure_is_retried_later_and_then_lands(tmp_path):
    vault, repo, row = _session_with_question(tmp_path)
    failing = NarrativeFake(fail=AIProviderUnavailable("timed out"))
    first = RN.narrate_digest(vault, repo, row["id"], client=failing, now=_now(), clock=at(300))
    assert first.status == "failed" and _row(repo, row["id"])["prompt_version"] is None
    assert RN.narrative_view(vault, repo, extraction_id=EXT, session_key=row["session_key"], now=_now(),
                             client=failing)["state"] == "unreachable"
    fake = NarrativeFake()
    assert RN.narrate_digest(vault, repo, row["id"], client=fake, now=_now(), clock=at(310)).status == "narrated"
    view = RN.narrative_view(vault, repo, extraction_id=EXT, session_key=row["session_key"], now=_now(),
                             client=fake)
    assert view["state"] == "landed" and view["label"] == "summary written by LearnLoop's model"
    assert view["authority"] == "salience_only" and view["text"] == fake.text


def test_a_waiting_session_reads_pending_and_a_running_one_reads_nothing(tmp_path):
    vault, repo, row = _session_with_question(tmp_path)
    fake = NarrativeFake()
    view = RN.narrative_view(vault, repo, extraction_id=EXT, session_key=row["session_key"], now=_now(),
                             client=fake)
    assert view["state"] == "pending" and view["digest_id"] == row["id"]
    # No digest row (a session part 1 has not planned, or one without activity): nothing to show.
    assert RN.narrative_view(vault, repo, extraction_id=EXT, session_key="v_other", now=_now(), client=fake) is None
    assert RN.digests_waiting(vault, repo, now=_now(), client=fake) == [row["id"]]


# -- the RPCs and the background job -------------------------------------------------------------


def test_the_card_and_wrap_up_carry_the_landed_narrative(tmp_path):
    vault, repo, row = _session_with_question(tmp_path)
    fake = NarrativeFake()
    RN.narrate_digest(vault, repo, row["id"], client=fake, now=_now(), clock=at(300))
    ctx = context(vault.root, reader_digest_client=fake)
    try:
        card = call(ctx, "reader.recap", {"extractionId": EXT, "visitId": "v_now"})["recap"]
        assert card["narrative"]["state"] == "landed" and card["narrative"]["text"] == fake.text
        assert card["narrative"]["citedEventIds"] == _row(repo, row["id"])["cited_event_ids"]
        wrap = call(ctx, "reader.wrap_up", {"extractionId": EXT})
        assert wrap["narrative"]["state"] == "landed"
    finally:
        ctx.close()
    assert fake.calls == 1  # reading the card never calls the model


def test_the_background_job_narrates_waiting_sessions(tmp_path):
    from learnloop_sidecar.background_jobs import background_jobs
    from learnloop_sidecar.handlers.reader_followups import prepare_followups

    vault, repo, row = _session_with_question(tmp_path)
    fake = NarrativeFake()
    ctx = context(vault.root, reader_digest_client=fake)
    try:
        loaded, repository = ctx.require_vault()
        prepare_followups(ctx, loaded, repository)
        for thread in background_jobs(ctx).running:
            thread.join(timeout=30)
        assert fake.calls == 1 and _row(repo, row["id"])["narrative_md"] == fake.text
        prepare_followups(ctx, loaded, repository)  # nothing waits: no second call
        for thread in background_jobs(ctx).running:
            thread.join(timeout=30)
        assert fake.calls == 1
    finally:
        ctx.close()


def test_with_the_narrative_off_the_queue_build_starts_no_narration_job(tmp_path):
    from learnloop_sidecar.background_jobs import background_jobs
    from learnloop_sidecar.handlers.reader_followups import prepare_followups

    vault, _repo, _row_ = _session_with_question(tmp_path, config="[digest]\nnarrative_enabled = false\n")
    fake = NarrativeFake()
    ctx = context(vault.root, reader_digest_client=fake)
    try:
        loaded, repository = ctx.require_vault()
        prepare_followups(ctx, loaded, repository)
        assert background_jobs(ctx).running == [] and fake.calls == 0
    finally:
        ctx.close()


# -- part 1 is undisturbed; never evidence -------------------------------------------------------


def test_a_narrative_written_meanwhile_never_supersedes_part_1s_plan(tmp_path):
    vault, repo, session = _seeded(tmp_path)
    first = _plan(vault, repo, session, FakeSearch([_candidate("pi_svd_define_002", 0.99, 0.01, 1.0)],
                                                   raise_first=SpendLimitExceeded("cap")))
    assert first["status"] == "incomplete"

    class NarratesMeanwhile(FakeSearch):
        """The narrative lands while the re-asked search runs (another
        process's job), between the plan's read and its publication."""

        def __call__(self, *args, **kwargs):
            assert RN.narrate_digest(vault, repo, first["id"], client=NarrativeFake(), now=_now(),
                                     clock=at(305)).status == "narrated"
            return super().__call__(*args, **kwargs)

    second = _plan(vault, repo, session, NarratesMeanwhile([_candidate("pi_svd_define_002", 0.99, 0.01, 1.0)]),
                   minutes=310)
    assert second["status"] == "planned" and second["followup_commitment_ids"]
    assert second["narrative_md"] == NarrativeFake().text  # the narrative stays


# -- Codex review F2: narration does not need follow-ups ----------------------------------------


def _commitment_count(repo) -> int:
    with repo.connection() as connection:
        return connection.execute("SELECT COUNT(*) FROM commitments").fetchone()[0]


def _ended_session_without_digest(tmp_path, config: str, **kwargs):
    vault, repo, _session = _seeded(tmp_path, config=config, **kwargs)
    ask(vault, repo, QUESTION, 5)
    with repo.connection() as connection:
        assert RDG.digests(connection) == []
    return vault, repo, RS.sessions_for_source(repo, EXT)[0]


def test_with_follow_ups_off_an_ended_session_is_summarized_and_narrated(tmp_path):
    vault, repo, session = _ended_session_without_digest(tmp_path, "[followups]\nenabled = false\n")
    before = _commitment_count(repo)
    assert [s.session_id for s in RN.sessions_to_summarize(vault, repo, now=_now())] == [session.session_id]
    [row] = RN.summarize_ended_sessions(vault, repo, now=_now(), clock=at(300))
    assert row["status"] == "incomplete" and row["followup_commitment_ids"] == []
    assert row["valuation"][RN.NOT_PLANNED_KEY] == "followups_off" and row["valuation"]["chosen"] == []
    assert row["summary"]["activity"] and _commitment_count(repo) == before  # nothing planned
    assert RN.sessions_to_summarize(vault, repo, now=_now()) == []  # once
    fake = NarrativeFake()
    assert RN.narrate_digest(vault, repo, row["id"], client=fake, now=_now(), clock=at(300)).status == "narrated"
    view = RN.narrative_view(vault, repo, extraction_id=EXT, session_key=session.session_id, now=_now())
    assert view["state"] == "landed" and view["text"] == fake.text
    # Still the typed summary; the learner's own words travel only as the
    # learner-blindness relax's inquiry quotes (digest.narrative_quotes_inquiry).
    payload = fake.payloads[0]
    assert QUESTION not in json.dumps(payload["summary"]) and QUESTION not in json.dumps(payload["titles"])
    assert all(QUESTION in quote["learner_question"] for quote in payload["inquiry_quotes"])

    # Follow-ups switched on later plan the session as any unfinished one; the narrative stays.
    from learnloop.instructional import reader_followups as RF
    from tests.ux_phase1_support import set_config

    set_config(vault.root, {("followups", "enabled"): True})
    vault = load_vault(vault.root)
    assert [s.session_id for s in RF.sessions_to_plan(vault, repo, now=_now())] == [session.session_id]
    planned = _plan(vault, repo, session, FakeSearch([_candidate("pi_svd_define_002", 0.99, 0.01, 1.0)]))
    assert planned["status"] == "planned" and planned["followup_commitment_ids"]
    assert RN.NOT_PLANNED_KEY not in planned["valuation"] and planned["narrative_md"] == fake.text


def test_below_the_follow_ups_successor_the_summary_row_says_so(tmp_path):
    from learnloop.algorithm_versions import READER_FOLLOWUPS_VERSIONS

    predecessor = "mvp-0.38"
    assert predecessor not in READER_FOLLOWUPS_VERSIONS
    vault, repo, _session = _ended_session_without_digest(tmp_path, "", version=predecessor)
    [row] = RN.summarize_ended_sessions(vault, repo, now=_now(), clock=at(300))
    assert row["valuation"][RN.NOT_PLANNED_KEY] == "below_followups_successor"


@pytest.mark.parametrize("config", ["[digest]\nnarrative_enabled = false\n[followups]\nenabled = false\n", ""])
def test_no_summary_row_with_narration_off_or_follow_ups_live(tmp_path, config):
    vault, repo, _session = _ended_session_without_digest(tmp_path, config) if config else (
        *_seeded(tmp_path)[:2], None)
    assert RN.sessions_to_summarize(vault, repo, now=_now()) == []
    assert RN.summarize_ended_sessions(vault, repo, now=_now()) == []


def test_the_queue_build_narrates_a_session_with_follow_ups_off(tmp_path, monkeypatch):
    from learnloop_sidecar.background_jobs import background_jobs
    from learnloop_sidecar.handlers import reader_followups as handler

    vault, repo, session = _ended_session_without_digest(tmp_path, "[followups]\nenabled = false\n")
    monkeypatch.setattr(handler, "_now", lambda: _now())
    fake = NarrativeFake()
    ctx = context(vault.root, reader_digest_client=fake)
    try:
        loaded, repository = ctx.require_vault()
        handler.prepare_followups(ctx, loaded, repository)
        for thread in background_jobs(ctx).running:
            thread.join(timeout=30)
        with repo.connection() as connection:
            row = RDG.digest_for_session(connection, EXT, session.session_id)
        assert fake.calls == 1 and row["narrative_md"] == fake.text and row["followup_commitment_ids"] == []
    finally:
        ctx.close()


# -- Codex review F3: one paid call per session across processes ---------------------------------


class BlockingFake(NarrativeFake):
    """Holds its call open until released (two narrations overlap)."""

    def __init__(self, **kwargs: Any) -> None:
        import threading

        super().__init__(**kwargs)
        self.entered = threading.Event()
        self.release = threading.Event()

    def complete(self, request: Any) -> Any:
        self.entered.set()
        assert self.release.wait(30)
        return super().complete(request)


def test_overlapping_narrations_from_two_repositories_pay_once(tmp_path):
    import threading

    from learnloop.db.repositories import Repository

    vault, repo, row = _session_with_question(tmp_path)
    first = BlockingFake()
    results: dict[str, Any] = {}
    worker = threading.Thread(target=lambda: results.update(first=RN.narrate_digest(
        vault, repo, row["id"], client=first, now=_now(), clock=at(300))))
    worker.start()
    try:
        assert first.entered.wait(30)
        # Another process: its own repository on the same database, while the first call is in flight.
        other_repo = Repository(repo.sqlite_path)
        second = NarrativeFake(text="A second narrative.")
        result = RN.narrate_digest(load_vault(vault.root), other_repo, row["id"], client=second, now=_now(),
                                   clock=at(301))
        assert result.status == "claimed" and second.calls == 0
    finally:
        first.release.set()
        worker.join(timeout=30)
    assert results["first"].status == "narrated" and first.calls == 1
    assert _row(repo, row["id"])["narrative_md"] == first.text
    # Afterwards the session is narrated: nobody pays again.
    later = NarrativeFake()
    assert RN.narrate_digest(vault, Repository(repo.sqlite_path), row["id"], client=later, now=_now(),
                             clock=at(400)).status == "already"
    assert later.calls == 0


def test_the_narrative_is_written_once_even_when_two_writers_race(tmp_path):
    vault, repo, row = _session_with_question(tmp_path)
    with repo.connection() as connection:
        assert RDG.set_narrative(connection, row["id"], narrative_md="first", cited_event_ids=["x"], model="m",
                                 prompt_version=RN.PROMPT_VERSION)
        assert not RDG.set_narrative(connection, row["id"], narrative_md="second", cited_event_ids=["y"],
                                     model="m", prompt_version=RN.PROMPT_VERSION)
        connection.commit()
    assert _row(repo, row["id"])["narrative_md"] == "first"


def test_rebuild_shadow_is_zero_with_a_narrative_present(tmp_path):
    from learnloop.substrate.replay import rebuild_derived_state
    from learnloop.substrate.shadow_rebuild import shadow_rebuild

    vault, repo, row = _session_with_question(tmp_path)
    rebuild_derived_state(vault, repo, clock=at(250))
    RN.narrate_digest(vault, repo, row["id"], client=NarrativeFake(), now=_now(), clock=at(300))
    with repo.connection() as connection:
        digests_before = connection.execute("SELECT * FROM reader_session_digests").fetchall()
    result = shadow_rebuild(load_vault(vault.root))
    assert result.learner_state_diff["summary"] == {"mastery": 0, "facet": 0, "schedule": 0}
    assert result.live_database_unchanged is True
    with repo.connection() as connection:
        assert connection.execute("SELECT * FROM reader_session_digests").fetchall() == digests_before


# -- Codex re-review F3: the claim's liveness before the request and at publication --------------


def _lapse_and_take_over(repo, digest_id: str) -> None:
    """The holder's lease lapses (its heartbeat stalled) and another process re-claims it."""

    from learnloop.clock import utc_now_iso
    from learnloop.db.stores.judgment_claims import CLAIMED, claim_work

    key = RN.claim_key(digest_id)
    with repo.atomic():
        connection = repo.connection()
        connection.execute("UPDATE judgment_work_claims SET lease_expires_at = '2000-01-01T00:00:00+00:00' "
                           "WHERE claim_key = ?", (key,))
        status, _epoch = claim_work(connection, claim_key=key, task=RN.CLAIM_TASK, producer=RN.OWNER_KIND,
                                    prompt_version=None, input_hash="", owner="proc_other:taker",
                                    now=utc_now_iso(), lease_seconds=120)
    assert status == CLAIMED


def test_a_lease_lost_before_the_request_sends_nothing_and_writes_nothing(tmp_path, monkeypatch):
    vault, repo, row = _session_with_question(tmp_path)
    real = RN.build_prompt

    def build_then_lose(*args: Any, **kwargs: Any) -> str:
        prompt = real(*args, **kwargs)
        _lapse_and_take_over(repo, row["id"])
        return prompt

    monkeypatch.setattr(RN, "build_prompt", build_then_lose)
    client = NarrativeFake()
    result = RN.narrate_digest(vault, repo, row["id"], client=client, now=_now(), clock=at(300))
    assert result.status == "claimed"
    assert client.calls == 0
    assert _row(repo, row["id"])["prompt_version"] is None
    assert _verdicts(repo, row["id"]) == []


def test_a_lease_lost_during_the_call_never_publishes_and_the_answer_is_not_paid_twice(tmp_path):
    import threading

    from learnloop.db.repositories import Repository

    vault, repo, row = _session_with_question(tmp_path)
    first = BlockingFake()
    results: dict[str, Any] = {}
    worker = threading.Thread(target=lambda: results.update(first=RN.narrate_digest(
        vault, repo, row["id"], client=first, now=_now(), clock=at(300))))
    worker.start()
    try:
        assert first.entered.wait(30)
        _lapse_and_take_over(repo, row["id"])
    finally:
        first.release.set()
        worker.join(timeout=30)
    # The stale holder paid for its answer but holds no lease: it publishes nothing.
    assert results["first"].status == "claimed" and first.calls == 1
    assert _row(repo, row["id"])["prompt_version"] is None
    assert _verdicts(repo, row["id"]) == []
    # Once the taker's lease is gone, the next holder lands the paid answer from its checkpoint, unasked.
    with repo.atomic():
        repo.connection().execute("UPDATE judgment_work_claims SET lease_expires_at = '2000-01-01T00:00:00+00:00' "
                                  "WHERE claim_key = ?", (RN.claim_key(row["id"]),))
    later = NarrativeFake(text="A different narrative.")
    result = RN.narrate_digest(load_vault(vault.root), Repository(repo.sqlite_path), row["id"], client=later,
                               now=_now(), clock=at(400))
    assert result.status == "narrated" and later.calls == 0
    assert _row(repo, row["id"])["narrative_md"] == first.text


# -- Final verify F3: no takeover sends while the predecessor's request may be outstanding ---------


class LeaseClock:
    """The claims' wall clock (``map_builder._lease_now``), moved by the test."""

    def __init__(self) -> None:
        from datetime import UTC, datetime

        self.now = datetime.now(UTC).replace(microsecond=0)

    def __call__(self) -> str:
        return self.now.isoformat()

    def advance(self, seconds: float) -> None:
        from datetime import timedelta

        self.now = self.now + timedelta(seconds=seconds)


class TimedFake(BlockingFake):
    """Holds its request open until released, remembering when (on the lease
    clock) it was sent and with what timeout. With ``enforce_timeout`` it acts
    as every transport does: released after its timeout ran out, it fails."""

    def __init__(self, clock: LeaseClock, *, enforce_timeout: bool = False, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.clock = clock
        self.enforce_timeout = enforce_timeout
        self.sent_at = None
        self.timeout_seconds = None

    def complete(self, request: Any) -> Any:
        from datetime import timedelta

        if self.sent_at is None:
            self.sent_at, self.timeout_seconds = self.clock.now, request.timeout_seconds
        self.entered.set()
        assert self.release.wait(30)
        if self.enforce_timeout and self.clock.now > self.sent_at + timedelta(seconds=float(request.timeout_seconds)):
            self.payloads.append({"timed_out": True})
            raise AIProviderUnavailable("the request timed out")
        return NarrativeFake.complete(self, request)


def _lease(repo, digest_id: str) -> tuple[str | None, Any]:
    from learnloop.clock import parse_utc

    with repo.connection() as connection:
        row = connection.execute("SELECT lease_owner, lease_expires_at FROM judgment_work_claims WHERE claim_key = ?",
                                 (RN.claim_key(digest_id),)).fetchone()
    return (row["lease_owner"], parse_utc(row["lease_expires_at"])) if row else (None, None)


def _completed_receipts(repo, digest_id: str) -> int:
    with repo.connection() as connection:
        return connection.execute("SELECT COUNT(*) FROM model_call_receipts WHERE owner_kind = ? AND owner_id = ? "
                                  "AND status = 'completed'", (RN.OWNER_KIND, digest_id)).fetchone()[0]


def _wait_for(predicate, what: str) -> None:
    import time

    deadline = time.monotonic() + 10
    while not predicate():
        assert time.monotonic() < deadline, what
        time.sleep(0.005)


@pytest.fixture
def lease_clock(monkeypatch):
    from learnloop.hints import map_builder

    clock = LeaseClock()
    monkeypatch.setattr(map_builder, "_lease_now", clock)
    # The heartbeat's interval, shortened so a test sees its beats; the lease is the narration's own.
    monkeypatch.setattr(map_builder, "CLAIM_HEARTBEAT_SECONDS", 0.005)
    return clock


def _start(vault, repo, digest_id: str, client) -> tuple[Any, dict[str, Any]]:
    import threading

    results: dict[str, Any] = {}
    worker = threading.Thread(target=lambda: results.update(result=RN.narrate_digest(
        vault, repo, digest_id, client=client, now=_now(), clock=at(300))))
    worker.start()
    assert client.entered.wait(30)
    return worker, results


def test_the_narration_lease_outlives_the_routes_request_timeout(tmp_path):
    from learnloop.hints import map_builder

    vault, repo, _row_ = _session_with_question(tmp_path)
    route = RN.NarrativeRoute(vault, repo, client=NarrativeFake(), envelope=None)
    assert route.request_timeout == float(vault.config.ai.timeout_seconds)
    lease = RN.narration_lease_seconds(route.request_timeout)
    # The margin is the claims' ordinary liveness lease, and it stays longer than the heartbeat interval.
    assert lease == route.request_timeout + map_builder.CLAIM_LEASE_SECONDS
    assert map_builder.CLAIM_LEASE_SECONDS > map_builder.CLAIM_HEARTBEAT_SECONDS
    assert RN.narration_lease_seconds(900.5) == 901 + map_builder.CLAIM_LEASE_SECONDS


def test_a_successor_never_sends_while_the_holder_renews_past_its_original_lease(tmp_path, lease_clock):
    from datetime import timedelta

    from learnloop.db.repositories import Repository

    vault, repo, row = _session_with_question(tmp_path)
    timeout = RN.NarrativeRoute(vault, repo, client=NarrativeFake(), envelope=None).request_timeout
    lease = RN.narration_lease_seconds(timeout)
    first = TimedFake(lease_clock)
    worker, results = _start(vault, repo, row["id"], first)
    try:
        holder, original = _lease(repo, row["id"])
        # The request carries the route's timeout, and the lease renewed just before it outlives it.
        assert first.timeout_seconds == timeout
        assert original >= first.sent_at + timedelta(seconds=lease) > first.sent_at + timedelta(seconds=timeout)
        # Held inside the request well past the original lease, renewing all the while.
        for _ in range(4):
            lease_clock.advance(lease / 3)
            _wait_for(lambda: _lease(repo, row["id"])[1] >= lease_clock.now + timedelta(seconds=lease),
                      "the holder's heartbeat renews its lease")
        assert lease_clock.now > original
        assert _lease(repo, row["id"])[0] == holder
        # Another process: the claim is held, so it sends nothing.
        second = NarrativeFake(text="A second narrative.")
        result = RN.narrate_digest(load_vault(vault.root), Repository(repo.sqlite_path), row["id"], client=second,
                                   now=_now(), clock=at(301))
        assert result.status == "claimed" and second.calls == 0
        assert _completed_receipts(repo, row["id"]) == 0
    finally:
        first.release.set()
        worker.join(timeout=30)
    assert results["result"].status == "narrated" and first.calls == 1
    assert _row(repo, row["id"])["narrative_md"] == first.text
    assert _completed_receipts(repo, row["id"]) == 1


def test_a_holder_that_stops_renewing_is_taken_over_only_after_its_request_timed_out(tmp_path, lease_clock,
                                                                                      monkeypatch):
    from datetime import timedelta

    from learnloop.db.repositories import Repository
    from learnloop.hints import map_builder

    vault, repo, row = _session_with_question(tmp_path)
    timeout = RN.NarrativeRoute(vault, repo, client=NarrativeFake(), envelope=None).request_timeout
    first = TimedFake(lease_clock, enforce_timeout=True)
    worker, results = _start(vault, repo, row["id"], first)
    try:
        holder, expires = _lease(repo, row["id"])
        real_renew = map_builder.renew_claim

        def dead_holder(connection, *, owner, **kwargs):
            # The holder's process died: its renewals stop (its heartbeat's writes never land).
            if owner == holder:
                raise RuntimeError("the holder is gone")
            return real_renew(connection, owner=owner, **kwargs)

        monkeypatch.setattr(map_builder, "renew_claim", dead_holder)
        # Just before the lease runs out its request may still be outstanding: no successor sends.
        lease_clock.advance((expires - lease_clock.now).total_seconds() - 1)
        early = NarrativeFake(text="Too early.")
        assert RN.narrate_digest(load_vault(vault.root), Repository(repo.sqlite_path), row["id"], client=early,
                                 now=_now(), clock=at(301)).status == "claimed"
        assert early.calls == 0 and _lease(repo, row["id"]) == (holder, expires)
        # Expired with nobody renewing it: by now the holder's request has timed out.
        lease_clock.advance(2)
        assert lease_clock.now > first.sent_at + timedelta(seconds=timeout)
        successor = NarrativeFake(text="The successor's narrative.")
        result = RN.narrate_digest(load_vault(vault.root), Repository(repo.sqlite_path), row["id"],
                                   client=successor, now=_now(), clock=at(302))
        assert result.status == "narrated" and successor.calls == 1
        assert _completed_receipts(repo, row["id"]) == 1
    finally:
        first.release.set()
        worker.join(timeout=30)
    # The holder's request had timed out; it neither retries nor publishes.
    assert results["result"].status == "claimed"
    assert first.payloads == [{"timed_out": True}]
    assert _row(repo, row["id"])["narrative_md"] == "The successor's narrative."
    assert _completed_receipts(repo, row["id"]) == 1
    assert [v["verdict"] for v in _verdicts(repo, row["id"])] == ["kept"]
