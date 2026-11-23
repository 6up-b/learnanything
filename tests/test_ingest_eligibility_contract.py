"""The desktop asks the sidecar what an ingest action may do instead of copying its rules.

Four copied rules disagreed with the backend: which synthesis a batch may retry, which roles never
define concepts, the image kind in the classifier's reply, and whether a native-engine PDF import takes
a page range. Each reply here is the backend's own check, and each test pins that the reply and the
action agree, so a desktop that reads the reply offers exactly what the action accepts.
"""

from __future__ import annotations

import pytest

from learnloop.content.pipeline.jobs import DurableIngestJobs, SYNTHESIS_RECOVERY_REFUSALS
from learnloop.content.pipeline.runner import IngestRunnerError, JobSpec, RunnerServices
from learnloop.content.sources.role_authority import (
    ASSESSMENT_ONLY_ROLES,
    KNOWN_ROLES,
    SCOPE_ONLY_ROLES,
    default_inventory_profile,
    role_authority,
)
from learnloop.db.repositories import Repository
from learnloop.ops.settings_store import apply_config_updates
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.ingest import PDF_ENGINES, _native_pdf_preflight

from tests.helpers import create_basic_vault
from tests.settings_sidecar_helpers import _settings_rpc


def _bind(tmp_path) -> DurableIngestJobs:
    jobs = DurableIngestJobs()
    jobs.bind(Repository(tmp_path / "state.sqlite"), tmp_path, services=RunnerServices(), background=False)
    return jobs


def _synthesis_batch(jobs: DurableIngestJobs, ending: str, *, details: dict | None = None) -> str:
    """An inventory and its synthesis, the synthesis ending ``failed``, ``cancelled`` or ``blocked``."""

    runner = jobs._require_runner()
    runner.handlers["inventory"] = (
        (lambda ctx: (_ for _ in ()).throw(RuntimeError("inventory broke"))) if ending == "blocked"
        else (lambda ctx: {"inventoried": True})
    )

    def fail_synthesis(ctx):
        raise IngestRunnerError("gates failed", code="synthesis_gate_failed", details=details or {}, retryable=True)

    runner.handlers["bootstrap_synthesis"] = fail_synthesis
    batch_id = runner.enqueue_batch(
        "bootstrap_synthesis",
        [
            JobSpec("inventory", {"units": [{"unit_id": "u1"}]}),
            JobSpec("bootstrap_synthesis", {"source_set_id": "set_x"}, depends_on=(0,)),
        ],
    )
    if ending == "cancelled":
        runner.drain(max_jobs=1)
        runner.cancel_batch(batch_id)
    else:
        runner.drain()
    statuses = [job["status"] for job in runner.repo.ingest_jobs_for_batch(batch_id)]
    expected = {"failed": ["completed", "failed"], "cancelled": ["completed", "cancelled"],
                "blocked": ["failed", "blocked"]}[ending]
    assert statuses == expected
    return batch_id


def test_a_cancelled_synthesis_offers_retry_and_the_retry_is_taken(tmp_path):
    jobs = _bind(tmp_path)
    batch_id = _synthesis_batch(jobs, "cancelled")

    batch = jobs.get_batch(batch_id)
    assert batch["status"] == "cancelled"
    assert batch["can_retry_synthesis"] is True
    assert batch["retry_synthesis_refusal"] is None
    assert batch["retry_synthesis_job_id"] == batch["jobs"][1]["id"]

    jobs._require_runner().handlers["bootstrap_synthesis"] = lambda ctx: {"synthesized": True}
    assert jobs.retry_synthesis(batch_id, unlimited_token_budget=True)["status"] == "completed"


@pytest.mark.parametrize("ending", ["failed", "cancelled", "blocked"])
def test_the_batch_view_offers_retry_exactly_when_the_host_takes_it(tmp_path, ending):
    jobs = _bind(tmp_path)
    batch_id = _synthesis_batch(jobs, ending)
    batch = jobs.get_batch(batch_id)
    jobs._require_runner().handlers["bootstrap_synthesis"] = lambda ctx: {"synthesized": True}

    if batch["can_retry_synthesis"]:
        jobs.retry_synthesis(batch_id, unlimited_token_budget=True)
    else:
        # A blocked synthesis behind a failed inventory: a synthesis-only retry would read a missing inventory.
        assert ending == "blocked"
        assert batch["retry_synthesis_refusal"] == "inventory_incomplete"
        with pytest.raises(ValueError, match=SYNTHESIS_RECOVERY_REFUSALS["inventory_incomplete"]):
            jobs.retry_synthesis(batch_id, unlimited_token_budget=True)


def test_a_completed_batch_offers_no_retry(tmp_path):
    jobs = _bind(tmp_path)
    runner = jobs._require_runner()
    runner.handlers["inventory"] = lambda ctx: {"inventoried": True}
    batch_id = runner.enqueue_batch("inventory", [JobSpec("inventory", {"units": [{"unit_id": "u1"}]})])
    runner.drain()

    batch = jobs.get_batch(batch_id)
    assert batch["can_retry_synthesis"] is False
    assert batch["retry_synthesis_refusal"] == "no_unfinished_synthesis"
    assert batch["can_reuse_candidate"] is False
    with pytest.raises(ValueError, match=SYNTHESIS_RECOVERY_REFUSALS["no_unfinished_synthesis"]):
        jobs.retry_synthesis(batch_id)


@pytest.mark.parametrize(
    ("details", "stored", "refusal"),
    [
        ({"candidate_preserved": True, "synthesis_run_id": "run_1"}, {"candidate_output": {"summary": "s"}}, None),
        ({"candidate_preserved": True, "synthesis_run_id": "run_1"}, None, "candidate_gone"),
        ({}, None, "no_preserved_candidate"),
    ],
)
def test_candidate_reuse_is_offered_exactly_when_the_host_takes_it(tmp_path, details, stored, refusal):
    jobs = _bind(tmp_path)
    batch_id = _synthesis_batch(jobs, "failed", details=details)
    runner = jobs._require_runner()
    runner.repo.synthesis_run = lambda run_id: ({"id": run_id, **stored} if stored else None)

    batch = jobs.get_batch(batch_id)
    assert batch["can_retry_synthesis"] is True
    assert batch["can_reuse_candidate"] is (refusal is None)
    assert batch["reuse_candidate_refusal"] == refusal
    assert jobs.list_batches()[0]["can_reuse_candidate"] is (refusal is None)

    runner.handlers["bootstrap_synthesis"] = lambda ctx: {"revalidated": True}
    if refusal is None:
        assert jobs.retry_synthesis(batch_id, reuse_candidate=True)["status"] == "completed"
    else:
        with pytest.raises(ValueError, match=SYNTHESIS_RECOVERY_REFUSALS[refusal]):
            jobs.retry_synthesis(batch_id, reuse_candidate=True)


def test_get_source_roles_is_the_authority_matrix_in_the_spec_order(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    reply = _settings_rpc(vault_root, ("get_source_roles", {}))[0]["result"]

    assert reply["version"] == 1
    roles = reply["roles"]
    assert [row["role"] for row in roles] == [
        "primary_textbook", "lecture", "paper", "reference", "alternate_explanation",
        "problem_set", "exam", "notes", "syllabus",
    ]
    assert {row["role"] for row in roles} == KNOWN_ROLES
    for row in roles:
        authority = role_authority(row["role"])
        assert row["semanticContract"] is authority.semantic_contract
        assert row["assessmentAlignment"] is authority.assessment_alignment
        assert row["assessmentOnly"] is (row["role"] in ASSESSMENT_ONLY_ROLES)
        assert row["scopeOnly"] is (row["role"] in SCOPE_ONLY_ROLES)
        assert row["defaultInventoryProfile"] == default_inventory_profile(row["role"])
    # The desktop's copy said {exam, problem_set} never define concepts; the matrix says notes doesn't either.
    never_defines = {row["role"] for row in roles if not row["semanticContract"] and not row["scopeOnly"]}
    assert never_defines == {"problem_set", "exam", "notes"}


def test_get_source_roles_takes_no_params(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    response = _settings_rpc(vault_root, ("get_source_roles", {"role": "exam"}))[0]

    assert "result" not in response
    assert response["error"]["data"]["code"] == "validation_error"


def test_settings_carry_every_budget_bound_the_handlers_enforce(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    bounds = _settings_rpc(vault_root, ("get_settings", {}))[0]["result"]["ingest"]["budgetBounds"]

    # The failed-synthesis retry panel's three ceilings.
    assert bounds["synthesisTotalInputCeiling"] == {"min": 10_000, "max": 2_000_000}
    assert bounds["synthesisShardOutputTokens"] == {"min": 1_000, "max": 200_000}
    assert bounds["synthesisOutputTokens"] == {"min": 1_000, "max": 200_000}


@pytest.mark.parametrize(
    ("vault_engine", "fallback", "refusing"),
    [
        ("auto", False, ["native"]),
        ("native", False, ["auto", "native"]),
        # An unready native model with the fallback opted in takes the local road, which honours page ranges:
        # the desktop disabled the range control for it all the same.
        ("auto", True, []),
        ("native", True, []),
    ],
)
def test_page_ranges_are_refused_under_exactly_the_engines_settings_name(
    tmp_path, monkeypatch, vault_engine, fallback, refusing
):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    apply_config_updates(
        vault_root / "learnloop.toml",
        {
            ("ingest", "pdf", "engine"): vault_engine,
            ("ingest", "native", "fallback_when_unavailable"): fallback,
        },
    )
    pdf_path = tmp_path / "chapter.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    # Only refused imports go over the wire: an accepted one would enqueue a real import of the fake file.
    responses = _settings_rpc(
        vault_root,
        ("get_settings", {}),
        *(
            ("start_import_batch", {"sources": [str(pdf_path)], "pdfEngine": engine, "pageStart": 1, "pageEnd": 3})
            for engine in refusing
        ),
    )

    assert responses[0]["result"]["ingest"]["pdfEnginesRefusingPageRanges"] == refusing
    for response in responses[1:]:
        assert response["error"]["data"]["code"] == "invalid_page_range", response
    vault = load_vault(vault_root)
    for engine in PDF_ENGINES:
        try:
            _native_pdf_preflight(vault, engine, [str(pdf_path)], has_page_ranges=True)
        except SidecarError as exc:
            refused = exc.code == "invalid_page_range"
        else:
            refused = False
        assert refused is (engine in refusing), engine
