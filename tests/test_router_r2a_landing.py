"""Router R2a composed with main at its landing: the one exam predicate.

R2a was built before exam protection landed, so its learner-state card read
main's corpus predicate and matched only an item's provenance refs by
extraction and span id. On main the card reads the one exam predicate
(``content.sources.exam_material``) through ``item_exam_status``: an item
reserved for a goal's held-out exam, or one whose own source (its canonical
exercise, a block-level source ref) is exam or held-out material. That is a
model-context protection (R2b will send the card), so it is not behind
``goals.held_out_selection``. A diagnosed cause resting on such work keeps its
topic and status but not its statement.

The staged frame has no exam rule of its own: it evaluates only what the
scheduler admitted (``build_due_queue``, whose routine exclusions hold exam
reservations out and, behind ``goals.held_out_selection``, items made from
held-out material). So its handling agrees with exam protection's: a reserved
item (a sitting's withdrawn items stay reserved until the sitting ends) is
never offered, and with the switch off a held-out item is served exactly as
the predecessor served it.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION
from learnloop.clock import FrozenClock
from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.daily_plan.engine import PlanEnv, build_plan
from learnloop.daily_plan.policy import policy_for
from learnloop.daily_plan.router_card import CardGatherer
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.ingest.locators import format_block_span
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_practice_item
from learnloop.vault.yaml_io import read_yaml

from tests.daily_plan_fakes import MovableClock, iso, seed_due
from tests.helpers import create_daily_plan_vault
from tests.source_service_fakes import build_textbook_vault
from tests.test_exam_protection_review import _switch_off
from tests.test_router_card import LAST, _attempt, _card, _card_world, _hypothesis

A = ROUTER_STAGED_FRAME_ALGORITHM_VERSION
PAST = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


def _reserve(repository, item_id: str, goal_id: str = "goal_exam") -> None:
    repository.insert_exam_pool_items([{"id": new_ulid(), "goal_id": goal_id, "practice_item_id": item_id,
                                        "facet_id": None, "difficulty_stratum": "mid",
                                        "reserved_at": "2026-10-13T00:00:00Z", "released_at": None}])


def _rewrite(root, item_id: str, **fields) -> None:
    vault = load_vault(root)
    path = next(VaultPaths(vault.root, vault.config).root.rglob(f"{item_id}.yaml"))
    payload = read_yaml(path)
    payload.update(fields)
    upsert_practice_item(root, payload, clock=FrozenClock(datetime(2026, 1, 1, tzinfo=UTC)))


def _textbook_world(tmp_path):
    """The textbook vault with three kinds of exam material, none of which
    R2a's provenance-only match saw: an item whose canonical exercise lies in
    a held-out unit, an item reserved for a goal's held-out exam, and an item
    citing a block of the exam source by its ``block_span_v1`` locator."""

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"exercises": "held_out_evaluation"})
    _rewrite(paths.root, "pi_eigen_1", canonical_exercise={
        "source_id": "src_text", "extraction_id": "ext_text", "span_ids": [spans["exercises"][1]],
        "relation": "verbatim"})
    _reserve(repository, "pi_eigen_2")
    _rewrite(paths.root, "pi_determinant_1", provenance={"origin": "human", "source_refs": [{
        "ref_type": "canonical_source", "ref_id": "src_exam", "locator": format_block_span("ext_exam", "s1")}]})
    return paths, repository


def test_the_card_withholds_what_the_one_exam_predicate_names(tmp_path):
    paths, repository = _textbook_world(tmp_path)
    unknowns: list[str] = []
    withheld = CardGatherer(load_vault(paths.root), repository)._withheld_items(unknowns)
    assert withheld.available and unknowns == []
    assert {"pi_eigen_1", "pi_eigen_2", "pi_determinant_1"} <= withheld.item_ids
    assert withheld.reason("pi_eigen_3") is None and withheld.reason("pi_matmul_1") is None


def test_the_cards_exam_protection_is_not_behind_the_serving_switch(tmp_path):
    """``goals.held_out_selection = false`` restores the predecessor's serving
    selection; the card is a model context, so it withholds the same items."""

    paths, repository = _textbook_world(tmp_path)
    before = CardGatherer(load_vault(paths.root), repository)._withheld_items([])
    _switch_off(paths.root)
    after = CardGatherer(load_vault(paths.root), repository)._withheld_items([])
    assert before == after and {"pi_eigen_1", "pi_eigen_2", "pi_determinant_1"} <= after.item_ids


def test_a_cause_diagnosed_from_exam_work_shows_no_statement(tmp_path, monkeypatch):
    env = _card_world(tmp_path, monkeypatch)
    _attempt(env, "att_a", "pi_a", "lo_m1", iso(LAST), answer="EXAM_WORDS_6610", correctness=0.0,
             attempt_type="exam_attempt")
    _hypothesis(env, "hyp_exam", status="candidate", statement="STATEMENT_FROM_THE_EXAM_4471", evidence={})
    card = _card(env)
    [cause] = [entry for entry in card["json"]["open_hypotheses"] if entry["kind"] == "diagnosed_cause"]
    assert (cause["hypothesis_id"], cause["topic"], cause["status"]) == ("hyp_exam", "M1", "candidate")
    # The shared protection names why (learner_protection, the chat frontend's too).
    assert cause["statement"] is None and cause["withheld"] == "exam or held-out material"
    assert "STATEMENT_FROM_THE_EXAM_4471" not in card["text"] and "EXAM_WORDS_6610" not in card["text"]
    assert "statement withheld (exam or held-out material)" in card["text"]


def test_a_cause_diagnosed_from_ordinary_practice_keeps_its_statement(tmp_path, monkeypatch):
    env = _card_world(tmp_path, monkeypatch)
    _attempt(env, "att_a", "pi_a", "lo_m1", iso(LAST), answer="right", correctness=0.0)
    _hypothesis(env, "hyp_open", status="candidate", statement="Swaps rows and columns", evidence={})
    [cause] = [entry for entry in _card(env)["json"]["open_hypotheses"] if entry["kind"] == "diagnosed_cause"]
    assert cause["statement"] == "Swaps rows and columns" and cause["withheld"] is None


# -- the staged frame serves only what the scheduler admitted --------------------------------------


def _real_queue_world(tmp_path, monkeypatch, *, switch_off: bool = False):
    paths = create_daily_plan_vault(
        tmp_path / "vault", learning_objects={"lo_m1": [("pi_ok", 2.0), ("pi_reserved", 2.0), ("pi_held", 2.0)]},
        version=A,
    )
    if switch_off:
        _switch_off(paths.root)
    vault = load_vault(paths.root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    for item in ("pi_ok", "pi_reserved", "pi_held"):
        seed_due(repository, item, due=PAST, last=LAST)
    _reserve(repository, "pi_reserved")
    # The held-out partition, stubbed for this item; the switch is read for real.
    from learnloop.scheduling import serving_exclusions

    monkeypatch.setattr(serving_exclusions, "held_out_items", lambda _vault, _repo: frozenset({"pi_held"}))
    clock = MovableClock()
    env = PlanEnv(vault=vault, repository=repository, clock=clock, session_id="s1", eligible=None)
    env.policy = policy_for(vault, repository, session_id="s1", clock=clock)
    return env


def _routed(env) -> tuple[list[str], list[dict]]:
    record = build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    planned = [item.practice_item_id for block in record.blocks for item in block.items]
    with env.repository.connection() as connection:
        rows = [dict(row) for row in connection.execute(
            "SELECT * FROM router_decisions WHERE decision_kind = 'plan_block' ORDER BY created_at, id")]
    return planned, rows


def test_exam_reserved_and_held_out_items_never_reach_the_frame(tmp_path, monkeypatch):
    env = _real_queue_world(tmp_path, monkeypatch)
    planned, rows = _routed(env)
    assert "pi_ok" in planned and "pi_reserved" not in planned and "pi_held" not in planned
    assert rows and all(row["policy"] == "staged_v1" for row in rows)
    for row in rows:
        # Never offered, so never the frame's to refuse: no named refusal, no candidate.
        assert "pi_reserved" not in row["candidates_json"] and "pi_held" not in row["candidates_json"]
        assert "pi_reserved" not in row["exclusions_json"] and "pi_held" not in row["exclusions_json"]


def test_with_the_serving_switch_off_the_frame_serves_held_out_items_as_the_predecessor(tmp_path, monkeypatch):
    env = _real_queue_world(tmp_path, monkeypatch, switch_off=True)
    planned, rows = _routed(env)
    assert "pi_held" in planned and "pi_reserved" not in planned
    for row in rows:
        assert "pi_held" not in json.dumps(json.loads(row["exclusions_json"]).get("named", {}))
