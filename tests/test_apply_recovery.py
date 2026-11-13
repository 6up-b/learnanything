"""Refactor K3.5: proposal apply recovery is safe and automatic.

docs/reviews/k2-ingestion-strategy-2026-11-11.md §3.1 K3.5 (map KD2, crash windows W2-W6);
docs/reviews/refactor-k3.5.md records which of these ran red before the change.

* Recovery writes a target only over its pre-image or when it already holds its post-image; a file
  changed after the intent is kept, nothing of that intent is written, and the intent is ``conflicted``.
* The sidecar recovers at every primary bind, beside facet-identity recovery.
* An accept refuses while an intent is pending or conflicted (``OutstandingApplyIntentError``).
* Recovery runs the content recalibration the apply would have run (W6).
* The maintenance feed's action on an outstanding intent has its handler (``resolve_apply_intent``).
"""

from __future__ import annotations

import multiprocessing
import os
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.content.proposals import apply_protocol
from learnloop.content.proposals.apply_protocol import (
    ApplyIntentResolutionError,
    ApplyTargetConflict,
    materialize_targets,
    recover_apply_intents,
    resolve_apply_intent,
)
from learnloop.content.proposals.patches import (
    OutstandingApplyIntentError,
    PatchApplicationError,
    apply_accepted_items,
)
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.apply_write_ahead_helpers import (
    LO_ID,
    PI_ID,
    _seed_lo_and_pi_proposal,
    create_vault_registering_application,
)
from tests.sidecar_contract_helpers import _rpc


def _repo(paths: VaultPaths) -> Repository:
    return Repository(paths.sqlite_path)


def _crash_child(vault_root: str, patch_id: str, renamed: int) -> None:
    """Run the write-ahead protocol and kill the process after ``renamed`` of its target renames (a real crash)."""

    from learnloop.content.proposals.patches import _proposal_origin

    vault = load_vault(Path(vault_root))
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    requested = repository.pending_proposal_items(patch_id)
    ordered_ids, _blocked = apply_protocol.compute_dependency_closure(repository, requested)
    by_id = {item["id"]: item for item in requested}
    targets, db_plan = apply_protocol.stage_target_contents(
        vault.root, vault, [by_id[item_id] for item_id in ordered_ids], _proposal_origin(repository, patch_id),
        patch_id, clock=None,
    )
    assert len(targets) >= 2, "the LO and its practice item live in two files"
    repository.insert_apply_intent(proposed_patch_id=patch_id, item_ids=ordered_ids, targets=targets, db_plan=db_plan)
    apply_protocol.materialize_targets(vault.root, targets[:renamed])
    os._exit(1)


def _crash_after(paths: VaultPaths, renamed: int, patch_id: str = "patch_wa") -> None:
    proc = multiprocessing.get_context("fork").Process(target=_crash_child, args=(str(paths.root), patch_id, renamed))
    proc.start()
    proc.join(timeout=60)
    assert proc.exitcode == 1


def _hand_edit(paths: VaultPaths, target: dict) -> str:
    """The owner edits a half-applied file by hand: the intent's post-image with its title changed."""

    text = target["post_content"].replace("SVD applications", "SVD applications, edited by hand")
    assert text != target["post_content"]
    (paths.root / target["rel_path"]).write_text(text, encoding="utf-8")
    return text


def _pending_intent(repository: Repository) -> dict:
    (intent,) = repository.pending_apply_intents()
    return intent


def _initialize(paths: VaultPaths, *calls: dict) -> list[dict]:
    messages = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(paths.root)}}]
    messages += [{"jsonrpc": "2.0", "id": index + 2, **call} for index, call in enumerate(calls)]
    return _rpc(messages)


# --- P-fail 1: never write over a newer file --------------------------------------------------------------------------


def test_recovery_keeps_a_file_changed_after_the_intent_and_marks_it_conflicted(tmp_path):
    paths = create_vault_registering_application(tmp_path / "vault")
    repository = _repo(paths)
    _seed_lo_and_pi_proposal(repository)
    _crash_after(paths, renamed=1)  # crash between the two renames (W2)
    intent = _pending_intent(repository)
    first, second = intent["targets"][0], intent["targets"][1]
    # Someone edits the half-applied file before anything recovers it.
    edited = paths.root / first["rel_path"]
    newer = edited.read_text(encoding="utf-8") + "\n# the owner's newer edit\n"
    edited.write_text(newer, encoding="utf-8")

    assert recover_apply_intents(paths.root, repository) == []

    assert edited.read_text(encoding="utf-8") == newer  # the newer file is kept
    assert not (paths.root / second["rel_path"]).exists()  # and nothing else of the intent was written
    (row,) = repository.outstanding_apply_intents()
    assert row["status"] == "conflicted"
    assert row["conflicts"] == [{"rel_path": first["rel_path"], "pre_hash": first["pre_hash"],
                                 "post_hash": first["post_hash"], "found_hash": row["conflicts"][0]["found_hash"]}]
    assert row["conflicts"][0]["found_hash"] not in {first["pre_hash"], first["post_hash"]}
    assert repository.proposal_item("item_lo")["decision"] == "pending"  # no DB effect performed


def test_materialize_writes_over_the_pre_image_only(tmp_path):
    root = tmp_path / "tree"
    root.mkdir()
    (root / "a.yaml").write_text("before\n", encoding="utf-8")
    target = {"rel_path": "a.yaml", "pre_hash": apply_protocol._sha256_bytes(b"before\n"),
              "post_content": "after\n", "post_hash": apply_protocol._sha256_bytes(b"after\n")}
    new_file = {"rel_path": "b.yaml", "pre_hash": None, "post_content": "new\n",
                "post_hash": apply_protocol._sha256_bytes(b"new\n")}
    (root / "a.yaml").write_text("someone else\n", encoding="utf-8")
    with pytest.raises(ApplyTargetConflict) as raised:
        materialize_targets(root, [new_file, target])
    assert [conflict["rel_path"] for conflict in raised.value.conflicts] == ["a.yaml"]
    assert not (root / "b.yaml").exists()  # checked before anything is written
    assert (root / "a.yaml").read_text(encoding="utf-8") == "someone else\n"

    (root / "a.yaml").write_text("before\n", encoding="utf-8")
    materialize_targets(root, [new_file, target])
    materialize_targets(root, [new_file, target])  # idempotent at the post-image
    assert (root / "a.yaml").read_text(encoding="utf-8") == "after\n"
    # A target with no pre_hash key (facet registry saves, doctor content fixes) writes unguarded, as before.
    materialize_targets(root, [{"rel_path": "a.yaml", "post_content": "plain\n",
                                "post_hash": apply_protocol._sha256_bytes(b"plain\n")}])
    assert (root / "a.yaml").read_text(encoding="utf-8") == "plain\n"


def _count_replaces(monkeypatch) -> list[str]:
    replaced: list[str] = []
    real = os.replace

    def counting(src, dst, *args, **kwargs):
        replaced.append(str(dst))
        return real(src, dst, *args, **kwargs)

    monkeypatch.setattr(apply_protocol.os, "replace", counting)
    return replaced


def test_a_registry_save_of_the_text_already_there_writes_nothing(tmp_path, monkeypatch):
    """D-11: ``write_registry_text`` gave ``post_hash`` without the ``sha256:``
    prefix, so the idempotent skip never matched and every save rewrote the file."""

    from learnloop.content.facet_identity import authority

    from tests.facet_identity_actions_helpers import _vault_with_duplicate

    paths, _vault, _repository = _vault_with_duplicate(tmp_path)
    text = paths.facets_path.read_text(encoding="utf-8")
    replaced = _count_replaces(monkeypatch)

    authority.write_registry_text(paths, text, basis={})

    assert replaced == []
    assert paths.facets_path.read_text(encoding="utf-8") == text


def test_a_target_hashed_without_the_prefix_is_still_read(tmp_path, monkeypatch):
    """Both forms are read: a target recorded before D-11 (a bare hex digest)
    is skipped at its post-image and written over its pre-image, never a conflict."""

    import hashlib

    def bare(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    root = tmp_path / "tree"
    root.mkdir()
    (root / "a.yaml").write_text("before\n", encoding="utf-8")
    target = {"rel_path": "a.yaml", "pre_hash": bare(b"before\n"), "post_content": "after\n",
              "post_hash": bare(b"after\n")}
    replaced = _count_replaces(monkeypatch)

    assert apply_protocol.target_conflicts(root, [target]) == []
    materialize_targets(root, [target])
    assert (root / "a.yaml").read_text(encoding="utf-8") == "after\n"
    assert apply_protocol.target_conflicts(root, [target]) == []
    materialize_targets(root, [target])  # at the post-image: skipped
    assert replaced == [str(root / "a.yaml")]


# --- P-fail 2: the next sidecar bind finishes a crash between two renames --------------------------------------------


def test_a_crash_between_two_renames_is_completed_at_the_next_sidecar_bind(tmp_path):
    paths = create_vault_registering_application(tmp_path / "vault")
    repository = _repo(paths)
    _seed_lo_and_pi_proposal(repository)
    _crash_after(paths, renamed=1)
    loaded = load_vault(paths.root)
    assert (LO_ID in loaded.learning_objects) != (PI_ID in loaded.practice_items)  # half-applied

    responses = _initialize(paths)
    assert "error" not in responses[0], responses[0]

    loaded = load_vault(paths.root)
    assert LO_ID in loaded.learning_objects and PI_ID in loaded.practice_items
    assert repository.pending_apply_intents() == []
    assert repository.outstanding_apply_intents() == []
    assert repository.proposal_item("item_lo")["decision"] == "accepted"
    assert repository.proposal_item("item_pi")["decision"] == "accepted"


def test_a_bind_with_nothing_pending_takes_no_apply_lock(tmp_path, monkeypatch):
    import learnloop.vault_lock as vault_lock

    paths = create_vault_registering_application(tmp_path / "vault")
    purposes: list[str] = []
    real = vault_lock.vault_mutation_lock

    def recording(root, *args, **kwargs):
        purposes.append(kwargs.get("purpose", ""))
        return real(root, *args, **kwargs)

    monkeypatch.setattr(vault_lock, "vault_mutation_lock", recording)
    assert recover_apply_intents(paths.root, _repo(paths)) == []
    responses = _initialize(paths)
    assert "error" not in responses[0], responses[0]
    assert "recover_apply_intents" not in purposes


def test_a_bind_leaves_a_conflicted_intent_for_the_owner_and_opens(tmp_path):
    paths = create_vault_registering_application(tmp_path / "vault")
    repository = _repo(paths)
    _seed_lo_and_pi_proposal(repository)
    _crash_after(paths, renamed=1)
    first = _pending_intent(repository)["targets"][0]
    edited = _hand_edit(paths, first)

    responses = _initialize(paths)

    assert "error" not in responses[0], responses[0]
    assert (paths.root / first["rel_path"]).read_text(encoding="utf-8") == edited
    assert [row["status"] for row in repository.outstanding_apply_intents()] == ["conflicted"]


# --- P-fail 3: an accept with an outstanding intent is refused --------------------------------------------------------


def test_an_accept_with_a_pending_intent_is_refused(tmp_path):
    paths = create_vault_registering_application(tmp_path / "vault")
    repository = _repo(paths)
    _seed_lo_and_pi_proposal(repository)
    _crash_after(paths, renamed=0)  # intent committed, nothing renamed
    intent = _pending_intent(repository)
    _seed_lo_and_pi_proposal_two(repository)

    with pytest.raises(OutstandingApplyIntentError) as raised:
        apply_accepted_items(paths.root, "patch_two")

    assert isinstance(raised.value, PatchApplicationError)  # every existing catch site still handles it
    assert raised.value.intents == [{"id": intent["id"], "status": "pending", "proposed_patch_id": "patch_wa",
                                     "paths": []}]
    assert "doctor --fix-state" in str(raised.value)
    assert repository.proposal_item("item_lo_two")["decision"] == "pending"
    assert len(repository.pending_apply_intents()) == 1  # no second intent was written


def test_the_sidecar_accept_names_the_outstanding_intent(tmp_path):
    paths = create_vault_registering_application(tmp_path / "vault")
    repository = _repo(paths)
    _seed_lo_and_pi_proposal(repository)
    _crash_after(paths, renamed=1)
    first = _pending_intent(repository)["targets"][0]
    _hand_edit(paths, first)
    _seed_lo_and_pi_proposal_two(repository)

    responses = _initialize(paths, {"method": "accept_proposal_items", "params": {"patchId": "patch_two"}})

    error = responses[1]["error"]
    assert error["data"]["code"] == "apply_intent_outstanding"
    (named,) = error["data"]["details"]["intents"]
    assert named["status"] == "conflicted" and named["paths"] == [first["rel_path"]]
    assert "Keep the files as they are" in error["message"]


# --- D-10: an undo is refused as an accept is ---------------------------------------------------------------------------


def _applied_two_then_crash(paths: VaultPaths, repository: Repository, *, renamed: int) -> None:
    """``patch_two`` applied cleanly, then ``patch_wa``'s apply crashes after ``renamed`` renames."""

    _seed_lo_and_pi_proposal_two(repository)
    apply_accepted_items(paths.root, "patch_two")
    _seed_lo_and_pi_proposal(repository)
    _crash_after(paths, renamed=renamed)


def test_an_undo_with_a_pending_intent_is_refused(tmp_path):
    """Reverting applied items writes vault files, so it must not run over a
    half-applied vault any more than an accept may."""

    from learnloop.content.proposals.patches import reject_applied_items
    from learnloop.content.proposals.proposals import reject_items

    paths = create_vault_registering_application(tmp_path / "vault")
    repository = _repo(paths)
    _applied_two_then_crash(paths, repository, renamed=0)
    intent = _pending_intent(repository)
    applied = {path: path.read_bytes() for path in paths.root.rglob("*.yaml")}

    for undo in (lambda: reject_applied_items(paths.root, "patch_two"), lambda: reject_items(paths.root, "patch_two")):
        with pytest.raises(OutstandingApplyIntentError) as raised:
            undo()
        assert [named["id"] for named in raised.value.intents] == [intent["id"]]
        assert str(raised.value).startswith("Refusing to undo")

    assert repository.proposal_item("item_lo_two")["decision"] == "accepted"
    assert {path: path.read_bytes() for path in paths.root.rglob("*.yaml")} == applied


def test_the_sidecar_reject_names_the_outstanding_intent(tmp_path):
    paths = create_vault_registering_application(tmp_path / "vault")
    repository = _repo(paths)
    _applied_two_then_crash(paths, repository, renamed=1)
    first = _pending_intent(repository)["targets"][0]
    _hand_edit(paths, first)  # conflicted at the bind, so it is still outstanding after it

    responses = _initialize(paths, {"method": "reject_proposal_items", "params": {"patchId": "patch_two"}})

    error = responses[1]["error"]
    assert error["data"]["code"] == "apply_intent_outstanding"
    (named,) = error["data"]["details"]["intents"]
    assert named["status"] == "conflicted" and named["paths"] == [first["rel_path"]]
    assert repository.proposal_item("item_lo_two")["decision"] == "accepted"


def test_the_book_cards_undo_is_refused_before_it_changes_anything(tmp_path):
    """The card's Undo advances the book's generation and cancels its builds
    before it reverts; refused, it does none of that."""

    from learnloop_sidecar.errors import SidecarError

    from tests.ux_phase1_add_source_helpers import _draining_ctx, call
    from tests.ux_phase1_support import fresh_library, grant_consent, write_book

    root = fresh_library(tmp_path)
    grant_consent(root)
    ctx = _draining_ctx(root)
    source_id = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})["items"][0]["sourceId"]
    generation = ctx.repository.source_auto_build_state(source_id)["generation"]
    intent_id = ctx.repository.insert_apply_intent(proposed_patch_id="patch_elsewhere", item_ids=[], targets=[],
                                                   db_plan=[])

    with pytest.raises(SidecarError) as raised:
        call(ctx, "source_action", {"sourceId": source_id, "action": "undo_questions"})

    assert raised.value.code == "apply_intent_outstanding"
    assert [named["id"] for named in raised.value.details["intents"]] == [intent_id]
    assert ctx.repository.source_auto_build_state(source_id)["generation"] == generation
    card = next(c for c in call(ctx, "get_source_library", {})["sources"] if c["sourceId"] == source_id)
    assert card["statusLine"]["text"] == "Questions for Ch. 1–2 come up as you read"


# --- W6: recovery recalibrates ----------------------------------------------------------------------------------------


def _recalibration_markers(paths: VaultPaths) -> int:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM derived_state_rebuilds WHERE learning_object_ids_json LIKE ?", (f"%{LO_ID}%",)
        ).fetchone()[0]


def test_recovery_runs_the_content_recalibration(tmp_path):
    paths = create_vault_registering_application(tmp_path / "vault")
    repository = _repo(paths)
    _seed_lo_and_pi_proposal(repository)
    _crash_after(paths, renamed=2)  # every file renamed, nothing in the database yet
    assert _recalibration_markers(paths) == 0

    assert len(recover_apply_intents(paths.root, repository)) == 1

    assert _recalibration_markers(paths) == 1  # the marker the apply itself stamps


def test_the_apply_recalibrates_before_it_marks_the_intent_applied(tmp_path, monkeypatch):
    paths = create_vault_registering_application(tmp_path / "vault")
    repository = _repo(paths)
    _seed_lo_and_pi_proposal(repository)

    def crash(*_args, **_kwargs):
        raise RuntimeError("simulated crash after the effects (W6)")

    monkeypatch.setattr(Repository, "mark_apply_intent_applied", crash)
    with pytest.raises(RuntimeError):
        apply_accepted_items(paths.root, "patch_wa")
    monkeypatch.undo()
    assert _recalibration_markers(paths) == 1
    assert len(repository.pending_apply_intents()) == 1  # still pending: recovery redoes it whole
    assert len(recover_apply_intents(paths.root, repository)) == 1
    assert repository.outstanding_apply_intents() == []


# --- the normal path: a file changed under the accept -----------------------------------------------------------------


def test_an_accept_whose_target_changes_under_it_writes_nothing_and_rolls_back(tmp_path, monkeypatch):
    paths = create_vault_registering_application(tmp_path / "vault")
    repository = _repo(paths)
    _seed_lo_and_pi_proposal(repository)
    real_stage = apply_protocol.stage_target_contents

    def stage_then_race(*args, **kwargs):
        targets, db_plan = real_stage(*args, **kwargs)
        # A writer that bypassed the vault lock creates one target between staging and the rename.
        (paths.root / targets[0]["rel_path"]).write_text("# raced\n", encoding="utf-8")
        return targets, db_plan

    monkeypatch.setattr(apply_protocol, "stage_target_contents", stage_then_race)
    with pytest.raises(PatchApplicationError, match="nothing was written"):
        apply_accepted_items(paths.root, "patch_wa")
    monkeypatch.undo()

    assert repository.outstanding_apply_intents() == []  # rolled back: it wrote nothing, so it blocks nothing
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        assert [row[0] for row in connection.execute("SELECT status FROM apply_intents")] == ["rolled_back"]
    assert repository.proposal_item("item_lo")["decision"] == "pending"


def _edit_live_file_during_staging(monkeypatch, path: Path, text: str) -> None:
    """A writer that bypassed the vault lock changes ``path`` once, after staging copied the vault and before it diffs."""

    from learnloop.content.proposals import patches

    real_compile = patches.compile_proposal_item
    done: list[bool] = []

    def compile_then_race(*args, **kwargs):
        if not done:
            done.append(True)
            path.write_text(text, encoding="utf-8")
        return real_compile(*args, **kwargs)

    monkeypatch.setattr(patches, "compile_proposal_item", compile_then_race)


def test_a_file_edited_while_staging_ran_is_not_overwritten_with_the_stale_copy(tmp_path, monkeypatch):
    """The staged copy of a file no item touches is not a target: an edit made after the staging copy survives
    the apply instead of being replaced by what staging read."""

    paths = create_vault_registering_application(tmp_path / "vault")
    repository = _repo(paths)
    _seed_lo_and_pi_proposal(repository)
    unrelated = paths.root / "profile" / "goals.md"
    _edit_live_file_during_staging(monkeypatch, unrelated, "# edited while the apply staged\n")

    apply_accepted_items(paths.root, "patch_wa")

    assert unrelated.read_text(encoding="utf-8") == "# edited while the apply staged\n"
    assert repository.proposal_item("item_lo")["decision"] == "accepted"


def test_a_target_changed_while_staging_ran_is_refused_and_keeps_the_edit(tmp_path, monkeypatch):
    """A file an item does change, edited after staging read it, is a target whose pre-image is what staging
    read: the apply writes nothing and rolls back, as when it changes after staging returns."""

    paths = create_vault_registering_application(tmp_path / "vault")
    repository = _repo(paths)
    _seed_lo_and_pi_proposal(repository)
    lo_file = paths.root / "subjects/linear-algebra/learning-objects" / f"{LO_ID}.yaml"
    assert not lo_file.exists()
    _edit_live_file_during_staging(monkeypatch, lo_file, "# written by hand while the apply staged\n")

    with pytest.raises(PatchApplicationError, match="nothing was written"):
        apply_accepted_items(paths.root, "patch_wa")

    assert lo_file.read_text(encoding="utf-8") == "# written by hand while the apply staged\n"
    assert repository.outstanding_apply_intents() == []
    assert repository.proposal_item("item_lo")["decision"] == "pending"


def test_only_the_files_the_items_change_become_targets(tmp_path, monkeypatch):
    """A file edited during staging that no item touches is no target at all, so a retry applies cleanly."""

    paths = create_vault_registering_application(tmp_path / "vault")
    repository = _repo(paths)
    _seed_lo_and_pi_proposal(repository)
    unrelated = paths.root / "profile" / "goals.md"
    _edit_live_file_during_staging(monkeypatch, unrelated, "# edited while the apply staged\n")
    requested = repository.pending_proposal_items("patch_wa")
    ordered_ids, _blocked = apply_protocol.compute_dependency_closure(repository, requested)
    by_id = {item["id"]: item for item in requested}

    targets, _plan = apply_protocol.stage_target_contents(
        paths.root, load_vault(paths.root), [by_id[item_id] for item_id in ordered_ids], "codex", "patch_wa", clock=None
    )

    assert "profile/goals.md" not in {target["rel_path"] for target in targets}
    assert unrelated.read_text(encoding="utf-8") == "# edited while the apply staged\n"


# --- the maintenance action's handler and the owner's settlement ------------------------------------------------------


def _conflicted_vault(tmp_path) -> tuple[VaultPaths, Repository, dict, str]:
    paths = create_vault_registering_application(tmp_path / "vault")
    repository = _repo(paths)
    _seed_lo_and_pi_proposal(repository)
    _crash_after(paths, renamed=1)
    intent = _pending_intent(repository)
    edited = _hand_edit(paths, intent["targets"][0])
    recover_apply_intents(paths.root, repository)
    return paths, repository, intent, edited


def test_doctor_and_the_feed_surface_a_conflicted_intent(tmp_path):
    from learnloop.ops.doctor import run_doctor
    from learnloop.ops.maintenance_feed import generate_maintenance_feed

    paths, repository, intent, edited = _conflicted_vault(tmp_path)
    rel_path = intent["targets"][0]["rel_path"]

    for fix_state in (False, True):
        report = run_doctor(paths.root, fix_state=fix_state)
        (issue,) = [issue for issue in report.issues if issue.code == "apply_intents:conflicted"]
        assert issue.severity == "error" and rel_path in issue.message
        assert (paths.root / rel_path).read_text(encoding="utf-8") == edited  # --fix-state too

    feed = generate_maintenance_feed(load_vault(paths.root), repository)
    (notice,) = [notice for notice in feed if notice["notice_type"] == "apply_conflicted"]
    assert notice["severity"] == "action_needed"
    assert notice["action"] == {"action": "resolve_apply_intent", "label": "Keep the files as they are",
                                "intent_id": intent["id"], "resolution": "keep_files"}
    assert notice["detail"]["paths"] == [rel_path]


def test_keep_files_sets_the_intent_aside_and_accepts_open_again(tmp_path):
    from learnloop.ops.maintenance_feed import generate_maintenance_feed

    paths, repository, intent, edited = _conflicted_vault(tmp_path)
    rel_path = intent["targets"][0]["rel_path"]

    responses = _initialize(paths, {"method": "resolve_apply_intent",
                                    "params": {"intentId": intent["id"], "resolution": "keep_files"}})

    assert responses[1]["result"]["intent"]["status"] == "set_aside", responses[1]
    assert (paths.root / rel_path).read_text(encoding="utf-8") == edited
    assert repository.outstanding_apply_intents() == []
    assert repository.proposal_item("item_lo")["decision"] == "pending"  # the items wait for review
    feed = generate_maintenance_feed(load_vault(paths.root), repository)
    assert not [notice for notice in feed if notice["notice_type"] == "apply_conflicted"]  # the notice clears
    with pytest.raises(ApplyIntentResolutionError):
        resolve_apply_intent(paths.root, repository, intent["id"], "keep_files")  # settled once

    _seed_lo_and_pi_proposal_two(repository)
    assert apply_accepted_items(paths.root, "patch_two").applied_count == 2


def test_complete_finishes_a_pending_intent_and_rechecks_a_conflicted_one(tmp_path):
    paths, repository, intent, _edited = _conflicted_vault(tmp_path)
    first = intent["targets"][0]

    still = resolve_apply_intent(paths.root, repository, intent["id"], "complete")
    assert still["status"] == "conflicted"  # the file still differs: nothing written

    (paths.root / first["rel_path"]).write_text(first["post_content"], encoding="utf-8")  # put back by hand
    done = resolve_apply_intent(paths.root, repository, intent["id"], "complete")
    assert done["status"] == "applied"
    assert repository.proposal_item("item_pi")["decision"] == "accepted"
    with pytest.raises(ApplyIntentResolutionError):
        resolve_apply_intent(paths.root, repository, intent["id"], "complete")


def _seed_lo_and_pi_proposal_two(repository: Repository) -> None:
    """A second, independent proposal (another LO) to try to accept beside the outstanding one."""

    from tests.helpers import NOW_ISO

    repository.insert_agent_run({"id": "agent_two", "purpose": "authoring", "provider": "fake",
                                 "output_schema": "AuthoringProposal", "started_at": NOW_ISO, "status": "completed",
                                 "completed_at": NOW_ISO})
    lo = {"id": "lo_svd_two", "title": "SVD two", "subjects": ["linear-algebra"],
          "concept_id": "singular_value_decomposition", "knowledge_type": "application",
          "summary": "A second SVD object."}
    pi = {"id": "pi_svd_two_001", "learning_object_id": "lo_svd_two", "subjects": None,
          "practice_mode": "short_answer", "attempt_types_allowed": ["independent_attempt"],
          "evidence_facets": ["application"], "evidence_weights": {"application": 1.0},
          "prompt": "Name another use of SVD.", "expected_answer": "Principal component analysis.",
          "grading_rubric": {"max_points": 4, "criteria": [{"id": "correctness", "points": 4,
                                                            "description": "Names a real use."}],
                             "fatal_errors": []}}
    repository.persist_proposal_batch(
        {"id": "patch_two", "agent_run_id": "agent_two", "purpose": "authoring", "source_refs": [],
         "summary": "Second SVD LO + item", "created_at": NOW_ISO},
        [
            {"id": "item_lo_two", "client_item_id": "client_lo_two", "item_type": "learning_object",
             "operation": "create", "payload": lo, "validation_status": "valid", "validation_errors": [],
             "created_at": NOW_ISO},
            {"id": "item_pi_two", "client_item_id": "client_pi_two", "item_type": "practice_item",
             "operation": "create", "payload": pi, "depends_on_client_item_ids": ["client_lo_two"],
             "validation_status": "valid", "validation_errors": [], "created_at": NOW_ISO},
        ],
    )
