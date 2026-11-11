"""What other test files use from ``tests/test_ux_phase1_review_fixes.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.content.pipeline.add_source import AddSourceOptions, add_source
from learnloop.content.pipeline.jobs import DurableIngestJobs
from learnloop.vault.loader import load_vault

from tests.ux_phase1_support import CLOCK, grant_consent, repository, route, set_config


def _jobs(root, services, *, hold: bool = False):
    repo = repository(root)
    jobs = DurableIngestJobs()
    jobs.bind(repo, root, background=False, clock=CLOCK, services=services)
    if hold:
        jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    return repo, jobs


def _drain(jobs, max_jobs=None):
    return jobs._require_runner().drain(max_jobs=max_jobs)


def _add(root, jobs, source, **options):
    return add_source(load_vault(root), jobs, str(source), AddSourceOptions(**options), clock=CLOCK)


def _build_batches(repo):
    return [batch for batch in repo.list_ingest_batches() if batch["workflow_type"] == "bootstrap_synthesis"]


def _receipt(repo, *, provider, cost=None, input_tokens=0, output_tokens=0, owner_kind="sidecar_request",
             owner_id="req_1", started_at=None):
    """A finished model call receipt, as the runner's observer records one."""

    call_id = f"call_{owner_id}_{provider}_{cost}_{input_tokens}_{started_at}"
    started = started_at or CLOCK.now().isoformat()
    repo.record_model_event("start", {"id": call_id, "purpose": "test", "provider": provider,
                                      "model": "m", "started_at": started},
                            owner_kind=owner_kind, owner_id=owner_id)
    repo.record_model_event("finish", {"id": call_id, "status": "completed", "finished_at": started,
                                       "input_tokens": input_tokens, "output_tokens": output_tokens,
                                       "cost": cost}, owner_kind=owner_kind, owner_id=owner_id)


def _metered(root, price):
    set_config(root, {("ingest", "cost_pause", "prices", "openrouter"): price})
    grant_consent(root, "openrouter")
    return route(provider="openrouter", subscription=False, consent_key="openrouter")
