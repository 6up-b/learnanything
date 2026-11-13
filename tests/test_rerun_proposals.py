"""A rebuild runs again, and an equal earlier proposal is its result.

No synthesis run is reused by its manifest: a rebuild re-runs the orchestration,
each paid call answers from its checkpoint, and the rows it normalizes are
compared with the set's earlier proposals (``proposal_match``). An equal waiting
proposal is returned (and applied when asked), an equal settled one means there
is nothing new, and an equal wholly rejected one is not offered again: its
answers are dropped and the build pays for fresh ones. Each test counts the
proposal batches and their decisions, not only the calls.

No LLM: house fake clients count every call.
"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime

import pytest

from learnloop.clock import FrozenClock
from learnloop.content.proposals import patches
from learnloop.content.proposals.proposals import reject_items
from learnloop.content.synthesis import ai_contracts
from learnloop.content.synthesis.ai_contracts import ConceptGraphStructuring, ConceptMergeGroup
from learnloop.content.synthesis.source_append import append_source
from learnloop.content.synthesis.source_set_synthesis import (
    BOOTSTRAP_PROPOSAL_PURPOSE,
    StudyMapError,
    create_study_map,
    revalidate_synthesis_candidate,
)
from learnloop.content.synthesis.source_unit_inventory import run_unit_inventory
from learnloop.content.synthesis.synthesis_manifests import curriculum_snapshot_hash
from learnloop.db.repositories import Repository
from learnloop.learner.learner_profile import write_learner_profile
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_concept, upsert_concept_edge, upsert_source_set

from tests.source_append_helpers import FakeAppendClient, _bootstrap_and_add
from tests.source_inventory_helpers import FakeInventoryClient
from tests.source_set_synthesis_helpers import (
    FakeSynthesisClient,
    _CLOCK,
    _distinct_title_builder,
    _setup,
    _setup_two_chapters,
)

_LATER = FrozenClock(datetime(2026, 8, 1, 9, 30, 0, tzinfo=UTC))


def _batches(repo: Repository) -> list[tuple[str, dict[str, int]]]:
    """Each proposal batch: its purpose and how many items carry each decision (sorted; the
    fixed test clock stamps every batch alike, so their order carries no meaning here)."""

    return _sorted([
        (batch["purpose"], dict(Counter(item["decision"] for item in repo.proposal_items(batch["id"]))))
        for batch in repo.proposal_batches()
    ])


def _sorted(batches: list[tuple[str, dict[str, int]]]) -> list[tuple[str, dict[str, int]]]:
    return sorted(batches, key=lambda batch: (batch[0], sorted(batch[1].items())))


def _review_build(root, repo, client, *, clock=_CLOCK, **kwargs):
    return create_study_map(root, "set_la", client=client, brief={"depth": "intro"}, repository=repo,
                            clock=clock, apply=False, **kwargs)


def _review_append(root, repo, client, **kwargs):
    return append_source(root, "set_la", client=client, new_revision_ids=["rev_alt"], repository=repo,
                         clock=_CLOCK, **kwargs)


_BOOTSTRAP = "sourceset_bootstrap"
_APPEND = "sourceset_append"


# --- what equal means -------------------------------------------------------


def test_two_runs_of_the_same_answers_store_equal_content_whatever_their_ids_and_clocks(tmp_path):
    from learnloop.content.synthesis.proposal_match import stored_content

    first_root, first_repo = _setup(tmp_path / "a", with_exam=False)
    second_root, second_repo = _setup(tmp_path / "b", with_exam=False)
    first = _review_build(first_root, first_repo, FakeSynthesisClient())
    second = _review_build(second_root, second_repo, FakeSynthesisClient(), clock=_LATER)

    one, two = first_repo.proposal_items(first.proposal_id), second_repo.proposal_items(second.proposal_id)
    # Each run mints its own ids and stamps its own clock ...
    assert {item["id"] for item in one}.isdisjoint(item["id"] for item in two)
    assert {item["created_at"] for item in one} != {item["created_at"] for item in two}
    # ... and the content the rule compares is equal.
    assert stored_content(first_repo, one) == stored_content(second_repo, two)
    assert any(content["depends_on"] for content in stored_content(first_repo, one).values())


def test_a_changed_payload_is_not_a_match(tmp_path):
    from learnloop.content.synthesis.proposal_match import match_proposal

    root, repo = _setup(tmp_path, with_exam=False)
    first = _review_build(root, repo, FakeSynthesisClient())
    items = repo.proposal_items(first.proposal_id)
    by_id = {item["id"]: item["client_item_id"] for item in items}
    rows = [
        {**item, "id": f"fresh_{index}", "created_at": "later",
         "depends_on_client_item_ids": [by_id[dep] for dep in repo.proposal_item_dependencies(item["id"])]}
        for index, item in enumerate(items)
    ]
    found = match_proposal(repo, source_set_id="set_la", purpose=BOOTSTRAP_PROPOSAL_PURPOSE, rows=rows)
    assert found is not None and (found.proposal_id, found.kind) == (first.proposal_id, "pending")

    rows[0] = {**rows[0], "payload": {**rows[0]["payload"], "title": "Another title"}}
    assert match_proposal(repo, source_set_id="set_la", purpose=BOOTSTRAP_PROPOSAL_PURPOSE, rows=rows) is None
    assert match_proposal(repo, source_set_id="set_la", purpose="sourceset_append", rows=rows[1:]) is None


# --- the rows of the stop report's table ------------------------------------


def test_a_retry_after_an_apply_failure_applies_the_proposal_it_persisted(tmp_path, monkeypatch):
    root, repo = _setup(tmp_path, with_exam=False)
    client = FakeSynthesisClient()

    def interrupted(*_args, **_kwargs):
        raise RuntimeError("interrupted apply")

    monkeypatch.setattr(patches, "apply_accepted_items", interrupted)
    with pytest.raises(RuntimeError, match="interrupted apply"):
        create_study_map(root, "set_la", client=client, repository=repo, clock=_CLOCK, apply=True)
    monkeypatch.undo()
    first_id = repo.proposal_batches()[0]["id"]
    paid = (len(client.calls), len(client.epigraph_calls))

    result = create_study_map(root, "set_la", client=client, repository=repo, clock=_CLOCK, apply=True)

    assert result.reused and result.applied and result.proposal_id == first_id
    assert _batches(repo) == [(_BOOTSTRAP, {"accepted": 7})]
    assert (len(client.calls), len(client.epigraph_calls)) == paid


def test_a_review_build_run_twice_returns_the_waiting_proposal(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    client = FakeSynthesisClient()
    first = _review_build(root, repo, client)

    again = _review_build(root, repo, client)

    assert again.reused and not again.nothing_new and again.proposal_id == first.proposal_id
    assert _batches(repo) == [(_BOOTSTRAP, {"pending": 7})]
    # Nothing new was persisted, so no second epigraph batch is paid.
    assert (len(client.calls), len(client.epigraph_calls)) == (1, 1)
    run = repo.synthesis_run(again.synthesis_run_id)
    assert run["status"] == "completed" and run["proposal_id"] == first.proposal_id
    assert run["coverage_decisions"]["matched_proposal"] == {"proposal_id": first.proposal_id, "kind": "pending"}


def test_a_review_append_run_twice_returns_the_waiting_proposal(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    client = FakeAppendClient()
    first = _review_append(root, repo, client, auto_apply=False)

    again = _review_append(root, repo, client, auto_apply=False)

    assert again.reused and again.proposal_id == first.proposal_id
    assert again.review_item_ids == first.review_item_ids
    assert _batches(repo) == _sorted([(_BOOTSTRAP, {"accepted": 7}), (_APPEND, {"pending": 1})])
    assert (len(client.calls), len(client.epigraph_calls)) == (1, 1)


def test_a_waiting_append_run_again_with_auto_apply_applies_its_waiting_links(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    first = _review_append(root, repo, FakeAppendClient(), auto_apply=False)

    again = _review_append(root, repo, FakeAppendClient())

    assert again.reused and again.proposal_id == first.proposal_id and again.auto_applied_item_ids
    assert _batches(repo) == _sorted([(_BOOTSTRAP, {"accepted": 7}), (_APPEND, {"accepted": 1})])


def test_an_auto_applied_append_run_again_writes_nothing_new(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    client = FakeAppendClient()
    first = _review_append(root, repo, client)
    links = len(repo.entity_source_links(entity_type="facet", entity_id="facet_symmetry_definition"))

    again = _review_append(root, repo, client)

    assert again.reused and again.nothing_new and again.proposal_id == first.proposal_id
    assert again.auto_applied_item_ids == [] and again.review_item_ids == []
    assert _batches(repo) == _sorted([(_BOOTSTRAP, {"accepted": 7}), (_APPEND, {"accepted": 1})])
    assert len(repo.entity_source_links(entity_type="facet", entity_id="facet_symmetry_definition")) == links
    # The applied link moved the request, so the append is paid; nothing is persisted, so no epigraphs.
    assert (len(client.calls), len(client.epigraph_calls)) == (2, 1)


# --- a rejected proposal is not offered again (ledger D-16) -----------------


def test_a_bootstrap_whose_proposal_was_wholly_rejected_pays_for_a_fresh_one(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    client = FakeSynthesisClient()
    first = _review_build(root, repo, client)
    reject_items(root, first.proposal_id)

    again = _review_build(root, repo, client)

    assert not again.reused and again.proposal_id != first.proposal_id
    assert _batches(repo) == _sorted([(_BOOTSTRAP, {"rejected": 7}), (_BOOTSTRAP, {"pending": 7})])
    assert len(client.calls) == 2  # the dropped answer is paid for again


def test_an_append_whose_proposal_was_wholly_rejected_pays_for_a_fresh_one(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    client = FakeAppendClient()
    first = _review_append(root, repo, client, auto_apply=False)
    reject_items(root, first.proposal_id)

    again = _review_append(root, repo, client, auto_apply=False)

    assert not again.reused and again.proposal_id != first.proposal_id
    assert _batches(repo) == _sorted([(_BOOTSTRAP, {"accepted": 7}), (_APPEND, {"rejected": 1}), (_APPEND, {"pending": 1})])
    assert len(client.calls) == 2


def test_a_partly_rejected_proposal_is_returned_with_its_rejections_kept(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    client = FakeSynthesisClient()
    first = _review_build(root, repo, client)
    practice = next(item for item in repo.proposal_items(first.proposal_id) if item["item_type"] == "practice_item")
    reject_items(root, first.proposal_id, [practice["id"]])

    again = _review_build(root, repo, client)
    assert again.reused and again.proposal_id == first.proposal_id
    assert _batches(repo) == [(_BOOTSTRAP, {"pending": 6, "rejected": 1})]

    applied = create_study_map(root, "set_la", client=client, brief={"depth": "intro"}, repository=repo,
                               clock=_CLOCK, apply=True)
    assert applied.reused and applied.applied and applied.proposal_id == first.proposal_id
    assert _batches(repo) == [(_BOOTSTRAP, {"accepted": 6, "rejected": 1})]
    assert repo.proposal_item(practice["id"])["decision"] == "rejected"
    assert len(client.calls) == 1


def test_a_repaired_candidate_equal_to_a_rejected_proposal_is_refused(tmp_path, monkeypatch):
    root, repo = _setup(tmp_path, with_exam=False)
    client = FakeSynthesisClient()
    first = _review_build(root, repo, client)
    reject_items(root, first.proposal_id)

    def explode(self, batch, rows, **_kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(Repository, "persist_proposal_batch", explode)
    with pytest.raises(RuntimeError, match="disk full"):
        _review_build(root, repo, client)
    monkeypatch.undo()
    with repo.connection() as connection:
        run_id = connection.execute("SELECT id FROM synthesis_runs WHERE status = 'failed'").fetchone()["id"]

    with pytest.raises(StudyMapError) as raised:
        revalidate_synthesis_candidate(root, run_id, repository=repo, clock=_CLOCK)

    assert raised.value.code == "matches_rejected_proposal" and not raised.value.candidate_preserved
    assert _batches(repo) == [(_BOOTSTRAP, {"rejected": 7})]


# --- over-invalidation: a moved record re-pays nothing ----------------------


def test_a_budget_change_re_pays_nothing_and_writes_nothing(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    client = FakeSynthesisClient()
    first = _review_build(root, repo, client)

    again = _review_build(root, repo, client, budget_overrides={"synthesis_output_tokens": 77777})

    assert again.manifest_hash != first.manifest_hash  # the record names the budget
    assert again.reused and again.proposal_id == first.proposal_id
    assert (len(client.calls), len(client.epigraph_calls)) == (1, 1)
    assert _batches(repo) == [(_BOOTSTRAP, {"pending": 7})]


# --- under-invalidation: an input the old key missed is paid ----------------


def test_a_changed_role_override_is_paid_and_recorded(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    client = FakeSynthesisClient()
    first = _review_build(root, repo, client)
    upsert_source_set(root, {"id": "set_la", "subject_id": "linear-algebra", "title": "Linear Algebra", "members": [{
        "source_id": "src_text", "revision_id": "rev_text", "default_role": "primary_textbook",
        "scope": [{"unit_id": "chapter_symmetry", "role_override": "alternate_explanation"}], "priority": 1,
    }]}, clock=_CLOCK)

    again = _review_build(root, repo, client)

    assert len(client.calls) == 2
    assert [entry["role"] for entry in client.calls[1].unit_inventories] == ["alternate_explanation"]
    manifest = repo.synthesis_manifest_by_hash(again.manifest_hash)
    assert manifest["membership"][0]["role_overrides"] == {"chapter_symmetry": "alternate_explanation"}
    assert repo.synthesis_manifest_by_hash(first.manifest_hash)["membership"][0]["role_overrides"] == {}


class _StructuringClient(FakeSynthesisClient):
    def __init__(self):
        super().__init__(builder=_distinct_title_builder)
        self.structuring_contexts: list = []

    def run_concept_graph_structuring(self, context):
        self.structuring_contexts.append(context)
        ids = [concept["client_item_id"] for concept in context.concepts]
        return ConceptGraphStructuring(
            merge_groups=[ConceptMergeGroup(canonical_client_id=ids[0], duplicate_client_ids=ids[1:])],
        )


def test_a_new_concept_edge_is_paid_by_the_structuring_pass_and_recorded(tmp_path):
    root, repo = _setup_two_chapters(tmp_path)
    for concept_id, title in (("concept_matrix", "Matrix"), ("concept_transpose", "Transpose")):
        upsert_concept(root, concept_id, {"title": title, "type": "concept", "description": title,
                                          "aliases": [], "tags": []}, clock=_CLOCK)
    client = _StructuringClient()
    two_shards = {"synthesis_shard_input_tokens": 1}
    first = _review_build(root, repo, client, budget_overrides=two_shards)
    assert len(client.structuring_contexts) == 1
    items = len(repo.proposal_items(first.proposal_id))
    upsert_concept_edge(root, {"id": "edge_t_m", "relation_type": "prerequisite", "source": "concept_matrix",
                               "target": "concept_transpose"}, clock=_CLOCK)

    again = _review_build(root, repo, client, budget_overrides=two_shards)

    assert len(client.structuring_contexts) == 2
    assert {"source": "concept_matrix", "target": "concept_transpose", "relation_type": "prerequisite"} in (
        client.structuring_contexts[1].registry_edges
    )
    assert again.manifest_hash != first.manifest_hash
    assert again.reused and _batches(repo) == [(_BOOTSTRAP, {"pending": items})]


class _EditedInventoryClient(FakeInventoryClient):
    def run_source_unit_inventory(self, context):
        inventory = super().run_source_unit_inventory(context)
        inventory.outline_summary = "summary under the edited prompt"
        return inventory


def test_an_inventory_re_read_in_place_reaches_synthesis_and_the_record(tmp_path, monkeypatch):
    root, repo = _setup(tmp_path, with_exam=False)
    client = FakeSynthesisClient()
    first = _review_build(root, repo, client)
    before = repo.synthesis_manifest_by_hash(first.manifest_hash)["unit_inventory_versions"]
    monkeypatch.setattr(ai_contracts, "SOURCE_UNIT_INVENTORY_PROMPT",
                        ai_contracts.SOURCE_UNIT_INVENTORY_PROMPT + "\nPrefer the shortest faithful wording.")
    run_unit_inventory(repo, "ext_text", "chapter_symmetry", role="primary_textbook", profile="combined",
                       client=_EditedInventoryClient(), input_budget_tokens=20000, clock=_CLOCK)

    again = _review_build(root, repo, client)

    assert len(client.calls) == 2
    assert client.calls[1].unit_inventories[0]["inventory"]["outline_summary"] == "summary under the edited prompt"
    after = repo.synthesis_manifest_by_hash(again.manifest_hash)["unit_inventory_versions"]
    key = "rev_text:chapter_symmetry"
    assert after[key]["inventory_id"] == before[key]["inventory_id"]  # the row was re-read in place
    assert after[key]["content_hash"] != before[key]["content_hash"]


def test_an_append_resolves_its_brief_and_inherits_the_learners_level(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    client = FakeAppendClient()
    first = _review_append(root, repo, client, auto_apply=False)
    assert client.calls[0].brief["practice_items"] == "upfront"
    vault = load_vault(root)
    write_learner_profile(VaultPaths(vault.root, vault.config), starting_level="comfortable", clock=_CLOCK)

    again = _review_append(root, repo, client, auto_apply=False)

    assert len(client.calls) == 2 and client.calls[1].brief["starting_level"] == "comfortable"
    assert repo.synthesis_manifest_by_hash(again.manifest_hash)["brief"]["starting_level"] == "comfortable"
    assert repo.synthesis_manifest_by_hash(first.manifest_hash)["brief"]["practice_items"] == "upfront"


# --- the record -------------------------------------------------------------


def test_the_manifest_records_what_the_run_read(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    result = _review_build(root, repo, FakeSynthesisClient())

    manifest = repo.synthesis_manifest_by_hash(result.manifest_hash)
    entry = manifest["unit_inventory_versions"]["rev_text:chapter_symmetry"]
    assert set(entry) == {"version", "inventory_id", "extraction_id", "content_hash"}
    assert entry["extraction_id"] == "ext_text" and entry["content_hash"].startswith("sha256:")
    assert set(manifest["asset_hashes"]) == {"rev_text"}
    assert set(manifest["extractor_versions"]) == {"ext_text"}
    assert manifest["lock_fingerprint"] is None


def test_the_curriculum_snapshot_names_the_concept_edges(tmp_path):
    root, _repo = _setup(tmp_path, with_exam=False)
    for concept_id in ("concept_a", "concept_b"):
        upsert_concept(root, concept_id, {"title": concept_id, "type": "concept", "description": concept_id,
                                          "aliases": [], "tags": []}, clock=_CLOCK)
    before = curriculum_snapshot_hash(load_vault(root))
    upsert_concept_edge(root, {"id": "edge_ab", "relation_type": "related", "source": "concept_a",
                               "target": "concept_b"}, clock=_CLOCK)
    assert curriculum_snapshot_hash(load_vault(root)) != before


def test_an_append_records_the_hash_of_its_revision_diff(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    plain = _review_append(root, repo, FakeAppendClient(), auto_apply=False)
    with_diff = _review_append(root, repo, FakeAppendClient(), auto_apply=False,
                               revision_diff={"old_revision_id": "rev_text", "new_revision_id": "rev_alt"})

    assert "revision_diff_hash" not in repo.synthesis_manifest_by_hash(plain.manifest_hash)["scope"]
    assert repo.synthesis_manifest_by_hash(with_diff.manifest_hash)["scope"]["revision_diff_hash"].startswith("sha256:")
