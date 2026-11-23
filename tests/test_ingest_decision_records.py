"""Why x and not y at the three ingest choices that were silent: an automatic build's scope, the inventory row each
unit's synthesis read, and what the apply step applied or left for review (ADR-017 decision records).

The planner's job id is the build's trace, so ``learnloop why <planner job id>`` answers all three from stored rows.
Every model call is a house fake.
"""

from __future__ import annotations

from learnloop import provenance
from learnloop.content.pipeline.add_source import (
    AUTO_STUDY_MAP_JOB,
    INGEST_BUILD_SCOPE,
    AddSourceOptions,
    BuildPlanChoice,
    Chapter,
    Coverage,
    ScopeDecision,
    add_source,
    advance_reading_build,
    build_scope_record,
    outline_chapters,
)
from learnloop.content.sources.source_outline import build_source_outline, resolve_extraction_id
from learnloop.content.synthesis.source_append import _auto_apply_refusal, _waiting_reasons
from learnloop.content.synthesis.source_set_synthesis import (
    INGEST_AUTO_APPLY,
    INGEST_INVENTORY_CHOICE,
    _map_apply_rule,
    gate_refusal,
)
from learnloop.content.synthesis.source_unit_inventory import best_inventory, inventory_choice
from learnloop.vault.loader import load_vault
from learnloop.why import reader

from tests.ux_phase1_auto_build_helpers import _jobs
from tests.ux_phase1_support import CLOCK, fake_services, fresh_library, grant_consent, set_config, write_book


def _add(root, jobs, source):
    return add_source(load_vault(root), jobs, str(source), AddSourceOptions(), clock=CLOCK)


def _planner_ids(repo):
    return [job["id"] for job in repo.ingest_jobs_by_types((AUTO_STUDY_MAP_JOB,))]


def _trace(repo, trace_id, kind=None):
    with repo.connection() as connection:
        return provenance.read(connection, trace_id, kind=kind)


def _labels(repo, source_id):
    extraction_id = resolve_extraction_id(repo, source_id)
    return {chapter.unit_id: chapter.label for chapter in outline_chapters(build_source_outline(repo, extraction_id))}


# -- an automatic build, end to end -----------------------------------------------------------------------------


def test_an_automatic_build_records_scope_inventory_rows_and_apply_under_its_planners_trace(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services())
    item = _add(root, jobs, write_book(tmp_path))
    (planner,) = _planner_ids(repo)

    records = _trace(repo, planner)
    kinds = [record.kind for record in records]
    assert INGEST_BUILD_SCOPE in kinds and INGEST_INVENTORY_CHOICE in kinds and INGEST_AUTO_APPLY in kinds

    (scope,) = [record for record in records if record.kind == INGEST_BUILD_SCOPE]
    labels = _labels(repo, item["source_id"])
    assert scope.status == "chosen" and scope.rule == "reading_order"
    assert scope.subject_kind == "job" and scope.subject_id == planner
    assert [labels[chapter_id] for chapter_id in scope.facts["chapter_ids"]] == [
        "1 Probability and counting", "2 Conditional probability",
    ]
    assert scope.facts["chapters_left_for_later"] > 0

    (inventory,) = [record for record in records if record.kind == INGEST_INVENTORY_CHOICE]
    run_id = inventory.detail_id
    assert inventory.detail_table == "synthesis_runs" and repo.synthesis_run(run_id) is not None
    units = inventory.facts["units"]
    assert units and all(unit["row"] and unit["rule"] == "only_row" for unit in units)
    # The rows it names are the ones the manifest records.
    manifest = repo.synthesis_manifest(repo.synthesis_run(run_id)["manifest_id"])
    recorded = {entry["inventory_id"] for entry in manifest["unit_inventory_versions"].values()}
    assert {unit["row"] for unit in units} == recorded

    (applied,) = [record for record in records if record.kind == INGEST_AUTO_APPLY]
    assert applied.status == "chosen" and applied.rule == "applied" and applied.facts["applied_count"] > 0
    assert applied.alternatives == ()

    # `learnloop why <planner job id>` reads the same trace.
    explanation = reader.answer(repo, planner, loaded=load_vault(root))
    assert explanation is not None
    assert {INGEST_BUILD_SCOPE, INGEST_INVENTORY_CHOICE, INGEST_AUTO_APPLY} <= {
        record["kind"] for record in explanation["records"]
    }


def test_a_build_waiting_for_a_look_says_why_each_item_waits(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    set_config(root, {("ingest", "auto_apply_passing_builds"): False})
    repo, jobs = _jobs(root, fake_services())
    _add(root, jobs, write_book(tmp_path))
    (planner,) = _planner_ids(repo)

    (record,) = _trace(repo, planner, kind=INGEST_AUTO_APPLY)
    assert record.status == "deferred" and record.rule == "apply_not_requested"
    proposal_items = repo.proposal_items(record.chosen_ref)
    concepts = [item["id"] for item in proposal_items if item["item_type"] == "concept"]
    assert concepts
    # "Why does this concept need a look?": the record names it, with the reason.
    with repo.connection() as connection:
        naming = provenance.read_naming(connection, concepts[0], kind=INGEST_AUTO_APPLY)
    assert naming and {"ref": concepts[0], "lost_by": "apply_not_requested"} in naming[0].alternatives


def test_reading_on_records_the_chapters_skipped_as_built(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services())
    item = _add(root, jobs, write_book(tmp_path))
    source_id = item["source_id"]
    labels = _labels(repo, source_id)
    by_label = {label: unit_id for unit_id, label in labels.items()}
    advance_reading_build(jobs, resolve_extraction_id(repo, source_id), by_label["2 Conditional probability"])

    second = [planner for planner in _planner_ids(repo) if _trace(repo, planner, kind=INGEST_BUILD_SCOPE)]
    scopes = [_trace(repo, planner, kind=INGEST_BUILD_SCOPE)[0] for planner in second]
    latest = max(scopes, key=lambda record: record.created_at)
    assert [labels[chapter_id] for chapter_id in latest.facts["chapter_ids"]] == ["3 Random variables"]
    skipped = {labels[alternative["ref"]] for alternative in latest.alternatives
               if alternative["lost_by"] == "already_built"}
    assert {"1 Probability and counting", "2 Conditional probability"} <= skipped
    # The append that build ran records its inventory rows and its apply under the same trace.
    trace_kinds = {record.kind for record in _trace(repo, latest.trace_id)}
    assert {INGEST_INVENTORY_CHOICE, INGEST_AUTO_APPLY} <= trace_kinds


# -- the record builders, on plain values ----------------------------------------------------------------------


def _chapter(unit_id, *units):
    return Chapter(unit_id=unit_id, label=unit_id, unit_ids=tuple(units or (unit_id,)), tokens=100)


def test_the_scope_record_names_withheld_built_and_reserved_chapters():
    chapters = (_chapter("ch1"), _chapter("ch2"), _chapter("ch3"), _chapter("ch4"), _chapter("ch5"))
    choice = BuildPlanChoice(extraction_id="ext", revision_id="rev", chapters=[chapters[2]], whole=False,
                             unit_ids=["ch3"], stages={}, totals={}, outline=None,
                             withheld_unit_ids=frozenset({"exam_u"}))
    decision = ScopeDecision(choice, "reading_order", frozenset({"exam_u"}), chapters,
                             Coverage(built={"ch1"}, reserved={"ch2"}))

    record = build_scope_record(decision, source_id="src", job_id="job_1", resolved=("rev", "ext"))

    assert provenance.check_no_prose(record) == []
    assert (record.status, record.rule, record.chosen_ref) == ("chosen", "reading_order", "src")
    assert list(record.alternatives) == [
        {"ref": "exam_u", "lost_by": "exam_material"},
        {"ref": "ch1", "lost_by": "already_built"},
        {"ref": "ch2", "lost_by": "being_built"},
    ]
    assert record.facts["chapters_left_for_later"] == 2 and record.facts["chapter_ids"] == ["ch3"]


def test_a_book_that_is_all_exam_material_records_an_exclusion():
    record = build_scope_record(ScopeDecision(None, "whole_reading_exam_material", None), source_id="src",
                                job_id="job_1", resolved=("rev", "ext"))
    assert (record.status, record.rule, record.facts["withheld_unit_count"]) == (
        "excluded", "whole_reading_exam_material", None,
    )


def _row(row_id, *, semantic_hash="h1", prompt="p2", route=("codex", "m"), profile="combined", created="2026-01-02"):
    return {"id": row_id, "unit_id": "u1", "unit_semantic_hash": semantic_hash, "prompt_version": prompt,
            "provider": route[0], "model": route[1], "inventory_profile": profile, "inventory_schema_version": 3,
            "created_at": created}


def test_the_inventory_choice_is_best_inventory_with_its_reasons():
    rows = [
        _row("old_prompt", prompt="p1", created="2026-01-03"),
        _row("current", created="2026-01-01"),
        _row("old_text", semantic_hash="h0", created="2026-01-04"),
        _row("other_route", route=("openrouter", "x"), created="2026-01-05"),
        _row("older_twin", created="2025-12-31"),
    ]
    query = {"semantic_hash": "h1", "prompt_version": "p2", "provider": "codex", "model": "m", "profile": "combined"}

    choice = inventory_choice(rows, "u1", **query)

    assert choice.row is best_inventory(rows, "u1", **query)
    assert choice.row["id"] == "current" and choice.rule == "newest" and choice.candidates == 5
    assert dict(choice.lost) == {
        "old_prompt": "prompt_version", "old_text": "unit_text", "other_route": "route", "older_twin": "newest",
    }
    alone = inventory_choice([_row("only")], "u1", **query)
    assert (alone.row["id"], alone.rule, alone.lost) == ("only", "only_row", ())
    assert inventory_choice(rows, "u_missing", **query).rule == "no_row"


class _Ref:
    def __init__(self, span_id):
        self.span_id = span_id


def test_the_append_lane_says_which_condition_kept_a_link_back():
    link = {"relation": "support", "locator": "p1", "target_entity_id": "lo_1", "expected_target_hash": "h"}
    assert _auto_apply_refusal(link, [_Ref("s1")], "h", "learning_object") is None
    assert _auto_apply_refusal(link, [_Ref("s1")], "h2", "learning_object") == "target_changed"
    assert _auto_apply_refusal(link, [_Ref("s1")], None, "learning_object") == "target_missing"
    assert _auto_apply_refusal(link, [_Ref(None)], "h", "learning_object") == "span_unresolved"
    assert _auto_apply_refusal({**link, "relation": "restructure"}, [], "h", "facet") == "relation_not_routine"
    assert _auto_apply_refusal({**link, "relation": "assessment_alignment"}, [], "h", "facet") == (
        "assessment_alignment_target"
    )

    items = [
        {"id": "i1", "client_item_id": "c1", "item_type": "provenance_link"},
        {"id": "i2", "client_item_id": "c2", "item_type": "provenance_link"},
        {"id": "i3", "client_item_id": "c3", "item_type": "concept"},
    ]
    assert _waiting_reasons(items, {"i1"}, {"c2": "target_changed"}, lane_refusal=None) == [
        ("i2", "target_changed"), ("i3", "review_only:concept"),
    ]
    assert _waiting_reasons(items, set(), {"c2": "target_changed"}, lane_refusal="undone") == [
        ("i1", "undone"), ("i2", "target_changed"), ("i3", "review_only:concept"),
    ]


def test_a_closed_gate_names_its_switch_or_undo():
    class Gate:
        refusal = None

        def __call__(self):
            self.refusal = "undone"
            return False

    gate = Gate()
    assert _map_apply_rule(True, False, gate) == "undone"
    assert _map_apply_rule(False, False, gate) == "apply_not_requested"
    assert _map_apply_rule(True, True, gate) == "nothing_new"
    assert _map_apply_rule(True, False, lambda: True) == "applied"
    assert gate_refusal(lambda: False) == "gate_closed"
