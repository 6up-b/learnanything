"""RW4e's kill switches restore a12ba5ba9's Reader byte for byte (spec §7.9, §12).

With ``roles.on_demand_enabled`` and ``roles.positive_filter_enabled`` off,
the library answer, its organizer notes and request, cue discovery (its
judge's requests, links and ledger) and the sources service's
``find_sources`` (the ``roles`` filter and the intents' lists) answer exactly
what the base tree (``a12ba5ba9``, the RW4d landing, before any RW4e code)
answered for the same vault, **although the tip's vault holds role proposals
on several of the passages** (written before the run, as the batch labeller
would). Neither judge writes a proposal while ``on_demand_enabled`` is off.

The golden file was recorded on that tree (``RW4E_WRITE_GOLDEN=1`` and
``-o pythonpath=fixtures-local/base-a12/src``, the base's ``git archive``:
pytest's own ``pythonpath = ["src"]`` would otherwise put this tree first),
which has no ``[roles]`` section and no proposal writer; ULIDs are replaced by their order of appearance and
wall-clock fields are left out. Fakes only.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

import pytest

from tests.library_ask_fixtures import OrganizerFake, ask_rows, call, context, table_counts
from tests.passage_cue_fakes import CueJudgeFake, build_cue_vault, loaded, set_config
from tests.source_service_fakes import FakeServiceLLM

GOLDEN = Path(__file__).parent / "fixtures" / "roles_switch_off_a12ba5ba9.json"
WRITE = os.environ.get("RW4E_WRITE_GOLDEN") == "1"
_ULID = re.compile(r"[0-9A-HJKMNP-TV-Z]{26}")
PROPOSAL_TABLES = ["source_objects", "source_object_versions", "source_object_citations", "source_object_relations"]
VOLATILE = {"createdAt", "created_at", "timingsMs", "timings_ms", "latencyMs", "latency_ms", "elapsedMs",
            "elapsed_ms", "durationMs", "duration_ms", "started_at", "finished_at",
            # A hash over the targets' refs, which carry a fresh episode ULID per run.
            "targets_key", "targetsKey"}
#: Ids hashed from a ULID-bearing target ref (a fresh episode per run): replaced
#: by their order of appearance, as ULIDs are.
_HASHED = re.compile(r"plink_[0-9a-f]{32}")
#: A cue target's state key (24 hex digits): a hash over its episode's state,
#: which carries the run's clock; replaced by order of appearance.
_STATE = re.compile(r"\b[0-9a-f]{24}\b")
QUESTION = "why does the determinant change sign when two rows are swapped"
#: The proposals the tip's vault holds before the run: a contrast on the
#: row-swap passage RW3b's misconception targets, an intuition and a
#: definition on prose, a worked example, a counterexample in the other book,
#: an explanation on an exercise and on a solution (exclusions stay).
SEEDED = (
    ("ext_text", "t3", "contrast", "high"),
    ("ext_text", "t2", "intuition", "high"),
    ("ext_text", "t2", "definition", "medium"),
    ("ext_text", "t5", "worked_example", "high"),
    ("ext_text", "t9", "explanation", "high"),
    ("ext_text", "t12", "explanation", "high"),
    ("ext_book", "s2", "counterexample", "medium"),
    ("ext_book", "s6", "alternative_treatment", "low"),
)


def _normalized(value: Any) -> Any:
    text = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    seen: dict[str, str] = {}

    def swap(match: re.Match[str]) -> str:
        return seen.setdefault(match.group(0), f"<ULID{len(seen)}>")

    text = _ULID.sub(swap, text)
    links: dict[str, str] = {}
    text = _HASHED.sub(lambda match: links.setdefault(match.group(0), f"<LINK{len(links)}>"), text)
    states: dict[str, str] = {}
    text = _STATE.sub(lambda match: states.setdefault(match.group(0), f"<STATE{len(states)}>"), text)
    return json.loads(text)


def _without(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _without(item) for key, item in value.items() if key not in VOLATILE}
    if isinstance(value, list):
        return [_without(item) for item in value]
    return value


def _rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{key: (json.loads(value) if key.endswith("_json") and isinstance(value, str) else value)
             for key, value in row.items()} for row in rows]


def _sha(texts: list[str]) -> list[str]:
    return [hashlib.sha256(text.encode("utf-8")).hexdigest() for text in texts]


def _seed(vault: Any, repository: Any) -> None:
    from learnloop.reader import source_roles as RS

    written = RS.propose_roles(vault, repository, [
        {"extraction_id": extraction_id, "span_id": span_id, "role": role, "confidence": confidence,
         "ledger_id": f"rlb_seed_{index}"}
        for index, (extraction_id, span_id, role, confidence) in enumerate(SEEDED)
    ], judge="role_labeller", prompt_version="role_labeller.v1", model="seed")
    assert len(written["written"]) == len(SEEDED), written


def _find(vault: Any, repository: Any) -> dict[str, Any]:
    from learnloop.source_retrieval.find_sources import find_sources_for_caller
    from learnloop.source_retrieval.policy import CallerContext

    reading = CallerContext(kind="reader")
    llm = FakeServiceLLM()
    calls = {
        "counterexample": ("determinant rows swapped", {"roles": ["counterexample"]}),
        "intuition": ("eigenvalues characteristic polynomial", {"roles": ["intuition"]}),
        "contrast": ("determinant sign rows", {"roles": ["contrast", "definition"]}),
        "exercise": ("solve eigenvalue", {"roles": ["exercise"]}),
        "explain": ("eigenvalues characteristic polynomial determinant", {}),
        "worked_example": ("solve for the eigenvalue", {"intent": "worked_example", "rerank_client": llm}),
        "alternative": ("eigenvalues", {"intent": "alternative", "rerank_client": llm}),
        "remediate": ("swapping rows determinant", {"intent": "remediate", "rerank_client": llm}),
        "practice_bound": ("subtracting gives eigenvalue", {
            "roles": ["explanation"], "scope": "teaching",
            "caller": CallerContext(kind="tutor", context="practice", item_id="pi_eigen_1")}),
    }
    out: dict[str, Any] = {}
    for name, (query, kwargs) in calls.items():
        caller = kwargs.pop("caller", reading)
        try:
            result = find_sources_for_caller(vault, repository, query, caller=caller, **kwargs)
        except Exception as exc:  # noqa: BLE001 - a refusal is pinned like an answer
            out[name] = {"error": f"{type(exc).__name__}: {exc}"}
            continue
        out[name] = {"hits": [[hit["extraction_id"], hit["span_id"], hit.get("role"), hit.get("verdict")]
                              for hit in result.hits],
                     "status": result.status, "manifest": result.manifest}
    return out


def _record(tmp_path: Path) -> dict[str, Any]:
    from learnloop.db.stores import reader_cue_links as store
    from learnloop.source_retrieval import passage_cues as PC

    paths, repository, _spans = build_cue_vault(tmp_path / "vault")
    if not WRITE:
        set_config(paths, "roles", on_demand_enabled=False, positive_filter_enabled=False)
        _seed(loaded(paths), repository)
    before = table_counts(repository, PROPOSAL_TABLES)
    ctx = context(paths.root)
    organizer = OrganizerFake(wrong_cite=("p2",))
    ctx.library_organizer_client = organizer
    asked = call(ctx, "reader.library_ask", {"query": QUESTION, "extractionId": "ext_text", "spanIds": ["t3"],
                                             "learningObjectIds": ["lo_matrices"]})
    notes = call(ctx, "reader.library_ask_notes", {"askId": asked["askId"]})
    where_else = call(ctx, "reader.library_ask", {"query": "eigenvalues characteristic polynomial",
                                                  "entry": "where_else_explained", "extractionId": "ext_text",
                                                  "spanIds": ["t2"]})
    vault = loaded(paths)
    judge = CueJudgeFake(roles=(("contrast", "high"), ("definition", "medium")))
    discovered = PC.discover(vault, repository, "ext_text", client=judge)
    with repository.connection() as connection:
        links = store.links_for_extraction(connection, "ext_text")
        ledger = [dict(row) for row in connection.execute(
            "SELECT id, task, left_kind, left_id, right_kind, right_id, verdict, score, prompt_version, input_hash "
            "FROM judgment_ledger ORDER BY id")]
    if WRITE:  # recorded on the base tree, never on this one
        import learnloop.source_retrieval.find_sources as base_module
        assert "base-a12" in str(base_module.__file__), base_module.__file__
    found = _find(vault, repository)
    after = table_counts(repository, PROPOSAL_TABLES)
    return _normalized(_without({
        "ask": asked, "notes": notes, "where_else": where_else, "rows": _rows(ask_rows(repository)),
        "organizer_prompts": _sha(organizer.prompts),
        "discovered": discovered, "links": links, "judge_prompts": _sha(judge.prompts), "ledger": ledger,
        "find_sources": found,
        "proposals_written_by_the_run": {table: after[table] - before[table] for table in PROPOSAL_TABLES},
    }))


def test_both_role_switches_off_are_a12ba5ba9_byte_for_byte(tmp_path):
    recorded = _record(tmp_path)
    if WRITE:
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(recorded, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                          encoding="utf-8")
        pytest.skip("golden written on the base")
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    if os.environ.get("RW4E_DUMP_RECORDED"):  # a diagnostic copy of what the tip answered
        Path(os.environ["RW4E_DUMP_RECORDED"]).write_text(
            json.dumps(recorded, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    assert [key for key in golden if recorded.get(key) != golden[key]] == []
    assert recorded == golden
    assert recorded["proposals_written_by_the_run"] == {table: 0 for table in PROPOSAL_TABLES}
