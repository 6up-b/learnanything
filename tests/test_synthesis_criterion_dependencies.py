"""Synthesis keeps a criterion's ``depends_on`` to sibling criteria (doctor investigation 2026-10-12).

The study-map normalizer copied each criterion's ``depends_on`` exactly as the
model wrote it, and the model often wrote facet or blueprint ids there (the
dependency-closure rule invited it). Those entries name no criterion: at
grading a missing dependency counts as passed, so the gating was silently
lost, and doctor reports ``criterion:unknown_dependency`` for each one. Now
``_normalize`` keeps only sibling criterion ids and drops the rest with a
review diagnostic; ``learnloop doctor --fix-content`` repairs vaults written
before the fix.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.content.synthesis.ai_contracts import (
    APPEND_RECONCILIATION_PROMPT,
    SOURCE_SET_SYNTHESIS_PROMPT,
    SourceSetSynthesisContext,
    SynthCriterion,
    SynthCriterionTarget,
    source_set_synthesis_prompt,
)
from learnloop.content.synthesis.source_set_synthesis import create_study_map
from learnloop.ops.doctor import run_doctor
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.test_source_set_synthesis import FakeSynthesisClient, _default_payload, _setup

_CLOCK = FrozenClock(datetime(2026, 10, 13, 12, 0, 0, tzinfo=UTC))


def _with_mixed_dependencies(context, _call):
    """pi_select_spectral gets two criteria: one sibling dependency, plus the
    facet, blueprint, cross-item and self ids models write in practice."""

    payload = _default_payload(context)
    item = payload.practice_items[1]
    item.criteria = [
        SynthCriterion(
            id="names_condition",
            points=1.0,
            description="Names the symmetry condition the theorem needs.",
            targets=[SynthCriterionTarget(facet_client_id="f_def", capability="schema_interpretation")],
        ),
        SynthCriterion(
            id="selects_spectral",
            points=1.0,
            description="Selects the spectral theorem for a symmetric matrix.",
            depends_on=[
                "names_condition",                 # a sibling: kept
                "f_spectral",                      # a facet client id
                "facet_spectral_applicability",    # a facet id
                "bp_select_and_apply_spectral",    # a blueprint id
                "identifies_symmetry",             # a criterion of another item
                "selects_spectral",                # itself
                "names_condition",                 # a repeat
            ],
            targets=[SynthCriterionTarget(facet_client_id="f_spectral", capability="method_selection")],
        ),
    ]
    payload.practice_items[0].criteria[0].depends_on = []
    return payload


def _criteria(root: Path, item_id: str) -> dict[str, list[str]]:
    item = load_vault(root).practice_items[item_id]
    return {criterion.id: list(criterion.depends_on) for criterion in item.grading_rubric.criteria}


def test_normalize_keeps_only_sibling_criterion_dependencies(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    result = create_study_map(root, "set_la", client=FakeSynthesisClient(builder=_with_mixed_dependencies),
                              repository=repo, clock=_CLOCK, apply=True)

    assert _criteria(root, "pi_select_spectral") == {
        "names_condition": [],
        "selects_spectral": ["names_condition"],
    }
    run = repo.synthesis_run(result.synthesis_run_id)
    dropped = [
        diag for diag in run["coverage_decisions"]["gate_diagnostics"]
        if diag.get("gate") == "criterion_dependency"
    ]
    assert len(dropped) == 1, dropped
    (diag,) = dropped
    assert diag["severity"] == "review"
    assert diag["entity_refs"][0] == "pi_select_spectral"
    for wrong in ("f_spectral", "facet_spectral_applicability", "bp_select_and_apply_spectral",
                  "identifies_symmetry", "selects_spectral"):
        assert wrong in diag["message"]
    # The repaired map is doctor-clean for criterion dependencies.
    codes = {issue.code for issue in run_doctor(root).issues}
    assert "criterion:unknown_dependency" not in codes


def test_the_prompts_say_criterion_depends_on_names_sibling_criteria_only():
    assert "only\nthe `id`s of SIBLING criteria in the same practice item" in SOURCE_SET_SYNTHESIS_PROMPT
    assert "Never put a facet, blueprint, learning\nobject, recipe or client item id there" in SOURCE_SET_SYNTHESIS_PROMPT
    # The rule changed the request, so its version moved (no stale cache reuse).
    context = SourceSetSynthesisContext(source_set_id="set", subject_id="subject", mode="bootstrap")
    assert "prompt_version: mvp-1.3-sibling-criterion-dependencies" in source_set_synthesis_prompt(context)
    assert "names only the `id`s of sibling\ncriteria in the same practice item" in APPEND_RECONCILIATION_PROMPT
    assert "lock_reasons" not in APPEND_RECONCILIATION_PROMPT


def _break_dependencies(root: Path) -> Path:
    """Write the July shape into an item's YAML: facet/blueprint ids in depends_on."""

    vault = load_vault(root)
    item = vault.practice_items["pi_select_spectral"]
    path = next((root / "subjects").rglob(f"{item.id}.yaml"))
    data = read_yaml(path)
    criteria = data["grading_rubric"]["criteria"]
    criteria[0]["depends_on"] = ["facet_spectral_applicability", "bp_select_and_apply_spectral"]
    write_yaml(path, data)
    return path


def _applied(tmp_path: Path) -> Path:
    root, repo = _setup(tmp_path, with_exam=False)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo, clock=_CLOCK, apply=True)
    return root


def test_fix_content_dry_run_lists_the_edits_and_writes_nothing(tmp_path):
    root = _applied(tmp_path)
    path = _break_dependencies(root)
    before = path.read_bytes()
    assert "criterion:unknown_dependency" in {issue.code for issue in run_doctor(root).issues}

    from learnloop.ops.content_fixes import fix_criterion_dependencies

    report = fix_criterion_dependencies(root, dry_run=True)

    assert report["dry_run"] is True
    assert report["items_changed"] == 1 and report["entries_removed"] == 2
    (change,) = report["changes"]
    assert change["practice_item_id"] == "pi_select_spectral"
    assert change["criteria"] == [{
        "criterion_id": "selects_spectral",
        "removed": ["facet_spectral_applicability", "bp_select_and_apply_spectral"],
        "kept": [],
    }]
    assert change["path"].endswith("pi_select_spectral.yaml")
    assert path.read_bytes() == before


def test_fix_content_removes_invalid_entries_and_keeps_the_rest_of_the_file(tmp_path):
    root = _applied(tmp_path)
    path = _break_dependencies(root)
    data = read_yaml(path)
    data["grading_rubric"]["criteria"][0]["depends_on"].insert(0, "selects_spectral_prereq")
    # A real sibling stays: add one and point at it.
    data["grading_rubric"]["criteria"].append({
        "id": "selects_spectral_prereq", "points": 1.0, "description": "Checks symmetry first.",
        "targets": [], "depends_on": [],
    })
    write_yaml(path, data)
    from learnloop.ops.content_fixes import fix_criterion_dependencies

    report = fix_criterion_dependencies(root, dry_run=False)

    assert report["items_changed"] == 1 and report["entries_removed"] == 2
    after = read_yaml(path)
    assert after["grading_rubric"]["criteria"][0]["depends_on"] == ["selects_spectral_prereq"]
    assert after["prompt"] == data["prompt"]
    assert "criterion:unknown_dependency" not in {issue.code for issue in run_doctor(root).issues}
    # Idempotent: a second run finds nothing.
    assert fix_criterion_dependencies(root, dry_run=False)["items_changed"] == 0


def test_doctor_fix_content_cli_dry_run_then_apply(tmp_path):
    root = _applied(tmp_path)
    _break_dependencies(root)
    runner = CliRunner()

    dry = runner.invoke(app, ["doctor", "--vault", str(root), "--fix-content", "--dry-run", "--json"])
    payload = json.loads(dry.stdout)
    assert payload["fix_content"]["dry_run"] is True
    assert payload["fix_content"]["entries_removed"] == 2
    assert "criterion:unknown_dependency" in {issue["code"] for issue in payload["issues"]}

    applied = runner.invoke(app, ["doctor", "--vault", str(root), "--fix-content", "--json"])
    payload = json.loads(applied.stdout)
    assert payload["fix_content"]["dry_run"] is False
    assert payload["fix_content"]["items_changed"] == 1
    assert "criterion:unknown_dependency" not in {issue["code"] for issue in payload["issues"]}


def test_fix_content_skips_unparseable_items_and_reports_them(tmp_path):
    root = _applied(tmp_path)
    paths = VaultPaths(root, load_vault(root).config)
    broken = next((root / "subjects").rglob("pi_identify_symmetry.yaml"))
    broken.write_text(broken.read_text(encoding="utf-8") + "dependencies:\n  A long key\n    wrapped.: []\n",
                      encoding="utf-8")
    _break_dependencies(root)
    from learnloop.ops.content_fixes import fix_criterion_dependencies

    report = fix_criterion_dependencies(root, dry_run=False)

    assert report["items_changed"] == 1
    assert [entry["path"] for entry in report["unreadable"]] == [str(broken)]
    assert paths.root == root
