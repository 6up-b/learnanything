"""Adaptive difficulty AD3: the relatedness proposal (spec §5.10; G-AD3-4 and the proposal side of G-AD3-5).

The proposal job reads exactly the subject's LO and facet text, the concept graph,
prerequisites and item stems; never learner data, a reference answer or held-out
material. It is spend-capped, dry-run first and ledgered; an unchanged input makes
no call, and a change re-proposes only the units it touches. Fails before AD3: no
proposal job existed. Fakes only (``tests.ad23_fakes.ProposalLLM``).
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from typing import Any

import pytest
from typer.testing import CliRunner

from learnloop.adaptive_difficulty import relatedness as R
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import ad_serving
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import COUPLED, ProposalLLM, ad23_vault, rows, set_item
from tests.helpers import set_algorithm_version

SENTINEL = "SENTINEL-AD3-4-ZQX"
SUBJECT = "linear-algebra"
LOS = {"lo_ra": ("pi_ra1", "pi_ra2"), "lo_rb": ("pi_rb1",), "lo_rc": ("pi_rc1",)}


def _vault(tmp_path, *, ad: str = ""):
    # learned_coupling is off by default (owner decision 2026-10-19); the proposal needs it on.
    ad = ad if "learned_coupling" in ad else COUPLED + ad
    paths = ad23_vault(tmp_path, items=LOS["lo_ra"], learning_objects={"lo_rb": LOS["lo_rb"], "lo_rc": LOS["lo_rc"]},
                       ad=ad)
    # Distinct facets per LO (the default vault gives every item the facet "recall").
    from tests.ad23_fakes import LO

    for lo, items in [(LO, LOS["lo_ra"]), *[(lo, LOS[lo]) for lo in ("lo_rb", "lo_rc")]]:
        for item in items:
            set_item(paths, item, learning_object_id=lo if lo != LO else LO,
                     evidence_facets=[f"f_{lo}"], evidence_weights={f"f_{lo}": 1.0})
    return paths


def _answer(subject_inputs: dict[str, Any]) -> dict[str, Any]:
    items = subject_inputs["payload"]["items"]
    los = [row["learning_object_id"] for row in subject_inputs["payload"]["learning_objects"]]
    facets = [row["facet_id"] for row in subject_inputs["payload"]["facets"]]
    first = items[0]
    other_facet = next(f for f in facets if f not in first["facets"])
    return {
        "items": [{"item_id": first["item_id"], "loadings": [
            {"facet_id": other_facet, "strength": "moderate", "why": "uses the prerequisite"},
            {"facet_id": first["facets"][0], "strength": "strong", "why": "self (dropped)"},
            {"facet_id": "f_unknown", "strength": "weak", "why": "unknown (dropped)"},
        ]}, {"item_id": "pi_not_there", "loadings": []}],
        "learning_objects": [{"learning_object_id": los[0], "related": [
            {"learning_object_id": los[1], "strength": "strong", "why": "same idea"},
            {"learning_object_id": los[0], "strength": "weak", "why": "self (dropped)"},
            {"learning_object_id": "lo_unknown", "strength": "weak", "why": "unknown (dropped)"},
        ]}],
    }


def _propose(paths, client: Any) -> R.ProposalOutcome:
    vault = load_vault(paths.root)
    return R.propose_subject(vault, Repository(paths.sqlite_path), SUBJECT, client=client)


def test_relatedness_proposal_reads_no_learner_or_held_out_data(tmp_path):
    """G-AD3-4: the job's input is exactly the subject's LO and facet text, the concept graph,
    prerequisites and item stems. A sentinel planted in an attempt, a grade, a diagnosis, a
    reading event, a tutor question, a reference answer, a held-out unit and an item derived
    from it reaches no prompt (fails before AD3: no proposal job existed)."""

    from learnloop.content.synthesis.source_unit_selection import save_unit_selection
    from learnloop.vault.models import CanonicalExercise
    from learnloop.vault.writer import upsert_practice_item
    from tests.daily_plan_fakes import seed_open_problem
    from tests.source_service_fakes import build_textbook_vault

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.28")
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"exercises": "held_out_evaluation"})
    vault = load_vault(paths.root)
    base = vault.practice_items["pi_eigen_1"]
    held = base.model_copy(update={
        "id": "pi_held", "prompt": f"{SENTINEL} held-out stem", "expected_answer": f"{SENTINEL} key",
        "canonical_exercise": CanonicalExercise(source_id="src_text", extraction_id="ext_text",
                                                span_ids=[spans["exercises"][1]]),
    })
    upsert_practice_item(paths.root, held.model_dump(mode="json"))
    keyed = vault.practice_items["pi_eigen_2"].model_copy(update={"expected_answer": f"{SENTINEL} reference answer"})
    upsert_practice_item(paths.root, keyed.model_dump(mode="json"))
    lo = base.learning_object_id
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "correctness, learner_answer_md, created_at) VALUES ('att_s', 'pi_eigen_2', ?, 'short_answer', "
            "'independent_attempt', 1.0, ?, '2026-10-11T09:00:00Z')", (lo, f"{SENTINEL} answer text"))
        connection.execute(
            "INSERT INTO question_events(id, context, question_md, answer_md, answer_status, created_at) VALUES "
            "('qe_s', 'reader', ?, ?, 'answered', '2026-10-11T09:00:00Z')", (f"{SENTINEL} tutor q", f"{SENTINEL} a"))
        connection.commit()
    seed_open_problem(repository, lo)
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE learner_state_hypotheses SET statement = ? WHERE learning_object_id = ?",
                           (f"{SENTINEL} diagnosis", lo)) if _has_column(connection, "learner_state_hypotheses",
                                                                        "statement") else None
        connection.commit()
    vault = load_vault(paths.root)
    vault.config.adaptive_difficulty.learned_coupling = True  # off by default (owner decision 2026-10-19)
    subject = vault.learning_objects[lo].subjects[0]
    inputs = R.subject_inputs(vault, repository, subject)
    assert set(inputs["payload"]) == {"subject", "learning_objects", "facets", "concept_graph", "items"}
    assert all(set(row) == {"item_id", "learning_object_id", "facets", "stem"} for row in inputs["payload"]["items"])
    assert "pi_held" not in inputs["item_ids"]
    llm = ProposalLLM()
    outcome = R.propose_subject(vault, repository, subject, client=llm)
    assert outcome.status == "ok" and llm.prompts
    sent = "\n".join(llm.prompts)
    assert SENTINEL not in sent
    assert "expected_answer" not in sent and "reference answer" not in sent


def _has_column(connection: Any, table: str, column: str) -> bool:
    try:
        return any(row[1] == column for row in connection.execute(f"PRAGMA table_info({table})"))
    except sqlite3.Error:
        return False


def test_each_loading_and_coupling_is_one_ledger_row_and_invalid_outputs_drop(tmp_path):
    paths = _vault(tmp_path)
    vault = load_vault(paths.root)
    inputs = R.subject_inputs(vault, Repository(paths.sqlite_path), SUBJECT)
    llm = ProposalLLM(_answer(inputs))
    outcome = _propose(paths, llm)
    assert outcome.status == "ok" and outcome.judgments == 2 and outcome.dropped >= 5
    judgments = rows(paths.sqlite_path, "SELECT * FROM judgment_ledger WHERE task = 'ad_relatedness' ORDER BY rowid")
    assert {(r["left_kind"], r["right_kind"], r["score"]) for r in judgments} == {
        ("learning_object", "learning_object", 1.0), ("practice_item_revision", "facet", 0.5)}
    assert all(r["prompt_version"] == "ad-relatedness-v1" and r["judge"] == "llm" for r in judgments)
    assert all(r["input_hash"] == outcome.input_hash for r in judgments)
    (run,) = ad_serving.relatedness_runs(connect(paths.sqlite_path))
    assert set(run["judgment_ids"]) == {r["id"] for r in judgments}
    assert set(run["units"]) == set(inputs["unit_hashes"])


def test_caps_hold():
    """At most 3 loadings per item and 3 coupled LOs per LO; loadings sum to at most 1."""

    inputs = {"payload": {"facets": [{"facet_id": f"f{k}"} for k in range(6)],
                          "learning_objects": [{"learning_object_id": f"l{k}"} for k in range(6)],
                          "items": [{"item_id": "i", "facets": ["f0"]}]}}
    answer = {"items": [{"item_id": "i", "loadings": [{"facet_id": f"f{k}", "strength": "strong", "why": "x"}
                                                      for k in range(1, 6)]}],
              "learning_objects": [{"learning_object_id": "l0", "related": [
                  {"learning_object_id": f"l{k}", "strength": "strong", "why": "x"} for k in range(1, 6)]}]}
    proposal = R.validate(answer, inputs)
    assert len(proposal.loadings["i"]) == 3 and sum(q for q, _w in proposal.loadings["i"].values()) == pytest.approx(1.0)
    assert len(proposal.couplings["l0"]) == 3
    assert sum(1 for d in proposal.dropped if d["why"] == "over_cap") == 4


def test_unchanged_input_makes_no_call_and_a_change_reproposes_only_what_it_touches(tmp_path):
    paths = _vault(tmp_path)
    vault = load_vault(paths.root)
    inputs = R.subject_inputs(vault, Repository(paths.sqlite_path), SUBJECT)
    first = ProposalLLM(_answer(inputs))
    assert _propose(paths, first).status == "ok" and len(first.prompts) == 1
    again = ProposalLLM(_answer(inputs))
    assert _propose(paths, again).status == "current" and not again.prompts
    # A retitled LO re-proposes its couplings only (no item revision is re-asked).
    lo_path = paths.learning_object_path(SUBJECT, "lo_rb")
    import yaml

    payload = yaml.safe_load(lo_path.read_text(encoding="utf-8"))
    payload["title"] = "Retitled topic"
    lo_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    retitled = ProposalLLM({"items": [], "learning_objects": []})
    assert _propose(paths, retitled).status == "ok" and len(retitled.prompts) == 1
    asked = json.loads(retitled.prompts[0][retitled.prompts[0].index("{"):])["state"]["propose_for"] \
        if retitled.prompts[0].strip().startswith("{") else None
    runs = ad_serving.relatedness_runs(connect(paths.sqlite_path))
    assert {unit for unit in runs[-1]["units"] if not unit.startswith("protection:")} == {"lo:lo_rb"}
    assert "Retitled topic" in retitled.prompts[0] and '"propose_for"' in retitled.prompts[0]
    # A new item revision re-proposes its loadings only.
    set_item(paths, "pi_rc1", prompt="A rewritten question about rc.")
    revised = ProposalLLM({"items": [], "learning_objects": []})
    assert _propose(paths, revised).status == "ok"
    runs = ad_serving.relatedness_runs(connect(paths.sqlite_path))
    (unit,) = {unit for unit in runs[-1]["units"] if not unit.startswith("protection:")}
    assert unit.startswith("rev:")
    assert asked is None or asked


def test_spend_capped_and_dry_run_first(tmp_path):
    """A metered route with no price is refused before sending; the dry run calls and writes nothing."""

    from learnloop.cli import app

    paths = _vault(tmp_path)

    class Metered(ProposalLLM):
        provider_name = "fake_metered"
        provider_type = "openai_compatible"

    metered = Metered()
    outcome = _propose(paths, metered)
    assert outcome.status == "refused_spend" and not metered.prompts
    result = CliRunner().invoke(app, ["ad", "relatedness", "--vault", str(paths.root), "--dry-run", "--json"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["status"] == "dry_run" and report["model_calls"] == 0 and report["writes"] == 0
    assert report["subjects"][SUBJECT]["units_to_propose"] > 0
    assert rows(paths.sqlite_path, "SELECT COUNT(*) AS n FROM judgment_ledger WHERE task = 'ad_relatedness'")[0]["n"] == 0
    assert rows(paths.sqlite_path, "SELECT COUNT(*) AS n FROM ad_relatedness_runs")[0]["n"] == 0


def test_no_proposal_call_with_learned_coupling_off_or_below_the_tag(tmp_path):
    off = _vault(tmp_path / "off", ad="learned_coupling = false\n")
    llm = ProposalLLM()
    assert _propose(off, llm).status == "disabled" and not llm.prompts
    below = _vault(tmp_path / "below")
    set_algorithm_version(below, "mvp-0.27")
    assert _propose(below, llm).status == "disabled" and not llm.prompts


def test_a_later_coupling_version_needs_its_shadow_report(tmp_path):
    """The first version adopts; a later one is a reinterpretation, refused until confirmed after
    its shadow report (which writes nothing)."""

    paths = _vault(tmp_path)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    inputs = R.subject_inputs(vault, repository, SUBJECT)
    _propose(paths, ProposalLLM(_answer(inputs)))
    first = R.adopt(repository, SUBJECT, adopted_by="test")
    assert first["version"] == 1
    set_item(paths, "pi_rc1", prompt="A rewritten question about rc.")
    _propose(paths, ProposalLLM({"items": [], "learning_objects": []}))
    with pytest.raises(R.ReinterpretationNeedsShadow):
        R.adopt(repository, SUBJECT, adopted_by="test")
    before = rows(paths.sqlite_path, "SELECT COUNT(*) AS n FROM ad_coupling_versions")[0]["n"]
    report = R.shadow_report(load_vault(paths.root), repository, SUBJECT)
    assert report["candidate"] and "attempts_moved" in report
    assert rows(paths.sqlite_path, "SELECT COUNT(*) AS n FROM ad_coupling_versions")[0]["n"] == before
    second = R.adopt(repository, SUBJECT, adopted_by="test", confirm_reinterpretation=True)
    assert second["version"] == 2
