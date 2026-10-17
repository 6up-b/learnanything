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
        "its import proposes, or a practice-family variant's stem with its parent's method (no learner text)."
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
