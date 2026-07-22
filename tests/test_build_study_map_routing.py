"""build_study_map routing (spec_source_ingestion_v2 §1/§8/§10).

The in-app "synthesize →" action must mirror the CLI's ``--mode auto`` decision:
with no live study map for the subject it BOOTSTRAPS (inventory every member →
bootstrap_synthesis); once a map exists it APPENDS — inventorying only the new,
not-yet-synthesized members and reconciling them via the bounded neighborhood,
never rebuilding the map. Here we assert the routing decision + job scoping with
the enqueue seam recorded (heavy synthesis paths live in the service tests).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.source_append import subject_has_applied_study_map
from learnloop.services.source_unit_inventory import run_unit_inventory
from learnloop.vault.loader import add_subject, init_vault, load_vault
from learnloop.vault.writer import upsert_source_set
from learnloop_sidecar.handlers.ingest import BuildStudyMapInput, build_study_map_rpc

from tests.test_source_inventory import FakeInventoryClient, _block, _ir, _persist, _register_revision

_CLOCK = FrozenClock(datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC))


class _RecordingJobs:
    """Records which enqueue path the RPC took without running any job."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def enqueue_source_set_build(self, **kwargs: Any) -> str:
        self.calls.append(("build", kwargs))
        return "batch_build"

    def enqueue_source_set_append(self, **kwargs: Any) -> str:
        self.calls.append(("append", kwargs))
        return "batch_append"

    def get_batch(self, batch_id: str) -> dict[str, Any]:
        return {"id": batch_id, "workflow_type": "recorded", "jobs": []}


def _seed(tmp_path: Path) -> tuple[Path, Repository]:
    """A subject with a two-member collection: rev_a already inventoried
    (an existing/synthesized member) and rev_b un-inventoried (freshly added)."""

    root = tmp_path / "vault"
    init_vault(root, clock=_CLOCK)
    add_subject(root, "linear-algebra", "Linear Algebra", clock=_CLOCK)
    repo = Repository(root / "state.sqlite")

    _register_revision(repo, source_id="src_a", revision_id="rev_a")
    _register_revision(repo, source_id="src_b", revision_id="rev_b")
    _persist(repo, _ir([("u_a", "A", [_block("s1", "An eigenvector of A.")], "sha256:a", 1)]),
             revision_id="rev_a", extraction_id="ext_a")
    _persist(repo, _ir([("u_b", "B", [_block("s2", "A basis of a vector space.")], "sha256:b", 1)]),
             revision_id="rev_b", extraction_id="ext_b")

    # rev_a is already inventoried -> counts as existing/synthesized material.
    run_unit_inventory(repo, "ext_a", "u_a", role="primary_textbook", client=FakeInventoryClient(), clock=_CLOCK)

    upsert_source_set(
        root,
        {
            "id": "set_x",
            "subject_id": "linear-algebra",
            "title": "Collection",
            "members": [
                {"source_id": "src_a", "revision_id": "rev_a", "default_role": "primary_textbook",
                 "scope": [{"unit_id": "u_a"}], "priority": 1},
                {"source_id": "src_b", "revision_id": "rev_b", "default_role": "primary_textbook",
                 "scope": [{"unit_id": "u_b"}], "priority": 2},
            ],
        },
        clock=_CLOCK,
    )
    return root, repo


def _ctx(root: Path, repo: Repository, jobs: _RecordingJobs) -> SimpleNamespace:
    vault = load_vault(root)
    return SimpleNamespace(
        vault=vault,
        repository=repo,
        vault_root=root,
        ingest_jobs=jobs,
        require_vault=lambda: (vault, repo),
    )


def test_helper_detects_applied_study_map() -> None:
    empty = SimpleNamespace(learning_objects={})
    assert subject_has_applied_study_map(empty, "linear-algebra") is False
    mapped = SimpleNamespace(
        learning_objects={"lo1": SimpleNamespace(subjects=["linear-algebra"])}
    )
    assert subject_has_applied_study_map(mapped, "linear-algebra") is True
    assert subject_has_applied_study_map(mapped, "topology") is False


def test_no_map_routes_to_bootstrap_over_all_members(tmp_path: Path) -> None:
    root, repo = _seed(tmp_path)
    jobs = _RecordingJobs()
    result = build_study_map_rpc(
        _ctx(root, repo, jobs),
        BuildStudyMapInput(source_set_id="set_x", inventory_output_tokens=12_000),
    )

    assert len(jobs.calls) == 1
    kind, kwargs = jobs.calls[0]
    assert kind == "build"
    # bootstrap inventories every member.
    assert {m["extraction_id"] for m in kwargs["members"]} == {"ext_a", "ext_b"}
    assert kwargs["output_budget_tokens"] == 12_000
    assert result["mode"] == "bootstrap"


def test_unlimited_budget_is_forwarded_to_every_build_stage(tmp_path: Path) -> None:
    root, repo = _seed(tmp_path)
    jobs = _RecordingJobs()

    build_study_map_rpc(
        _ctx(root, repo, jobs),
        BuildStudyMapInput(
            source_set_id="set_x",
            inventory_output_tokens=1,
            unlimited_token_budget=True,
        ),
    )

    kind, kwargs = jobs.calls[0]
    assert kind == "build"
    assert kwargs["unlimited_token_budget"] is True
    # Retaining the number lets the UI restore it if unlimited is toggled off.
    assert kwargs["output_budget_tokens"] == 1


def test_existing_map_routes_to_append_over_new_members_only(tmp_path: Path, monkeypatch) -> None:
    root, repo = _seed(tmp_path)
    # The subject already carries a study map -> auto routes to append.
    monkeypatch.setattr(
        "learnloop.services.source_append.subject_has_applied_study_map",
        lambda vault, subject_id: True,
    )
    jobs = _RecordingJobs()
    result = build_study_map_rpc(_ctx(root, repo, jobs), BuildStudyMapInput(source_set_id="set_x"))

    assert len(jobs.calls) == 1
    kind, kwargs = jobs.calls[0]
    assert kind == "append"
    # Only the un-inventoried (new) member is inventoried; the append is pinned to it.
    assert [m["extraction_id"] for m in kwargs["members"]] == ["ext_b"]
    assert kwargs["new_revision_ids"] == ["rev_b"]
    assert result["mode"] == "append"
