"""The facet-authority chokepoint, after its Codex re-review (job ``20261013-084836-j0SaqX``).

The re-review of ``783263ef..dd4e41af`` found six ways the one chokepoint
(``content.facet_identity.authority``) still let exam material, or an
unvalidated citation, reach a facet's meaning or its displayed authority:

1. a refused undo committed its intent first, so recovery retried the
   forbidden restoration forever and every later facet operation failed;
2. ``meaning_support: []`` (or malformed bookkeeping) hid the exam citation a
   write's own provenance records;
3. a split unit's children expanded to the whole raw unit, so selecting one
   child selected the other, and their role overrides overwrote each other;
4. a re-extraction of a member's pinned revision made the old extraction's
   citations unresolvable, and an unresolved recorded citation was treated as
   genuinely uncited (an undo could then mint an exam-only candidate);
5. a citation that does not resolve became a ``current`` primary source link,
   and so the facet's displayed semantic authority;
6. a Library save (the owner's manual authority) recorded no owner verdict, and
   example-only edits and new facets no record at all.
"""

from __future__ import annotations

import json

import pytest

from learnloop.content.facet_identity import actions as facet_actions
from learnloop.content.facet_identity import authority
from learnloop.content.facet_identity.actions import FacetIdentityActionError, list_actions, undo_action
from learnloop.content.proposals.patches import PatchApplicationError, apply_accepted_items
from learnloop.content.sources.provenance import get_entity_provenance
from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_source_set
from learnloop.vault.yaml_io import read_yaml, yaml_to_string

from tests.test_facet_authority import (
    _CLOCK,
    EXAM_CLAIM,
    EXAM_SPAN,
    NEW_CLAIM,
    SUBJECT,
    TEXT_SPAN,
    _add_two_units,
    _exam_alias_consolidation,
    _exam_vault,
    _facet_proposal,
    _owner_judgments,
    _source_set,
    _support,
)
from tests.test_facet_identity_actions import SELECT, SHARED, _vault_with_duplicate
from tests.test_facet_reword_paths import SYMMETRY
from tests.test_source_append import _bootstrap_and_add
from tests.test_source_inventory import _block, _ir, _persist, _register_revision
from tests.test_source_set_synthesis import _setup


def _block_ref(extraction_id: str, span_id: str, *, source_id: str, revision_id: str, relation: str = "primary") -> dict:
    """A persisted block-span provenance ref, as a facet payload records one."""

    return {
        "ref_type": "canonical_source", "ref_id": source_id, "source_id": source_id, "revision_id": revision_id,
        "extraction_id": extraction_id, "locator": f"span:{extraction_id}/{span_id}",
        "locator_scheme": "block_span_v1", "relation": relation,
    }


EXAM_REF = _block_ref("ext_exam", "s1", source_id="src_exam", revision_id="rev_exam")


# --- F1: a refused undo is settled, never retried forever --------------------------------


def test_recovery_settles_an_undo_intent_the_authority_rule_refuses(tmp_path):
    """An ``undoing`` row whose restoration the chokepoint refuses (recorded before
    the pre-check existed, or refused because the source set changed in
    between) is settled with an auditable outcome instead of failing every
    later facet operation."""

    root, repo, result = _exam_alias_consolidation(tmp_path)
    (action,) = result.facet_identity["actions"]
    record = facet_actions.action_by_id(repo, action["id"])
    with repo.atomic():
        facet_actions._record_undo_intent(repo.connection(), record, clock=_CLOCK)

    (outcome,) = facet_actions.recover_interrupted_actions(root, repo, clock=_CLOCK)

    assert outcome["from"] == "undoing" and outcome["to"] == "applied" and outcome["refused"] == "exam_authority"
    assert outcome["refusal"] and "problem" not in outcome  # settled, not left for repair
    settled = facet_actions.action_by_id(repo, action["id"])
    assert settled["status"] == "applied"
    assert settled["undo_detail"]["refused"]["code"] == "exam_authority"
    assert "facet_symmetry_exam" not in load_vault(root).evidence_facets
    # Nothing is left in flight: the next operations run.
    assert facet_actions.recover_interrupted_actions(root, repo, clock=_CLOCK) == []
    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    document = read_yaml(paths.facets_path)
    next(entry for entry in document["facets"] if entry["id"] == "facet_symmetry_definition")["claim"] = NEW_CLAIM
    facet_actions.save_registry_text(root, repo, yaml_to_string(document), clock=_CLOCK)
    assert load_vault(root).evidence_facets["facet_symmetry_definition"].claim == NEW_CLAIM


# --- F2: meaning_support never hides the write's own exam citation ------------------------


@pytest.mark.parametrize("support", [[], [{"from": "f_new", "citations": []}]])
def test_an_empty_meaning_support_never_hides_a_writes_exam_citation(tmp_path, support):
    root, repo = _exam_vault(tmp_path)
    patch_id = _facet_proposal(repo, {
        "id": "facet_exam_minted", "kind": "definition", "claim": EXAM_CLAIM,
        "provenance": {"origin": "sourceset_synthesis", "source_refs": [dict(EXAM_REF)]},
        "meaning_support": support,
    }, operation="create")

    with pytest.raises(PatchApplicationError, match="exam"):
        apply_accepted_items(root, patch_id, clock=_CLOCK)

    assert "facet_exam_minted" not in load_vault(root).evidence_facets


def test_a_citation_the_write_records_but_its_meaning_support_leaves_out_is_judged_on_its_own(tmp_path):
    """Declared contributions keep their boundaries: an exam span the payload
    records outside every declared contribution is not corroborated by them."""

    root, repo = _exam_vault(tmp_path)
    text_ref = _block_ref("ext_text", "s1", source_id="src_text", revision_id="rev_text")
    patch_id = _facet_proposal(repo, {
        "id": "facet_exam_beside", "kind": "definition", "claim": EXAM_CLAIM,
        "provenance": {"origin": "sourceset_synthesis", "source_refs": [text_ref, dict(EXAM_REF)]},
        "meaning_support": _support(TEXT_SPAN, label="f_text"),
    }, operation="create")

    with pytest.raises(PatchApplicationError, match="exam"):
        apply_accepted_items(root, patch_id, clock=_CLOCK)

    assert "facet_exam_beside" not in load_vault(root).evidence_facets


def test_a_write_whose_meaning_support_declares_its_exam_citation_with_textbook_support_applies(tmp_path):
    root, repo = _exam_vault(tmp_path)
    text_ref = _block_ref("ext_text", "s1", source_id="src_text", revision_id="rev_text")
    patch_id = _facet_proposal(repo, {
        "id": "facet_corroborated", "kind": "definition", "claim": NEW_CLAIM,
        "provenance": {"origin": "sourceset_synthesis", "source_refs": [text_ref, dict(EXAM_REF)]},
        "meaning_support": _support(TEXT_SPAN, EXAM_SPAN, label="f_both"),
    }, operation="create")

    apply_accepted_items(root, patch_id, clock=_CLOCK)

    assert load_vault(root).evidence_facets["facet_corroborated"].claim == NEW_CLAIM


@pytest.mark.parametrize("support", [
    "ext_exam:s1",
    {"from": "f", "citations": []},
    [42],
    [{"from": "f"}],
    [{"from": "f", "citations": "ext_exam:s1"}],
    [{"from": "f", "citations": [7]}],
])
def test_a_malformed_meaning_support_is_refused(tmp_path, support):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    patch_id = _facet_proposal(repository, {
        "id": "facet_malformed", "kind": "definition", "claim": NEW_CLAIM, "meaning_support": support,
    }, operation="create")

    with pytest.raises(PatchApplicationError, match="meaning_support"):
        apply_accepted_items(paths.root, patch_id, clock=_CLOCK)

    assert "facet_malformed" not in load_vault(paths.root).evidence_facets


# --- F3: a split unit's children are their own spans, with their own roles ----------------


def _add_split_chapter(repo, root, scope):
    """A textbook chapter the owner split at its level-2 headings: ``Theory`` (s1) and ``Exam`` (s2)."""

    _register_revision(repo, source_id="src_split", revision_id="rev_split")
    ir = _ir([("chapter", "Chapter", [
        _block("s1", "Theory: a symmetric matrix equals its transpose.", section=("chapter", "Theory")),
        _block("s2", "Exam: on the test, symmetric means a positive diagonal.", section=("chapter", "Exam")),
    ], "sha256:chapter", 3)])
    _persist(repo, ir, revision_id="rev_split", extraction_id="ext_split")
    save_unit_selection(repo, "ext_split", ["chapter"],
                        boundary_overrides=[{"op": "split_at_heading", "unit_id": "chapter"}], clock=_CLOCK)
    current = _source_set(root)
    members = [member.model_dump(mode="json", exclude_none=True) for member in current.members]
    members.append({"source_id": "src_split", "revision_id": "rev_split", "default_role": "primary_textbook",
                    "scope": scope, "priority": 1})
    upsert_source_set(root, {"id": "set_la", "subject_id": SUBJECT, "title": "Linear Algebra",
                             "members": members}, clock=_CLOCK)
    return authority.CitationResolver.for_source_set(repo, _source_set(root))


def test_selecting_one_child_of_a_split_unit_never_selects_its_sibling(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    resolver = _add_split_chapter(repo, root, [{"unit_id": "chapter#Theory"}])

    theory = resolver.resolve({"extraction_id": "ext_split", "unit_id": "chapter#Theory", "span_id": "s1"})
    assert isinstance(theory, authority.ResolvedCitation) and theory.role == "primary_textbook"
    for unit_id in ("chapter#Theory", "chapter", ""):
        cited = {"extraction_id": "ext_split", "span_id": "s2", **({"unit_id": unit_id} if unit_id else {})}
        assert isinstance(resolver.resolve(cited), authority.CitationProblem), unit_id


@pytest.mark.parametrize("theory_role", [None, "primary_textbook"])
@pytest.mark.parametrize("exam_first", [False, True])
def test_split_children_keep_their_own_role_overrides_in_any_order(tmp_path, theory_role, exam_first):
    root, repo = _setup(tmp_path, with_exam=False)
    theory = {"unit_id": "chapter#Theory", **({"role_override": theory_role} if theory_role else {})}
    exam = {"unit_id": "chapter#Exam", "role_override": "exam"}
    resolver = _add_split_chapter(repo, root, [exam, theory] if exam_first else [theory, exam])

    for unit_id in ("chapter#Exam", "chapter", ""):
        cited = {"extraction_id": "ext_split", "span_id": "s2", "relation": "primary",
                 **({"unit_id": unit_id} if unit_id else {})}
        resolved = resolver.resolve(cited)
        assert isinstance(resolved, authority.ResolvedCitation), unit_id
        assert (resolved.role, resolved.relation) == ("exam", "assessment_alignment"), unit_id
    resolved = resolver.resolve({"extraction_id": "ext_split", "unit_id": "chapter#Theory", "span_id": "s1"})
    assert isinstance(resolved, authority.ResolvedCitation) and resolved.role == "primary_textbook"
    # The exam half cited under the theory child is not in that unit.
    assert isinstance(resolver.resolve({"extraction_id": "ext_split", "unit_id": "chapter#Theory", "span_id": "s2"}),
                      authority.CitationProblem)


def test_the_writer_never_writes_a_reword_citing_the_unselected_half_of_a_split_unit(tmp_path):
    from learnloop.content.facet_identity.actions import pending_reword_confirms

    root, repo = _bootstrap_and_add(tmp_path)
    _add_split_chapter(repo, root, [{"unit_id": "chapter#Theory"}])
    patch_id = _facet_proposal(repo, {"id": SYMMETRY, "claim": EXAM_CLAIM, "meaning_support": _support(
        {"extraction_id": "ext_split", "unit_id": "chapter#Theory", "span_id": "s2"})}, operation="update")

    apply_accepted_items(root, patch_id, clock=_CLOCK)

    # The citation supports nothing (s2 is not in chapter#Theory, and the
    # other half is not selected): the reword is not written, and waits for
    # the owner's confirm, which names the citation that does not count
    # (owner, 2026-10-13). Selected as exam material, it is refused instead
    # (tests/test_facet_reword_confirm.py).
    assert load_vault(root).evidence_facets[SYMMETRY].claim != EXAM_CLAIM
    (confirm,) = pending_reword_confirms(repo, load_vault(root))
    assert confirm["sources"] == [] and any("chapter#Theory" in problem for problem in confirm["unresolved"])


# --- F4: a re-extraction never turns exam material into "uncited" ------------------------


def _re_extract_exam(repo) -> None:
    """A second completed extraction of the exam member's pinned revision."""

    _persist(repo, repo.load_document_ir("ext_exam"), revision_id="rev_exam", extraction_id="ext_exam_2",
             config={"re_extract": 1})
    assert resolve_extraction_id(repo, "rev_exam") == "ext_exam_2"


def test_a_citation_of_an_earlier_extraction_of_a_member_revision_keeps_its_role(tmp_path):
    root, repo = _setup(tmp_path, with_exam=True)
    _re_extract_exam(repo)

    resolved = authority.CitationResolver.for_source_set(repo, _source_set(root)).resolve(dict(EXAM_SPAN))

    assert isinstance(resolved, authority.ResolvedCitation)
    assert (resolved.extraction_id, resolved.role, resolved.revision_id) == ("ext_exam", "exam", "rev_exam")


def test_a_re_extraction_never_makes_an_exam_only_restoration_admissible(tmp_path):
    root, repo, result = _exam_alias_consolidation(tmp_path)
    (action,) = result.facet_identity["actions"]
    _re_extract_exam(repo)
    status = facet_actions.action_by_id(repo, action["id"])["status"]

    with pytest.raises(FacetIdentityActionError) as raised:
        undo_action(root, repo, action["id"], clock=_CLOCK)

    assert raised.value.code == "exam_authority"
    assert "facet_symmetry_exam" not in load_vault(root).evidence_facets
    assert facet_actions.action_by_id(repo, action["id"])["status"] == status != "undoing"


def test_an_undo_never_mints_a_candidate_whose_recorded_citations_no_longer_resolve(tmp_path):
    """The exam member left the source set: the candidate's recorded citation
    does not resolve, and that is not the same as citing nothing.

    Exam protection (2026-10-13): while the paper's selection still marks it
    ``held_out_evaluation`` it stays exam material outside any source set (the
    one predicate, ``content.sources.exam_material``: held-out units count
    wherever they sit), so the undo is refused as exam authority; once the
    mark is gone too, the citation is merely unresolved."""

    root, repo, result = _exam_alias_consolidation(tmp_path)
    (action,) = result.facet_identity["actions"]
    current = _source_set(root)
    members = [member.model_dump(mode="json", exclude_none=True) for member in current.members
               if member.revision_id != "rev_exam"]
    upsert_source_set(root, {"id": "set_la", "subject_id": SUBJECT, "title": "Linear Algebra",
                             "members": members}, clock=_CLOCK)
    status = facet_actions.action_by_id(repo, action["id"])["status"]

    with pytest.raises(FacetIdentityActionError) as raised:
        undo_action(root, repo, action["id"], clock=_CLOCK)
    assert raised.value.code == "exam_authority"

    save_unit_selection(repo, "ext_exam", ["paper_2024"], clock=_CLOCK, exam_use_modes={})
    with pytest.raises(FacetIdentityActionError) as raised:
        undo_action(root, repo, action["id"], clock=_CLOCK)

    assert raised.value.code == "unresolved_citation"
    assert "facet_symmetry_exam" not in load_vault(root).evidence_facets
    assert facet_actions.action_by_id(repo, action["id"])["status"] == status != "undoing"


# --- F5: a citation that does not resolve is never a semantic-authority link ---------------


def test_a_citation_that_does_not_resolve_never_becomes_a_semantic_authority_link(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    _add_two_units(repo, root)
    unselected = _block_ref("ext_two", "s2", source_id="src_two", revision_id="rev_two")
    selected = _block_ref("ext_two", "s1", source_id="src_two", revision_id="rev_two")
    rejected = _facet_proposal(repo, {
        "id": "facet_unselected_cite", "kind": "definition", "claim": "A symmetric matrix has a positive diagonal.",
        "provenance": {"origin": "sourceset_synthesis", "source_refs": [unselected]},
    }, operation="create")
    accepted = _facet_proposal(repo, {
        "id": "facet_selected_cite", "kind": "definition", "claim": "Symmetric matrices have real eigenvalues.",
        "provenance": {"origin": "sourceset_synthesis", "source_refs": [selected]},
    }, operation="create")

    apply_accepted_items(root, rejected, clock=_CLOCK)
    apply_accepted_items(root, accepted, clock=_CLOCK)

    # An uncited new facet is still admitted (the accepted default), but the
    # citation outside the selected units supports nothing anywhere.
    assert "facet_unselected_cite" in load_vault(root).evidence_facets
    assert repo.entity_source_links("facet", "facet_unselected_cite") == []
    shown = get_entity_provenance(repo, "facet", "facet_unselected_cite")
    assert shown["semantic_authority"] is None and shown["semantic_sources"] == []
    # A citation that resolves is still the facet's semantic authority.
    shown = get_entity_provenance(repo, "facet", "facet_selected_cite")
    assert shown["semantic_authority"]["locator"] == "span:ext_two/s1"


# --- F6: every manual-authority change to a facet's meaning is audited ---------------------


def _authority_verdicts(repository) -> list[dict]:
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT * FROM judgment_ledger WHERE task = ? ORDER BY left_id, created_at, id",
            (facet_actions.MANUAL_AUTHORITY_TASK,),
        ).fetchall()
    return [dict(row) for row in rows]


def test_every_library_change_to_a_facets_meaning_records_the_owners_authority_verdict(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    document = read_yaml(paths.facets_path)
    by_id = {entry["id"]: entry for entry in document["facets"]}
    by_id[SHARED]["claim"] = NEW_CLAIM  # a reword (a new version)
    by_id[SELECT]["positive_examples"] = ["Use SVD for a least-squares fit."]  # meaning, not a version
    by_id["recall"]["aliases"] = ["svd_recall_alias"]  # not meaning
    document["facets"].append({"id": "facet_owner_written", "kind": "definition", "claim": "An owner's own facet."})

    saved = facet_actions.save_registry_text(paths.root, repository, yaml_to_string(document), clock=_CLOCK)

    verdicts = _authority_verdicts(repository)
    assert sorted(row["left_id"] for row in verdicts) == sorted([SHARED, SELECT, "facet_owner_written"])
    for row in verdicts:
        assert (row["judge"], row["verdict"], row["left_kind"]) == ("owner", "granted", "facet")
        assert row["created_at"]
        audit = json.loads(row["rationale"])
        assert audit["actor"] == "owner" and audit["granted_at"] and audit["rationale"]
        assert audit["scope"]["facet_id"] == row["left_id"] and audit["scope"]["fields"]
    by_facet = {row["left_id"]: json.loads(row["rationale"]) for row in verdicts}
    assert by_facet["facet_owner_written"]["scope"]["new_facet"] is True
    assert by_facet[SELECT]["scope"]["fields"] == ["positive_examples"]
    # The version policy is unchanged: only the reword is a new version with an undo.
    (reword,) = list_actions(repository)
    assert saved["reword_action_ids"] == [reword["id"]] and reword["survivor_facet_id"] == SHARED
    assert reword["detail"]["authority_judgment_id"] == next(row["id"] for row in verdicts if row["left_id"] == SHARED)


def test_a_library_save_that_never_lands_withdraws_its_authority_verdicts(tmp_path, monkeypatch):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    document = read_yaml(paths.facets_path)
    document["facets"].append({"id": "facet_owner_written", "kind": "definition", "claim": "An owner's own facet."})

    def crash(*_args, **_kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(facet_actions, "_write_registry", crash)
    with pytest.raises(RuntimeError):
        facet_actions.save_registry_text(paths.root, repository, yaml_to_string(document), clock=_CLOCK)

    verdicts = _authority_verdicts(repository)
    assert sorted(row["verdict"] for row in verdicts) == ["granted", "withdrawn"]
    granted = next(row for row in verdicts if row["verdict"] == "granted")
    withdrawn = next(row for row in verdicts if row["verdict"] == "withdrawn")
    assert withdrawn["supersedes_id"] == granted["id"] and granted["left_id"] == "facet_owner_written"
    assert "facet_owner_written" not in load_vault(paths.root).evidence_facets


def test_the_registry_writer_refuses_an_owner_edit_with_no_audit_record(tmp_path):
    paths, vault, repository = _vault_with_duplicate(tmp_path)
    document = read_yaml(paths.facets_path)
    next(entry for entry in document["facets"] if entry["id"] == SHARED)["claim"] = NEW_CLAIM
    before = paths.facets_path.read_text(encoding="utf-8")

    with pytest.raises(authority.FacetAuthorityError) as raised:
        authority.write_registry_text(paths, yaml_to_string(document), basis={SHARED: authority.OwnerEdit("")})

    assert raised.value.code == "unaudited"
    assert paths.facets_path.read_text(encoding="utf-8") == before
    assert _owner_judgments(repository) == []


class _Killed(BaseException):
    """The process stops (not an exception the save could handle)."""


def test_recovery_withdraws_the_verdicts_of_a_library_save_killed_before_its_write(tmp_path, monkeypatch):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    document = read_yaml(paths.facets_path)
    next(entry for entry in document["facets"] if entry["id"] == SHARED)["claim"] = NEW_CLAIM
    document["facets"].append({"id": "facet_owner_written", "kind": "definition", "claim": "An owner's own facet."})

    def killed(*_args, **_kwargs):
        raise _Killed()

    monkeypatch.setattr(facet_actions, "_write_registry", killed)
    with pytest.raises(_Killed):
        facet_actions.save_registry_text(paths.root, repository, yaml_to_string(document), clock=_CLOCK)
    monkeypatch.undo()
    assert {row["verdict"] for row in _authority_verdicts(repository)} == {"granted"}

    outcomes = facet_actions.recover_interrupted_actions(paths.root, repository, clock=_CLOCK)

    # The save's intent and its reword are both withdrawn (Codex re-review 2,
    # F7: the save's intent owns the verdicts).
    assert sorted((row.get("kind", "action"), row["to"]) for row in outcomes) == [
        ("action", "abandoned"), ("library_save", "abandoned")]
    verdicts = _authority_verdicts(repository)
    granted = {row["id"] for row in verdicts if row["verdict"] == "granted"}
    assert len(granted) == 2
    assert {row["supersedes_id"] for row in verdicts if row["verdict"] == "withdrawn"} == granted
