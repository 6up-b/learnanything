"""Reader workbench RW3b: with every RW3b switch off, RW3a's cues are byte-identical (stage pin).

The fixture ``tests/fixtures/reader_rw3a_cues_c9ad9cce1.json`` was written by
this test on the unchanged base ``c9ad9cce1`` (RW1c's landing tip, before any
RW3b code), with ``LEARNLOOP_WRITE_RW3B_PIN=1``: the guide plan's ``cues``
through the real sidecar for the RW3a fixture vault at every density, and the
cue actions' answers. With ``cues.discovery_enabled``, ``try_first_enabled``,
``value_order_enabled`` off and ``holdout_rate = 0`` (RW3b's switches), the
same requests must answer the same bytes. Fakes only; no model is called.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from tests.helpers import append_config_toml
from tests.test_reader_cues import _cue_vault
from tests.test_sidecar_reader import _init, _rpc

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "reader_rw3a_cues_c9ad9cce1.json"
#: RW3b's own switches, all off. The base ignores none of them: on the base
#: run they are not written (its CuesConfig predates them).
RW3B_OFF = "discovery_enabled = false\ntry_first_enabled = false\nvalue_order_enabled = false\nholdout_rate = 0.0\n"
DENSITIES = ("off", "fewer", "normal", "more")


def _writing() -> bool:
    return os.environ.get("LEARNLOOP_WRITE_RW3B_PIN") == "1"


def _call(root, method: str, params: dict) -> dict:
    return _rpc([_init(root), {"jsonrpc": "2.0", "id": 2, "method": method, "params": params}])[1]


def _observed(tmp_path, density: str) -> dict:
    extra = "" if _writing() else RW3B_OFF
    root, _vault, _repository = _cue_vault(tmp_path / density, on_disk=True,
                                           config=f'[cues]\ndensity = "{density}"\n{extra}')
    plan = _call(root, "reader.guide_plan", {"extractionId": "ext1"})["result"]
    out: dict = {"cues": plan.get("cues"), "plan_keys": sorted(plan)}
    marks = (plan.get("cues") or {}).get("marks") or []
    if marks:
        first = marks[0]["cueId"]
        answer = _call(root, "reader.cue_action", {"extractionId": "ext1", "cueId": first, "action": "opened"})
        result = dict(answer["result"])
        result.pop("eventId", None)  # a fresh ULID per run
        out["opened"] = result
        prefs = _call(root, "reader.cue_preferences", {"sourceId": "src1"})["result"]
        out["preferences"] = prefs
    return out


def test_rw3a_cues_with_every_rw3b_switch_off_are_byte_identical_to_the_base(tmp_path):
    observed = {density: _observed(tmp_path, density) for density in DENSITIES}
    text = json.dumps(observed, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    if _writing():
        FIXTURE.write_text(text, encoding="utf-8")
        pytest.skip("pin written on the base")
    assert text == FIXTURE.read_text(encoding="utf-8")


def test_cues_switched_off_entirely_still_carry_no_cues_key(tmp_path):
    root, _vault, _repository = _cue_vault(tmp_path, on_disk=True)
    append_config_toml(root, "[cues]\nenabled = false\n" + ("" if _writing() else RW3B_OFF.replace(
        "discovery_enabled = false", "discovery_enabled = true")))
    plan = _call(root, "reader.guide_plan", {"extractionId": "ext1"})["result"]
    assert "cues" not in plan
