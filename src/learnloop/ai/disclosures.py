"""Privacy disclosures for the judgment routes (router spec §6.2, D6).

Settings and ``learnloop eval judges`` show one disclosure per route whose
provider would receive learner text, naming who receives it, what is sent,
and when. Nothing is sent by merely configuring a route.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

from learnloop.config import LearnLoopConfig

#: (route task, judge, consumer) for the judgment routes. The Decider's
#: Tier-1 route and the learner-text gaps' Decider route send learner text in
#: the ordinary course at mvp-0.22 (owner decision 2026-10-13, D6; review F5);
#: the router's two routes do at mvp-0.24 (router R2b, D6 recorded 2026-10-13).
JUDGE_ROUTES: tuple[tuple[str, str, str], ...] = (
    ("llm_probability_decider", "decider", "llm_probability"),
    ("llm_probability_llm", "llm", "llm_probability"),
    ("router_decider", "decider", "router"),
    ("router_llm", "llm", "router"),
    ("tier1_decider", "decider", "tier1"),
    ("learner_gap_decider", "decider", "learner_text_gaps"),
    ("reader_intent", "decider", "reader_intent"),
    ("library_organizer", "llm", "library_ask"),
    ("approach_map", "llm", "approach_maps"),
    ("hint_chooser", "decider", "hint_chooser"),
    ("hint_writer", "llm", "hint_writer"),
    ("hint_outcome", "llm", "hint_outcome"),
    ("ad_forecast_llm", "llm", "adaptive_difficulty"),
    ("ad_forecast_decider", "decider", "adaptive_difficulty"),
    ("ad_feature_audit", "llm", "ad_feature_audit"),
    ("workbench_check", "llm", "workbench_check"),
    ("passage_cue_judge", "llm", "cues"),
    ("reading_path_judge", "llm", "reading_paths"),
)

_WHEN = {
    "llm_probability": (
        "Only when you run the offline llm_probability harness yourself (field.enabled and "
        "field.llm_probability_enabled, then an explicit --prepare-llm). V1 sends item content "
        "only; V2 adds your recent right/wrong results; V3 adds excerpts of your earlier answers, "
        "their grades, diagnosis hypotheses and your tutor questions."
    ),
    "router": (
        "From mvp-0.24, while router.enabled is on and router.mode is mixture: each time Today chooses "
        "your next block (and each time a follow-up question could interrupt a block), the learner state "
        "card is sent: your recent answers and the questions they answered, their grades, open problems "
        "the diagnoser found, your self-ratings and teach-back summaries, the blocks on offer and, on about "
        "half of the choices, similar earlier choices with what followed. Never a reference answer, an "
        "answer key, a rubric or exam material. The router's model also summarizes each graded teach-back "
        "dialogue (router.teach_back_summary). Below mvp-0.24, or with router.mode = staged, nothing is sent."
    ),
    "tier1": (
        "At mvp-0.22, for each [decider_routes] switch that is on: a misconception statement "
        "diagnosed in your answer with the registry beliefs it might match, whenever an attempt's "
        "misconceptions are matched; your tutor questions when you run learnloop field "
        "classify-questions; your questions and the tutor's answers (and generated items beside "
        "held-out exam text) when you run a contamination report; your earlier and current answers "
        "when you run learnloop diagnose review. At every version, the cited source passages and the "
        "new wording of a facet reword a proposal makes, and (decider_routes.required_method_statement, "
        "while ai.routing.rubric_phrasing_judge is unset) a textbook exercise's statement with the method "
        "its import proposes, or a practice-family variant's stem with its parent's method (no learner text). "
        "While adaptive_difficulty.feature_audit and decider_routes.ad_feature_audit are on, once per version of "
        "a practice question, in the background: its statement and reference answer, so the Decider can say "
        "how the question is built (no learner text)."
    ),
    "learner_text_gaps": (
        "When the learner-text gap pipeline reads your tutor questions, stuck answers or diagnosis "
        "readings (learner_text_gaps.enabled and learner_text_gaps.decider_enabled): the text, what "
        "it was about, and the candidate prerequisites or beliefs it might match. At mvp-0.22 the "
        "Decider decides; before it, its answer is a logged second opinion."
    ),
    "reader_intent": (
        "While reader_intent.enabled is on, each time you type into the Reader's intent box (the "
        "small box under a selection) and press Enter: your words, the selected passage (cut to a "
        "short excerpt) and the names of the actions on offer, so the Decider can pick the one you "
        "meant. With reader_intent.speculative_enabled on (the default) the same is sent once you "
        "pause typing for a moment, before you press Enter, so the action is ready when you do; "
        "switching it off sends nothing until Enter. An empty Enter sends nothing."
    ),
    "library_ask": (
        "While library_ask.enabled is on, each time you ask your library (Shift+Enter in the library "
        "search, Ctrl+Shift+F in the Reader, or where else is this explained? / where is this used? / "
        "what do I need first? on a selection): your question and the passages found in your books, so "
        "LearnLoop's model can note what each one contributes. With the \"personalized\" chip on (the "
        "default, library_ask.personalized_default) the open questions LearnLoop has named from your "
        "own words on those passages' topics go too; with it off, none do. Comparing pinned passages "
        "and asking the tutor about them send those passages to their own routes (source_compare, "
        "tutor_qa), only when you press them."
    ),
    "approach_maps": (
        "While hints.maps.enabled is on: when the practice screen first shows a question with no approach "
        "map yet (hints.maps.build_on_serve, in the background), when you run learnloop hints maps build, "
        "and when your new correct answers are merged into a map: the question, its reference solution, "
        "rubric and authored hints, its solution recipes, passages from your own books, and your own "
        "correct answers to it and its sibling questions, so LearnLoop's model can sketch the routes to "
        "the answer. Nothing in it is shown to you or to the grader."
    ),
    "hint_chooser": (
        "While hints.adaptive_enabled and hints.chooser_enabled are on, each time you ask for a hint on the "
        "practice screen: a short typed summary of where you stand on the question (its placement, your "
        "recent results on it and its topic, the kinds of hint you were shown and how you replied, how much "
        "you have written, your help style) and the kinds of hint on offer, so the Decider can choose one. "
        "Never your answer text, the reference answer or the question's solution."
    ),
    "hint_writer": (
        "While hints.adaptive_enabled is on, each time you ask for a hint on the practice screen: the "
        "question, its reference solution, rubric and authored hints, its approach map, your current "
        "answer draft, the earlier hints and your replies, and a short summary of your state, so "
        "LearnLoop's model can write the hint for your work. Never sent to Codex (hints fall back to the "
        "question's own hints there)."
    ),
    "adaptive_difficulty": (
        "While adaptive_difficulty.outside_forecasters names them (by default all three), in the background "
        "and never while you wait: once per new version of a practice question, before it is first served, its "
        "statement, topic and skill names (llm_v1:item, never the reference answer, rubric or hints); and after "
        "each daily-plan question is served, the same plus a short record of your earlier answers on its topic "
        "and the topics it builds on, as of when it was served (each earlier question, whether it was right, the "
        "hints used, never your answer text), so LearnLoop can score how well each forecaster predicts your "
        "answers (llm_v3:llm on ai.routing.ad_forecast_llm, llm_v3:decider on ai.routing.ad_forecast_decider). "
        "Measurement only: nothing served, graded or scheduled changes. Never material held out for an exam."
    ),
    "ad_feature_audit": (
        "While adaptive_difficulty.feature_audit is on, when the Decider gives no answer for a dimension (or with "
        "decider_routes.ad_feature_audit off): a practice question's statement and reference answer, once per "
        "version, in the background, so LearnLoop's model can say how the question is built (complexity, "
        "transfer, scaffolding, span, response). No learner text."
    ),
    "hint_outcome": (
        "While hints.adaptive_enabled and hints.outcome_placement_enabled are on, in the background after you "
        "submit an answer you had hints on that was not fully right, on a question with an approach map: the "
        "question, its approach map, your submitted answer and where each hint was aiming, so LearnLoop's model "
        "can say how far along the route your answer got. Measurement only: it never changes your grade."
    ),
    "workbench_check": (
        "While workbench.help_enabled is on, each time you press \"Check my work\" in the workbench: the "
        "problem, its reference solution and rubric, your steps, and the question's approach map when it has "
        "one, so LearnLoop's model can say which steps hold. Never sent to Codex. It never grades you."
    ),
    "cues": (
        "While cues.enabled and cues.discovery_enabled are on, in the background when you open a book in the "
        "Reader: for each of your open questions on what the book teaches (a misunderstanding LearnLoop's "
        "model named from your answers, an open explanation it is weighing, a gap named from your own words) "
        "and for each skill you have shown, its statement and passages from that book, so LearnLoop's model "
        "can say which passages connect to it and quote what they rely on. At most "
        "cues.max_calls_per_source_open calls per open and cues.max_calls_per_source_per_day per book in any 24 hours; "
        "never material held out for an exam, never a "
        "solution. Display only: it never grades you."
    ),
    "reading_paths": (
        "While reading_paths.enabled is on, once per book and depth (and again when the depth, the book's "
        "sections or your status on what they teach changes), when the Guide shows your reading path: the "
        "book's section titles in order, each section's instructional roles, the titles of the topics each "
        "teaches with your status on each (shown on your own, assumed known, learning, new), the depth you "
        "chose and your active goal's title, so LearnLoop's model can say which sections are core, "
        "prerequisite or enrichment. No passage text, nothing you wrote, never material held out for an "
        "exam. Display only: it changes no plan and never grades you."
    ),
}


def _host(url: str | None) -> str:
    parts = urlsplit(url or "")
    return parts.hostname or "an unnamed endpoint"


def recipient(config: LearnLoopConfig, provider_name: str) -> str:
    profile = config.ai.providers.get(provider_name)
    if profile is None:
        return f"the unconfigured provider {provider_name!r} (nothing can be sent)"
    kind = profile.type.strip().lower()
    if kind == "decider":
        if getattr(profile, "api", "openrouter") == "perplexity":
            return f"Perplexity's Decisions API directly ({_host(profile.base_url or 'https://api.perplexity.ai')})"
        return (
            "OpenRouter, which forwards it to Perplexity (the only provider OpenRouter lists for "
            "the Decider). LearnLoop does not request OpenRouter's data_collection=deny for this "
            "route: the listing does not show that Perplexity's endpoint satisfies it, and a request "
            "that requires it fails when no provider does"
        )
    if kind in {"codex_sdk", "http"}:
        return "OpenAI, through your ChatGPT subscription (Codex)"
    if kind == "chatgpt_plan":
        return "OpenAI, through your ChatGPT plan (Sign in with ChatGPT; requests are sent with store=false)"
    if kind == "openrouter":
        return "OpenRouter and the upstream provider it routes the model to"
    if kind == "openai_chat":
        return f"the chat endpoint at {_host(profile.base_url or 'https://api.openai.com')}"
    return f"the {profile.type} endpoint at {_host(profile.base_url)}"


def judge_route_disclosures(config: LearnLoopConfig) -> list[dict[str, Any]]:
    """One entry per judgment route: who receives learner text, what and when."""

    from learnloop.ai.routing import provider_for_task

    entries = []
    for task, judge, consumer in JUDGE_ROUTES:
        # The offline harness ignores LEARNLOOP_AI_PROVIDER; live routes do not.
        name = provider_for_task(config, task, allow_env=consumer != "llm_probability").provider_name  # type: ignore[arg-type]
        profile = config.ai.providers.get(name) if name else None
        who = recipient(config, name) if name else "no provider (the route is unset)"
        entries.append({
            "route": task,
            "judge": judge,
            "consumer": consumer,
            "provider": name or None,
            "provider_type": profile.type if profile is not None else None,
            "model": profile.model if profile is not None else None,
            "disclosure": (
                f"{_WHEN[consumer]} Learner text goes to {who}. Check that provider's retention "
                "terms before relying on it (router D6)."
            ),
        })
    return entries


def decider_destination(config: LearnLoopConfig, task: str) -> tuple[str, str] | None:
    """``(the key it needs, where it goes)`` for a Decider route, in the connection sheet's plain words.

    The same recipient :func:`recipient` names for Settings: OpenRouter,
    which forwards to Perplexity, or Perplexity's API directly. None when the
    route is not served by a ``decider`` profile.
    """

    from learnloop.ai.routing import provider_for_task

    name = provider_for_task(config, task, allow_env=False).provider_name  # type: ignore[arg-type]
    profile = config.ai.providers.get(name) if name else None
    if profile is None or profile.type.strip().lower() != "decider":
        return None
    if getattr(profile, "api", "openrouter") == "perplexity":
        return "a Perplexity key", "Perplexity"
    return "an OpenRouter key", "Perplexity, through OpenRouter"


__all__ = ["JUDGE_ROUTES", "decider_destination", "judge_route_disclosures", "recipient"]
