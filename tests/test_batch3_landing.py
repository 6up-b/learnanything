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


from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    ONE_ASK_ALGORITHM_VERSION,
    ONE_ASK_VERSIONS,
    REPLAY_LEDGER_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.db.repositories import Repository
from learnloop.ops.upgrades import rewrite_algorithm_version
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.hint_h2b_review_helpers import grader  # noqa: F401 - the blind grader fixture
from tests.helpers import allow_below_floor

TAG = ONE_ASK_ALGORITHM_VERSION
PREDECESSOR = REPLAY_LEDGER_ALGORITHM_VERSION


# -- the chain -------------------------------------------------------------------------------------


def test_mvp035_is_one_constant_after_mvp034_and_the_latest():

    # The kept replaced claims' mvp-0.36, mobile PR-4's mvp-0.37, the cold-retry reschedule's mvp-0.38, Reader RW6b's mvp-0.39 and
    # curriculum C1's mvp-0.40, teacher TE1's mvp-0.41, follow-ups Nov 2's mvp-0.42 and teacher TE1b's mvp-0.43 (the
    # latest) follow it (and keep it).
    assert SUCCESSOR_CHAIN[-27:] == ("mvp-0.33", "mvp-0.34", "mvp-0.35", "mvp-0.36", "mvp-0.37", "mvp-0.38", "mvp-0.39", "mvp-0.40", "mvp-0.41", "mvp-0.42", "mvp-0.43", "mvp-0.44", "mvp-0.45", "mvp-0.46", "mvp-0.47", "mvp-0.48", "mvp-0.49", "mvp-0.50", "mvp-0.51", "mvp-0.52", "mvp-0.53", "mvp-0.54", "mvp-0.55", "mvp-0.56", "mvp-0.57", "mvp-0.58", "mvp-0.59")
    assert TAG == "mvp-0.35" == SUCCESSOR_CHAIN[-25] and LATEST_ALGORITHM_VERSION == "mvp-0.59"
    assert PREDECESSOR == "mvp-0.34"
    assert ONE_ASK_VERSIONS == frozenset({TAG, "mvp-0.36", "mvp-0.37", "mvp-0.38", "mvp-0.39", "mvp-0.40", "mvp-0.41", "mvp-0.42", "mvp-0.43", "mvp-0.44", "mvp-0.45", "mvp-0.46", "mvp-0.47", "mvp-0.48", "mvp-0.49", "mvp-0.50", "mvp-0.51", "mvp-0.52", "mvp-0.53", "mvp-0.54", "mvp-0.55", "mvp-0.56", "mvp-0.57", "mvp-0.58", "mvp-0.59"})


# -- the journalled activation ----------------------------------------------------------------------


# -- (i) show me is not an Ask question --------------------------------------------------------------


def _question_events(repository) -> int:
    import sqlite3
    from contextlib import closing

    with closing(sqlite3.connect(repository.sqlite_path)) as connection:
        return connection.execute("SELECT COUNT(*) FROM question_events").fetchone()[0]


def test_i_a_figure_goal_from_the_ask_rail_or_the_tutor_never_spends_an_ask_question(tmp_path, monkeypatch):
    from learnloop.tutor.tutor_qa import question_usage
    from tests.figure_fixtures import AuthorFake, build, flagship
    from tests.figures_show_me_helpers import GOAL, READING_AT, FindFake, _ctx, _tutor_ask

    goal = "vary p and watch the mass left of zero follow it"
    paths, repository, ctx, _tutor, author, _find, answer = _tutor_ask(tmp_path, monkeypatch, figure_goal=goal)
    rewrite_algorithm_version(paths.root / "learnloop.toml", load_vault(paths.root).config.algorithms.algorithm_version,
                              TAG)  # CA2's successor, its panel on (the default)
    allow_below_floor(paths.root)
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
    from tests.reader_ca2_fix_orchestrator_helpers import _call, _open, _row, _step
    from tests.reader_ca2_codex_rereview_helpers import _attempt, _draft, _steps_sidecar

    paths, ctx, session = _steps_sidecar(tmp_path)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG
    _draft(ctx, session, CDF_ITEM, "kA", **({"earlierOpened": True} if opened else {}))
    view = _open(ctx, session)
    assert bool(_row(paths, view["sessionId"])["earlier_opened_at"]) is opened
    _step(ctx, view["sessionId"])
    attempt = _call(ctx, "workbench.submit", {"sessionId": view["sessionId"], "practiceSessionId": session})["attempt"]
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == (1 if opened else 0)
    # The submit queued background post-attempt jobs. A shadow rebuild refuses a database that changes under it, so
    # they stop first; otherwise the result depended on which thread won.
    ctx.close()
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
    from tests.plan_first_transport_paid_roles_helpers import _priced_vault

    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))  # the plan is signed out
    for name in ("LEARNLOOP_AI_PROVIDER", "LEARNLOOP_AI_FALLBACK", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    fake = install_fake_openai(monkeypatch)
    plan_fallback.revoke_all()
    try:
        root = _priced_vault(tmp_path)
        rewrite_algorithm_version(root / "learnloop.toml", load_vault(root).config.algorithms.algorithm_version, TAG)
        allow_below_floor(root)
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
    from tests.query_student_helpers import _adopt, _space

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
