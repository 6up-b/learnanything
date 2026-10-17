"""RW4a's calls to the sources spec's find_sources (spec_reader_workbench_v1 §7.2; G19, G53).

* Every Reader call gets its policy from the caller context the server
  builds, never from an argument: the Reader context gives ``reading``, a
  workbench session bound to an item ``assisted_practice`` for that item, an
  open cold administration ``cold_attempt`` and nothing at all.
* With the service present, the Reader's ``assisted_practice`` scope is
  ``TutorSpanProvider``'s for the same item (the same extractions, the same
  exclusions), so no exercise, solution or item-linked passage is shown.
* No Reader surface ever receives ``authoring`` material; the policy, how it
  was derived and every expansion call are on the manifest.
* G53: with the service faked, the Reader's calls are the documented ones
  (``find_sources`` with intent ``explain`` under a ``reader`` caller); with
  it absent (``source_service.enabled = false``), the library ask is absent
  and refuses; and no Reader package defines a second ``find_sources``,
  ``compare_sources``, ``find_practice`` or ``value_candidates``.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from learnloop.reader import reader_intent as RI
from learnloop.source_retrieval.find_sources import SourceHits, scope_for
from learnloop.source_retrieval.tutor import tutor_scope
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers import library_ask as handler
from tests.library_ask_fixtures import ask_rows, build_library_vault, call, context, set_config

ROOT = Path(__file__).resolve().parents[1]
QUESTION = "eigenvalue solve subtract solution exercise"
NOW = "2026-10-17T10:00:00Z"


@pytest.fixture
def library(tmp_path):
    paths, repository, spans = build_library_vault(tmp_path / "vault")
    return paths, repository, spans


def _ask(ctx, **extra):
    return call(ctx, "reader.library_ask", {"query": QUESTION, "extractionId": "ext_text", "spanIds": ["t2"],
                                            "learningObjectIds": ["lo_matrices"], **extra})


def _bound_session(repository, item_id: str = "pi_eigen_1") -> str:
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO workbench_sessions (id, practice_item_id, stem_md, import_status, origin, entry, "
            "extraction_id, span_ids_json, source_visible, created_at, updated_at) "
            "VALUES ('wbs_1', ?, 'Solve it', 'bound', 'reader', 'work_through', 'ext_text', '[\"t6\"]', 1, ?, ?)",
            (item_id, NOW, NOW))
        connection.commit()
    return "wbs_1"


def test_the_reader_context_reads(library):
    paths, repository, _spans = library
    result = _ask(context(paths.root))
    assert result["policy"] == "reading"
    manifest = json.loads(ask_rows(repository)[0]["manifest_json"])
    assert manifest["main"]["policy"] == "reading" and manifest["main"]["policy_derived_from"]
    assert manifest["caller"] == {"kind": "reader", "ref": "ext_text", "context": None, "item_id": None,
                                  "policy": "reading", "derived_from": "reader caller with no item bound"}
    for record in manifest["expansions"]:
        assert record["manifest"]["policy"] == "reading"


def test_a_workbench_session_asks_as_its_items_practice(library):
    paths, repository, spans = library
    session = _bound_session(repository)
    result = _ask(context(paths.root), workbenchSessionId=session)
    assert result["policy"] == "assisted_practice"
    keys = {(hit["extractionId"], hit["spanId"]) for hit in result["hits"]}
    assert not keys & {("ext_text", span) for span in spans["exercises"] + spans["solutions"]}
    vault = load_vault(paths.root)
    item = vault.practice_items["pi_eigen_1"]
    reader = scope_for(vault, repository, policy="assisted_practice", scope="library",
                       learning_object_ids=["lo_matrices"], item=item)
    tutor = tutor_scope(vault, repository, context="practice", learning_object_ids=["lo_matrices"], item=item)
    assert set(reader.extractions) == set(tutor.extractions) and reader.excluded == tutor.excluded
    assert keys <= {key for key in keys if tutor.allows(*key)}


def test_a_cold_administration_retrieves_nothing(library, monkeypatch):
    paths, repository, _spans = library
    import learnloop.instructional.policy as policy

    session = _bound_session(repository)
    monkeypatch.setattr(policy, "cold_administration_open", lambda repo, item_id: item_id == "pi_eigen_1")
    result = _ask(context(paths.root), workbenchSessionId=session)
    assert result["policy"] == "cold_attempt" and result["hits"] == [] and result["expansions"] == []
    manifest = json.loads(ask_rows(repository)[0]["manifest_json"])
    assert manifest["expansions_skipped"] == "nothing is retrieved during a cold administration"


def test_no_reader_input_names_a_policy_and_none_is_authoring(library):
    paths, repository, _spans = library
    for model in (handler.LibraryAskInput, handler.LibraryCompareInput, handler.LibraryAskTutorInput):
        assert "policy" not in model.model_fields
    ctx = context(paths.root)
    _ask(ctx)
    _bound_session(repository)
    _ask(ctx, workbenchSessionId="wbs_1")
    for row in ask_rows(repository):
        manifest = json.loads(row["manifest_json"])
        policies = {manifest["policy"], manifest["main"]["policy"],
                    *(record["manifest"]["policy"] for record in manifest["expansions"] if "manifest" in record)}
        assert policies <= {"reading", "assisted_practice", "cold_attempt"}


def test_with_the_sources_spec_faked_the_readers_calls_are_the_documented_ones(library, monkeypatch):
    paths, _repository, _spans = library
    import learnloop.instructional.sources as service

    calls = []

    def fake_propose_sources(vault, repository, query, *, caller, intent="explain", **kwargs):
        calls.append({"caller": caller, "intent": intent, **kwargs})
        hits = SourceHits(intent=intent, policy="reading")
        hits.manifest = {"policy": "reading", "search": {"lists": ["keyword"]}, "returned": []}
        return hits

    monkeypatch.setattr(service, "propose_sources", fake_propose_sources)
    result = _ask(context(paths.root))
    assert result["hits"] == [] and result["status"] == "ok"
    assert [c["learning_object_ids"] for c in calls] == [["lo_matrices"], ["lo_vectors"], ["lo_inner"]]
    for c in calls:
        assert c["intent"] == "explain" and c["scope"] == "library" and c["verify"] is False
        assert c["caller"].kind == "reader" and c["caller"].ref == "ext_text" and "policy" not in c


def test_with_the_sources_spec_absent_the_library_ask_is_absent(library):
    paths, _repository, _spans = library
    set_config(paths, "source_service", enabled=False)
    ctx = context(paths.root)
    vault, _repo = ctx.require_vault()
    assert handler.prompt_contract_fields(vault) == {}
    assert not {"library_ask"} & {a.effect["kind"] for a in RI.available_actions(RI.Availability.from_config(vault.config))}
    with pytest.raises(SidecarError) as caught:
        _ask(ctx)
    assert caught.value.code == "library_ask_disabled"


def _defined_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def test_no_reader_package_defines_a_second_service_function():
    """Built once (G53, §20.9): the Reader consumes the sources spec's functions."""

    owned = {"find_sources", "find_sources_for_caller", "compare_sources", "find_practice", "value_candidates",
             "propose_sources", "propose_comparison"}
    files = sorted((ROOT / "src" / "learnloop" / "reader").rglob("*.py"))
    files += [ROOT / "src" / "learnloop_sidecar" / "handlers" / name
              for name in ("reader.py", "reader_intent.py", "library_ask.py", "workbench.py", "recap.py")]
    # The Reader's library answer, composed beside T6's library search.
    files += [ROOT / "src" / "learnloop" / "source_retrieval" / name for name in ("library_ask.py", "library.py")]
    found = {path.name: _defined_names(path) & owned for path in files}
    assert {name: names for name, names in found.items() if names} == {}
