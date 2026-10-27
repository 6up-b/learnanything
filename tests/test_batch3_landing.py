"""Reader CA2 (mvp-0.35, migration 223) + Reader RW5d P1 (migration 224) + local retrieval P2, landed together.

CA2 built its successor as mvp-0.34 on mvp-0.32; the batch landing chained it after
rebuild equivalence's mvp-0.34 as **mvp-0.35**, with the same journalled activation
the claim fixes (mvp-0.33) and rebuild equivalence (mvp-0.34) use: one transaction,
the config's publication last, a journal (``predecessor``, ``target``) beside the
database while they disagree. One completion serves the chain: a journal naming
mvp-0.35 is completed by its upgrade; any other is handed down the chain.

The interactions the landing checks:

(i) RW5d's *show me* (the Ask rail's figure goal, the tutor's ``figure_goal``) is
    not an Ask question: it writes no question event and leaves CA2's question
    budgets as they were (RW5d spec §6.2: "sends the box's text as a figure goal
    instead of a question"; CA2's K5 cap counts questions).
(ii) CA2's ``earlier_opened_at`` is LIFECYCLE state rebuild never reads: an
    attempt submitted with an earlier opening carried into steps rebuilds exactly
    as the same submit without it (mastery and facets 0/0).
(iii) T1's offer is keyed by the action that asked: a grant given on a figure
    request never routes CA2's Ask to a metered provider, and a grant given on the
    Ask meters it, so CA2's per-attempt cap applies there.
(iv) Local retrieval P2 behind RW5d's grounding: with ``embedding.local.student``
    off (or no adopted student) the RW5d grounding retrieval returns exactly what
    P1's empty hook returned.
"""
from __future__ import annotations

import json
import multiprocessing
import os

import pytest
from typer.testing import CliRunner

from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    ONE_ASK_ALGORITHM_VERSION,
    ONE_ASK_VERSIONS,
    REPLAY_LEDGER_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.db.repositories import Repository
from learnloop.ops.vault_upgrade import rewrite_algorithm_version
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.test_hint_h2b_review import grader  # noqa: F401 - the blind grader fixture

TAG = ONE_ASK_ALGORITHM_VERSION
PREDECESSOR = REPLAY_LEDGER_ALGORITHM_VERSION


@pytest.fixture(autouse=True)
def _cli_process(monkeypatch):
    """This process as the CLI is: importing it installs the completion."""

    from learnloop import activation_journal
    from learnloop.cli.runtime import _complete_interrupted_activation

    monkeypatch.setattr(activation_journal, "_COMPLETER", _complete_interrupted_activation)


def _journal(paths):
    return paths.sqlite_path.with_name(paths.sqlite_path.name + ".claim-fixes-activation")


def _vault_at(tmp_path, name, version):
    from tests.helpers import create_placement_vault

    return create_placement_vault(tmp_path / name, version=version)


def _version(paths) -> str:
    return load_vault(paths.root).config.algorithms.algorithm_version


def _activated(paths, version=TAG) -> bool:
    import sqlite3
    from contextlib import closing

    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        return connection.execute(
            "SELECT 1 FROM derived_state_rebuilds WHERE scope = 'p0_projection_activation' AND algorithm_version = ?",
            (version,),
        ).fetchone() is not None


# -- the chain -------------------------------------------------------------------------------------


def test_mvp035_is_one_constant_after_mvp034_and_the_latest():
    from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, defaults_fingerprint_for_version
    from learnloop.one_ask_upgrade import PREDECESSOR as UPGRADE_PREDECESSOR

    # The kept replaced claims' mvp-0.36 follows it as the latest (and keeps it).
    assert SUCCESSOR_CHAIN[-4:] == ("mvp-0.33", "mvp-0.34", "mvp-0.35", "mvp-0.36")
    assert TAG == "mvp-0.35" and LATEST_ALGORITHM_VERSION == "mvp-0.36"
    assert UPGRADE_PREDECESSOR == PREDECESSOR == "mvp-0.34"
    assert ONE_ASK_VERSIONS == frozenset({TAG, "mvp-0.36"})
    for version in SUCCESSOR_CHAIN:
        assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[version] == defaults_fingerprint_for_version(version), version


@pytest.mark.parametrize("start", ["mvp-0.9", "mvp-0.27", "mvp-0.29", "mvp-0.30", "mvp-0.31", "mvp-0.32",
                                   "mvp-0.33", "mvp-0.34"])
def test_upgrade_to_mvp035_works_from_every_supported_version(tmp_path, start):
    from learnloop.cli import app

    paths = _vault_at(tmp_path, "v", start)
    result = CliRunner().invoke(app, ["upgrade", "--to", TAG, "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"{start} -> {TAG}" in result.output
    assert _version(paths) == TAG and _activated(paths) and not _journal(paths).exists()


def test_a_bare_upgrade_targets_the_latest_through_mvp035(tmp_path):
    from learnloop.cli import app

    # The latest is the kept replaced claims' mvp-0.36, chained through this tag.
    paths = _vault_at(tmp_path, "v", PREDECESSOR)
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"{PREDECESSOR} -> {LATEST_ALGORITHM_VERSION}" in result.output
    assert _version(paths) == LATEST_ALGORITHM_VERSION and _activated(paths)


# -- the journalled activation ----------------------------------------------------------------------


def _interrupted(tmp_path, name):
    """What a death between the publication and the commit leaves: the tag's
    label over the predecessor's database, with the journal naming both."""

    paths = _vault_at(tmp_path, name, PREDECESSOR)
    _journal(paths).write_text(json.dumps({"predecessor": PREDECESSOR, "target": TAG}), encoding="utf-8")
    rewrite_algorithm_version(paths.root / "learnloop.toml", PREDECESSOR, TAG, durable=True)
    assert not _activated(paths)
    return paths


def _die_after_publication(root):
    import learnloop.one_ask_upgrade as upgrade

    real = upgrade._publish_algorithm_version

    def publish_then_die(*args, **kwargs):
        real(*args, **kwargs)
        os._exit(17)  # no handler runs: the transaction never commits

    upgrade._publish_algorithm_version = publish_then_die
    upgrade.upgrade_to_one_ask(root)


def _open_vault_repository(paths):
    from learnloop.vault.repository import open_vault_repository

    open_vault_repository(paths.root, paths.sqlite_path)


def _vault_repository(paths):
    from learnloop.vault.repository import vault_repository

    vault_repository(VaultPaths(paths.root, load_vault(paths.root).config))


def _sidecar_start(paths):
    from learnloop_sidecar.context import SidecarContext

    SidecarContext().load(paths.root)


def _cli_command(paths):
    from learnloop.cli import app

    result = CliRunner().invoke(app, ["backfill-originals", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output


OPENERS = {
    "open_vault_repository": _open_vault_repository,
    "vault_repository": _vault_repository,
    "sidecar_start": _sidecar_start,
    "cli_command": _cli_command,
}


@pytest.mark.filterwarnings("ignore:This process .* is multi-threaded:DeprecationWarning")
def test_a_real_death_after_the_publication_is_journalled_and_the_next_cli_command_completes_it(tmp_path):
    from learnloop.one_ask_upgrade import upgrade_to_one_ask

    paths = _vault_at(tmp_path, "crashed", PREDECESSOR)
    process = multiprocessing.get_context("fork").Process(target=_die_after_publication, args=(paths.root,))
    process.start()
    process.join(60)
    assert process.exitcode == 17
    assert _version(paths) == TAG and _journal(paths).exists() and not _activated(paths)

    _cli_command(paths)

    assert not _journal(paths).exists() and _activated(paths)
    again = upgrade_to_one_ask(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


@pytest.mark.parametrize("opener", sorted(OPENERS))
def test_every_opener_that_may_write_completes_an_interrupted_mvp035_activation_first(tmp_path, opener):
    paths = _interrupted(tmp_path, "interrupted")
    OPENERS[opener](paths)
    assert not _journal(paths).exists() and _activated(paths) and _version(paths) == TAG


def test_without_a_completion_every_attach_refuses_with_the_mvp035_upgrade_message(tmp_path, monkeypatch):
    from learnloop import activation_journal

    paths = _interrupted(tmp_path, "interrupted")
    monkeypatch.setattr(activation_journal, "_COMPLETER", None)
    with pytest.raises(activation_journal.InterruptedActivation, match=f"learnloop upgrade --to {TAG}"):
        _open_vault_repository(paths)
    for attach in (lambda: Repository.attach(paths.sqlite_path, read_only=True), lambda: Repository(paths.sqlite_path)):
        with pytest.raises(activation_journal.InterruptedActivation, match=f"learnloop upgrade --to {TAG}"):
            attach()
    assert _journal(paths).exists() and not _activated(paths)


def test_the_upgrade_completes_its_own_journal(tmp_path):
    from learnloop.one_ask_upgrade import upgrade_to_one_ask

    paths = _interrupted(tmp_path, "interrupted")
    result = upgrade_to_one_ask(paths.root)
    assert result.upgraded and result.notes == [f"completed the interrupted activation of {TAG}"]
    assert not _journal(paths).exists() and _activated(paths)


def test_a_failure_after_the_rename_leaves_the_predecessor_and_no_journal(tmp_path, monkeypatch):
    import learnloop.one_ask_upgrade as upgrade

    paths = _vault_at(tmp_path, "failing", PREDECESSOR)
    real = upgrade._publish_algorithm_version

    def publish_then_fail(config_path, from_version, to_version, *, renamed=None):
        real(config_path, from_version, to_version, renamed=renamed)
        if to_version == TAG:
            raise OSError("the directory fsync failed")

    monkeypatch.setattr(upgrade, "_publish_algorithm_version", publish_then_fail)
    with pytest.raises(OSError):
        upgrade.upgrade_to_one_ask(paths.root)
    assert _version(paths) == PREDECESSOR and not _journal(paths).exists() and not _activated(paths)


def test_an_mvp034_journal_is_handed_to_its_own_upgrade_then_the_tag_activates(tmp_path):
    from learnloop.one_ask_upgrade import complete_interrupted_activation, upgrade_to_one_ask
    from tests.test_rbeq_pr2_landing import _interrupted as rbeq_interrupted

    paths, _live = rbeq_interrupted(tmp_path, "rbeq")
    assert _version(paths) == PREDECESSOR and _journal(paths).exists()
    assert complete_interrupted_activation(paths.root) == PREDECESSOR
    assert not _journal(paths).exists() and complete_interrupted_activation(paths.root) is None
    result = upgrade_to_one_ask(paths.root)
    assert result.upgraded and _version(paths) == TAG and not _journal(paths).exists()


def test_a_torn_journal_at_the_predecessor_is_removed_and_nothing_activates(tmp_path):
    from learnloop.one_ask_upgrade import complete_interrupted_activation

    paths = _vault_at(tmp_path, "torn", PREDECESSOR)
    _journal(paths).write_text('{"predecessor": "mvp-0.3', encoding="utf-8")
    assert complete_interrupted_activation(paths.root) is None
    assert not _journal(paths).exists() and _version(paths) == PREDECESSOR and not _activated(paths)


# -- (i) show me is not an Ask question --------------------------------------------------------------


def _question_events(repository) -> int:
    import sqlite3
    from contextlib import closing

    with closing(sqlite3.connect(repository.sqlite_path)) as connection:
        return connection.execute("SELECT COUNT(*) FROM question_events").fetchone()[0]


def test_i_a_figure_goal_from_the_ask_rail_or_the_tutor_never_spends_an_ask_question(tmp_path, monkeypatch):
    from learnloop.tutor.tutor_qa import question_usage
    from tests.figure_fixtures import AuthorFake, build, flagship
    from tests.test_figures_show_me import GOAL, READING_AT, FindFake, _ctx, _tutor_ask

    goal = "vary p and watch the mass left of zero follow it"
    paths, repository, ctx, _tutor, author, _find, answer = _tutor_ask(tmp_path, monkeypatch, figure_goal=goal)
    rewrite_algorithm_version(paths.root / "learnloop.toml", load_vault(paths.root).config.algorithms.algorithm_version,
                              TAG)  # CA2's successor, its panel on (the default)
    ctx.load(paths.root)
    vault = load_vault(paths.root)
    assert vault.config.algorithms.algorithm_version == TAG and vault.config.ask.panel_enabled
    asked = _question_events(repository)
    assert asked == 1
    budgets = {context: question_usage(vault, repository, context=context, practice_item_id="pi_x",
                                       session_id="sess_x", submission_id="k", note_id="note_x")
               for context in ("practice", "library")}

    # The tutor's figure goal, pressed: a figure request, not a question.
    build(ctx, {"origin": "tutor", "goalText": goal, "offerRef": answer["eventId"],
                "readingAt": {"extractionId": READING_AT["extractionId"], "spanId": "p6"}}, rpc="figure.request")
    # The Ask rail's box sent as *show me* (alt+Enter).
    rail = _ctx(paths, author=AuthorFake([flagship(kind="illustrative")]), find=FindFake([]))
    build(rail, {"goalText": GOAL, "readingAt": READING_AT, "origin": "show_me"}, rpc="figure.request")

    assert _question_events(repository) == asked
    after = {context: question_usage(vault, repository, context=context, practice_item_id="pi_x",
                                     session_id="sess_x", submission_id="k", note_id="note_x")
             for context in ("practice", "library")}
    assert after == budgets


# -- (ii) CA2's earlier opening and rebuild equivalence ---------------------------------------------


def _workbench_submit_shadow(tmp_path, *, opened: bool):
    from learnloop.substrate.shadow_rebuild import shadow_rebuild
    from tests.hint_fakes import ITEM as CDF_ITEM
    from tests.test_reader_ca2_fix_orchestrator import _attempt, _call, _draft, _open, _row, _step, _steps_sidecar

    paths, ctx, session = _steps_sidecar(tmp_path)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG
    _draft(ctx, session, CDF_ITEM, "kA", **({"earlierOpened": True} if opened else {}))
    view = _open(ctx, session)
    assert bool(_row(paths, view["sessionId"])["earlier_opened_at"]) is opened
    _step(ctx, view["sessionId"])
    attempt = _call(ctx, "workbench.submit", {"sessionId": view["sessionId"], "practiceSessionId": session})["attempt"]
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == (1 if opened else 0)
    result = shadow_rebuild(load_vault(paths.root))
    assert result.live_database_unchanged
    return result.learner_state_diff


def _due_seconds(change) -> float:
    from datetime import datetime

    before, after = (datetime.fromisoformat(change[side]["due_at"].replace("Z", "+00:00")) for side in ("before", "after"))
    return abs((before - after).total_seconds())


def test_ii_an_earlier_opening_carried_into_steps_adds_nothing_to_rebuild(tmp_path, grader):
    """The opening is LIFECYCLE state replay never reads: mastery and facets
    rebuild 0/0, exactly as the same submit without it. (Landing finding,
    pre-existing on main at mvp-0.34: the workbench submit's live due time is
    computed from a wall-clock read up to a second after the attempt's own time,
    so a rebuild moves that one item's due time by about a second; it is the same with or
    without the opening and is recorded as an open item.)"""

    opened = _workbench_submit_shadow(tmp_path / "opened", opened=True)
    plain = _workbench_submit_shadow(tmp_path / "plain", opened=False)
    for diff in (opened, plain):
        assert diff["summary"]["mastery"] == 0 and diff["summary"]["facet"] == 0
        for change in diff["schedule"]["changes"]:
            moved = {key for key in change["before"] if change["before"][key] != change["after"].get(key)}
            # Real wall clock: the drift is about a second, and either submit may round to none.
            assert moved == {"due_at"} and _due_seconds(change) <= 5.0, change


# -- (iii) T1's offer keying and CA2's routes ---------------------------------------------------------


def test_iii_a_figure_grant_never_meters_an_ask_and_an_ask_grant_meters_it_under_the_cap(tmp_path, monkeypatch):
    from learnloop.ai import plan_fallback
    from learnloop.ai.routing import ready_client_for_task
    from learnloop.ai.spend import is_subscription_transport
    from learnloop.figures.routes import AUTHOR_TASK
    from learnloop.tutor.tutor_qa import question_usage
    from tests.openai_fakes import install_fake_openai
    from tests.test_plan_first_transport_paid_roles import _priced_vault

    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))  # the plan is signed out
    for name in ("LEARNLOOP_AI_PROVIDER", "LEARNLOOP_AI_FALLBACK", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    fake = install_fake_openai(monkeypatch)
    plan_fallback.revoke_all()
    try:
        root = _priced_vault(tmp_path)
        rewrite_algorithm_version(root / "learnloop.toml", load_vault(root).config.algorithms.algorithm_version, TAG)
        vault = load_vault(root)
        assert vault.config.algorithms.algorithm_version == TAG and vault.config.ask.panel_enabled

        def provider(task: str) -> tuple[str | None, bool]:
            client = ready_client_for_task(root, vault.config, task)  # type: ignore[arg-type]
            return getattr(client, "provider_name", None), is_subscription_transport(client=client)

        # A yes to "use OpenRouter" on a figure request, naming even the tutor's task.
        plan_fallback.grant_origin(root, "figure.request", [AUTHOR_TASK, "tutor_qa"])
        with plan_fallback.request(root, "figure.request"):
            assert provider(AUTHOR_TASK)[0] == "openrouter"
        with plan_fallback.request(root, "ask_tutor_question"):
            name, subscription = provider("tutor_qa")
            assert name != "openrouter"
        # A yes on the Ask itself: the Ask is metered, so CA2's per-attempt cap applies.
        plan_fallback.grant_origin(root, "ask_tutor_question", ["tutor_qa"])
        with plan_fallback.request(root, "ask_tutor_question"):
            name, subscription = provider("tutor_qa")
            assert name == "openrouter" and not subscription
            repository = Repository(VaultPaths(root, vault.config).sqlite_path)
            used, limit = question_usage(vault, repository, context="practice", practice_item_id="pi_x",
                                         session_id="sess_x", submission_id="k", metered=not subscription)
            assert (used, limit) == (0, vault.config.tutor_qa.max_questions_practice)
        # The plan's own route stays unlimited while the panel is on (owner, 2026-10-26).
        assert question_usage(vault, repository, context="practice", practice_item_id="pi_x", session_id="sess_x",
                              submission_id="k", metered=False) == (0, None)
    finally:
        plan_fallback.revoke_all()
    assert all(instance.requests == [] for instance in fake.instances)  # built at most, never called


# -- (iv) local retrieval P2 behind RW5d's grounding --------------------------------------------------


def test_iv_with_the_student_off_rw5ds_grounding_retrieval_is_p1s(tmp_path, monkeypatch):
    from learnloop.ai.spend import SpendCaps
    from learnloop.figures.service import GROUNDING_PASSAGES
    from learnloop.ops.embedding_backfill import backfill_embeddings
    from learnloop.source_retrieval import spaces
    from learnloop.source_retrieval import student_encoder as E
    from learnloop.source_retrieval.find_sources import find_sources_for_caller
    from learnloop.source_retrieval.policy import CallerContext
    from learnloop.source_retrieval.recipes import SOURCE_RETRIEVAL_RECIPES
    from tests.ux_phase1_support import set_config
    from tests.query_student_fakes import student_vault
    from tests.source_retrieval_fakes import HashingEmbedder, loaded
    from tests.test_query_student import _adopt, _space

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))  # the student's data root, per test
    paths, repository, root, _model, _report = student_vault(
        tmp_path, extra='\n[embedding.source_space]\ndefault = "local:grouped"\n')
    caps = SpendCaps(max_candidates=10_000, max_pairs=0, max_calls=100, max_total_tokens=10**8, max_estimated_usd=10.0)
    assert backfill_embeddings(loaded(paths), caps=caps, recipes=("source_block",), registry=SOURCE_RETRIEVAL_RECIPES,
                               client_factory=HashingEmbedder)["status"] == "complete"
    _adopt(root, _space(paths))
    from learnloop.source_retrieval import student_data as D

    monkeypatch.delenv(D.MODELS_ENV, raising=False)  # conftest keeps the student's models off
    started: list[object] = []

    def spawn(command, *, env, log):
        started.append(command)
        raise OSError("no query process in this test")

    monkeypatch.setattr(E, "_spawn", spawn)

    def ground():
        from learnloop.source_retrieval.dense import clear_cache

        clear_cache()
        E._ENCODERS.clear()
        hits = find_sources_for_caller(loaded(paths), repository, "eigenvalues of a symmetric matrix",
                                       caller=CallerContext(kind="reader"), intent="explain", verify=False,
                                       limit=GROUNDING_PASSAGES, embedder=HashingEmbedder())
        return hits.status, [(hit["extraction_id"], hit["span_id"]) for hit in hits.hits]

    # The adopted student is live behind the hook while the switch is on.
    E._ENCODERS.clear()
    assert spaces.LOCAL_QUERY_ENCODER(loaded(paths)) is not None
    # The kill switch: no encoder behind the hook, no start, exactly P1's empty hook.
    set_config(paths.root, {("embedding", "local", "student"): False})
    E._ENCODERS.clear()
    assert spaces.LOCAL_QUERY_ENCODER(loaded(paths)) is None
    started.clear()
    off = ground()
    assert started == []
    monkeypatch.setattr(spaces, "LOCAL_QUERY_ENCODER", lambda _vault: None)
    assert off == ground() and off[1]
