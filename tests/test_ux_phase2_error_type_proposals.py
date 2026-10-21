"""UX Phase 2, Codex review of ux-phase2-shell F6: one waiting proposal per new
error type.

Phase 1's usability round 1 deferred to Phase 2 "Proposals grows on every
practice, with duplicate error-type proposals". The cause is the writer:
``persist_unknown_error_type_proposals`` checked the vault's accepted error
types and the built-ins, never the proposals still waiting, so every grading
that named the same new error type wrote another pending batch for it. It now
appends the new attempt to the waiting proposal's batch instead (its source
refs keep every contributing attempt), and the check and the write are one
step under SQLite's write lock, so two gradings at once cannot both write.

Proposal tables are WORKFLOW (``db/table_roles.py``): no replayer rebuilds
them and no grading, scheduling, evidence or projection path reads them, so
this changes no persisted meaning and needs no algorithm successor.

Fakes only; no network, no model call.
"""

from __future__ import annotations

import json
import threading

from learnloop.attempts.grading import ValidatedErrorAttribution
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.diagnosis.error_taxonomy import persist_unknown_error_type_proposals
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from tests.helpers import NOW, create_basic_vault


def _setup(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    repository.insert_agent_run(
        {"id": "run_grading", "purpose": "grading", "started_at": NOW.isoformat(), "status": "completed"}
    )
    return paths, vault, repository, clock


def _attribution(error_type: str) -> ValidatedErrorAttribution:
    return ValidatedErrorAttribution(error_type=error_type, severity=0.6, evidence="The learner slipped.")


def _grade(vault, repository, clock, attempt_id: str, *error_types: str) -> str | None:
    return persist_unknown_error_type_proposals(
        vault,
        repository,
        attributions=[_attribution(error_type) for error_type in error_types],
        attempt_id=attempt_id,
        agent_run_id="run_grading",
        clock=clock,
    )


def _pending_error_type_items(repository: Repository) -> list[dict]:
    items = []
    for batch in repository.proposal_batches():
        for item in repository.proposal_items(batch["id"]):
            if item["item_type"] == "error_type" and item["decision"] == "pending":
                items.append({**item, "batch": batch})
    return items


def _attempt_refs(batch: dict) -> list[str]:
    return [ref["ref_id"] for ref in batch["source_refs"] if ref.get("locator") == "grading_error_attribution"]


def test_repeated_gradings_naming_one_new_error_type_leave_one_waiting_proposal(tmp_path):
    _paths, vault, repository, clock = _setup(tmp_path)
    first = _grade(vault, repository, clock, "attempt_1", "local_slip")
    assert first is not None
    _grade(vault, repository, clock, "attempt_2", "local_slip")
    _grade(vault, repository, clock, "attempt_3", "local_slip")

    pending = _pending_error_type_items(repository)
    assert [item["client_item_id"] for item in pending] == ["error_type:local_slip"]
    # Every grading that named it is still on the waiting proposal.
    assert _attempt_refs(pending[0]["batch"]) == ["attempt_1", "attempt_2", "attempt_3"]
    assert len(repository.proposal_batches()) == 1


def test_a_grading_naming_a_waiting_type_and_a_new_one_writes_only_the_new_one(tmp_path):
    _paths, vault, repository, clock = _setup(tmp_path)
    _grade(vault, repository, clock, "attempt_1", "local_slip")
    _grade(vault, repository, clock, "attempt_2", "local_slip", "representation_notation_error")

    pending = sorted(item["client_item_id"] for item in _pending_error_type_items(repository))
    assert pending == ["error_type:local_slip", "error_type:representation_notation_error"]
    by_type = {item["client_item_id"]: item for item in _pending_error_type_items(repository)}
    assert _attempt_refs(by_type["error_type:local_slip"]["batch"]) == ["attempt_1", "attempt_2"]
    assert _attempt_refs(by_type["error_type:representation_notation_error"]["batch"]) == ["attempt_2"]


def test_a_regrade_of_the_same_attempt_adds_nothing(tmp_path):
    _paths, vault, repository, clock = _setup(tmp_path)
    _grade(vault, repository, clock, "attempt_1", "local_slip")
    assert _grade(vault, repository, clock, "attempt_1", "local_slip") is not None
    pending = _pending_error_type_items(repository)
    assert len(pending) == 1
    assert _attempt_refs(pending[0]["batch"]) == ["attempt_1"]


def test_a_rejected_proposal_does_not_absorb_a_later_grading(tmp_path):
    """Only a waiting proposal collects later gradings; once the learner has
    decided one, a new grading that names the type proposes it afresh, as
    before."""

    paths, vault, repository, clock = _setup(tmp_path)
    _grade(vault, repository, clock, "attempt_1", "local_slip")
    with connect(paths.sqlite_path) as connection:
        connection.execute("UPDATE proposed_patch_items SET decision = 'rejected' WHERE item_type = 'error_type'")
        connection.commit()
    _grade(vault, repository, clock, "attempt_2", "local_slip")
    pending = _pending_error_type_items(repository)
    assert len(pending) == 1
    assert _attempt_refs(pending[0]["batch"]) == ["attempt_2"]


def test_a_grading_that_waits_on_another_writer_sees_its_proposal(tmp_path):
    """Two gradings at once: the second waits for the first's write to commit
    and then appends to it, rather than reading before the lock and writing a
    second proposal after it (the check and the write are one step)."""

    paths, vault, repository, clock = _setup(tmp_path)
    done = threading.Event()
    outcome: dict[str, object] = {}

    def second_grading() -> None:
        try:
            outcome["batch"] = _grade(vault, Repository(paths.sqlite_path), clock, "attempt_2", "local_slip")
        except BaseException as exc:  # surfaced below
            outcome["error"] = exc
        finally:
            done.set()

    holder = connect(paths.sqlite_path)
    holder.isolation_level = None
    try:
        # The first grading's write, under its write lock and not yet committed.
        holder.execute("BEGIN IMMEDIATE")
        now = NOW.isoformat()
        holder.execute(
            "INSERT INTO proposed_patches(id, agent_run_id, purpose, source_refs_json, summary, status_cache, "
            "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "patch_first",
                "run_grading",
                "grading_error_type",
                json.dumps([{"ref_type": "manual_context", "ref_id": "attempt_1", "locator": "grading_error_attribution"}]),
                "Proposed error taxonomy entries from grading.",
                "pending",
                now,
                now,
            ),
        )
        holder.execute(
            "INSERT INTO proposed_patch_items(id, proposed_patch_id, client_item_id, item_type, operation, payload_json, "
            "decision, validation_status, validation_errors_json, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "item_first",
                "patch_first",
                "error_type:local_slip",
                "error_type",
                "create",
                json.dumps({"id": "local_slip", "title": "Local Slip"}),
                "pending",
                "valid",
                "[]",
                now,
                now,
            ),
        )
        thread = threading.Thread(target=second_grading)
        thread.start()
        # The second grading is waiting on the lock, not done.
        assert not done.wait(0.5)
        holder.execute("COMMIT")
        assert done.wait(10)
        thread.join(10)
    finally:
        holder.close()
    assert "error" not in outcome, outcome.get("error")
    pending = _pending_error_type_items(repository)
    assert [item["client_item_id"] for item in pending] == ["error_type:local_slip"]
    assert _attempt_refs(pending[0]["batch"]) == ["attempt_1", "attempt_2"]


# ── Fix round 2 (orchestrator; whole-stage verify 20261021-114726-Jrt7sA, 5) ──
# The payload editor can change a waiting proposal's ``id`` while its
# ``client_item_id`` stays ``error_type:<old id>``. The dedupe must match a
# waiting create by what it would now create (the edited payload's id when
# edited, otherwise the original), not by the stale client id.


def _rename_waiting(paths, repository: Repository, old: str, new: str) -> dict:
    from learnloop.content.proposals.proposals import edit_proposal_item

    (item,) = [item for item in _pending_error_type_items(repository) if item["payload"]["id"] == old]
    edit_proposal_item(paths.root, item["batch"]["id"], item["id"], {**item["payload"], "id": new, "title": "Notation Slip"})
    (edited,) = [entry for entry in _pending_error_type_items(repository) if entry["id"] == item["id"]]
    # The edit keeps the client id; only the edited payload names the new type.
    assert edited["client_item_id"] == f"error_type:{old}"
    assert edited["edited_payload"]["id"] == new
    return edited


def test_a_grading_naming_the_edited_id_joins_the_renamed_proposal(tmp_path):
    paths, vault, repository, clock = _setup(tmp_path)
    _grade(vault, repository, clock, "attempt_1", "local_slip")
    renamed = _rename_waiting(paths, repository, "local_slip", "notation_slip")

    joined = _grade(vault, repository, clock, "attempt_2", "notation_slip")

    assert joined == renamed["batch"]["id"]
    pending = _pending_error_type_items(repository)
    assert [item["id"] for item in pending] == [renamed["id"]]
    assert _attempt_refs(pending[0]["batch"]) == ["attempt_1", "attempt_2"]
    assert len(repository.proposal_batches()) == 1


def test_a_grading_naming_the_old_id_of_a_renamed_proposal_proposes_it_afresh(tmp_path):
    paths, vault, repository, clock = _setup(tmp_path)
    _grade(vault, repository, clock, "attempt_1", "local_slip")
    renamed = _rename_waiting(paths, repository, "local_slip", "notation_slip")

    fresh = _grade(vault, repository, clock, "attempt_2", "local_slip")

    assert fresh is not None and fresh != renamed["batch"]["id"]
    pending = _pending_error_type_items(repository)
    effective = sorted((item.get("edited_payload") or item["payload"])["id"] for item in pending)
    assert effective == ["local_slip", "notation_slip"]
    by_batch = {item["batch"]["id"]: item for item in pending}
    # The renamed proposal keeps only the attempt that named it; the new one has the new attempt.
    assert _attempt_refs(by_batch[renamed["batch"]["id"]]["batch"]) == ["attempt_1"]
    assert _attempt_refs(by_batch[fresh]["batch"]) == ["attempt_2"]
