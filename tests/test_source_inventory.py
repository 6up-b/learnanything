"""ING M4 — source sets, role-specific inventories, exam profiles, authority, and
coverage (spec_source_ingestion_v2 §4/§7/§9.3, §14 rows).

No LLM: the codex `run_source_unit_inventory` method is stubbed with canned
SourceUnitInventory JSON (house fake-client pattern). Ids are deterministic and
cache identity is exercised directly.
"""

from __future__ import annotations

import pytest

from learnloop.content.synthesis.ai_contracts import (
    InventoryAssessmentSignal,
    InventoryClaim,
    InventoryProcedureSignal,
    SourceUnitInventory,
)
from learnloop.content.synthesis.exam_profile import ExamUnitEntry, aggregate_exam_profile, exam_family_key
from learnloop.content.sources.role_authority import (
    ManualAuthorityGrant,
    can_authorize_semantic,
    role_authority,
)
from learnloop.content.synthesis.source_unit_inventory import (
    INVENTORY_SCHEMA_VERSION,
    InventoryValidationError,
    build_inventory_windows,
    profile_satisfies,
    run_unit_inventory,
    validate_inventory,
)
from tests.source_inventory_helpers import (
    FakeInventoryClient,
    _CLOCK,
    _block,
    _ir,
    _persist,
    _register_revision,
    _repo,
)

# ---------------------------------------------------------------------------
# §14 role-aware inventory
# ---------------------------------------------------------------------------


def test_role_aware_inventory_profiles(tmp_path):
    repo = _repo(tmp_path)
    _register_revision(repo)
    ir = _ir([("u1", "Eigenvalues", [_block("s1", "An eigenvector of A is a nonzero vector.")], "sha256:h1", 1)])
    _persist(repo, ir, revision_id="rev1", extraction_id="ext1")
    client = FakeInventoryClient()

    # Explanatory unit (semantic profile) emits conditioned claims + procedure signals.
    explanatory = run_unit_inventory(repo, "ext1", "u1", role="primary_textbook", profile="semantic", client=client, clock=_CLOCK)
    assert explanatory.inventory.claims and explanatory.inventory.claims[0].preconditions
    assert explanatory.inventory.procedure_signals
    assert not explanatory.inventory.assessment_signals

    # Problem set (practice profile) emits task/method signals.
    problem = run_unit_inventory(repo, "ext1", "u1", role="problem_set", profile="practice", client=client, clock=_CLOCK)
    assert problem.inventory.practice_signals and problem.inventory.practice_signals[0].task_family
    # No independent semantic authority: no canonical claims minted.
    assert not problem.inventory.claims

    # Exam (assessment profile) emits held-out assessment signals and NEVER claims.
    exam = run_unit_inventory(repo, "ext1", "u1", role="exam", profile="assessment", client=client, clock=_CLOCK)
    assert exam.inventory.assessment_signals and exam.inventory.assessment_signals[0].held_out
    assert not exam.inventory.claims  # exam text never promoted to a canonical claim (§4.2)


def test_inventory_can_disable_the_output_ceiling(tmp_path):
    repo = _repo(tmp_path)
    _register_revision(repo)
    _persist(
        repo,
        _ir([("u1", "Unit", [_block("s1", "An eigenvector definition.")], "sha256:u1", 1)]),
        revision_id="rev1",
        extraction_id="ext1",
    )
    client = FakeInventoryClient()

    with pytest.raises(InventoryValidationError, match="configured token budget"):
        run_unit_inventory(
            repo,
            "ext1",
            "u1",
            role="primary_textbook",
            client=client,
            output_budget_tokens=1,
            clock=_CLOCK,
        )
    assert len(client.calls) == 1

    result = run_unit_inventory(
        repo,
        "ext1",
        "u1",
        role="primary_textbook",
        client=client,
        output_budget_tokens=None,
        clock=_CLOCK,
    )
    assert result.cache_hit is False
    assert result.usage["output_tokens_estimate"] > 1
    # The over-budget window validated and was paid for, so the retry reuses it.
    assert len(client.calls) == 1
    assert result.usage["reused_windows"] == 1


def test_deterministic_inventory_ids_stable(tmp_path):
    repo = _repo(tmp_path)
    _register_revision(repo)
    ir = _ir([("u1", "Eigen", [_block("s1", "An eigenvector of A is a nonzero vector.")], "sha256:h1", 1)])
    _persist(repo, ir, revision_id="rev1", extraction_id="ext1")

    first = run_unit_inventory(repo, "ext1", "u1", role="primary_textbook", client=FakeInventoryClient(), clock=_CLOCK)
    ids = [claim.claim_id for claim in first.inventory.claims]
    assert ids and all(cid.startswith("u1|w0|") for cid in ids)
    # A fresh run over the same semantic view is a cache hit returning identical ids.
    reuse = run_unit_inventory(repo, "ext1", "u1", role="primary_textbook", client=FakeInventoryClient(), clock=_CLOCK)
    assert reuse.cache_hit
    assert [claim.claim_id for claim in reuse.inventory.claims] == ids


# ---------------------------------------------------------------------------
# §14 unit inventory caching
# ---------------------------------------------------------------------------


def test_unit_inventory_cache_reuse_across_collections(tmp_path):
    repo = _repo(tmp_path)
    _register_revision(repo)
    ir = _ir(
        [
            ("u1", "Ch1", [_block("s1", "Chapter one prose about eigenvectors.")], "sha256:h1", 1),
            ("u2", "Ch2", [_block("s2", "Chapter two prose about eigenvalues.")], "sha256:h2", 2),
        ]
    )
    _persist(repo, ir, revision_id="rev1", extraction_id="ext1")

    client = FakeInventoryClient()
    # Collection A inventories both units.
    run_unit_inventory(repo, "ext1", "u1", role="primary_textbook", client=client, clock=_CLOCK)
    run_unit_inventory(repo, "ext1", "u1", role="primary_textbook", client=client, clock=_CLOCK)
    calls_after_first = len(client.calls)

    # Collection B (same pinned revision) requests u1 again → zero new calls.
    second = run_unit_inventory(repo, "ext1", "u1", role="primary_textbook", client=client, clock=_CLOCK)
    assert second.cache_hit
    assert len(client.calls) == calls_after_first  # no new tokens spent


def test_changed_page_reinventories_only_that_unit(tmp_path):
    repo = _repo(tmp_path)
    _register_revision(repo)
    ir = _ir(
        [
            ("u1", "Ch1", [_block("s1", "Chapter one prose.")], "sha256:h1", 1),
            ("u2", "Ch2", [_block("s2", "Chapter two prose.")], "sha256:h2", 2),
        ]
    )
    _persist(repo, ir, revision_id="rev1", extraction_id="ext1")
    client = FakeInventoryClient()
    run_unit_inventory(repo, "ext1", "u1", role="reference", client=client, clock=_CLOCK)
    run_unit_inventory(repo, "ext1", "u2", role="reference", client=client, clock=_CLOCK)
    baseline = len(client.calls)

    # A repair extraction over the SAME revision: u2's semantic hash changed, u1's did not.
    repaired = _ir(
        [
            ("u1", "Ch1", [_block("s1", "Chapter one prose.")], "sha256:h1", 1),
            ("u2", "Ch2", [_block("s2", "Chapter two prose, improved OCR.")], "sha256:h2b", 2),
        ]
    )
    _persist(repo, repaired, revision_id="rev1", extraction_id="ext2", config={"repair": True})

    u1_again = run_unit_inventory(repo, "ext2", "u1", role="reference", client=client, clock=_CLOCK)
    assert u1_again.cache_hit
    assert len(client.calls) == baseline  # unchanged unit reused
    rebound = repo.get_unit_inventory(u1_again.inventory_id)
    assert rebound is not None
    assert rebound["extraction_id"] == "ext2"

    u2_again = run_unit_inventory(repo, "ext2", "u2", role="reference", client=client, clock=_CLOCK)
    assert not u2_again.cache_hit
    assert len(client.calls) == baseline + 1  # only the changed unit re-inventoried


def test_semantic_inventory_cache_rebinds_across_revisions(tmp_path):
    repo = _repo(tmp_path)
    _register_revision(repo)
    first_ir = _ir(
        [
            (
                "u1",
                "Ch1",
                [_block("s1", "Chapter one prose about eigenvectors.")],
                "sha256:h1",
                1,
            )
        ]
    )
    _persist(repo, first_ir, revision_id="rev1", extraction_id="ext1")
    client = FakeInventoryClient()
    first = run_unit_inventory(
        repo,
        "ext1",
        "u1",
        role="reference",
        client=client,
        clock=_CLOCK,
    )
    baseline = len(client.calls)

    # The source acquired a new revision and extractor-local span id, but its
    # normalized unit view is unchanged. The semantic artifact is re-anchored and
    # bound to rev2 without another model call.
    now = _CLOCK.now().isoformat()
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, created_at) VALUES (?,?,?,?)",
            ("rev2", "src1", "sha256:def", now),
        )
        connection.commit()
    second_ir = _ir(
        [
            (
                "u1",
                "Ch1",
                [_block("s2", "Chapter one prose about eigenvectors.")],
                "sha256:h1",
                1,
            )
        ]
    )
    _persist(repo, second_ir, revision_id="rev2", extraction_id="ext2")

    rebound = run_unit_inventory(
        repo,
        "ext2",
        "u1",
        role="reference",
        client=client,
        clock=_CLOCK,
    )

    assert rebound.cache_hit
    assert rebound.inventory_id != first.inventory_id
    assert len(client.calls) == baseline
    assert rebound.inventory.concept_mentions[0].span_ids == ["s2"]
    rev2_rows = repo.unit_inventories_for_revision("rev2")
    assert [row["id"] for row in rev2_rows] == [rebound.inventory_id]
    assert rev2_rows[0]["usage"]["calls"] == 0
    assert rev2_rows[0]["usage"]["rebound_from_inventory_id"] == first.inventory_id


def test_composite_inventory_cache_rebinds_all_member_spans_across_revisions(tmp_path):
    repo = _repo(tmp_path)
    _register_revision(repo)
    first_ir = _ir(
        [
            ("u1", "Ch1", [_block("s1", "Eigenvectors scale under A.")], "sha256:h1", 1),
            (
                "u2",
                "Ch2",
                [_block("s2", "Eigenvalues solve the characteristic equation.")],
                "sha256:h2",
                2,
            ),
        ]
    )
    _persist(repo, first_ir, revision_id="rev1", extraction_id="ext1")
    client = FakeInventoryClient()
    first = run_unit_inventory(
        repo,
        "ext1",
        "u1+u2",
        unit_ids=["u1", "u2"],
        role="reference",
        client=client,
        clock=_CLOCK,
    )
    baseline = len(client.calls)

    now = _CLOCK.now().isoformat()
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, created_at) VALUES (?,?,?,?)",
            ("rev2", "src1", "sha256:def", now),
        )
        connection.commit()
    second_ir = _ir(
        [
            ("u1", "Ch1", [_block("s11", "Eigenvectors scale under A.")], "sha256:h1", 1),
            (
                "u2",
                "Ch2",
                [_block("s12", "Eigenvalues solve the characteristic equation.")],
                "sha256:h2",
                2,
            ),
        ]
    )
    _persist(repo, second_ir, revision_id="rev2", extraction_id="ext2")

    rebound = run_unit_inventory(
        repo,
        "ext2",
        "u1+u2",
        unit_ids=["u1", "u2"],
        role="reference",
        client=client,
        clock=_CLOCK,
    )

    assert rebound.cache_hit
    assert rebound.inventory_id != first.inventory_id
    assert len(client.calls) == baseline
    assert rebound.inventory.claims[0].span_ids == ["s11", "s12"]


def test_combined_satisfies_narrower_only_when_schema_allows():
    # §7 deterministic decider.
    assert profile_satisfies("combined", INVENTORY_SCHEMA_VERSION, "semantic")
    assert profile_satisfies("combined", INVENTORY_SCHEMA_VERSION, "assessment")
    assert profile_satisfies("semantic", INVENTORY_SCHEMA_VERSION, "semantic")
    # A narrower stored profile never satisfies a different request.
    assert not profile_satisfies("semantic", INVENTORY_SCHEMA_VERSION, "assessment")
    # An unknown/future schema version's combined guarantees nothing.
    assert not profile_satisfies("combined", 999, "semantic")


def test_combined_inventory_reused_for_semantic_request(tmp_path):
    repo = _repo(tmp_path)
    _register_revision(repo)
    ir = _ir([("u1", "Ch1", [_block("s1", "Chapter one prose about eigenvectors.")], "sha256:h1", 1)])
    _persist(repo, ir, revision_id="rev1", extraction_id="ext1")
    client = FakeInventoryClient()
    # A combined inventory exists (primary_textbook defaults to combined).
    run_unit_inventory(repo, "ext1", "u1", role="primary_textbook", profile="combined", client=client, clock=_CLOCK)
    baseline = len(client.calls)
    # A narrower semantic request reuses it (schema guarantees the fields).
    narrower = run_unit_inventory(repo, "ext1", "u1", role="reference", profile="semantic", client=client, clock=_CLOCK)
    assert narrower.cache_hit and narrower.reused_profile == "combined"
    assert len(client.calls) == baseline


# ---------------------------------------------------------------------------
# §14 validation & windowing
# ---------------------------------------------------------------------------


def test_inventory_rejects_uncited_and_unknown_spans():
    inv = SourceUnitInventory(claims=[InventoryClaim(statement="x", span_ids=[])])
    with pytest.raises(Exception):
        validate_inventory(inv, {"s1"})
    inv2 = SourceUnitInventory(claims=[InventoryClaim(statement="x", span_ids=["s99"])])
    with pytest.raises(Exception):
        validate_inventory(inv2, {"s1"})
    # Well-cited assertion passes.
    validate_inventory(SourceUnitInventory(claims=[InventoryClaim(statement="x", span_ids=["s1"])]), {"s1"})


def test_oversize_unit_splits_into_windows(tmp_path):
    repo = _repo(tmp_path)
    long_a = "Alpha prose. " * 500
    long_b = "Beta prose. " * 500
    ir = _ir(
        [
            (
                "u1",
                "Big",
                [
                    _block("s1", long_a, section=("root", "A")),
                    _block("s2", long_b, section=("root", "B")),
                ],
                "sha256:h1",
                1,
            )
        ]
    )
    windows = build_inventory_windows(ir, "u1", input_budget_tokens=1000)
    assert len(windows) >= 2  # split on the section boundary
    assert all(window["window_count"] == len(windows) for window in windows)

    _register_revision(repo)
    _persist(repo, ir, revision_id="rev1", extraction_id="ext1")
    progress: list[tuple[int, int]] = []
    result = run_unit_inventory(
        repo,
        "ext1",
        "u1",
        role="primary_textbook",
        client=FakeInventoryClient(),
        input_budget_tokens=1000,
        progress=lambda current, total: progress.append((current, total)),
        clock=_CLOCK,
    )
    assert result.usage["calls"] == len(windows)
    assert progress == [
        (current, len(windows)) for current in range(1, len(windows) + 1)
    ]


# ---------------------------------------------------------------------------
# §14 exam profiles + same-family collapse
# ---------------------------------------------------------------------------


def _exam_inventory(task_family="compute_eigenvalues", capability="apply", representation="symbolic", fmt="short_answer") -> dict:
    return SourceUnitInventory(
        assessment_signals=[
            InventoryAssessmentSignal(
                held_out=True,
                task_family=task_family,
                capability_demands=[capability],
                representation=representation,
                response_format=fmt,
                point_or_time_emphasis="high",
                span_ids=["s1"],
            )
        ]
    ).model_dump()


def test_same_family_exam_papers_collapse_to_one_vote():
    # Two years of the SAME syllabus family testing the same task family collapse
    # to ONE assessment-alignment vote (§4.2 correlation discipline).
    entries = [
        ExamUnitEntry("u_2023", _exam_inventory(), {"syllabus": "AQA-A-level", "year": "2023"}),
        ExamUnitEntry("u_2024", _exam_inventory(), {"syllabus": "AQA-A-level", "year": "2024"}),
    ]
    profile = aggregate_exam_profile(entries)
    assert profile.family_count == 1
    assert profile.task_families["compute_eigenvalues"] == 1  # one vote, not two

    # A genuinely different syllabus family is independent evidence.
    entries.append(ExamUnitEntry("u_ib", _exam_inventory(), {"syllabus": "IB-HL", "year": "2024"}))
    profile2 = aggregate_exam_profile(entries)
    assert profile2.family_count == 2
    assert profile2.task_families["compute_eigenvalues"] == 2


def test_exam_family_key_ignores_year():
    a = exam_family_key({"syllabus": "AQA", "year": "2023"})
    b = exam_family_key({"syllabus": "AQA", "year": "2024"})
    assert a == b
    assert exam_family_key({"syllabus": "AQA", "version": "v2"}) != a


# ---------------------------------------------------------------------------
# inventory job type in the durable runner (depends on extraction; zero tokens
# on cache hit)
# ---------------------------------------------------------------------------


def test_inventory_job_caches_zero_tokens_on_hit(tmp_path):
    from learnloop.content.pipeline.runner import IngestRunner, JobSpec, RunnerServices

    repo = _repo(tmp_path)
    _register_revision(repo)
    ir = _ir([("u1", "Ch1", [_block("s1", "Chapter one prose about eigenvectors.")], "sha256:h1", 1)])
    _persist(repo, ir, revision_id="rev1", extraction_id="ext1")

    client = FakeInventoryClient()
    services = RunnerServices(inventory_client_factory=lambda ctx: client)
    runner = IngestRunner(repo, vault_root=tmp_path, worker_id="w1", clock=_CLOCK, services=services)

    payload = {"extraction_id": "ext1", "units": [{"unit_id": "u1", "role": "primary_textbook", "profile": "combined"}]}
    batch1 = runner.enqueue_batch("import_inventory", [JobSpec("inventory", payload)])
    runner.drain()
    job1 = runner.repo.ingest_jobs_for_batch(batch1)[0]
    assert job1["status"] == "completed"
    assert job1["result"]["cache_hits"] == 0
    assert len(client.calls) == 1

    # A second inventory batch over the same pinned unit spends ZERO new tokens.
    batch2 = runner.enqueue_batch("import_inventory", [JobSpec("inventory", payload)])
    runner.drain()
    job2 = runner.repo.ingest_jobs_for_batch(batch2)[0]
    assert job2["status"] == "completed"
    assert job2["result"]["cache_hits"] == 1
    assert job2["result"]["units"][0]["cache_hit"] is True
    assert len(client.calls) == 1  # no new calls


def test_inventory_job_blocks_when_extraction_dependency_fails(tmp_path):
    from learnloop.content.pipeline.runner import IngestRunner, JobSpec, RunnerServices

    repo = _repo(tmp_path)
    client = FakeInventoryClient()
    services = RunnerServices(inventory_client_factory=lambda ctx: client)
    runner = IngestRunner(repo, vault_root=tmp_path, worker_id="w1", clock=_CLOCK, services=services)
    # inventory depends on a (failing, missing extraction) import job.
    batch = runner.enqueue_batch(
        "import_inventory",
        [
            JobSpec("import", {"source": "/does/not/exist.pdf"}),
            JobSpec("inventory", {"extraction_id": "extX", "units": [{"unit_id": "u1", "role": "reference"}]}, depends_on=(0,)),
        ],
    )
    runner.drain()
    jobs = {job["job_type"]: job for job in runner.repo.ingest_jobs_for_batch(batch)}
    assert jobs["inventory"]["status"] == "blocked"
    assert not client.calls  # never ran


# ---------------------------------------------------------------------------
# §14 unknown role fails closed for authority
# ---------------------------------------------------------------------------


def test_unknown_role_fails_closed_for_authority():
    unknown = role_authority("something_new")
    assert not unknown.known
    assert not unknown.semantic_contract
    assert not unknown.assessment_alignment

    # Exam has assessment alignment but never semantic authority.
    exam = role_authority("exam")
    assert exam.known and not exam.semantic_contract and exam.assessment_alignment
    assert not can_authorize_semantic("exam")

    # Empty role also fails closed.
    assert not role_authority("").semantic_contract

    # A manual grant with full audit metadata can lift an unknown role.
    grant = ManualAuthorityGrant(
        semantic_contract=True,
        assessment_alignment=False,
        scope="concept:eigenvector",
        rationale="curated instructor notes",
        actor="teacher@example.com",
        granted_at="2026-07-13T12:00:00Z",
    )
    lifted = role_authority("something_new", manual_grant=grant)
    assert lifted.manual and lifted.semantic_contract and lifted.audit["actor"] == "teacher@example.com"

    # A grant missing audit metadata is refused.
    with pytest.raises(ValueError):
        role_authority("x", manual_grant={"semantic_contract": True})


def test_procedure_signal_span_ids_coercion_and_validation():
    # Model returns span_ids instead of observable_step_span_ids on procedure signals
    raw = {
        "procedure_id": "p1",
        "contract": "solve linear system",
        "ordered_steps": ["step 1"],
        "span_ids": ["s01", "s02"],
    }
    proc = InventoryProcedureSignal.model_validate(raw)
    assert proc.observable_step_span_ids == ["s01", "s02"]

    # Validate inventory handles procedure_signals with span_ids correctly
    inv = SourceUnitInventory(
        unit_id="u1",
        semantic_hash="hash1",
        procedure_signals=[proc],
    )
    validate_inventory(inv, {"s01", "s02"})
