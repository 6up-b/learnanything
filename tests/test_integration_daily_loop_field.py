"""Integration cross-checks: the daily-loop follow-ups with Slice A F1 and PF-a.

The follow-ups adopt and retire reader-authored cards (reader authoring, the
sidecar reload sweep). F1 changed the outcome view and the map's untested
state, and PF-a added family fields to practice items and the family proposer.
These check the merged behaviour, not just that the files merge.
"""
from __future__ import annotations

from learnloop.ai.spend import SpendCaps
from learnloop.db.repositories import Repository
from learnloop.field.outcomes import load_attempt_rows
from learnloop.ops.family_proposals import propose_families
from learnloop.reader import reader_authoring as AUTH
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml

from tests.test_daily_loop_reader_authored_practice import (
    ANSWER, CLOCK, QUESTION, _author, _reader_vault,
)
from tests.test_daily_loop_reference_adoption import _cite_passage, _learner_cards


def _call(ctx, name, params):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def test_adopted_reader_card_is_untested_on_the_map_with_no_outcome_row(tmp_path):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext

    paths = _reader_vault(tmp_path, cite_span=False)
    toml = paths.root / "learnloop.toml"
    text = toml.read_text(encoding="utf-8")
    toml.write_text(
        text.replace("reader_enabled = false", "reader_enabled = true")
        if "reader_enabled" in text else text + "\n[tutor_qa]\nreader_enabled = true\n",
        encoding="utf-8",
    )
    ctx = SidecarContext()
    ctx.load(paths.root)
    saved = _call(ctx, "reader.author_qa", {
        "question": QUESTION, "answer": ANSWER, "sourceId": "src1", "revisionId": "rev1",
        "subjectId": "span:ext1/s2", "clientIdempotencyKey": "cross-1",
    })
    assert saved["practiceStatus"] == "reference_only"
    _cite_passage(paths)
    ctx.reload(maintenance=False)  # F3: the reload sweep adopts the question

    card, = _learner_cards(paths)
    # PF-a: an unfamilied adopted card serializes without family fields.
    raw = read_yaml(next(paths.root.rglob(f"{card.id}.yaml")))
    assert "family_id" not in raw and "variant_relation" not in raw
    # F1: the map shows the new card, and a card is not evidence: no facet
    # point claims a Ready estimate without direct graded evidence.
    knowledge_map = _call(ctx, "get_knowledge_map", {})
    assert card.id in {point["id"] for point in knowledge_map["points"]}
    for point in knowledge_map["facetField"]["points"]:
        assert point["untested"] is True and "ready" not in point
    with ctx.repository.connection() as connection:
        assert not [row for row in load_attempt_rows(connection, ctx.vault, retrieval=True)
                    if row.features.item_id == card.id]


def test_retired_reader_card_is_never_a_family_candidate(tmp_path):
    paths = _reader_vault(tmp_path)
    saved = _author(paths)
    item_id = saved["practice_item_id"]
    caps = SpendCaps(max_candidates=1000, max_pairs=1000, max_calls=1000, max_total_tokens=10**9)
    before = propose_families(load_vault(paths.root), dry_run=True, caps=caps, price_per_million=1.0)
    AUTH.maintain(Repository(paths.sqlite_path), action="retire",
                  commitment_id=saved["commitment_id"], root=paths.root, clock=CLOCK)
    vault = load_vault(paths.root)
    assert vault.practice_items[item_id].status == "retired"
    after = propose_families(vault, dry_run=True, caps=caps, price_per_million=1.0)
    assert after["candidates"] == before["candidates"] - 1
