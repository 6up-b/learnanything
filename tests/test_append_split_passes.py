"""An append too large for one request is split into checkpointed passes instead of refused.

The new inventories are split, in order, into passes whose requests each fit ``append_input_ceiling`` with room for
a span round; each pass sends the run's one neighbourhood and is saved under its own checkpoint, so a stop or crash
resumes at the next pass and pays for none twice; the passes' answers are merged into one proposal, applied once. A
split append applies the rows one unsplit append would, and a request that fits is never split. What cannot be split
(a single inventory over the ceiling) is still refused, with the same code.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from learnloop.content.synthesis.ai_contracts import (
    AppendProvenanceLink,
    AppendReconciliation,
    SynthSpanRef,
    append_reconciliation_prompt,
)
from learnloop.content.synthesis.source_append import append_source
from learnloop.content.synthesis.source_set_synthesis import StudyMapError, create_study_map
from learnloop.content.synthesis.source_unit_inventory import run_unit_inventory
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_source_set
from tests.source_append_helpers import _CLOCK, FakeAppendClient, SymmetryInventoryClient, _neighborhood_facet_id
from tests.source_inventory_helpers import _block, _ir, _persist, _register_revision
from tests.source_set_synthesis_helpers import FakeSynthesisClient, _setup

UNITS = ("chapter_1", "chapter_2", "chapter_3")


def _three_new_units(tmp_path):
    """Bootstrap and apply a map, then add one member with three new units (each mentions the map's concept)."""

    root, repo = _setup(tmp_path, with_exam=False)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo, clock=_CLOCK, apply=True,
                     brief={"depth": "intro"})
    _register_revision(repo, source_id="src_alt", revision_id="rev_alt")
    ir = _ir([(unit, f"Symmetric matrices, part {n}", [_block(f"s{n}", f"Part {n}: a real A with A^T = A is "
                                                                      "called symmetric. " * 30)],
               f"sha256:{unit}", n) for n, unit in enumerate(UNITS, start=1)])
    _persist(repo, ir, revision_id="rev_alt", extraction_id="ext_alt")
    for unit in UNITS:
        run_unit_inventory(repo, "ext_alt", unit, role="alternate_explanation", profile="combined",
                           client=SymmetryInventoryClient(), input_budget_tokens=20000, clock=_CLOCK)
    vault = load_vault(root)
    members = [{"source_id": m.source_id, "revision_id": m.revision_id, "default_role": m.default_role,
                "scope": [{"unit_id": s.unit_id} for s in m.scope], "priority": m.priority}
               for m in next(s for s in vault.source_sets if s.id == "set_la").members]
    members.append({"source_id": "src_alt", "revision_id": "rev_alt", "default_role": "alternate_explanation",
                    "scope": [{"unit_id": unit} for unit in UNITS], "priority": 1})
    upsert_source_set(root, {"id": "set_la", "subject_id": "linear-algebra", "title": "Linear Algebra",
                             "members": members}, clock=_CLOCK)
    return root, repo


def _links(context, _n):
    """One provenance link per new unit the request names, each citing that unit's span: what an unsplit append
    and the passes of a split one both write, unit for unit."""

    target = _neighborhood_facet_id(context)
    links = []
    for entry in context.new_inventories:
        spans = [span for claim in entry["inventory"].get("claims") or [] for span in claim.get("span_ids") or []]
        links.append(AppendProvenanceLink(
            client_item_id=f"plink_{entry['unit_id']}", reconciliation_intent="alternate_explanation",
            target_entity_type="facet", target_entity_id=target, relation="alternate",
            span=SynthSpanRef(extraction_id=entry["extraction_id"], unit_id=entry["unit_id"], span_id=spans[0],
                              relation="support")))
    return AppendReconciliation(summary="append alternate explanations", provenance_links=links)


def _applied(repo) -> list[tuple[Any, ...]]:
    with repo.connection() as connection:
        rows = connection.execute(
            "SELECT entity_type, entity_id, extraction_id, locator, relation, status FROM entity_source_links "
            "WHERE extraction_id = 'ext_alt' ORDER BY locator").fetchall()
    return [tuple(row) for row in rows]


def _unsplit(tmp_path):
    """The rows one unsplit append of the three units applies (under the default ceiling, one request)."""

    root, repo = _three_new_units(tmp_path / "whole")
    client = FakeAppendClient(builder=_links)
    append_source(root, "set_la", client=client, new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)
    assert len(client.calls) == 1
    return _applied(repo)


def _whole_request(root, repo) -> int:
    """The unsplit request's input estimate in this vault, as the append's budget reads it: one request is asked
    and fails (nothing is saved or applied), and its context is sized as the shard runner sizes every request."""

    def fails(_context, _n):
        raise RuntimeError("measured, not answered")

    measuring = FakeAppendClient(builder=fails)
    with pytest.raises(RuntimeError):
        append_source(root, "set_la", client=measuring, new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)
    (context,) = measuring.calls
    return max(1, (len(append_reconciliation_prompt(context))
                   + len(json.dumps(AppendReconciliation.model_json_schema()))) // 4)


def _split_budget(root, repo, **extra: int) -> dict[str, int]:
    """The whole request just over the ceiling (so every single unit's request is under it)."""

    return {"append_input_ceiling": _whole_request(root, repo) - 1, **extra}


def test_an_append_over_its_ceiling_is_split_and_applies_what_one_unsplit_append_would(tmp_path):
    whole_rows = _unsplit(tmp_path)
    assert len(whole_rows) == 3
    root, repo = _three_new_units(tmp_path / "split")
    client = FakeAppendClient(builder=_links)
    result = append_source(root, "set_la", client=client, new_revision_ids=["rev_alt"], repository=repo,
                           clock=_CLOCK, budget_overrides=_split_budget(root, repo))
    assert [[entry["unit_id"] for entry in context.new_inventories] for context in client.calls] == [
        [unit] for unit in UNITS]
    assert all(context.neighborhood == client.calls[0].neighborhood for context in client.calls)
    assert all((context.shard_ordinal, context.shard_count) == (0, 1) for context in client.calls)
    assert repo.synthesis_run(result.synthesis_run_id)["status"] == "completed"
    assert _applied(repo) == whole_rows


def test_passes_hold_as_many_units_as_fit_with_room_for_a_span_round(tmp_path):
    whole_rows = _unsplit(tmp_path)
    root, repo = _three_new_units(tmp_path / "split")
    client = FakeAppendClient(builder=_links)
    # A one-token span-round reserve: two units fit under the ceiling with it, three do not.
    append_source(root, "set_la", client=client, new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK,
                  budget_overrides=_split_budget(root, repo, synthesis_span_request_max_count=1,
                                                 synthesis_span_char_cap=4))
    assert [len(context.new_inventories) for context in client.calls] == [2, 1]
    assert _applied(repo) == whole_rows


def test_an_append_that_fits_is_one_request_as_before(tmp_path):
    root, repo = _three_new_units(tmp_path)
    client = FakeAppendClient(builder=_links)
    append_source(root, "set_la", client=client, new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)
    (context,) = client.calls
    assert [entry["unit_id"] for entry in context.new_inventories] == list(UNITS)


@pytest.mark.parametrize("crash_at", [1, 2, 3])
def test_a_crash_at_any_pass_resumes_at_that_pass_and_applies_once(tmp_path, crash_at):
    whole_rows = _unsplit(tmp_path)
    root, repo = _three_new_units(tmp_path / "split")
    asked: list[str] = []

    def crashing(context, n):
        asked.append(context.new_inventories[0]["unit_id"])
        if len(asked) == crash_at:
            raise RuntimeError("the process died here")
        return _links(context, n)

    with pytest.raises(RuntimeError):
        append_source(root, "set_la", client=FakeAppendClient(builder=crashing), new_revision_ids=["rev_alt"],
                      repository=repo, clock=_CLOCK, budget_overrides=_split_budget(root, repo))
    assert _applied(repo) == []  # nothing applied before every pass answered
    resumed = FakeAppendClient(builder=_links)
    append_source(root, "set_la", client=resumed, new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK,
                  budget_overrides=_split_budget(root, repo))
    # The passes answered before the crash are their checkpoints': only the crashed pass and those after are asked.
    assert [context.new_inventories[0]["unit_id"] for context in resumed.calls] == list(UNITS[crash_at - 1:])
    assert _applied(repo) == whole_rows


def test_a_single_unit_over_the_ceiling_is_still_refused_before_any_call(tmp_path):
    root, repo = _three_new_units(tmp_path)
    client = FakeAppendClient(builder=_links)
    with pytest.raises(StudyMapError) as raised:
        append_source(root, "set_la", client=client, new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK,
                      budget_overrides={"append_input_ceiling": 1000})
    assert raised.value.code == "append_input_over_ceiling" and client.calls == []
    assert _applied(repo) == []


def test_each_pass_is_its_own_paid_request_under_the_appends_limits(tmp_path):
    from learnloop.ai.execution import observe_model_calls

    root, repo = _three_new_units(tmp_path)
    budget = _split_budget(root, repo)
    receipts: list[dict[str, Any]] = []

    def observe(event: str, payload: dict[str, Any]) -> None:
        if event == "start" and payload["purpose"] == "append_reconciliation":
            receipts.append(payload)

    with observe_model_calls(observe):
        append_source(root, "set_la", client=FakeAppendClient(builder=_links), new_revision_ids=["rev_alt"],
                      repository=repo, clock=_CLOCK, budget_overrides=budget)
    assert len(receipts) == 3 and all(receipt["parent_call_id"] is None for receipt in receipts)
    assert {receipt["output_budget_tokens"] for receipt in receipts} == {
        load_vault(root).config.ingest.budgets.append_output_tokens}


def test_a_split_appends_answers_merge_once_per_concept_and_restructure():
    from learnloop.content.synthesis import source_append as SA
    from learnloop.content.synthesis.ai_contracts import AppendRestructure, SynthConcept

    first = AppendReconciliation(summary="part", concepts=[SynthConcept(client_item_id="c1", title="Symmetric matrix")],
                                 restructures=[AppendRestructure(client_item_id="r1", target_entity_id="lo_a")])
    second = AppendReconciliation(summary="part", concepts=[SynthConcept(client_item_id="c2",
                                                                         title="Symmetric Matrix")],
                                  restructures=[AppendRestructure(client_item_id="r2", target_entity_id="lo_a"),
                                                AppendRestructure(client_item_id="r3", target_entity_id="lo_b")])
    merged = SA._merge_append(first, second)
    assert merged.summary == "part" and len(merged.concepts) == 2 and len(merged.restructures) == 3
    run = type("Run", (), {"brief": {}})()
    answer, _usage, diagnostics = SA._within_the_brief(run, merged, shard_count=2)
    assert [concept.client_item_id for concept in answer.concepts] == ["c1"]
    assert [restructure.client_item_id for restructure in answer.restructures] == ["r1", "r3"]
    (diagnostic,) = diagnostics
    assert diagnostic["gate"] == "split_append_restructures" and diagnostic["entity_refs"] == ["lo_a"]
    # An unsplit append's answer is the model's, as before.
    unsplit, _usage, none = SA._within_the_brief(run, merged, shard_count=1)
    assert unsplit is merged and none == []


def test_every_pass_shares_its_prompt_through_the_neighbourhood_so_providers_can_cache_it(tmp_path):
    """The owner's rule (2026-11-20): take advantage of cached tokens. A pass's request renders the task, then the
    context's fields in sorted order (``render_structured_prompt``): the brief, the change kind, the exam profile and
    the neighbourhood come before the pass's own new inventories, so every pass of a split append sends the same
    prefix through the neighbourhood, the part a provider's prompt cache can reuse."""

    root, repo = _three_new_units(tmp_path)
    client = FakeAppendClient(builder=_links)
    append_source(root, "set_la", client=client, new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK,
                  budget_overrides=_split_budget(root, repo))
    prompts = [append_reconciliation_prompt(context) for context in client.calls]
    assert len(prompts) == 3
    shared = prompts[0][:prompts[0].index('"new_inventories"')]
    assert '"neighborhood"' in shared and all(prompt.startswith(shared) for prompt in prompts)
    assert len(shared) > len(prompts[0]) // 2  # most of each request is the shared part
