"""Router R2a: ``LearnerStateCardV1``, built and stored at each boundary (never sent).

* **G5, no leakage**: a planted reference solution, an unattempted stem on a
  surface reserved for an assessment, exam material (by the exam predicate,
  and an ``exam_attempt``) and a grade held for review never reach the card's
  text or JSON; a held grade reads "held for review", never a score.
* **Determinism**: the same ledger at the same instant gives the same card and
  hash; the hash is on the decision row and with the stored payload.
* **Budget**: over ``router.card_token_budget`` older successes leave first,
  then older excerpts, then older attempts; typed fields never drop.
* ``learnloop router card`` prints a decision's stored card (read-only).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

from typer.testing import CliRunner

from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION
from learnloop.cli import app
from learnloop.daily_plan.engine import build_plan
from learnloop.daily_plan.policy import policy_for
from learnloop.router.card import CardInputs, build_card, estimate_tokens
from learnloop.substrate.activities import reserve_surface, resolve_legacy_item
from learnloop.vault.loader import load_vault

from tests.daily_plan_fakes import MovableClock, iso, make_env, scheduled, seed_due
from tests.helpers import NOW_ISO, create_daily_plan_vault, write_yaml

PAST = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
LAST = datetime(2026, 9, 20, 9, 0, tzinfo=UTC)
A = ROUTER_STAGED_FRAME_ALGORITHM_VERSION

REFERENCE = "REFSOL_SECRET_7731"
RESERVED_STEM = "RESERVED_STEM_4410"
EXAM_STEM = "EXAM_STEM_9902"
EXAM_ANSWER = "EXAM_ANSWER_5528"
HELD_SCORE = 0.4321
OWN_ANSWER = "MY_OWN_WORDS_1203"


def _item(paths, item_id: str, lo_id: str, *, prompt: str, expected: str, source_refs: list | None = None) -> None:
    write_yaml(
        paths.practice_item_path("linear-algebra", item_id),
        {
            "schema_version": 1, "id": item_id, "learning_object_id": lo_id, "subjects": None,
            "practice_mode": "short_answer", "attempt_types_allowed": ["independent_attempt", "exam_attempt"],
            "evidence_facets": ["recall"], "evidence_weights": {"recall": 1.0},
            "prompt": prompt, "expected_answer": expected, "difficulty": 0.5, "tags": [], "expected_minutes": 2.0,
            "grading_rubric": {"max_points": 4, "criteria": [{"id": "correctness", "points": 4, "description": "Right."}]},
            "provenance": {"origin": "human", "source_refs": source_refs or []},
            "created_at": NOW_ISO, "updated_at": NOW_ISO,
        },
    )


def _attempt(env, attempt_id: str, item_id: str, lo_id: str, at: str, *, answer: str, correctness: float,
             attempt_type: str = "independent_attempt") -> None:
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "learner_answer_md, correctness, hints_used, created_at, session_id, evidence_origin) "
            "VALUES (?, ?, ?, 'short_answer', ?, ?, ?, 0, ?, 'old', 'human')",
            (attempt_id, item_id, lo_id, attempt_type, answer, correctness, at),
        )
        connection.commit()


def _world(tmp_path, monkeypatch):
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects={"lo_m1": []}, version=A)
    _item(paths, "pi_ref", "lo_m1", prompt="What is a basis?", expected=REFERENCE)
    _item(paths, "pi_reserved", "lo_m1", prompt=RESERVED_STEM, expected="kept")
    _item(paths, "pi_exam", "lo_m1", prompt=EXAM_STEM, expected="exam key",
          source_refs=[{"ref_type": "canonical_source", "ref_id": "src_exam", "extraction_id": "ext_exam",
                        "span_ids": ["span_1"]}])
    _item(paths, "pi_held", "lo_m1", prompt="A proof.", expected="QED")
    clock = MovableClock()
    env = make_env(
        paths.root,
        [scheduled(item, "lo_m1", forgetting_risk=0.6) for item in ("pi_ref", "pi_reserved", "pi_exam", "pi_held")],
        clock=clock, session_id="s1",
    )
    for item in ("pi_ref", "pi_reserved", "pi_exam", "pi_held"):
        seed_due(env.repository, item, due=PAST, last=LAST if item != "pi_reserved" else None)
    _attempt(env, "att_ref", "pi_ref", "lo_m1", iso(LAST), answer=OWN_ANSWER, correctness=1.0)
    _attempt(env, "att_exam", "pi_exam", "lo_m1", iso(LAST), answer=EXAM_ANSWER, correctness=0.5)
    _attempt(env, "att_exam2", "pi_exam", "lo_m1", "2026-09-21T09:00:00Z", answer=EXAM_ANSWER, correctness=1.0,
             attempt_type="exam_attempt")
    _attempt(env, "att_held", "pi_held", "lo_m1", "2026-09-22T09:00:00Z", answer="my proof", correctness=HELD_SCORE)
    vault = load_vault(paths.root)
    resolved = resolve_legacy_item(vault, env.repository, vault.practice_items["pi_reserved"], purpose="assessment")
    reserve_surface(env.repository, surface_id=resolved.surface_id, purpose="assessment")

    from learnloop.source_retrieval import corpus

    monkeypatch.setattr(corpus, "exam_exclusions",
                        lambda _vault, _repo: corpus.Exclusions(frozenset({"ext_exam"}), frozenset()))
    import learnloop.held_grades as held_grades

    real = held_grades.held_for_review_attempts
    monkeypatch.setattr(held_grades, "held_for_review_attempts",
                        lambda connection, ids=None: frozenset({"att_held"}) | real(connection, ids))
    env.policy = policy_for(env.vault, env.repository, session_id="s1", clock=clock)
    return env


def _stored_card(env) -> tuple[dict, dict]:
    with env.repository.connection() as connection:
        row = connection.execute(
            "SELECT * FROM router_decisions WHERE decision_kind = 'plan_block' ORDER BY created_at, id LIMIT 1"
        ).fetchone()
        payload = connection.execute(
            "SELECT * FROM router_decision_payloads WHERE decision_id = ? AND kind = 'card'", (row["id"],)
        ).fetchone()
    return dict(row), dict(payload)


def test_g5_no_reference_reserved_stem_exam_text_or_held_score_reaches_the_card(tmp_path, monkeypatch):
    env = _world(tmp_path, monkeypatch)
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    row, payload = _stored_card(env)
    text, body = payload["content_text"], payload["content_json"]
    for planted in (REFERENCE, RESERVED_STEM, EXAM_STEM, EXAM_ANSWER, str(HELD_SCORE)):
        assert planted not in text, planted
        assert planted not in body, planted
    card = json.loads(body)
    work = {entry["attempt_id"]: entry for entry in card["recent_work"]}
    # The learner's own answer to ordinary practice is theirs to show.
    assert OWN_ANSWER in text and work["att_ref"]["answer"] == OWN_ANSWER
    # Exam work keeps its result, with no question and no answer.
    assert work["att_exam"]["stem"] is None and work["att_exam"]["answer"] is None
    assert work["att_exam"]["withheld"] == "exam or reserved material"
    assert work["att_exam2"]["result"] == "correct" and work["att_exam2"]["answer"] is None
    # A held grade is "held for review", never a score.
    assert work["att_held"]["result"] == "held_for_review"
    assert "held for review (no score yet)" in text
    # A candidate item is its topic, minutes and kind only.
    for candidate in card["candidates"]:
        assert set(candidate) <= {"ref", "lane", "kind", "est_minutes", "item_count", "topics", "learning_object_ids",
                                  "section", "reversible", "reason_code", "ladder"}
    assert row["card_hash"] == payload["content_hash"] and len(row["card_hash"]) == 64


def test_the_exam_predicate_failing_withholds_every_question_and_answer(tmp_path, monkeypatch):
    env = _world(tmp_path, monkeypatch)
    from learnloop.source_retrieval import corpus

    def broken(_vault, _repo):
        raise RuntimeError("no source sets readable")

    monkeypatch.setattr(corpus, "exam_exclusions", broken)
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    _row, payload = _stored_card(env)
    card = json.loads(payload["content_json"])
    assert all(entry["stem"] is None and entry["answer"] is None for entry in card["recent_work"])
    assert any("exam material could not be read" in unknown for unknown in card["unknowns"])
    assert OWN_ANSWER not in payload["content_text"]


def test_the_card_is_deterministic_for_the_same_ledger_and_instant(tmp_path, monkeypatch):
    env = _world(tmp_path, monkeypatch)
    gatherer = env.policy.chooser.card_builder
    from learnloop.daily_plan.engine import _live_context, decide, get_or_create_today

    record = get_or_create_today(env)
    context, _built = _live_context(env, record)
    decision = decide(record, context, env.policy.projection())
    first = gatherer(decision.state, decision.feasible)
    second = gatherer(decision.state, decision.feasible)
    assert first.card_hash == second.card_hash and first.text == second.text and first.json == second.json
    env.clock.advance(60)
    later = gatherer(decision.state, decision.feasible)
    assert later.card_hash != first.card_hash  # the decision time is part of the card


def _inputs(work: int, *, text: str = "x" * 300) -> CardInputs:
    entries = [
        {"attempt_id": f"a{index}", "at": f"2026-10-{(index % 28) + 1:02d}T09:00:00Z", "learning_object_id": "lo",
         "topic": "Bases", "kind": "short_answer", "result": "correct" if index % 2 else "incorrect",
         "hints_used": 0, "key_status": None, "stem": text, "answer": text}
        for index in range(work)
    ]
    return CardInputs(
        decision={"surface": "daily_plan", "decided_at": "2026-10-12T09:00:00Z"},
        session={"plan_kind": "normal", "minutes_left": 10, "minutes_budget": 25},
        candidates=[{"ref": "maintain:1", "kind": "maintain", "est_minutes": 4, "topics": ["Bases"],
                     "reversible": True, "reason_code": "review"}],
        learning_objects={"lo": {"title": "Bases", "status": "demonstrated", "evidence": {"graded": 3}}},
        interaction_7d={"attempts": 3},
        unknowns=["never tested: Spans"],
        recent_work=entries,
    )


def test_over_budget_older_successes_go_first_then_excerpts_then_attempts():
    inputs = _inputs(30)
    full = build_card(inputs, token_budget=10**6)
    assert full.truncation == {"dropped_successes": 0, "dropped_excerpts": 0, "dropped_attempts": 0}
    budget = full.tokens // 2
    card = build_card(inputs, token_budget=budget)
    assert card.tokens <= budget
    assert card.truncation["dropped_successes"] > 0
    kept = card.json["recent_work"]
    # The newest entries stay; successes go before failures.
    assert kept[0]["attempt_id"] == "a0"
    assert sum(1 for entry in kept if entry["result"] == "correct") < sum(1 for entry in kept if entry["result"] != "correct")
    tight = build_card(inputs, token_budget=estimate_tokens(build_card(_inputs(0), token_budget=10**6).json) * 3)
    assert tight.truncation["dropped_excerpts"] > 0 or tight.truncation["dropped_attempts"] > 0
    # Typed fields never drop.
    for card_ in (card, tight):
        assert card_.json["candidates"] == full.json["candidates"]
        assert card_.json["learning_objects"] == full.json["learning_objects"]
        assert card_.json["unknowns"] == full.json["unknowns"]
        assert "over the card budget" in card_.text


def test_router_card_prints_a_decisions_stored_card(tmp_path, monkeypatch):
    env = _world(tmp_path, monkeypatch)
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    row, payload = _stored_card(env)
    runner = CliRunner()
    result = runner.invoke(app, ["router", "card", "--vault", str(env.vault.root), "--decision", row["id"]])
    assert result.exit_code == 0, result.output
    assert payload["content_text"] in result.output and row["card_hash"] in result.output
    as_json = runner.invoke(app, ["router", "card", "--vault", str(env.vault.root), "--decision", row["id"], "--json"])
    assert as_json.exit_code == 0 and json.loads(as_json.output)["card_hash"] == row["card_hash"]
    missing = runner.invoke(app, ["router", "card", "--vault", str(env.vault.root), "--decision", "nope"])
    assert missing.exit_code == 1


def test_payloads_older_than_the_retention_window_are_pruned(tmp_path, monkeypatch):
    env = _world(tmp_path, monkeypatch)
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO router_decisions(id, receipt_key, decision_kind, surface, mode, policy, algorithm_version, "
            "log_version, snapshot_hash, candidates_json, exclusions_json, candidate_count, chosen_ref, propensity, "
            "propensity_kind, detail_json, created_at) VALUES ('rd_old', 'plan_block:old', 'plan_block', 'daily_plan', "
            "'staged', 'staged_v1', ?, 'router_decisions_v1', 'h', '[]', '{}', 0, 'stop_for_today', 1, "
            "'deterministic', '{}', '2025-01-01T00:00:00Z')", (A,),
        )
        connection.execute(
            "INSERT INTO router_decision_payloads(id, decision_id, kind, format_version, content_hash, created_at) "
            "VALUES ('pl_old', 'rd_old', 'card', 'learner_state_card_v1', 'h', '2025-01-01T00:00:00Z')"
        )
        connection.commit()
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    with sqlite3.connect(env.repository.sqlite_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM router_decision_payloads WHERE id = 'pl_old'").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM router_decisions WHERE id = 'rd_old'").fetchone()[0] == 1


# -- Codex review F6-F8: the card's past work, topic statuses and open problems ----

OLD_STEM = "OLD_STEM_THE_LEARNER_SAW_3301"
NEW_STEM = "NEW_STEM_NEVER_ATTEMPTED_8812"


def _card_world(tmp_path, monkeypatch):
    """Two candidate topics: lo_m1 (pi_a, answered then edited) and lo_m2 (pi_b)."""

    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects={"lo_m1": [], "lo_m2": []}, version=A)
    _item(paths, "pi_a", "lo_m1", prompt=NEW_STEM, expected="kept")
    _item(paths, "pi_b", "lo_m2", prompt="Name a basis of R^2.", expected="e1, e2")
    clock = MovableClock()
    env = make_env(paths.root, [scheduled("pi_a", "lo_m1", forgetting_risk=0.6),
                                scheduled("pi_b", "lo_m2", forgetting_risk=0.6)], clock=clock, session_id="s1")
    for item in ("pi_a", "pi_b"):
        seed_due(env.repository, item, due=PAST, last=LAST)
    from learnloop.source_retrieval import corpus

    monkeypatch.setattr(corpus, "exam_exclusions",
                        lambda _vault, _repo: corpus.Exclusions(frozenset(), frozenset()))
    env.policy = policy_for(env.vault, env.repository, session_id="s1", clock=clock)
    return env


def _graded_under(env, attempt_id: str, item_id: str, *, prompt: str) -> str:
    """Grade ``attempt_id`` under a pinned contract whose revision showed ``prompt``."""

    from learnloop.learner.assessment_contracts import snapshot_for_presentation

    item = env.vault.practice_items[item_id].model_copy(update={"prompt": prompt})
    version_id = snapshot_for_presentation(env.repository, env.vault, item)
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO grading_evidence(id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, "
            "assessment_contract_version_id, grading_revision) VALUES (?, ?, 'correctness', 4, 1, ?, ?, 0)",
            (f"ge_{attempt_id}", attempt_id, iso(LAST), version_id),
        )
        connection.commit()
    return version_id


def _card(env) -> dict:
    """The card stored with the plan's first block decision."""

    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    _row, payload = _stored_card(env)
    return {"json": json.loads(payload["content_json"]), "text": payload["content_text"]}


def test_past_work_shows_the_revision_it_answered_never_todays_edit(tmp_path, monkeypatch):
    """Review F6: an answered item is edited afterwards. The card shows the
    question from the attempt's pinned contract, never the current prompt; an
    attempt whose revision cannot be established shows no question."""

    env = _card_world(tmp_path, monkeypatch)
    _attempt(env, "att_old", "pi_a", "lo_m1", iso(LAST), answer=OWN_ANSWER, correctness=1.0)
    _graded_under(env, "att_old", "pi_a", prompt=OLD_STEM)
    _attempt(env, "att_unpinned", "pi_a", "lo_m1", "2026-09-21T09:00:00Z", answer="second try", correctness=0.0)
    card = _card(env)
    work = {entry["attempt_id"]: entry for entry in card["json"]["recent_work"]}
    assert work["att_old"]["stem"] == OLD_STEM and work["att_old"]["answer"] == OWN_ANSWER
    assert work["att_unpinned"]["stem"] is None and work["att_unpinned"]["answer"] == "second try"
    assert "question revision not recorded" in card["text"]
    assert NEW_STEM not in card["text"] and NEW_STEM not in json.dumps(card["json"])


def test_failed_or_assisted_work_is_never_demonstrated(tmp_path, monkeypatch):
    """Review F7: a graded attempt is not a demonstration. An incorrect,
    hinted, primed attempt is assisted-only; unassisted work without
    capability credit is attempted, not demonstrated; only the authoritative
    classification (the Today headline's) says demonstrated."""

    env = _card_world(tmp_path, monkeypatch)
    _attempt(env, "att_a", "pi_a", "lo_m1", iso(LAST), answer="right", correctness=1.0)
    _attempt(env, "att_b", "pi_b", "lo_m2", iso(LAST), answer="wrong", correctness=0.0)
    with env.repository.connection() as connection:
        connection.execute("UPDATE practice_attempts SET hints_used = 2, primed = 1 WHERE id = 'att_b'")
        connection.commit()
    statuses = {lo: row["status"] for lo, row in _card(env)["json"]["learning_objects"].items()}
    assert statuses == {"lo_m1": "attempted_not_demonstrated", "lo_m2": "assisted_only"}


def test_only_the_authoritative_classification_says_demonstrated(tmp_path, monkeypatch):
    env = _card_world(tmp_path, monkeypatch)
    _attempt(env, "att_a", "pi_a", "lo_m1", iso(LAST), answer="right", correctness=1.0)
    import learnloop.daily_plan.headline as headline

    real = headline.classify_learning_objects
    monkeypatch.setattr(headline, "classify_learning_objects",
                        lambda vault, repository, **kw: {**real(vault, repository, **kw), "lo_m1": "demonstrated"})
    statuses = {lo: row["status"] for lo, row in _card(env)["json"]["learning_objects"].items()}
    assert statuses == {"lo_m1": "demonstrated", "lo_m2": "untested"}


def _hypothesis(env, hypothesis_id: str, *, status: str, statement: str, evidence: dict) -> None:
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO causal_hypotheses(id, episode_key, version, attempt_id, learning_object_id, cause_scope, "
            "statement, statement_normalized, status, evidence_json, created_at) "
            "VALUES (?, ?, 1, 'att_a', 'lo_m1', 'learner_state', ?, ?, ?, ?, ?)",
            (hypothesis_id, f"ep_{hypothesis_id}", statement, statement.lower(), status, json.dumps(evidence),
             iso(LAST)),
        )
        connection.commit()


def test_a_resolved_promoted_misconception_is_not_an_open_problem(tmp_path, monkeypatch):
    """Review F8: a validated cause whose promoted misconception has been
    resolved is closed, exactly as the daily plan's own predicate says; an
    open one stays, with its supporting evidence ids."""

    from learnloop.db.stores.daily_plans import open_diagnosed_problem_learning_object_ids

    env = _card_world(tmp_path, monkeypatch)
    _attempt(env, "att_a", "pi_a", "lo_m1", iso(LAST), answer="right", correctness=1.0)
    _hypothesis(env, "hyp_resolved", status="validated", statement="Confuses rank and nullity",
                evidence={"promoted_misconception_id": "mc_resolved"})
    _hypothesis(env, "hyp_open", status="candidate", statement="Swaps rows and columns", evidence={})
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO misconceptions(id, learning_object_id, statement, status, resolved_at) "
            "VALUES ('mc_resolved', 'lo_m1', 'Confuses rank and nullity', 'resolved', ?)", (iso(LAST),),
        )
        connection.commit()
        # The daily plan's predicate: the LO stays open through hyp_open only.
        assert "lo_m1" in open_diagnosed_problem_learning_object_ids(connection)
    card = _card(env)
    causes = [entry for entry in card["json"]["open_hypotheses"] if entry["kind"] == "diagnosed_cause"]
    assert "Confuses rank and nullity" not in card["text"]
    assert [(entry["statement"], entry["hypothesis_id"], entry["attempt_id"]) for entry in causes] == [
        ("Swaps rows and columns", "hyp_open", "att_a")
    ]
