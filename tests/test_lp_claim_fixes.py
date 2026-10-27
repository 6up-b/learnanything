"""LP-min (a): the four claim-defect fixes (spec_learned_parameters_v1 §3.0b item 1).

One successor (``CLAIM_FIXES_ALGORITHM_VERSION``) with one kill switch for all
four (``mastery.claim_fixes_enabled``):

1. a tutor gap declaration re-anchors its LO through
   ``reanchor_mastery_from_claim`` (the predecessor wrote the claim only, so it
   was inert on every LO sync had already materialized);
2. replay applies each claim at its own time, never the claims in force now;
3. a claim merged into a state with evidence (``apply_claim_evidence``) moves
   the mean only: it never lowers the variance (AD §5.5);
4. among equally specific claims the most recent wins, then the larger
   pseudo-count; the claimed level never breaks a tie.

Each defect has a pair: the ``_on`` test fails on the predecessor's code (the
stage record runs them with the fixes forced off), and the ``_off`` test pins
that the switch, or a version below the tag, keeps the predecessor exactly.
"""

from __future__ import annotations

from datetime import timedelta
import re
import sqlite3

import pytest

from learnloop.algorithm_versions import (
    CLAIM_FIXES_ALGORITHM_VERSION,
    CLAIM_FIXES_VERSIONS,
    LATEST_ALGORITHM_VERSION,
    READING_PATH_PLAN_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.clock import FrozenClock
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import MasteryState, Repository
from learnloop.learner.mastery import (
    apply_claim_evidence,
    claim_fixes_live,
    covering_learner_claim,
    logit,
    reanchor_mastery_from_claim,
)
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.tutor.ai_contracts import PromotionAnalysis
from learnloop.tutor.promotions import promote_tutor_question
from learnloop.vault.loader import load_vault
from learnloop.vault.repository import open_vault_repository

from tests.helpers import NOW, append_config_toml, create_placement_vault, set_algorithm_version
from tests.owner_vaults import owner_vault, working_vault_params
from tests.test_assumed_known import _answer
from tests.test_tutor_promotion_service import _AnalysisClient, _insert_event

TAG = CLAIM_FIXES_ALGORITHM_VERSION
#: The predecessor as the upgrade names it (one constant; the landing renumbers).
PREDECESSOR = SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1]
OFF = "[mastery]\nclaim_fixes_enabled = false\n"
LO = "lo_svd_definition"
ITEM = "pi_svd_define_001"


def _iso(minutes: float) -> str:
    return (NOW + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def _vault(tmp_path, name="vault", *, version=TAG, toml=None):
    paths = create_placement_vault(tmp_path / name, version=version)
    if toml:
        append_config_toml(paths.root, toml)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return paths, vault, repository


def _claim(repository, *, minutes, level, pseudo_count=2.0, source="manual_cli", scope_type="learning_object",
           scope_id=LO, claim_id=None):
    payload = {
        "claim_type": "self_rating", "scope_type": scope_type, "scope_id": scope_id,
        "evidence_family": "recall", "claimed_level": level, "prior_pseudo_count": pseudo_count,
        "source": source, "created_at": _iso(minutes),
    }
    if claim_id is not None:
        payload["id"] = claim_id
    return repository.insert_learner_claim(payload)


def _live_reanchoring_claim(vault, repository, *, minutes, level, pseudo_count=2.0, source="learner_report"):
    """A claim written and re-anchored live, as a too-easy report does."""

    _claim(repository, minutes=minutes, level=level, pseudo_count=pseudo_count, source=source)
    return reanchor_mastery_from_claim(
        vault, repository, LO, claimed_level=level, prior_pseudo_count=pseudo_count, now_iso=_iso(minutes),
    )


def _mastery(repository, lo=LO) -> tuple[float, float, int]:
    state = repository.mastery_state(lo)
    assert state is not None
    return (state.logit_mean, state.logit_variance, state.evidence_count)


def _gap(root, repository, event_id="ev_gap"):
    _insert_event(repository, event_id)
    client = _AnalysisClient(PromotionAnalysis(attributed_facets=["recall"], question_nature="mechanism"))
    return promote_tutor_question(root, client, event_id=event_id, intent="gap", clock=FrozenClock(NOW + timedelta(minutes=30)))


def _state(mean, variance, evidence=3):
    return MasteryState(
        learning_object_id=LO, logit_mean=mean, logit_variance=variance, evidence_count=evidence,
        last_evidence_at=None, algorithm_version=TAG, updated_at=_iso(0),
    )


# ── the successor ────────────────────────────────────────────────────────────


def test_the_successor_is_one_constant_after_its_predecessor():
    from learnloop.claim_fixes_upgrade import PREDECESSOR as UPGRADE_PREDECESSOR
    from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, defaults_fingerprint_for_version

    # Rebuild equivalence's mvp-0.34, Reader CA2's mvp-0.35 and the kept replaced claims' mvp-0.36 (the latest) landed after it and keep it.
    assert TAG == SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(PREDECESSOR) + 1]
    assert LATEST_ALGORITHM_VERSION == SUCCESSOR_CHAIN[-1] == "mvp-0.36"
    assert UPGRADE_PREDECESSOR == PREDECESSOR == READING_PATH_PLAN_ALGORITHM_VERSION == "mvp-0.32"
    # Built as mvp-0.32 beside RW7b's successor; RW7b landed first, so the landing renumbered it.
    assert TAG == "mvp-0.33"
    assert CLAIM_FIXES_VERSIONS == frozenset({TAG, "mvp-0.34", "mvp-0.35", LATEST_ALGORITHM_VERSION})
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[TAG] == defaults_fingerprint_for_version(TAG)


def test_one_switch_on_by_default_classified_and_gated_by_the_tag():
    from learnloop.config.schema import MasteryConfig
    from learnloop.params import parameter_registry as registry

    assert MasteryConfig().claim_fixes_enabled is True
    rule = registry.classify_config_path("mastery.claim_fixes_enabled")
    assert rule is not None
    config = type("C", (), {"algorithms": type("A", (), {"algorithm_version": TAG})(), "mastery": MasteryConfig()})()
    vault = type("V", (), {"config": config})()
    assert claim_fixes_live(vault)
    config.algorithms.algorithm_version = PREDECESSOR
    assert not claim_fixes_live(vault)
    config.algorithms.algorithm_version = TAG
    config.mastery = MasteryConfig(claim_fixes_enabled=False)
    assert not claim_fixes_live(vault)


# ── defect 1: a gap declaration re-anchors ───────────────────────────────────


def test_defect1_on_a_gap_declaration_reanchors_a_materialized_lo(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    cold = _mastery(repository)
    assert cold[2] == 0 and cold[0] == 0.0  # sync materialized the row before any claim

    result = _gap(paths.root, repository)

    assert result["learner_claim_id"] is not None
    config = vault.config
    mean, variance, evidence = _mastery(repository)
    assert mean == pytest.approx(logit(config.tutor_promotion.gap_claim_level))
    # Review F4: the claim moves the mean only; it never makes the cold row
    # more certain (the predecessor's seed would set max(1/pc, 2.0) < 3.0).
    assert variance == cold[1] == config.mastery.cold_start_prior_logit_variance
    assert evidence == 0


def test_defect1_on_a_gap_on_a_practised_lo_moves_the_mean_down_and_keeps_the_variance(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    _answer(vault, repository, ITEM, 4.0, minutes=5)
    before = _mastery(repository)
    assert before[2] > 0

    _gap(paths.root, repository)

    mean, variance, evidence = _mastery(repository)
    assert mean < before[0]  # toward the low gap level
    assert variance == before[1]  # defect 3: a claim never shrinks a variance
    assert evidence == before[2]


@pytest.mark.parametrize("variant", ["switch_off", "below_tag"])
def test_defect1_off_a_gap_declaration_writes_the_claim_only(tmp_path, variant):
    paths, _vault_, repository = _vault(
        tmp_path, version=PREDECESSOR if variant == "below_tag" else TAG, toml=OFF if variant == "switch_off" else None,
    )
    cold = _mastery(repository)

    result = _gap(paths.root, repository)

    assert result["learner_claim_id"] is not None
    assert _mastery(repository) == cold  # the predecessor's defect: inert on an existing row


# ── defect 2: replay applies claims at their own time ────────────────────────
#
# A one-attempt history replays to the live state exactly (the oracle the tests
# below use); a longer one differs from live for reasons outside claims, so the
# order of claims and attempts there is read from the replay itself.


def _rebuild(paths):
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    rebuild_all_derived_state(vault, repository, clock=FrozenClock(NOW + timedelta(hours=1)))
    return repository


def _history(vault, repository):
    """Two attempts, a too-easy report between them, a manual claim after both."""

    _answer(vault, repository, ITEM, 4.0, minutes=5)
    _live_reanchoring_claim(vault, repository, minutes=10, level=0.9)
    _answer(vault, repository, ITEM, 1.0, minutes=15)
    _claim(repository, minutes=20, level=0.05, pseudo_count=4.0)  # later; seeds nothing earlier


def test_defect2_on_the_seed_never_reads_a_later_claim(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    _answer(vault, repository, ITEM, 4.0, minutes=5)
    live = _mastery(repository)
    _claim(repository, minutes=20, level=0.05, pseudo_count=4.0)  # inert live: the row exists

    assert _mastery(_rebuild(paths)) == live


def test_defect2_on_a_claim_after_the_last_attempt_still_reanchors_in_replay(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    _answer(vault, repository, ITEM, 4.0, minutes=5)
    _live_reanchoring_claim(vault, repository, minutes=10, level=0.2)
    live = _mastery(repository)

    assert _mastery(_rebuild(paths)) == live


def test_defect2_on_a_claim_between_attempts_reanchors_between_them(tmp_path, monkeypatch):
    import learnloop.learner.mastery as mastery

    paths, vault, repository = _vault(tmp_path)
    _history(vault, repository)
    seen: list[tuple[str, int]] = []
    original = mastery.reanchor_mastery_from_claim

    def spy(vault_, repository_, learning_object_id, **kwargs):
        state = repository_.mastery_state(learning_object_id)
        seen.append((kwargs["now_iso"], state.evidence_count if state is not None else -1))
        return original(vault_, repository_, learning_object_id, **kwargs)

    monkeypatch.setattr(mastery, "reanchor_mastery_from_claim", spy)
    _rebuild(paths)

    # The too-easy report re-anchors once, at its own time, after the first
    # attempt and before the second; the manual claim (not a re-anchoring
    # source) never does, and seeds nothing because it came after the first.
    assert seen == [(_iso(10), 1)]


@pytest.mark.parametrize("variant", ["switch_off", "below_tag"])
def test_defect2_off_replay_seeds_from_the_claims_in_force_now(tmp_path, variant):
    paths, vault, repository = _vault(
        tmp_path, version=PREDECESSOR if variant == "below_tag" else TAG, toml=OFF if variant == "switch_off" else None,
    )
    _answer(vault, repository, ITEM, 4.0, minutes=5)
    live = _mastery(repository)
    _claim(repository, minutes=20, level=0.05, pseudo_count=4.0)

    rebuilt = _mastery(_rebuild(paths))

    # The predecessor's defect: a claim made after the attempt seeds its prior.
    assert rebuilt[0] < live[0]


# ── defect 3: a warm merge keeps a variance floor ────────────────────────────


def test_defect3_apply_claim_evidence_mean_only_never_lowers_the_variance():
    state = _state(1.0, 0.4)
    merged = apply_claim_evidence(state, claimed_level=0.2, prior_pseudo_count=2.0, now_iso=_iso(1), mean_only=True)
    plain = apply_claim_evidence(state, claimed_level=0.2, prior_pseudo_count=2.0, now_iso=_iso(1))

    assert merged.logit_variance == state.logit_variance
    assert merged.logit_mean == plain.logit_mean < state.logit_mean  # the same precision-weighted mean move
    assert plain.logit_variance < state.logit_variance  # the predecessor's defect


def test_defect3_on_a_warm_reanchor_keeps_the_variance(tmp_path):
    _paths, vault, repository = _vault(tmp_path)
    _answer(vault, repository, ITEM, 4.0, minutes=5)
    before = _mastery(repository)

    after = _live_reanchoring_claim(vault, repository, minutes=10, level=0.9, pseudo_count=4.0)

    assert after.logit_variance == before[1]
    assert after.logit_mean > before[0]


@pytest.mark.parametrize("variant", ["switch_off", "below_tag"])
def test_defect3_off_a_warm_reanchor_shrinks_the_variance(tmp_path, variant):
    _paths, vault, repository = _vault(
        tmp_path, version=PREDECESSOR if variant == "below_tag" else TAG, toml=OFF if variant == "switch_off" else None,
    )
    _answer(vault, repository, ITEM, 4.0, minutes=5)
    before = _mastery(repository)

    after = _live_reanchoring_claim(vault, repository, minutes=10, level=0.9, pseudo_count=4.0)

    assert after.logit_variance < before[1]


# ── defect 4: ties by recency, then pseudo-count, never by level ─────────────


def _tied_claims(repository):
    # Same specificity. The older claim has the larger pseudo-count AND the higher level.
    _claim(repository, minutes=1, level=0.9, pseudo_count=4.0, claim_id="claim_old")
    _claim(repository, minutes=2, level=0.3, pseudo_count=2.0, claim_id="claim_new")
    # Same instant and pseudo-count, different levels: only the id may decide.
    _claim(repository, minutes=0, level=0.2, pseudo_count=1.0, scope_type="global", scope_id=None, claim_id="g_z")
    _claim(repository, minutes=0, level=0.95, pseudo_count=1.0, scope_type="global", scope_id=None, claim_id="g_a")


def test_defect4_on_the_most_recent_claim_wins_then_pseudo_count_never_level(tmp_path):
    _paths, vault, repository = _vault(tmp_path)
    _tied_claims(repository)
    assert covering_learner_claim(vault, repository, LO)["id"] == "claim_new"
    # lo_diag has only the global claims: recency and pseudo-count tie, the level is ignored.
    assert covering_learner_claim(vault, repository, "lo_diag")["id"] == "g_z"
    # Recency before pseudo-count; pseudo-count before the id.
    _claim(repository, minutes=3, level=0.5, pseudo_count=1.0, claim_id="claim_a_newest_small")
    _claim(repository, minutes=3, level=0.5, pseudo_count=3.0, claim_id="claim_0_newest_large")
    assert covering_learner_claim(vault, repository, LO)["id"] == "claim_0_newest_large"


@pytest.mark.parametrize("variant", ["switch_off", "below_tag"])
def test_defect4_off_the_predecessor_prefers_pseudo_count_then_the_higher_level(tmp_path, variant):
    _paths, vault, repository = _vault(
        tmp_path, version=PREDECESSOR if variant == "below_tag" else TAG, toml=OFF if variant == "switch_off" else None,
    )
    _tied_claims(repository)
    assert covering_learner_claim(vault, repository, LO)["id"] == "claim_old"
    assert covering_learner_claim(vault, repository, "lo_diag")["id"] == "g_a"


# ── the kill switch is the predecessor exactly ───────────────────────────────


def _everything(paths, vault, repository):
    _tied_claims(repository)
    _history(vault, repository)
    _gap(paths.root, repository)
    _answer(vault, repository, "pi_diag_easy", 3.0, minutes=40)


def _mastery_rows(path):
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("SELECT * FROM learning_object_mastery ORDER BY learning_object_id").fetchall()
    # The version label is the only column that names the tag.
    return [tuple((key, row[key]) for key in row.keys() if key != "algorithm_version") for row in rows]


def test_off_is_the_predecessor_byte_for_byte_live_and_rebuilt(tmp_path):
    base_paths, base_vault, base_repo = _vault(tmp_path, "base", version=PREDECESSOR)
    off_paths, off_vault, off_repo = _vault(tmp_path, "off", version=TAG, toml=OFF)
    _everything(base_paths, base_vault, base_repo)
    _everything(off_paths, off_vault, off_repo)
    assert _mastery_rows(off_paths.sqlite_path) == _mastery_rows(base_paths.sqlite_path)

    _rebuild(base_paths)
    _rebuild(off_paths)
    assert _mastery_rows(off_paths.sqlite_path) == _mastery_rows(base_paths.sqlite_path)

    on_paths, on_vault, on_repo = _vault(tmp_path, "on", version=TAG)
    _everything(on_paths, on_vault, on_repo)
    assert _mastery_rows(on_paths.sqlite_path) != _mastery_rows(base_paths.sqlite_path)


FIXTURE = "fixtures/mvp017_route_check_replay"


def _fixture_copy(tmp_path, name, *, version, toml=None):
    from pathlib import Path

    source = Path(__file__).resolve().parents[1] / FIXTURE
    root = tmp_path / name
    copy_tree_with_databases(source, root)
    set_algorithm_version(type("Paths", (), {"root": root})(), version)
    if toml:
        append_config_toml(root, toml)
    return root


def _claims_on_fixture(root):
    repository = open_vault_repository(root, root / "state.sqlite")
    vault = load_vault(root)
    attempts = repository.list_all_attempts()
    assert attempts, "the fixture replays attempts"
    first = min(attempts, key=lambda row: row["created_at"])
    lo = str(first["learning_object_id"])
    stamps = sorted(str(row["created_at"]) for row in attempts if row["learning_object_id"] == lo)
    # One claim before the first attempt, one re-anchoring claim between, one after all.
    for index, (stamp, level, source) in enumerate(
        [(stamps[0], 0.7, "init_wizard"), (stamps[-1], 0.3, "learner_report"), ("2099-01-01T00:00:00Z", 0.9, "learner_report")]
    ):
        created = stamp if index != 1 else stamps[len(stamps) // 2]
        repository.insert_learner_claim({
            "id": f"fx_claim_{index}", "claim_type": "self_rating",
            "scope_type": "global" if source == "init_wizard" else "learning_object",
            "scope_id": None if source == "init_wizard" else lo, "evidence_family": None,
            "claimed_level": level, "prior_pseudo_count": 2.0, "source": source, "created_at": created,
        })
    return vault, repository


def test_off_is_the_predecessor_on_a_tracked_fixture_copy(tmp_path):
    rows = {}
    for name, version, toml in (("base", PREDECESSOR, None), ("off", TAG, OFF), ("on", TAG, None)):
        root = _fixture_copy(tmp_path, name, version=version, toml=toml)
        vault, repository = _claims_on_fixture(root)
        rebuild_all_derived_state(vault, repository, clock=FrozenClock(NOW))
        rows[name] = _mastery_rows(root / "state.sqlite")
    assert rows["off"] == rows["base"]
    assert rows["on"] != rows["base"]  # the fixes move the claimed LOs only


def _switch_off_in_place(root):
    """The kill switch on a real vault's config, whose [mastery] table already exists (the landing's owner lane)."""

    path = root / "learnloop.toml"
    text = path.read_text(encoding="utf-8")
    if re.search(r"(?m)^\[mastery\]\s*$", text) is None:
        append_config_toml(root, OFF)
        return
    path.write_text(re.sub(r"(?m)^\[mastery\]\s*$", "[mastery]\nclaim_fixes_enabled = false", text, count=1), encoding="utf-8")
    assert load_vault(root).config.mastery.claim_fixes_enabled is False


@pytest.mark.parametrize("fixture", working_vault_params())
def test_owner_copies_off_is_the_predecessor_and_on_reports_the_mastery_deltas(tmp_path, fixture, capsys):
    """Owner lane (backup-API copies only): parity off, and the deltas on, printed for the stage record."""

    if not (owner_vault(fixture) / "state.sqlite").exists():
        pytest.skip(f"{fixture} copy absent")
    rows = {}
    for name, version, toml in (("base", PREDECESSOR, None), ("off", TAG, OFF), ("on", TAG, None)):
        root = tmp_path / name
        copy_tree_with_databases(owner_vault(fixture), root)
        set_algorithm_version(type("Paths", (), {"root": root})(), version)
        if toml:
            _switch_off_in_place(root)
        repository = open_vault_repository(root, root / "state.sqlite")
        vault = load_vault(root)
        rebuild_all_derived_state(vault, repository, clock=FrozenClock(NOW))
        rows[name] = {dict(row)["learning_object_id"]: dict(row) for row in _mastery_rows(root / "state.sqlite")}
    assert rows["off"] == rows["base"]
    deltas = {
        lo: (rows["on"][lo]["logit_mean"] - row["logit_mean"], rows["on"][lo]["logit_variance"] - row["logit_variance"])
        for lo, row in rows["base"].items()
        if lo in rows["on"] and (rows["on"][lo]["logit_mean"], rows["on"][lo]["logit_variance"])
        != (row["logit_mean"], row["logit_variance"])
    }
    print(f"{fixture}: {len(deltas)} of {len(rows['base'])} LOs move; {sorted(deltas.items())[:20]}")


# ── the upgrade ──────────────────────────────────────────────────────────────


def test_upgrade_from_the_predecessor_replays_claimed_los_and_through_the_chain(tmp_path):
    from typer.testing import CliRunner

    from learnloop.claim_fixes_upgrade import upgrade_to_claim_fixes
    from learnloop.cli.app import app

    direct, vault, repository = _vault(tmp_path, "direct", version=PREDECESSOR)
    _answer(vault, repository, ITEM, 4.0, minutes=5)
    _claim(repository, minutes=20, level=0.05, pseudo_count=4.0)  # later than the attempt
    live = _mastery(repository)
    result = upgrade_to_claim_fixes(direct.root)
    assert result.upgraded and (result.from_version, result.to_version) == (PREDECESSOR, TAG)
    assert any(LO in note for note in result.notes)
    assert load_vault(direct.root).config.algorithms.algorithm_version == TAG
    # The replay applied the claim at its own time: the earlier attempt keeps its seed.
    assert _mastery(Repository(direct.sqlite_path)) == pytest.approx(live, rel=1e-12, abs=1e-12)
    again = upgrade_to_claim_fixes(direct.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]

    chained = create_placement_vault(tmp_path / "chained", version="mvp-0.30")
    assert upgrade_to_claim_fixes(chained.root).upgraded
    assert load_vault(chained.root).config.algorithms.algorithm_version == TAG

    old = create_placement_vault(tmp_path / "old", version="mvp-0.8")
    refused = upgrade_to_claim_fixes(old.root)
    assert not refused.upgraded and load_vault(old.root).config.algorithms.algorithm_version == "mvp-0.8"

    cli = create_placement_vault(tmp_path / "cli", version=PREDECESSOR)
    # Its own step (the default target is the latest's, rebuild equivalence's, since its landing).
    invoked = CliRunner().invoke(app, ["upgrade", "--vault", str(cli.root), "--to", TAG])
    assert invoked.exit_code == 0, invoked.output
    assert f"{PREDECESSOR} -> {TAG}" in invoked.output
