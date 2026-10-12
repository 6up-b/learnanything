from __future__ import annotations

import json
import sqlite3

import pytest
from pydantic import create_model

from learnloop.db.repositories import Repository
from learnloop.db.stores.families import current_memberships, record_revision
from learnloop.db.stores.judgments import append_judgment
from learnloop.substrate.activities import resolve_legacy_item
from learnloop.substrate.families import FAMILY_JUDGE_PROMPTS, apply_family, family_item_input_hash, recover_family_operations, sync_authored_families, undo_family
from learnloop.vault.hashes import practice_item_hash
from learnloop.vault.loader import load_vault
from learnloop.vault.models import ActivityFamily, PracticeItem, VaultModel
from learnloop.vault.writer import upsert_activity_family
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.helpers import NOW_ISO, create_basic_vault


def setup_family(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    item = vault.practice_items["pi_svd_define_001"]
    family = ActivityFamily(id="family_svd", learning_object_id=item.learning_object_id,
                            idea_statement="SVD", retrieval_target="State the decomposition",
                            created_at=NOW_ISO, updated_at=NOW_ISO)
    return paths, vault, repository, item, family


def test_absent_fields_are_byte_identical_to_pre_family_model(tmp_path):
    _, _, _, item, _ = setup_family(tmp_path)
    old = create_model("OldPracticeItem", __base__=VaultModel, **{
        name: (field.annotation, field)
        for name, field in PracticeItem.model_fields.items()
        if name not in {"family_id", "variant_relation"}
    }).model_validate(item.model_dump())
    assert old.model_dump() == item.model_dump()
    assert old.model_dump_json() == item.model_dump_json()
    explicit_none = item.model_copy(update={"family_id": None, "variant_relation": None})
    assert explicit_none.model_dump_json() == old.model_dump_json()
    grouped = item.model_copy(update={"family_id": "f", "variant_relation": "same_target"})
    assert practice_item_hash(item) == practice_item_hash(grouped)
    assert json.loads(grouped.model_dump_json())["family_id"] == "f"


@pytest.mark.parametrize("collision", ["seq", "id", "proposal_card_action"])
def test_membership_replace_cannot_rewrite_history(tmp_path, collision):
    _, vault, repository, item, family = setup_family(tmp_path)
    apply_family(vault, repository, family, {item.id: "same_target"}, proposal_id="p")
    with repository.connection() as connection:
        connection.execute("PRAGMA recursive_triggers=OFF")
        original = dict(connection.execute("SELECT * FROM activity_family_membership_events").fetchone())
        replacement = {**original, "variant_relation": "far"}
        if collision != "seq":
            replacement["seq"] += 1
        if collision != "id":
            replacement["id"] = "replacement"
        if collision != "proposal_card_action":
            replacement["proposal_id"] = "another"
        columns = ",".join(replacement)
        placeholders = ",".join("?" for _ in replacement)
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                f"INSERT OR REPLACE INTO activity_family_membership_events ({columns}) VALUES ({placeholders})",
                tuple(replacement.values()),
            )
        assert dict(connection.execute("SELECT * FROM activity_family_membership_events").fetchone()) == original


@pytest.mark.parametrize("reset", [False, True])
def test_undo_uses_immutable_plan_not_workflow(tmp_path, reset):
    _, vault, repository, family, members, ids = judged_pair(tmp_path)
    apply_family(vault, repository, family, members, proposal_id="p", judge="verifier", judgment_ids=ids)
    with repository.connection() as connection:
        decision = connection.execute("SELECT * FROM judgment_ledger WHERE verdict='accept'").fetchone()
        plan = json.loads(decision["rationale"])["plan"]
        assert plan["judgment_ids"] == ids
        assert plan["family"] == family.model_dump(mode="json")
        assert len(plan["patches"]) == 3
        if reset:
            connection.execute("DELETE FROM family_proposals")
        else:
            connection.execute("UPDATE family_proposals SET plan_json='{}',state='undone'")
    undo_family(vault, repository, "p")
    with repository.connection() as connection:
        assert not current_memberships(connection)
        assert connection.execute("SELECT state FROM family_proposals").fetchone()[0] == "undone"
        assert connection.execute("SELECT COUNT(*) FROM judgment_ledger WHERE verdict='undo'").fetchone()[0] == 1
        connection.execute("DELETE FROM family_proposals")
    undo_family(vault, repository, "p")
    assert all(vault.practice_items[item_id].family_id is None for item_id in members)


def test_undo_does_not_revert_owner_family_revision(tmp_path):
    paths, vault, repository, item, family = setup_family(tmp_path)
    apply_family(vault, repository, family, {item.id: "same_target"}, proposal_id="p")
    edited = family.model_copy(update={"idea_statement": "Owner revised idea"})
    upsert_activity_family(paths.root, edited)
    sync_authored_families(vault, repository)
    undo_family(vault, repository, "p")
    with repository.connection() as connection:
        versions = connection.execute(
            "SELECT family_spec_json FROM activity_family_versions WHERE family_id=? ORDER BY version",
            (family.id,),
        ).fetchall()
    assert len(versions) == 2
    assert json.loads(versions[-1][0])["idea_statement"] == edited.idea_statement


@pytest.mark.parametrize("failure_at", [1, 2, 3])
def test_interrupted_apply_can_abort_after_owner_edit(tmp_path, monkeypatch, failure_at):
    from learnloop.substrate import families
    paths, vault, repository, family, members, ids = judged_pair(tmp_path)
    original = families._write_atomic
    calls = 0

    def interrupted(path, data):
        nonlocal calls
        calls += 1
        if calls == failure_at:
            raise OSError("power failure")
        original(path, data)

    monkeypatch.setattr(families, "_write_atomic", interrupted)
    with pytest.raises(OSError):
        apply_family(vault, repository, family, members, proposal_id="p", judge="verifier", judgment_ids=ids)
    monkeypatch.setattr(families, "_write_atomic", original)
    item_id = sorted(members)[0]
    path = paths.practice_item_path("linear-algebra", item_id)
    data = read_yaml(path)
    data["prompt"] = "Owner changed the judged prompt"
    write_yaml(path, data)
    with pytest.raises(ValueError, match="learnloop families undo p"):
        recover_family_operations(vault, repository)
    with repository.connection() as connection:
        connection.execute("DELETE FROM family_proposals")
    undo_family(vault, repository, "p")
    assert vault.practice_items[item_id].prompt == data["prompt"]
    assert all(vault.practice_items[i].family_id is None for i in members)
    with repository.connection() as connection:
        assert not current_memberships(connection)
        assert connection.execute("SELECT state FROM family_proposals").fetchone()[0] == "undone"
        decisions = connection.execute(
            "SELECT verdict,judge FROM judgment_ledger WHERE task='family_decision' ORDER BY rowid"
        ).fetchall()
        assert [tuple(row) for row in decisions] == [("accept", "verifier"), ("undo", "owner")]


def test_family_schema_and_loader_relationships(tmp_path):
    paths, vault, _, item, family = setup_family(tmp_path)
    for reference in ({"verification": "assumed"}, {"verification": "verified"}):
        with pytest.raises(ValueError):
            ActivityFamily.model_validate({**family.model_dump(), "reference": reference})
    valid = ActivityFamily.model_validate({
        **family.model_dump(), "reference": {"verification": "verified", "check": "Owner checked source"},
    })
    assert valid.reference.verification == "verified"
    with pytest.raises(ValueError, match="specified together"):
        PracticeItem.model_validate({**item.model_dump(), "family_id": family.id})
    path = paths.practice_item_path("linear-algebra", item.id)
    write_yaml(path, {**item.model_dump(mode="json"), "family_id": family.id, "variant_relation": "same_target"})
    loaded = load_vault(paths.root)
    assert "practice_item:missing_activity_family" in {issue.code for issue in loaded.issues}
    write_yaml(paths.activity_family_path("linear-algebra", family.id),
               {**family.model_dump(mode="json"), "learning_object_id": "missing"})
    loaded = load_vault(paths.root)
    assert {"activity_family:missing_learning_object", "practice_item:family_learning_object_mismatch"} <= {
        issue.code for issue in loaded.issues
    }


def test_apply_undo_preserves_cards_and_owner_edits(tmp_path):
    paths, vault, repository, item, family = setup_family(tmp_path)
    before = {purpose: resolve_legacy_item(vault, repository, item, purpose=purpose)
              for purpose in ("practice", "diagnostic", "assessment")}
    apply_family(vault, repository, family, {item.id: "same_target"}, proposal_id="p")
    for purpose, previous in before.items():
        assert resolve_legacy_item(vault, repository, vault.practice_items[item.id], purpose=purpose) == previous
    path = paths.practice_item_path("linear-algebra", item.id)
    data = read_yaml(path)
    data["prompt"] = "Owner edit after acceptance"
    write_yaml(path, data)
    undo_family(vault, repository, "p")
    undo_family(vault, repository, "p")
    assert vault.practice_items[item.id].prompt == "Owner edit after acceptance"
    assert vault.practice_items[item.id].family_id is None
    assert family.id in vault.activity_families
    with repository.connection() as connection:
        assert current_memberships(connection) == []
        assert [r["action"] for r in connection.execute("SELECT action FROM activity_family_membership_events ORDER BY seq")] == ["add", "remove"]
        assert [r["verdict"] for r in connection.execute("SELECT verdict FROM judgment_ledger ORDER BY rowid")] == ["accept", "undo"]
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("UPDATE activity_family_membership_events SET action='remove'")


def test_recovery_after_partial_vault_write(tmp_path, monkeypatch):
    from learnloop.substrate import families
    _, vault, repository, item, family = setup_family(tmp_path)
    original = families._write_atomic
    calls = 0

    def interrupted(path, data):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("power failure")
        original(path, data)

    monkeypatch.setattr(families, "_write_atomic", interrupted)
    with pytest.raises(OSError, match="power failure"):
        apply_family(vault, repository, family, {item.id: "same_target"}, proposal_id="p")
    monkeypatch.setattr(families, "_write_atomic", original)
    recover_family_operations(vault, repository)
    assert vault.practice_items[item.id].family_id == family.id
    with repository.connection() as connection:
        assert len(current_memberships(connection)) == 1
        assert connection.execute("SELECT COUNT(*) FROM judgment_ledger").fetchone()[0] == 1


def test_undo_conflicting_membership_is_not_overwritten(tmp_path):
    paths, vault, repository, item, family = setup_family(tmp_path)
    apply_family(vault, repository, family, {item.id: "same_target"}, proposal_id="p")
    path = paths.practice_item_path("linear-algebra", item.id)
    data = read_yaml(path)
    data["family_id"] = "owner_reassigned"
    write_yaml(path, data)
    with pytest.raises(ValueError, match="Owner edit conflicts"):
        undo_family(vault, repository, "p")
    assert read_yaml(path)["family_id"] == "owner_reassigned"


def test_authored_family_versions(tmp_path):
    paths, vault, repository, _, family = setup_family(tmp_path)
    path = upsert_activity_family(paths.root, family)
    sync_authored_families(vault, repository)
    edited = family.model_copy(update={"idea_statement": "Owner revision"})
    upsert_activity_family(paths.root, edited)
    sync_authored_families(vault, repository)
    sync_authored_families(vault, repository)
    assert path.exists()
    with repository.connection() as connection:
        rows = connection.execute("SELECT * FROM activity_family_versions WHERE family_id=? ORDER BY version", (family.id,)).fetchall()
        assert len(rows) == 2
        assert json.loads(rows[1]["family_spec_json"])["idea_statement"] == "Owner revision"


def test_undo_recovery_after_membership_file_write(tmp_path, monkeypatch):
    from learnloop.substrate import families
    _, vault, repository, item, family = setup_family(tmp_path)
    apply_family(vault, repository, family, {item.id: "same_target"}, proposal_id="p")
    original = families.append_membership

    def interrupted(*args, **kwargs):
        raise OSError("completion failed")

    monkeypatch.setattr(families, "append_membership", interrupted)
    with pytest.raises(OSError, match="completion failed"):
        undo_family(vault, repository, "p")
    monkeypatch.setattr(families, "append_membership", original)
    recover_family_operations(vault, repository)
    assert vault.practice_items[item.id].family_id is None
    with repository.connection() as connection:
        assert current_memberships(connection) == []
        assert connection.execute("SELECT COUNT(*) FROM judgment_ledger").fetchone()[0] == 2


def test_apply_idempotency_rejects_changed_payload(tmp_path):
    _, vault, repository, item, family = setup_family(tmp_path)
    apply_family(vault, repository, family, {item.id: "same_target"}, proposal_id="p")
    apply_family(vault, repository, family, {item.id: "same_target"}, proposal_id="p")
    with pytest.raises(ValueError, match="another family operation"):
        apply_family(vault, repository, family, {item.id: "near"}, proposal_id="p")
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM judgment_ledger").fetchone()[0] == 1


def judged_pair(tmp_path):
    paths, vault, repository, item, family = setup_family(tmp_path)
    other = item.model_copy(update={"id": "pi_svd_other"})
    write_yaml(paths.practice_item_path("linear-algebra", other.id), other.model_dump(mode="json"))
    vault = load_vault(paths.root)
    members = {item.id: "same_target", other.id: "isomorph"}
    ids = []
    with repository.connection() as connection:
        for prompt in FAMILY_JUDGE_PROMPTS:
            ids.append(append_judgment(
                connection, task="same_target", left_kind="practice_item", left_id=item.id,
                right_kind="practice_item", right_id=other.id, judge="llm",
                judge_model="fake", prompt_version=prompt, input_hash="request-key",
                verdict="same", rationale=json.dumps({
                    "result": {"verdict": "same", "variant_relation": "isomorph",
                               "idea_statement": family.idea_statement, "retrieval_target": family.retrieval_target},
                    "item_hashes": {i: family_item_input_hash(vault, vault.practice_items[i]) for i in members},
                }),
            ))
    return paths, vault, repository, family, members, ids


def test_auto_family_requires_both_independent_passes(tmp_path):
    _, vault, repository, family, members, ids = judged_pair(tmp_path)
    with pytest.raises(ValueError, match="two agreeing"):
        apply_family(vault, repository, family, members, proposal_id="p",
                     judge="verifier", judgment_ids=ids[:1])
    apply_family(vault, repository, family, members, proposal_id="p",
                 judge="verifier", judgment_ids=ids)
    with repository.connection() as connection:
        assert len(current_memberships(connection)) == 2
        assert connection.execute(
            "SELECT prompt_version FROM judgment_ledger WHERE verdict='accept'"
        ).fetchone()[0] == "unanimous-components-v1"


@pytest.mark.parametrize("mutation", ["verdict", "relation", "members", "wording", "prompt"])
def test_verifier_rejects_unbound_acceptance(tmp_path, mutation):
    _, vault, repository, family, members, ids = judged_pair(tmp_path)
    if mutation == "members":
        members[max(members)] = "near"
    elif mutation == "wording":
        family = family.model_copy(update={"idea_statement": "Unjudged idea"})
    else:
        with repository.connection() as connection:
            old = connection.execute("SELECT * FROM judgment_ledger WHERE id=?", (ids[-1],)).fetchone()
            rationale = json.loads(old["rationale"])
            if mutation == "verdict":
                rationale["result"]["verdict"] = "different"
            elif mutation == "relation":
                rationale["result"]["variant_relation"] = "same_target"
            ids[-1] = append_judgment(
                connection, task="same_target", left_kind="practice_item", left_id=old["left_id"],
                right_kind="practice_item", right_id=old["right_id"], judge="llm",
                judge_model="fake", prompt_version="arbitrary" if mutation == "prompt" else old["prompt_version"],
                input_hash=old["input_hash"], verdict="same", rationale=json.dumps(rationale),
                supersedes_id=old["id"],
            )
    with pytest.raises(ValueError):
        apply_family(vault, repository, family, members, proposal_id="p", judge="verifier", judgment_ids=ids)
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM judgment_ledger WHERE verdict='accept'").fetchone()[0] == 0


@pytest.mark.parametrize("legacy_kind", ["practice_item", None])
def test_authored_identity_cannot_claim_legacy_family(tmp_path, legacy_kind):
    paths, vault, repository, item, family = setup_family(tmp_path)
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO activity_families(id,purpose,title,legacy_kind,created_at) VALUES (?,'practice',?,?,?)",
            (family.id, item.id, legacy_kind, NOW_ISO),
        )
        connection.execute(
            "INSERT INTO activity_family_versions(id,family_id,version,family_spec_json,created_at) VALUES (?,?,1,?,?)",
            ("legacy-version", family.id, json.dumps({"legacy_kind": "practice_item"}), NOW_ISO),
        )
        with pytest.raises(ValueError, match="collides"):
            record_revision(connection, family_id=family.id, spec_json=family.model_dump_json(),
                            title=family.idea_statement, created_at=NOW_ISO)
    with pytest.raises(ValueError, match="collides"):
        apply_family(vault, repository, family, {item.id: "same_target"}, proposal_id="p")
    assert not paths.activity_family_path("linear-algebra", family.id).exists()


def test_auto_family_rechecks_judged_content_from_disk(tmp_path):
    paths, vault, repository, family, members, ids = judged_pair(tmp_path)
    path = paths.practice_item_path("linear-algebra", next(iter(members)))
    data = read_yaml(path)
    data["prompt"] = "New prompt after judgments"
    write_yaml(path, data)
    with pytest.raises(ValueError, match="two agreeing"):
        apply_family(vault, repository, family, members, proposal_id="p",
                     judge="verifier", judgment_ids=ids)
    with repository.connection() as connection:
        assert not current_memberships(connection)
        assert connection.execute("SELECT COUNT(*) FROM family_proposals").fetchone()[0] == 0


def test_stale_loaded_vault_cannot_regroup_an_accepted_member(tmp_path):
    _, stale, repository, family, members, ids = judged_pair(tmp_path)
    current = load_vault(stale.root)
    apply_family(current, repository, family, members, proposal_id="p",
                 judge="verifier", judgment_ids=ids)
    replacement = family.model_copy(update={"id": "other_family"})
    with pytest.raises(ValueError, match="unfamilied"):
        apply_family(stale, repository, replacement, members, proposal_id="other",
                     judge="verifier", judgment_ids=ids)


def test_complete_link_cannot_chain_pair_judgments(tmp_path):
    paths, vault, repository, family, members, ids = judged_pair(tmp_path)
    third = next(iter(vault.practice_items.values())).model_copy(update={"id": "pi_third"})
    write_yaml(paths.practice_item_path("linear-algebra", third.id), third.model_dump(mode="json"))
    members[third.id] = "same_target"
    with pytest.raises(ValueError, match="two agreeing"):
        apply_family(vault, repository, family, members, proposal_id="p",
                     judge="verifier", judgment_ids=ids)


def test_ensemble_source_kind_loads_and_round_trips(tmp_path):
    """Review F10: spec §5.1 lists ``ensemble`` (PF-b's second generation path)."""
    paths, vault, _, _, family = setup_family(tmp_path)
    ensemble = family.model_copy(update={"source_kind": "ensemble"})
    ActivityFamily.model_validate(ensemble.model_dump(mode="json"))
    path = upsert_activity_family(paths.root, ensemble)
    assert read_yaml(path)["source_kind"] == "ensemble"
    loaded = load_vault(paths.root)
    assert loaded.activity_families[family.id].source_kind == "ensemble"
    assert not [issue for issue in loaded.issues if family.id in str(issue)]
