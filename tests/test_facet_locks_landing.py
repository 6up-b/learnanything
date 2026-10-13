"""The facet-locks landing onto main: the chokepoint and the sources track composed.

merge/facet-locks (facet locks removed, the facet-meaning chokepoint
``content.facet_identity.authority``, the owner's one-tap reword confirm)
landed after main's sources track (canonical-source practice and probes,
exercise imports, practice proposals, source-first needs, the source
service). Two things are pinned here:

* the chokepoint's structural bypass test parses the sources track's modules
  too, and none of them touches the facet registry: an exercise import, a
  practice proposal or a source-first need writes practice items and database
  rows that reference registered facets, never a facet's meaning;
* the two exam predicates agree on held-out evaluation units. A unit the owner
  marked ``held_out_evaluation`` is exam material whatever its member's role:
  the facet authority resolver gave it the role ``exam`` (owner, 2026-10-13),
  and main's ``corpus.exam_withheld`` (tutor pins, find_sources, compare) and
  ``corpus.teaching_exclusions`` (the tutor's teaching scope, a model reader's
  results) withhold it too. The predicates are not unified here; a later
  exam-protection stage makes one (docs/reviews/facet-reword-confirm.md,
  "Landing onto main").
"""

from __future__ import annotations

import ast

from learnloop.content.facet_identity.authority import CitationResolver
from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.source_retrieval.corpus import (
    exam_withheld,
    model_reader_withheld,
    teaching_exclusions,
)
from learnloop.source_retrieval.tutor import PinnedSpanProvider
from tests.source_service_fakes import build_textbook_vault, loaded
from tests.test_facet_authority import _GUARDED_CALLS, _REGISTRY_FILE_MODULES, _called, _python_sources

#: The sources track's modules that create practice, proposals, imports or
#: needs (main, mvp-0.18/0.19). Each must be parsed by the bypass test.
SOURCES_TRACK_MODULES = frozenset({
    "learnloop/ai/tool_requests.py",
    "learnloop/cli/sources.py",
    "learnloop/content/authoring/draft_validation.py",
    "learnloop/content/authoring/exercise_authoring.py",
    "learnloop/content/authoring/source_exercise_import.py",
    "learnloop/db/stores/source_service.py",
    "learnloop/instructional/discriminating.py",
    "learnloop/instructional/exercises.py",
    "learnloop/instructional/exposure.py",
    "learnloop/instructional/harvest.py",
    "learnloop/instructional/interventions.py",
    "learnloop/instructional/needs.py",
    "learnloop/instructional/offers.py",
    "learnloop/instructional/policy.py",
    "learnloop/instructional/practice.py",
    "learnloop/instructional/screen.py",
    "learnloop/instructional/sources.py",
    "learnloop/instructional/tools.py",
    "learnloop/instructional/valuation.py",
    "learnloop/instructional/wiring.py",
    "learnloop/ops/pf_publish.py",
    "learnloop/ops/pf_verify.py",
    "learnloop/practice_index/retrieval.py",
    "learnloop/source_retrieval/compare.py",
    "learnloop/source_retrieval/corpus.py",
    "learnloop/source_retrieval/find_sources.py",
    "learnloop/source_retrieval/policy.py",
    "learnloop/source_retrieval/service_spend.py",
    "learnloop/source_retrieval/tutor.py",
    "learnloop/sources_upgrade.py",
    "learnloop/substrate/intervention_outcomes.py",
    "learnloop_sidecar/handlers/item_authoring.py",
    "learnloop_sidecar/handlers/source_service.py",
})


def test_the_bypass_test_parses_the_sources_track_and_none_of_it_writes_facet_meaning():
    parsed = {module: tree for module, tree in _python_sources()}
    assert SOURCES_TRACK_MODULES <= set(parsed), sorted(SOURCES_TRACK_MODULES - set(parsed))
    guarded = set(_GUARDED_CALLS) | {"write_registry_text", "check_meaning_write", "persist_proposal_batch"}
    for module in sorted(SOURCES_TRACK_MODULES):
        assert module not in _REGISTRY_FILE_MODULES, module
        calls = {_called(node) for node in ast.walk(parsed[module]) if isinstance(node, ast.Call)}
        names = {node.attr for node in ast.walk(parsed[module]) if isinstance(node, ast.Attribute)}
        constants = {node.value for node in ast.walk(parsed[module]) if isinstance(node, ast.Constant)}
        # No facet writer, no proposal batch (the only way a facet item reaches
        # the compiler), and no registry path.
        assert not (calls & guarded), (module, sorted(calls & guarded))
        assert "facets_path" not in names and "facets.yaml" not in constants, module


def _held_out_textbook(tmp_path, unit="ch5"):
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={unit: "held_out_evaluation"})
    return loaded(paths), repository, spans


def test_a_held_out_textbook_unit_is_exam_material_to_both_predicates(tmp_path):
    vault, repository, spans = _held_out_textbook(tmp_path)
    held = ("ext_text", spans["ch5"][1])
    taught = ("ext_text", spans["worked"][1])

    # The facet authority resolver: role exam, assessment alignment only.
    resolver = CitationResolver.for_vault(repository, vault)
    resolved = resolver.resolve({"extraction_id": held[0], "span_id": held[1], "unit_id": "ch5"})
    assert (resolved.role, resolved.relation) == ("exam", "assessment_alignment")
    assert resolver.resolve({"extraction_id": taught[0], "span_id": taught[1], "unit_id": "worked"}).role == (
        "primary_textbook")

    # main's corpus predicates: withheld from models and from teaching.
    assert exam_withheld(vault, repository, [held, taught]) == frozenset({held})
    exclusions = teaching_exclusions(vault, repository)
    assert held in exclusions.spans and taught not in exclusions.spans
    assert "ext_text" not in exclusions.extractions
    assert model_reader_withheld(vault, repository, [held, taught]) == {held: "assessment_lane"}


def test_a_pinned_passage_in_a_held_out_textbook_unit_never_grounds_the_tutor(tmp_path):
    vault, repository, spans = _held_out_textbook(tmp_path)
    held, taught = spans["ch5"][1], spans["worked"][1]
    pinned, manifest = PinnedSpanProvider([f"ext_text:{held}", f"ext_text:{taught}"])(
        vault, repository, context="library", question_md="q", learning_object_ids=[], item=None)
    assert [span["span_id"] for span in pinned] == [taught]
    assert {entry["span_id"]: entry["reason"] for entry in manifest["dropped_pins"]} == {
        held: "it is exam material"}


def test_a_held_out_unit_that_does_not_resolve_withholds_its_whole_extraction(tmp_path):
    vault, repository, spans = _held_out_textbook(tmp_path, unit="no_such_unit")
    taught = ("ext_text", spans["worked"][1])
    assert exam_withheld(vault, repository, [taught]) == frozenset({taught})
    assert "ext_text" in teaching_exclusions(vault, repository).extractions


def test_a_held_out_split_child_withholds_its_whole_raw_parent(tmp_path):
    vault, repository, spans = _held_out_textbook(tmp_path, unit="ch5#Theory")
    keys = [("ext_text", span) for span in spans["ch5"]]
    assert exam_withheld(vault, repository, keys) == frozenset(keys)
    assert exam_withheld(vault, repository, [("ext_text", spans["worked"][1])]) == frozenset()


def test_an_exam_members_material_is_exam_to_both_predicates(tmp_path):
    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    vault = loaded(paths)
    from tests.test_sources_merge_composition import _exam_span

    exam = ("ext_exam", _exam_span(repository))
    assert exam_withheld(vault, repository, [exam]) == frozenset({exam})
    resolver = CitationResolver.for_vault(repository, vault)
    assert resolver.exam_material({"extraction_id": exam[0], "span_id": exam[1]})
