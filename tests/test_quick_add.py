"""Quick add (spec_source_ingestion_v2 §1, §14).

Service-level: one URL through the Quick-add batch machinery with canned codex
reaches a study-map proposal with EXACTLY ONE consent/confirmation checkpoint in
the flow's state machine, and Quick-add batches take queue priority over bulk
batches. Deterministic — no network, no real LLM.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ingest.resolution import resolve_source
from learnloop.services.ingest_runner import RunnerServices
from learnloop.services.quick_add import (
    QuickAddPlan,
    enqueue_quick_add,
    plan_quick_add,
    select_relevant_units,
)
from learnloop.services.source_outline import build_source_outline
from learnloop.vault.loader import add_subject, init_vault, load_vault
from learnloop.vault.paths import VaultPaths
from learnloop_sidecar.ingest_jobs import QUICK_ADD_PRIORITY, DurableIngestJobs

from tests.helpers import set_algorithm_version
from tests.test_source_inventory import FakeInventoryClient, _block, _ir, _persist
from tests.test_source_set_synthesis import FakeSynthesisClient

_CLOCK = FrozenClock(datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC))


def _register_source(repo: Repository, *, source_id: str, revision_id: str, category: str, uri: str) -> None:
    now = _CLOCK.now().isoformat()
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, current_revision_id, created_at, updated_at) VALUES (?,?,?,?,?,?)",
            (source_id, category, uri, revision_id, now, now),
        )
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            (revision_id, source_id, f"sha256:{source_id}", uri, now),
        )
        connection.commit()


def _setup(tmp_path: Path):
    """A vault with one imported textbook (completed extraction, no inventories yet)
    and the runner services stubbed with canned inventory + synthesis clients."""

    root = tmp_path / "vault"
    init_vault(root, clock=_CLOCK)
    add_subject(root, "linear-algebra", "Linear Algebra", clock=_CLOCK)
    set_algorithm_version(VaultPaths(root, load_vault(root).config), "mvp-0.7")
    repo = Repository(root / "state.sqlite")

    pdf = tmp_path / "symmetry.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    resolved = resolve_source(str(pdf))
    _register_source(repo, source_id="src_text", revision_id="rev_text", category=resolved.category, uri=resolved.source)

    ir = _ir([
        ("chapter_symmetry", "Symmetric matrices",
         [_block("s1", "A real square matrix is symmetric when A^T = A."),
          _block("s2", "The spectral theorem applies to real symmetric matrices.")],
         "sha256:sym", 5),
    ])
    _persist(repo, ir, revision_id="rev_text", extraction_id="ext_text")

    services = RunnerServices(
        inventory_client_factory=lambda ctx: FakeInventoryClient(),
        synthesis_client_factory=lambda ctx: FakeSynthesisClient(),
    )
    jobs = DurableIngestJobs()
    jobs.bind(repo, root, background=False, clock=_CLOCK, services=services)
    return root, repo, jobs, str(pdf)


# --------------------------------------------------------------------------
# Deterministic ToC-guided selection (§1)
# --------------------------------------------------------------------------


def test_select_relevant_units_whole_source_when_small(tmp_path):
    root, repo, _jobs, _src = _setup(tmp_path)
    outline = build_source_outline(repo, "ext_text")
    unit_ids, labels, tokens, whole = select_relevant_units(outline, keywords=set(), cap_tokens=1_000_000)
    assert whole is True
    assert unit_ids == ["chapter_symmetry"]
    assert tokens == outline.approx_tokens


def test_select_relevant_units_keyword_subset_under_cap():
    class _Unit:
        def __init__(self, unit_id, label, approx_tokens):
            self.unit_id, self.label, self.approx_tokens = unit_id, label, approx_tokens

    class _Outline:
        units = [
            _Unit("u1", "Introduction to widgets", 30000),
            _Unit("u2", "Advanced symmetry", 30000),
            _Unit("u3", "Appendix of tables", 30000),
        ]

    unit_ids, labels, tokens, whole = select_relevant_units(
        _Outline(), keywords={"symmetry"}, cap_tokens=40000
    )
    assert whole is False
    assert unit_ids == ["u2"]  # only the keyword match fits under the cap
    assert tokens == 30000


# --------------------------------------------------------------------------
# §14 named row: one URL -> one confirmation -> study map
# --------------------------------------------------------------------------


def test_quick_add_one_url_one_confirmation_to_study_map(tmp_path):
    root, repo, jobs, source = _setup(tmp_path)

    # Step 1 (pure): the plan IS the single confirmation payload — no writes yet.
    plan = plan_quick_add(repo, load_vault(root).config, load_vault(root), source, subject_id="linear-algebra")
    assert isinstance(plan, QuickAddPlan)
    assert plan.extraction_id == "ext_text"
    assert plan.suggested_role == "primary_textbook"
    assert plan.role_ambiguous is False
    assert plan.selected_unit_ids == ["chapter_symmetry"]

    # The state machine exposes EXACTLY ONE confirmation checkpoint.
    plan_dict = plan.as_dict()
    assert plan_dict["confirmation"]["id"] == "quick_add_confirm"
    checkpoints = [key for key in plan_dict if key == "confirmation"]
    assert len(checkpoints) == 1
    assert plan.confirmation()["requires_external_ai"] is True
    assert plan.confirmation()["estimated_input_tokens"] > 0

    # No batch, source set, inventory, or proposal exists before confirmation.
    assert repo.list_ingest_batches() == []
    assert load_vault(root).source_sets == []

    # Step 2 (post-confirmation): the ONE confirmation gate is crossed here.
    result = enqueue_quick_add(
        load_vault(root), jobs, plan, output_budget_tokens=12_000
    )  # background=False drains inline
    batch = jobs.get_batch(result["batch_id"])
    queued_jobs = jobs._require_runner().repo.ingest_jobs_for_batch(result["batch_id"])
    inventory_job = next(job for job in queued_jobs if job["job_type"] == "inventory")
    assert inventory_job["payload"]["output_budget_tokens"] == 12_000

    # v2 machinery is exercised: extraction run, inventories, synthesis, gates.
    assert batch["status"] == "completed"
    job_types = {job["job_type"]: job for job in batch["jobs"]}
    assert set(job_types) == {"inventory", "bootstrap_synthesis"}
    assert job_types["inventory"]["status"] == "completed"
    synth = job_types["bootstrap_synthesis"]
    assert synth["status"] == "completed"

    # The one confirmation produces a directly usable study map; the proposal
    # remains as the durable audit/review record.
    study_map = synth["result"]
    assert study_map["proposal_id"] is not None
    assert study_map["applied"] is True
    assert study_map["item_counts"]["facet"] >= 1
    assert not any(d["severity"] == "hard_fail" for d in study_map["gate_diagnostics"])

    # The source set was created with exactly the confirmed scope.
    source_set = next(s for s in load_vault(root).source_sets if s.id == plan.source_set_id)
    assert [m.default_role for m in source_set.members] == ["primary_textbook"]


# --------------------------------------------------------------------------
# §14 named row: Quick-add batches take queue priority over bulk batches
# --------------------------------------------------------------------------


def test_quick_add_batches_take_queue_priority(tmp_path):
    root, repo, jobs, _source = _setup(tmp_path)
    runner = jobs._require_runner()

    # A bulk import batch is enqueued FIRST (older created_at, default priority 0).
    from learnloop.services.ingest_runner import JobSpec

    bulk_id = runner.enqueue_batch("import", [JobSpec("import", {"source": "https://example.com/a"})], priority=0)
    # A Quick-add build batch is enqueued SECOND but at QUICK_ADD_PRIORITY.
    quick_id = runner.enqueue_batch(
        "bootstrap_synthesis",
        [JobSpec("inventory", {"extraction_id": "ext_text", "units": [{"unit_id": "chapter_symmetry", "role": "primary_textbook"}]})],
        priority=QUICK_ADD_PRIORITY,
    )

    # The drain claims the higher-priority Quick-add job first, despite being
    # enqueued later than the bulk batch.
    claimed = repo.claim_next_ingest_job(
        worker_id="w-test",
        now_iso=_CLOCK.now().isoformat(),
        lease_cutoff_iso="1970-01-01T00:00:00+00:00",
    )
    assert claimed is not None
    assert claimed["batch_id"] == quick_id
    assert claimed["batch_id"] != bulk_id
