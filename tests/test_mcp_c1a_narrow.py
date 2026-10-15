"""Chat frontend C1a, narrowed (owner decision 2026-10-14, "land narrow, then fix source").

``learning_context`` (and the topic names ``today`` and ``progress`` show) keep
one structural rule: a text leaves LearnLoop only when it is

(a) authored vault text (a topic name or id the learner or an authored vault
    file wrote, the question as graded);
(b) the learner's own answer on a pinned attempt, through the answer guard;
(c) a derived text with a recorded, complete write-time provenance whose
    inputs are all safe (the hook for the "diagnosis input provenance" stage;
    nothing records one yet).

Everything a diagnosis, the normalizer, the gap reader or the drafter wrote,
and every generated topic's name and id, is held back with one plain reason.

The first group of tests is the last verify's reproductions (Codex job
``20261014-205718-WNjtvF247``): each leaked text on ``34527fa13`` and must not
leak now. They import nothing the old code lacks, so they fail on the leak.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import re
from typing import Any

import anyio
import pytest
from mcp import Client

from learnloop.remote.runtime import RemoteRuntime
from learnloop.vault.loader import load_vault
from learnloop_mcp.server import build_server
from tests.helpers import NOW_ISO
from tests.mcp_world import (
    CANDIDATE,
    GAP_TEXT,
    GENERATED_TITLE,
    HYPOTHESIS,
    LEGACY_KEY,
    MISCONCEPTION,
    OWN_ANSWER,
    PEER,
    PEER_ANSWER,
    PINNED_STEM,
    PROTECTED,
    build_world,
    c4_receipt,
    candidate_row,
    error_event,
    gap_row,
    generated_world,
    group_row,
    hold_att_held,
    hypothesis_row,
    legacy_answer,
    live_diagnosis,
    misconception_row,
    no_model_calls,
    payload_text,
    pinned_answer,
)

#: The one reason a derived text is withheld (``learner_context.HELD_BACK``).
HELD_BACK = "Held back until LearnLoop records what this was written from"
#: The words of the drafted title as a model would write them in prose.
TITLE_WORDS = "legacy key 8841 a row swap negates the volume"


def _call_all(server, calls):
    async def main():
        async with Client(server) as client:
            return [await client.call_tool(name, arguments) for name, arguments in calls]

    return anyio.run(main)


def _text(result) -> str:
    return payload_text(result.structured_content) + "".join(getattr(c, "text", "") for c in result.content)


def _context(world, **arguments) -> tuple[dict, str]:
    server = build_server(RemoteRuntime.attach(world.root, load_environment=False))
    (result,) = _call_all(server, [("learning_context", {"max_traces": 30, **arguments})])
    assert not result.is_error, result.content
    return result.structured_content, _text(result)


def _slug(lo_id: str) -> str:
    return lo_id.split("lo_ltg_", 1)[1].rsplit("_", 1)[0]


def _no_protected(text: str) -> None:
    leaked = [planted for planted in PROTECTED if planted in text]
    assert not leaked, leaked


@pytest.fixture
def paid_routes(monkeypatch):
    return no_model_calls(monkeypatch)


@pytest.fixture
def world(tmp_path, monkeypatch, paid_routes):
    hold_att_held(monkeypatch)
    return build_world(tmp_path / "w")


# -- the last verify's reproductions -------------------------------------------------------


def test_a_snapshot_diagnosis_and_the_beliefs_drawn_from_it_are_held_back(world):
    """Verify F1: ``att_own`` and ``PEER`` are pinned, ``att_legacy`` is not, and
    ``PEER``'s joint grader was shown ``att_legacy``. A snapshot diagnosis of
    ``att_own`` read ``PEER``'s grading from the whole-vault export without
    naming it (nothing records what it opened) and copied the key into its
    summary and into a cause the overlay lays on ``att_own``'s event; a
    misconception, a candidate, a hypothesis and its group were drawn from it."""

    legacy_answer(world)
    pinned_answer(world, PEER, PEER_ANSWER, "2026-09-21T09:00:00Z")
    cause = f"Believes {LEGACY_KEY} for every matrix"
    with world.repository.connection() as connection:
        c4_receipt(connection, PEER, ["att_legacy"])
        error_event(connection, "ev_own", "att_own", None)
        connection.commit()
    live_diagnosis(world.repository, "att_own", f"Like an earlier answer, the learner wrote {LEGACY_KEY}.",
                   view={"events": {"ev_own": {"misconception_statement": cause, "is_misconception": True}}},
                   receipt={"retrieval": {"neighborhood_learning_object_ids": ["lo_matrices"]}},
                   history_mode="snapshot")
    hypothesis_id = hypothesis_row(world, "ep_snap", "att_own", cause, event_id="ev_own")
    with world.repository.connection() as connection:
        misconception_row(connection, "mc_snap", cause, '["ev_own"]', f"Correct: never {LEGACY_KEY}")
        candidate_row(connection, "mcand_snap", cause, events='["ev_own"]', items='["pi_own"]', count=2)
        group_row(connection, "grp_snap", "ep_snap", cause)
        connection.commit()
    context, text = _context(world)
    assert LEGACY_KEY not in text and "8841" not in text
    own = next(t for t in context["recent_answer_traces"] if t["attempt_id"] == "att_own")
    assert own["answer"] == OWN_ANSWER and own["stem"] == PINNED_STEM
    assert own["diagnosis"]["status"] == "done"
    assert own["diagnosis"]["summary"] is None and own["diagnosis"]["summary_note"] == HELD_BACK
    snap = next(m for m in context["misconceptions"] if m["misconception_id"] == "mc_snap")
    assert snap["statement"] is None and snap["statement_note"] == HELD_BACK
    assert snap["correction"] is None and snap["correction_note"] == HELD_BACK
    assert snap["status"] == "active" and snap["evidence_count"] == 1
    candidate = next(c for c in context["misconception_candidates"] if c["candidate_id"] == "mcand_snap")
    assert candidate["statement"] is None and candidate["statement_note"] == HELD_BACK
    assert candidate["evidence_count"] == 2
    hypothesis = next(h for h in context["open_hypotheses"] if h.get("hypothesis_id") == hypothesis_id)
    assert hypothesis["statement"] is None and hypothesis["statement_note"] == HELD_BACK
    assert hypothesis["evidence_for"]["answers_in_episode"] == 1
    assert all(group["statement"] is None for group in context["recurrence_groups"])
    _no_protected(text)


def test_a_missing_c4_receipt_releases_nothing_the_joint_grader_wrote(world):
    """Verify F1, Q14: ``PEER``'s joint grader was shown ``att_legacy``, but its
    Phase-C receipt was never written (the write is outside the grading
    transaction and failures are swallowed), so it reads as shown nothing. The
    cause it wrote, a misconception normalized from it and a diagnosis shown
    ``PEER`` carry the key; none of it is shown. ``PEER``'s own answer is."""

    legacy_answer(world)
    pinned_answer(world, PEER, PEER_ANSWER, "2026-09-21T09:00:00Z")
    cause = f"Thinks {LEGACY_KEY} as graded jointly"
    with world.repository.connection() as connection:
        error_event(connection, "ev_peer", PEER, cause, "mc_peer")
        misconception_row(connection, "mc_peer", cause, '["ev_peer"]', None)
        connection.commit()
    live_diagnosis(world.repository, "att_own", f"As in an earlier answer, the learner wrote {LEGACY_KEY}.",
                   receipt={"failure_attempt_ids": [PEER]})
    context, text = _context(world)
    assert LEGACY_KEY not in text
    peer = next(m for m in context["misconceptions"] if m["misconception_id"] == "mc_peer")
    assert peer["statement"] is None and peer["statement_note"] == HELD_BACK
    traces = {t["attempt_id"]: t for t in context["recent_answer_traces"]}
    assert traces["att_own"]["diagnosis"]["summary"] is None
    assert traces["att_own"]["diagnosis"]["summary_note"] == HELD_BACK
    assert traces[PEER]["answer"] == PEER_ANSWER


def test_a_generated_title_read_from_the_snapshot_is_held_back(world):
    """Verify F2, scenario 1: a prerequisite drafted from ``att_legacy`` lies
    outside the diagnosis's neighbourhood; a snapshot diagnosis read its title
    from the exported graph and wrote its words as prose."""

    los = generated_world(world)
    live_diagnosis(world.repository, "att_own", f"The learner seems to lack {TITLE_WORDS}.",
                   receipt={"retrieval": {"neighborhood_learning_object_ids": ["lo_matrices"]}},
                   history_mode="snapshot")
    context, text = _context(world)
    assert "8841" not in text and TITLE_WORDS not in text.lower()
    assert _slug(los["tainted"]) not in text and los["tainted"] not in text
    own = next(t for t in context["recent_answer_traces"] if t["attempt_id"] == "att_own")
    assert own["diagnosis"]["summary"] is None and own["diagnosis"]["summary_note"] == HELD_BACK


def test_a_generated_id_in_a_misconception_statement_is_held_back(world):
    """Verify F2, scenario 2: the diagnosis's summary is generic, and the
    generated topic's literal id is in a misconception statement drawn from
    the pinned answer's event."""

    los = generated_world(world)
    statement = f"Confuses lo_matrices with {los['tainted']}"
    with world.repository.connection() as connection:
        error_event(connection, "ev_named", "att_own", statement, "mc_named")
        misconception_row(connection, "mc_named", statement, '["ev_named"]', None)
        connection.commit()
    live_diagnosis(world.repository, "att_own", "The learner mixed up two topics.",
                   receipt={"retrieval": {"neighborhood_learning_object_ids": ["lo_matrices"]}})
    context, text = _context(world)
    assert los["tainted"] not in text and _slug(los["tainted"]) not in text and "8841" not in text
    named = next(m for m in context["misconceptions"] if m["misconception_id"] == "mc_named")
    assert named["statement"] is None and named["statement_note"] == HELD_BACK


def test_the_old_alias_of_a_generated_topic_cannot_be_recomputed(world):
    """The alias of a withheld topic was ``sha256(id)``: a client that guessed
    the title (and so the id: the slug and the source's hash, ``att_legacy``
    being in the output) could confirm it. Aliases are keyed now."""

    los = generated_world(world)
    unkeyed = "lo_withheld_" + hashlib.sha256(los["tainted"].encode("utf-8")).hexdigest()[:16]
    context, text = _context(world)
    assert unkeyed not in text
    aliases = {gap["learning_object_id"] for gap in context["open_learner_text_gaps"] if gap["gap_id"] == "gap_gen"}
    assert len(aliases) == 1 and next(iter(aliases)).startswith("lo_withheld_")


def test_a_recurrence_group_key_cannot_confirm_a_guessed_statement(world):
    """Q13: the stored group key is ``rg:`` + SHA-256 of the root's normalized
    statement, so a client that guessed a withheld statement could confirm it
    by recomputing the key. The output key is an opaque keyed digest."""

    from learnloop.recurrence import group_key_for, normalize_statement

    statement = "Thinks every swap of two rows doubles the determinant"
    key = group_key_for(normalize_statement(statement))
    hypothesis_row(world, "ep_guess", "att_own", statement)
    with world.repository.connection() as connection:
        group_row(connection, key, "ep_guess", statement)
        connection.commit()
    context, text = _context(world)
    assert key not in text and key.split(":", 1)[1] not in text and statement not in text
    keys = [group["group_key"] for group in context["recurrence_groups"]]
    assert len(keys) == len(set(keys)) >= 3
    assert all(re.fullmatch(r"rg_[0-9a-f]{20}", value) for value in keys), keys
    # Stable across calls of one server, so a host can tell groups apart.
    again, _text_again = _context(world)
    assert sorted(group["group_key"] for group in again["recurrence_groups"]) == sorted(keys)


# -- today and progress (Q12) -----------------------------------------------------------------


GENERATED_LO = "lo_ltg_legacy_key_8841_a_row_swap_negates_the_volume_abcdef12"


def _plan_vault(tmp_path, monkeypatch):
    from learnloop.daily_plan.engine import build_plan
    from tests.daily_plan_fakes import NOW, MovableClock, make_env, scheduled, seed_due
    from tests.helpers import create_daily_plan_vault

    no_model_calls(monkeypatch)
    paths = create_daily_plan_vault(tmp_path / "plan", learning_objects={
        "lo_m1": [("pi_m1a", 2.0)], GENERATED_LO: [("pi_g1", 2.0), ("pi_g2", 2.0)]})
    clock = MovableClock()
    # Both topics are due: today's (stored) block is one maintain block whose
    # computed why names them by the titles it was built with.
    env = make_env(paths.root, [scheduled("pi_m1a", "lo_m1", forgetting_risk=0.6),
                                scheduled("pi_g1", GENERATED_LO, forgetting_risk=0.6),
                                scheduled("pi_g2", GENERATED_LO, forgetting_risk=0.5)], clock=clock)
    for item in ("pi_m1a", "pi_g1", "pi_g2"):
        seed_due(env.repository, item, due=NOW, last=NOW.replace(day=1))
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    return paths, clock


def test_today_and_progress_never_show_a_generated_topic_s_name(tmp_path, monkeypatch):
    """Q12: ``today`` (block topics and the computed why, which embeds the
    titles it was built with) and ``progress`` (goal topics, the assumed list,
    retention risks) route every topic name and id through the guard: a
    generated topic shows a fixed label and an opaque alias; an authored one
    shows as the vault has it."""

    import learnloop.daily_plan.headline as headline

    paths, clock = _plan_vault(tmp_path, monkeypatch)
    real = headline.classify_learning_objects

    def assumed(vault, repository, *, now):
        return {**real(vault, repository, now=now), GENERATED_LO: "assumed"}

    monkeypatch.setattr(headline, "classify_learning_objects", assumed)
    server = build_server(RemoteRuntime.attach(paths.root, load_environment=False), clock=clock)
    today, progress = _call_all(server, [("today", {}), ("progress", {})])
    for result in (today, progress):
        assert not result.is_error, result.content
        text = _text(result)
        assert "8841" not in text and GENERATED_LO not in text and "Legacy Key" not in text, text
    (block,) = today.structured_content["plan"]["blocks"]
    assert block["topics"][0] == "M1" and block["topics"][1].startswith("a topic named from")
    # The computed why named the generated title: held back (an authored-only
    # block keeps its why: test_mcp_tools' today test).
    assert block["why"] is None and block["why_note"] == HELD_BACK
    report = progress.structured_content
    topics = [topic for goal in report["goals"] for topic in (goal["report"] or {}).get("topics", [])]
    named = {topic["learning_object_id"]: topic["topic"] for topic in topics}
    assert named.get("lo_m1") == "M1"
    hidden = [lo for lo in named if lo.startswith("lo_withheld_")]
    assert hidden and all(named[lo].startswith("a topic named from") for lo in hidden)
    assert report["assumed"] and all(name.startswith("a topic named from") for name in report["assumed"])
    risks = {risk["learning_object_id"]: risk["topic"] for risk in report["retention_risks"]}
    assert any(lo.startswith("lo_withheld_") for lo in risks) and risks.get("lo_m1") == "M1"


# -- the rule, piece by piece -------------------------------------------------------------------


def test_the_learner_s_own_pinned_answers_and_authored_names_still_show(world):
    context, text = _context(world)
    traces = {trace["attempt_id"]: trace for trace in context["recent_answer_traces"]}
    assert traces["att_own"]["answer"] == OWN_ANSWER and traces["att_own"]["stem"] == PINNED_STEM
    assert traces["att_own"]["topic"] == "Matrix computations" and traces["att_own"]["learning_object_id"] == "lo_matrices"
    # What a model wrote is held back everywhere; the entries, counts and status stay.
    for planted in (MISCONCEPTION, CANDIDATE, HYPOTHESIS):
        assert planted not in text, planted
    (misconception,) = context["misconceptions"]
    assert misconception["statement"] is None and misconception["statement_note"] == HELD_BACK
    assert misconception["evidence_count"] == 2 and misconception["status"] == "active"
    # The learner's question (a tutor question, not an answer) is held back too.
    (gap,) = context["open_learner_text_gaps"]
    assert gap["learner_text"] is None and gap["learner_text_note"] == HELD_BACK
    assert gap["target"] is None and gap["target_note"] == HELD_BACK and gap["target_topic"] == "Matrix computations"
    assert GAP_TEXT not in text
    _no_protected(text)


def test_a_gap_drawn_from_a_pinned_answer_shows_that_answer_and_nothing_else(world):
    with world.repository.connection() as connection:
        gap_row(connection, "gap_stuck", source_kind="stuck_answer", source_id="att_own", attempt_id="att_own",
                item_id="pi_own", text="a stored excerpt the reader chose", target_kind="candidate",
                target_id="mcand_row")
        gap_row(connection, "gap_unpinned", source_kind="stuck_answer", source_id="att_unpinned",
                attempt_id="att_unpinned", item_id="pi_edited", text="UNPINNED words", target_kind=None,
                target_id=None)
        gap_row(connection, "gap_reader", source_kind="tutor_question", source_id="q_reader", attempt_id=None,
                item_id=None, text="READER_QUESTION_3310 what does this exam question ask", target_kind=None,
                target_id=None)
        connection.commit()
    context, text = _context(world)
    gaps = {gap["gap_id"]: gap for gap in context["open_learner_text_gaps"]}
    # The answer itself (as recorded on the attempt), through the answer guard.
    assert gaps["gap_stuck"]["learner_text"] == OWN_ANSWER and gaps["gap_stuck"]["target"] is None
    assert "a stored excerpt" not in text
    assert gaps["gap_unpinned"]["learner_text"] is None and "revision" in gaps["gap_unpinned"]["learner_text_note"]
    assert gaps["gap_reader"]["learner_text"] is None and gaps["gap_reader"]["learner_text_note"] == HELD_BACK
    assert "READER_QUESTION_3310" not in text and "UNPINNED words" not in text


def test_a_question_on_a_generated_topic_is_held_back_its_answer_is_not(world):
    """An item on a generated topic was seeded from the learner's question:
    its prompt is drafted text, so its stem is held back; the learner's own
    pinned answer to it shows."""

    los = generated_world(world)
    with world.repository.connection() as connection:
        connection.execute(
            "INSERT INTO assessment_contract_versions(id, practice_item_id, contract_hash, contract_json, "
            "schema_version, created_at) VALUES ('acv_gen', 'pi_gen', 'h_gen', ?, 1, ?)",
            ('{"prompt": "SEEDED_PROMPT_4402 swap two rows", "expected_answer": "they differ in sign"}', NOW_ISO))
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "learner_answer_md, correctness, hints_used, created_at, session_id, evidence_origin, entry_surface) "
            "VALUES ('att_gen_pinned', 'pi_gen', ?, 'short_answer', 'independent_attempt', 'GEN_PINNED_7710 equal', "
            "0.0, 0, '2026-09-22T09:00:00Z', 'old', 'human', 'desktop_practice')", (los["tainted"],))
        connection.execute(
            "INSERT INTO grading_evidence(id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, "
            "assessment_contract_version_id) VALUES ('ge_gen', 'att_gen_pinned', 'correct', 0, 1, ?, 'acv_gen')",
            (NOW_ISO,))
        connection.commit()
    context, text = _context(world)
    trace = next(t for t in context["recent_answer_traces"] if t["attempt_id"] == "att_gen_pinned")
    assert trace["answer"] == "GEN_PINNED_7710 equal"
    assert trace["stem"] is None and trace["stem_note"] == HELD_BACK and "SEEDED_PROMPT_4402" not in text
    assert trace["topic"].startswith("a topic named from") and trace["learning_object_id"].startswith("lo_withheld_")
    assert "8841" not in text


def test_generated_topics_are_aliased_everywhere_and_accepted_back(world):
    los = generated_world(world)
    server = build_server(RemoteRuntime.attach(world.root, load_environment=False))
    (everything,) = _call_all(server, [("learning_context", {"max_traces": 30})])
    context, text = everything.structured_content, _text(everything)
    for lo in los.values():
        assert lo not in text and _slug(lo) not in text
    for title in ("Permutation parity basics", "Elementary matrix inverses", "8841"):
        assert title not in text
    gaps = {gap["gap_id"]: gap for gap in context["open_learner_text_gaps"]}
    alias = gaps["gap_gen"]["learning_object_id"]
    assert alias.startswith("lo_withheld_") and alias in context["scope"]["learning_object_ids"]
    assert gaps["gap_gen"]["target_topic"].startswith("a topic named from")
    named, searched = _call_all(server, [("learning_context", {"learning_object_ids": [alias]}),
                                         ("learning_context", {"topic": "8841 negates"})])
    assert named.structured_content["scope"]["learning_object_ids"] == [alias]
    assert any(m["misconception_id"] == "mc_gen" for m in named.structured_content["misconceptions"])
    assert searched.structured_content["scope"]["learning_object_count"] == 0
    for result in (named, searched):
        assert los["tainted"] not in _text(result) and "8841" not in _text(result).replace("8841 negates", "")


# -- (c): the write-time provenance hook ---------------------------------------------------------


def _recorded(records: dict[tuple[str, str], Any]):
    def source(_connection, kind, record_id):
        return records.get((kind, record_id))

    return source


def test_a_recorded_complete_provenance_with_safe_inputs_releases_a_derived_text(world):
    from learnloop.learner_context import HELD_BACK as MODULE_HELD_BACK
    from learnloop.learner_context import RecordedText, WriteProvenance, learning_context

    assert MODULE_HELD_BACK == HELD_BACK
    safe = WriteProvenance(complete=True, answers=("att_own",), items=("pi_own",), topics=("lo_matrices",))
    records = {("misconception", "mc_swap"): safe, ("candidate", "mcand_row"): safe,
               ("hypothesis", world.hypothesis_id): safe}
    context = learning_context(load_vault(world.root), world.repository, provenance=_recorded(records))
    (misconception,) = context["misconceptions"]
    assert misconception["statement"] == MISCONCEPTION and isinstance(misconception["statement"], RecordedText)
    # The correction has no record of its own: still held back (it also states a key).
    assert misconception["correction"] is None and misconception["correction_note"] == HELD_BACK
    (candidate,) = context["misconception_candidates"]
    assert candidate["statement"] == CANDIDATE
    swap = next(h for h in context["open_hypotheses"] if h.get("hypothesis_id") == world.hypothesis_id)
    assert swap["statement"] == HYPOTHESIS


@pytest.mark.parametrize("case", ["incomplete", "empty", "unpinned_answer", "protected_answer", "unknown_answer",
                                  "protected_item", "generated_topic", "unknown_topic", "states_a_key",
                                  "malformed", "source_fails"])
def test_a_recorded_provenance_releases_nothing_unless_complete_and_safe(world, case):
    from learnloop.learner_context import WriteProvenance, learning_context

    los = generated_world(world)
    record: Any = {
        "incomplete": WriteProvenance(complete=False, answers=("att_own",)),
        "empty": WriteProvenance(complete=True),
        "unpinned_answer": WriteProvenance(complete=True, answers=("att_own", "att_legacy")),
        "protected_answer": WriteProvenance(complete=True, answers=("att_own", "att_cold")),
        "unknown_answer": WriteProvenance(complete=True, answers=("att_nowhere",)),
        "protected_item": WriteProvenance(complete=True, answers=("att_own",), items=("pi_exam",)),
        "generated_topic": WriteProvenance(complete=True, answers=("att_own",), topics=(los["tainted"],)),
        "unknown_topic": WriteProvenance(complete=True, answers=("att_own",), topics=("lo_nowhere",)),
        "states_a_key": WriteProvenance(complete=True, answers=("att_own",)),
        "malformed": WriteProvenance(complete=True, answers=("att_own", "")),  # type: ignore[arg-type]
    }.get(case)
    statement = f"Thinks the key is {'CONTRACT_KEY_9134 never shown' if case == 'states_a_key' else 'a row swap'}"
    with world.repository.connection() as connection:
        misconception_row(connection, "mc_hook", statement, '["e1"]', None)
        connection.commit()

    def source(_connection, kind, record_id):
        if case == "source_fails":
            raise RuntimeError("the provenance store could not be read")
        return record if (kind, record_id) == ("misconception", "mc_hook") else None

    context = learning_context(load_vault(world.root), world.repository, provenance=source)
    hooked = next(m for m in context["misconceptions"] if m["misconception_id"] == "mc_hook")
    assert hooked["statement"] is None, case
    assert hooked["statement_note"], case
    assert "CONTRACT_KEY_9134" not in payload_text(context)


def test_a_recorded_provenance_releases_a_generated_topic_s_name(world):
    from learnloop.learner_context import WriteProvenance, learning_context

    los = generated_world(world)
    safe = WriteProvenance(complete=True, answers=("att_own",), topics=("lo_matrices",))
    context = learning_context(load_vault(world.root), world.repository,
                               provenance=_recorded({("learning_object", los["safe"]): safe}))
    gaps = {gap["gap_id"]: gap for gap in context["open_learner_text_gaps"]}
    assert gaps["gap_gen_safe"]["target_topic"] == "Permutation parity basics"
    assert gaps["gap_gen_safe"]["learning_object_id"] == los["safe"]
    # The others have no record: still a label and an alias.
    assert gaps["gap_gen"]["learning_object_id"].startswith("lo_withheld_")
    assert gaps["gap_gen_later"]["target_topic"].startswith("a topic named from")


def test_aliases_are_keyed_per_vault(world):
    from learnloop.learner_context import learning_context

    los = generated_world(world)
    vault = load_vault(world.root)
    first = learning_context(vault, world.repository, alias_key=b"a" * 32)
    second = learning_context(vault, world.repository, alias_key=b"b" * 32)
    again = learning_context(vault, world.repository, alias_key=b"a" * 32)

    def refs(context):
        return (sorted(context["scope"]["learning_object_ids"]),
                sorted(group["group_key"] for group in context["recurrence_groups"]))

    assert refs(first) == refs(again) and refs(first) != refs(second)
    assert los["tainted"] not in payload_text(first)


def test_the_server_keeps_its_alias_key_beside_the_endpoint_token(world):
    """``learnloop mcp serve`` makes the key (machine-local, 0600, never
    printed); a runtime reads it, and without it falls back to a key for the
    process. Attach and views never write it."""

    import os
    import stat

    from learnloop.remote.endpoint_token import alias_key_path, ensure_alias_key

    runtime = RemoteRuntime.attach(world.root, load_environment=False)
    assert not alias_key_path(world.root).exists()
    # No vault key yet: None, so the read model keys aliases for this process.
    assert runtime.alias_key() is None and not alias_key_path(world.root).exists()
    key = ensure_alias_key(world.root)
    assert stat.S_IMODE(os.stat(alias_key_path(world.root)).st_mode) == 0o600
    assert ensure_alias_key(world.root) == key and len(key) == 32
    assert RemoteRuntime.attach(world.root, load_environment=False).alias_key() == key


# -- the schema: every text field is (a), (b) or withheld without (c) --------------------------------


def _schema_text_fields(schema: dict) -> set[str]:
    """Every string field of a JSON schema, by path (``a[].b``; a union entry
    of a list by its ``kind``: ``a[kind].b``). Every object must be closed and
    every leaf typed, so no text field can hide in an open dict."""

    defs = schema.get("$defs", {})

    def resolve(node: dict) -> dict:
        while "$ref" in node:
            node = defs[node["$ref"].rsplit("/", 1)[-1]]
        return node

    found: set[str] = set()

    def walk(node: dict, path: str) -> None:
        node = resolve(node)
        branches = node.get("anyOf") or node.get("oneOf")
        if branches:
            objects = [resolve(branch) for branch in branches if resolve(branch).get("type") == "object"]
            if len(objects) > 1:
                base = path[:-2] if path.endswith("[]") else path
                for branch in objects:
                    walk(branch, f"{base}[{branch['properties']['kind']['const']}]")
                return
            for branch in branches:
                walk(branch, path)
            return
        kind = node.get("type")
        if kind == "string":
            found.add(path)
        elif kind == "array":
            walk(node["items"], f"{path}[]")
        elif kind == "object":
            assert node.get("additionalProperties") is False and node.get("properties"), f"open object at {path!r}"
            for name, child in node["properties"].items():
                walk(child, f"{path}.{name}" if path else name)
        else:
            assert kind in ("integer", "number", "boolean", "null"), f"untyped field at {path!r}: {node}"

    walk(schema, "")
    return found


def _output_leaves(value: Any, path: str, unions: set[str], out: list[tuple[str, Any]]) -> None:
    if isinstance(value, dict):
        for name, child in value.items():
            _output_leaves(child, f"{path}.{name}" if path else name, unions, out)
    elif isinstance(value, list):
        for child in value:
            label = f"{path}[{child['kind']}]" if path in unions and isinstance(child, dict) else f"{path}[]"
            _output_leaves(child, label, unions, out)
    elif isinstance(value, str):
        out.append((path, value))


def _pin_generated_item(world, tainted: str) -> None:
    """A pinned answer on an item seeded on the generated topic: its stem is (c)."""

    with world.repository.connection() as connection:
        connection.execute(
            "INSERT INTO assessment_contract_versions(id, practice_item_id, contract_hash, contract_json, "
            "schema_version, created_at) VALUES ('acv_gen', 'pi_gen', 'h_gen', ?, 1, ?)",
            ('{"prompt": "SEEDED_PROMPT_4402 swap two rows", "expected_answer": "they differ in sign"}', NOW_ISO))
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "learner_answer_md, correctness, hints_used, created_at, session_id, evidence_origin, entry_surface) "
            "VALUES ('att_gen_pinned', 'pi_gen', ?, 'short_answer', 'independent_attempt', 'GEN_PINNED_7710 equal', "
            "0.0, 0, '2026-09-22T09:00:00Z', 'old', 'human', 'desktop_practice')", (tainted,))
        connection.execute(
            "INSERT INTO grading_evidence(id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, "
            "assessment_contract_version_id) VALUES ('ge_gen', 'att_gen_pinned', 'correct', 0, 1, ?, 'acv_gen')",
            (NOW_ISO,))
        connection.commit()


def _derived_everywhere(world) -> list[str]:
    """A belief, a correction, a hypothesis, a group, a diagnosis with its
    summary, a gap matched to a belief and a gap drawn from the pinned answer,
    and a generated topic (with a seeded, answered item) in every section:
    every field exercised. Returns the derived texts planted."""

    los = generated_world(world)
    _pin_generated_item(world, los["tainted"])
    correction = "PLANTED_CORRECTION_1 each swap flips the sign once"
    with world.repository.connection() as connection:
        error_event(connection, "ev_scale", "att_own", "PLANTED_CAUSE_2 scaling leaves det fixed", "mc_scale")
        misconception_row(connection, "mc_scale", "PLANTED_CAUSE_2 scaling leaves det fixed", '["ev_scale"]',
                          correction)
        gap_row(connection, "gap_answer", source_kind="diagnosis", source_id="diag_x", attempt_id="att_own",
                item_id="pi_own", text=OWN_ANSWER, target_kind="durable", target_id="mc_scale")
        connection.execute(
            "INSERT INTO unresolved_cause_factors(id, attempt_id, candidate_causes_json, status, algorithm_version, "
            "created_at, updated_at) VALUES ('ucf_own', 'att_own', '[]', 'open', 'test', ?, ?)", (NOW_ISO, NOW_ISO))
        connection.commit()
    live_diagnosis(world.repository, "att_own", "PLANTED_SUMMARY_3 the learner lost track of signs.",
                   receipt={"failure_attempt_ids": ["att_own"]})
    return [MISCONCEPTION, CANDIDATE, HYPOTHESIS, GAP_TEXT, correction, "PLANTED_CAUSE_2", "PLANTED_SUMMARY_3",
            GENERATED_TITLE, "8841", "Permutation parity basics", "Elementary matrix inverses", "SEEDED_PROMPT_4402",
            "Drops the sign when pivoting", "Thinks a pivot may be zero", "Thinks pivots commute"]


def test_every_text_field_is_authored_an_answer_or_withheld_without_a_record(world):
    """The one rule, against the output schema itself. Each text field of
    ``learning_context`` is classified: released only by (a) authored vault
    text, (b) the learner's own pinned answer or (c) a recorded write-time
    provenance (``RELEASED_BY``), or structural (ids, codes, times, fixed
    notes). Without records nothing (c) shows, so every derived field is
    withheld; with safe records every (c) field is released, by the hook only."""

    from learnloop.learner_context import (
        AUTHORED,
        HELD_BACK as MODULE_HELD_BACK,
        LO_ALIAS_PREFIX,
        RECORDED,
        RELEASE_TYPES,
        RELEASED_BY,
        STRUCTURAL_FIELDS,
        TOPIC_WITHHELD,
        ContextLimits,
        GuardedText,
        RecordedText,
        WriteProvenance,
        learning_context,
    )
    from learnloop_mcp.server import ContextOut

    assert MODULE_HELD_BACK == HELD_BACK
    server = build_server(RemoteRuntime.attach(world.root, load_environment=False))

    async def advertised():
        async with Client(server) as client:
            return {tool.name: tool for tool in (await client.list_tools()).tools}

    fields = _schema_text_fields(anyio.run(advertised)["learning_context"].output_schema)
    assert fields == _schema_text_fields(ContextOut.model_json_schema())
    assert not set(RELEASED_BY) & set(STRUCTURAL_FIELDS), "the classes overlap"
    classified = set(RELEASED_BY) | set(STRUCTURAL_FIELDS)
    assert fields == classified, (sorted(fields - classified), sorted(classified - fields))
    assert all(rules and rules <= set(RELEASE_TYPES) for rules in RELEASED_BY.values())

    planted = _derived_everywhere(world)
    unions = {path.split("[", 1)[0] for path in fields if re.match(r"^\w+\[[a-z_]+\]\.", path)}
    vault = load_vault(world.root)

    def leaves(context: dict) -> list[tuple[str, Any]]:
        out: list[tuple[str, Any]] = []
        _output_leaves(context, "", unions, out)
        assert all(path in fields for path, _value in out)
        return out

    def stand_in(path: str, value: str) -> bool:
        return AUTHORED in RELEASED_BY.get(path, ()) and (
            value.startswith(TOPIC_WITHHELD) or value.startswith(LO_ALIAS_PREFIX))

    def check(context: dict) -> dict[str, set[str]]:
        released: dict[str, set[str]] = {}
        for path, value in leaves(context):
            if path in STRUCTURAL_FIELDS:
                assert not isinstance(value, GuardedText), (path, value)
                continue
            rules = RELEASED_BY[path]
            if stand_in(path, value):
                released.setdefault(path, set()).add("stand_in")
                continue
            matched = [rule for rule in rules if type(value) is RELEASE_TYPES[rule]]
            assert matched, (path, value, type(value))
            released.setdefault(path, set()).update(matched)
        return released

    # Without a record: nothing (c) shows; nothing planted shows anywhere.
    context = learning_context(vault, world.repository, limits=ContextLimits(traces=30))
    ContextOut.model_validate(context)
    for path, value in leaves(context):
        assert not [text for text in planted if text in value], (path, value)
    released = check(context)
    assert not [path for path, rules in released.items() if RECORDED in rules]
    assert {path for path in RELEASED_BY if RELEASED_BY[path] == {RECORDED}} & set(released) == set()
    assert {path for path, rules in RELEASED_BY.items() if rules - {RECORDED}} <= set(released), sorted(
        {path for path, rules in RELEASED_BY.items() if rules - {RECORDED}} - set(released))
    topic_fields = {path for path in RELEASED_BY if "topic" in path or "learning_object_id" in path}
    assert topic_fields <= {path for path, rules in released.items() if "stand_in" in rules}

    # With a safe, complete record for every derived text: every (c) field is
    # released, as RecordedText (the hook's type) and by nothing else.
    safe = WriteProvenance(complete=True, answers=("att_own",), items=("pi_own",), topics=("lo_matrices",))
    recorded = learning_context(vault, world.repository, limits=ContextLimits(traces=30),
                                provenance=lambda _connection, _kind, _record_id: safe)
    ContextOut.model_validate(recorded)
    released = check(recorded)
    by_hook = {path for path, rules in released.items() if RECORDED in rules}
    assert by_hook == {path for path, rules in RELEASED_BY.items() if RECORDED in rules}, sorted(
        {path for path, rules in RELEASED_BY.items() if RECORDED in rules} - by_hook)
    assert all(type(value) is RecordedText for path, value in leaves(recorded)
               if RELEASED_BY.get(path) == {RECORDED})


def test_each_kind_of_released_text_has_exactly_one_renderer():
    """A release type is constructed in one method only: authored text by the
    authored-name renderer, the learner's answer by the answer guard, a derived
    text by the write-time provenance check."""

    import learnloop.learner_context as module
    from learnloop.learner_context import AnswerText, GuardedText

    with pytest.raises(TypeError):
        GuardedText("an answer", object())
    with pytest.raises(TypeError):
        AnswerText("an answer", object())
    tree = ast.parse(inspect.getsource(module))
    functions: dict[str, list[ast.AST]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.setdefault(node.name, []).append(node)

    def owners(name: str) -> set[str]:
        found = set()
        for function_name, nodes in functions.items():
            for function in nodes:
                for child in ast.walk(function):
                    if isinstance(child, ast.Call) and getattr(child.func, "id", None) == name:
                        found.add(function_name)
        return found

    assert owners("AuthoredText") == {"_authored"}
    assert owners("AnswerText") == {"answer"}
    assert owners("RecordedText") == {"derived"}
    assert owners("GuardedText") == set()
