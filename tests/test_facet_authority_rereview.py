"""The facet-authority chokepoint, after its second Codex re-review (job ``20261013-095625-XzqNgm``).

The re-review of ``dd4e41af..ddf941d5`` confirmed F1, F3, F4, F5 and F6 fixed
and found two remaining defects:

* F2 (reopened): a write's ``meaning_support`` covered a recorded span by its
  ``(extraction_id, span_id)`` before the declared citation was validated. A
  declaration citing the exam span under the wrong unit fails resolution, yet
  it still kept the write's own exam ref from being judged, and the new facet
  compiled as ``new_unsupported``.
* F7: a Library save tracked its write-ahead state only through its reword
  rows, so a save with no reword (a new facet, a worked-example edit) killed
  between its committed verdicts and its registry write left those ``granted``
  verdicts standing for wording the registry never showed.
"""

from __future__ import annotations

import json

import pytest

from learnloop.content.facet_identity import actions as facet_actions
from learnloop.content.facet_identity import authority
from learnloop.content.proposals.patches import PatchApplicationError, apply_accepted_items
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, yaml_to_string

from tests.test_facet_authority import _CLOCK, EXAM_CLAIM, NEW_CLAIM, _facet_proposal, _support
from tests.test_facet_authority_review import _add_split_chapter, _authority_verdicts, _block_ref
from tests.test_facet_identity_actions import SELECT, SHARED, _vault_with_duplicate
from tests.test_source_set_synthesis import _setup

SPLIT_SCOPE = [{"unit_id": "chapter#Theory"}, {"unit_id": "chapter#Exam", "role_override": "exam"}]
EXAM_HALF_REF = _block_ref("ext_split", "s2", source_id="src_split", revision_id="rev_split")
THEORY_HALF_REF = _block_ref("ext_split", "s1", source_id="src_split", revision_id="rev_split")


# --- F2 (reopened): only a declared citation that resolves covers a recorded span ---------


@pytest.mark.parametrize("declared_unit", ["chapter#Theory", "chapter#Nowhere"])
def test_a_declared_citation_that_does_not_resolve_never_hides_the_writes_exam_ref(tmp_path, declared_unit):
    """The payload records the exam half (``s2``, selected under ``chapter#Exam``
    with ``role_override: exam``) and declares it under a unit that does not
    hold it. The declaration supports nothing, so the recorded exam ref is
    judged on its own: exam material alone, refused."""

    root, repo = _setup(tmp_path, with_exam=False)
    _add_split_chapter(repo, root, SPLIT_SCOPE)
    patch_id = _facet_proposal(repo, {
        "id": "facet_exam_misdeclared", "kind": "definition", "claim": EXAM_CLAIM,
        "provenance": {"origin": "sourceset_synthesis", "source_refs": [dict(EXAM_HALF_REF)]},
        "meaning_support": _support({"extraction_id": "ext_split", "unit_id": declared_unit, "span_id": "s2"},
                                    label="f_misdeclared"),
    }, operation="create")

    with pytest.raises(PatchApplicationError, match="exam"):
        apply_accepted_items(root, patch_id, clock=_CLOCK)

    assert "facet_exam_misdeclared" not in load_vault(root).evidence_facets


def test_a_declared_citation_covers_a_recorded_span_only_when_it_resolves(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    resolver = _add_split_chapter(repo, root, SPLIT_SCOPE)
    after = {"id": "f", "kind": "definition", "claim": EXAM_CLAIM,
             "provenance": {"source_refs": [dict(EXAM_HALF_REF)]}}
    misdeclared = {"meaning_support": _support({"extraction_id": "ext_split", "unit_id": "chapter#Theory",
                                                "span_id": "s2"}, label="f_misdeclared")}
    declared = {"meaning_support": _support({"extraction_id": "ext_split", "unit_id": "chapter#Exam",
                                             "span_id": "s2"}, label="f_declared")}

    contributed = authority.write_contributions(misdeclared, before=None, after=after, resolver=resolver)
    assert [item.label for item in contributed] == ["f_misdeclared", "provenance"]
    assert [(c["extraction_id"], c["span_id"]) for c in contributed[1].citations] == [("ext_split", "s2")]
    # Without a resolver nothing is validated, so nothing covers a recorded span.
    assert [item.label for item in authority.write_contributions(misdeclared, before=None, after=after)] == [
        "f_misdeclared", "provenance"]
    # A declaration that resolves still covers it (its own contribution judges it).
    contributed = authority.write_contributions(declared, before=None, after=after, resolver=resolver)
    assert [item.label for item in contributed] == ["f_declared"]


def test_a_write_declaring_both_halves_of_a_split_unit_under_their_own_units_applies(tmp_path):
    """Guard: the exam half declared under ``chapter#Exam`` beside the theory half
    under ``chapter#Theory`` is corroborated, and the facet is written."""

    root, repo = _setup(tmp_path, with_exam=False)
    _add_split_chapter(repo, root, SPLIT_SCOPE)
    patch_id = _facet_proposal(repo, {
        "id": "facet_split_corroborated", "kind": "definition", "claim": NEW_CLAIM,
        "provenance": {"origin": "sourceset_synthesis", "source_refs": [dict(THEORY_HALF_REF), dict(EXAM_HALF_REF)]},
        "meaning_support": _support(
            {"extraction_id": "ext_split", "unit_id": "chapter#Theory", "span_id": "s1"},
            {"extraction_id": "ext_split", "unit_id": "chapter#Exam", "span_id": "s2"}, label="f_both"),
    }, operation="create")

    apply_accepted_items(root, patch_id, clock=_CLOCK)

    assert load_vault(root).evidence_facets["facet_split_corroborated"].claim == NEW_CLAIM


# --- F7: every Library save with verdicts is a recoverable intent --------------------------


class _Killed(BaseException):
    """The process stops (not an exception the save could handle)."""


def _new_facet_only(document) -> str:
    document["facets"].append({"id": "facet_owner_written", "kind": "definition", "claim": "An owner's own facet."})
    return "facet_owner_written"


def _example_only(document) -> str:
    next(entry for entry in document["facets"] if entry["id"] == SELECT)["positive_examples"] = [
        "Use SVD for a least-squares fit."]
    return SELECT


def _claim_edit(document) -> str:
    next(entry for entry in document["facets"] if entry["id"] == SHARED)["claim"] = NEW_CLAIM
    return SHARED


def _kill(monkeypatch, name: str) -> None:
    def killed(*_args, **_kwargs):
        raise _Killed()

    monkeypatch.setattr(facet_actions, name, killed)


@pytest.mark.parametrize("edit", [_new_facet_only, _example_only, _claim_edit],
                         ids=["new_facet_only", "example_only", "claim_edit"])
def test_recovery_withdraws_the_verdict_of_a_save_killed_before_its_write(tmp_path, monkeypatch, edit):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    document = read_yaml(paths.facets_path)
    facet_id = edit(document)
    before = paths.facets_path.read_text(encoding="utf-8")

    _kill(monkeypatch, "_write_registry")
    with pytest.raises(_Killed):
        facet_actions.save_registry_text(paths.root, repository, yaml_to_string(document), clock=_CLOCK)
    monkeypatch.undo()
    (granted,) = _authority_verdicts(repository)
    assert (granted["verdict"], granted["left_id"]) == ("granted", facet_id)
    assert paths.facets_path.read_text(encoding="utf-8") == before

    recovered = facet_actions.recover_interrupted_actions(paths.root, repository, clock=_CLOCK)

    save = next(row for row in recovered if row.get("kind") == "library_save")
    assert (save["from"], save["to"]) == ("applying", "abandoned")
    assert all(row["to"] == "abandoned" for row in recovered)
    verdicts = _authority_verdicts(repository)
    assert sorted(row["verdict"] for row in verdicts) == ["granted", "withdrawn"]
    withdrawn = next(row for row in verdicts if row["verdict"] == "withdrawn")
    assert withdrawn["supersedes_id"] == granted["id"]
    assert json.loads(withdrawn["rationale"])["withdrawn_id"] == granted["id"]
    # Settled once: nothing is left in flight, and nothing is withdrawn twice.
    assert facet_actions.recover_interrupted_actions(paths.root, repository, clock=_CLOCK) == []
    assert len(_authority_verdicts(repository)) == 2
    assert facet_actions.interrupted_registry_saves(repository) == []


@pytest.mark.parametrize("edit", [_new_facet_only, _example_only, _claim_edit],
                         ids=["new_facet_only", "example_only", "claim_edit"])
def test_recovery_keeps_the_verdict_of_a_save_killed_after_its_write(tmp_path, monkeypatch, edit):
    """The registry write landed and the process stopped before the save was
    marked done: the owner's verdict names the wording the registry shows, so
    it stands."""

    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    document = read_yaml(paths.facets_path)
    facet_id = edit(document)

    _kill(monkeypatch, "refresh_derived_state")
    with pytest.raises(_Killed):
        facet_actions.save_registry_text(paths.root, repository, yaml_to_string(document), clock=_CLOCK)
    monkeypatch.undo()

    recovered = facet_actions.recover_interrupted_actions(paths.root, repository, clock=_CLOCK)

    save = next(row for row in recovered if row.get("kind") == "library_save")
    assert (save["from"], save["to"]) == ("applying", "applied")
    assert all(row["to"] == "applied" for row in recovered)
    assert [(row["verdict"], row["left_id"]) for row in _authority_verdicts(repository)] == [("granted", facet_id)]
    assert facet_id in load_vault(paths.root).evidence_facets
    assert facet_actions.interrupted_registry_saves(repository) == []


def test_a_save_that_fails_in_process_settles_its_intent(tmp_path, monkeypatch):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    document = read_yaml(paths.facets_path)
    _new_facet_only(document)

    def crash(*_args, **_kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(facet_actions, "_write_registry", crash)
    with pytest.raises(RuntimeError):
        facet_actions.save_registry_text(paths.root, repository, yaml_to_string(document), clock=_CLOCK)

    assert facet_actions.interrupted_registry_saves(repository) == []
    assert sorted(row["verdict"] for row in _authority_verdicts(repository)) == ["granted", "withdrawn"]
    assert facet_actions.recover_interrupted_actions(paths.root, repository, clock=_CLOCK) == []


def test_a_save_that_lands_records_a_settled_intent(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    document = read_yaml(paths.facets_path)
    facet_id = _new_facet_only(document)

    saved = facet_actions.save_registry_text(paths.root, repository, yaml_to_string(document), clock=_CLOCK)

    (verdict,) = _authority_verdicts(repository)
    record = facet_actions.registry_save_by_id(repository, saved["save_id"])
    assert record["status"] == "applied" and record["applied_at"]
    assert record["judgment_ids"] == {facet_id: verdict["id"]}
    assert json.loads(verdict["rationale"])["save_id"] == saved["save_id"]
    assert facet_actions.interrupted_registry_saves(repository) == []


def test_doctor_reports_and_settles_an_interrupted_save_with_no_reword(tmp_path, monkeypatch):
    from learnloop.ops.doctor import run_doctor

    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    document = read_yaml(paths.facets_path)
    _new_facet_only(document)
    _kill(monkeypatch, "_write_registry")
    with pytest.raises(_Killed):
        facet_actions.save_registry_text(paths.root, repository, yaml_to_string(document), clock=_CLOCK)
    monkeypatch.undo()

    report = run_doctor(paths.root)
    assert any(issue.code == "facet_identity:interrupted" for issue in report.issues)
    fixed = run_doctor(paths.root, fix_state=True)
    assert any(issue.code == "facet_identity:recovered" and "abandoned" in issue.message for issue in fixed.issues)
    assert sorted(row["verdict"] for row in _authority_verdicts(repository)) == ["granted", "withdrawn"]


def test_a_save_intent_has_a_closed_lifecycle(tmp_path):
    """Migration 197: a save is ``applying``, ``applied`` or ``abandoned``, and a settled save stays settled."""

    import sqlite3

    from learnloop.db.stores import facet_identity as store

    _paths, _vault, repository = _vault_with_duplicate(tmp_path)
    with repository.atomic():
        connection = repository.connection()
        store.insert_registry_save(connection, save_id="save_1", created_at="2026-10-13T12:00:00Z",
                                   facets={"f": {"before": None, "after": "k", "fields": ["claim"]}},
                                   judgment_ids={"f": "j1"}, action_ids=[])
        store.settle_registry_save(connection, "save_1", "applied", at="2026-10-13T12:00:01Z")
        store.settle_registry_save(connection, "save_1", "abandoned", at="2026-10-13T12:00:02Z")
    record = facet_actions.registry_save_by_id(repository, "save_1")
    assert (record["status"], record["abandoned_at"]) == ("applied", None)
    with pytest.raises(sqlite3.IntegrityError):
        with repository.atomic():
            repository.connection().execute(
                "INSERT INTO facet_registry_saves(id, created_at, status, facets_json, judgment_ids_json) "
                "VALUES ('save_2', '2026-10-13T12:00:00Z', 'pending', '{}', '{}')")
