"""Slice 2 T5 at ingest: the structuring pass, the append lane and revalidation.

The graph-structuring model receives registry concept titles and definitions
for the nominated candidates (not ids alone) and decides; the append
neighbourhood unions embedding nominations with the lexical reasons; the kill
switch restores the pre-T5 requests; revalidation never pays.
"""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

import pytest

from learnloop.ai.spend import SpendCaps
from learnloop.ai.transport import render_structured_prompt
from learnloop.content.synthesis.ai_contracts import (
    CONCEPT_GRAPH_REGISTRY_PROMPT_VERSION,
    CONCEPT_GRAPH_STRUCTURING_PROMPT,
    CONCEPT_GRAPH_STRUCTURING_PROMPT_VERSION,
    ConceptGraphContext,
    ConceptGraphStructuring,
    ConceptGraphStructuringWithRegistry,
    ConceptMergeGroup,
    RegistryConceptMerge,
    concept_graph_structuring_prompt,
)
from learnloop.content.synthesis.source_append import append_source
from learnloop.content.synthesis.source_set_synthesis import (
    create_study_map,
    revalidate_synthesis_candidate,
)
from learnloop.db.repositories import Repository
from learnloop.ops.embedding_backfill import backfill_embeddings
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_concept, upsert_facet

from tests.embedding_fakes import BagOfWordsEmbedder, ExplodingFactory
from tests.helpers import append_config_toml
from tests.test_source_append import FakeAppendClient, _bootstrap_and_add
from tests.test_source_set_synthesis import (
    _CLOCK,
    FakeSynthesisClient,
    _distinct_title_builder,
    _setup,
    _setup_two_chapters,
)

REGISTRY_ID = "concept_symmetric_registry"


def _enable(root: Path, *, nominations: bool = True) -> None:
    path = root / "learnloop.toml"
    text = path.read_text(encoding="utf-8")
    block = "[embedding]\nenabled = false\nbackfill_enabled = false\n"
    assert block in text
    text = text.replace(block, "[embedding]\nenabled = true\nbackfill_enabled = true\n")
    text = text.replace("dimensions = 4096", "dimensions = 64")
    path.write_text(text, encoding="utf-8")
    append_config_toml(root, f"""
        [graph_nomination]
        enabled = {'true' if nominations else 'false'}
        top_k = 2
    """)


def _backfill(root: Path, embedder: BagOfWordsEmbedder, recipes: tuple[str, ...]) -> None:
    report = backfill_embeddings(
        load_vault(root), caps=SpendCaps(max_candidates=1000, max_total_tokens=10**7),
        recipes=recipes, client_factory=lambda: embedder,
    )
    assert report["status"] == "complete", report


def _registry_concept(root: Path, *, type_: str = "concept") -> None:
    upsert_concept(root, REGISTRY_ID, {
        "title": "Symmetric matrix", "type": type_,
        "description": "A square matrix equal to its own transpose.",
        "aliases": [], "tags": [],
    }, clock=_CLOCK)


class RegistryStructuringClient(FakeSynthesisClient):
    """Records the structuring context and decides what the test tells it to."""

    def __init__(self, decide=None):
        super().__init__(builder=_distinct_title_builder)
        self.structuring_contexts: list[ConceptGraphContext] = []
        self.decide = decide

    def run_concept_graph_structuring(self, context):
        self.structuring_contexts.append(context)
        ids = [c["client_item_id"] for c in context.concepts]
        merges = [ConceptMergeGroup(canonical_client_id=ids[0], duplicate_client_ids=ids[1:])]
        if not context.registry_concept_details:
            return ConceptGraphStructuring(merge_groups=merges)
        return ConceptGraphStructuringWithRegistry(
            merge_groups=merges,
            registry_merges=self.decide(context, ids) if self.decide else [],
        )


def _ledger(repo: Repository) -> list[dict]:
    with repo.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM judgment_ledger WHERE task='same_concept' ORDER BY created_at, id"
        )]


def _synthesize(root, repo, client, **kwargs):
    return create_study_map(
        root, "set_la", client=client, brief={"depth": "intro"}, repository=repo,
        clock=_CLOCK, budget_overrides={"synthesis_shard_input_tokens": 1}, **kwargs,
    )


@pytest.mark.durability
def test_structuring_sees_registry_definitions_and_decides_a_registry_merge(tmp_path):
    root, repo = _setup_two_chapters(tmp_path)
    _registry_concept(root)
    _enable(root)
    embedder = BagOfWordsEmbedder()
    _backfill(root, embedder, ("concept/definition",))

    def decide(context, ids):
        return [RegistryConceptMerge(
            client_item_id=ids[0], registry_concept_id=context.registry_concept_details[0]["id"],
            rationale="the same idea: a matrix equal to its transpose",
        )]

    client = RegistryStructuringClient(decide)
    result = _synthesize(root, repo, client, apply=True, embedding_client_factory=lambda: embedder)

    context = client.structuring_contexts[0]
    assert context.registry_concepts == [REGISTRY_ID]  # ids, as before
    assert context.registry_concept_details == [{
        "id": REGISTRY_ID, "title": "Symmetric matrix", "type": "concept", "aliases": [],
        "description": "A square matrix equal to its own transpose.",
    }]
    assert {n["client_item_id"] for n in context.registry_nominations} == {
        c["client_item_id"] for c in context.concepts
    }
    # The candidate folded into the registry concept: no new concept row, and
    # every learning object anchors to the registry concept.
    assert "concept" not in result.item_counts
    vault = load_vault(root)
    assert set(vault.concepts) == {REGISTRY_ID}
    assert {lo.concept for lo in vault.learning_objects.values()} == {REGISTRY_ID}
    run = repo.synthesis_run(result.synthesis_run_id)
    assert run["actual_usage"]["registry_merges"] == 1
    assert run["coverage_decisions"]["graph_nomination"]["summary"]["status"] == "active"
    [verdict] = _ledger(repo)
    assert (verdict["judge"], verdict["verdict"], verdict["right_id"]) == ("llm", "same", REGISTRY_ID)
    assert verdict["prompt_version"] == CONCEPT_GRAPH_REGISTRY_PROMPT_VERSION
    assert verdict["left_kind"] == "concept_candidate"
    assert json.loads(verdict["rationale"])["applied"] is True


def test_nominations_alone_never_merge(tmp_path):
    """R1: a nominated registry concept stays separate unless the model decides."""

    root, repo = _setup_two_chapters(tmp_path)
    _registry_concept(root)
    _enable(root)
    embedder = BagOfWordsEmbedder()
    _backfill(root, embedder, ("concept/definition",))
    client = RegistryStructuringClient(decide=None)
    result = _synthesize(root, repo, client, embedding_client_factory=lambda: embedder)
    assert client.structuring_contexts[0].registry_concept_details  # it was nominated
    assert result.item_counts["concept"] == 1  # the candidates merged with each other only
    assert _ledger(repo) == []


def test_guarded_registry_merge_is_ledgered_but_not_applied(tmp_path):
    root, repo = _setup_two_chapters(tmp_path)
    _registry_concept(root, type_="procedure")
    _enable(root)
    embedder = BagOfWordsEmbedder()
    _backfill(root, embedder, ("concept/definition",))

    def decide(context, ids):
        return [
            RegistryConceptMerge(client_item_id=ids[0], registry_concept_id=REGISTRY_ID, rationale="same"),
            RegistryConceptMerge(client_item_id="ghost", registry_concept_id="no_such_concept"),
            RegistryConceptMerge(client_item_id="ghost", registry_concept_id=REGISTRY_ID),
            RegistryConceptMerge(client_item_id=ids[0], registry_concept_id="no_such_concept"),
        ]

    result = _synthesize(root, repo, RegistryStructuringClient(decide), embedding_client_factory=lambda: embedder)
    assert result.item_counts["concept"] == 1
    refused = [json.loads(v["rationale"]) for v in _ledger(repo)]
    assert sorted((r["applied"], r["refused"]) for r in refused) == [
        (False, "type_mismatch"), (False, "unknown_registry_concept"),
    ]


def test_kill_switch_restores_the_pre_t5_request(tmp_path):
    root, repo = _setup_two_chapters(tmp_path)
    _registry_concept(root)
    _enable(root, nominations=False)
    _backfill(root, BagOfWordsEmbedder(), ("concept/definition",))
    factory = ExplodingFactory()
    client = RegistryStructuringClient(decide=None)
    result = _synthesize(root, repo, client, embedding_client_factory=factory)
    assert factory.calls == 0
    context = client.structuring_contexts[0]
    assert context.registry_concept_details == [] and context.registry_nominations == []
    run = repo.synthesis_run(result.synthesis_run_id)
    assert "graph_nomination" not in run["coverage_decisions"]
    assert "registry_merges" not in run["actual_usage"]
    # The manifest scope is the brief's (here none), exactly as before T5.
    assert repo.synthesis_manifest_by_hash(result.manifest_hash)["scope"] is None
    # Byte-identical prompt to the pre-T5 contract when there are no nominations.
    legacy = {key: value for key, value in asdict(context).items()
              if key not in {"registry_concept_details", "registry_nominations"}}
    assert concept_graph_structuring_prompt(context) == render_structured_prompt(
        "learnloop concept graph structuring", CONCEPT_GRAPH_STRUCTURING_PROMPT_VERSION,
        {"task": CONCEPT_GRAPH_STRUCTURING_PROMPT, "context": legacy},
    )


def test_unbackfilled_registry_degrades_to_lexical_and_says_so(tmp_path):
    root, repo = _setup_two_chapters(tmp_path)
    _registry_concept(root)
    _enable(root)
    factory = ExplodingFactory()
    client = RegistryStructuringClient(decide=None)
    result = _synthesize(root, repo, client, embedding_client_factory=factory)
    assert factory.calls == 0  # nothing to compare with, so nothing is paid for
    assert client.structuring_contexts[0].registry_concept_details == []
    summary = repo.synthesis_run(result.synthesis_run_id)["coverage_decisions"]["graph_nomination"]["summary"]
    assert summary["status"] == "lexical_only"
    assert summary["indexes"]["concept/definition"] == "index_incomplete"


def test_revalidation_reuses_paid_vectors_and_makes_no_embedding_call(tmp_path, monkeypatch):
    root, repo = _setup(tmp_path)
    # A registered facet so the mint shadow has a complete index to compare with.
    upsert_facet(root, {
        "id": "facet_elimination", "kind": "procedure_contract",
        "claim": "Gaussian elimination reaches row echelon form",
        "instructional_repairs": ["practise one pivot at a time"],
    }, clock=_CLOCK)
    _enable(root)
    embedder = BagOfWordsEmbedder()
    _backfill(root, embedder, ("facet/definition",))
    client = FakeSynthesisClient()

    def explode(self, batch, rows):
        raise RuntimeError("disk full")

    monkeypatch.setattr(Repository, "persist_proposal_batch", explode)
    with pytest.raises(RuntimeError, match="disk full"):
        create_study_map(root, "set_la", client=client, brief={"depth": "intro"},
                         repository=repo, clock=_CLOCK, embedding_client_factory=lambda: embedder)
    monkeypatch.undo()
    with repo.connection() as connection:
        run_id = connection.execute(
            "SELECT id FROM synthesis_runs ORDER BY created_at DESC, id DESC LIMIT 1"
        ).fetchone()["id"]
    paid = len(embedder.calls)
    first = repo.synthesis_run(run_id)
    assert paid >= 2  # the backfill, then the candidates' definitions at ingest

    def no_paid_client(*_args, **_kwargs):
        raise AssertionError("revalidation must not resolve a paid client")

    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task", no_paid_client)
    result = revalidate_synthesis_candidate(root, run_id, repository=repo, clock=_CLOCK)
    assert len(embedder.calls) == paid
    record = repo.synthesis_run(run_id)["coverage_decisions"]["graph_nomination"]
    assert record["summary"]["mode"] == "review"
    assert record["summary"]["counts"]["calls"] == 0
    # The candidates' paid definition vectors were found by content.
    assert all(c["embedding_neighbours"] for c in record["candidates"])
    assert first["status"] == "failed"
    assert result.item_counts["facet"] == 2


def test_append_neighbourhood_records_embedding_nominations(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    _enable(root)
    embedder = BagOfWordsEmbedder()
    _backfill(root, embedder, ("facet/definition", "concept/definition"))
    client = FakeAppendClient()
    result = append_source(root, "set_la", client=client, new_revision_ids=["rev_alt"],
                           repository=repo, clock=_CLOCK, embedding_client_factory=lambda: embedder)
    reasons = result.neighborhood["match_reasons"]
    assert any(r["kind"] == "embedding" for rs in reasons.values() for r in rs)
    assert result.neighborhood["nomination"]["status"] == "active"
    run = repo.synthesis_run(result.synthesis_run_id)
    assert run["coverage_decisions"]["graph_nomination"]["summary"]["mode"] == "ingest"
    # The new claim was embedded once, under the nominator's receipts.
    with repo.connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM model_call_receipts WHERE owner_kind='graph_nomination'"
        ).fetchone()[0] >= 1


# --- Codex review regressions (cache identity, ledger durability) -----------


def _set_nominations(root: Path, enabled: bool) -> None:
    path = root / "learnloop.toml"
    text = path.read_text(encoding="utf-8")
    old, new = (("enabled = false\ntop_k", "enabled = true\ntop_k") if enabled
                else ("enabled = true\ntop_k", "enabled = false\ntop_k"))
    assert old in text
    path.write_text(text.replace(old, new), encoding="utf-8")


def _merge_into_registry(context, ids):
    return [RegistryConceptMerge(
        client_item_id=ids[0], registry_concept_id=REGISTRY_ID,
        rationale="the same idea: a matrix equal to its transpose",
    )]


def test_kill_switch_never_reuses_a_nominated_bootstrap(tmp_path):
    """F1: an unapplied run that merged into the registry is not reused (or
    applied) once ``graph_nomination.enabled`` is turned off."""

    root, repo = _setup_two_chapters(tmp_path)
    _registry_concept(root)
    _enable(root)
    embedder = BagOfWordsEmbedder()
    _backfill(root, embedder, ("concept/definition",))
    first = _synthesize(root, repo, RegistryStructuringClient(_merge_into_registry),
                        embedding_client_factory=lambda: embedder)
    assert repo.synthesis_run(first.synthesis_run_id)["actual_usage"]["registry_merges"] == 1

    _set_nominations(root, False)
    factory = ExplodingFactory()
    client = RegistryStructuringClient(_merge_into_registry)
    second = _synthesize(root, repo, client, apply=True, embedding_client_factory=factory)
    assert second.reused is False and second.manifest_hash != first.manifest_hash
    # Shards are checkpointed (nominations never reach them); the structuring
    # pass ran again, lexical-only.
    assert client.structuring_contexts[0].registry_concept_details == []
    assert factory.calls == 0
    # The lexical-only run kept its own concept: no registry merge was applied.
    assert len(load_vault(root).concepts) == 2


def test_kill_switch_never_reuses_a_nominated_bootstrap_cached_before_the_fix(tmp_path, monkeypatch):
    """F1 (re-review), upgrade: a nominated, unapplied run cached by the T5
    code before nomination identity entered the manifest has the kill-switch
    manifest hash. Its recorded provenance, not its hash, keeps it from being
    reused or applied once ``graph_nomination.enabled`` is off; the
    lexical-only rerun is then the cache."""

    import learnloop.content.proposals.patches as patches
    import learnloop.content.synthesis.source_set_synthesis as synthesis

    root, repo = _setup_two_chapters(tmp_path)
    _registry_concept(root)
    _enable(root)
    embedder = BagOfWordsEmbedder()
    _backfill(root, embedder, ("concept/definition",))
    real_build_manifest = synthesis.build_manifest

    def pre_fix_manifest(*args, scope=None, **kwargs):
        # The pre-fix manifest: the brief's scope, nominations on or off.
        if isinstance(scope, dict) and "graph_nomination" in scope:
            scope = scope["brief_scope"]
        return real_build_manifest(*args, scope=scope, **kwargs)

    with monkeypatch.context() as legacy_code:
        legacy_code.setattr(synthesis, "build_manifest", pre_fix_manifest)
        legacy = _synthesize(root, repo, RegistryStructuringClient(_merge_into_registry),
                             embedding_client_factory=lambda: embedder)
    legacy_run = repo.synthesis_run(legacy.synthesis_run_id)
    assert legacy_run["actual_usage"]["registry_merges"] == 1
    assert "graph_nomination" in legacy_run["coverage_decisions"]

    applied: list[str] = []
    real_apply = patches.apply_accepted_items

    def recording_apply(root_, proposal_id, **kwargs):
        applied.append(proposal_id)
        return real_apply(root_, proposal_id, **kwargs)

    monkeypatch.setattr(patches, "apply_accepted_items", recording_apply)
    _set_nominations(root, False)
    factory = ExplodingFactory()
    client = RegistryStructuringClient(_merge_into_registry)
    upgraded = _synthesize(root, repo, client, embedding_client_factory=factory)
    # The kill switch keeps the pre-T5 hash, which the legacy run shares ...
    assert upgraded.manifest_hash == legacy.manifest_hash
    # ... but a nominated run is never reused with the switch off: the
    # structuring pass ran again, lexical-only.
    assert upgraded.reused is False and upgraded.proposal_id != legacy.proposal_id
    assert client.structuring_contexts[0].registry_concept_details == []
    assert factory.calls == 0

    # The lexical-only rerun is the cache now (zero model and embedding
    # calls), and it is what apply accepts; the legacy proposal never is.
    repeat_client = RegistryStructuringClient()
    repeat = _synthesize(root, repo, repeat_client, apply=True, embedding_client_factory=ExplodingFactory())
    assert repeat.reused is True and repeat.proposal_id == upgraded.proposal_id
    assert repeat_client.calls == []
    assert applied == [upgraded.proposal_id]
    assert len(load_vault(root).concepts) == 2  # no registry merge was applied


def test_enabling_nominations_or_completing_the_index_is_a_new_bootstrap(tmp_path):
    """F1, other direction: a lexical-only result is not reused once nominations
    could act (switch turned on, then the index completed)."""

    root, repo = _setup_two_chapters(tmp_path)
    _registry_concept(root)
    _enable(root, nominations=False)
    first = _synthesize(root, repo, RegistryStructuringClient(), embedding_client_factory=ExplodingFactory())

    _set_nominations(root, True)
    incomplete_client = RegistryStructuringClient()
    incomplete = _synthesize(root, repo, incomplete_client, embedding_client_factory=ExplodingFactory())
    assert incomplete.reused is False and incomplete.manifest_hash != first.manifest_hash
    assert incomplete_client.structuring_contexts[0].registry_concept_details == []  # index incomplete

    embedder = BagOfWordsEmbedder()
    _backfill(root, embedder, ("concept/definition",))
    client = RegistryStructuringClient()
    third = _synthesize(root, repo, client, embedding_client_factory=lambda: embedder)
    assert third.reused is False
    assert client.structuring_contexts[0].registry_concept_details  # nominated now


def test_registry_definition_change_is_a_new_bootstrap_and_repeats_reuse(tmp_path):
    """F1: identity covers the nominated registry's definitions; an identical
    repeat still reuses with zero model and embedding calls."""

    root, repo = _setup_two_chapters(tmp_path)
    _registry_concept(root)
    _enable(root)
    embedder = BagOfWordsEmbedder()
    _backfill(root, embedder, ("concept/definition",))
    first = _synthesize(root, repo, RegistryStructuringClient(), embedding_client_factory=lambda: embedder)
    paid = len(embedder.calls)

    again_client = RegistryStructuringClient()
    again = _synthesize(root, repo, again_client, embedding_client_factory=lambda: embedder)
    assert again.reused is True and again.manifest_hash == first.manifest_hash
    assert again_client.calls == [] and len(embedder.calls) == paid

    upsert_concept(root, REGISTRY_ID, {
        "title": "Symmetric matrix", "type": "concept",
        "description": "A square matrix whose entries mirror across the main diagonal.",
        "aliases": [], "tags": [],
    }, clock=_CLOCK)
    _backfill(root, embedder, ("concept/definition",))
    changed_client = RegistryStructuringClient()
    changed = _synthesize(root, repo, changed_client, embedding_client_factory=lambda: embedder)
    assert changed.reused is False
    assert changed_client.structuring_contexts[0].registry_concept_details[0]["description"].startswith(
        "A square matrix whose entries mirror"
    )


@pytest.mark.parametrize("nominations", [False, True])
def test_identical_append_reuses_its_completed_run(tmp_path, nominations):
    """F2: embedding usage counters are not manifest identity, so a repeat of
    an append that changed nothing reuses it with zero model or embedding calls."""

    root, repo = _bootstrap_and_add(tmp_path)
    _enable(root, nominations=nominations)
    embedder = BagOfWordsEmbedder()
    _backfill(root, embedder, ("facet/definition", "concept/definition"))
    first = append_source(root, "set_la", client=FakeAppendClient(), new_revision_ids=["rev_alt"],
                          repository=repo, clock=_CLOCK, auto_apply=False,
                          embedding_client_factory=lambda: embedder)
    if nominations:
        assert first.neighborhood["nomination"]["status"] == "active"
        assert len(embedder.calls) > 1  # the backfill, then the new claims
    paid = len(embedder.calls)
    client = FakeAppendClient()
    second = append_source(root, "set_la", client=client, new_revision_ids=["rev_alt"],
                           repository=repo, clock=_CLOCK, auto_apply=False,
                           embedding_client_factory=lambda: embedder)
    assert second.reused is True and second.manifest_hash == first.manifest_hash
    assert second.proposal_id == first.proposal_id
    assert client.calls == [] and len(embedder.calls) == paid


@pytest.mark.parametrize("fail_on", [1, 2])
def test_registry_merge_is_declined_when_its_verdict_cannot_be_ledgered(tmp_path, monkeypatch, fail_on):
    """F3: a registry merge whose judgment did not reach judgment_ledger never
    reaches the proposal; the verdicts are one transaction (a failure on the
    second rolls back the first) and the declined decisions stay on the run."""

    import sqlite3

    from learnloop.db.stores import judgments

    root, repo = _setup_two_chapters(tmp_path)
    _registry_concept(root)
    _enable(root)
    embedder = BagOfWordsEmbedder()
    _backfill(root, embedder, ("concept/definition",))
    real_append = judgments.append_judgment
    attempts: list[int] = []

    def locked_on_nth(*args, **kwargs):
        attempts.append(1)
        if len(attempts) == fail_on:
            raise sqlite3.OperationalError("database is locked")
        return real_append(*args, **kwargs)

    def decide(context, ids):
        # A merge and a second (guard-refused) decision about the same candidate.
        return _merge_into_registry(context, ids) * 2

    monkeypatch.setattr(judgments, "append_judgment", locked_on_nth)
    result = _synthesize(root, repo, RegistryStructuringClient(decide), apply=True,
                         embedding_client_factory=lambda: embedder)
    assert len(attempts) == fail_on
    assert _ledger(repo) == []
    usage = repo.synthesis_run(result.synthesis_run_id)["actual_usage"]
    assert usage["registry_merges"] == 0
    assert usage["registry_merges_declined"] == "ledger_write_failed:OperationalError"
    assert [(d["registry_concept_id"], d["refused"]) for d in usage["registry_merge_decisions_unrecorded"]] == [
        (REGISTRY_ID, None), (REGISTRY_ID, "duplicate_decision"),
    ]
    assert result.item_counts["concept"] == 1
    vault = load_vault(root)
    assert len(vault.concepts) == 2 and REGISTRY_ID in vault.concepts
    assert REGISTRY_ID not in {lo.concept for lo in vault.learning_objects.values()}


def test_backfill_after_apply_reuses_the_vectors_paid_at_ingest(tmp_path):
    """F5 end to end: synthesis embeds each candidate concept under its client
    id; apply gives it a canonical id; the backfill then buys nothing for a
    definition apply left unchanged."""

    class KeepEveryCandidate(RegistryStructuringClient):
        def run_concept_graph_structuring(self, context):
            self.structuring_contexts.append(context)
            return ConceptGraphStructuringWithRegistry()

    root, repo = _setup_two_chapters(tmp_path)
    _registry_concept(root)
    _enable(root)
    embedder = BagOfWordsEmbedder()
    _backfill(root, embedder, ("concept/definition",))
    _synthesize(root, repo, KeepEveryCandidate(), apply=True,
                embedding_client_factory=lambda: embedder)
    minted = set(load_vault(root).concepts) - {REGISTRY_ID}
    assert len(minted) == 2  # both candidates, under canonical ids
    paid = len(embedder.calls)
    report = backfill_embeddings(
        load_vault(root), caps=SpendCaps(max_candidates=1000, max_total_tokens=10**7),
        recipes=("concept/definition",), client_factory=ExplodingFactory(),
    )
    assert report["status"] == "complete", report
    assert (report["pending"], report["reused_by_content"]) == (0, len(minted))
    assert len(embedder.calls) == paid
    with repo.connection() as connection:
        rows = {row[0] for row in connection.execute(
            "SELECT record_id FROM embedding_vectors WHERE record_kind='concept'"
        )}
    assert minted <= rows  # canonical identity rows for identity-keyed consumers


_COUNTED_TABLES = ("synthesis_manifests", "synthesis_runs", "agent_runs", "embedding_vectors",
                   "model_call_receipts", "judgment_ledger")


def _row_counts(repo: Repository) -> dict[str, int]:
    with repo.connection() as connection:
        return {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in _COUNTED_TABLES}


def _no_paid_client(monkeypatch) -> None:
    def explode(*_args, **_kwargs):
        raise AssertionError("a dry run must not resolve a paid client")

    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task", explode)


def _cap_bound(root: Path) -> float:
    from learnloop.ai.embedding import EMBEDDING_PRICES_PER_MILLION

    config = load_vault(root).config
    price = EMBEDDING_PRICES_PER_MILLION[config.embedding.model]
    caps = config.graph_nomination
    return min(caps.max_query_cost_usd, caps.max_query_tokens * price / 1_000_000)


def test_bootstrap_dry_run_plans_ingest_embedding_without_a_client(tmp_path, monkeypatch):
    """F6: a nonmutating plan of a synthesis run's embedding spend: candidate
    text is generated by the run, so its bound is the per-run cap."""

    from learnloop.content.synthesis.source_set_synthesis import plan_study_map_embedding

    root, repo = _setup_two_chapters(tmp_path)
    _registry_concept(root)
    _enable(root)
    embedder = BagOfWordsEmbedder()
    _backfill(root, embedder, ("concept/definition",))
    before = _row_counts(repo)
    with monkeypatch.context() as patched:
        _no_paid_client(patched)
        plan = plan_study_map_embedding(root, "set_la")
    assert _row_counts(repo) == before
    assert (plan["dry_run"], plan["entry"], plan["status"]) == (True, "bootstrap", "may_embed")
    assert plan["indexes"]["concept/definition"] == "complete"
    assert plan["known_queries"]["texts"] == 0
    assert plan["generated_text"]["paid_when"]
    assert plan["max_estimated_usd"] == pytest.approx(_cap_bound(root))

    result = _synthesize(root, repo, RegistryStructuringClient(), embedding_client_factory=lambda: embedder)
    charged = repo.synthesis_run(result.synthesis_run_id)["coverage_decisions"]["graph_nomination"]["summary"]["charged"]
    assert 0 < charged["estimated_usd"] <= plan["max_estimated_usd"]

    _set_nominations(root, False)
    off = plan_study_map_embedding(root, "set_la")
    assert (off["status"], off["max_estimated_usd"]) == ("off", 0.0)


def test_append_dry_run_estimates_known_queries_without_a_client(tmp_path, monkeypatch):
    """F6: the append plan prices the new inventory's queries exactly (what is
    not stored yet) and bounds the generated candidates by the per-run cap."""

    from learnloop.content.synthesis.source_append import plan_append_embedding

    root, repo = _bootstrap_and_add(tmp_path)
    _enable(root)
    embedder = BagOfWordsEmbedder()
    _backfill(root, embedder, ("facet/definition", "concept/definition"))
    before = _row_counts(repo)
    with monkeypatch.context() as patched:
        _no_paid_client(patched)
        plan = plan_append_embedding(root, "set_la", new_revision_ids=["rev_alt"])
    assert _row_counts(repo) == before
    assert (plan["entry"], plan["status"]) == ("append", "may_embed")
    known = plan["known_queries"]
    assert known["texts"] >= 1 and known["pending"] == known["texts"] and known["stored"] == 0
    assert known["estimated_usd"] > 0 and known["exceeds_caps"] is False
    assert plan["max_estimated_usd"] == pytest.approx(_cap_bound(root))
    config_path = root / "learnloop.toml"
    config_text = config_path.read_text(encoding="utf-8")
    config_path.write_text(config_text.replace("top_k = 2", "top_k = 2\nmax_query_tokens = 1"), encoding="utf-8")
    capped = plan_append_embedding(root, "set_la", new_revision_ids=["rev_alt"])
    assert capped["known_queries"]["exceeds_caps"] is True
    config_path.write_text(config_text, encoding="utf-8")

    paid = len(embedder.calls)
    append_source(root, "set_la", client=FakeAppendClient(), new_revision_ids=["rev_alt"],
                  repository=repo, clock=_CLOCK, auto_apply=False,
                  embedding_client_factory=lambda: embedder)
    # The neighbourhood's call embedded exactly the planned known queries.
    assert len(embedder.calls[paid][0]) == known["pending"]
    again = plan_append_embedding(root, "set_la", new_revision_ids=["rev_alt"])
    assert (again["known_queries"]["stored"], again["known_queries"]["pending"]) == (known["texts"], 0)


def test_synthesize_dry_run_cli_prints_the_plan_and_resolves_no_provider(tmp_path, monkeypatch):
    import learnloop.cli as cli_module
    from typer.testing import CliRunner

    from learnloop.cli import app

    root, _repo = _bootstrap_and_add(tmp_path)
    _enable(root)

    def no_provider(*_args, **_kwargs):
        raise AssertionError("--dry-run must not resolve the synthesis provider")

    monkeypatch.setattr(cli_module, "_ready_provider_for_task", no_provider)
    _no_paid_client(monkeypatch)
    result = CliRunner().invoke(app, ["synthesize", "set_la", "--dry-run", "--json", "--vault", str(root)])
    assert result.exit_code == 0, result.output
    plan = json.loads(result.output)["dryRun"]
    assert plan["entry"] == "append" and plan["dry_run"] is True
    append_text = CliRunner().invoke(app, ["synthesize", "set_la", "--dry-run", "--vault", str(root)])
    assert append_text.exit_code == 0, append_text.output
    assert f"to embed in {plan['known_queries']['estimated_calls']} calls" in append_text.output
    text = CliRunner().invoke(app, ["synthesize", "set_la", "--dry-run", "--mode", "bootstrap",
                                    "--vault", str(root)])
    assert text.exit_code == 0, text.output
    assert "embedding" in text.output and "$" in text.output
