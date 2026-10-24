"""Adaptive difficulty AD3: monitoring, never gating (spec §10.4, D3; G-AD3-3, the integration side of G-AD3-9).

The report computes field §7.4's rule as a monitor, the confidence sequences, the
honest lines and the auto-flags; nothing it computes changes a switch, the vault
config or anything served. Fails before AD3: no report existed. Fakes only.
"""

from __future__ import annotations

import hashlib
import json
from contextlib import closing
from typing import Any

import numpy as np
import pytest
from typer.testing import CliRunner

from learnloop.adaptive_difficulty import arms as A
from learnloop.adaptive_difficulty import monitoring as MON
from learnloop.adaptive_difficulty import report as REP
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import ad23_vault, answer, env_for, set_item

ITEMS = ("pi_q1", "pi_q2", "pi_q3", "pi_q4")
OTHER = ("pi_x1", "pi_x2")


def _vault_with_answers(tmp_path):
    paths = ad23_vault(tmp_path, items=ITEMS, learning_objects={"lo_x": OTHER}, config="[router]\nenabled = false\n")
    for item in OTHER:
        set_item(paths, item, evidence_facets=["f_x"], evidence_weights={"f_x": 1.0})
    env, clock = env_for(paths, items=ITEMS + OTHER)
    build_plan(env, kind="normal", budget=20.0, remembered=20, minutes_source="chip")
    for k in range(6):
        _record, step = advance(env, serve=True)
        if step["kind"] != "item":
            break
        clock.advance(2)
        answer(paths, step["practice_item_id"], correct=k % 3 != 1, presentation_id=step["presentation_id"],
               clock=clock)
        clock.advance(1)
    return paths


def _fingerprint(paths) -> str:
    digest = hashlib.sha256((paths.root / "learnloop.toml").read_bytes())
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        for (table,) in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"):
            count = connection.execute(f"SELECT COUNT(*) FROM \"{table}\"").fetchone()[0]
            digest.update(f"{table}:{count}".encode())
    return digest.hexdigest()


def test_monitoring_applies_field_rule_as_monitor_never_gate(tmp_path):
    """G-AD3-3: the report computes field §7.4's rule for ``@subject`` against ``mastery_ekf``,
    ``@lo`` and ``@subject_uniform`` (log loss overall and on the first-attempt split, the bootstrap
    interval at margin 0, the fast-track miss rate), the never-seen-cell split, band-region
    reliability and the confidence sequences, and states "helping", "hurting" or "can't tell yet"
    for sharing, coupling, reading and verdicts. No outcome changes any switch, config or served
    item."""

    paths = _vault_with_answers(tmp_path)
    before = _fingerprint(paths)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        report = REP.build(vault, repository, connection, sensitivity=True)
    assert _fingerprint(paths) == before
    assert report["records"] > 0
    for comparator in (A.LO, A.UNIFORM):
        rule = report["field_rule_monitor"][comparator]
        for split in ("all", "first_attempt_lo"):
            assert {"improvement", "beats", "sequence"} <= set(rule[split])
            assert rule[split]["improvement"]["n"] == rule[split]["sequence"]["n"]
        assert {"predicted", "missed", "miss_rate", "wilson"} == set(rule["fast_track"])
    for arm in (A.SUBJECT, A.LO, A.UNIFORM):
        assert {"first_attempt_lo", "first_surface_cell", "all"} == set(report["scores"][arm])
        assert "band_region_error" in report["scores"][arm]["all"]
    lines = report["honest_lines"]
    assert len(lines) == 4 and all(any(v in line for v in (MON.HELPING, MON.HURTING, MON.CANT_TELL)) for line in lines)
    assert all("first attempts)" in line for line in lines)
    assert {flag["flag"] for flag in report["auto_flags"]} == set(MON.FLAG_SWITCHES)
    assert all(flag["recommends"] == MON.FLAG_SWITCHES[flag["flag"]] for flag in report["auto_flags"])
    assert report["identifiability"]["statement"] == REP.HONEST_STATEMENT
    assert "hyperparameter_margins" in report["identifiability"]
    assert report["prior_sensitivity"] is not None
    assert "dose_and_burden" in report and "self_check_calibration" in report
    assert "time_to_usable_by_subject" in report["selection"]


def test_report_cli_is_read_only_dry_run_first(tmp_path):
    from learnloop.cli import app

    paths = _vault_with_answers(tmp_path)
    before = _fingerprint(paths)
    dry = CliRunner().invoke(app, ["ad", "report", "--vault", str(paths.root), "--dry-run", "--json"])
    assert dry.exit_code == 0, dry.output
    plan = json.loads(dry.output)
    assert plan["status"] == "dry_run" and plan["model_calls"] == 0 and plan["writes"] == 0
    result = CliRunner().invoke(app, ["ad", "report", "--vault", str(paths.root), "--json", "--no-sensitivity"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["version"] == REP.REPORT_VERSION and report["auto_flags"]
    markdown = CliRunner().invoke(app, ["ad", "report", "--vault", str(paths.root), "--no-sensitivity"])
    assert "## Auto-flags" in markdown.output and "## Is it helping?" in markdown.output
    assert _fingerprint(paths) == before


def test_honest_verdicts_follow_the_sequence():
    assert MON.verdict({"n": 0}) == MON.CANT_TELL
    assert MON.verdict({"n": 50, "lower": -0.3, "upper": -0.01}) == MON.HELPING
    assert MON.verdict({"n": 50, "lower": 0.01, "upper": 0.3}) == MON.HURTING
    assert MON.verdict({"n": 50, "lower": -0.1, "upper": 0.1}) == MON.CANT_TELL


def test_confidence_sequence_is_anytime_valid_under_the_null():
    """The predictable-range normal-mixture sequence (amendment A7) covers a zero mean at every
    time at once in >= 95% of 400 null runs, and its width shrinks as data arrive."""

    rng = np.random.default_rng(9)
    misses = 0
    for _ in range(400):
        values, ranges = [], []
        crossed = False
        for t in range(300):
            p = rng.uniform(0.2, 0.9)
            a, b = np.log(rng.uniform(0.5, 1.5)), np.log(rng.uniform(0.5, 1.5))
            low, high = sorted((a, b))
            y = rng.random() < p
            centred = (high if y else low) - (p * high + (1 - p) * low)
            values.append(centred)
            ranges.append((low - (p * high + (1 - p) * low), high - (p * high + (1 - p) * low)))
            if t % 25 == 24:
                sequence = MON.confidence_sequence(values, ranges=ranges)
                crossed |= not (sequence["lower"] <= 0.0 <= sequence["upper"])
        misses += crossed
    assert misses / 400 <= 0.05
    wide = MON.confidence_sequence([0.1] * 20, ranges=[(-1, 1)] * 20)
    narrow = MON.confidence_sequence([0.1] * 2000, ranges=[(-1, 1)] * 2000)
    assert narrow["half_width"] < wide["half_width"]


def test_no_flag_edits_the_vault_config(tmp_path):
    """Flags recommend; the owner flips a switch; code never edits the vault config."""

    paths = _vault_with_answers(tmp_path)
    toml = (paths.root / "learnloop.toml").read_text(encoding="utf-8")
    vault = load_vault(paths.root)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        REP.build(vault, Repository(paths.sqlite_path), connection, previous_errors=(0.2, 0.2), sensitivity=False)
    assert (paths.root / "learnloop.toml").read_text(encoding="utf-8") == toml
    assert load_vault(paths.root).config.adaptive_difficulty.model_dump() == vault.config.adaptive_difficulty.model_dump()
