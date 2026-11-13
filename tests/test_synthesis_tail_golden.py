"""What one bootstrap and one append build write, pinned whole on fixed fake model answers.

Each case builds a small synthetic vault, runs one build, and compares a record of that build with its golden file
under ``tests/goldens/synthesis_tail/``. The record holds every row the build added, changed or removed in the vault's
database, table by table (proposal batch and items with their gate verdicts and the instrument gates' audit,
dependencies, manifest, agent and synthesis runs, checkpoints, facet-identity actions, links, epigraphs ...); every
vault file it changed (what an apply wrote); the model requests it made, in order, as purpose and prompt digest; and
its returned result, or its typed error.

The cases cover, for each mode: a clean run (applied), a run a synthesis gate fails, a run an instrument gate holds,
items off, a rerun an equal waiting proposal answers, and a rerun after the learner rejected the whole proposal;
the append also runs its narrow-adjunct preset. The run's head (what is refused before anything is written, and what
the manifest and run rows record) has its own cases: an unknown source set, bootstrap's unsupported mode, a run
refused by its input ceiling after its rows were opened, an unlimited run's budget record, and the append's unit
filter and revision diff. The append's model call has its own cases, which also record each request as sent (its
schema and output limit) and the budgets declared on its receipt: a span round under a per-request input ceiling,
answers an over-budget run saved and its rerun reuses, a rejected match followed by a gate failure while another run
saves an answer again, and a call that fails part way. The fake answers are the house fakes'.

Ids are reproducible: the process's ULID stream is seeded and its clock held for the whole case, setup included.
Stamps written from the wall clock (the run rows' completion) read ``<wall>``; ids from a stream this does not seed
read ``<ulid:n>`` in order of first appearance. The vault's algorithm tag reads ``<head tag>``, and the manifest
and context hashes that fold it in read ``<manifest:n>`` and ``<context:n>``, so a new successor tag alone moves
nothing here.

A change that means to change what a build writes regenerates the files and shows the difference in review:

    SYNTHESIS_TAIL_GOLDEN_WRITE=1 uv run pytest tests/test_synthesis_tail_golden.py

``SYNTHESIS_TAIL_GOLDEN_ACTUAL=<dir>`` writes each case's record there as well, to diff against its golden.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import yaml

from learnloop.ai.execution import observe_model_calls
from learnloop.ai.usage import TokenUsage
from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.content.proposals.proposals import reject_items
from learnloop.content.synthesis.ai_contracts import (
    AppendConflict,
    AppendNotationMapping,
    AppendProvenanceLink,
    AppendReconciliation,
    AppendRestructure,
    SynthPracticeItem,
    SynthRecipe,
    SynthSpanRef,
    SynthSpanRequest,
)
from learnloop.content.synthesis.source_append import append_source
from learnloop.content.synthesis.source_set_synthesis import StudyMapError, create_study_map

from tests.facet_reword_paths_helpers import NEW_SPAN, _facet_restructure
from tests.source_append_helpers import (
    FakeAppendClient,
    _bootstrap_and_add,
    _default_append,
    _first_new_span,
    _neighborhood_facet_id,
)
from tests.source_set_synthesis_helpers import FakeSynthesisClient, _CLOCK, _default_payload, _setup

GOLDEN_DIR = Path(__file__).parent / "goldens" / "synthesis_tail"
WRITE = os.environ.get("SYNTHESIS_TAIL_GOLDEN_WRITE") == "1"

#: The held ULID clock (ms): every id a case mints shares it, so ids differ only in their counted randomness.
_ULID_MS = 1_790_000_000_000
_ULID = re.compile(r"\b[0-9A-HJKMNP-TV-Z]{26}\b")
_STAMP = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?")
#: Tables a build never writes on its own account; FTS shadow tables hold binary segments.
#: A new algorithm tag is not a change of what a build writes: the vault's tag reads ``<head tag>``, and the
#: manifest and context hashes that fold it in read ``<manifest:n>`` and ``<context:n>`` (the manifest's fields
#: are recorded beside, so its content stays pinned).
_HEAD_TAG = re.compile(re.escape(LATEST_ALGORITHM_VERSION) + r"(?![0-9.])")
_SKIPPED_TABLE = re.compile(r"_(data|idx|content|docsize|config)$")


# --- recording fakes ---------------------------------------------------------


class _Recorder:
    """Records each structured request (purpose, prompt digest) and reports a fixed usage per request, so the agent
    runs' recorded tokens show where each build drains its client."""

    requests: list[list[str]]
    _pending: int

    def _record(self, request: Any) -> None:
        if not hasattr(self, "requests"):
            self.requests, self._pending = [], 0
        self.requests.append([request.purpose, _digest(_normalize_text(request.prompt))])
        # The rest of what is sent, which the call cases record (see ``_record_sent``).
        getattr(self, "sent", []).append({
            "purpose": request.purpose,
            "result_model": request.result_model.__name__,
            "schema": _digest(json.dumps(request.result_model.model_json_schema(), sort_keys=True)),
            "output_budget_tokens": request.output_budget_tokens,
            "timeout_seconds": request.timeout_seconds,
            "reasoning_effort": request.reasoning_effort,
            "isolated": request.isolated,
        })
        self._pending += 1

    def consume_usage(self) -> TokenUsage:
        pending, self._pending = getattr(self, "_pending", 0), 0
        return TokenUsage(input_tokens=100 * pending, output_tokens=10 * pending, calls=pending)


class _SynthesisClient(_Recorder, FakeSynthesisClient):
    def complete(self, request: Any) -> Any:
        self._record(request)
        return super().complete(request)


class _AppendClient(_Recorder, FakeAppendClient):
    def complete(self, request: Any) -> Any:
        self._record(request)
        return super().complete(request)


# --- normalization -----------------------------------------------------------


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _normalize_text(text: str) -> str:
    return _HEAD_TAG.sub("<head tag>", _STAMP.sub(lambda match: _stamp(match.group(0)), text))


def _stamp(text: str) -> str:
    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00").replace(" ", "T"))
    except ValueError:
        return text
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return "<wall>" if abs((moment - datetime.now(UTC)).total_seconds()) < 3 * 86400 else text


class _Ids:
    """Ids the seeded stream did not mint, as ``<ulid:n>`` in order of first appearance."""

    def __init__(self, named: dict[str, str]) -> None:
        self.seen: dict[str, str] = {}
        self.named = named

    def __call__(self, text: str) -> str:
        def one(match: re.Match[str]) -> str:
            value = match.group(0)
            if value.startswith(_encode_ms(_ULID_MS)):
                return value
            return self.seen.setdefault(value, f"<ulid:{len(self.seen)}>")

        for value, name in self.named.items():
            text = text.replace(value, name)
        return _ULID.sub(one, _normalize_text(text))


def _encode_ms(ms: int) -> str:
    alphabet = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    out = ""
    for _ in range(10):
        out = alphabet[ms & 31] + out
        ms >>= 5
    return out


def _clean(value: Any, ids: _Ids) -> Any:
    if isinstance(value, dict):
        return {str(key): _clean(item, ids) for key, item in value.items()}
    if isinstance(value, list | tuple | set | frozenset):
        items = [_clean(item, ids) for item in value]
        return sorted(items, key=json.dumps) if isinstance(value, set | frozenset) else items
    if isinstance(value, bytes):
        return f"<bytes:{_digest(value.hex())}>"
    if isinstance(value, str):
        stripped = value.strip()
        if stripped[:1] in "[{":
            try:
                return {"<json>": _clean(json.loads(value), ids)}
            except ValueError:
                pass
        return ids(value)
    return value


# --- what a build wrote ------------------------------------------------------


def _database(path: Path) -> dict[str, list[dict[str, Any]]]:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        tables = [
            row["name"] for row in connection.execute(
                "SELECT name, sql FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
            if not _SKIPPED_TABLE.search(row["name"]) and "VIRTUAL TABLE" not in str(row["sql"]).upper()
        ]
        out: dict[str, list[dict[str, Any]]] = {}
        for table in tables:
            try:
                rows = connection.execute(f'SELECT rowid AS "<rowid>", * FROM "{table}" ORDER BY rowid').fetchall()
            except sqlite3.OperationalError:  # WITHOUT ROWID
                rows = connection.execute(f'SELECT * FROM "{table}"').fetchall()
            out[table] = [dict(row) for row in rows]
        return out
    finally:
        connection.close()


def _row_key(row: dict[str, Any]) -> str:
    return str(row["<rowid>"]) if "<rowid>" in row else json.dumps(row, sort_keys=True, default=str)


def _database_changes(before: dict[str, list[dict]], after: dict[str, list[dict]]) -> dict[str, Any]:
    changes: dict[str, Any] = {}
    for table in sorted(set(before) | set(after)):
        old = {_row_key(row): row for row in before.get(table, [])}
        new = {_row_key(row): row for row in after.get(table, [])}
        added = [row for key, row in new.items() if key not in old]
        removed = [row for key, row in old.items() if key not in new]
        changed = [{"before": old[key], "after": row} for key, row in new.items() if key in old and old[key] != row]
        entry = {name: rows for name, rows in (("added", added), ("changed", changed), ("removed", removed)) if rows}
        if entry:
            changes[table] = entry
    return changes


def _files(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if not path.is_file() or relative.startswith("state.sqlite") or path.suffix in {".lock", ".sqlite"}:
            continue
        if "/." in f"/{relative}" or relative.endswith(("-wal", "-shm", "-journal")):
            continue
        out[relative] = path.read_text(encoding="utf-8", errors="replace")
    return out


def _file_changes(before: dict[str, str], after: dict[str, str]) -> dict[str, Any]:
    changes: dict[str, Any] = {}
    for name in sorted(set(before) | set(after)):
        if before.get(name) == after.get(name):
            continue
        text = after.get(name)
        if text is None:
            changes[name] = "<removed>"
        elif name.endswith((".yaml", ".yml")):
            changes[name] = {"<yaml>": yaml.safe_load(text)}
        else:
            changes[name] = text
    return changes


def _outcome(run: Any) -> dict[str, Any]:
    try:
        result = run()
    except StudyMapError as error:
        return {"error": {
            "code": error.code, "message": str(error), "diagnostics": error.diagnostics,
            "synthesis_run_id": error.synthesis_run_id, "candidate_preserved": error.candidate_preserved,
        }}
    return {"result": result.as_dict()}


def _record(root: Path, repo: Any, client: _Recorder, run: Any) -> dict[str, Any]:
    """What ``run`` (one build) wrote and returned, against the vault as it stood just before."""

    database, files = _database(repo.sqlite_path), _files(root)
    client.requests, client._pending = [], 0
    outcome = _outcome(run)
    changes = _database_changes(database, _database(repo.sqlite_path))
    manifests = [row["manifest_hash"] for row in changes.get("synthesis_manifests", {}).get("added", [])]
    manifests += [outcome["result"]["manifest_hash"]] if "result" in outcome else []
    contexts = [row["input_context_hash"] for row in changes.get("agent_runs", {}).get("added", [])]
    named: dict[str, str] = {}
    for label, values in (("manifest", manifests), ("context", contexts)):
        for value in values:
            if value and value not in named:
                named[value] = f"<{label}:{sum(name.startswith(f'<{label}:') for name in named.values())}>"
    return _clean({
        **outcome,
        "model_requests": client.requests,
        "database": changes,
        "files": _file_changes(files, _files(root)),
    }, _Ids(named))


def _record_sent(root: Path, repo: Any, client: _Recorder, run: Any) -> dict[str, Any]:
    """:func:`_record`, with every request as sent (its schema and output limit beside its prompt's digest) and the
    receipt each opened (the budgets declared on it): what moves if the call path sends anything else."""

    receipts: list[dict[str, Any]] = []

    def observe(event: str, payload: dict[str, Any]) -> None:
        if event == "start":
            receipts.append({
                "purpose": payload["purpose"], "root": payload["parent_call_id"] is None,
                "schema_hash": payload["schema_hash"], "budget_json": payload["budget_json"],
                "output_budget_tokens": payload["output_budget_tokens"],
            })

    client.sent = []
    with observe_model_calls(observe):
        record = _record(root, repo, client, run)
    return {**record, "sent": _clean(client.sent, _Ids({})), "receipts": _clean(receipts, _Ids({}))}


@pytest.fixture
def seeded_ids(monkeypatch):
    """Reproducible ids for the whole case: a held clock and seeded randomness for the process's ULID stream."""

    from learnloop import ids

    monkeypatch.setattr(ids, "_wall_clock_ms", lambda: _ULID_MS)
    monkeypatch.setattr(ids, "secrets", SimpleNamespace(randbits=random.Random(20261113).getrandbits))
    monkeypatch.setattr(ids, "_last_timestamp_ms", -1)
    monkeypatch.setattr(ids, "_last_randomness", 0)


def _check(name: str, record: dict[str, Any]) -> None:
    path = GOLDEN_DIR / f"{name}.json"
    text = json.dumps(record, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if WRITE:
        GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return
    assert path.exists(), f"no golden for {name}: regenerate with SYNTHESIS_TAIL_GOLDEN_WRITE=1"
    expected = json.loads(path.read_text(encoding="utf-8"))
    if os.environ.get("SYNTHESIS_TAIL_GOLDEN_ACTUAL"):
        Path(os.environ["SYNTHESIS_TAIL_GOLDEN_ACTUAL"], f"{name}.json").write_text(text, encoding="utf-8")
    assert record == expected, f"{name}: what the build wrote moved (see the module docstring to regenerate)"


# --- bootstrap ---------------------------------------------------------------


def _build(root, repo, client, **kwargs):
    kwargs.setdefault("brief", {"depth": "intro"})
    return create_study_map(root, "set_la", client=client, repository=repo, clock=_CLOCK, **kwargs)


def _vacuous_recipe(context, _n):
    payload = _default_payload(context)
    payload.blueprints[0] = payload.blueprints[0].model_copy(update={"recipes": [SynthRecipe(id="recipe_vacuous")]})
    return payload


def _selected_response(context, _n):
    payload = _default_payload(context)
    payload.practice_items[0] = payload.practice_items[0].model_copy(
        update={"prompt": "Which of the following statements is true about symmetric matrices?"})
    return payload


def test_bootstrap_clean_applied_with_its_exam_goal(tmp_path, seeded_ids):
    root, repo = _setup(tmp_path)
    client = _SynthesisClient()
    record = _record(root, repo, client, lambda: _build(
        root, repo, client, apply=True, create_goal=True,
        brief={"depth": "intro", "outcome": "exam preparation", "goal_title": "Final exam"},
    ))
    _check("bootstrap_clean_applied", record)


def test_bootstrap_a_synthesis_gate_fails(tmp_path, seeded_ids):
    root, repo = _setup(tmp_path, with_exam=False)
    client = _SynthesisClient(builder=_vacuous_recipe)
    _check("bootstrap_gate_fails", _record(root, repo, client, lambda: _build(root, repo, client)))


def test_bootstrap_an_instrument_gate_holds_an_item(tmp_path, seeded_ids):
    root, repo = _setup(tmp_path, with_exam=False)
    client = _SynthesisClient(builder=_selected_response)
    _check("bootstrap_instrument_gate_holds", _record(root, repo, client, lambda: _build(root, repo, client)))


def test_bootstrap_items_off(tmp_path, seeded_ids):
    root, repo = _setup(tmp_path, with_exam=False)
    client = _SynthesisClient()
    record = _record(root, repo, client, lambda: _build(
        root, repo, client, apply=True, brief={"depth": "intro", "practice_items": "as_you_read"}))
    _check("bootstrap_items_off", record)


def test_bootstrap_rerun_is_answered_by_the_waiting_proposal(tmp_path, seeded_ids):
    root, repo = _setup(tmp_path, with_exam=False)
    client = _SynthesisClient()
    _build(root, repo, client)
    _check("bootstrap_rerun_waiting", _record(root, repo, client, lambda: _build(root, repo, client, apply=True)))


def test_bootstrap_rerun_after_a_wholly_rejected_proposal(tmp_path, seeded_ids):
    root, repo = _setup(tmp_path, with_exam=False)
    client = _SynthesisClient()
    first = _build(root, repo, client)
    reject_items(root, first.proposal_id)
    _check("bootstrap_rerun_rejected", _record(root, repo, client, lambda: _build(root, repo, client)))


def test_bootstrap_an_unknown_source_set_is_refused_before_the_mode(tmp_path, seeded_ids):
    root, repo = _setup(tmp_path, with_exam=False)
    client = _SynthesisClient()
    record = _record(root, repo, client, lambda: create_study_map(
        root, "set_missing", client=client, repository=repo, clock=_CLOCK, mode="append"))
    _check("bootstrap_unknown_source_set", record)


def test_bootstrap_an_unsupported_mode_is_refused_before_any_write(tmp_path, seeded_ids):
    root, repo = _setup(tmp_path, with_exam=False)
    client = _SynthesisClient()
    _check("bootstrap_unsupported_mode", _record(root, repo, client, lambda: _build(root, repo, client, mode="append")))


def test_bootstrap_over_its_input_ceiling_fails_the_run_it_opened(tmp_path, seeded_ids):
    root, repo = _setup(tmp_path, with_exam=False)
    client = _SynthesisClient()
    record = _record(root, repo, client, lambda: _build(
        root, repo, client, budget_overrides={"synthesis_total_input_ceiling": 10}))
    _check("bootstrap_over_input_ceiling", record)


def test_bootstrap_unlimited_records_only_its_shard_size(tmp_path, seeded_ids):
    root, repo = _setup(tmp_path, with_exam=False)
    client = _SynthesisClient()
    record = _record(root, repo, client, lambda: _build(
        root, repo, client, unlimited_token_budget=True, budget_overrides={"synthesis_output_tokens": 123}))
    _check("bootstrap_unlimited", record)


# --- append ------------------------------------------------------------------


def _append(root, repo, client, **kwargs):
    return append_source(root, "set_la", client=client, new_revision_ids=["rev_alt"], repository=repo,
                         clock=_CLOCK, **kwargs)


def _mixed_append(context, _n):
    """A link (auto-applies), a notation mapping and a conflict (both reviewed)."""

    ext, unit, span = _first_new_span(context)
    target = _neighborhood_facet_id(context)
    ref = SynthSpanRef(extraction_id=ext, unit_id=unit, span_id=span)
    return AppendReconciliation(
        summary="mixed append",
        provenance_links=[AppendProvenanceLink(
            client_item_id="plink", reconciliation_intent="alternate_explanation", target_entity_type="facet",
            target_entity_id=target, relation="alternate", span=ref)],
        notation_mappings=[AppendNotationMapping(
            client_item_id="notation", target_entity_type="facet", target_entity_id=target,
            canonical_notation="A^T", alternate_notation="A'", context="transpose", span=ref)],
        conflicts=[AppendConflict(
            client_item_id="conflict1", entity_type="facet", entity_id=target,
            statement="sources disagree on the symmetry condition",
            left=SynthSpanRef(extraction_id="ext_text", unit_id="chapter_symmetry", span_id="s1"), right=ref)],
    )


def _append_item(prompt: str):
    def builder(context, _n):
        ext, unit, span = _first_new_span(context)
        return AppendReconciliation(summary="append with a practice item", practice_items=[SynthPracticeItem(
            client_item_id="pi_appended", learning_object_id="lo_diagonalize_symmetric", prompt=prompt,
            expected_answer="A^T = A.",
            provenance=[SynthSpanRef(extraction_id=ext, unit_id=unit, span_id=span, relation="exercise")])])

    return builder


def _with_restructure(context, _n):
    return _default_append(context).model_copy(update={"restructures": [AppendRestructure(
        client_item_id="forbidden_restructure", target_entity_type="learning_object",
        target_entity_id="lo_diagonalize_symmetric", operation="deactivate")]})


def test_append_clean_auto_applies_its_routine_link(tmp_path, seeded_ids):
    root, repo = _bootstrap_and_add(tmp_path, add_role="primary_textbook")
    client = _AppendClient(builder=_mixed_append)
    _check("append_clean_applied", _record(root, repo, client, lambda: _append(root, repo, client)))


def test_append_a_synthesis_gate_fails(tmp_path, seeded_ids):
    root, repo = _bootstrap_and_add(tmp_path, add_role="exam")
    rejected = _facet_restructure()
    client = _AppendClient(builder=lambda context, n: rejected(context, n))
    _check("append_gate_fails", _record(root, repo, client, lambda: _append(root, repo, client)))


def test_append_an_instrument_gate_holds_an_item(tmp_path, seeded_ids):
    root, repo = _bootstrap_and_add(tmp_path)
    client = _AppendClient(builder=_append_item("Which of the following statements defines a symmetric matrix?"))
    record = _record(root, repo, client, lambda: _append(root, repo, client, brief={"practice_items": "upfront"}))
    _check("append_instrument_gate_holds", record)


def test_append_items_off(tmp_path, seeded_ids):
    root, repo = _bootstrap_and_add(tmp_path)
    client = _AppendClient(builder=_append_item("State the definition of a symmetric matrix."))
    record = _record(root, repo, client, lambda: _append(root, repo, client, brief={"practice_items": "as_you_read"}))
    _check("append_items_off", record)


def test_append_rerun_is_answered_by_the_waiting_proposal_and_applies_it(tmp_path, seeded_ids):
    root, repo = _bootstrap_and_add(tmp_path)
    client = _AppendClient()
    _append(root, repo, client, auto_apply=False)
    _check("append_rerun_waiting", _record(root, repo, client, lambda: _append(root, repo, client)))


def test_append_rerun_after_a_wholly_rejected_proposal(tmp_path, seeded_ids):
    root, repo = _bootstrap_and_add(tmp_path)
    client = _AppendClient()
    first = _append(root, repo, client, auto_apply=False)
    reject_items(root, first.proposal_id)
    _check("append_rerun_rejected", _record(root, repo, client, lambda: _append(root, repo, client, auto_apply=False)))


def test_append_narrow_adjunct_drops_model_restructures(tmp_path, seeded_ids):
    root, repo = _bootstrap_and_add(tmp_path)
    client = _AppendClient(builder=_with_restructure)
    record = _record(root, repo, client, lambda: _append(root, repo, client, brief={"authoring_preset": "narrow_adjunct"}))
    _check("append_narrow_adjunct", record)


def test_append_an_unknown_source_set_is_refused_before_any_write(tmp_path, seeded_ids):
    root, repo = _bootstrap_and_add(tmp_path)
    client = _AppendClient()
    record = _record(root, repo, client, lambda: append_source(
        root, "set_missing", client=client, new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK))
    _check("append_unknown_source_set", record)


def test_append_over_its_input_ceiling_fails_the_run_it_opened(tmp_path, seeded_ids):
    root, repo = _bootstrap_and_add(tmp_path)
    client = _AppendClient()
    record = _record(root, repo, client, lambda: _append(
        root, repo, client, budget_overrides={"append_input_ceiling": 10}))
    _check("append_over_input_ceiling", record)


def test_append_a_unit_filter_a_revision_diff_and_no_limits(tmp_path, seeded_ids):
    """The append-only inputs its scope records: the change kind, the unit filter, the revision diff's hash, and the
    one budget an unlimited run still records."""

    root, repo = _bootstrap_and_add(tmp_path)
    client = _AppendClient()
    record = _record(root, repo, client, lambda: _append(
        root, repo, client, new_unit_ids={"rev_alt": ["chapter_symmetry_alt"]}, change_kind="revision_adopted",
        revision_diff={"old_revision_id": "rev_text", "new_revision_id": "rev_alt"}, unlimited_token_budget=True,
        budget_overrides={"append_neighborhood_input_tokens": 9000}, auto_apply=False))
    _check("append_unit_filter_diff_unlimited", record)


# --- the append's model call -------------------------------------------------
#
# What an append sends and saves, request by request: the span round, the answers it saves and reuses, the answers it
# drops, and a call that fails part way. These record each request whole (``_record_sent``).


#: Just over the span round's request (about 7,616 tokens, its first call's about 7,559), under the two together.
SPAN_ROUND_CEILING = 7_620
#: Between the first answer's size (about 107 tokens) and the span round's (about 399).
SPAN_ANSWER_OVER_BUDGET = 200


def _asks_for_a_span(then):
    """The first answer asks for the new inventory's first span; the span round's answer is ``then``'s."""

    def builder(context, n):
        if context.resolved_spans:
            return then(context, n)
        ext, unit, span = _first_new_span(context)
        return AppendReconciliation(summary="asks to read a span", span_requests=[SynthSpanRequest(
            extraction_id=ext, unit_id=unit, span_id=span, purpose="check the symmetry condition")])

    return builder


def test_append_span_round_under_a_per_request_input_ceiling(tmp_path, seeded_ids):
    """The span round sends the same request with the resolved span; its ceiling holds each request alone, so a
    ceiling just over the span round's request lets both through though their sum is over it."""

    root, repo = _bootstrap_and_add(tmp_path, add_role="primary_textbook")
    client = _AppendClient(builder=_asks_for_a_span(_mixed_append))
    record = _record_sent(root, repo, client, lambda: _append(
        root, repo, client, budget_overrides={"append_input_ceiling": SPAN_ROUND_CEILING}))
    _check("append_span_round", record)


def test_append_rerun_reuses_the_answers_an_over_budget_run_saved(tmp_path, seeded_ids):
    """An answer over the output budget fails the run but stays saved; the rerun under the default budget pays for
    nothing it already has."""

    root, repo = _bootstrap_and_add(tmp_path, add_role="primary_textbook")
    client = _AppendClient(builder=_asks_for_a_span(_mixed_append))
    first = _record_sent(root, repo, client, lambda: _append(
        root, repo, client, budget_overrides={"append_output_tokens": SPAN_ANSWER_OVER_BUDGET}))
    rerun = _record_sent(root, repo, client, lambda: _append(root, repo, client))
    _check("append_rerun_reuses_saved_answers", {"first": first, "rerun": rerun})


def _append_checkpoints(repo) -> list[tuple[str, dict[str, Any]]]:
    with repo.connection() as connection:
        rows = connection.execute(
            "SELECT cache_key, result_json FROM model_work_checkpoints WHERE purpose = 'append_reconciliation' "
            "ORDER BY rowid").fetchall()
    return [(row[0], json.loads(row[1])) for row in rows]


def _aligns_with_the_exam(context, _n):
    """The exam member's span asked for, then aligned with a learning object (an exam's only routine link)."""

    if not context.resolved_spans:
        return AppendReconciliation(summary="asks to read the exam's span", span_requests=[
            SynthSpanRequest(**NEW_SPAN, purpose="check what the exam asks")])
    return AppendReconciliation(summary="aligns the exam", provenance_links=[AppendProvenanceLink(
        client_item_id="plink_exam", reconciliation_intent="assessment_alignment",
        target_entity_type="learning_object", target_entity_id="lo_diagonalize_symmetric",
        relation="assessment_alignment", span=SynthSpanRef(**NEW_SPAN))])


def test_append_rejected_match_then_a_gate_failure_with_another_run_saving(tmp_path, seeded_ids):
    """A rerun after the whole append was rejected: its saved answers (a call and its span round) reproduce the
    rejected proposal, so they are dropped and the model asked again; while that fresh call runs, another run saves
    the span round's answer again, identical; the fresh answer, an exam-only reword, then fails the gates and is
    dropped. Which saved answers remain is what each drop names."""

    root, repo = _bootstrap_and_add(tmp_path, add_role="exam")
    rejected = _facet_restructure()
    saved: list[tuple[str, dict[str, Any]]] = []

    def builder(context, n):
        if n <= 2:
            return _aligns_with_the_exam(context, n)
        # The other run: the first build's span-round answer, saved again under its key.
        key, result = saved[-1]
        repo.save_model_checkpoint(key, purpose="append_reconciliation", result=result)
        return rejected(context, n)

    client = _AppendClient(builder=builder)
    first = _append(root, repo, client, auto_apply=False)
    reject_items(root, first.proposal_id)
    saved.extend(_append_checkpoints(repo))
    record = _record_sent(root, repo, client, lambda: _append(root, repo, client, auto_apply=False))
    _check("append_rejected_match_then_gate_failure", record)


class _Raised:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def as_dict(self) -> dict[str, Any]:
        # No manifest hash to name: the run's own manifest is in the rows the build added.
        return {"raised": type(self.error).__name__, "message": str(self.error), "manifest_hash": None}


def test_append_a_call_that_fails_part_way(tmp_path, seeded_ids):
    """The provider fails on the span round: the first answer stays saved, both run rows fail, and the agent run
    records the usage the client reports by then."""

    root, repo = _bootstrap_and_add(tmp_path, add_role="primary_textbook")

    def fails(_context, _n):
        raise RuntimeError("the provider went away")

    client = _AppendClient(builder=_asks_for_a_span(fails))

    def run():
        try:
            return _append(root, repo, client)
        except RuntimeError as error:
            return _Raised(error)

    _check("append_fails_part_way", _record_sent(root, repo, client, run))
