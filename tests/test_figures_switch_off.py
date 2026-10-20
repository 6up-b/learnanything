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
    return {"contract": call(ctx, "reader.prompt_contract", {})}


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
    assert recorded.pop("figures") == {"predictions": True, "region": True, "revisions": True}
    added = []
    for group in recorded["intent"]["palette"]:
        kept = [action for action in group["actions"] if action["effect"] != {"kind": "figure"}]
        added += [action["id"] for action in group["actions"] if action["effect"] == {"kind": "figure"}]
        group["actions"] = kept
    assert added == ["make_explorable"]
    assert recorded == golden
