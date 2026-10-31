"""RW5a's kill switch restores the Reader of before RW5a byte for byte (spec §8.6, W3, U13).

With ``figures.enabled`` off, the Reader's prompt contract (its intent box's
palettes included) is exactly what the base tree (``e14b4e4ff``) produced:
no ``figures`` key and no "make this explorable". The golden file was
recorded on that tree, before any RW5a code existed (an export of it, with
``RW5A_WRITE_GOLDEN=1``); every figure RPC then refuses and no route is
called (tests/test_figures_rpc.py).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from tests.library_ask_fixtures import build_library_vault, call, context, set_config

GOLDEN = Path(__file__).parent / "fixtures" / "figures_switch_off.json"
WRITE = os.environ.get("RW5A_WRITE_GOLDEN") == "1"


def _record(tmp_path: Path, *, enabled: bool | None) -> dict:
    paths, _repository, _spans = build_library_vault(tmp_path / "vault")
    if enabled is not None:
        set_config(paths, "figures", enabled=enabled)
    ctx = context(paths.root)
    contract = call(ctx, "reader.prompt_contract", {})
    return {"contract": contract if WRITE else _without_later_stages(contract)}


#: What main gained after the golden's tree (e14b4e4ff), each stage behind its
#: own switch and pinned by its own tests (RW5a landing): RW4d's
#: ``compareKeep`` and RW7a's ``readingPaths`` with Orient's "what matters
#: here?" in the contract; RW4d's ``comparisons``, RW4e's ``roles`` and RW7a's
#: ``reading_paths`` in the report. These pins are about RW5a's switch, so
#: everything else stays byte for byte. Reader CA5a's ``correspondence``
#: (find this section in my other books) is pinned by
#: tests/test_reader_ca5a_find_section.py.
LATER_CONTRACT_KEYS = ("compareKeep", "readingPaths", "correspondence")
LATER_REPORT_KEYS = ("comparisons", "roles", "reading_paths")


def _without_later_stages(contract: dict) -> dict:
    for key in LATER_CONTRACT_KEYS:
        contract.pop(key)
    # Reader CA3 (on by default, pinned by tests/test_reader_ca3_compare_anywhere.py):
    # libraryAsk.compareScope and Transfer's "how do my other books treat this?".
    assert contract["libraryAsk"].pop("compareScope") is True
    for group in contract["intent"]["palette"]:
        group["actions"] = [action for action in group["actions"]
                            if action["effect"] != {"kind": "reading_path"} and action["effect"]["kind"] != "compare"]
    return contract


def test_figures_off_is_the_base_reader_contract_byte_for_byte(tmp_path):
    recorded = _record(tmp_path, enabled=None if WRITE else False)
    if WRITE:
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(recorded, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        pytest.skip("golden written")
    assert recorded == json.loads(GOLDEN.read_text(encoding="utf-8"))


def test_figures_on_adds_only_its_key_and_its_action(tmp_path):
    if WRITE:
        pytest.skip("the golden is written by the switch-off case")
    recorded = _record(tmp_path, enabled=True)["contract"]
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))["contract"]
    # RW5b adds offers (figures.offers_enabled, on by default); RW5d P1 show_me.
    assert recorded.pop("figures") == {"predictions": True, "region": True, "revisions": True, "offers": True,
                                       "showMe": True}
    added = []
    for group in recorded["intent"]["palette"]:
        kept = [action for action in group["actions"] if action["effect"] != {"kind": "figure"}]
        added += [action["id"] for action in group["actions"] if action["effect"] == {"kind": "figure"}]
        group["actions"] = kept
    assert added == ["make_explorable"]
    assert recorded == golden


# ---------------------------------------------------------------------------
# Fix round 3: the Reader report with figures off is the base report
# ---------------------------------------------------------------------------

REPORT_GOLDEN = Path(__file__).parent / "fixtures" / "figures_switch_off_report.json"


def _seed_figure_rows(repository) -> None:
    """One shown figure and one missed prediction with its explanation (the
    rows the figures block counts), written straight to migration 216's tables."""

    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO interactive_figures (id, extraction_id, origin, spec_json, spec_version, kind, verification, "
            "prompt_version, input_hash, created_at) VALUES ('fig_off', 'ext1', 'selection', '{}', 'ifs-v1', "
            "'illustrative', 'illustrative', 'figure_author.v1', 'hash_off', ?)", ("2026-01-01T00:10:00Z",))
        connection.execute(
            "INSERT INTO figure_predictions (id, figure_id, extraction_id, prediction_index, learner_answer, "
            "observed_json, matched, explanation_text, created_at) VALUES ('fpr_off', 'fig_off', 'ext1', 0, 'rises', "
            "'{}', 0, 'p sets it', ?)", ("2026-01-01T00:11:00Z",))
        connection.commit()


def _report(tmp_path: Path, *, figures: bool | None) -> dict:
    from datetime import timedelta

    from learnloop.reader.reader_report import build_reader_report
    from tests.helpers import NOW
    from tests.test_reader_report import _seed

    _vault, repo, _old = _seed(tmp_path)
    if figures is None:  # the base tree: no figure tables, no switch
        return build_reader_report(repo.sqlite_path, now=NOW + timedelta(minutes=60))
    _seed_figure_rows(repo)
    report = build_reader_report(repo.sqlite_path, now=NOW + timedelta(minutes=60), figures_enabled=figures)
    for key in LATER_REPORT_KEYS:  # main's later blocks (RW5a landing; see LATER_CONTRACT_KEYS)
        report.pop(key)
    return report


def test_figures_off_is_the_base_reader_report(tmp_path):
    """Recorded on an export of e14b4e4ff (RW5A_WRITE_GOLDEN=1, -o pythonpath=<export>/src); here the
    vault also has a figure and a prediction, which the switched-off report never reads."""

    recorded = _report(tmp_path, figures=None if WRITE else False)
    if WRITE:
        REPORT_GOLDEN.write_text(json.dumps(recorded, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                                 encoding="utf-8")
        pytest.skip("report golden written")
    assert json.loads(json.dumps(recorded)) == json.loads(REPORT_GOLDEN.read_text(encoding="utf-8"))


def test_figures_on_adds_only_the_figures_block_to_the_report(tmp_path):
    if WRITE:
        pytest.skip("the golden is written by the switch-off case")
    recorded = json.loads(json.dumps(_report(tmp_path, figures=True)))
    assert recorded.pop("figures") == {"built": {"illustrative": 1}, "unsupported_by_kind": {}, "revisions": 0,
                                       "regions": 0, "predictions": 1, "predictions_missed": 1, "what_changed": 1}
    assert recorded == json.loads(REPORT_GOLDEN.read_text(encoding="utf-8"))


def test_the_report_cli_follows_the_switch(tmp_path):
    from typer.testing import CliRunner

    from learnloop.cli import app
    from tests.test_reader_report import _seed

    if WRITE:
        pytest.skip("the golden is written by the switch-off case")
    vault, repo, _old = _seed(tmp_path)
    _seed_figure_rows(repo)
    set_config(_Paths(vault.root), "figures", enabled=False)
    seen = {}
    for enabled in (False, True):
        if enabled:
            _flip(vault.root)
        result = CliRunner().invoke(app, ["reader", "report", "--vault", str(vault.root), "--json"])
        assert result.exit_code == 0, result.output
        seen[enabled] = "figures" in json.loads(result.output)
    assert seen == {False: False, True: True}


class _Paths:
    def __init__(self, root: Path) -> None:
        self.root = root


def _flip(root: Path) -> None:
    config = root / "learnloop.toml"
    config.write_text(config.read_text(encoding="utf-8").replace("[figures]\nenabled = false",
                                                                 "[figures]\nenabled = true"), encoding="utf-8")


# ---------------------------------------------------------------------------
# Fix round 4: figure-derived learner text is switched off with figures
# ---------------------------------------------------------------------------

BACKLOG_GOLDEN = Path(__file__).parent / "fixtures" / "figures_switch_off_backlog.json"


def _switch(root: Path, section: str, enabled: bool) -> None:
    import re

    config = root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    value = "true" if enabled else "false"
    found = re.search(rf"(?ms)^\[{section}\]\n(.*?)(?=^\[|\Z)", text)
    if found is None:
        text = text.rstrip("\n") + f"\n\n[{section}]\nenabled = {value}\n"
    elif re.search(r"(?m)^enabled = ", found.group(1)):
        body = re.sub(r"(?m)^enabled = \w+", f"enabled = {value}", found.group(1), count=1)
        text = text[:found.start(1)] + body + text[found.end(1):]
    else:
        text = text[:found.start(1)] + f"enabled = {value}\n" + text[found.start(1):]
    config.write_text(text, encoding="utf-8")


def _backlog_dry_run(root: Path) -> dict:
    from typer.testing import CliRunner

    from learnloop.cli import app

    result = CliRunner().invoke(app, ["gaps", "run", "--vault", str(root), "--backlog", "--dry-run", "--json"])
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def test_figures_off_backlog_dry_run_is_the_base_output(tmp_path):
    """Recorded on an export of e14b4e4ff (RW5A_WRITE_GOLDEN=1, -o pythonpath=<export>/src). Here the vault
    also holds an unread missed prediction with its explanation (no job), which figures off never sees.
    Plan-first transport T1 re-recorded only the route names (codex_* tiers -> chatgpt_* tiers)."""

    from tests.test_reader_report import _seed

    vault, repo, _old = _seed(tmp_path)
    if WRITE:
        BACKLOG_GOLDEN.write_text(json.dumps(_backlog_dry_run(vault.root), indent=1, sort_keys=True) + "\n",
                                  encoding="utf-8")
        pytest.skip("backlog golden written")
    _seed_figure_rows(repo)
    _switch(vault.root, "figures", False)
    assert _backlog_dry_run(vault.root) == json.loads(BACKLOG_GOLDEN.read_text(encoding="utf-8"))
    # On, the same vault owes the prediction: the golden is not trivially equal.
    _switch(vault.root, "figures", True)
    assert _backlog_dry_run(vault.root)["would_queue"]["reader_formative"] == 1


def test_figures_off_queues_and_reads_no_figure_text(tmp_path):
    from learnloop.diagnosis.text_gaps import jobs as gap_jobs
    from learnloop.vault.loader import load_vault
    from tests.test_figures_codex_review import _clients, _missed_prediction

    if WRITE:
        pytest.skip("the golden is written by the switch-off case")
    paths, repository, _ctx, found = _missed_prediction(tmp_path)  # figures on: its job is queued
    prediction_id = found["predictionId"]
    _switch(paths.root, "figures", False)
    vault = load_vault(paths.root)
    assert gap_jobs.enqueue_figure_prediction(vault, repository, prediction_id="fpr_other") is None
    assert gap_jobs.enqueue_figure_explanation(vault, repository, prediction_id=prediction_id) is None
    assert gap_jobs.sweep_backlog(vault, repository)["reader_formative"] == 0
    llm, clients = _clients()
    outcome = gap_jobs.process_next_gap_job(paths.root, repository, owner="t", clients=clients)
    # Main's path for a source with nothing to read (owner decision
    # 2026-10-21: a figure text queued while figures are off is dropped).
    assert (outcome.state, outcome.error) == ("skipped", None)
    assert llm.calls == []  # no model call
    with repository.connection() as connection:
        state, error = connection.execute(
            "SELECT state, last_error FROM learner_text_gap_jobs WHERE source_id = ?", (prediction_id,)).fetchone()
    assert (state, error) == ("skipped", "nothing to read")
    assert gap_jobs.run_pending(paths.root, repository, owner="t", clients=clients) == []
    assert llm.calls == []
    assert gap_sources_text(vault, repository, prediction_id) is None


def gap_sources_text(vault, repository, source_id):
    from learnloop.diagnosis.text_gaps.sources import learner_text

    return learner_text(vault, repository, "reader_formative", source_id)


# ---------------------------------------------------------------------------
# The owner's scope decision (2026-10-21): an already-queued figure job with
# figures off takes main's path, so the output is main's by construction
# ---------------------------------------------------------------------------

QUEUED_GOLDEN = Path(__file__).parent / "fixtures" / "figures_switch_off_queued_job.json"


def _normalized(payload: dict) -> dict:
    import re

    text = json.dumps(payload, sort_keys=True)
    return json.loads(re.sub(r'"job_id": "[^"]+"', '"job_id": "<job>"', text))


def _queued_job_runs(root: Path) -> dict:
    from typer.testing import CliRunner

    from learnloop.cli import app

    out = {}
    for name, args in (("dry_run", ["--backlog", "--dry-run"]), ("run", [])):
        result = CliRunner().invoke(app, ["gaps", "run", "--vault", str(root), *args, "--json"])
        assert result.exit_code == 0, result.output
        out[name] = _normalized(json.loads(result.output))
    return out


def test_an_already_queued_figure_job_with_figures_off_is_the_base_output(tmp_path):
    """Recorded on an export of e14b4e4ff (RW5A_WRITE_GOLDEN=1, -o pythonpath=<export>/src): a vault
    with a queued reader_formative/fpr_ job. Here the vault also holds that prediction's rows and
    figures are off: `learnloop gaps run --backlog --dry-run --json` and the processing run
    (`learnloop gaps run --json`) both equal main's. Plan-first transport T1 re-recorded only the
    route names (codex_* tiers -> chatgpt_* tiers)."""

    from learnloop.diagnosis.text_gaps.jobs import enqueue
    from tests.test_reader_report import _seed

    vault, repo, _old = _seed(tmp_path)
    enqueue(repo, source_kind="reader_formative", source_id="fpr_off")
    if WRITE:
        QUEUED_GOLDEN.write_text(json.dumps(_queued_job_runs(vault.root), indent=1, sort_keys=True) + "\n",
                                 encoding="utf-8")
        pytest.skip("queued-job golden written")
    _seed_figure_rows(repo)
    _switch(vault.root, "figures", False)
    assert _queued_job_runs(vault.root) == json.loads(QUEUED_GOLDEN.read_text(encoding="utf-8"))
