"""RW4e: instructional roles as source-object proposals (spec_reader_workbench_v1 §7.9; G44).

* Each role on each passage is one ``source_objects`` proposal: ``object_type``
  by §3.4 item 14, ``authorial_role`` the role, the confidence, judge, ledger
  id and prompt version in ``content_json``, ``authorship = 'ai'``, ``status
  = 'proposed'``, one citation with the span, its block hash and the revision.
* A second judge proposing the same role on the same passage adds a version
  (agreement is visible); the same judge again writes nothing; a reviewed
  proposal takes no further version.
* Exam and held-out passages are never proposed, and a proposal whose passage
  is held out later is never returned by any reader, filter or grouping (the
  one predicate, fail closed).
* Roles add, never exclude (G44): teaching exclusions, item exclusions, the
  model-reader filter and item-bound scopes are the same with proposals as
  without; a proposal never admits a solution or an item's linked block.
* Writes touch only the three proposal tables: no concept edge, learning
  object, evidence or mastery. Fakes only.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.reader import source_objects as SO
from learnloop.reader import source_roles as RS
from tests.passage_cue_fakes import build_cue_vault, loaded, set_config
from tests.source_service_fakes import LEARNING_STATE_TABLES

PROPOSAL_TABLES = ("source_objects", "source_object_versions", "source_object_citations")


@pytest.fixture
def library(tmp_path):
    paths, repository, spans = build_cue_vault(tmp_path / "vault")
    return paths, repository, spans


def _claim(span_id: str, role: str, confidence: str = "high", *, extraction_id: str = "ext_text",
           ledger_id: str = "rlb_x") -> dict:
    return {"extraction_id": extraction_id, "span_id": span_id, "role": role, "confidence": confidence,
            "ledger_id": ledger_id}


def _propose(paths, repository, claims, *, judge=RS.JUDGE_LABELLER, prompt_version="role_labeller.v1"):
    return RS.propose_roles(loaded(paths), repository, claims, judge=judge, prompt_version=prompt_version,
                            model="fake-model")


def _all_counts(repository) -> dict[str, int]:
    with repository.connection() as connection:
        names = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            "AND name NOT LIKE '%_fts%'")]
        return {name: connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0] for name in names}


def _yaml_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.yaml")):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _versions(repository, object_id: str) -> list[dict]:
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM source_object_versions WHERE source_object_id = ? ORDER BY version_ordinal",
            (object_id,))]


# -- the proposal ---------------------------------------------------------------------------------


@pytest.mark.parametrize(("role", "object_type"), [
    ("worked_example", "worked_example"), ("exercise", "problem"), ("definition", "definition"),
    ("theorem", "claim"), ("counterexample", "motif_or_passage"), ("contrast", "motif_or_passage"),
    ("intuition", "motif_or_passage"), ("explanation", "motif_or_passage"), ("figure", "motif_or_passage"),
    ("prerequisite", "motif_or_passage"), ("alternative_treatment", "motif_or_passage"),
    ("application", "motif_or_passage"),
])
def test_the_object_type_is_mapped_by_section_3_4_item_14(role, object_type):
    assert RS.object_type_for(role) == object_type


def test_a_proposal_carries_confidence_judge_ledger_id_revision_and_one_citation(library):
    paths, repository, _spans = library
    before = _all_counts(repository)
    yaml_before = _yaml_digest(paths.root)
    written = _propose(paths, repository, [_claim("t3", "contrast", "high", ledger_id="pcj_1")],
                       judge=RS.JUDGE_CUE, prompt_version="passage_cue_judge.v2")
    (object_id,) = written["written"]
    head = repository.source_object_head(object_id)
    assert head["object"]["source_id"] == "src_text"
    version = head["version"]
    assert (version["object_type"], version["authorial_role"], version["authorship"], version["status"]) == (
        "motif_or_passage", "contrast", "ai", "proposed")
    assert version["revision_id"] == "rev_text" and version["exact_text"] == ""
    content = json.loads(version["content_json"])
    assert content == {"kind": "instructional_role", "role": "contrast", "confidence": "high",
                       "judge": "passage_cue_judge", "ledger_id": "pcj_1", "prompt_version": "passage_cue_judge.v2",
                       "model": "fake-model", "extraction_id": "ext_text"}
    assert json.loads(version["model_provenance_json"])["judge"] == "passage_cue_judge"
    (citation,) = head["citations"]
    with repository.connection() as connection:
        (block_hash,) = connection.execute(
            "SELECT content_hash FROM source_document_blocks WHERE extraction_id = 'ext_text' AND span_id = 't3'"
        ).fetchone()
    assert (citation["span_id"], citation["revision_id"], citation["block_content_hash"]) == (
        "t3", "rev_text", block_hash)
    assert block_hash
    # Only the three proposal tables changed; no YAML (no concept edge, LO or facet change).
    after = _all_counts(repository)
    changed = {name for name in after if after[name] != before.get(name)}
    assert changed == set(PROPOSAL_TABLES)
    assert all(after[table] == before[table] for table in LEARNING_STATE_TABLES if table in after)
    assert _yaml_digest(paths.root) == yaml_before
    assert repository.mapping_proposals() == []
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM source_object_relations").fetchone()[0] == 0


def test_a_second_judge_adds_a_version_and_the_same_judge_writes_nothing(library):
    paths, repository, _spans = library
    first = _propose(paths, repository, [_claim("t3", "contrast", "low", ledger_id="rlb_1")])
    (object_id,) = first["written"]
    again = _propose(paths, repository, [_claim("t3", "contrast", "high", ledger_id="rlb_2")])
    assert again["written"] == [] and again["versions"] == []
    assert again["skipped"] == [{"key": ["ext_text", "t3"], "role": "contrast",
                                 "reason": "already proposed by this judge"}]
    agreed = _propose(paths, repository, [_claim("t3", "contrast", "medium", ledger_id="pcj_9")],
                      judge=RS.JUDGE_CUE, prompt_version="passage_cue_judge.v2")
    assert agreed["written"] == [] and [entry["source_object_id"] for entry in agreed["versions"]] == [object_id]
    versions = _versions(repository, object_id)
    assert [(v["version_ordinal"], json.loads(v["content_json"])["judge"], v["status"]) for v in versions] == [
        (1, "role_labeller", "proposed"), (2, "passage_cue_judge", "proposed")]
    (label,) = RS.role_proposals(loaded(paths), repository, extraction_ids=["ext_text"])
    # Agreement is visible, and the best judge's confidence counts (low only alone).
    assert label.judges == ("role_labeller", "passage_cue_judge") and label.confidence == "medium"
    assert label.versions == 2 and label.key == ("ext_text", "t3")
    # Another role on the same passage is its own proposal.
    other = _propose(paths, repository, [_claim("t3", "counterexample")])
    assert len(other["written"]) == 1 and other["written"][0] != object_id


def test_a_reviewed_or_rejected_proposal_takes_no_further_version(library):
    paths, repository, _spans = library
    (object_id,) = _propose(paths, repository, [_claim("t2", "intuition")])["written"]
    SO.review_source_object(repository, source_object_id=object_id, status="rejected")
    result = _propose(paths, repository, [_claim("t2", "intuition")], judge=RS.JUDGE_ORGANIZER,
                      prompt_version="library_organizer.v2")
    assert result["versions"] == [] and result["skipped"][0]["reason"] == "reviewed as rejected"
    assert RS.role_proposals(loaded(paths), repository, extraction_ids=["ext_text"]) == []
    with pytest.raises(SO.SourceObjectError):
        SO.append_proposal_version(repository, source_object_id=object_id, revision_id="rev_text",
                                   object_type="motif_or_passage", content={}, citations=[])


def test_malformed_claims_are_skipped_never_written(library):
    paths, repository, _spans = library
    result = _propose(paths, repository, [
        _claim("t3", "not_a_role"), _claim("t3", "contrast", "certain"), _claim("", "contrast"),
        _claim("t999", "contrast"),
    ])
    assert result["written"] == []
    assert [entry["reason"] for entry in result["skipped"]] == ["malformed", "malformed", "malformed",
                                                                 "no such passage"]


def test_clean_roles_reads_a_roles_field_tolerantly():
    assert RS.clean_roles(None) == [] and RS.clean_roles("definition") == []
    assert RS.clean_roles([{"role": "contrast", "confidence": "high"}, {"role": "contrast", "confidence": "low"},
                           {"role": "definition"}, {"role": "nope", "confidence": "high"}, 7,
                           RS.RoleProposal(role="intuition", confidence="low")]) == [
        {"role": "contrast", "confidence": "high"}, {"role": "intuition", "confidence": "low"}]


# -- exam protection --------------------------------------------------------------------------------


def _exam_span(repository) -> str:
    with repository.connection() as connection:
        (span,) = connection.execute(
            "SELECT span_id FROM source_document_blocks WHERE extraction_id = 'ext_exam' AND text != '' "
            "ORDER BY ordinal LIMIT 1").fetchone()
    return str(span)


def test_exam_and_held_out_passages_are_never_proposed(library):
    paths, repository, spans = library
    exam = _exam_span(repository)
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"ch5": "held_out_evaluation"})
    before = _all_counts(repository)
    result = _propose(paths, repository, [_claim(exam, "definition", extraction_id="ext_exam"),
                                          _claim("t3", "contrast")])
    assert result["written"] == []
    assert {entry["reason"] for entry in result["skipped"]} == {"exam_material"}
    assert _all_counts(repository) == before


def test_an_unreadable_exam_predicate_proposes_nothing(library, monkeypatch):
    paths, repository, _spans = library

    def broken(*_args, **_kwargs):
        raise RuntimeError("predicate unreadable")

    monkeypatch.setattr(RS.EM, "exam_material", broken)
    result = _propose(paths, repository, [_claim("t3", "contrast")])
    assert result["written"] == [] and result["skipped"][0]["reason"] == "exam_material"


def test_a_proposal_held_out_later_is_never_returned(library):
    from learnloop.source_retrieval.find_sources import find_sources_for_caller, source_object_lists
    from learnloop.source_retrieval.policy import CallerContext

    paths, repository, spans = library
    _propose(paths, repository, [_claim("t3", "counterexample"), _claim("t2", "contrast"),
                                 _claim("s2", "counterexample", extraction_id="ext_book")])
    vault = loaded(paths)
    reading = CallerContext(kind="reader")
    assert {label.key for label in RS.role_proposals(vault, repository)} == {
        ("ext_text", "t3"), ("ext_text", "t2"), ("ext_book", "s2")}
    shown = find_sources_for_caller(vault, repository, "determinant rows swapped", caller=reading,
                                    roles=["counterexample"])
    assert ("ext_text", "t3") in {(hit["extraction_id"], hit["span_id"]) for hit in shown.hits}
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"ch5": "held_out_evaluation"})
    vault = loaded(paths)
    labels = RS.role_proposals(vault, repository)
    assert {label.key for label in labels} == {("ext_book", "s2")}
    assert RS.role_keys(vault, repository, ["ext_text", "ext_book"], ["counterexample", "contrast"]) == (
        {("ext_book", "s2")}, set())
    assert set(RS.best_roles(vault, repository, [("ext_text", "t3"), ("ext_text", "t2")])) == set()
    assert source_object_lists(vault, repository, "remediate", ["ext_text"]) == {}
    held = find_sources_for_caller(vault, repository, "determinant rows swapped", caller=reading,
                                   roles=["counterexample"])
    assert not {hit["span_id"] for hit in held.hits} & {"t2", "t3"}
    # The rows stay in the ledger (nothing is deleted); only what is returned is filtered.
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM source_objects").fetchone()[0] == 3
    # The P3 review read hides them too (RW4d's hidden_source_objects).
    visible = SO.source_objects_for_source(vault, repository, source_id="src_text")
    assert visible == []


def test_a_failing_protection_read_returns_no_proposal(library, monkeypatch):
    paths, repository, _spans = library
    _propose(paths, repository, [_claim("t3", "counterexample")])
    real = RS.SO.hidden_source_objects

    def hide_all(vault, repo, heads):
        return frozenset(str(head["object"]["id"]) for head in heads)

    monkeypatch.setattr(RS.SO, "hidden_source_objects", hide_all)
    assert RS.role_proposals(loaded(paths), repository) == []
    monkeypatch.setattr(RS.SO, "hidden_source_objects", real)
    assert len(RS.role_proposals(loaded(paths), repository)) == 1


# -- roles add, never exclude (G44) -----------------------------------------------------------------


def _exclusions(vault, repository):
    from learnloop.source_retrieval.corpus import item_exclusions, model_reader_withheld, teaching_exclusions
    from learnloop.source_retrieval.find_sources import scope_for

    item = vault.practice_items["pi_eigen_1"]
    with repository.connection() as connection:
        keys = [(row[0], row[1]) for row in connection.execute(
            "SELECT extraction_id, span_id FROM source_document_blocks ORDER BY extraction_id, ordinal")]
    teaching = teaching_exclusions(vault, repository)
    items = item_exclusions(repository, item)
    scope = scope_for(vault, repository, policy="assisted_practice", scope="teaching",
                      learning_object_ids=[item.learning_object_id], item=item)
    return {
        "teaching": (sorted(teaching.extractions), sorted(teaching.spans)),
        "item": (sorted(items.extractions), sorted(items.spans)),
        "model_reader": sorted(model_reader_withheld(vault, repository, keys).items()),
        "scope": scope.describe(),
        "allowed": sorted(key for key in keys if key[0] in scope.extractions and scope.allows(*key)),
    }


def test_a_proposal_never_admits_a_block_nor_removes_an_exclusion(library):
    from learnloop.source_retrieval.find_sources import find_sources_for_caller
    from learnloop.source_retrieval.policy import CallerContext

    paths, repository, spans = library
    vault = loaded(paths)
    before = _exclusions(vault, repository)
    # An explanation and an intuition on a solution, the exercises and the
    # worked example (an item's linked block), a definition on the exam.
    proposals = [_claim(span, "explanation") for span in spans["solutions"][1:]]
    proposals += [_claim(span, "intuition") for span in spans["exercises"][1:]]
    proposals += [_claim(span, "explanation") for span in spans["worked"][1:]]
    _propose(paths, repository, proposals)
    vault = loaded(paths)
    assert _exclusions(vault, repository) == before
    practice = CallerContext(kind="tutor", context="practice", item_id="pi_eigen_1")
    for role in ("explanation", "intuition"):
        hits = find_sources_for_caller(vault, repository, "subtracting gives eigenvalue solve", caller=practice,
                                       scope="teaching", roles=[role])
        returned = {(hit["extraction_id"], hit["span_id"]) for hit in hits.hits}
        assert not returned & {("ext_text", span) for span in spans["solutions"]}
        assert returned <= set(before["allowed"])


def test_roles_filters_match_ingest_hints_and_proposals_with_the_low_confidence_rule(library):
    from learnloop.source_retrieval.find_sources import find_sources_for_caller
    from learnloop.source_retrieval.policy import CallerContext

    paths, repository, spans = library
    reading = CallerContext(kind="reader")
    vault = loaded(paths)
    # Ingest's hint alone: the worked example.
    worked = find_sources_for_caller(vault, repository, "solve the eigenvalue", caller=reading,
                                     roles=["worked_example"])
    assert {hit["span_id"] for hit in worked.hits} == set(spans["worked"][1:])
    # A proposal adds a passage ingest has no role for.
    _propose(paths, repository, [_claim("t3", "worked_example", "medium")])
    vault = loaded(paths)
    both = find_sources_for_caller(vault, repository, "solve the eigenvalue determinant rows swapped",
                                   caller=reading, roles=["worked_example"])
    assert {hit["span_id"] for hit in both.hits} >= {*spans["worked"][1:], "t3"}
    assert both.manifest["search"]["role_basis"]["proposals"] == 1
    # Low confidence counts only when nothing better exists.
    _propose(paths, repository, [_claim("t2", "intuition", "low")])
    vault = loaded(paths)
    alone = find_sources_for_caller(vault, repository, "eigenvalues characteristic polynomial", caller=reading,
                                    roles=["intuition"])
    assert {hit["span_id"] for hit in alone.hits} == {"t2"}
    assert alone.manifest["search"]["role_basis"]["low_confidence"] == 1
    _propose(paths, repository, [_claim("t3", "intuition", "high")])
    vault = loaded(paths)
    better = find_sources_for_caller(vault, repository, "eigenvalues characteristic polynomial determinant",
                                     caller=reading, roles=["intuition"])
    assert {hit["span_id"] for hit in better.hits} == {"t3"}
    # The positive filter's switch: off, proposals are ignored; ingest's hints stay.
    set_config(paths, "roles", positive_filter_enabled=False)
    vault = loaded(paths)
    off = find_sources_for_caller(vault, repository, "eigenvalues characteristic polynomial determinant",
                                  caller=reading, roles=["intuition"])
    assert off.hits == [] and off.manifest["search"]["role_basis"]["proposals"] == 0
    hints = find_sources_for_caller(vault, repository, "solve the eigenvalue determinant rows swapped",
                                    caller=reading, roles=["worked_example"])
    assert {hit["span_id"] for hit in hints.hits} == set(spans["worked"][1:])
    assert RS.role_proposals(vault, repository) == []


def test_intent_lists_read_proposals_by_role_and_by_their_mapped_type(library):
    from learnloop.source_retrieval.find_sources import source_object_lists

    paths, repository, _spans = library
    _propose(paths, repository, [_claim("t3", "contrast"), _claim("t2", "theorem"), _claim("t5", "worked_example"),
                                 _claim("t2", "alternative_treatment", "low"),
                                 _claim("s6", "intuition", extraction_id="ext_book")])
    vault = loaded(paths)
    assert source_object_lists(vault, repository, "remediate", ["ext_text"]) == {
        "source_objects": [("ext_text", "t3")]}
    # theorem is a claim (explain's type) and an explain role; the worked example by type.
    assert source_object_lists(vault, repository, "explain", ["ext_text"]) == {"source_objects": [("ext_text", "t2")]}
    assert source_object_lists(vault, repository, "worked_example", ["ext_text"]) == {
        "source_objects": [("ext_text", "t5")]}
    # Codex review F3: the low one only when nothing better exists, not last.
    assert source_object_lists(vault, repository, "alternative", ["ext_text", "ext_book"]) == {
        "source_objects": [("ext_book", "s6")]}
    assert source_object_lists(vault, repository, "alternative", ["ext_text"]) == {
        "source_objects": [("ext_text", "t2")]}
    set_config(paths, "roles", positive_filter_enabled=False)
    off = loaded(paths)
    assert all(source_object_lists(off, repository, intent, ["ext_text", "ext_book"]) == {}
               for intent in ("remediate", "explain", "worked_example", "alternative"))


def _spy_lists(monkeypatch):
    """The extra lists each ``find_sources`` passes its search (the retrieval
    boost an intent list gives)."""

    from learnloop.source_retrieval import find_sources as FS

    seen: list[dict] = []
    real = FS.search_spans

    def spy(*args, extra_lists=None, **kwargs):
        seen.append({name: list(keys) for name, keys in (extra_lists or {}).items()})
        return real(*args, extra_lists=extra_lists, **kwargs)

    monkeypatch.setattr(FS, "search_spans", spy)
    return seen


def test_an_intent_list_takes_a_low_confidence_proposal_only_when_no_stronger_one_is_in_scope(library, monkeypatch):
    """Codex review F3 (sources §9.2), through ``find_sources``: a weak
    ``alternative_treatment`` beside a strong ``intuition`` gets no boost; it
    counts once the caller's scope leaves no stronger candidate."""

    from learnloop.source_retrieval.find_sources import find_sources_for_caller
    from learnloop.source_retrieval.policy import CallerContext
    from tests.source_service_fakes import FakeServiceLLM

    paths, repository, _spans = library
    _propose(paths, repository, [_claim("t3", "intuition", "high"), _claim("t2", "alternative_treatment", "low")])
    vault = loaded(paths)
    seen = _spy_lists(monkeypatch)
    reading = CallerContext(kind="reader")
    find_sources_for_caller(vault, repository, "eigenvalues characteristic polynomial", caller=reading,
                            intent="alternative", rerank_client=FakeServiceLLM())
    assert seen[-1]["source_objects"] == [("ext_text", "t3")]
    # The stronger proposal excluded by the caller (already shown): the weak one counts.
    find_sources_for_caller(vault, repository, "eigenvalues characteristic polynomial", caller=reading,
                            intent="alternative", exclude_span_keys=[["ext_text", "t3"]],
                            rerank_client=FakeServiceLLM())
    assert seen[-1]["source_objects"] == [("ext_text", "t2")]
    # The same exclusion by span id (the Reader's shown passages).
    find_sources_for_caller(vault, repository, "eigenvalues characteristic polynomial", caller=reading,
                            intent="alternative", exclude_span_ids=["ext_text:t3"],
                            rerank_client=FakeServiceLLM())
    assert seen[-1]["source_objects"] == [("ext_text", "t2")]


def test_a_stronger_proposal_the_scope_excludes_never_blocks_the_low_confidence_one(library, monkeypatch):
    """Codex review F3: the stronger candidate must be eligible in the
    effective scope (here a solution, which a practice caller's teaching scope
    excludes), for an intent list and for the ``roles`` filter alike."""

    from learnloop.source_retrieval.find_sources import find_sources_for_caller, scope_for
    from learnloop.source_retrieval.policy import CallerContext
    from tests.source_service_fakes import FakeServiceLLM

    paths, repository, spans = library
    solution = spans["solutions"][1]
    _propose(paths, repository, [_claim(solution, "intuition", "high"), _claim("t2", "intuition", "low")])
    vault = loaded(paths)
    item = vault.practice_items["pi_eigen_1"]
    scope = scope_for(vault, repository, policy="assisted_practice", scope="teaching",
                      learning_object_ids=[item.learning_object_id], item=item)
    assert not scope.allows("ext_text", solution) and scope.allows("ext_text", "t2")
    practice = CallerContext(kind="tutor", context="practice", item_id="pi_eigen_1")
    seen = _spy_lists(monkeypatch)
    find_sources_for_caller(vault, repository, "eigenvalues characteristic polynomial", caller=practice,
                            scope="teaching", intent="alternative", rerank_client=FakeServiceLLM())
    assert seen[-1]["source_objects"] == [("ext_text", "t2")]
    hits = find_sources_for_caller(vault, repository, "eigenvalues characteristic polynomial", caller=practice,
                                   scope="teaching", roles=["intuition"])
    assert {hit["span_id"] for hit in hits.hits} == {"t2"}
    assert hits.manifest["search"]["role_basis"]["low_confidence"] == 1


def test_a_stronger_proposal_the_roles_filter_rejects_never_blocks_the_low_confidence_one(library, monkeypatch):
    """Codex re-review F5: with ``roles=``, the intent list's "stronger
    candidate" must also pass the role filter. A strong ``intuition`` the
    ``alternative_treatment`` filter rejects never suppresses the weak
    ``alternative_treatment`` passage, which (no keyword match of its own)
    reaches the retrieval pool only through that list."""

    from learnloop.source_retrieval import find_sources as FS
    from learnloop.source_retrieval.policy import CallerContext
    from tests.source_service_fakes import FakeServiceLLM

    paths, repository, _spans = library
    # A = t2 (the query's own words), B = t3 (the row swap: no query word).
    _propose(paths, repository, [_claim("t2", "intuition", "high"), _claim("t3", "alternative_treatment", "low")])
    vault = loaded(paths)
    seen: list[dict] = []
    pools: list[list] = []
    real = FS.search_spans

    def spy(*args, extra_lists=None, **kwargs):
        seen.append({name: list(keys) for name, keys in (extra_lists or {}).items()})
        search = real(*args, extra_lists=extra_lists, **kwargs)
        pools.append([hit.key for hit in search.hits])
        return search

    monkeypatch.setattr(FS, "search_spans", spy)
    reading = CallerContext(kind="reader")
    query = "eigenvalues characteristic polynomial"
    FS.find_sources_for_caller(vault, repository, query, caller=reading, intent="alternative",
                               rerank_client=FakeServiceLLM())
    assert ("ext_text", "t3") not in pools[-1]  # B has no retrieval match of its own
    hits = FS.find_sources_for_caller(vault, repository, query, caller=reading, intent="alternative",
                                      roles=["alternative_treatment"], rerank_client=FakeServiceLLM())
    assert seen[-1]["source_objects"] == [("ext_text", "t3")]
    assert pools[-1] == [("ext_text", "t3")]
    assert hits.manifest["search"]["role_basis"]["low_confidence"] == 1
    # The role filter that admits the strong one keeps it alone, as before.
    FS.find_sources_for_caller(vault, repository, query, caller=reading, intent="alternative",
                               roles=["intuition"], rerank_client=FakeServiceLLM())
    assert seen[-1]["source_objects"] == [("ext_text", "t2")]


# -- configuration ----------------------------------------------------------------------------------


def test_every_roles_key_and_the_route_are_classified_as_operational_switches_and_bounds():
    from learnloop.config.schema import LearnLoopConfig, RolesConfig
    from learnloop.params.parameter_registry import classify_config_path

    keys = [f"roles.{name}" for name in RolesConfig.model_fields]
    assert keys == ["roles.on_demand_enabled", "roles.positive_filter_enabled", "roles.batch_max_cost_usd"]
    for path in [*keys, "ai.routing.role_labeller"]:
        rule = classify_config_path(path)
        assert rule is not None, path
        assert (rule.kind, rule.param_class) == ("structural", "operational"), path
    defaults = LearnLoopConfig().roles
    assert (defaults.on_demand_enabled, defaults.positive_filter_enabled, defaults.batch_max_cost_usd) == (
        True, True, 5.0)
    assert LearnLoopConfig().ai.routing.role_labeller is None


def test_the_reader_report_counts_proposals_by_role_judge_and_agreement(library):
    from learnloop.reader.reader_report import build_reader_report

    paths, repository, _spans = library
    _propose(paths, repository, [_claim("t3", "contrast", "high"), _claim("t2", "intuition", "low")])
    _propose(paths, repository, [_claim("t3", "contrast", "medium")], judge=RS.JUDGE_CUE,
             prompt_version="passage_cue_judge.v2")
    report = build_reader_report(paths.sqlite_path)["roles"]
    assert report == {"proposals": 2, "by_role": {"contrast": 1, "intuition": 1},
                      "by_confidence": {"medium": 1, "low": 1},
                      "versions_by_judge": {"role_labeller": 2, "passage_cue_judge": 1}, "agreed": 1,
                      "reviewed": {"proposed": 2}}
    assert "Swapping" not in json.dumps(report)  # counts and labels only, never passage text
