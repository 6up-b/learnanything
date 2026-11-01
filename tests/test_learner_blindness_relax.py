"""Learner-blindness relax (owner direction 2026-11-01: blindness only where it matters, the grader).

docs/reviews/learner-blindness-relax.md. Four model contexts may now read the
learner, each behind its own switch, none of them the grader:

1. the Reader tutor (``reader_tutor.learner_state_enabled``): readiness in
   words, TE0's confidence events and recent exchanges and outcomes on the
   passage's topics, through ``learner_protection``; none during a cold
   administration; the reserved-surface and cold in-flight exclusions stay;
2. the reader narrative (``digest.narrative_quotes_inquiry``): the learner's
   own inquiry words, with the cited-id, 120-word and well-marker checks;
3. the diagnoser (``diagnosis.history_includes_prior_analysis``): a
   randomized (default) or fixed arm re-feeding earlier analyses and
   workbench traces, recorded on the receipt and read per arm in the report;
4. AD's ``llm_v3`` history card (``adaptive_difficulty.history_answer_excerpts``):
   bounded answer excerpts through the material view, state ``v2``.

Pinned here: the blind grader's inputs are byte-identical in every arm and
switch setting; each switch off is byte-identical; nothing here writes an
attempt, a claim or mastery. Fakes only; no model call anywhere.
"""

from __future__ import annotations

import json
from contextlib import closing
from pathlib import Path
from typing import Any

import pytest

from learnloop import reader_learner_state as RLS
from learnloop.db.connection import connect
from learnloop.vault.loader import load_vault

READER_SWITCHES = {"retrieval_enabled": False, "offers_enabled": False}
EVIDENCE_TABLE_HINTS = ("mastery", "claim", "certification", "facet_capability", "fsrs", "grading_evidence")


def _items_on(vault: Any, lo_id: str) -> list[str]:
    return sorted(item_id for item_id, item in vault.practice_items.items() if item.learning_object_id == lo_id)


def _attempt(sqlite_path: Path, attempt_id: str, *, item_id: str, lo_id: str, at: str, correctness: float | None,
             attempt_type: str = "independent_attempt", hints: int = 0, answer: str = "my answer",
             tap: int | None = None) -> None:
    with closing(connect(sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO practice_attempts (id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "learner_answer_md, correctness, rubric_score, hints_used, created_at, answer_confidence) "
            "VALUES (?, ?, ?, 'short_answer', ?, ?, ?, ?, ?, ?, ?)",
            (attempt_id, item_id, lo_id, attempt_type, answer, correctness,
             None if correctness is None else correctness * 4, hints, at, tap))
        connection.commit()


def _question(repository: Any, *, context: str, item_id: str, attempt_id: str | None, question: str, answer: str,
              at: str) -> str:
    return repository.insert_question_event({
        "context": context, "practice_item_id": item_id, "attempt_id": attempt_id, "question_md": question,
        "answer_md": answer, "answer_status": "answered", "created_at": at,
    })


def _evidence_counts(sqlite_path: Path) -> dict[str, int]:
    with closing(connect(sqlite_path, read_only=True)) as connection:
        tables = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
        wanted = [name for name in tables if name == "practice_attempts"
                  or any(hint in name for hint in EVIDENCE_TABLE_HINTS)]
        return {name: connection.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0] for name in sorted(wanted)}


# -- 1. the Reader tutor ------------------------------------------------------------------------------


def _reader(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, learner_state: bool | None = None):
    import learnloop_sidecar.handlers.reader as reader_handler
    from tests.library_ask_fixtures import build_library_vault, context, set_config
    from tests.source_service_fakes import tool_tutor

    paths, repository, _spans = build_library_vault(tmp_path / "vault")
    set_config(paths, "reader_tutor", **READER_SWITCHES)
    if learner_state is not None:
        set_config(paths, "reader_tutor", learner_state_enabled=learner_state)
    tutor = tool_tutor(answer_md="The determinant vanishes there, so t is a root.")

    class Ready:
        ready = True

    monkeypatch.setattr(reader_handler, "ready_tutor_qa_provider", lambda vault: ("fake", Ready(), tutor))
    return paths, repository, tutor, context


def _seed_learner(paths: Any, repository: Any) -> dict[str, str]:
    vault = load_vault(paths.root)
    items = _items_on(vault, "lo_matrices")
    assert len(items) >= 2, items
    plain, probe = items[0], items[1]
    sqlite = paths.sqlite_path
    _attempt(sqlite, "att_old_right", item_id=plain, lo_id="lo_matrices", at="2026-09-01T09:00:00Z",
             correctness=1.0, hints=2, tap=4)
    _attempt(sqlite, "att_last_wrong", item_id=plain, lo_id="lo_matrices", at="2026-09-02T09:00:00Z",
             correctness=0.0, tap=5)
    # A diagnostic probe: protected, so neither it nor anything asked about it shows.
    _attempt(sqlite, "att_probe", item_id=probe, lo_id="lo_matrices", at="2026-09-03T09:00:00Z",
             correctness=1.0, attempt_type="diagnostic_probe", tap=1)
    _question(repository, context="feedback", item_id=plain, attempt_id="att_last_wrong",
              question="MY_OWN_FEEDBACK_QUESTION why the eigenvalue?", answer="SECRET_WORKED_SOLUTION 42",
              at="2026-09-02T10:00:00Z")
    _question(repository, context="practice", item_id=probe, attempt_id="att_probe",
              question="PROBE_QUESTION_TEXT", answer="PROBE_ANSWER_TEXT", at="2026-09-03T09:30:00Z")
    return {"plain": plain, "probe": probe}


def _ask(ctx_factory, paths, counts: dict[str, Any] | None = None, **extra):
    from tests.library_ask_fixtures import call

    ctx = ctx_factory(paths.root)
    try:
        ctx.require_vault()  # opening the vault syncs its state; the Ask is measured after it
        if counts is not None:
            counts["before"] = _evidence_counts(paths.sqlite_path)
        answer = call(ctx, "reader.ask", {"extractionId": "ext_text", "spanId": "t2",
                                          "question": "why is an eigenvalue a root?", **extra})
        if counts is not None:
            counts["after"] = _evidence_counts(paths.sqlite_path)
        return answer
    finally:
        ctx.close()


def test_the_reader_tutor_reads_the_learner_state_through_the_protection(tmp_path, monkeypatch):
    paths, repository, tutor, ctx_factory = _reader(tmp_path, monkeypatch)
    seeded = _seed_learner(paths, repository)
    counts: dict[str, Any] = {}
    answer = _ask(ctx_factory, paths, counts)
    [prompt] = tutor.prompts
    assert "+learner-state-v1" in prompt
    payload = json.loads(prompt[prompt.index("{", prompt.index("prompt_version")):])
    state = payload["context"]["learner_state"]
    [topic] = state["topics"]
    assert topic["readiness"] in RLS.READINESS_WORDS.values()
    # Outcomes in words, newest first, the probe left out.
    assert topic["recent_attempts"] == ["2026-09-02: wrong, unassisted", "2026-09-01: right, with 2 hints"]
    # The learner's own question shows; the feedback answer (written with the
    # rubric) does not, while the item can still be answered cold.
    [exchange] = topic["recent_tutor_questions"]
    assert "MY_OWN_FEEDBACK_QUESTION" in exchange["learner_question"]
    assert exchange["answer_left_out"] and "answer_shown" not in exchange
    for hidden in ("SECRET_WORKED_SOLUTION", "PROBE_QUESTION_TEXT", "PROBE_ANSWER_TEXT"):
        assert hidden not in prompt
    # TE0's confidence events now reach the Reader too (the probe's tap left out).
    events = payload["context"]["learner_confidence"]["topics"][0]["events"]
    assert events == ["2026-09-02: marked 5/5 sure; wrong", "2026-09-01: marked 4/5 sure; right"]
    # The task reads the state instead of the blind wording.
    assert "MUST NOT tune the answer to a supposed deficit" not in prompt
    manifest = answer["manifest"]
    assert manifest["version"].endswith("+learner-state-v1")
    assert manifest["excluded"] == ["assessment_reserved_surface", "cold_in_flight_response"]
    assert manifest["learnerState"]["given"] is True and manifest["learnerState"]["learningObjectIds"] == ["lo_matrices"]
    stored = repository.question_events(context="reader")[-1]["source_context"]["learner_state"]
    assert stored["counts"] == {"topics": 1, "attempts": 2, "exchanges": 1, "answers_left_out": 1}
    # No new evidence path: the Ask wrote no attempt, grade, claim or mastery.
    assert counts["after"] == counts["before"] and "practice_attempts" in counts["before"]
    assert seeded["plain"] != seeded["probe"]


def test_a_tutor_answer_shows_once_its_item_can_no_longer_be_answered_cold(tmp_path, monkeypatch):
    paths, repository, tutor, ctx_factory = _reader(tmp_path, monkeypatch)
    seeded = _seed_learner(paths, repository)
    _attempt(paths.sqlite_path, "att_now_right", item_id=seeded["plain"], lo_id="lo_matrices",
             at="2026-09-04T09:00:00Z", correctness=1.0)
    _ask(ctx_factory, paths)
    [prompt] = tutor.prompts
    assert "SECRET_WORKED_SOLUTION" in prompt
    assert "PROBE_ANSWER_TEXT" not in prompt and "PROBE_QUESTION_TEXT" not in prompt


def test_a_cold_administration_carries_no_learner_state_and_keeps_the_exclusions(tmp_path, monkeypatch):
    paths, repository, tutor, ctx_factory = _reader(tmp_path, monkeypatch)
    _seed_learner(paths, repository)
    answer = _ask(ctx_factory, paths, coldActive=True)
    [prompt] = tutor.prompts
    assert "learner_state" not in prompt and "learner_confidence" not in prompt
    assert "+learner-state-v1" not in prompt and "MY_OWN_FEEDBACK_QUESTION" not in prompt
    assert "MUST NOT tune the answer to a supposed deficit" in prompt
    manifest = answer["manifest"]
    assert manifest["learnerState"]["omitted"] == RLS.OMITTED_COLD and manifest["learnerState"]["given"] is False
    assert "cold_in_flight_response" in manifest["excluded"]
    assert "assessment_reserved_surface" in manifest["excluded"]


def test_switched_off_the_reader_tutor_is_todays_byte_for_byte(tmp_path, monkeypatch):
    on_paths, on_repo, on_tutor, on_ctx = _reader(tmp_path / "on", monkeypatch, learner_state=False)
    _seed_learner(on_paths, on_repo)
    off_answer = _ask(on_ctx, on_paths)
    [off_prompt] = on_tutor.prompts
    assert "learner_state" not in off_prompt and "learner_confidence" not in off_prompt
    assert "MY_OWN_FEEDBACK_QUESTION" not in off_prompt
    assert off_answer["manifest"]["version"] == "p3-reader-branches-v1"
    assert off_answer["manifest"]["excluded"] == ["ability_estimate", "assessment_reserved_surface",
                                                  "cold_in_flight_response"]
    assert "learnerState" not in off_answer["manifest"]
    assert "learner_state" not in (on_repo.question_events(context="reader")[-1]["source_context"] or {})
    # The same vault with no learner data and the switch on differs only by
    # the state's own markers (the golden in tests/fixtures/reader_tutor_switch_off.json
    # pins the off path against the base tree).


def test_the_prompt_contract_names_the_learner_state_only_while_on(tmp_path):
    from learnloop.reader import reader_dialogue as RD

    base = RD.reader_prompt_contract(branches=True)
    relaxed = RD.reader_prompt_contract(branches=True, learner_state=True)
    assert relaxed["version"] == base["version"] + RD.READER_LEARNER_STATE_CONTRACT_SUFFIX
    assert "the learner ability / posterior estimate" in base["manifest_never_includes"]
    assert relaxed["manifest_never_includes"] == ["any assessment-reserved surface statement or rubric",
                                                  "any cold administration's in-flight response"]
    assert RD.reader_prompt_contract() == RD._base_prompt_contract(branches=False)


def test_a_bound_question_carries_no_earlier_tutor_answer_and_unreadable_protection_carries_nothing(
        tmp_path, monkeypatch):
    from learnloop import learner_protection
    from tests.library_ask_fixtures import build_library_vault

    paths, repository, _spans = build_library_vault(tmp_path / "vault")
    seeded = _seed_learner(paths, repository)
    _attempt(paths.sqlite_path, "att_now_right", item_id=seeded["plain"], lo_id="lo_matrices",
             at="2026-09-04T09:00:00Z", correctness=1.0)
    vault = load_vault(paths.root)
    free = RLS.build(vault, repository, learning_object_ids=["lo_matrices"], now_iso="2026-10-01T00:00:00Z")
    bound = RLS.build(vault, repository, learning_object_ids=["lo_matrices"], now_iso="2026-10-01T00:00:00Z",
                      bound_item_id=seeded["plain"])
    assert "SECRET_WORKED_SOLUTION" in json.dumps(free.state)
    assert "SECRET_WORKED_SOLUTION" not in json.dumps(bound.state)
    # Strictly before the ask: an attempt from later never shows.
    early = RLS.build(vault, repository, learning_object_ids=["lo_matrices"], now_iso="2026-09-01T12:00:00Z")
    assert early.state["topics"][0]["recent_attempts"] == ["2026-09-01: right, with 2 hints"]
    monkeypatch.setattr(learner_protection, "withheld_items",
                        lambda *_a, **_k: learner_protection.Withheld(available=False))
    closed = RLS.build(vault, repository, learning_object_ids=["lo_matrices"], now_iso="2026-10-01T00:00:00Z")
    assert closed.state is None and closed.confidence is None and closed.omitted == RLS.OMITTED_UNREADABLE


# -- 2. the reader narrative ------------------------------------------------------------------------


def test_the_narrative_may_quote_the_learners_inquiry_words_under_the_same_checks(tmp_path):
    from learnloop.instructional import reader_digest as RN
    from tests.recap_fixtures import at
    from tests.test_reader_digest_narrative import QUESTION, NarrativeFake, _row, _session_with_question
    from tests.test_reader_followups import _now

    vault, repo, row = _session_with_question(tmp_path)
    fake = NarrativeFake(text=f'You asked "{QUESTION}" and worked one problem with the book open.')
    result = RN.narrate_digest(vault, repo, row["id"], client=fake, now=_now(), clock=at(300))
    assert result.status == "narrated"
    [payload] = fake.payloads
    assert f"prompt_version: {RN.QUOTES_PROMPT_VERSION}" in fake.prompts[0]
    quotes = payload["inquiry_quotes"]
    assert quotes and QUESTION in quotes[0]["learner_question"]
    assert {quote["root_exchange_id"] for quote in quotes} <= RN.citable_ids(row["summary"])
    assert all(len(quote["learner_question"]) <= RN.QUOTE_CHARS for quote in quotes)
    assert _row(repo, row["id"])["prompt_version"] == RN.QUOTES_PROMPT_VERSION
    # The checks are unchanged: an over-long quoting narrative is dropped.
    vault2, repo2, row2 = _session_with_question(tmp_path / "long")
    long = NarrativeFake(text=f'You asked "{QUESTION}" ' + "word " * 125)
    dropped = RN.narrate_digest(vault2, repo2, row2["id"], client=long, now=_now(), clock=at(300))
    assert dropped.status == "dropped" and any(r.startswith("over_word_cap") for r in dropped.reasons)


def test_switched_off_the_narrative_prompt_is_todays_exactly(tmp_path):
    from learnloop.ai.transport import render_structured_prompt
    from learnloop.instructional import reader_digest as RN
    from tests.recap_fixtures import at
    from tests.test_reader_digest_narrative import QUESTION, NarrativeFake, _row, _session_with_question
    from tests.test_reader_followups import _now

    vault, repo, row = _session_with_question(tmp_path, config="[digest]\nnarrative_quotes_inquiry = false\n")
    fake = NarrativeFake()
    RN.narrate_digest(vault, repo, row["id"], client=fake, now=_now(), clock=at(300))
    summary = row["summary"]
    expected = render_structured_prompt("learnloop reader session narrative", RN.PROMPT_VERSION, {
        "task": RN._INSTRUCTIONS, "max_words": RN.MAX_WORDS, "summary": dict(summary),
        "titles": RN._titles(vault, repo, summary), "citable_event_ids": sorted(RN.citable_ids(summary)),
    })
    assert fake.prompts == [expected]
    assert QUESTION not in fake.prompts[0]
    assert _row(repo, row["id"])["prompt_version"] == RN.PROMPT_VERSION


# -- 3. the diagnoser's prior-analysis arm ------------------------------------------------------------


def test_the_arm_is_a_seeded_equipoise_draw_or_the_configured_arm():
    from learnloop.diagnosis.split import prior_analysis as PA

    first, again = PA.assign("randomized", "att_x"), PA.assign("randomized", "att_x")
    assert first == again and first.assignment == "randomized" and first.propensity == PA.EQUIPOISE
    arms = [PA.assign("randomized", f"att_{n}").arm for n in range(400)]
    assert 150 < arms.count(PA.ARM_ON) < 250
    assert PA.assign("on", "att_x").receipt() == {"arm": PA.ARM_ON, "assignment": "config",
                                                  "design": PA.DESIGN, "propensity": 1.0}
    assert PA.assign("off", "att_x").arm == PA.ARM_OFF


def _assembled(vault: Any, repository: Any, prior: Any):
    from learnloop.diagnosis.split.context import assemble_diagnosis_context
    from learnloop.diagnosis.split.history import VaultHistoryStore
    from learnloop.diagnosis.split.settings import DiagnosisSettings
    from tests.test_diagnosis_context import _current

    store = VaultHistoryStore(vault, repository)
    return assemble_diagnosis_context(vault, store, _current(vault, store), DiagnosisSettings(), mode="full",
                                      prior_analysis=prior)


def test_the_off_arm_is_todays_context_and_the_on_arm_refeeds_earlier_analyses(tmp_path):
    from learnloop.diagnosis.split import prior_analysis as PA
    from learnloop.diagnosis.split.contract import diagnosis_prompt, diagnosis_prompt_version
    from learnloop.diagnosis.split.settings import DIAGNOSIS_PROMPT_VERSION
    from tests.diagnosis_split_helpers import build_diagnosis_vault, seed_history

    paths = build_diagnosis_vault(tmp_path / "vault")
    vault, repository = seed_history(paths)
    base = _assembled(vault, repository, None)
    shown = [row["attempt_id"] for row in base.blocks["history"]]
    assert shown

    def reader(ids, before):
        assert before == base.receipt["context_as_of_attempt_id"] or before
        return {shown[0]: {"earlier_diagnosis": {"diagnosis_id": "diag_earlier", "written": "2026-01-01",
                                                 "analysis_md": "EARLIER_READING", "full_text": "EARLIER_READING"},
                           "workbench_trace": {"note": "n", "assists": [{"order": 1, "assist": "hint"}]}}}

    off = _assembled(vault, repository, PA.PriorAnalysis(arm=PA.assign("off", "x"), read=reader))
    assert off.rendered() == base.rendered() and off.context_hash == base.context_hash
    assert diagnosis_prompt(off) == diagnosis_prompt(base)
    assert diagnosis_prompt_version(off) == DIAGNOSIS_PROMPT_VERSION
    assert off.receipt["prior_analysis"]["arm"] == PA.ARM_OFF
    assert {key: value for key, value in off.receipt.items() if key != "prior_analysis"} == base.receipt

    on = _assembled(vault, repository, PA.PriorAnalysis(arm=PA.assign("on", "x"), read=reader))
    assert on.context_hash != base.context_hash
    row = next(r for r in on.blocks["history"] if r["attempt_id"] == shown[0])
    assert row["earlier_diagnosis"] == {"written": "2026-01-01", "analysis_md": "EARLIER_READING"}
    assert row["workbench_trace"]["assists"] == [{"order": 1, "assist": "hint"}]
    assert on.blocks["disclosures"]["prior_analysis"] == PA.NOTE
    assert diagnosis_prompt_version(on) == DIAGNOSIS_PROMPT_VERSION + PA.SUFFIX
    assert ("diagnosis", "diag_earlier", "EARLIER_READING") in on.reads.records
    assert on.receipt["prior_analysis"] == {"arm": PA.ARM_ON, "assignment": "config", "design": PA.DESIGN,
                                            "propensity": 1.0}


def _live(tmp_path: Path, setting: str):
    from tests.split_live_helpers import drain_jobs, fake_client, split_vault, submit

    paths, vault, repository = split_vault(
        tmp_path / setting, config=f'[diagnosis]\nhistory_includes_prior_analysis = "{setting}"\n')
    from datetime import datetime, timezone

    from learnloop.clock import FrozenClock

    client = fake_client()
    day = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    first = submit(vault, repository, client, answer="A = U Sigma V wrong first", when=day)
    drain_jobs(vault, repository, client, clock=FrozenClock(day.replace(minute=5)))
    second = submit(vault, repository, client, answer="A = U Sigma V wrong second", when=day.replace(hour=11))
    drain_jobs(vault, repository, client, clock=FrozenClock(day.replace(hour=11, minute=5)))
    return paths, vault, repository, client, first, second


def _diagnosis_of(repository: Any, attempt_id: str) -> dict[str, Any]:
    rows = [row for row in repository.all_attempt_diagnoses() if row["attempt_id"] == attempt_id]
    assert rows, attempt_id
    return rows[-1]


def _attempt_id(result: Any) -> str:
    return str(getattr(result, "attempt_id", None) or result["attempt_id"])


@pytest.mark.parametrize("setting", ["on", "off"])
def test_the_live_diagnosis_records_its_arm_and_the_grader_never_sees_it(tmp_path, setting):
    from learnloop.diagnosis.split import prior_analysis as PA
    from learnloop.diagnosis.split.settings import DIAGNOSIS_PROMPT_VERSION

    _paths, _vault, repository, client, first, second = _live(tmp_path, setting)
    diagnosis = _diagnosis_of(repository, _attempt_id(second))
    receipt = repository.diagnosis_context_receipt(str(diagnosis["id"]))
    arm = receipt["retrieval"]["prior_analysis"]
    assert arm["arm"] == (PA.ARM_ON if setting == "on" else PA.ARM_OFF) and arm["assignment"] == "config"
    assert receipt["context_hash"]
    expected = DIAGNOSIS_PROMPT_VERSION + (PA.SUFFIX if setting == "on" else "")
    assert diagnosis["diagnosis_prompt_version"] == expected
    diagnosis_prompts = [p for purpose, p in zip(client.calls, client.prompts) if purpose == "diagnosis"]
    assert ("earlier_diagnosis" in diagnosis_prompts[-1]) is (setting == "on")
    grading_prompts = [p for purpose, p in zip(client.calls, client.prompts) if purpose != "diagnosis"]
    assert grading_prompts and all("earlier_diagnosis" not in p and "prior_analysis" not in p
                                   for p in grading_prompts)
    assert _diagnosis_of(repository, _attempt_id(first))


def test_the_report_reads_anchoring_suspect_per_arm(tmp_path):
    from learnloop.diagnosis.split.reports import m2_report, render_markdown

    _paths, vault, repository, _client, _first, _second = _live(tmp_path, "on")
    report = m2_report(vault, repository)["e2_prior_analysis_arms"]
    rates = report["anchoring_suspect_by_arm"]
    assert set(rates) == {"with_prior_analysis"} and rates["with_prior_analysis"]["n"] == 2
    assert report["assignments"] == {"with_prior_analysis:config": 2}
    assert "E2 anchoring by prior-analysis arm" in render_markdown(m2_report(vault, repository))


def test_the_blind_graders_context_is_byte_identical_in_every_arm_and_switch_setting(tmp_path):
    from learnloop.attempts.attempts import _blind_grading_plan
    from learnloop.attempts.blind_grading import blind_grading_prompt
    from learnloop.attempts.grading import build_grading_context
    from tests.split_live_helpers import split_vault

    settings = [
        "",
        '[diagnosis]\nhistory_includes_prior_analysis = "on"\n[reader_tutor]\nlearner_state_enabled = true\n'
        "[digest]\nnarrative_quotes_inquiry = true\n[adaptive_difficulty]\nhistory_answer_excerpts = true\n",
        '[diagnosis]\nhistory_includes_prior_analysis = "off"\n[reader_tutor]\nlearner_state_enabled = false\n'
        "[digest]\nnarrative_quotes_inquiry = false\n[adaptive_difficulty]\nhistory_answer_excerpts = false\n",
        '[diagnosis]\nhistory_includes_prior_analysis = "randomized"\n',
    ]
    seen = set()
    for index, config in enumerate(settings):
        _paths, vault, _repository = split_vault(tmp_path / f"v{index}", config=config)
        item = vault.practice_items["pi_svd_compute_001"]
        context = build_grading_context(vault, item, attempt_id="att_fixed", learner_answer_md="A = U Sigma V")
        plan = _blind_grading_plan(vault, item, context)
        seen.add((plan.context_hash, blind_grading_prompt(plan.context), plan.prompt_version))
    assert len(seen) == 1


# -- 4. AD's llm_v3 history card ----------------------------------------------------------------------


class _View:
    """The material view's two reads the card makes (withheld attempts already filtered out)."""

    def __init__(self, vault: Any, rows: list[dict[str, Any]]) -> None:
        self.vault, self._rows = vault, rows

    def attempts(self, _connection: Any) -> list[dict[str, Any]]:
        return list(self._rows)

    def item(self, item_id: Any) -> Any:
        return self.vault.practice_items.get(str(item_id))

    def lookup(self, _connection: Any, _table: str, _where: str, _args: Any) -> tuple[str, None]:
        return "missing", None  # no incumbent receipt


def test_the_history_card_carries_bounded_answer_excerpts_only_while_on(tmp_path):
    from learnloop.adaptive_difficulty import outside as O
    from tests.diagnosis_split_helpers import build_diagnosis_vault

    paths = build_diagnosis_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    item = vault.practice_items["pi_svd_compute_001"]
    rows = [{"id": "a1", "practice_item_id": item.id, "learning_object_id": item.learning_object_id,
             "attempt_type": "independent_attempt", "correctness": 0.0, "hints_used": 0, "primed": 0,
             "created_at": "2026-01-01T00:00:00Z", "learner_answer_md": "MY ANSWER " + "x" * 600}]
    view = _View(vault, rows)
    off = O.history_card(vault, None, item, served_at="2026-02-01T00:00:00Z", view=view, incumbent=None)
    on = O.history_card(vault, None, item, served_at="2026-02-01T00:00:00Z", view=view, incumbent=None,
                        answers=True)
    assert "answer_excerpt" not in json.dumps(off)
    [entry] = on["recent_attempts"]
    assert entry["answer_excerpt"].startswith("MY ANSWER") and len(entry["answer_excerpt"]) <= O.HISTORY_ANSWER_LIMIT
    assert {k: v for k, v in entry.items() if k != "answer_excerpt"} == off["recent_attempts"][0]
    assert O.STATE_VERSION == "ad-forecast-state-v1" and O.STATE_VERSION_ANSWER_EXCERPTS == "ad-forecast-state-v2"
    assert O.answer_excerpts_enabled(vault) is True


def test_the_frozen_state_version_follows_the_switch(tmp_path, monkeypatch):
    from learnloop.adaptive_difficulty import operation
    from learnloop.adaptive_difficulty import outside as O
    from learnloop.db.stores import ad_receipts as store
    from tests.diagnosis_split_helpers import build_diagnosis_vault
    from tests.split_live_helpers import append_config

    captured: list[dict[str, Any]] = []
    monkeypatch.setattr(store, "insert_payload", lambda _connection, **kwargs: captured.append(kwargs))
    monkeypatch.setattr(operation, "epoch_of", lambda _view: "epoch-1")
    for setting, expected in ((True, O.STATE_VERSION_ANSWER_EXCERPTS), (False, O.STATE_VERSION)):
        paths = build_diagnosis_vault(tmp_path / f"v{setting}")
        append_config(paths.root, f"[adaptive_difficulty]\nhistory_answer_excerpts = {str(setting).lower()}\n")
        vault = load_vault(paths.root)
        item = vault.practice_items["pi_svd_compute_001"]
        O.freeze_presentation_inputs(vault, None, item, presentation_id="pp_1", served_at="2026-02-01T00:00:00Z",
                                     protected=None, view=_View(vault, []))
        assert captured[-1]["content"]["state_version"] == expected
