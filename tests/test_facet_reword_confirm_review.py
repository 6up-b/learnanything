"""The Codex review of the facet reword confirm (stage ``facet-reword-confirm``).

Six findings, each pinned here through the real producers, compiler and
confirm path:

* F1: an attach or in-run absorb whose candidate cites exam material under the
  wrong unit dropped that citation before the authority check, so the exam
  wording joined the facet as an "uncited" worked example. The unresolved
  citations now travel with every contribution.
* F2: a confirm replaced every field the held reword changed, so an alias (or
  an error signature, a repair) added to the facet since was lost when the
  reword changed that list too. It now merges each field three ways and
  refuses a conflict it cannot merge.
* F3: a confirm's source excerpts were cached when the reword was held, so a
  source re-marked as an exam, or a unit held out since, kept showing its
  text. Every listing now re-resolves each source with today's roles.
* F4: a confirmed reword wrote its citations to facets.yaml but never to
  ``entity_source_links``, the authoritative provenance. The confirm now
  installs them write-ahead, and recovery finishes an interrupted one.
* F5: the append producer could not deliver a title or worked-example change
  (``AppendFacetWording`` had neither field, and only meaning fields were
  copied). It now carries both.
* F6: the admission change had no kill switch.
  ``facet_identity.reword_confirm = false`` restores the predecessor rule.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from learnloop.clock import FrozenClock
from learnloop.content.facet_identity import actions as facet_actions
from learnloop.content.facet_identity import authority
from learnloop.content.facet_identity.actions import FacetIdentityActionError, facet_history, list_actions
from learnloop.content.proposals.patches import PatchApplicationError, apply_accepted_items
from learnloop.content.synthesis.ai_contracts import AppendReconciliation, SynthFacet, SynthSpanRef
from learnloop.content.synthesis.source_append import append_source
from learnloop.content.sources.provenance import get_entity_provenance
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_source_set

from tests.facet_identity_fakes import FakeFacetJudge
from tests.helpers import append_config_toml
from tests.test_facet_authority import EXAM_CLAIM, EXAM_CONDITION, EXAM_SPAN, _consolidation, _meaning
from tests.test_facet_identity_actions import SHARED, _vault_with_duplicate
from tests.test_facet_identity_ingest import DEF_CLAIM
from tests.test_facet_reword_confirm import (
    _held,
    _pending,
    _proposal,
    _seed,
    _support,
)
from tests.test_facet_reword_paths import (
    NEW_SPAN,
    SYMMETRY,
    SYMMETRY_CLAIM,
    TEXT_SPAN,
    _call,
    _facet_restructure,
    _sidecar,
)
from tests.test_facet_rewords import NEW_CLAIM, OLD_CLAIM, _entry, _facet_update_proposal
from tests.test_source_append import FakeAppendClient, _bootstrap_and_add

_CLOCK = FrozenClock(datetime(2026, 10, 13, 16, 0, 0, tzinfo=UTC))
EXAM_RESTATED = "On the final exam, a matrix is symmetric when flipping it across the diagonal changes nothing."
NOTES_TEXT = "My notes: every real matrix has a singular value decomposition."


def _facet_rows(repo, proposal_id):
    return [row for row in repo.proposal_items(proposal_id or "") or [] if row["item_type"] == "facet"]


def _accept_all(root, repo, proposal_id):
    pending = [row["id"] for row in repo.proposal_items(proposal_id or "") or [] if row["decision"] == "pending"]
    if pending:
        apply_accepted_items(root, proposal_id, item_ids=pending, clock=_CLOCK)


# --- F1: an absorbed candidate's misdeclared exam citation is still exam material ---------------


def test_an_attach_absorbing_an_exam_span_cited_under_the_wrong_unit_never_grows_the_facet(tmp_path):
    """End to end: the append producer, the identity judge, the gates and the compiler."""

    root, repo = _bootstrap_and_add(tmp_path, add_role="exam")
    misplaced = {**NEW_SPAN, "unit_id": "chapter_symmetry"}  # the exam's span, named under the textbook's unit

    def builder(_context, _n):
        return AppendReconciliation(summary="restated from the exam", facets=[SynthFacet(
            client_item_id="f_exam", id="facet_symmetry_exam", concept_id="concept_symmetric_matrix",
            kind="definition", claim=EXAM_RESTATED,
            provenance=[SynthSpanRef(**misplaced, relation="primary", role="primary_textbook")],
        )])

    judge = FakeFacetJudge(clusters=[[DEF_CLAIM, EXAM_RESTATED]], action="absorb")
    result = append_source(root, "set_la", client=FakeAppendClient(builder=builder), new_revision_ids=["rev_alt"],
                           repository=repo, clock=_CLOCK, facet_identity_client=judge)

    (action,) = result.facet_identity["actions"]
    assert (action["scope"], action["action"]) == ("attach", "absorb")
    (row,) = _facet_rows(repo, result.proposal_id)
    assert "positive_examples" not in row["payload"]  # an alias only
    assert any(diag["gate"] == "exam_authority" and SYMMETRY in diag["entity_refs"]
               for diag in result.gate_diagnostics)
    _accept_all(root, repo, result.proposal_id)
    facet = load_vault(root).evidence_facets[SYMMETRY]
    assert EXAM_RESTATED not in facet.positive_examples
    assert "facet_symmetry_exam" in facet.aliases
    assert _pending(repo, root) == []


@pytest.mark.parametrize(("action", "absorb_as"), [("merge", None), ("absorb", "precondition"), ("absorb", "example")])
def test_an_in_run_consolidation_never_takes_exam_meaning_cited_under_the_wrong_unit(tmp_path, action, absorb_as):
    _normalized, _report, survivor = _consolidation(
        tmp_path, survivor_cites=TEXT_SPAN, retired_cites={**EXAM_SPAN, "unit_id": "chapter_symmetry"},
        action=action, absorb_as=absorb_as,
    )

    meaning = _meaning(survivor)
    assert EXAM_CLAIM not in meaning and EXAM_CONDITION not in meaning


# --- F2: a confirm merges what changed since; it never overwrites it -----------------------------


def test_a_confirm_keeps_an_alias_added_since_when_the_reword_adds_one_too(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    apply_accepted_items(paths.root, _facet_update_proposal(repository, {"id": SHARED, "aliases": ["original"]}),
                         clock=_CLOCK)
    confirm = _held(paths, repository, {"id": SHARED, "claim": NEW_CLAIM, "aliases": ["original", "proposed"]})
    apply_accepted_items(
        paths.root, _facet_update_proposal(repository, {"id": SHARED, "aliases": ["original", "later"]}),
        clock=_CLOCK,
    )

    facet_actions.confirm_reword(paths.root, repository, confirm["action_id"], clock=_CLOCK)

    entry = _entry(paths, SHARED)
    assert entry["claim"] == NEW_CLAIM
    assert entry["aliases"] == ["original", "later", "proposed"]
    # The card showed everything the confirm writes, the alias included.
    assert [(change["field"], change["after"]) for change in confirm["changes"]] == [
        ("claim", NEW_CLAIM), ("aliases", ["original", "proposed"])]


def test_a_confirm_keeps_error_signatures_and_repairs_changed_since(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    confirm = _held(paths, repository, {"id": SHARED, "claim": NEW_CLAIM, "error_signatures": ["swaps U and V"],
                                        "instructional_repairs": ["write out the shapes"]})
    apply_accepted_items(paths.root, _facet_update_proposal(repository, {
        "id": SHARED, "error_signatures": ["forgets the transpose"], "instructional_repairs": ["check A^T A"],
    }), clock=_CLOCK)

    facet_actions.confirm_reword(paths.root, repository, confirm["action_id"], clock=_CLOCK)

    entry = _entry(paths, SHARED)
    assert entry["error_signatures"] == ["forgets the transpose", "swaps U and V"]
    assert entry["instructional_repairs"] == ["check A^T A", "write out the shapes"]


def test_a_confirm_refuses_a_conflicting_change_it_cannot_merge(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    confirm = _held(paths, repository, {"id": SHARED, "claim": NEW_CLAIM, "status": "proposed"})
    apply_accepted_items(paths.root, _facet_update_proposal(repository, {"id": SHARED, "status": "retired"}),
                         clock=_CLOCK)

    with pytest.raises(FacetIdentityActionError) as raised:
        facet_actions.confirm_reword(paths.root, repository, confirm["action_id"], clock=_CLOCK)

    assert raised.value.code == "changed_since" and "status" in str(raised.value)
    entry = _entry(paths, SHARED)
    assert (entry["claim"], entry["status"]) == (OLD_CLAIM, "retired")
    assert facet_actions.keep_current_wording(paths.root, repository, confirm["action_id"],
                                              clock=_CLOCK)["status"] == "kept"


# --- F3: excerpts follow today's roles and held-out selections ------------------------------------


def _held_on_notes(paths, repository):
    notes = _seed(paths, repository, "notes", "notes", text=NOTES_TEXT)
    apply_accepted_items(paths.root, _proposal(repository, {"id": SHARED, "claim": NEW_CLAIM,
                                                            "meaning_support": _support(notes)}), clock=_CLOCK)
    (confirm,) = _pending(repository, paths.root)
    assert confirm["sources"][0]["excerpt"] == NOTES_TEXT
    return notes, confirm


def _assert_hidden(confirm):
    (source,) = confirm["sources"]
    assert source["excerpt"] is None and source["assessment_only"] is True and source["role"] == "exam"
    assert NOTES_TEXT not in json.dumps(confirm)


def test_a_pending_confirm_hides_a_sources_text_once_its_member_is_an_exam(tmp_path):
    from learnloop.curriculum.subject_registry import build_subject_registry

    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    _held_on_notes(paths, repository)
    source_set = next(item for item in load_vault(paths.root).source_sets if item.id == "set_src_notes")
    upsert_source_set(paths.root, {
        "id": source_set.id, "subject_id": source_set.subject_id, "title": source_set.title,
        "members": [{**member.model_dump(mode="json", exclude_none=True), "default_role": "exam"}
                    for member in source_set.members],
    }, clock=_CLOCK)

    (confirm,) = _pending(repository, paths.root)
    _assert_hidden(confirm)
    (listed,) = build_subject_registry(load_vault(paths.root), repository, "linear-algebra")["reword_confirms"]
    _assert_hidden(listed)
    inbox = _call(_sidecar(paths), "get_proposals", {})
    assert NOTES_TEXT not in json.dumps(inbox)
    record = facet_actions.action_by_id(repository, confirm["action_id"])
    assert NOTES_TEXT not in json.dumps(facet_actions.describe(record, load_vault(paths.root)))
    assert NOTES_TEXT not in json.dumps(facet_history(repository, SHARED, load_vault(paths.root)))


def test_a_pending_confirm_hides_a_sources_text_once_its_unit_is_held_out(tmp_path):
    from learnloop.content.synthesis.source_unit_selection import save_unit_selection

    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    notes, _confirm = _held_on_notes(paths, repository)
    save_unit_selection(repository, notes["extraction_id"], [notes["unit_id"]],
                        exam_use_modes={notes["unit_id"]: "held_out_evaluation"})

    (confirm,) = _pending(repository, paths.root)
    _assert_hidden(confirm)


# --- F4: a confirm installs the reword's validated source links ---------------------------------


def _notes_append_confirm(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path, add_role="notes")
    result = append_source(root, "set_la", client=FakeAppendClient(builder=_facet_restructure()),
                           new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)
    (item,) = [row for row in _facet_rows(repo, result.proposal_id) if row["operation"] == "update"]
    apply_accepted_items(root, result.proposal_id, item_ids=[item["id"]], clock=_CLOCK)
    (confirm,) = _pending(repo, root)
    return root, repo, confirm


def _alt_links(repo):
    return [link for link in repo.entity_source_links("facet", SYMMETRY) if link["extraction_id"] == "ext_alt"]


def _assert_linked(root, repo):
    (link,) = _alt_links(repo)
    assert (link["relation"], link["revision_id"], link["status"]) == ("support", "rev_alt", "current")
    view = get_entity_provenance(repo, "facet", SYMMETRY)
    assert any(source["extraction_id"] == "ext_alt" for source in view["semantic_sources"])
    stored = next(ref for ref in load_vault(root).evidence_facets[SYMMETRY].provenance.source_refs
                  if getattr(ref, "extraction_id", None) == "ext_alt")
    assert stored.locator == link["locator"]


def test_a_confirmed_reword_installs_its_source_links(tmp_path):
    root, repo, confirm = _notes_append_confirm(tmp_path)
    assert _alt_links(repo) == []  # held: nothing links yet

    facet_actions.confirm_reword(root, repo, confirm["action_id"], clock=_CLOCK)

    assert load_vault(root).evidence_facets[SYMMETRY].claim == SYMMETRY_CLAIM
    _assert_linked(root, repo)


class _Killed(BaseException):
    """The process stopping after the file write (nothing in process catches it)."""


def test_an_interrupted_confirm_installs_its_source_links_on_recovery(tmp_path, monkeypatch):
    root, repo, confirm = _notes_append_confirm(tmp_path)

    def killed(*_args, **_kwargs):
        raise _Killed()

    monkeypatch.setattr(facet_actions, "refresh_derived_state", killed)
    with pytest.raises(_Killed):
        facet_actions.confirm_reword(root, repo, confirm["action_id"], clock=_CLOCK)
    monkeypatch.undo()
    assert facet_actions.action_by_id(repo, confirm["action_id"])["status"] == "applying"
    assert load_vault(root).evidence_facets[SYMMETRY].claim == SYMMETRY_CLAIM  # the file write landed

    outcomes = facet_actions.recover_interrupted_actions(root, repo, clock=_CLOCK)

    (outcome,) = [row for row in outcomes if row["id"] == confirm["action_id"]]
    assert outcome["to"] == "applied"
    _assert_linked(root, repo)
    # A second recovery (or a second pass of the links) changes nothing.
    assert facet_actions.recover_interrupted_actions(root, repo, clock=_CLOCK) == []
    assert len(_alt_links(repo)) == 1


# --- F5: the append producer delivers title and worked-example updates --------------------------


def _wording_restructure(wording: dict, *, citations=(), loose: bool = False):
    """A facet restructure carrying only ``wording`` (the strict ``facet_wording``, or the loose payload)."""

    def builder(_context, _n):
        restructure = {
            "client_item_id": "reword_symmetry", "target_entity_type": "facet", "target_entity_id": SYMMETRY,
            "operation": "update", "expected_target_hash": "", "payload": {},
        }
        if loose:
            restructure["payload"] = dict(wording)
        else:
            restructure["facet_wording"] = {
                "kind": None, "claim": "", "description": "", "preconditions": [], "postconditions": [],
                "applicability": [], "non_goals": [], **wording,
                "provenance": [{"revision_id": "", "source_id": "", "locator": "", "relation": "support",
                                "role": "primary_textbook", **span} for span in citations],
            }
        return AppendReconciliation.model_validate({"summary": "a better title", "restructures": [restructure]})

    return builder


def _presentation_update(tmp_path, wording_of, *, loose=False):
    root, repo = _bootstrap_and_add(tmp_path)
    old = load_vault(root).evidence_facets[SYMMETRY]
    wording = wording_of(old)
    result = append_source(root, "set_la", client=FakeAppendClient(builder=_wording_restructure(wording, loose=loose)),
                           new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)
    (item,) = [row for row in _facet_rows(repo, result.proposal_id) if row["operation"] == "update"]
    assert not any(diag["severity"] == "hard_fail" for diag in result.gate_diagnostics)
    assert not any(diag["gate"] == "facet_reword_confirm" for diag in result.gate_diagnostics)
    apply_accepted_items(root, result.proposal_id, item_ids=[item["id"]], clock=_CLOCK)
    return root, repo, old, wording


@pytest.mark.parametrize("loose", [False, True], ids=["facet_wording", "loose_payload"])
def test_an_append_title_update_applies_without_a_new_version(tmp_path, loose):
    root, repo, old, _wording = _presentation_update(
        tmp_path, lambda _old: {"title": "Symmetric matrix: the definition"}, loose=loose,
    )

    facet = load_vault(root).evidence_facets[SYMMETRY]
    assert facet.title == "Symmetric matrix: the definition"
    assert (facet.claim, facet.version) == (old.claim, old.version)
    assert _pending(repo, root) == []
    (record,) = [row for row in facet_history(repo, SYMMETRY, load_vault(root)) if row["action"] == "reword"]
    assert record["presentation"] is True and record["reworded"]["fields"] == ["title"]


def test_an_append_worked_example_update_applies_without_a_new_version(tmp_path):
    root, repo, old, wording = _presentation_update(
        tmp_path, lambda old: {"positive_examples": [*old.positive_examples, "the 2x2 identity matrix"]},
    )

    facet = load_vault(root).evidence_facets[SYMMETRY]
    assert facet.positive_examples == wording["positive_examples"] and facet.version == old.version
    (record,) = [row for row in facet_history(repo, SYMMETRY, load_vault(root)) if row["action"] == "reword"]
    assert record["presentation"] is True and record["reworded"]["fields"] == ["positive_examples"]


def test_the_append_schema_lets_a_provider_send_a_title_and_worked_examples():
    from learnloop.ai.strict_schema import strict_output_schema

    wording = strict_output_schema(AppendReconciliation)["$defs"]["AppendFacetWording"]["properties"]
    assert {"title", "positive_examples", "negative_examples"} <= set(wording)


# --- F6: the kill switch restores the predecessor admission rule ---------------------------------


def _switched_off(root):
    append_config_toml(root, "[facet_identity]\nreword_confirm = false")
    assert load_vault(root).config.facet_identity.reword_confirm is False


@pytest.mark.parametrize("change", [{"claim": NEW_CLAIM}, {"title": "SVD"}], ids=["claim", "title"])
def test_with_the_kill_switch_an_unsupported_change_is_refused_at_accept_not_held(tmp_path, change):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    _switched_off(paths.root)
    before = paths.facets_path.read_text(encoding="utf-8")

    with pytest.raises(PatchApplicationError, match="explanatory source"):
        apply_accepted_items(paths.root, _proposal(repository, {"id": SHARED, **change}), clock=_CLOCK)

    assert paths.facets_path.read_text(encoding="utf-8") == before
    assert _pending(repository, paths.root) == [] and list_actions(repository) == []


def test_with_the_kill_switch_the_append_lane_drops_an_uncited_reword(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    _switched_off(root)

    result = append_source(root, "set_la", client=FakeAppendClient(builder=_facet_restructure(citations=())),
                           new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)

    assert not [row for row in _facet_rows(repo, result.proposal_id) if row["operation"] == "update"]
    assert any(diag["gate"] == "facet_restructure" and SYMMETRY in diag["entity_refs"]
               for diag in result.gate_diagnostics)
    assert not any(diag["gate"] == "facet_reword_confirm" for diag in result.gate_diagnostics)


def test_with_the_kill_switch_an_uncited_absorbed_example_joins_as_an_alias_only(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    _switched_off(root)
    restated = "Symmetry of a real square matrix means it coincides with its transpose."

    def builder(_context, _n):
        return AppendReconciliation(summary="restated", facets=[SynthFacet(
            client_item_id="f_new", id="facet_symmetry_restated", concept_id="concept_symmetric_matrix",
            kind="definition", claim=restated, provenance=[],
        )])

    judge = FakeFacetJudge(clusters=[[DEF_CLAIM, restated]], action="absorb")
    result = append_source(root, "set_la", client=FakeAppendClient(builder=builder), new_revision_ids=["rev_alt"],
                           repository=repo, clock=_CLOCK, facet_identity_client=judge)

    (row,) = _facet_rows(repo, result.proposal_id)
    assert "positive_examples" not in row["payload"]


def test_with_the_kill_switch_a_reword_held_earlier_can_still_be_decided(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    confirm = _held(paths, repository)
    _switched_off(paths.root)

    facet_actions.confirm_reword(paths.root, repository, confirm["action_id"], clock=_CLOCK)

    assert _entry(paths, SHARED)["claim"] == NEW_CLAIM


def test_the_policy_follows_the_switch():
    from learnloop.config.schema import LearnLoopConfig

    on = LearnLoopConfig()
    off = LearnLoopConfig.model_validate({"facet_identity": {"reword_confirm": False}})
    assert authority.meaning_policy(on) == authority.REWORD_CONFIRM
    assert authority.meaning_policy(off) == authority.EXPLANATORY_ONLY
    before = {"id": "f", "kind": "definition", "claim": "old", "title": "old"}
    for policy, title_allowed, claim_confirmable in (
        (authority.REWORD_CONFIRM, True, True), (authority.EXPLANATORY_ONLY, False, False),
    ):
        title = authority.check_meaning_write("f", before=before, after={**before, "title": "new"}, registered=True,
                                              contributions=(), resolver=None, policy=policy)
        claim = authority.check_meaning_write("f", before=before, after={**before, "claim": "new"}, registered=True,
                                              contributions=(), resolver=None, policy=policy)
        assert title.allowed is title_allowed
        assert (claim.allowed, claim.confirmable, claim.code) == (False, claim_confirmable, "unsupported_reword")
