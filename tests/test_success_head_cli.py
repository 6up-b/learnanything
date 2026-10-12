"""`learnloop eval success-head` and its content loader: read-only, aggregate-only."""
from contextlib import closing
from datetime import timedelta
import hashlib
import json
import sqlite3
from types import SimpleNamespace

import numpy as np
import pytest
from typer.testing import CliRunner

from learnloop.cli import app, probability_arms
from learnloop.clock import FrozenClock
from learnloop.config.loader import global_settings_path as ORIGINAL_SETTINGS_PATH
from learnloop.config.loader import load_dotenv as ORIGINAL_LOAD_DOTENV
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.embedding_vectors import put_vector
from learnloop.field.item_content import load_content_index
from learnloop.field.success_head import PREREGISTRATION, preregistration_hash
from learnloop.field.types import AttemptRow, ItemFeatures
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.embedding_recipes import EMBEDDING_RECIPES, EmbeddingRecipe
from learnloop.vault.loader import load_vault
from tests.helpers import NOW, create_basic_vault
from tests.test_facet_evidence_timeline import _attempt
from tests.test_km3_projections import build_blueprint_vault


ITEMS = ("pi_comp_a", "pi_comp_b", "pi_comp_a", "pi_integrated", "pi_comp_b", "pi_comp_a", "pi_integrated")


def _vector(record_id: str, text: str, dims: int = 64) -> np.ndarray:
    seed = int(hashlib.sha256(f"{record_id}|{text}".encode()).hexdigest()[:8], 16)
    return np.random.default_rng(seed).normal(size=dims)


def _store(paths, model, record_id, text, *, field="stem", recipe=EMBEDDING_RECIPES["item/stem"]):
    with closing(connect(paths.sqlite_path)) as connection, connection:
        put_vector(connection, record_kind="item", record_id=record_id, field=field,
                   content_hash=recipe.content_hash(text), model_id=model,
                   task_prefix="retrieval-document", vector=_vector(record_id, text))


@pytest.fixture
def seeded(tmp_path):
    paths = build_blueprint_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    for k, item in enumerate(ITEMS):
        _attempt(vault, repository, item, (4, 0, 2)[k % 3], clock=FrozenClock(NOW + timedelta(hours=k)))
    for item_id, item in vault.practice_items.items():
        _store(paths, vault.config.embedding.model, item_id, item.prompt)
    return paths, vault


def _forbid_models(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("success-head replay must not call a model or load secrets")

    # The LLM arm is router R0's V2 arm: its client seam too. Patched first,
    # with the module imported at the top of this file, so it never binds a
    # patched routing function at import time.
    monkeypatch.setattr(probability_arms, "ready_client_for_task", forbidden)
    monkeypatch.setattr(probability_arms, "load_machine_environment", forbidden)
    monkeypatch.setattr("learnloop.config.loader.load_dotenv", forbidden)
    monkeypatch.setattr("learnloop.config.loader.global_settings_path", forbidden)
    monkeypatch.setattr("learnloop.ai.client.make_ai_provider_client", forbidden)
    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task", forbidden)


def _enable_field_switches(root):
    """Both field switches on; ai.routing.llm_probability_llm stays unset (template Codex)."""
    config = root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    for old, new in (
        ("[field]\n", "[field]\nenabled = true\n"),
        ("llm_probability_enabled = false", "llm_probability_enabled = true"),
    ):
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    config.write_text(text, encoding="utf-8")


def _allow_environment(monkeypatch):
    """A paid step loads keys like `embeddings backfill` (isolated config dir)."""
    loaded = []

    def spy(path):
        loaded.append(path)
        return ORIGINAL_LOAD_DOTENV(path)

    monkeypatch.setattr("learnloop.config.loader.load_dotenv", spy)
    monkeypatch.setattr("learnloop.config.loader.global_settings_path", ORIGINAL_SETTINGS_PATH)
    return loaded


def _digest(paths):
    return hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest()


def _invoke(*args):
    return CliRunner().invoke(app, ["eval", "success-head", *args])


def _private_text(vault):
    return [*vault.practice_items, *(item.prompt for item in vault.practice_items.values())]


def test_dry_run_plans_coverage_without_calls_or_writes(seeded, monkeypatch, tmp_path):
    paths, vault = seeded
    _forbid_models(monkeypatch)
    before = _digest(paths)
    result = _invoke("--vault", str(paths.root), "--legacy-fallback", "current_content",
                     "--output", str(tmp_path / "out"), "--dry-run", "--json")
    assert result.exit_code == 0, result.output
    plan = json.loads(result.output)
    assert plan["status"] == "dry_run" and plan["calls"] == 0
    coverage = plan["content"]["by_revision_status"]["reconstructed_current"]
    assert coverage["attempts"] == len(ITEMS) and coverage["stem_vector"] == len(ITEMS)
    assert plan["unavailable"]["success_head+difficulty"].startswith("no solver_panel")
    # Phase 5a registers item/skeleton; this vault has no PF-b skeletons yet.
    assert plan["content"]["skeleton"].startswith("available")
    assert coverage["skeleton_vector"] == 0
    assert not (tmp_path / "out").exists()
    assert _digest(paths) == before
    assert not any(secret in result.output for secret in _private_text(vault))


def test_report_runs_all_arms_read_only_and_aggregate_only(seeded, monkeypatch, tmp_path):
    paths, vault = seeded
    _forbid_models(monkeypatch)
    before = _digest(paths)
    output = tmp_path / "out"
    runs = []
    for _ in range(2):
        result = _invoke("--vault", str(paths.root), "--legacy-fallback", "current_content",
                         "--output", str(output), "--bootstrap-samples", "20", "--json")
        assert result.exit_code == 0, result.output
        runs.append(json.loads(result.output))
    assert runs[0] == runs[1]
    report = runs[0]["evaluation"]
    arms = report["report1"]["arms"]
    assert set(arms) == {"base_rate_lo", "mastery_ekf", "lo_general", "tag_logistic",
                         "emb_ridge", "success_head"}
    assert arms["emb_ridge"]["overall"]["n"] == report["counts"]["ability_scored_attempts"] > 0
    t8 = report["analyses"]["t8"]
    # Seven attempts on three items. v3's percentile item bootstrap killed
    # here ([-0.173, -0.0001] at 20 resamples); v4's cluster-robust t interval
    # has 2 degrees of freedom (t = 4.30), reaches both 0 and delta, and
    # decides nothing. There is still no item floor.
    verdict = t8["primary"]["verdict"]
    assert (verdict["n"], verdict["item_clusters"], verdict["df"]) == (len(ITEMS), 3, 2)
    assert verdict["method"] == "cluster_robust_t_cr1"
    lower, upper = verdict["ci95"]
    assert lower < 0 and upper > .005
    assert (verdict["decision"], verdict["reason_code"]) == ("insufficient_data", "undecided")
    assert verdict["smallest_worthwhile_gain_nats_per_attempt"] == .005
    assert report["manifest"]["t8"]["smallest_worthwhile_gain_nats_per_attempt"] == .005
    assert report["manifest"]["t8"]["decision_interval"] == "cluster_robust_t_cr1"
    # Every interval in the report clusters on items, and the manifest says so (review F1).
    assert report["manifest"]["bootstrap"]["unit"] == "item"
    intervals, stack = [], [report]
    while stack:
        value = stack.pop()
        if isinstance(value, dict):
            intervals += [value] if "ci95" in value else []
            stack.extend(value.values())
        elif isinstance(value, list):
            stack.extend(value)
    assert intervals and all("clusters" in interval or "item_clusters" in interval
                             for interval in intervals)
    assert t8["preregistration"]["deviations"] == ["bootstrap_samples"]
    assert t8["preregistration"]["version"] == "t8-preregistration-v4"
    assert t8["preregistration"]["hash"] == report["manifest"]["t8"]["preregistration_hash"] == (
        preregistration_hash())
    assert t8["gated"]["success_head+difficulty"]["status"] == "unavailable"
    assert t8["descriptive"]["llm_zero_data"]["status"] == "unavailable"
    assert report["manifest"]["embedding_model"] == vault.config.embedding.model
    # Phase 5a registers item/skeleton, so the index carries both views; this
    # vault has no skeletons, so the skeleton block of every design row is zero.
    assert report["manifest"]["t8"]["views"] == ["stem", "skeleton"]
    files = [output / name.rsplit("/", 1)[-1] for name in runs[0]["reports"].values()]
    assert all(path.name.startswith("t8-success-head-") for path in files)
    markdown = next(path for path in files if path.suffix == ".md").read_text()
    assert "T8 pre-registered verdict" in markdown
    assert "**Decision: insufficient_data** (`undecided`)" in markdown
    assert "n = 7 common attempts in 3 item clusters" in markdown
    assert "δ in force: 0.005 nats per attempt (m = 0.0)" in markdown
    assert "cluster-robust t interval (CR1 over items, df = 2, t = 4.303)" in markdown
    for path in files:
        text = path.read_text()
        assert not any(secret in text for secret in _private_text(vault))
    assert _digest(paths) == before


def test_without_vectors_the_embedding_arms_abstain_and_say_so(tmp_path, monkeypatch):
    paths = build_blueprint_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    _attempt(vault, repository, "pi_comp_a", 4)
    _forbid_models(monkeypatch)
    result = _invoke("--vault", str(paths.root), "--legacy-fallback", "current_content",
                     "--output", str(tmp_path / "out"), "--bootstrap-samples", "5", "--json")
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)["evaluation"]
    assert report["report1"]["arms"]["emb_ridge"]["overall"]["n"] == 0
    assert report["t8_inputs"]["content"]["by_revision_status"]["reconstructed_current"]["stem_vector"] == 0
    assert report["analyses"]["t8"]["primary"]["verdict"]["decision"] == "insufficient_data"


def test_llm_cache_requires_switches_and_prepare_requires_cache(seeded, tmp_path):
    paths, _ = seeded
    result = _invoke("--vault", str(paths.root), "--prepare-llm", "--json")
    assert result.exit_code == 1 and "requires --llm-cache" in json.loads(result.output)["reason"]
    result = _invoke("--vault", str(paths.root), "--legacy-fallback", "current_content",
                     "--llm-cache", str(tmp_path / "cache"), "--json")
    assert result.exit_code == 1 and json.loads(result.output)["status"] == "disabled"


class _Transport:
    """An LLM judge transport seen through the real execute_structured_operation."""

    provider_name, provider_type, model = "codex", "codex_sdk", "fake-codex"

    def __init__(self, *capabilities, p=.6):
        self.capabilities, self.requests, self.p = set(capabilities), [], p

    def supports(self, capability):
        return capability in self.capabilities

    def complete(self, request):
        self.requests.append(request)
        return request.result_model(p_correct=self.p)


def _route_transport(monkeypatch, transport):
    monkeypatch.setattr("learnloop.cli.probability_arms.ready_client_for_task", lambda *a, **k: SimpleNamespace(
        client=transport, runtime=SimpleNamespace(ready=True)))


def _ledgered(paths):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM judgment_ledger WHERE task='llm_probability' AND judge='llm'").fetchone()[0]


def test_llm_prepare_dry_run_then_fake_codex_then_cache_only_replay(seeded, monkeypatch, tmp_path):
    """T8's zero-data arm is R0's llm_probability/v2/llm under T8's names (owner, 2026-10-12)."""
    from learnloop.ai.transport import ISOLATED_TURN, STRUCTURED_COMPLETION

    paths, vault = seeded
    _enable_field_switches(paths.root)
    cache = tmp_path / "cache"
    common = ("--vault", str(paths.root), "--legacy-fallback", "current_content",
              "--llm-cache", str(cache), "--output", str(tmp_path / "out"), "--json")
    _forbid_models(monkeypatch)
    before = _digest(paths)
    result = _invoke(*common, "--prepare-llm", "--dry-run", "--max-tokens", "0", "--max-cost-usd", "0")
    assert result.exit_code == 0, result.output
    plan = json.loads(result.output)
    llm = plan["llm"]
    assert llm["status"] == "dry_run" and llm["selection"] == ["v2/llm"]
    assert llm["aliases"] == {"llm_zero_data": "llm_probability/v2/llm",
                              "llm_zero_data:recalibrated": "llm_probability/v2/llm+recal"}
    judge = llm["judges"]["llm"]
    assert judge["billing"] == "subscription" and judge["charged"]["calls"] == 0
    assert judge["pending"] == judge["requests"] > 0
    assert _digest(paths) == before and not cache.exists()
    # A dry run without --prepare-llm plans the same work: nothing cached yet.
    status = json.loads(_invoke(*common, "--dry-run").output)["llm"]
    assert status["status"] == "dry_run" and status["judges"]["llm"]["pending"] == judge["pending"]

    transport = _Transport(STRUCTURED_COMPLETION, ISOLATED_TURN)
    _route_transport(monkeypatch, transport)
    environment = _allow_environment(monkeypatch)
    monkeypatch.setattr("learnloop.cli.probability_arms.load_machine_environment",
                        lambda root: environment.append(root))
    result = _invoke(*common, "--prepare-llm", "--bootstrap-samples", "10")
    assert result.exit_code == 0, result.output
    assert environment  # the paid step lets the app load its keys itself
    assert len(transport.requests) == judge["pending"]
    assert all(request.isolated for request in transport.requests)
    assert all("learner_answer" not in request.prompt and "An answer." not in request.prompt
               for request in transport.requests)
    report = json.loads(result.output)["evaluation"]
    assert report["offline_preparation"]["judges"]["llm"]["cost_basis"] == "estimated_only"
    arms = report["report1"]["arms"]
    assert {"llm_zero_data", "llm_zero_data:recalibrated"} <= set(arms)
    assert not any(name.startswith("llm_probability/") for name in arms)
    assert report["t8_inputs"]["llm_aliases"]["llm_zero_data"] == "llm_probability/v2/llm"
    assert "difficulty prior" in report["t8_inputs"]["llm_alias_note"]
    assert report["analyses"]["t8"]["descriptive"]["llm_zero_data"]["vs_emb_ridge"]["status"] == "computed"
    # The pre-registration is untouched: same version and hash.
    assert report["analyses"]["t8"]["preregistration"]["version"] == PREREGISTRATION["version"]
    assert report["analyses"]["t8"]["preregistration"]["hash"] == preregistration_hash()
    assert _ledgered(paths) == len(transport.requests)
    # Replay from the cache: no client, no writes.
    _forbid_models(monkeypatch)
    before = _digest(paths)
    result = _invoke(*common, "--bootstrap-samples", "10")
    assert result.exit_code == 0, result.output
    assert _digest(paths) == before


def test_the_t8_alias_and_the_v2_llm_arm_are_one_arm_paid_for_once(seeded, monkeypatch, tmp_path):
    """Owner decision 2026-10-12: comparable, and never paid for twice."""
    from learnloop.ai.transport import ISOLATED_TURN, STRUCTURED_COMPLETION

    paths, _ = seeded
    _enable_field_switches(paths.root)
    transport = _Transport(STRUCTURED_COMPLETION, ISOLATED_TURN)
    _route_transport(monkeypatch, transport)
    monkeypatch.setattr("learnloop.cli.probability_arms.load_machine_environment", lambda root: None)
    cache = tmp_path / "cache"
    field = CliRunner().invoke(app, [
        "eval", "--vault", str(paths.root), "--section", "field", "--legacy-fallback", "current_content",
        "--probability-arm", "v2/llm", "--llm-cache", str(cache), "--prepare-llm",
        "--output", str(tmp_path / "field"), "--bootstrap-samples", "5", "--json",
    ])
    assert field.exit_code == 0, field.output
    paid = len(transport.requests)
    assert paid > 0 and _ledgered(paths) == paid
    field_report = json.loads(field.output)["evaluation"]

    # T8 replays the field section's cache with no client.
    _forbid_models(monkeypatch)
    result = _invoke("--vault", str(paths.root), "--legacy-fallback", "current_content",
                     "--llm-cache", str(cache), "--output", str(tmp_path / "t8"),
                     "--bootstrap-samples", "5", "--json")
    assert result.exit_code == 0, result.output
    t8 = json.loads(result.output)["evaluation"]
    for alias, arm in (("llm_zero_data", "llm_probability/v2/llm"),
                       ("llm_zero_data:recalibrated", "llm_probability/v2/llm+recal")):
        assert t8["manifest"]["arm_hashes"][alias] == field_report["manifest"]["arm_hashes"][arm]
        assert t8["report1"]["arms"][alias]["overall"]["log_loss"]["mean"] == pytest.approx(
            field_report["report1"]["arms"][arm]["overall"]["log_loss"]["mean"])

    # A T8 preparation into a new cache recovers the ledgered verdicts: no new call.
    _route_transport(monkeypatch, transport)
    monkeypatch.setattr("learnloop.cli.probability_arms.load_machine_environment", lambda root: None)
    _allow_environment(monkeypatch)
    result = _invoke("--vault", str(paths.root), "--legacy-fallback", "current_content",
                     "--llm-cache", str(tmp_path / "other-cache"), "--prepare-llm",
                     "--output", str(tmp_path / "t8b"), "--bootstrap-samples", "5", "--json")
    assert result.exit_code == 0, result.output
    assert len(transport.requests) == paid and _ledgered(paths) == paid
    recovered = json.loads(result.output)["evaluation"]["offline_preparation"]["judges"]["llm"]
    assert recovered["recovered"] == recovered["requests"] and recovered["completed"] == 0


def test_a_transport_that_cannot_isolate_the_turn_is_refused_before_any_call(seeded, monkeypatch, tmp_path):
    from learnloop.ai.transport import STRUCTURED_COMPLETION

    paths, _ = seeded
    _enable_field_switches(paths.root)
    transport = _Transport(STRUCTURED_COMPLETION)
    _route_transport(monkeypatch, transport)
    _allow_environment(monkeypatch)
    monkeypatch.setattr("learnloop.cli.probability_arms.load_machine_environment", lambda root: None)
    result = _invoke("--vault", str(paths.root), "--legacy-fallback", "current_content",
                     "--llm-cache", str(tmp_path / "cache"), "--prepare-llm", "--json")
    assert result.exit_code == 1
    assert json.loads(result.output)["status"] == "provider_failed"
    assert not transport.requests
    assert _ledgered(paths) == 0


def _row(item_id, at, *, status, digest=None):
    return AttemptRow(f"a-{item_id}-{at}", ItemFeatures(item_id, "lo_svd", at), 1.0, 1.0,
                      revision_status=status, item_snapshot_hash=digest)


def _snapshot(paths, item, prompt):
    raw = item.model_copy(update={"prompt": prompt}).model_dump_json()
    digest = hashlib.sha256(raw.encode()).hexdigest()
    with closing(connect(paths.sqlite_path)) as connection, connection:
        connection.execute("INSERT OR IGNORE INTO practice_item_snapshots VALUES (?,?,?,?)",
                           (digest, item.id, raw, "2026-01-01T00:00:00Z"))
    return digest


def test_loader_uses_the_seen_text_and_never_substitutes_current_vectors(tmp_path, monkeypatch):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    item_id, item = next(iter(sorted(vault.practice_items.items())))
    model = vault.config.embedding.model
    _store(paths, model, item_id, item.prompt)
    same = _snapshot(paths, item, item.prompt)
    edited = _snapshot(paths, item, item.prompt + " (an earlier wording)")
    rows = [
        _row(item_id, "2026-01-02T00:00:00Z", status="exact", digest=same),
        _row(item_id, "2026-01-03T00:00:00Z", status="exact", digest=edited),
        _row(item_id, "2026-01-04T00:00:00Z", status="reconstructed_current"),
        _row(item_id, "2026-01-05T00:00:00Z", status="excluded"),
    ]
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        index, report = load_content_index(connection, vault, rows)
    exact, earlier, current, excluded = (index.get(row.features) for row in rows)
    assert exact.stem == item.prompt and "stem" in exact.vectors and exact.stem_source == "exact_snapshot"
    assert earlier.stem.endswith("(an earlier wording)") and not earlier.vectors
    assert current.stem_source == "current_content" and "stem" in current.vectors
    assert excluded.stem is None and not excluded.vectors
    assert len(exact.vectors["stem"]) == 32
    assert np.isclose(np.linalg.norm(exact.vectors["stem"]), 1.0)
    assert report["by_revision_status"]["exact"] == {
        "attempts": 2, "positive_mass": 2, "seen_text": 2, "skeleton_vector": 0, "stem_vector": 1}
    assert item.prompt not in json.dumps(report) and item_id not in json.dumps(report)


def test_loader_clears_ambiguous_identities_and_reads_skeletons_for_current_text(tmp_path, monkeypatch):
    from types import MappingProxyType

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    item_id, item = next(iter(sorted(vault.practice_items.items())))
    model = vault.config.embedding.model
    skeleton = EmbeddingRecipe("item", "skeleton", 1, "test skeleton",
                               lambda loaded: iter([(item_id, "steps: reduce, read rank")]))
    monkeypatch.setattr("learnloop.field.item_content.EMBEDDING_RECIPES",
                        MappingProxyType({**EMBEDDING_RECIPES, "item/skeleton": skeleton}))
    _store(paths, model, item_id, item.prompt)
    _store(paths, model, item_id, "steps: reduce, read rank", field="skeleton", recipe=skeleton)
    edited = _snapshot(paths, item, "Another wording")
    at = "2026-01-02T00:00:00Z"
    rows = [_row(item_id, "2026-01-01T00:00:00Z", status="reconstructed_current"),
            _row(item_id, at, status="reconstructed_current"),
            _row(item_id, at, status="exact", digest=edited)]
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        index, report = load_content_index(connection, vault, rows)
    first = index.get(rows[0].features)
    assert set(first.vectors) == {"stem", "skeleton"}
    assert index.views == ("stem", "skeleton")
    ambiguous = index.get(rows[1].features)
    assert ambiguous.stem is None and not ambiguous.vectors
    assert report["ambiguous_attempt_identities"] == 1


def test_loader_reads_phase_5a_skeletons_keyed_by_item_id(tmp_path):
    """Phase 5a merge: the real item/skeleton recipe yields each item's current
    PF-b skeleton keyed by item id, and its stored vector reaches the view."""
    from learnloop.db.stores.pf import insert_skeleton
    from learnloop.vault.hashes import skeleton_content_hash

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    item_id, item = next(iter(sorted(vault.practice_items.items())))
    model = vault.config.embedding.model
    recipe = EMBEDDING_RECIPES["item/skeleton"]
    with closing(connect(paths.sqlite_path)) as connection, connection:
        insert_skeleton(
            connection, skeleton_id="sk_test", subject_kind="practice_item", subject_id=item_id,
            content_hash=skeleton_content_hash(item.prompt, item.expected_answer),
            model_id="fake/skeleton", prompt_version="pf-skeleton-test", techniques=["reduce"],
            operations=[], checkpoints=[], skeleton_text="steps: reduce, read rank",
            created_at="2026-01-01T00:00:00Z",
        )
    assert [(r.record_id, r.text) for r in recipe.records(vault)] == [(item_id, "steps: reduce, read rank")]
    _store(paths, model, item_id, item.prompt)
    _store(paths, model, item_id, "steps: reduce, read rank", field="skeleton", recipe=recipe)
    rows = [_row(item_id, "2026-01-01T00:00:00Z", status="reconstructed_current")]
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        index, report = load_content_index(connection, vault, rows)
    assert set(index.get(rows[0].features).vectors) == {"stem", "skeleton"}
    assert index.views == ("stem", "skeleton") and report["skeleton"].startswith("available")


class FakeEmbedder:
    def __init__(self, model, dims):
        self.model_id, self.dims = model, dims
        self.modalities, self.max_input_tokens = frozenset({"text"}), 32_000
        self.texts = []

    def embed(self, inputs, task_prefix):
        self.texts.extend(inputs)
        return [_vector("x", text, self.dims).tolist() for text in inputs]


def _enable_embeddings(root):
    config = root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    for old, new in (("[embedding]\nenabled = false\nbackfill_enabled = false\n",
                      "[embedding]\nenabled = true\nbackfill_enabled = true\n"),
                     ("dimensions = 4096\n", "dimensions = 64\n")):
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    config.write_text(text, encoding="utf-8")


def test_seen_stem_backfill_embeds_retired_and_earlier_texts_only_explicitly(tmp_path, monkeypatch):
    paths = build_blueprint_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    for k, item in enumerate(ITEMS):
        _attempt(vault, repository, item, 4, clock=FrozenClock(NOW + timedelta(hours=k)))
    _enable_embeddings(paths.root)
    common = ("--vault", str(paths.root), "--legacy-fallback", "current_content", "--json")
    assert json.loads(_invoke(*common, "--backfill-seen-stems", "--prepare-llm",
                              "--llm-cache", str(tmp_path / "c")).output)["status"] == "invalid"
    _forbid_models(monkeypatch)
    before = _digest(paths)
    plan = json.loads(_invoke(*common, "--backfill-seen-stems", "--dry-run").output)
    assert plan["status"] == "dry_run" and plan["backfill"]["records_source"] == "explicit"
    assert plan["backfill"]["records"] == len(set(ITEMS)) == plan["backfill"]["pending"]
    assert _digest(paths) == before
    fake = FakeEmbedder(vault.config.embedding.model, 64)
    monkeypatch.setattr("learnloop.ops.embedding_backfill.ready_client_for_task",
                        lambda *a, **k: SimpleNamespace(client=fake, runtime=SimpleNamespace(ready=True)))
    environment = _allow_environment(monkeypatch)
    result = _invoke(*common, "--backfill-seen-stems")
    assert result.exit_code == 0, result.output
    assert environment
    assert json.loads(result.output)["backfill"]["embedded"] == len(set(ITEMS))
    assert sorted(fake.texts) == sorted(vault.practice_items[i].prompt for i in set(ITEMS))
    _forbid_models(monkeypatch)
    plan = json.loads(_invoke(*common, "--dry-run").output)
    assert plan["content"]["by_revision_status"]["reconstructed_current"]["stem_vector"] == len(ITEMS)


def test_seen_stem_records_follow_the_seen_revision_and_scored_rows(tmp_path):
    from learnloop.field.item_content import seen_stem_records

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    item_id, item = next(iter(sorted(vault.practice_items.items())))
    edited = _snapshot(paths, item, "An earlier wording")
    rows = [
        _row(item_id, "2026-01-02T00:00:00Z", status="exact", digest=edited),
        _row(item_id, "2026-01-03T00:00:00Z", status="reconstructed_current"),
        _row(item_id, "2026-01-04T00:00:00Z", status="excluded"),
        AttemptRow("zero", ItemFeatures("other", "lo", "2026-01-05T00:00:00Z"), 1., 0.,
                   revision_status="reconstructed_current"),
    ]
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        records = seen_stem_records(connection, vault, rows)
    assert sorted(r.text for r in records) == sorted(["An earlier wording", item.prompt])
    recipe = EMBEDDING_RECIPES["item/stem"]
    assert all(r.content_hash == recipe.content_hash(r.text) and r.record_id == item_id for r in records)


def test_explicit_backfill_records_must_be_canonical_recipe_texts():
    from learnloop.ops.embedding_backfill import _explicit_records
    from learnloop.vault.embedding_recipes import EmbeddingRecord, select_recipes

    recipe = EMBEDDING_RECIPES["item/stem"]
    good = EmbeddingRecord("item", "i", "stem", "text", recipe.content_hash("text"))
    assert _explicit_records([good, good], select_recipes(["item/stem"])) == [good]
    for bad in (EmbeddingRecord("item", "i", "stem", "text", "forged"),
                EmbeddingRecord("facet", "i", "definition", "text",
                                EMBEDDING_RECIPES["facet/definition"].content_hash("text")),
                EmbeddingRecord("item", "i", "stem", " ", recipe.content_hash(" "))):
        with pytest.raises(ValueError, match="canonical"):
            _explicit_records([bad], select_recipes(["item/stem"]))
