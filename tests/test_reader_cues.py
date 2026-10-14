"""Reader workbench RW3a: margin cues from the Guide (spec_reader_workbench_v1 §6).

The Guide's own ``recent_misunderstanding`` passages become quiet margin marks:
the margin and the rail agree (G30), the copy is fixed templates that say what
connects (G16), each section shows at most the learner's density budget (G14),
held-out and exam material never carries a cue, taps are salience-only events
and ``learner_card`` verdicts on ``passage_cue``, and nothing a cue does reaches
evidence, mastery, projections, FSRS or the plan (G13). Fakes only.
"""

from __future__ import annotations

import json
import re
import tomllib

import pytest

from learnloop.attempts import salience_firewall as SF
from learnloop.clock import FrozenClock
from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.reader import reader_cues as RCU
from learnloop.reader import reader_inquiry as RI
from learnloop.reader.reader_guidance import build_guide_plan
from learnloop.vault.loader import load_vault
from learnloop.vault.models import SourceRef
from learnloop.vault.writer import upsert_practice_item
from tests.helpers import NOW, NOW_ISO, add_followup_item, append_config_toml, create_basic_vault
from tests.reader_fixtures import transcript_source
from tests.test_reader_inquiry_status import table_counts
from tests.test_sidecar_reader import _init, _rpc
from tests.test_source_inventory import _persist, _register_revision

_CLOCK = FrozenClock(NOW)
STATEMENT = "SVD is the same as eigendecomposition"
#: Trait words and, about the learner's work, verdict words (spec G16, UX U6).
BANNED = re.compile(
    r"\b(weak|you don'?t understand|you struggle|you always|wrong|error|errors|mistake|mistakes|"
    r"confused|failed|failure|overdue)\b",
    re.IGNORECASE,
)


def _ir() -> DocumentIR:
    """Two sections: u1 (s0-s3) is read, u2 (s4-s5) holds the exercises."""

    text = {
        "s1": "The singular value decomposition writes A as U Sigma V transpose.",
        "s2": "The columns of U and V are orthonormal.",
        "s3": "Sigma holds the singular values on its diagonal.",
        "s5": "Exercise 2.1: compute the SVD of a 2 by 2 matrix.",
    }
    blocks = [
        DocumentBlock.build(span_id="s0", block_type="Section", text="Singular value decomposition",
                            ordinal=0, page=1, section_path=["SVD"]),
        *[DocumentBlock.build(span_id=span, block_type="Text", text=text[span], ordinal=index + 1, page=1,
                              section_path=["SVD"]) for index, span in enumerate(("s1", "s2", "s3"))],
        DocumentBlock.build(span_id="s4", block_type="Section", text="Exercises", ordinal=4, page=2,
                            section_path=["Exercises"]),
        DocumentBlock.build(span_id="s5", block_type="Text", text=text["s5"], ordinal=5, page=2,
                            section_path=["Exercises"]),
    ]
    units = [
        DocumentUnit(unit_id="u1", label="SVD", ordinal=0, semantic_hash="sha256:svd", page_start=1, page_end=1,
                     span_ids=["s0", "s1", "s2", "s3"]),
        DocumentUnit(unit_id="u2", label="Exercises", ordinal=1, semantic_hash="sha256:ex", page_start=2,
                     page_end=2, span_ids=["s4", "s5"]),
    ]
    return DocumentIR(extractor="marker", extractor_version="1", units=units, blocks=blocks, assets=[],
                      health=ExtractionHealth())


def _refs(spans) -> list[SourceRef]:
    return [SourceRef(ref_type="canonical_source", ref_id="src1", locator=f"span:ext1/{span}",
                      source_id="src1", extraction_id="ext1") for span in spans]


def _active_error(repository: Repository, *, error_id: str = "err-svd", attempt_id: str | None = None) -> None:
    event = {
        "id": error_id, "learning_object_id": "lo_svd_definition", "error_type": "conceptual_slip",
        "severity": 0.9, "is_misconception": True, "status": "active", "created_at": NOW_ISO,
        "misconception_statement": STATEMENT,
    }
    if attempt_id:
        event["attempt_id"] = attempt_id
    repository.insert_error_event(event)


def _cue_vault(tmp_path, *, cite=("s1", "s2", "s3", "s5"), error: bool = True, on_disk: bool = False, config: str = ""):
    """The basic vault with ``ext1`` (two sections) and pi_svd_define_001
    citing ``cite``; an active error on its LO makes every cited passage a
    ``recent_misunderstanding`` passage of the Guide."""

    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    if config:
        append_config_toml(root, config)
    repository = Repository(paths.sqlite_path)
    _register_revision(repository, source_id="src1", revision_id="rev1")
    _persist(repository, _ir(), revision_id="rev1", extraction_id="ext1")
    vault = load_vault(root)
    item = vault.practice_items["pi_svd_define_001"]
    item.provenance.source_refs = _refs(cite)
    if on_disk:
        upsert_practice_item(root, item, clock=_CLOCK)
        vault = load_vault(root)
    if error:
        _active_error(repository)
    return root, vault, repository


def _plan_and_cues(vault, repository):
    plan = build_guide_plan(vault, repository, extraction_id="ext1")
    return plan, RCU.guide_cues(vault, repository, extraction_id="ext1", plan=plan)


# -- G30: the margin and the rail agree ---------------------------------------------------------


def test_each_cue_is_one_of_the_rails_misunderstanding_passages_in_the_rails_order(tmp_path):
    _root, vault, repository = _cue_vault(tmp_path)
    plan, cues = _plan_and_cues(vault, repository)
    rail = {
        section["id"]: [p for p in section["suggested_passages"] if p["learner_signal"] == "recent_misunderstanding"]
        for section in plan["sections"]
    }
    assert [p["span_id"] for p in rail["u1"]] == ["s1", "s2", "s3"]
    assert cues["marks"], cues
    for mark in cues["marks"]:
        (passage,) = [p for p in rail[mark["section_id"]] if p["span_id"] == mark["span_id"]]
        assert mark["learning_object_id"] == passage["learning_object_id"]
        assert mark["learning_object_title"] == passage["learning_object_title"]
        # The rail's reason and the cue's earlier work name the same statement.
        assert passage["reason"] == f"Revisit this to resolve: {mark['earlier']['statement']}."
    by_section: dict[str, list[str]] = {}
    for mark in cues["marks"]:
        by_section.setdefault(mark["section_id"], []).append(mark["span_id"])
    for section_id, spans in by_section.items():
        assert spans == [p["span_id"] for p in rail[section_id]][: len(spans)]


def test_no_misunderstanding_no_cue(tmp_path):
    _root, vault, repository = _cue_vault(tmp_path, error=False)
    plan, cues = _plan_and_cues(vault, repository)
    assert any(section["suggested_passages"] for section in plan["sections"])
    assert cues["marks"] == []


# -- G14: the density budget; every section, every density --------------------------------------


@pytest.mark.parametrize("density,budget,expected_u1", [("off", 0, 0), ("fewer", 1, 1), ("normal", 2, 2), ("more", 4, 3)])
def test_no_section_shows_more_cues_than_the_density_budget(tmp_path, density, budget, expected_u1):
    _root, vault, repository = _cue_vault(tmp_path, config=f'[cues]\ndensity = "{density}"\n')
    _plan, cues = _plan_and_cues(vault, repository)
    assert cues["density"] == density and cues["budget_per_section"] == budget
    counts: dict[str, int] = {}
    for mark in cues["marks"]:
        counts[mark["section_id"]] = counts.get(mark["section_id"], 0) + 1
    assert all(count <= budget for count in counts.values())
    # The Guide lists at most three passages a section: "more" shows all three.
    assert counts.get("u1", 0) == expected_u1
    assert cues["withheld"]["density"] == 3 - expected_u1 + (1 if budget == 0 else 0)


def test_cues_are_ranked_each_sections_first_before_any_second(tmp_path):
    _root, vault, repository = _cue_vault(tmp_path)
    _plan, cues = _plan_and_cues(vault, repository)
    assert [(m["section_id"], m["span_id"], m["rank"]) for m in cues["marks"]] == [
        ("u1", "s1", 0), ("u2", "s5", 1), ("u1", "s2", 2),
    ]


def test_the_default_is_normal_one_per_viewport_and_on(tmp_path):
    _root, vault, repository = _cue_vault(tmp_path)
    _plan, cues = _plan_and_cues(vault, repository)
    assert (cues["density"], cues["budget_per_section"], cues["one_per_viewport"], cues["source_off"]) == (
        "normal", 2, True, False)


# -- never on held-out or exam material ----------------------------------------------------------


def test_a_held_out_section_never_carries_a_cue_though_the_rail_still_lists_it(tmp_path):
    _root, vault, repository = _cue_vault(tmp_path)
    save_unit_selection(repository, "ext1", ["u1", "u2"], exam_use_modes={"u2": "held_out_evaluation"})
    plan, cues = _plan_and_cues(vault, repository)
    by_id = {section["id"]: section for section in plan["sections"]}
    assert [p["span_id"] for p in by_id["u2"]["suggested_passages"]] == ["s5"]
    assert "s5" not in {mark["span_id"] for mark in cues["marks"]}
    assert {mark["section_id"] for mark in cues["marks"]} == {"u1"}
    assert cues["withheld"]["held_out"] == 1


def test_exam_material_never_carries_a_cue(tmp_path):
    from learnloop.vault.writer import upsert_source_set

    root, _vault, repository = _cue_vault(tmp_path, on_disk=True)
    upsert_source_set(root, {
        "id": "set_exam", "subject_id": "linear-algebra", "title": "The exam",
        "members": [{"source_id": "src1", "revision_id": "rev1", "default_role": "exam",
                     "scope": [{"unit_id": "u1"}, {"unit_id": "u2"}], "priority": 1}],
    }, clock=_CLOCK)
    vault = load_vault(root)
    _plan, cues = _plan_and_cues(vault, repository)
    assert cues["marks"] == []
    assert cues["withheld"]["held_out"] == 4


def test_a_cue_on_held_out_material_cannot_be_tapped(tmp_path):
    _root, vault, repository = _cue_vault(tmp_path)
    plan, cues = _plan_and_cues(vault, repository)
    s5 = next(mark for mark in cues["marks"] if mark["span_id"] == "s5")
    save_unit_selection(repository, "ext1", ["u1", "u2"], exam_use_modes={"u2": "held_out_evaluation"})
    plan = build_guide_plan(vault, repository, extraction_id="ext1")
    with pytest.raises(RCU.CueError):
        RCU.find_cue(vault, repository, extraction_id="ext1", cue_id=s5["cue_id"], plan=plan)


# -- G16: fixed templates that say what connects ------------------------------------------------


def test_cue_copy_is_fixed_templates_that_never_judge_the_learner(tmp_path):
    for template in RCU.CUE_TEMPLATES:
        assert not BANNED.search(template), template
    assert RCU.BECAUSE_TEMPLATE.endswith("from the Guide's citations")
    _root, vault, repository = _cue_vault(tmp_path)
    _plan, cues = _plan_and_cues(vault, repository)
    for mark in cues["marks"]:
        assert mark["note"] == RCU.render_note(mark["learning_object_title"])
        assert mark["note"] == "Connects to something you worked on: SVD definition."
        assert mark["because"] == RCU.render_because(mark["earlier"]["answered_on"])
        assert mark["because"].endswith("· from the Guide's citations")
        assert mark["label"] == f"Note on this paragraph: {mark['note']} {mark['because']}"
        # The rail's "Revisit this to resolve" stays in the rail only.
        assert "Revisit" not in mark["note"] + mark["because"] + mark["label"]
        assert STATEMENT not in mark["note"] + mark["because"]
        assert not BANNED.search(mark["note"] + " " + mark["because"])


# -- G30 on the split: the diagnoser's statement, as the rail names it ---------------------------


def test_a_split_cue_names_the_diagnosers_statement_as_the_rail_does(tmp_path):
    from learnloop.diagnosis.split.jobs import DONE, diagnosis_status
    from tests.split_live_helpers import drain_jobs, submit
    from tests.test_reader_guidance import _DIAGNOSED, _StatementFake, _cite_extraction, _graded_vault_with_extraction

    _paths, vault, repository = _graded_vault_with_extraction(tmp_path, version="mvp-0.10")
    client = _StatementFake()
    result = submit(vault, repository, client)
    pending_plan = None
    _cite_extraction(vault)
    pending_plan, pending = _plan_and_cues(vault, repository)
    (mark,) = [m for m in pending["marks"] if m["learning_object_id"] == "lo_svd_compute"]
    assert mark["earlier"]["statement_pending"] is True
    drain_jobs(vault, repository, client)
    assert diagnosis_status(repository, result.attempt_id)["status"] == DONE
    plan, cues = _plan_and_cues(vault, repository)
    (mark,) = [m for m in cues["marks"] if m["learning_object_id"] == "lo_svd_compute"]
    (passage,) = [p for p in plan["sections"][0]["suggested_passages"] if p["span_id"] == mark["span_id"]]
    assert _DIAGNOSED in passage["reason"]
    assert mark["earlier"]["statement"] == _DIAGNOSED
    assert mark["earlier"]["statement_pending"] is False
    assert mark["earlier"]["attempt_id"] == result.attempt_id
    assert mark["earlier"]["practice_item_id"] == "pi_svd_compute_001"
    assert mark["earlier"]["prompt"]
    # "Open" shows the cited attempt itself: the learner's own answer (review F7).
    assert mark["earlier"]["answer"] == "A = U Sigma V wrong"
    assert mark["because"] == f"Because: your answer on {mark['earlier']['answered_on']} · from the Guide's citations"
    # The note never repeats the statement (details on demand: "Open").
    assert _DIAGNOSED not in mark["note"]
    assert pending_plan is not None


# -- "Open" shows the earlier work: the learner's own answer (review F7) -------------------------


def _attempt(repository: Repository, *, attempt_id: str, answer: str | None) -> None:
    repository.insert_practice_attempt({
        "id": attempt_id, "practice_item_id": "pi_svd_define_001", "learning_object_id": "lo_svd_definition",
        "subject": "linear-algebra", "concept": "singular_value_decomposition", "practice_mode": "short_answer",
        "attempt_type": "independent_attempt", "learner_answer_md": answer, "evidence_facets": ["recall"],
        "evidence_weights": {"recall": 1.0}, "rubric_score": 1, "correctness": 0.25, "confidence": 3,
        "latency_seconds": 30, "hints_used": 0, "error_type": "conceptual_slip", "grader_confidence": 1.0,
        "created_at": NOW_ISO, "updated_at": NOW_ISO,
    })


def test_open_carries_the_cited_attempts_answer_in_the_learners_words(tmp_path):
    _root, vault, repository = _cue_vault(tmp_path, error=False)
    answer = "SVD is just the eigendecomposition.\n\nSo Sigma holds the eigenvalues."
    _attempt(repository, attempt_id="att-svd", answer=answer)
    _active_error(repository, attempt_id="att-svd")
    _plan, cues = _plan_and_cues(vault, repository)
    assert cues["marks"]
    for mark in cues["marks"]:
        earlier = mark["earlier"]
        assert earlier["attempt_id"] == "att-svd"
        # Verbatim, line breaks kept: the learner's voice, not a summary.
        assert earlier["answer"] == answer
        # Never in the note or the "because" line (details on demand).
        assert "eigendecomposition" not in mark["note"] + mark["because"] + mark["label"]


def test_a_long_answer_is_clipped_and_an_error_without_an_attempt_has_none(tmp_path):
    _root, vault, repository = _cue_vault(tmp_path, error=False)
    _attempt(repository, attempt_id="att-long", answer="word " * 400)
    _active_error(repository, attempt_id="att-long")
    _plan, cues = _plan_and_cues(vault, repository)
    clipped = cues["marks"][0]["earlier"]["answer"]
    assert clipped.endswith("…") and len(clipped) <= RCU.MAX_ANSWER_CHARS
    _root2, vault2, repository2 = _cue_vault(tmp_path / "bare")
    _plan2, bare = _plan_and_cues(vault2, repository2)
    assert bare["marks"] and all(mark["earlier"]["answer"] is None for mark in bare["marks"])


# -- taps: events and learner_card verdicts ------------------------------------------------------


def _ledger(repository: Repository) -> list[dict]:
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT id, left_id, right_id, verdict, supersedes_id, judge, rationale FROM judgment_ledger "
            "WHERE task = 'passage_cue' ORDER BY created_at, id"
        ).fetchall()
    return [dict(zip(("id", "left_id", "right_id", "verdict", "supersedes_id", "judge", "rationale"), row)) for row in rows]


def _cue_events(repository: Repository) -> list[dict]:
    return [event for event in repository.reader_interaction_events(kind="reader_action_invoked")
            if str(event["payload"].get("event", "")).startswith("cue_")]


def test_taps_are_salience_only_events_and_learner_card_verdicts(tmp_path):
    _root, vault, repository = _cue_vault(tmp_path)
    _plan, cues = _plan_and_cues(vault, repository)
    mark = cues["marks"][0]
    opened = RCU.record_cue_tap(repository, extraction_id="ext1", cue=mark, action="opened", clock=_CLOCK)
    assert opened["verdict"] == "same" and opened["ledger_id"]
    again = RCU.record_cue_tap(repository, extraction_id="ext1", cue=mark, action="opened", clock=_CLOCK)
    assert again["ledger_id"] is None  # a repeated verdict appends nothing
    checked = RCU.record_cue_tap(repository, extraction_id="ext1", cue=mark, action="check_me", clock=_CLOCK)
    assert checked["ledger_id"] is None and checked["verdict"] == "same"
    off = RCU.record_cue_tap(repository, extraction_id="ext1", cue=mark, action="not_relevant",
                             text="It's about the transpose, not this.", clock=_CLOCK)
    assert off["verdict"] == "different"
    ledger = _ledger(repository)
    assert [(row["verdict"], row["judge"]) for row in ledger] == [("same", "learner_card"), ("different", "learner_card")]
    assert ledger[1]["supersedes_id"] == ledger[0]["id"]
    assert ledger[0]["left_id"] == f"ext1/{mark['span_id']}" and ledger[0]["right_id"] == mark["target_id"]
    assert "It's about the transpose, not this." in ledger[1]["rationale"]
    events = _cue_events(repository)
    assert [event["payload"]["event"] for event in events] == ["cue_opened", "cue_opened", "cue_check_me", "cue_not_relevant"]
    for event in events:
        assert event["payload"]["authority_class"] == SF.SALIENCE_ONLY
        with pytest.raises(SF.SalienceEvidenceRejected):
            SF.reject_salience(event)
        assert "transpose" not in json.dumps(event["payload"])
    assert events[-1]["payload"]["has_text"] is True


def test_not_relevant_withholds_the_cue_until_the_learner_undoes_it(tmp_path):
    _root, vault, repository = _cue_vault(tmp_path)
    _plan, cues = _plan_and_cues(vault, repository)
    first = cues["marks"][0]
    RCU.record_cue_tap(repository, extraction_id="ext1", cue=first, action="not_relevant", clock=_CLOCK)
    _plan, after = _plan_and_cues(vault, repository)
    assert first["cue_id"] not in {mark["cue_id"] for mark in after["marks"]}
    assert after["withheld"]["not_relevant"] == 1
    # The next passage of the section moves up into the budget.
    assert [m["span_id"] for m in after["marks"] if m["section_id"] == "u1"] == ["s2", "s3"]
    plan = build_guide_plan(vault, repository, extraction_id="ext1")
    found = RCU.find_cue(vault, repository, extraction_id="ext1", cue_id=first["cue_id"], plan=plan)
    undone = RCU.record_cue_tap(repository, extraction_id="ext1", cue=found, action="not_relevant_undone", clock=_CLOCK)
    assert undone["verdict"] == "undone"
    _plan, back = _plan_and_cues(vault, repository)
    assert first["cue_id"] in {mark["cue_id"] for mark in back["marks"]}
    # Nothing to undo appends nothing.
    count = len(_ledger(repository))
    RCU.record_cue_tap(repository, extraction_id="ext1", cue=found, action="not_relevant_undone", clock=_CLOCK)
    assert len(_ledger(repository)) == count


def test_a_new_error_on_the_learning_object_is_a_new_cue(tmp_path):
    _root, vault, repository = _cue_vault(tmp_path)
    _plan, cues = _plan_and_cues(vault, repository)
    RCU.record_cue_tap(repository, extraction_id="ext1", cue=cues["marks"][0], action="not_relevant", clock=_CLOCK)
    repository.insert_error_event({
        "id": "err-svd-2", "learning_object_id": "lo_svd_definition", "error_type": "conceptual_slip",
        "severity": 1.0, "is_misconception": True, "status": "active", "created_at": NOW_ISO,
        "misconception_statement": "Sigma can be negative",
    })
    _plan, later = _plan_and_cues(vault, repository)
    assert later["withheld"]["not_relevant"] == 0
    assert later["marks"][0]["span_id"] == cues["marks"][0]["span_id"]
    assert later["marks"][0]["cue_id"] != cues["marks"][0]["cue_id"]


@pytest.mark.parametrize("event", RCU.SERVER_CUE_EVENTS)
def test_every_server_cue_event_is_salience_only(tmp_path, event):
    _root, vault, repository = _cue_vault(tmp_path)
    _plan, cues = _plan_and_cues(vault, repository)
    mark = cues["marks"][0]
    actions = {tap_event: action for action, (tap_event, _verdict) in RCU.CUE_TAP_ACTIONS.items()}
    if event in actions:
        if event == "cue_not_relevant_undone":
            RCU.record_cue_tap(repository, extraction_id="ext1", cue=mark, action="not_relevant", clock=_CLOCK)
        RCU.record_cue_tap(repository, extraction_id="ext1", cue=mark, action=actions[event], clock=_CLOCK)
    else:
        payload = {"event": event, "via": "footer", "from": "normal", "to": "fewer", "source_id": "src1"}
        RCU.log_preference_events(repository, [payload], extraction_id="ext1", clock=_CLOCK)
    rows = [e for e in repository.reader_interaction_events(kind="reader_action_invoked") if e["payload"].get("event") == event]
    assert rows
    for row in rows:
        assert row["payload"]["authority_class"] == SF.SALIENCE_ONLY
        with pytest.raises(SF.SalienceEvidenceRejected):
            SF.reject_salience(row)


def test_the_client_records_cue_impressions_and_cannot_forge_a_tap(tmp_path):
    _root, _vault, repository = _cue_vault(tmp_path)
    assert "cue_shown" in RI.CLIENT_ACTION_EVENTS
    (event_id,) = RI.record_activity(repository, [{
        "kind": "reader_action_invoked", "event": "cue_shown",
        "payload": {"visitId": "v1", "extractionId": "ext1", "spanId": "s1", "cueId": "cue_x", "cueKind": "revisit",
                    "density": "normal", "element": "margin_mark", "note": "a learner-facing sentence"},
    }], clock=_CLOCK)
    (row,) = [e for e in repository.reader_interaction_events() if e["id"] == event_id]
    assert row["payload"]["cue_id"] == "cue_x" and row["payload"]["density"] == "normal"
    assert "note" not in row["payload"]
    for forged in RCU.SERVER_CUE_EVENTS:
        with pytest.raises(RI.InquiryError):
            RI.record_activity(repository, [{"kind": "reader_action_invoked", "event": forged, "payload": {}}])


# -- G13: display only --------------------------------------------------------------------------


def test_cues_and_their_taps_write_no_evidence_mastery_fsrs_or_plan_row(tmp_path):
    _root, vault, repository = _cue_vault(tmp_path)
    before = table_counts(repository)
    _plan, cues = _plan_and_cues(vault, repository)
    assert table_counts(repository) == before  # computing cues reads only
    for action in ("opened", "check_me", "not_relevant", "not_relevant_undone"):
        RCU.record_cue_tap(repository, extraction_id="ext1", cue=cues["marks"][0], action=action, clock=_CLOCK)
    after = table_counts(repository)
    # The only writes: the taps' events (interaction_events is allowed) and
    # three learner_card verdicts (same, different, undone).
    assert after.pop("judgment_ledger") - before.pop("judgment_ledger") == 3
    assert after == before


def test_the_plan_with_cues_off_is_byte_identical_and_the_rail_unchanged(tmp_path):
    root, vault, repository = _cue_vault(tmp_path, on_disk=True)
    plan_rpc = _rpc([_init(root), {"jsonrpc": "2.0", "id": 2, "method": "reader.guide_plan",
                                    "params": {"extractionId": "ext1"}}])[1]["result"]
    assert plan_rpc["cues"]["marks"]
    append_config_toml(root, "[cues]\nenabled = false\n")
    off = _rpc([_init(root), {"jsonrpc": "2.0", "id": 2, "method": "reader.guide_plan",
                               "params": {"extractionId": "ext1"}}])[1]["result"]
    assert "cues" not in off
    on_without = {key: value for key, value in plan_rpc.items() if key != "cues"}
    assert json.dumps(on_without, sort_keys=True) == json.dumps(off, sort_keys=True)


# -- the RPCs: taps, check me, preferences ---------------------------------------------------------


def _call(root, method: str, params: dict) -> dict:
    return _rpc([_init(root), {"jsonrpc": "2.0", "id": 2, "method": method, "params": params}])[1]


def _marks(root) -> list[dict]:
    return _call(root, "reader.guide_plan", {"extractionId": "ext1"})["result"]["cues"]["marks"]


def test_cue_action_rpc_records_the_tap(tmp_path):
    root, _vault, repository = _cue_vault(tmp_path, on_disk=True)
    mark = _marks(root)[0]
    result = _call(root, "reader.cue_action", {"extractionId": "ext1", "cueId": mark["cueId"], "action": "opened"})["result"]
    assert result["verdict"] == "same" and result["check"] is None
    bad = _call(root, "reader.cue_action", {"extractionId": "ext1", "cueId": "cue_nope", "action": "opened"})
    assert bad["error"]["data"]["code"] == "validation_error"
    bad_action = _call(root, "reader.cue_action", {"extractionId": "ext1", "cueId": mark["cueId"], "action": "made_up"})
    assert bad_action["error"]["data"]["code"] == "validation_error"
    assert [e["payload"]["event"] for e in _cue_events(repository)] == ["cue_opened"]


def test_check_me_proposes_one_item_on_the_cues_learning_object(tmp_path):
    root, _vault, repository = _cue_vault(tmp_path, on_disk=True)
    add_followup_item(root)
    mark = _marks(root)[0]
    result = _call(root, "reader.cue_action", {"extractionId": "ext1", "cueId": mark["cueId"], "action": "check_me"})["result"]
    assert result["verdict"] == "same"
    check = result["check"]
    assert check["status"] == "found"
    assert check["practiceItemId"] in {"pi_svd_define_001", "pi_svd_define_002"}
    assert check["learningObjectId"] == "lo_svd_definition"
    assert check["proposalId"]
    assert [e["payload"]["event"] for e in _cue_events(repository)] == ["cue_check_me"]


def _answered_cue() -> dict:
    """A cue whose earlier work is an answer to pi_svd_define_001."""

    return {
        "cue_id": "cue_answered", "span_id": "s1", "learning_object_id": "lo_svd_definition",
        "learning_object_title": "SVD definition", "target_id": "err-svd",
        "earlier": {"practice_item_id": "pi_svd_define_001"},
    }


def test_check_me_never_offers_the_question_the_learner_answered(tmp_path):
    from learnloop_sidecar.handlers.reader import check_me_proposal

    root, vault, repository = _cue_vault(tmp_path, on_disk=True)
    request = RCU.check_me_request(vault, _answered_cue())
    assert request["constraints"]["learning_object_ids"] == ["lo_svd_definition"]
    assert request["constraints"]["exclude_item_ids"] == ["pi_svd_define_001"]
    assert request["constraints"]["kinds"] == "items" and request["constraints"]["rerank"] is False
    # Only the answered question exists on the LO: nothing fits, said plainly.
    assert check_me_proposal(vault, repository, "ext1", _answered_cue())["status"] == "none"
    add_followup_item(root)
    vault = load_vault(root)
    found = check_me_proposal(vault, repository, "ext1", _answered_cue())
    assert found["status"] == "found" and found["practice_item_id"] == "pi_svd_define_002"


def test_preferences_rpc_writes_vault_config_and_the_plan_follows(tmp_path):
    root, _vault, repository = _cue_vault(tmp_path, on_disk=True)
    prefs = _call(root, "reader.set_cue_preferences", {"extractionId": "ext1", "density": "fewer", "via": "fewer"})["result"]
    assert prefs["density"] == "fewer" and prefs["budgetPerSection"] == 1
    config = tomllib.loads((root / "learnloop.toml").read_text(encoding="utf-8"))
    assert config["cues"]["density"] == "fewer"
    assert all(mark["sectionRank"] == 0 for mark in _marks(root))
    off = _call(root, "reader.set_cue_preferences", {"extractionId": "ext1", "sourceId": "src1", "sourceOff": True, "via": "popover"})["result"]
    assert off["sourceOff"] is True
    plan = _call(root, "reader.guide_plan", {"extractionId": "ext1"})["result"]
    assert plan["cues"]["sourceOff"] is True and plan["cues"]["marks"] == []
    back = _call(root, "reader.set_cue_preferences", {"extractionId": "ext1", "sourceId": "src1", "sourceOff": False, "via": "undo"})["result"]
    assert back["sourceOff"] is False and _marks(root)
    events = [e["payload"] for e in _cue_events(repository)]
    assert [(e["event"], e.get("via")) for e in events] == [
        ("cue_density_changed", "fewer"), ("cue_source_off", "popover"), ("cue_source_on", "undo"),
    ]
    assert events[0]["from"] == "normal" and events[0]["to"] == "fewer"
    refused = _call(root, "reader.set_cue_preferences", {"density": "lots"})
    assert refused["error"]["data"]["code"] == "validation_error"


def test_the_cue_rpcs_answer_cues_disabled_when_switched_off(tmp_path):
    root, _vault, _repository = _cue_vault(tmp_path, on_disk=True, config="[cues]\nenabled = false\n")
    for method, params in (
        ("reader.cue_action", {"extractionId": "ext1", "cueId": "cue_x", "action": "opened"}),
        ("reader.set_cue_preferences", {"density": "fewer"}),
    ):
        assert _call(root, method, params)["error"]["data"]["code"] == "cues_disabled"
    prefs = _call(root, "reader.cue_preferences", {})["result"]
    assert prefs["enabled"] is False


def test_step_down_walks_more_normal_fewer_off():
    assert [RCU.step_down(d) for d in ("more", "normal", "fewer", "off")] == ["normal", "fewer", "off", "off"]


# -- one interaction model: a video transcript ---------------------------------------------------


def test_a_transcript_passage_carries_a_cue_like_any_source(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    repository = Repository(paths.sqlite_path)
    source = transcript_source(repository)
    vault = load_vault(root)
    vault.practice_items["pi_svd_define_001"].provenance.source_refs = [
        SourceRef(ref_type="canonical_source", ref_id=source["source_id"], locator=f"span:{source['extraction_id']}/{source['span_id']}",
                  source_id=source["source_id"], extraction_id=source["extraction_id"]),
    ]
    _active_error(repository)
    plan = build_guide_plan(vault, repository, extraction_id=source["extraction_id"])
    cues = RCU.guide_cues(vault, repository, extraction_id=source["extraction_id"], plan=plan)
    assert [mark["span_id"] for mark in cues["marks"]] == [source["span_id"]]


# -- the report: the cue funnel (spec §15) -------------------------------------------------------


def test_the_report_counts_marks_shown_taps_and_choices_against_marks_shown(tmp_path):
    from learnloop.reader.reader_report import build_reader_report

    _root, vault, repository = _cue_vault(tmp_path)
    _plan, cues = _plan_and_cues(vault, repository)
    RI.record_activity(repository, [
        {"kind": "reader_view_opened", "payload": {"visit_id": "v1", "extraction_id": "ext1"}},
        *[{"kind": "reader_action_invoked", "event": "cue_shown",
           "payload": {"visit_id": "v1", "extraction_id": "ext1", "cue_id": mark["cue_id"], "span_id": mark["span_id"],
                       "cue_kind": "revisit", "density": "normal", "element": "margin_mark"}}
          for mark in cues["marks"][:2]],
        {"kind": "reader_view_closed", "payload": {"visit_id": "v1", "active_seconds": 1800, "idle_seconds": 0}},
    ], clock=_CLOCK)
    RCU.record_cue_tap(repository, extraction_id="ext1", cue=cues["marks"][0], action="opened", clock=_CLOCK)
    RCU.record_cue_tap(repository, extraction_id="ext1", cue=cues["marks"][1], action="not_relevant", clock=_CLOCK)
    RCU.log_preference_events(repository, [{"event": "cue_density_changed", "from": "normal", "to": "fewer",
                                            "via": "fewer"}], extraction_id="ext1", clock=_CLOCK)
    report = build_reader_report(repository.sqlite_path)
    assert report["cues"]["shown"] == 2
    assert report["cues"]["opened"] == {"count": 1, "of": 2, "share": 0.5}
    assert report["cues"]["not_relevant"]["count"] == 1
    assert report["cues"]["per_reading_hour"] == 4.0
    assert report["cues"]["density_changes"] == {"normal->fewer": 1}
    assert report["proactive_load"]["by_element"]["margin_mark"] == 2
    assert "transpose" not in json.dumps(report)
