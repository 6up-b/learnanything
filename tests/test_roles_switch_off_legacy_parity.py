"""RW4e fix round 4: with the role switches off, legacy retrieval and the cue
judge's valid answers are a12ba5ba9's exactly (spec_reader_workbench_v1 §7.9, §12).

* **Legacy source objects** (no RW4e proposal: ordinary ``claim`` objects
  with an ``authorial_role`` and a ``confidence``, one strong and one weak):
  with ``roles.positive_filter_enabled`` off, ``find_sources``' intent lists,
  its ``roles=`` filter and its low-confidence handling, with and without
  ``roles=`` and with a caller exclusion, and RW3b's contrast list, answer
  what the base answered. Fix round 3's effective eligibility and its
  fallback apply only while the switch is on.
* **The cue judge's valid answer** (Codex verify ``20261020-222324-zO2vAN``
  finding 2): a ``roles`` array the base schema accepts, with a duplicate
  role, is parsed, returned and stored exactly as the base did (duplicates and
  order kept) under both switch states; only the proposals (written while
  ``on_demand_enabled`` is on) are deduplicated.

The golden file was recorded on the base tree (``RW4E_WRITE_LEGACY_GOLDEN=1``
and ``-o pythonpath=fixtures-local/tmp/base-a12-r4/src``, the base's
``git archive``), which has no ``[roles]`` section. Fakes only.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from tests.passage_cue_fakes import CueJudgeFake, build_cue_vault, loaded, set_config
from tests.source_service_fakes import FakeServiceLLM
from tests.test_roles_switch_off import _normalized, _sha, _without

GOLDEN = Path(__file__).parent / "fixtures" / "roles_switch_off_legacy_a12ba5ba9.json"
WRITE = os.environ.get("RW4E_WRITE_LEGACY_GOLDEN") == "1"
QUERY = "eigenvalues characteristic polynomial"
#: The legacy objects: (span, object type, authorial role, confidence). A and
#: B are the verify's strong and weak ``claim`` pair: A on the query's own
#: words (t2), B on the row swap (t3, no query word, so it reaches the pool
#: only through a list). C and D are contrast-list rows on the target's LO: a
#: confident counterexample on a solution block and a weak contrast on prose.
LEGACY = (
    ("t2", "claim", "intuition", "high"),
    ("t3", "claim", "intuition", "low"),
    ("t12", "claim", "counterexample", "high"),
    ("t2", "claim", "contrast", "low"),
)
#: A cue judge's valid answer with one role twice, in this order.
DUPLICATE_ROLES = (("contrast", "low"), ("contrast", "high"))


def _base_check() -> None:
    if WRITE:  # recorded on the base tree, never on this one
        import learnloop.source_retrieval.find_sources as base_module
        assert "base-a12" in str(base_module.__file__), base_module.__file__


def _seed_legacy(repository: Any) -> None:
    from learnloop.ingest.locators import format_block_span
    from learnloop.reader.source_objects import author_source_object

    for span_id, object_type, role, confidence in LEGACY:
        author_source_object(repository, source_id="src_text", revision_id="rev_text", object_type=object_type,
                             authorial_role=role, content={"confidence": confidence},
                             citations=[{"revision_id": "rev_text", "span_id": span_id}])
    # The solution teaches the target's LO too, so the contrast list reads it.
    repository.insert_entity_source_link(
        entity_type="learning_object", entity_id="lo_matrices", locator=format_block_span("ext_text", "t12"),
        relation="primary", source_id="src_text", revision_id="rev_text", extraction_id="ext_text")


def _legacy_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    from learnloop.source_retrieval import find_sources as FS
    from learnloop.source_retrieval import passage_cues as PC
    from learnloop.source_retrieval.policy import CallerContext

    paths, repository, _spans = build_cue_vault(tmp_path / "vault")
    if not WRITE:
        set_config(paths, "roles", on_demand_enabled=False, positive_filter_enabled=False)
    _seed_legacy(repository)
    vault = loaded(paths)
    _base_check()
    seen: list[dict[str, Any]] = []
    real = FS.search_spans

    def spy(*args, extra_lists=None, **kwargs):
        search = real(*args, extra_lists=extra_lists, **kwargs)
        seen.append({"lists": {name: [list(key) for key in keys] for name, keys in (extra_lists or {}).items()},
                     "pool": [list(hit.key) for hit in search.hits], "role_basis": dict(search.role_basis)})
        return search

    monkeypatch.setattr(FS, "search_spans", spy)
    reading = CallerContext(kind="reader")
    excluded = {"exclude_span_keys": [["ext_text", "t2"]]}
    calls = {
        "explain": {},
        "explain_excluded": dict(excluded),
        "explain_roles": {"roles": ["intuition"]},
        "explain_roles_excluded": {"roles": ["intuition"], **excluded},
        "alternative": {"intent": "alternative"},
        "alternative_excluded": {"intent": "alternative", **excluded},
        "alternative_roles_excluded": {"intent": "alternative", "roles": ["intuition"], **excluded},
        "remediate": {"intent": "remediate"},
    }
    out: dict[str, Any] = {}
    for name, kwargs in calls.items():
        if kwargs.get("intent", "explain") != "explain":
            kwargs["rerank_client"] = FakeServiceLLM()
        result = FS.find_sources_for_caller(vault, repository, QUERY, caller=reading, **kwargs)
        out[name] = {"search": seen[-1], "status": result.status,
                     "hits": [[hit["extraction_id"], hit["span_id"], hit.get("verdict")] for hit in result.hits]}
    (target,) = PC.cue_targets(vault, repository, "ext_text")
    out["contrast_list"] = [list(key) for key in PC.contrast_list(vault, repository, target, "ext_text")]
    return out


def _cue_record(tmp_path: Path, switches: bool | None) -> tuple[dict[str, Any], Any, Any]:
    from learnloop.db.stores import reader_cue_links as store
    from learnloop.source_retrieval import passage_cues as PC

    paths, repository, _spans = build_cue_vault(tmp_path / "cue")
    if switches is not None:
        set_config(paths, "roles", on_demand_enabled=switches, positive_filter_enabled=switches)
    vault = loaded(paths)
    _base_check()
    answer = {"judgments": [{"ref": "p1", "relation": "clarifies_distinction", "rationale": "it draws it",
                             "quote": "rows", "roles": [{"role": role, "confidence": confidence}
                                                        for role, confidence in DUPLICATE_ROLES]}],
              "picks": ["p1"]}
    parsed = PC.CueJudgeResult.model_validate_json(json.dumps(answer)).model_dump(mode="json")
    judge = CueJudgeFake(roles=DUPLICATE_ROLES)
    discovered = PC.discover(vault, repository, "ext_text", client=judge)
    discovered.pop("role_proposals", None)
    for target in discovered.get("targets") or ():
        target.pop("role_proposals", None)
    with repository.connection() as connection:
        links = store.links_for_extraction(connection, "ext_text")
        ledger = [dict(row) for row in connection.execute(
            "SELECT id, task, left_kind, left_id, right_kind, right_id, verdict, score, prompt_version, input_hash "
            "FROM judgment_ledger ORDER BY id")]
    record = _normalized(_without({"parsed": parsed, "discovered": discovered, "links": links,
                                   "judge_prompts": _sha(judge.prompts), "ledger": ledger}))
    return record, repository, judge


def _golden() -> dict[str, Any]:
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


def test_record_the_base_golden(tmp_path, monkeypatch):
    if not WRITE:
        pytest.skip("records the golden on the base tree only (RW4E_WRITE_LEGACY_GOLDEN=1)")
    legacy = _legacy_record(tmp_path / "legacy", monkeypatch)
    cue, _repository, _judge = _cue_record(tmp_path / "cue", None)
    GOLDEN.parent.mkdir(parents=True, exist_ok=True)
    GOLDEN.write_text(json.dumps({"legacy": legacy, "cue": cue}, indent=1, sort_keys=True, ensure_ascii=False)
                      + "\n", encoding="utf-8")


@pytest.mark.skipif(WRITE, reason="the golden is being recorded")
def test_legacy_source_objects_with_the_positive_filter_off_are_a12ba5ba9s(tmp_path, monkeypatch):
    recorded = _legacy_record(tmp_path, monkeypatch)
    golden = _golden()["legacy"]
    assert [name for name in golden if recorded.get(name) != golden[name]] == []
    assert recorded == golden
    # The verify's case: the weak claim stays in the explain list, after the strong ones.
    assert recorded["explain"]["search"]["lists"]["source_objects"] == [
        ["ext_text", "t2"], ["ext_text", "t12"], ["ext_text", "t3"]]
    # The confident contrast on a solution still leads the contrast list, as on the base.
    assert recorded["contrast_list"] == [["ext_text", "t12"], ["ext_text", "t2"]]


@pytest.mark.skipif(WRITE, reason="the golden is being recorded")
@pytest.mark.parametrize("switches", [False, True], ids=["switches_off", "switches_on"])
def test_a_valid_cue_answer_with_a_duplicate_role_is_parsed_and_stored_as_a12ba5ba9_did(tmp_path, switches):
    from tests.test_roles_judges import _proposals

    recorded, repository, _judge = _cue_record(tmp_path, switches)
    golden = _golden()["cue"]
    assert [name for name in golden if recorded.get(name) != golden[name]] == []
    assert recorded == golden
    assert recorded["parsed"]["judgments"][0]["roles"] == [
        {"role": role, "confidence": confidence} for role, confidence in DUPLICATE_ROLES]
    assert recorded["links"] and all(link["roles"] == recorded["parsed"]["judgments"][0]["roles"]
                                     for link in recorded["links"])
    rows = _proposals(repository)
    if switches:
        # Only the proposals are deduplicated: one contrast per judged passage, its first entry.
        spans = [row["span_id"] for row in rows]
        assert rows and len(spans) == len(set(spans))
        assert {(row["authorial_role"], row["content"]["confidence"]) for row in rows} == {("contrast", "low")}
    else:
        assert rows == []
