"""Arc C deleted config fields nothing read; identities that hashed them must not move.

Arc C's contract (``docs/specs/refactor_strategy_v3.md`` §2.1, §2.5): a deletion changes nothing at a fixed input.
Some places hash a config section into an identity that is compared later: the synthesis manifest (the cache key
that lets a completed bootstrap or append run be reused) and a predictor's version hash (a forecast's version label,
a VOI receipt's dedupe key through the valuation's state hash, the eval harness's arm hashes). The digests below
were recorded by running the code at ``88607cb3fe`` (arc C's base) from a ``git archive`` extract on the same fixed
inputs (``docs/reviews/arcC-review-fixes.md`` §3): the default config, and ``LEGACY_TOML`` (an old config setting
every removed key). The Codex review's scenario is here too: a run completed before arc C is reused for the same
request after it.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from learnloop.ai.execution import content_key
from learnloop.ai.spend import SpendCaps
from learnloop.config.loader import load_config
from learnloop.config.schema import LearnLoopConfig
from learnloop.content.synthesis import source_append, source_set_synthesis
from learnloop.content.synthesis.source_append import append_source
from learnloop.content.synthesis.source_set_synthesis import create_study_map
from learnloop.field.predictors import create_predictor
from learnloop.ops.embedding_compare import CompareRequest, run_compare
from learnloop.placement.predictor import LiveMasteryPredictor
from tests.helpers import append_config_toml
from tests.pf_fakes import PFFake, seed_pf_vault
from tests.source_append_helpers import FakeAppendClient, _bootstrap_and_add
from tests.source_set_synthesis_helpers import _CLOCK, FakeSynthesisClient, _setup

#: An old ``learnloop.toml`` setting every key arc C removed, with non-default values where it can.
LEGACY_TOML = """\
[facet_identity]
merge_locked_facets = false
shortlist_top_k = 5

[locks]
facet_lock_mass = 3

[plan]
pre_questions = 5

[mastery.irt]
discrimination_min = 0.5
discrimination_max = 2.5

[recall_coverage.severity_examples.custom]
expected_error_type = "conceptual_error"
expected_severity_band = [0.1, 0.2]
target_error_type = "conceptual_error"

[error_impacts.recall_failure]
families = { recall = -0.3 }

[error_impacts.custom_impact]
lo_mastery_delta = -0.1

[ai]
agent_harness_opt_in = true

[codex]
provider = "sdk"
model = "gpt-5.5"
timeout_seconds = 200
"""

#: Recorded at 88607cb3fe: sha256 of the sorted, compact JSON of ``config.facet_identity.model_dump(mode="json")``,
#: the ``config`` entry of the facet-identity block both synthesis entries hash into their manifests.
BASE_FACET_IDENTITY_SHA256 = {
    "default": "a86a21e99129979f16c1c9a14ba3b040fb78ea18ec3c8ca81356f92ac4eccc91",
    "legacy": "736cb6a2089fe21d1b71528b75dca8950c2e038e0db0d75cca45b86c2d25fd93",
}
#: The default dump itself at 88607cb3fe (its digest is the one above): what a run cached before arc C carries.
BASE_FACET_IDENTITY_DUMP = {
    "attach_top_k": 4, "enabled": True, "max_calls": 24, "max_cost_usd": 0.5, "max_facets": 400,
    "max_group_size": 40, "max_pairs": 20000, "max_retries": 2, "max_total_tokens": 600000,
    "merge_locked_facets": True, "price_per_million_input": None, "price_per_million_output": None,
    "reword_confirm": True, "shortlist_top_k": 4,
}
#: Recorded at 88607cb3fe: ``LiveMasteryPredictor(...).version_hash`` and ``create_predictor(name,
#: config=config.mastery).version_hash`` (no mastery states, no item parameters).
BASE_VERSION_HASHES = {
    "default": {
        "live_mastery": "cf2f953ebde8596e5f0b90b0c836d8740ad55e0701a01f7d0fd45c498431479f",
        "lo_general": "6ebe01dffc5633e41eaae22fb2e93c7640782ab53d4e4258d49a213f626b3c48",
        "mastery_ekf": "257294998cc4abcaaeceef883bcf550f02171523baefe0ea8cea56e698e0bb35",
        "lo_general+composite": "fb014a375436e38b9ce93f671f2cf8dd838476b83f4fcc2ed5315fea01a9c7f1",
    },
    "legacy": {
        "live_mastery": "107300143852038d2579e92f3b33f55738c4eb0fe66361dbbd89bebb8e28ce3f",
        "lo_general": "4405086b93e548c3f8498c240a5f9e5038362cad1558692479b05bd890e7ad90",
        "mastery_ekf": "ebc2f528ee012224305742089ebd0d35dfb8cc836e185012bba2c7c7521646b7",
        "lo_general+composite": "f30ae1c4207bbaaf743ee6cb0c808fc6a36930eab52a8a7e3fdc123812012cc4",
    },
}
#: Recorded at 88607cb3fe: ``content_key(config.model_dump(mode="json"))``, a report manifest's ``config_hash``.
BASE_CONFIG_CONTENT_KEY = {
    "default": "beffb8c8dff11caaa683cf1ce557f3c5d3a575d841c83fbff64f6b3bd83109f7",
    "legacy": "5cbd4ee74e3f40c5f6bbe70b7317679f1cd5a146ce7e7a7cb0ab550933085549",
}


def _sha256(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _legacy_config(tmp_path: Path) -> LearnLoopConfig:
    path = tmp_path / "legacy.toml"
    path.write_text(LEGACY_TOML, encoding="utf-8")
    return load_config(path, load_environment=False)


def _configs(tmp_path: Path) -> dict[str, LearnLoopConfig]:
    return {"default": LearnLoopConfig(), "legacy": _legacy_config(tmp_path)}


def _capture_scope(monkeypatch, module) -> list[dict]:
    """Record the ``scope`` each ``build_manifest`` call in ``module`` hashes."""

    seen: list[dict] = []
    real = module.build_manifest

    def recording(vault, **kwargs):
        seen.append(copy.deepcopy(kwargs["scope"]))
        return real(vault, **kwargs)

    monkeypatch.setattr(module, "build_manifest", recording)
    return seen


def _as_before_arc_c(monkeypatch, module) -> None:
    """``module``'s next manifests as the code at 88607cb3fe built them: its facet-identity config dump."""

    real = module.build_manifest

    def before(vault, **kwargs):
        scope = copy.deepcopy(kwargs["scope"])
        scope["facet_identity"]["config"] = copy.deepcopy(BASE_FACET_IDENTITY_DUMP)
        return real(vault, **{**kwargs, "scope": scope})

    monkeypatch.setattr(module, "build_manifest", before)


def test_the_recorded_facet_identity_dump_is_the_recorded_digest():
    assert _sha256(BASE_FACET_IDENTITY_DUMP) == BASE_FACET_IDENTITY_SHA256["default"]


@pytest.mark.parametrize("case", ["default", "legacy"])
def test_bootstrap_manifest_hashes_the_facet_identity_config_as_before_arc_c(tmp_path, monkeypatch, case):
    root, repo = _setup(tmp_path, with_exam=False)
    if case == "legacy":
        append_config_toml(root, "[facet_identity]\nmerge_locked_facets = false\nshortlist_top_k = 5\n")
    seen = _capture_scope(monkeypatch, source_set_synthesis)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo, clock=_CLOCK)
    assert seen and _sha256(seen[0]["facet_identity"]["config"]) == BASE_FACET_IDENTITY_SHA256[case]


def test_append_manifest_hashes_the_facet_identity_config_as_before_arc_c(tmp_path, monkeypatch):
    root, repo = _bootstrap_and_add(tmp_path)
    seen = _capture_scope(monkeypatch, source_append)
    append_source(root, "set_la", client=FakeAppendClient(), new_revision_ids=["rev_alt"], repository=repo,
                  clock=_CLOCK, auto_apply=False)
    assert seen and _sha256(seen[0]["facet_identity"]["config"]) == BASE_FACET_IDENTITY_SHA256["default"]


def test_a_bootstrap_run_completed_before_arc_c_is_reused_for_the_same_request(tmp_path, monkeypatch):
    """The Codex review's finding 1: the same request after arc C must not start a new (paid) agent run."""

    root, repo = _setup(tmp_path, with_exam=False)
    client = FakeSynthesisClient()
    with monkeypatch.context() as patch:
        _as_before_arc_c(patch, source_set_synthesis)
        before = create_study_map(root, "set_la", client=client, brief={"a": 1}, repository=repo, clock=_CLOCK)
    assert not before.reused and before.proposal_id is not None
    calls = len(client.calls)

    after = create_study_map(root, "set_la", client=client, brief={"a": 1}, repository=repo, clock=_CLOCK)

    assert after.reused is True
    assert after.proposal_id == before.proposal_id
    assert after.manifest_hash == before.manifest_hash
    assert len(client.calls) == calls  # no new agent run


def test_an_append_run_completed_before_arc_c_is_reused_for_the_same_request(tmp_path, monkeypatch):
    root, repo = _bootstrap_and_add(tmp_path)
    client = FakeAppendClient()
    with monkeypatch.context() as patch:
        _as_before_arc_c(patch, source_append)
        before = append_source(root, "set_la", client=client, new_revision_ids=["rev_alt"], repository=repo,
                               clock=_CLOCK, auto_apply=False)
    assert not before.reused
    calls = len(client.calls)

    after = append_source(root, "set_la", client=client, new_revision_ids=["rev_alt"], repository=repo,
                          clock=_CLOCK, auto_apply=False)

    assert after.reused is True
    assert after.manifest_hash == before.manifest_hash
    assert len(client.calls) == calls


@pytest.mark.parametrize("case", ["default", "legacy"])
def test_predictor_version_hashes_are_the_ones_recorded_before_arc_c(tmp_path, case):
    config = _configs(tmp_path)[case]
    expected = BASE_VERSION_HASHES[case]
    repository = SimpleNamespace(mastery_states=lambda: {}, item_parameter_states=lambda: {})
    assert LiveMasteryPredictor(SimpleNamespace(config=config), repository).version_hash == expected["live_mastery"]
    for name in ("lo_general", "mastery_ekf", "lo_general+composite"):
        assert create_predictor(name, config=config.mastery).version_hash == expected[name], name


def _pre_arc_c_shape(dump: dict) -> dict:
    """A config dump as 88607cb3fe wrote it, for a config that sets none of the removed keys and defines none of
    the built-in error-impact or severity-example entries itself (written out independently of the fix)."""

    shaped = copy.deepcopy(dump)
    shaped["facet_identity"]["merge_locked_facets"] = True
    shaped["plan"]["pre_questions"] = 3
    shaped["mastery"]["irt"].update(discrimination_min=0.2, discrimination_max=3.0)
    shaped["ai"]["agent_harness_opt_in"] = False
    shaped["locks"] = {"facet_lock_mass": 2.0, "facet_surface_groups": 2}
    for key, impact in shaped["error_impacts"].items():
        impact["lo_mastery_delta"] = -0.05 if key in {"recall_failure", "scaffold_failure"} else 0.0
    for key, example in shaped["recall_coverage"]["severity_examples"].items():
        example["target_error_type"] = "arithmetic_slip" if key == "arithmetic_slip" else None
    return shaped


def test_the_pre_arc_c_shape_reproduces_the_recorded_default_digest():
    assert content_key(_pre_arc_c_shape(LearnLoopConfig().model_dump(mode="json"))) == (
        BASE_CONFIG_CONTENT_KEY["default"])


def test_the_config_identity_reproduces_both_recorded_digests(tmp_path):
    from learnloop.config.retired import identity_dump

    for case, config in _configs(tmp_path).items():
        assert content_key(identity_dump(config)) == BASE_CONFIG_CONTENT_KEY[case], case


def test_retired_fields_stay_off_the_models_and_out_of_every_other_dump(tmp_path):
    """The models keep a retired field only for identity dumps: never a field, never in a plain dump."""

    from learnloop.config import schema
    from learnloop.config.retired import RETIRED_FIELDS, KeepsRetiredFields

    for field in RETIRED_FIELDS:
        model = getattr(schema, field.model)
        assert issubclass(model, KeepsRetiredFields), field.model
        assert field.path[0] not in model.model_fields, field
    legacy = _legacy_config(tmp_path)
    plain = legacy.model_dump(mode="json")
    assert "merge_locked_facets" not in plain["facet_identity"]
    assert "pre_questions" not in plain["plan"]
    assert "lo_mastery_delta" not in plain["error_impacts"]["custom_impact"]
    assert not hasattr(legacy.ai, "agent_harness_opt_in")


def test_an_embedding_compare_report_is_named_as_before_arc_c(tmp_path):
    """The manifest's config hash names the report files: a rerun at a fixed input replaces its report."""

    vault, _, _paths = seed_pf_vault(tmp_path / "vault")
    clients = {role: PFFake("m") for role in ("skeleton", "freshness", "valid_alternative", "equivalence")}
    report = run_compare(vault, request=CompareRequest(suite="valid_alternative", output_dir=tmp_path / "out",
                                                       dry_run=True),
                         caps=SpendCaps(max_candidates=100, max_pairs=2000, max_calls=2000,
                                        max_total_tokens=10**9, max_estimated_usd=10**4),
                         price_per_million=2.0, clients=clients)
    assert report["manifest"]["config_hash"] == content_key(_pre_arc_c_shape(vault.config.model_dump(mode="json")))
