// The desks' goal fixture (spec §12, §18.3): a goal over the synthetic softmax book and attention note, answering
// goal.band, goal.lens and the learner's choices the way the sidecar does, from project-authored words only. The
// levels follow the backend's rules (curriculum/goal_lens.py) for this small path; nothing here comes from a vault.
import type {
  GoalBandDto,
  GoalBandLoDto,
  GoalLensDto,
  GoalLensSectionDto,
  GoalsListSnapshot,
  ReadingPathDepth,
} from "../../api/dto";
import { FIXTURE_SOURCES, FIXTURE_VIEWS } from "./sources";

export const FIXTURE_GOAL_ID = "fx_goal_softmax";
const BOOK = FIXTURE_SOURCES.book;
const PAPER = FIXTURE_SOURCES.paper;
const VIDEO = FIXTURE_SOURCES.video;
const DEPTHS: Array<{ id: ReadingPathDepth; label: string; means: string }> = [
  { id: "get_the_idea", label: "get the idea", means: "definitions, examples, visualizations" },
  { id: "learn_to_use_it", label: "learn to use it", means: "explanations, worked examples, practice" },
  { id: "fluency", label: "fluency", means: "novel problems, changed assumptions, delayed checks" },
];

interface FixtureLo {
  id: string;
  title: string;
  /** needed, or a prerequisite reached only past "get the idea" (later there). */
  kind: "needed" | "deep";
  readiness: GoalBandLoDto["readiness"];
}

const LOS: FixtureLo[] = [
  { id: "lo_fx_xent", title: "Cross-entropy from the true class's weight", kind: "deep", readiness: "untested" },
  { id: "lo_fx_softmax", title: "Turn scores into softmax weights", kind: "needed", readiness: "likely" },
  { id: "lo_fx_temp", title: "Temperature as a scale on the scores", kind: "deep", readiness: "untested" },
  { id: "lo_fx_grad", title: "The softmax cross-entropy gradient", kind: "needed", readiness: "untested" },
  { id: "lo_fx_attend", title: "Scaled dot-product attention", kind: "needed", readiness: "untested" },
];

/** [section, LO or null, treatment, the path's own reason, how the path places it] */
type Place = "primary" | "alternate" | "elsewhere" | "out_of_scope" | "not_about";
const BOOK_SECTIONS: Array<[string, string | null, string, string, Place]> = [
  ["s1", "lo_fx_softmax", "introduces", "The formula you'll write: exponentiate each score and divide by the sum.", "primary"],
  ["s2", "lo_fx_softmax", "develops", "Why the exponential: gaps between scores become ratios of weights.", "elsewhere"],
  ["s3", "lo_fx_temp", "develops", "Dividing by a temperature is the same move as attention's square root.", "primary"],
  ["s4", "lo_fx_xent", "develops", "The loss the gradient starts from.", "primary"],
  ["s5", "lo_fx_grad", "develops", "The gradient your backward pass needs, derived in one line.", "primary"],
  ["s6", null, "", "Not about any topic of your goal, as far as coverage says.", "out_of_scope"],
];
const PAPER_SECTIONS: Array<[string, string | null, string, string, Place]> = [
  ["p1", "lo_fx_attend", "introduces", "The definition you'll implement, as one line of matrices.", "primary"],
  ["p2", "lo_fx_temp", "mentions", "Why the square root: a temperature set by the dimension.", "alternate"],
  ["p3", null, "", "Coverage judged it not about the topics of your goal.", "not_about"],
];

/** The synthetic transcript's passages (cue numbers, inclusive): [section, from, to, LO, treatment, reason, place]. */
const VIDEO_SECTIONS: Array<[string, number, number, string | null, string, string, Place]> = [
  ["v0", 1, 3, null, "", "the setup, before any score: no LO your goal needs", "out_of_scope"],
  ["v1", 4, 11, "lo_fx_softmax", "develops", "the same recipe spoken: exponentiate, then divide by the sum", "alternate"],
  ["v2", 12, 15, "lo_fx_temp", "mentions", "the temperature knob, turned by hand", "alternate"],
  ["v3", 16, 25, "lo_fx_grad", "develops", "the gradient checked with a small nudge", "alternate"],
  ["v4", 26, 30, null, "", "safe computation and a goodbye: not in this goal's scope", "out_of_scope"],
];

export class FixtureGoal {
  depth: ReadingPathDepth = "learn_to_use_it";
  choices = new Map<string, string>();
  overrides = new Map<string, { choice: string; sectionRef?: string }>();
  operations = new Set<string>();

  goals(): GoalsListSnapshot {
    return { version: 1, goals: [{
      id: FIXTURE_GOAL_ID, title: "softmax for attention", intentSentence: "Understand softmax well enough to implement attention",
      creationSource: "learner", resolvedQuestSentence: null, questBasis: "explicit_intent", status: "active", priority: 0.5,
      targetRecall: 0.8, dueAt: null, facetScope: { concepts: [], facets: [] }, exam: { enabled: false, itemCount: 20 },
      practicableItemCount: 0, createdAt: "2026-11-02T10:00:00Z", updatedAt: "2026-11-02T10:00:00Z", report: null,
    }] };
  }

  private kind(lo: FixtureLo): "needed" | "prerequisite" | "later" {
    if (lo.kind === "needed") return "needed";
    return this.depth === "get_the_idea" ? "later" : "prerequisite";
  }

  private primary(extractionId: string, sectionId: string) {
    const view = Object.values(FIXTURE_VIEWS).find((each) => each.extractionId === extractionId);
    const heading = view?.blocks.find((block) => block.spanId === `${extractionId}_${sectionId}_h`);
    const title = String(heading?.markdown ?? "").replace(/^#+\s*/, "");
    return { extractionId, sectionId: `${extractionId}_${sectionId}`, startSpanId: `${extractionId}_${sectionId}_h`, title,
      book: extractionId === BOOK.extractionId ? "Softmax, a short book" : "Attention as averaging (a note)" };
  }

  private sectionOf(loId: string): [string, string] | null {
    for (const [section, lo, , , place] of BOOK_SECTIONS) if (lo === loId && place === "primary") return [BOOK.extractionId, section];
    for (const [section, lo, , , place] of PAPER_SECTIONS) if (lo === loId && place === "primary") return [PAPER.extractionId, section];
    return null;
  }

  band(): GoalBandDto {
    const dots: GoalBandLoDto[] = LOS.map((lo, ordinal) => {
      const at = this.sectionOf(lo.id);
      const kind = this.kind(lo);
      return { learningObjectId: lo.id, title: lo.title, kind, ordinal, readiness: lo.readiness,
        readinessLine: lo.readiness === "likely" ? "likely · LearnLoop's prediction from 3 attempts" : "Not tested on your own yet.",
        beyondDepth: kind === "later", primary: at ? this.primary(at[0], at[1]) : null, check: null, held: false };
    });
    const within = dots.filter((dot) => dot.kind !== "later");
    const lines = dots.filter((dot) => dot.kind !== "later" && dot.primary).map((dot, ordinal) => {
      const at = this.sectionOf(dot.learningObjectId)!;
      const row = [...BOOK_SECTIONS, ...PAPER_SECTIONS].find(([section, lo]) => section === at[1] && lo === dot.learningObjectId)!;
      const primary = dot.primary!;
      return {
        learningObjectId: dot.learningObjectId, title: dot.title ?? "", phrase: "", kind: dot.kind as "needed" | "prerequisite",
        label: (dot.kind === "needed" ? "core" : "prerequisite") as "core" | "prerequisite", chip: dot.kind === "needed" ? "core" : "prerequisite",
        effectiveLabel: (dot.kind === "needed" ? "core" : "prerequisite") as "core" | "prerequisite", reason: row[3], reasonBy: "model" as const,
        override: (this.overrides.get(dot.learningObjectId)?.choice ?? null) as never,
        section: { extractionId: primary.extractionId, sectionId: primary.sectionId, title: primary.title, book: primary.book,
          sourceId: primary.extractionId === BOOK.extractionId ? BOOK.sourceId : PAPER.sourceId, startSpanId: primary.startSpanId,
          minutes: 2, treatment: row[2], treatmentWords: `${row[2]} it`, read: false, canUseInstead: true },
        alternates: dot.learningObjectId === "lo_fx_softmax" ? [{
          extractionId: BOOK.extractionId, sectionId: `${BOOK.extractionId}_s2`, title: "2 Why the exponential", book: "Softmax, a short book",
          sourceId: BOOK.sourceId, startSpanId: `${BOOK.extractionId}_s2_h`, minutes: 1, treatment: "develops", treatmentWords: "develops it",
          read: false, canUseInstead: true, difference: "the same idea through ratios of weights" }] : [],
        exercise: null, check: null, ordinal,
      };
    });
    const depthSize = (depth: ReadingPathDepth) => {
      const count = LOS.filter((lo) => lo.kind === "needed" || depth !== "get_the_idea").length;
      return { learningObjects: count, sections: count, minutes: count * 2 };
    };
    return {
      version: 1, goalId: FIXTURE_GOAL_ID,
      goal: { id: FIXTURE_GOAL_ID, title: "softmax for attention", sentence: "Understand softmax well enough to implement attention", kind: "quest",
        dueAt: null, setAt: "2026-11-02T10:00:00Z" },
      status: "ready", message: null, reason: null, depth: this.depth, depthLabel: DEPTHS.find((d) => d.id === this.depth)?.label,
      depths: DEPTHS.map((depth) => ({ ...depth, ...depthSize(depth.id) })),
      learningObjects: dots,
      counts: { learningObjects: within.length, demonstrated: within.filter((d) => d.readiness === "demonstrated").length,
        likely: within.filter((d) => d.readiness === "likely").length, untested: within.filter((d) => d.readiness === "untested").length },
      unmatched: [{ phrase: "implement", proposedTitle: "Write softmax as numerically safe code" }],
      checks: { dueToday: 0, answeredToday: 0, first: null },
      next: { kind: "section", learningObjectId: within[0].learningObjectId, section: within[0].primary! },
      pace: { attemptsPerDay: 4.2, attemptsLast14d: 59, daysLeft: null, attemptsRemaining: null, neededPerDay: null, onPace: null,
        attemptsLogged: 59, paceKind: "qualifying" },
      coverage: { unjudged: [], covering: false, failure: null },
      path: { goalId: FIXTURE_GOAL_ID, title: "softmax for attention", sentence: "Understand softmax well enough to implement attention", kind: "quest",
        dueAt: null, depth: this.depth, depthLabel: null, depths: DEPTHS, status: "ready", lines: lines as never, uncovered: [],
        stateKey: "fx", message: null, reason: null, covering: false, minutes: lines.length * 2 },
    };
  }

  private level(extractionId: string, section: string, lo: string | null, treatment: string, reason: string, place: Place,
                cues?: [number, number], cueTitle?: string): GoalLensSectionDto {
    const view = Object.values(FIXTURE_VIEWS).find((each) => each.extractionId === extractionId)!;
    const spanIds = cues
      ? Array.from({ length: cues[1] - cues[0] + 1 }, (_, i) => `${extractionId}_c${cues[0] + i}`)
      : view.blocks.filter((block) => block.spanId?.startsWith(`${extractionId}_${section}_`)).map((block) => block.spanId as string);
    const ref = `${extractionId}/${extractionId}_${section}`;
    const choice = (this.choices.get(ref) ?? null) as "read_anyway" | null;
    const fixtureLo = lo ? LOS.find((each) => each.id === lo)! : null;
    const kind = fixtureLo ? this.kind(fixtureLo) : null;
    let level: GoalLensSectionDto["level"];
    let reasonKey: GoalLensSectionDto["reasonKey"];
    let reasonMd = reason;
    if (!fixtureLo) {
      level = "skippable";
      reasonKey = place === "not_about" ? "not_about" : "out_of_scope";
    } else if (kind === "later") {
      level = "later";
      reasonKey = "deeper_depth";
      reasonMd = `Needed for “${fixtureLo.title}” only deeper than get the idea.`;
    } else if (place === "primary") {
      level = kind === "needed" ? "core" : "supporting";
      reasonKey = kind === "needed" ? "primary" : "prerequisite";
    } else if (place === "alternate") {
      level = "supporting";
      reasonKey = treatment === "mentions" ? "mentions" : "alternate";
    } else {
      level = "supporting";
      reasonKey = "another_treatment";
    }
    const heading = view.blocks.find((block) => block.spanId === `${extractionId}_${section}_h`);
    const verb = { introduces: "introduces", develops: "develops", applies: "uses", mentions: "mentions" }[treatment] ?? treatment;
    const role = kind === "needed" ? "a goal LO" : kind === "later" ? "needed at a deeper depth" : "a prerequisite";
    const where = place === "primary" ? "its primary section" : place === "alternate" ? "another way" : "not on your path here";
    return {
      sectionId: `${extractionId}_${section}`, title: cueTitle ?? String(heading?.markdown ?? "").replace(/^#+\s*/, ""),
      startSpanId: cues ? spanIds[0] : `${extractionId}_${section}_h`,
      spanIds, level, mapping: "mapped", reasonKey, reasonMd, knownLevel: null,
      loIds: lo ? [lo] : [],
      learningObjects: fixtureLo ? [{ learningObjectId: fixtureLo.id, title: fixtureLo.title, kind: kind!, level: level as never, reasonKey,
        treatment, pathLabel: place === "primary" ? (kind === "needed" ? "core" : "prerequisite") : null, override: null, held: false, answeredToday: false }] : [],
      determiningLoId: lo, learnerLine: choice ? "You chose to read it anyway." : null,
      coverageLine: fixtureLo ? `coverage: ${verb} “${fixtureLo.title}” · ${role} · ${where} · ${level.replace("_", " ")}` : null,
      held: false, dim: (level === "skippable" || level === "later") && choice !== "read_anyway", choice, judgedPer: "section",
    };
  }

  lens(extractionId: string): GoalLensDto {
    const table = extractionId === BOOK.extractionId ? BOOK_SECTIONS : extractionId === PAPER.extractionId ? PAPER_SECTIONS : [];
    const levels = extractionId === VIDEO.extractionId
      ? VIDEO_SECTIONS.map(([section, from, to, lo, treatment, reason, place]) => this.level(extractionId, section, lo, treatment, reason, place, [from, to], `cues ${from}–${to}`))
      : table.map(([section, lo, treatment, reason, place]) => this.level(extractionId, section, lo, treatment, reason, place));
    return { version: 1, goalId: FIXTURE_GOAL_ID, extractionId, status: "ready", message: null, depth: this.depth,
      depthLabel: DEPTHS.find((d) => d.id === this.depth)?.label, mapping: levels.length ? "mapped" : "unmapped", levels };
  }

  sectionChoice(input: { goalId: string; extractionId: string; sectionId: string; choice: string; operationId: string }) {
    const ref = `${input.extractionId}/${input.sectionId}`;
    const replayed = this.operations.has(input.operationId);
    if (!replayed) {
      this.operations.add(input.operationId);
      if (input.choice === "none") this.choices.delete(ref); else this.choices.set(ref, input.choice);
    }
    return { version: 1, choice: { operationId: input.operationId, goalId: input.goalId, extractionId: input.extractionId,
      sectionId: input.sectionId, choice: input.choice, replayed, createdAt: "2026-11-23T10:00:00Z" } };
  }

  setDepth(depth: ReadingPathDepth) {
    this.depth = depth;
    return this.band().path;
  }

  override(input: { learningObjectId: string; choice: string; sectionRef?: string }) {
    this.overrides.set(input.learningObjectId, { choice: input.choice, sectionRef: input.sectionRef });
    return { override: input, path: this.band().path };
  }
}
