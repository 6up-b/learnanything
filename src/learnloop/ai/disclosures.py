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
    ("compare_scope", "decider", "compare_scope"),
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
    ("deliverable_scope_resolver", "llm", "curriculum_scope"),
    ("deliverable_path_judge", "llm", "curriculum_path"),
    ("figure_author", "llm", "figures"),
    ("figure_rich_author", "llm", "figures_rich"),
    ("figure_prefetch_judge", "llm", "figures_prefetch"),
    ("followup_probe_author", "llm", "followup_probes"),
    ("reader_digest", "llm", "reader_digest"),
    ("note_link_judge", "llm", "notes"),
    ("teacher", "llm", "teacher"),
)

_WHEN = {
    "llm_probability": (
        "Only when you run the offline llm_probability harness yourself (field.enabled and "
        "field.llm_probability_enabled, then an explicit --prepare-llm). V1 sends item content "
        "only; V2 adds your recent right/wrong results; V3 adds excerpts of your earlier answers, "
        "their grades, diagnosis hypotheses and your tutor questions. At mvp-0.30, while "
        "adaptive_difficulty.learned_coupling is on, adaptive difficulty's relatedness proposal also uses "
        "this route: once per subject when you run learnloop ad relatedness, then when a subject's content "
        "changes, it sends the subject's topic and facet titles and summaries, the concept graph and the "
        "practice questions' wording (never your answers, grades or any other learner text, never a "
        "reference answer, never exam material)."
    ),
    "followup_probes": (
        "From mvp-0.45, while followup.generate_and_serve is on: after a missed question whose diagnosis leaves "
        "rival causes, and for a probe an episode needs, the topic's title and summary, the possible causes the "
        "diagnoser wrote, the question you missed and the topic's other practice questions are sent, to write "
        "one new question. Never your answer, never a reference answer and never exam material."
    ),
    "router": (
        "From mvp-0.24, while router.enabled is on and router.mode is mixture: each time Today chooses "
        "your next block (and each time a follow-up question could interrupt a block), the learner state "
        "card is sent: your recent answers and the questions they answered, their grades, open problems "
        "the diagnoser found, your self-ratings, any marks you gave possible causes with what you wrote there "
        "(while followup.hypothesis_marks is on), teach-back summaries, the blocks on offer and, on about "
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
    "compare_scope": (
        "While reader_compare.scope_enabled is on, each time you press Enter in the ask box (Ctrl+Shift+F in "
        "the Reader, or Ask on the library page) or in a comparison's refine box (/): your words and the titles "
        "and file names of the books in your library (and, when refining, which of them are being compared), "
        "so the Decider can say whether you asked for a comparison, which books you named and what the topic "
        "is. Never a passage of a book, nothing else you wrote and never material held out for an exam. "
        "Nothing is sent while you type, or for any other way into a comparison."
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
        "hints used and, while adaptive_difficulty.history_answer_excerpts is on (the default), a short excerpt "
        "of your answer; off, never your answer text), so LearnLoop can score how well each forecaster predicts "
        "your answers (llm_v3:llm on ai.routing.ad_forecast_llm, llm_v3:decider on ai.routing.ad_forecast_decider). "
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
        "exam. It never grades you; with reading_paths.plan_uses_path on, today's plan reads the labels "
        "(no further call) so your reading block opens the next core or prerequisite section."
    ),
    "curriculum_scope": (
        "While curriculum.enabled is on, each time you name or change what you are learning for (a deliverable: "
        "a sentence, a pasted topic list, a selected passage of one of your books, a correction such as \"not "
        "Jordan form\") or write \"also about...\" on a section: your words in order, and your vault's active "
        "topics as short records (title, statement, concept, prerequisites), so LearnLoop's model can say which "
        "topics you need and which phrases match none. Never a practice question, an answer or a grade, never "
        "material held out for an exam (a protected passage is refused before anything is sent). It never grades "
        "you; a new topic is created only when you say yes."
    ),
    "curriculum_path": (
        "While curriculum.enabled is on, once per deliverable and depth (and again when its topics, your status "
        "on them, the sections your books have for them or your reading changes), when the Guide shows the "
        "deliverable's path: your deliverable's sentence and deadline, each topic it needs with the phrase of "
        "yours it answers and your status on it (shown on your own, assumed known, learning, new), the sections "
        "of your books that treat it (book and section titles, how each treats it, its roles and notation line, "
        "minutes of reading), which books you have been reading and the choices you made on earlier paths (use "
        "this one instead, skip), so LearnLoop's model can pick one section per topic. No passage text, never "
        "material held out for an exam. It never grades you; nothing in today's plan reads the path yet."
    ),
    "figures": (
        "While figures.enabled is on, each time you press \"make this explorable\" in the Reader: the selected "
        "passage, its caption and the paragraphs around it (and the figure's image or your selected region of "
        "it, when the route can read images), so LearnLoop's model can write an interactive version; with "
        "figures.revisions_enabled, a \"not right?\" note you write goes with the earlier version. With "
        "figures.show_me_enabled, \"show me\" sends your request in your words (or the goal LearnLoop's tutor "
        "wrote, when you press it) and, when you select no passage, the passages LearnLoop finds in your books for "
        "it (or none) -- never to grade you. With figures.author_learner_state on (the default), when you have "
        "state on the passage's topics, it also sends where you stand on them: your status on each in words, the "
        "open misunderstandings and gaps LearnLoop has named, and at most two of your recent answers on them with "
        "their questions and results, so the figure can show what you most need to see. Never an answer on exam, "
        "held-out or reserved material or on a check still waiting for you, never a reference answer, and never "
        "material held out for an exam. A figure never grades you and is never evidence."
    ),
    "figures_rich": (
        "While figures.rich_tiers_enabled is on and a richer kind of figure (a narrated Manim animation, after "
        "you allow it once) was chosen for a request you pressed: what the figure author received (the passage "
        "and the paragraphs around it, or the passages found in your books, and your request in your words or "
        "the goal LearnLoop's tutor wrote, and, with figures.author_learner_state on, where you stand on the "
        "passage's topics as the figure author received it) and the author's plan for the animation, so "
        "LearnLoop's model can write it; when an attempt fails, what went wrong in code's words. Never an answer "
        "on exam, held-out or reserved material or on a check still waiting for you, and never material held out "
        "for an exam. It never grades you and is never evidence."
    ),
    "figures_prefetch": (
        "Only while figures.prefetch_enabled is on (off unless you turn it on), on this computer's desktop app, "
        "on mains power, in the background, and only on the ChatGPT plan (never a metered route, never an offer): "
        "the blocks of a section LearnLoop expects you to read next (the plan's reading, the section after the "
        "one you are in, a lesson's planned passages), with exam and held-out material removed, so LearnLoop's "
        "model can say which blocks are worth an explorable figure and how likely a reader is to open one. For a "
        "gap LearnLoop found in your understanding on a topic the plan or a lesson touches, also what LearnLoop "
        "thinks you're unsure of, in one sentence, with the topic and a passage that treats it, to prepare a "
        "figure. The figures it builds are sent to the figure author like any figure you ask for. Never an answer "
        "key, a rubric or exam material. It never grades you and is never evidence."
    ),
    "reader_digest": (
        "While digest.enabled and digest.narrative_enabled are on, once per reader session, in the background "
        "after the session has ended: the session's typed summary (which sections you read, the ids and status "
        "of the questions you opened, the problems you worked with the help level and grade, missed predictions "
        "and the gaps named from your questions, as ids, kinds and verdicts) with the titles of the topics and "
        "sections it names, so LearnLoop's model can write a short summary of what you did. While "
        "digest.narrative_quotes_inquiry is on (the default) the words of the questions you opened go too (a "
        "short excerpt each), so the summary may quote them; off, nothing you wrote. No passage text, never "
        "material held out for an exam. It never grades you and is never evidence."
    ),
    "notes": (
        "While notes.enabled is on, in the background for each topic on a deliverable's path: the topic's title "
        "and statement, the opening of its chosen passage, and the text of the notes of yours in this vault "
        "(notes and highlights you wrote in the Reader, and your captured notes) found for it, so LearnLoop's "
        "model can say which notes discuss it. It runs quietly on the note link route as configured (the "
        "ChatGPT plan by default; a metered route only when priced and inside the curriculum's daily cap), "
        "and never asks. A note written beside protected exam material is never sent. Only the notes it links "
        "are kept, in your vault. A note is never a source, never used to write questions and never evidence. "
        "It never grades you. While embeddings are on, your notes are embedded like your books (the embedding "
        "route), so you can search them by meaning. Only if you turn on notes.gaps_enabled (off unless you opt "
        "in, in Settings): also, in the background, one note you linked with the titles and statements of the "
        "topics it is linked to and the opening of those passages, read like your other questions and answers "
        "for a gap in your understanding; that only steers what LearnLoop suggests, never grades you, and a "
        "note you hid is never sent."
    ),
    "teacher": (
        "From mvp-0.41, while teacher.enabled is on, only during a lesson you start (Teach me this): each "
        "turn sends the lesson's teaching rules, a brief of what LearnLoop knows about you on the lesson's "
        "topics (labels, predictions, your earlier answers and questions on them, the results of earlier "
        "lessons and their later checks, and with your notes linked, which notes discuss them), the topic's "
        "sections from your books (never exam or held-out material) and the lesson so far, including your "
        "replies and answers. With the ChatGPT plan down you are asked before OpenRouter is used. The "
        "teacher never grades you: your answers to its checks are graded by the grader, which sees only the "
        "question, the answer and the rubric."
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
