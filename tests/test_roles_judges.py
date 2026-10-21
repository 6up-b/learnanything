"""RW4e: the Reader's two judges propose roles at no extra call (spec_reader_workbench_v1 §7.9, §6.2, §7.3).

* The cue judge (RW3b) already returns per-passage roles with a confidence:
  with ``roles.on_demand_enabled`` every judged passage's roles become
  proposals; its request (prompt and schema) is the same either way, and a
  missing or malformed ``roles`` field never fails its links.
* The library organizer (RW4a): off, RW4a's request exactly; on, RW4e's
  (roles optional, each with a confidence), whose roles become proposals; its
  lines, verdicts and order survive a missing or malformed roles field.
* A second judge agreeing on a passage's role adds a version.
* RW3b prefers contrast and counterexample passages for distinction cues
  through its extra list; library answers group a proposed role, labelled the
  model's. All of it only while ``roles.positive_filter_enabled`` is on.
Fakes only.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from learnloop.reader import source_roles as RS
from learnloop.source_retrieval import library_ask as LA
from learnloop.source_retrieval import passage_cues as PC
from tests.library_ask_fixtures import OrganizerFake, call, context
from tests.passage_cue_fakes import CueJudgeFake, build_cue_vault, loaded, set_config

QUESTION = "why does the determinant change sign when two rows are swapped"
#: The base tree's (a12ba5ba9) JSON schemas of the two judges' RW3b/RW4a
#: results: RW4e's tolerant parsing changes neither, so no request identity
#: (input hash, ledger ids) moves.
BASE_SCHEMA_SHA = {
    "CueJudgeResult": "a90da02592f8025e95ed3b5996709b383e57392f22386a1dc0f9a717953f6ce2",
    "OrganizerResult": "9780ce231c887b28e17e8457a9a5238517b0f8f004792599ec7fa20f059e827c",
}


@pytest.fixture
def library(tmp_path):
    paths, repository, spans = build_cue_vault(tmp_path / "vault")
    return paths, repository, spans


def _proposals(repository) -> list[dict]:
    with repository.connection() as connection:
        return [{**dict(row), "content": json.loads(row["content_json"])} for row in connection.execute(
            "SELECT v.source_object_id, v.version_ordinal, v.authorial_role, v.object_type, v.status, "
            "v.content_json, c.span_id FROM source_object_versions v "
            "JOIN source_object_citations c ON c.source_object_version_id = v.id "
            "ORDER BY v.source_object_id, v.version_ordinal")]


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_the_judges_result_schemas_are_the_base_trees():
    for model in (PC.CueJudgeResult, LA.OrganizerResult):
        schema = json.dumps(model.model_json_schema(), sort_keys=True)
        assert hashlib.sha256(schema.encode()).hexdigest() == BASE_SCHEMA_SHA[model.__name__], model.__name__


# -- the cue judge ------------------------------------------------------------------------------------


class _ReshapedCueJudge(CueJudgeFake):
    """The cue judge whose answer's ``roles`` field is missing or malformed."""

    def __init__(self, shape: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.shape = shape

    def complete(self, request):
        answer = super().complete(request).model_dump()
        for judgment in answer["judgments"]:
            if self.shape == "missing":
                judgment.pop("roles")
            elif self.shape == "string":
                judgment["roles"] = "contrast"
            elif self.shape == "entries":
                judgment["roles"] = [{"role": "contrast"}, {"role": "intuition", "confidence": "sure"}, None,
                                     {"role": "definition", "confidence": "low"}]
        return PC.CueJudgeResult.model_validate(answer)


def test_the_cue_judges_roles_become_proposals_for_every_judged_passage(library):
    paths, repository, _spans = library
    judge = CueJudgeFake(roles=(("contrast", "high"), ("definition", "medium")))
    result = PC.discover(loaded(paths), repository, "ext_text", client=judge)
    assert result["judged"] == 1 and len(judge.prompts) == 1  # no extra call
    candidates = [candidate["ref"] for candidate in judge.contexts[0]["candidates"]]
    rows = _proposals(repository)
    assert {(row["authorial_role"], row["content"]["confidence"]) for row in rows} == {
        ("contrast", "high"), ("definition", "medium")}
    # Every judged passage (not only the picks), two roles each, one version each.
    assert len(rows) == 2 * len(candidates) and {row["version_ordinal"] for row in rows} == {1}
    with repository.connection() as connection:
        ledger = {row[0]: row[1] for row in connection.execute(
            "SELECT id, right_id FROM judgment_ledger WHERE task = 'passage_cue'")}
    for row in rows:
        assert row["content"]["judge"] == "passage_cue_judge"
        assert row["content"]["prompt_version"] == PC.PROMPT_VERSION
        assert ledger[row["content"]["ledger_id"]] == f"ext_text/{row['span_id']}"
        assert row["status"] == "proposed"


@pytest.mark.parametrize("shape", ["missing", "string", "entries"])
def test_a_missing_or_malformed_roles_field_never_fails_the_cue_judges_links(library, shape):
    paths, repository, _spans = library
    plain = build_cue_vault(paths.root.parent / "plain")
    expected = PC.discover(loaded(plain[0]), plain[1], "ext_text", client=CueJudgeFake())
    result = PC.discover(loaded(paths), repository, "ext_text", client=_ReshapedCueJudge(shape))
    assert result["judged"] == 1
    links = [len(target.get("links") or ()) for target in result["targets"]]
    assert links == [len(target.get("links") or ()) for target in expected["targets"]] and sum(links) >= 1
    rows = _proposals(repository)
    if shape == "entries":
        # Only the well-formed entry is kept.
        assert {(row["authorial_role"], row["content"]["confidence"]) for row in rows} == {("definition", "low")}
    else:
        assert rows == []


def test_with_on_demand_off_the_cue_judge_writes_nothing_and_asks_the_same(library, tmp_path):
    paths, repository, _spans = library
    on_judge = CueJudgeFake()
    PC.discover(loaded(paths), repository, "ext_text", client=on_judge)
    assert _proposals(repository)
    off_paths, off_repository, _ = build_cue_vault(tmp_path / "off")
    set_config(off_paths, "roles", on_demand_enabled=False)
    off_judge = CueJudgeFake()
    result = PC.discover(loaded(off_paths), off_repository, "ext_text", client=off_judge)
    assert result["judged"] == 1 and _proposals(off_repository) == []
    assert [_sha(prompt) for prompt in off_judge.prompts] == [_sha(prompt) for prompt in on_judge.prompts]


# -- the library organizer -----------------------------------------------------------------------------


def _notes(paths, fake, **extra):
    ctx = context(paths.root)
    ctx.library_organizer_client = fake
    asked = call(ctx, "reader.library_ask", {"query": QUESTION, "extractionId": "ext_text", "spanIds": ["t3"],
                                             "learningObjectIds": ["lo_matrices"], **extra})
    return asked, call(ctx, "reader.library_ask_notes", {"askId": asked["askId"]})


def test_the_organizer_asks_rw4es_request_and_its_roles_become_proposals(library):
    paths, repository, _spans = library
    fake = OrganizerFake(wrong_cite=("p2",), roles=(("definition", "high"), ("not_a_role", "high"),
                                                    ("intuition", "low")))
    asked, notes = _notes(paths, fake)
    assert len(fake.prompts) == 1  # no extra call
    assert LA.ROLES_PROMPT_VERSION in fake.prompts[0] and "each with a confidence" in fake.prompts[0]
    assert notes["status"] == "judged"
    keys = [hit["key"] for hit in asked["hits"]]
    by_key = {note["key"]: note for note in notes["notes"]}
    assert by_key[keys[0]]["roles"] == ["definition", "intuition"]  # names, as RW4a's notes
    assert by_key[keys[1]]["line"] is None  # its line cites another passage: still dropped
    rows = _proposals(repository)
    assert {row["span_id"] for row in rows} == {key.split(":", 1)[1] for key in keys}
    assert {(row["authorial_role"], row["content"]["confidence"]) for row in rows} == {
        ("definition", "high"), ("intuition", "low")}
    assert {row["content"]["judge"] for row in rows} == {"library_organizer"}
    assert {row["content"]["prompt_version"] for row in rows} == {LA.ROLES_PROMPT_VERSION}
    assert {row["object_type"] for row in rows} == {"definition", "motif_or_passage"}


@pytest.mark.parametrize("shape", ["missing", "string", "entries"])
def test_a_missing_or_malformed_roles_field_never_fails_the_organizers_lines(library, tmp_path, shape):
    paths, repository, _spans = library
    good_paths, _good_repo, _ = build_cue_vault(tmp_path / "good")
    _good_ask, good = _notes(good_paths, OrganizerFake(wrong_cite=("p2",), reverse=True))
    _asked, notes = _notes(paths, OrganizerFake(wrong_cite=("p2",), reverse=True, malformed_roles=shape))
    assert notes["status"] == "judged"
    assert [(n["key"], n["line"], n["verdict"]) for n in notes["notes"]] == [
        (n["key"], n["line"], n["verdict"]) for n in good["notes"]]
    assert notes["order"] == good["order"] and notes["droppedLines"] == good["droppedLines"]
    assert all(note["roles"] == [] for note in notes["notes"])
    assert _proposals(repository) == []


def test_with_on_demand_off_the_organizer_asks_rw4as_request_and_writes_nothing(library):
    paths, repository, _spans = library
    set_config(paths, "roles", on_demand_enabled=False)
    fake = OrganizerFake()
    _asked, notes = _notes(paths, fake)
    assert LA.PROMPT_VERSION in fake.prompts[0] and LA.ROLES_PROMPT_VERSION not in fake.prompts[0]
    assert "each with a confidence" not in fake.prompts[0]
    assert all(note["roles"] == ["definition"] for note in notes["notes"])
    assert "roleProposals" not in notes and _proposals(repository) == []


def test_two_judges_agreeing_on_a_passages_role_make_one_proposal_with_two_versions(library):
    paths, repository, _spans = library
    PC.discover(loaded(paths), repository, "ext_text", client=CueJudgeFake(roles=(("definition", "medium"),)))
    _notes(paths, OrganizerFake(roles=(("definition", "high"),)))
    rows = [row for row in _proposals(repository) if row["span_id"] == "t3" and row["authorial_role"] == "definition"]
    assert [(row["version_ordinal"], row["content"]["judge"]) for row in rows] == [
        (1, "passage_cue_judge"), (2, "library_organizer")]
    assert len({row["source_object_id"] for row in rows}) == 1
    (label,) = [label for label in RS.role_proposals(loaded(paths), repository, roles=["definition"])
                if label.key == ("ext_text", "t3")]
    assert label.judges == ("passage_cue_judge", "library_organizer") and label.confidence == "high"


# -- positive use: RW3b's contrast preference, library grouping -------------------------------------------


def _claim(span_id: str, role: str, confidence: str = "high", extraction_id: str = "ext_text") -> dict:
    return {"extraction_id": extraction_id, "span_id": span_id, "role": role, "confidence": confidence,
            "ledger_id": "rlb_test"}


def test_rw3b_prefers_contrast_and_counterexample_passages_for_distinction_cues(library):
    paths, repository, _spans = library
    vault = loaded(paths)
    (target,) = PC.cue_targets(vault, repository, "ext_text")
    without = PC.shortlist(vault, repository, target, "ext_text", deep=False)
    assert "contrast" not in without.lists
    RS.propose_roles(vault, repository, [_claim("t2", "contrast")], judge=RS.JUDGE_LABELLER,
                     prompt_version="role_labeller.v1")
    vault = loaded(paths)
    preferred = PC.shortlist(vault, repository, target, "ext_text", deep=False)
    assert preferred.lists.get("contrast") == 1
    assert "contrast" in preferred.ranks[("ext_text", "t2")]
    # It ranks no lower than without its contrast role (the list only adds evidence).
    assert preferred.keys.index(("ext_text", "t2")) <= (
        without.keys.index(("ext_text", "t2")) if ("ext_text", "t2") in without.keys else len(without.keys))
    # A contrast on a passage outside the target's LOs (or their confusables) is not added.
    RS.propose_roles(vault, repository, [_claim("t7", "counterexample")], judge=RS.JUDGE_LABELLER,
                     prompt_version="role_labeller.v1")
    assert PC.contrast_list(loaded(paths), repository, target, "ext_text") == [("ext_text", "t2")]
    set_config(paths, "roles", positive_filter_enabled=False)
    off = loaded(paths)
    assert PC.contrast_list(off, repository, target, "ext_text") == []
    assert "contrast" not in PC.shortlist(off, repository, target, "ext_text", deep=False).lists


def test_rw3b_contrast_list_takes_a_low_confidence_proposal_only_when_none_better_is_on_target(library):
    """Codex review F3: a confident counterexample outside the target's LOs
    (and its confusables) never blocks a low-confidence contrast on them."""

    paths, repository, _spans = library
    vault = loaded(paths)
    (target,) = PC.cue_targets(vault, repository, "ext_text")
    RS.propose_roles(vault, repository, [_claim("t7", "counterexample"), _claim("t2", "contrast", "low")],
                     judge=RS.JUDGE_LABELLER, prompt_version="role_labeller.v1")
    assert PC.contrast_list(loaded(paths), repository, target, "ext_text") == [("ext_text", "t2")]


def test_library_answers_group_a_proposed_role_labelled_as_the_models(library):
    paths, repository, _spans = library
    vault = loaded(paths)
    RS.propose_roles(vault, repository, [_claim("t3", "counterexample"), _claim("t3", "intuition", "low"),
                                         _claim("s2", "application", "medium", "ext_book")],
                     judge=RS.JUDGE_LABELLER, prompt_version="role_labeller.v1")
    ctx = context(paths.root)
    asked = call(ctx, "reader.library_ask", {"query": QUESTION, "extractionId": "ext_text", "spanIds": ["t3"],
                                             "learningObjectIds": ["lo_matrices"]})
    by_key = {hit["key"]: hit for hit in asked["hits"]}
    assert by_key["ext_text:t3"]["proposedRole"] == {"role": "counterexample", "confidence": "high",
                                                     "judges": ["role_labeller"], "label": "model's label"}
    assert by_key["ext_text:t3"]["group"] == "Contrast"
    assert by_key["ext_book:s2"]["group"] == "Application" and by_key["ext_book:s2"]["proposedRole"]["role"] == (
        "application")
    # Ingest's own roles keep their groups; passages without a proposal carry none.
    for key, hit in by_key.items():
        if key not in ("ext_text:t3", "ext_book:s2"):
            assert "proposedRole" not in hit
            assert hit["group"] in LA.GROUP_ORDER or hit["expansion"]
    groups = {group["group"] for source in asked["groups"]["sources"] for group in source["groups"]}
    assert {"Contrast", "Application"} <= groups
    for source in asked["groups"]["sources"]:
        names = [group["group"] for group in source["groups"]]
        assert names == [name for name in LA.ROLE_GROUP_ORDER if name in names]
    # Off: RW4a's grouping and no proposed role.
    set_config(paths, "roles", positive_filter_enabled=False)
    off = call(context(paths.root), "reader.library_ask", {"query": QUESTION, "extractionId": "ext_text",
                                                           "spanIds": ["t3"], "learningObjectIds": ["lo_matrices"]})
    assert all("proposedRole" not in hit for hit in off["hits"])
    assert {hit["key"]: hit["group"] for hit in off["hits"]}["ext_text:t3"] == "Explanation"


def test_rw3b_contrast_list_a_confident_contrast_the_judge_may_not_be_shown_never_blocks_the_low_one(library):
    """Fix round 3 (the one effective eligibility): a confident
    counterexample on the target's LO that the shortlist's pool would drop
    (a solution block: the model-reader filter) is no stronger candidate, so
    the low-confidence contrast on the target counts; once the confident one
    is on a passage the judge may read, it alone is the list, as before."""

    from learnloop.ingest.locators import format_block_span

    paths, repository, spans = library
    solution = spans["solutions"][1]
    # The solution (and t3) teach the target's LO too (provenance links to it).
    for span_id in (solution, "t3"):
        repository.insert_entity_source_link(
            entity_type="learning_object", entity_id="lo_matrices", locator=format_block_span("ext_text", span_id),
            relation="primary", source_id="src_text", revision_id="rev_text", extraction_id="ext_text")
    vault = loaded(paths)
    (target,) = PC.cue_targets(vault, repository, "ext_text")
    RS.propose_roles(vault, repository, [_claim(solution, "counterexample"), _claim("t2", "contrast", "low")],
                     judge=RS.JUDGE_LABELLER, prompt_version="role_labeller.v1")
    vault = loaded(paths)
    assert PC.contrast_list(vault, repository, target, "ext_text") == [("ext_text", "t2")]
    shortlisted = PC.shortlist(vault, repository, target, "ext_text", deep=False)
    assert shortlisted.lists.get("contrast") == 1 and ("ext_text", "t2") in shortlisted.keys
    assert ("ext_text", solution) not in shortlisted.keys
    # A confident contrast the judge may read wins over the low one, as before.
    RS.propose_roles(vault, repository, [_claim("t3", "counterexample")], judge=RS.JUDGE_LABELLER,
                     prompt_version="role_labeller.v1")
    assert PC.contrast_list(loaded(paths), repository, target, "ext_text") == [("ext_text", "t3")]
