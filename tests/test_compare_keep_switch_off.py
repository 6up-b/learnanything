"""RW4d's kill switch restores RW4a's compare byte for byte (spec §7.8, §12; G18).

With ``reader_compare.keep_enabled`` off, the library answer, the compare
table, the stored ``library_asks`` row and the prompt contract are exactly
what the base tree (``3988cf778``, the RW4b landing, before any RW4d code)
produced for the same faked comparison. The golden file was recorded on that
tree (``RW4D_WRITE_GOLDEN=1`` with the base's ``src`` first on the path);
ULIDs are replaced by their order of appearance and times are left out.
Plan-first transport T1 edited only the three unavailable-route ``reason``
strings by hand (the default route is now the signed-out ChatGPT plan, not an
unconfigured Codex checkout); nothing else was re-recorded.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import pytest

from tests.library_ask_fixtures import ask_rows, build_library_vault, call, context, set_config, table_counts
from tests.source_service_fakes import FakeServiceLLM

GOLDEN = Path(__file__).parent / "fixtures" / "compare_keep_switch_off.json"
WRITE = os.environ.get("RW4D_WRITE_GOLDEN") == "1"
_ULID = re.compile(r"[0-9A-HJKMNP-TV-Z]{26}")
QUESTION = "why does the determinant change sign when two rows are swapped"
PROPOSAL_TABLES = ["source_objects", "source_object_versions", "source_object_citations", "source_object_relations"]
#: Wall-clock fields (times and durations), never part of what is pinned.
VOLATILE = {"createdAt", "created_at", "timingsMs", "timings_ms", "latencyMs", "latency_ms", "elapsedMs",
            "elapsed_ms", "durationMs", "duration_ms"}


def _normalized(value: Any) -> Any:
    text = json.dumps(value, sort_keys=True, ensure_ascii=False)
    seen: dict[str, str] = {}

    def swap(match: re.Match[str]) -> str:
        return seen.setdefault(match.group(0), f"<ULID{len(seen)}>")

    return json.loads(_ULID.sub(swap, text))


def _without(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _without(item) for key, item in value.items() if key not in VOLATILE}
    if isinstance(value, list):
        return [_without(item) for item in value]
    return value


def _record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    import learnloop.instructional.sources as service

    paths, repository, _spans = build_library_vault(tmp_path / "vault")
    if not WRITE:
        # Recorded on the base tree, which has no keep_enabled key.
        set_config(paths, "reader_compare", keep_enabled=False)
        # RW7a (landed after this golden was recorded): off, so its contract key
        # and Orient's "what matters here?" are absent; these pins are RW4d's.
        set_config(paths, "reading_paths", enabled=False)
        # RW5a (landed after this golden too): off, so its contract key and
        # "make this explorable" are absent; these pins are RW4d's.
        set_config(paths, "figures", enabled=False)
    ctx = context(paths.root)
    real = service.propose_comparison
    llm = FakeServiceLLM()
    monkeypatch.setattr(service, "propose_comparison", lambda *a, **k: real(*a, client=llm, verify_client=llm, **k))
    contract = call(ctx, "reader.prompt_contract", {})
    asked = call(ctx, "reader.library_ask", {"query": QUESTION, "extractionId": "ext_text", "spanIds": ["t3"],
                                             "learningObjectIds": ["lo_matrices"]})
    table = call(ctx, "reader.library_compare", {"askId": asked["askId"],
                                                  "pinnedSpanKeys": ["ext_book:s6", "ext_text:t3"],
                                                  "openSourceId": "src_text"})
    # The row's JSON columns are read as JSON, so their wall-clock fields
    # (the search's timings) are left out like any other.
    rows = [{key: (json.loads(value) if key.endswith("_json") and isinstance(value, str) else value)
             for key, value in row.items() if key != "created_at"} for row in ask_rows(repository)]
    return _normalized(_without({
        "contract": contract, "ask": asked, "table": table, "rows": rows,
        "proposals": table_counts(repository, PROPOSAL_TABLES),
    }))


def test_keep_off_is_rw4as_compare_byte_for_byte(tmp_path, monkeypatch):
    recorded = _record(tmp_path, monkeypatch)
    if WRITE:
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(recorded, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                          encoding="utf-8")
        pytest.skip("golden written")
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    for key in golden:
        assert recorded[key] == golden[key], key
    assert recorded == golden
    assert recorded["proposals"] == {table: 0 for table in PROPOSAL_TABLES}


def test_keep_off_every_rw4d_rpc_refuses_and_writes_nothing(tmp_path, monkeypatch):
    if WRITE:
        pytest.skip("RW4d's RPCs do not exist on the base tree")
    from learnloop_sidecar.errors import SidecarError

    import learnloop.instructional.sources as service

    paths, repository, _spans = build_library_vault(tmp_path / "vault")
    set_config(paths, "reader_compare", keep_enabled=False)
    ctx = context(paths.root)
    real = service.propose_comparison
    llm = FakeServiceLLM()
    monkeypatch.setattr(service, "propose_comparison", lambda *a, **k: real(*a, client=llm, verify_client=llm, **k))
    asked = call(ctx, "reader.library_ask", {"query": QUESTION, "extractionId": "ext_text", "spanIds": ["t3"]})
    call(ctx, "reader.library_compare", {"askId": asked["askId"], "pinnedSpanKeys": ["ext_book:s6", "ext_text:t3"]})
    watched = PROPOSAL_TABLES + ["library_asks", "interaction_events"]
    before = table_counts(repository, watched)
    for name, params in (
        ("reader.library_compare_keep", {"askId": asked["askId"]}),
        ("reader.library_compare_keep", {"toolCallId": "stc_x"}),
        ("reader.library_compare_remove", {"askId": asked["askId"]}),
        ("reader.library_compare_reopen", {"askId": asked["askId"]}),
        ("reader.kept_comparisons", {"extractionId": "ext_text"}),
    ):
        with pytest.raises(SidecarError) as caught:
            call(ctx, name, params)
        assert caught.value.code == "reader_compare_keep_disabled", name
    # Perspectives are RW4d's: refused while it is off (the table above had none).
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.library_compare", {"askId": asked["askId"], "pinnedSpanKeys": ["ext_book:s6", "ext_text:t3"],
                                             "requestedPerspectives": ["geometric view"]})
    assert caught.value.code == "reader_compare_keep_disabled"
    assert table_counts(repository, watched) == before
    assert "compareKeep" not in call(ctx, "reader.prompt_contract", {})
