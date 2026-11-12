"""The collection build sends every unit not yet inventoried (refactor K3.3).

``build_study_map`` called a member new only when its revision had no
inventory at all, so one cached unit made the whole revision old: its newly
selected units got no inventory job, and the append left them out.
"""

from __future__ import annotations

from types import SimpleNamespace

from learnloop.content.synthesis.source_set_synthesis import create_study_map
from learnloop.content.synthesis.source_unit_inventory import inventoried_unit_ids, run_unit_inventory
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_source_set
from learnloop_sidecar.handlers.ingest import BuildStudyMapInput, build_study_map_rpc

from tests.source_inventory_helpers import FakeInventoryClient, _block, _ir, _persist, _register_revision
from tests.source_set_synthesis_helpers import _CLOCK, FakeSynthesisClient, _setup
from tests.ux_phase1_auto_build_helpers import _jobs
from tests.ux_phase1_support import fake_services


class _RecordingJobs:
    def __init__(self, real=None) -> None:
        self.calls: list[tuple[str, dict]] = []
        self.real = real

    def enqueue_source_set_append(self, **kwargs) -> str:
        self.calls.append(("append", kwargs))
        return self.real.enqueue_source_set_append(**kwargs) if self.real else "batch_append"

    def enqueue_source_set_build(self, **kwargs) -> str:
        self.calls.append(("build", kwargs))
        return "batch_build"

    def get_batch(self, batch_id: str) -> dict:
        return {"id": batch_id, "jobs": []}


def _with_partly_inventoried_member(tmp_path):
    """An applied map from the textbook, plus a second book whose first unit is
    inventoried and whose two later units were just added to the collection."""

    root, repo = _setup(tmp_path, with_exam=False)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo,
                     clock=_CLOCK, apply=True, brief={"depth": "intro"})
    _register_revision(repo, source_id="src_more", revision_id="rev_more")
    _persist(repo, _ir([
        ("u1", "Orthogonal matrices", [_block("m1", "An orthogonal matrix has orthonormal columns.")], "sha256:m1", 3),
        ("u2", "Projections", [_block("m2", "A projection matrix satisfies P^2 = P.")], "sha256:m2", 4),
        ("u3", "Least squares", [_block("m3", "Least squares projects b onto the column space.")], "sha256:m3", 5),
    ]), revision_id="rev_more", extraction_id="ext_more")
    run_unit_inventory(repo, "ext_more", "u1", role="primary_textbook", profile="combined",
                       client=FakeInventoryClient(), input_budget_tokens=20000, clock=_CLOCK)
    vault = load_vault(root)
    members = [
        {"source_id": m.source_id, "revision_id": m.revision_id, "default_role": m.default_role,
         "scope": [{"unit_id": s.unit_id} for s in m.scope], "priority": m.priority}
        for m in next(s for s in vault.source_sets if s.id == "set_la").members
    ]
    members.append({"source_id": "src_more", "revision_id": "rev_more", "default_role": "primary_textbook",
                    "scope": [{"unit_id": "u1"}, {"unit_id": "u2"}, {"unit_id": "u3"}], "priority": 2})
    upsert_source_set(root, {"id": "set_la", "subject_id": "linear-algebra", "title": "Linear Algebra",
                             "members": members}, clock=_CLOCK)
    return root, repo


def _ctx(root, repo, jobs):
    vault = load_vault(root)
    return SimpleNamespace(vault=vault, repository=repo, vault_root=root, ingest_jobs=jobs,
                           require_vault=lambda: (vault, repo))


def test_new_units_of_a_partly_inventoried_member_are_inventoried_and_appended(tmp_path):
    root, repo = _with_partly_inventoried_member(tmp_path)
    appended = []
    _repo, real_jobs = _jobs(root, fake_services(on_append=appended.append))
    jobs = _RecordingJobs(real_jobs)

    result = build_study_map_rpc(_ctx(root, repo, jobs), BuildStudyMapInput(source_set_id="set_la"))

    assert result["mode"] == "append"
    _kind, kwargs = jobs.calls[0]
    assert [(m["extraction_id"], [u["unit_id"] for u in m["units"]]) for m in kwargs["members"]] == [
        ("ext_more", ["u2", "u3"]),
    ]
    assert kwargs["new_revision_ids"] == ["rev_more"]
    assert kwargs["new_unit_ids"] == {"rev_more": ["u2", "u3"]}
    # The batch ran: both new units were inventoried and reached the append, and nothing else did.
    assert {"u2", "u3"} <= inventoried_unit_ids(repo.unit_inventories_for_revision("rev_more"))
    assert len(appended) == 1
    assert sorted((e["revision_id"], e["unit_id"]) for e in appended[0].new_inventories) == [
        ("rev_more", "u2"), ("rev_more", "u3"),
    ]


def test_a_wholly_new_member_keeps_the_unfiltered_append(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo,
                     clock=_CLOCK, apply=True, brief={"depth": "intro"})
    _register_revision(repo, source_id="src_new", revision_id="rev_new")
    _persist(repo, _ir([("u1", "Orthogonal matrices", [_block("n1", "Q^T Q = I.")], "sha256:n1", 3)]),
             revision_id="rev_new", extraction_id="ext_new")
    vault = load_vault(root)
    members = [
        {"source_id": m.source_id, "revision_id": m.revision_id, "default_role": m.default_role,
         "scope": [{"unit_id": s.unit_id} for s in m.scope], "priority": m.priority}
        for m in next(s for s in vault.source_sets if s.id == "set_la").members
    ]
    members.append({"source_id": "src_new", "revision_id": "rev_new", "default_role": "primary_textbook",
                    "scope": [{"unit_id": "u1"}], "priority": 2})
    upsert_source_set(root, {"id": "set_la", "subject_id": "linear-algebra", "title": "Linear Algebra",
                             "members": members}, clock=_CLOCK)
    jobs = _RecordingJobs()

    build_study_map_rpc(_ctx(root, repo, jobs), BuildStudyMapInput(source_set_id="set_la"))

    _kind, kwargs = jobs.calls[0]
    assert kwargs["new_revision_ids"] == ["rev_new"]
    # No unit filter, so the append's payload and manifest keep their bytes.
    assert kwargs["new_unit_ids"] is None


def test_inventoried_unit_ids_counts_merged_members():
    rows = [{"unit_id": "u1"}, {"unit_id": "u4+u5"}]
    assert inventoried_unit_ids(rows) == {"u1", "u4", "u5"}
