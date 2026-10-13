"""S1 (G7): an imported exercise joins a matching family, append-only, with undo and recovery."""
from __future__ import annotations

import pytest

from learnloop.content.authoring import source_exercise_import as SEI
from learnloop.substrate.families import apply_family, attach_to_family, undo_family
from learnloop.vault.models import ActivityFamily
from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, loaded, service_clients


def _family(paths, repository, members=("pi_eigen_1",), family_id="fam_eigen", lo="lo_matrices"):
    vault = loaded(paths)
    family = ActivityFamily(id=family_id, learning_object_id=lo, idea_statement="find an eigenvalue",
                            retrieval_target="solve for the eigenvalue",
                            created_at="2026-10-12T00:00:00Z", updated_at="2026-10-12T00:00:00Z")
    apply_family(vault, repository, family, {member: "same_target" for member in members},
                 proposal_id=f"fp_{family_id}", judge="owner", rationale="test family")
    return family


def _memberships(repository):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(
            "SELECT family_id, practice_item_id, variant_relation, action FROM activity_family_membership_events "
            "ORDER BY seq")]


def test_a_matching_family_is_joined_and_undone(tmp_path):
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    _family(paths, repository)
    result = SEI.import_source_exercise(paths.root, repository, extraction_id="ext_text",
                                       span_ids=[spans["exercises"][1]], caller="learner",
                                       clients=service_clients(FakeServiceLLM(family_verdict="same")))
    assert result["family"]["status"] == "attached"
    item = loaded(paths).practice_items[result["practice_item_id"]]
    assert (item.family_id, item.variant_relation) == ("fam_eigen", "isomorph")
    assert ("fam_eigen", item.id, "isomorph", "add") in _memberships(repository)
    with repository.connection() as connection:
        judged = connection.execute("SELECT COUNT(*) FROM judgment_ledger WHERE task='same_target'").fetchone()[0]
    assert judged == 2  # both passes for the one pair
    undo_family(loaded(paths), repository, result["family"]["family_proposal_id"])
    item = loaded(paths).practice_items[result["practice_item_id"]]
    assert item.family_id is None and item.variant_relation is None
    assert ("fam_eigen", item.id, "isomorph", "remove") in _memberships(repository)


def test_no_matching_family_leaves_the_item_unfamilied(tmp_path):
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    _family(paths, repository)
    result = SEI.import_source_exercise(paths.root, repository, extraction_id="ext_text",
                                       span_ids=[spans["exercises"][1]], caller="learner",
                                       clients=service_clients(FakeServiceLLM(family_verdict="different")))
    assert result["family"]["status"] == "unfamilied"
    assert loaded(paths).practice_items[result["practice_item_id"]].family_id is None


def test_attach_refuses_an_lo_mismatch_and_missing_judgments(tmp_path):
    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    _family(paths, repository)
    vault = loaded(paths)
    with pytest.raises(ValueError, match="learning object"):
        attach_to_family(vault, repository, "fam_eigen", "pi_span_1", "isomorph", proposal_id="fpa_x",
                         judgment_ids=[])
    with pytest.raises(ValueError, match="two agreeing judge passes"):
        attach_to_family(vault, repository, "fam_eigen", "pi_eigen_2", "isomorph", proposal_id="fpa_y",
                         judgment_ids=[])
    with pytest.raises(ValueError, match="Only same_target or isomorph"):
        attach_to_family(vault, repository, "fam_eigen", "pi_eigen_2", "near", proposal_id="fpa_z",
                         judgment_ids=[])


def test_attach_switch_off_skips_the_judge(tmp_path):
    from tests.source_service_fakes import set_config

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    _family(paths, repository)
    set_config(paths, "source_service", family_attachment=False)
    llm = FakeServiceLLM(family_verdict="same")
    result = SEI.import_source_exercise(paths.root, repository, extraction_id="ext_text",
                                       span_ids=[spans["exercises"][1]], caller="learner",
                                       clients=service_clients(llm))
    assert result["family"] == {"status": "disabled"}
    assert "FamilyVerdict" not in {name for _purpose, name in llm.calls}
