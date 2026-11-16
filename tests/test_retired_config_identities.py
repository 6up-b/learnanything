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
from learnloop.content.synthesis import source_set_synthesis
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
#: Config defaults added after 88607cb3fe, each on purpose (the step that added it is named). The whole-config
#: digests above hold arc C's deletions to their base; a new default is not a deletion, so it is taken out before
#: comparing. A report's whole-config ``config_hash`` (an embedding-compare report's file name) moves with each one,
#: as with any schema change; nothing that pays or scores compares it.
ADDED_SINCE_BASE: tuple[tuple[str, ...], ...] = (
    ("ingest", "budgets", "append_input_ceiling"),  # refactor K3.4: the append call's input ceiling
    ("facet_diagnostic", "canonical_belief_fixes"),  # arc D fixes part 1: the facet-belief successor's kill switch
    ("probe", "episode", "robust_gate_fixes"),  # K9.0b: the robust completion gate fixes' kill switch (mvp-0.59)
)


def _without_additions(dump: dict) -> dict:
    shaped = copy.deepcopy(dump)
    for *parents, name in ADDED_SINCE_BASE:
        node = shaped
        for key in parents:
            node = node[key]
        del node[name]  # a KeyError means the entry is stale: the default left or moved
    return shaped


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


def test_append_manifest_hashes_the_facet_identity_config_as_before_arc_c(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    result = append_source(root, "set_la", client=FakeAppendClient(), new_revision_ids=["rev_alt"], repository=repo,
                           clock=_CLOCK, auto_apply=False)
    scope = repo.synthesis_manifest_by_hash(result.manifest_hash)["scope"]
    assert _sha256(scope["facet_identity"]["config"]) == BASE_FACET_IDENTITY_SHA256["default"]


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


def test_an_append_run_completed_before_arc_c_is_reused_for_the_same_request(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    client = FakeAppendClient()
    before = append_source(root, "set_la", client=client, new_revision_ids=["rev_alt"], repository=repo,
                           clock=_CLOCK, auto_apply=False)
    # The manifest the code at 88607cb3fe wrote for this request: its facet-identity config dump, byte for byte.
    scope = repo.synthesis_manifest_by_hash(before.manifest_hash)["scope"]
    assert scope["facet_identity"]["config"] == BASE_FACET_IDENTITY_DUMP
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
    # The kill switches removed since, at their defaults (a section that lost its last field goes whole).
    shaped["diagnosis"].update(split_enabled=True, shadow=False)
    shaped["stuck_prompt"] = {"enabled": True}
    shaped["proof_check"] = {"enabled": True}
    shaped["required_method"] = {"enabled": True}
    shaped["hints"]["fold_follows_attach"] = True
    shaped["mastery"]["claim_fixes_enabled"] = True
    shaped["replay"] = {"ledger_bounded": True}
    shaped["practice"].update(attempt_keeps_content_state=True, reschedule_cold_after_assist=True)
    shaped["ask"]["cold_help_converts"] = True
    shaped["eligibility"] = {"enabled": True}
    shaped["teacher"]["weight"] = {"learned": True, "source": "pool"}
    shaped["adaptive_difficulty"]["generation_contract"] = True
    shaped["router"]["probe_tie_admission"] = True
    shaped["intent"].update(enabled=True, recall_targets_enabled=True)
    shaped["followups"]["enabled"] = True
    shaped["reading_paths"]["plan_uses_path"] = True
    shaped["curriculum"]["plan_uses_path"] = True
    shaped["teacher"]["probes"] = True
    shaped["router"]["lesson_suggestions"].update(enabled=True, in_objective=True)
    shaped["data_capture"]["serving"] = True
    return shaped


def test_the_pre_arc_c_shape_reproduces_the_recorded_default_digest():
    assert content_key(_without_additions(_pre_arc_c_shape(LearnLoopConfig().model_dump(mode="json")))) == (
        BASE_CONFIG_CONTENT_KEY["default"])


def test_the_config_identity_reproduces_both_recorded_digests(tmp_path):
    from learnloop.config.retired import identity_dump

    for case, config in _configs(tmp_path).items():
        assert content_key(_without_additions(identity_dump(config))) == BASE_CONFIG_CONTENT_KEY[case], case


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


# --- the kill switches the version floor passed (ADR-019) -------------------------------------------------------

#: A ``learnloop.toml`` setting every kill switch the first removal batch takes, each away from its default (the
#: predecessor's value). The owner's vaults set none of them; a vault that still does must load, and every identity
#: that dumped the section must keep the bytes it had while the switch existed.
SWITCHES_TOML = """\
[diagnosis]
split_enabled = false
shadow = true

[stuck_prompt]
enabled = false

[proof_check]
enabled = false

[required_method]
enabled = false

[hints]
fold_follows_attach = false

[mastery]
claim_fixes_enabled = false

[replay]
ledger_bounded = false

[practice]
attempt_keeps_content_state = false
reschedule_cold_after_assist = false

[ask]
cold_help_converts = false

[eligibility]
enabled = false

[teacher.weight]
learned = false
source = "parametric"
"""

#: Recorded at ``b4c8fbad98`` (the switches all present) from a ``git archive`` extract on the same inputs:
#: ``content_key(identity_dump(config))``, the sha256 of ``identity_dump(config.mastery)`` (C1's section), and the
#: two predictor version hashes that dump the mastery section.
SWITCHES_BASE_IDENTITIES = {
    "default": {
        "config": "31b289ba4099f83919ec2226a9349e8457d20b8d8b18ecce318cd6cc0057771c",
        "mastery": "3b21afb8e641f0b1970adc413ec64320ebcdfd2bfdfa432db91118ef3b3c8239",
        "live_mastery": "cf2f953ebde8596e5f0b90b0c836d8740ad55e0701a01f7d0fd45c498431479f",
        "lo_general": "6ebe01dffc5633e41eaae22fb2e93c7640782ab53d4e4258d49a213f626b3c48",
    },
    "switched": {
        "config": "1f18b851de9635a025cb9adb50726302ffe7e605cc0b6432195125e60aed3162",
        "mastery": "df3572352b5d0f68c3ed12007910a56ebd5b40de248bd7fe9a063573a0cd280e",
        "live_mastery": "30ece97b76db29523d151958e3929b024ac871ab6844636fc7cb4878ec8fcfa5",
        "lo_general": "6ebe01dffc5633e41eaae22fb2e93c7640782ab53d4e4258d49a213f626b3c48",
    },
}


#: Config defaults added after ``b4c8fbad98``, each on purpose: taken out of the whole-config dump before it is
#: compared with the digests above, as ``ADDED_SINCE_BASE`` does for arc C's base. A new default is not a removal.
ADDED_SINCE_SWITCHES_BASE: tuple[tuple[str, ...], ...] = (
    ("probe", "episode", "robust_gate_fixes"),  # K9.0b: the robust completion gate fixes' kill switch (mvp-0.59)
)


def _without_additions_since_switches_base(dump: dict) -> dict:
    shaped = copy.deepcopy(dump)
    for *parents, name in ADDED_SINCE_SWITCHES_BASE:
        node = shaped
        for key in parents:
            node = node[key]
        del node[name]  # a KeyError means the entry is stale: the default left or moved
    return shaped


def _removed_switches() -> list:
    from learnloop.config.retired import RETIRED_FIELDS

    return [field for field in RETIRED_FIELDS if field.removed_by == "D7"]


@pytest.mark.parametrize("case", ["default", "switched"])
def test_a_config_setting_the_removed_switches_keeps_every_identity(tmp_path, case):
    from learnloop.config.retired import identity_dump

    path = tmp_path / "switches.toml"
    path.write_text(SWITCHES_TOML, encoding="utf-8")
    config = LearnLoopConfig() if case == "default" else load_config(path, load_environment=False)
    expected = SWITCHES_BASE_IDENTITIES[case]
    repository = SimpleNamespace(mastery_states=lambda: {}, item_parameter_states=lambda: {})
    assert content_key(_without_additions_since_switches_base(identity_dump(config))) == expected["config"]
    assert _sha256(identity_dump(config.mastery)) == expected["mastery"]
    assert LiveMasteryPredictor(SimpleNamespace(config=config), repository).version_hash == expected["live_mastery"]
    assert create_predictor("lo_general", config=config.mastery).version_hash == expected["lo_general"]


#: The third removal batch's switches (Today: the plan, the router frame, reading paths, intent, capture), each away
#: from its default, as :data:`SWITCHES_TOML` is for the first batch.
TODAY_SWITCHES_TOML = """\
[plan]
enabled = false

[router]
enabled = false
probe_tie_admission = false
restraint = false

[router.lesson_suggestions]
enabled = false
in_objective = false

[reading_paths]
plan_uses_path = false

[curriculum]
plan_uses_path = false

[followups]
enabled = false

[intent]
enabled = false
recall_targets_enabled = false

[data_capture]
serving = false

[teacher]
probes = false

[adaptive_difficulty]
generation_contract = false
"""

#: Recorded at ``250b0e16fe`` (the third batch's switches all present), on the same inputs: ``content_key`` of the
#: whole identity dump, and the sha256 of each section's identity dump that held one of the batch's switches.
TODAY_SWITCHES_BASE_IDENTITIES = {
    "default": {
        "config": "04d7f6544c6541a1e47b94a7d6496f0e1fff6d75b3120a08961f9487f7158e7a",
        "plan": "e0febd72d8f343654ab77cc5054eca899891de7f4c29481ed8d68ea3337af10e",
        "router": "f610b41929aa7427b602e8facf313f96f0663aef76f8f96ca1e818913af54b82",
        "reading_paths": "10f7e3d4eaada9d3c31e7266fc55808b0a00e445893a1a3006f00562fce74208",
        "curriculum": "262cde9cd36ef4da4ffd1c56f53bdd67febd840ffbc1506bf01a8ff65ab7f338",
        "followups": "425bbf3f8e249ebe9c408011a1b26c3d22429cdbb83a2b981bb4150caebd7571",
        "intent": "f3ffb5106671ed3dfba8728cf4f3895d020b4595e1855ca094ba621c606aeb84",
        "data_capture": "eebbd28351b9d7dd915087fee2093c0ed4e1491fa07ab71fe330c0bcfc4cc010",
        "teacher": "3d4d81b96a45c8cfa3e3d6a71af396b325a2af585e999dd519b4f5e2b00bb8a1",
        "adaptive_difficulty": "7ad0b3f5a78ef01e8b77a91ec01eadae19a8919854bf99c10ba2105fed2d0c62",
    },
    "switched": {
        "config": "a3c5b9d76325362d398311c6b573c3cdd470fdefaa247a602e2cb73fdf870e8d",
        "plan": "1a8796871b16c45c5a35ac85d9c86201b81c5e13805e53b60f077b1febbf22e2",
        "router": "0202fb6c79e51ac0d07ade597cc35d4fad457db3fb008a741e8f4ee63fcab1da",
        "reading_paths": "fdcc8d3751c9d1709822e25ea6b130fcf7afb3bfb441a80cb8b1993fc32baeec",
        "curriculum": "154b62f7d12996e37f331299e11e4f2032e505f6fe23daae8de3304bea895f13",
        "followups": "acb16896962663ae034bc5a3747bc7324566d0573bdb59d1c1c40eb0a24ceacd",
        "intent": "d0816e99d91d0c30fd2462960e649843e45b04dec8c6e4ec2b9afb837c0b7618",
        "data_capture": "147bbf5ae55da96726ea6e314ec10f214eec39855877a33950ff11d605bd576b",
        "teacher": "a93dfdbf1b1414834fed2248b5c857593ba1dd271fbbec3181d0c7e6d233c91a",
        "adaptive_difficulty": "b8037e36c98b9f5a9873ba2ead1a578cd838c22fa097487f11e7851eab8b1007",
    },
}


@pytest.mark.parametrize("case", ["default", "switched"])
def test_a_config_setting_todays_removed_switches_keeps_every_identity(tmp_path, case):
    from learnloop.config.retired import identity_dump

    path = tmp_path / "switches.toml"
    path.write_text(TODAY_SWITCHES_TOML, encoding="utf-8")
    config = LearnLoopConfig() if case == "default" else load_config(path, load_environment=False)
    expected = TODAY_SWITCHES_BASE_IDENTITIES[case]
    dump = identity_dump(config)
    assert content_key(dump) == expected["config"]
    for section, digest in expected.items():
        if section != "config":
            assert _sha256(dump[section]) == digest, section


def test_every_removed_switch_is_in_the_switches_config_away_from_its_default():
    import tomllib

    given = tomllib.loads(SWITCHES_TOML + "\n" + TODAY_SWITCHES_TOML)
    for field in _removed_switches():
        node = given
        for key in (*_section_of(field), *field.path):
            node = node[key]
        assert node != field.default, field


def _section_of(field) -> tuple[str, ...]:
    """The config path of the model a retired field lived on ("" for the root)."""

    from learnloop.config import schema

    def walk(model, prefix):
        if model.__name__ == field.model:
            yield prefix
        for name, info in model.model_fields.items():
            annotation = info.annotation
            if isinstance(annotation, type) and issubclass(annotation, schema.BaseModel):
                yield from walk(annotation, (*prefix, name))

    found = list(walk(schema.LearnLoopConfig, ()))
    assert len(found) == 1, (field.model, found)
    return found[0]


def test_a_vault_that_still_sets_a_removed_switch_loads_and_the_switch_reads_nothing(tmp_path):
    """The key is ignored, not refused: the vault opens, no model has the field, and only an identity dump shows the
    value the file set."""

    from learnloop.config.retired import identity_dump
    from learnloop.vault.loader import load_vault
    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path / "vault")
    append_config_toml(paths.root, SWITCHES_TOML + "\n" + TODAY_SWITCHES_TOML)
    config = load_vault(paths.root).config
    dump = identity_dump(config)
    for field in _removed_switches():
        model, node = config, dump
        for key in _section_of(field):
            model, node = getattr(model, key), node[key]
        assert field.path[0] not in type(model).model_fields, field
        for key in field.path:
            node = node[key]
        assert node != field.default, field


def test_the_lesson_suggestions_section_still_refuses_an_unknown_key_but_loads_its_retired_ones(tmp_path):
    """``[router.lesson_suggestions]`` refuses unknown keys (a typo there fails loudly). Its two retired kill switches
    are not unknown: a vault that still sets them loads, and only an identity dump shows what it set."""

    from pydantic import ValidationError

    from learnloop.config.retired import identity_dump
    from learnloop.config.schema import RouterLessonSuggestionsConfig

    section = RouterLessonSuggestionsConfig.model_validate({"enabled": False, "in_objective": False,
                                                            "ceiling_per_day": 2})
    assert section.model_dump() == {"ceiling_per_day": 2}
    assert identity_dump(section) == {"ceiling_per_day": 2, "enabled": False, "in_objective": False}
    with pytest.raises(ValidationError):
        RouterLessonSuggestionsConfig.model_validate({"ceiling_per_day": 2, "celing_per_day": 1})
    path = tmp_path / "learnloop.toml"
    path.write_text("[router.lesson_suggestions]\nenabled = false\nin_objective = false\n", encoding="utf-8")
    loaded = load_config(path, load_environment=False)
    assert loaded.router.lesson_suggestions.model_dump() == {"ceiling_per_day": 3}
