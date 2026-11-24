// The goal lens's state on the desks (spec §12.1-§12.5): which goal, its band, one whole-reading goal.lens per
// reading in view (filtered client-side), dimming, the path view and the why card. Reads only; the writes are the
// learner's own choices (the depth, a path line's choice, read it anyway), through the RPCs that own them.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../../../api/client";
import { peek, setQueryData, subscribe } from "../../../api/queryCache";
import { TAG } from "../../../api/queryTags";
import type {
  DeliverablePathChoice,
  GoalBandDto,
  GoalLensDto,
  GoalLensInput,
  GoalLensSectionDto,
  GoalSectionChoiceDto,
  GoalSectionChoiceInput,
  GoalChoicesDto,
  GoalsListSnapshot,
  ReadingPathDepth,
} from "../../../api/dto";
import type { Timers } from "../keys/router";
import { indexLens, type LensIndex } from "./model";

/** The goal lens's calls; absent, the sidecar's. */
export interface GoalTransport {
  goals: () => Promise<GoalsListSnapshot>;
  /** The chooser's labels, protected on the server (goal.choices); absent, the chooser names goals neutrally. */
  choices?: () => Promise<GoalChoicesDto>;
  band: (input: { goalId: string }) => Promise<GoalBandDto>;
  lens: (input: GoalLensInput) => Promise<GoalLensDto>;
  sectionChoice: (input: GoalSectionChoiceInput) => Promise<GoalSectionChoiceDto>;
  /** curriculum.path with judge: true starts the coverage and the path judgment the goal owes (background). */
  path: (input: { goalId: string; judge?: boolean }) => Promise<unknown>;
  setDepth: (input: { goalId: string; depth: ReadingPathDepth }) => Promise<unknown>;
  override: (input: { goalId: string; learningObjectId: string; choice: DeliverablePathChoice; sectionRef?: string }) => Promise<unknown>;
  /** "map it": the goal's own sentence as its first scope input (curriculum.set_scope; a pressed action). */
  setScope: (input: { goalId: string; kind: "text" | "correction"; text: string }) => Promise<unknown>;
  /** "add it" on a phrase not in the library (curriculum.scope_decide: the learner's yes creates the LO). */
  scopeDecide: (input: { goalId: string; phrase: string; decision: "create" | "decline" }) => Promise<unknown>;
}

export const LIVE_GOAL_TRANSPORT: GoalTransport = {
  goals: () => api.goalsList(),
  choices: () => api.goalChoices(),
  band: (input) => api.goalBand(input),
  lens: (input) => api.goalLens(input),
  sectionChoice: (input) => api.goalSectionChoice(input),
  path: (input) => api.curriculumPath(input),
  setDepth: (input) => api.curriculumSetDepth(input),
  override: (input) => api.curriculumPathOverride(input),
  setScope: (input) => api.curriculumSetScope(input),
  scopeDecide: (input) => api.curriculumScopeDecide(input),
};

/** While the path is being judged or its coverage checked, the band is read again this often (a design value:
 *  the judgment runs in the background and the view never waits on it). */
export const BAND_RECHECK_MS = 6000;
/** The longest delay a browser timer keeps (2^31 - 1 ms); a later deadline is waited for in steps. */
const LONGEST_TIMER_MS = 2 ** 31 - 1;

/** The query cache entry the lens watches: the app's writes mark these tags stale (an answer, a goal paused or
 *  ended, a source imported or switched, the vault changed on disk), and the band and goals are read again. */
const WATCH_KEY = ["goal-lens:state-changes"] as const;
const WATCH_TAGS = [TAG.goals, TAG.queue, TAG.sources, TAG.vault, TAG.graph];

export function watchStateChanges(onChange: () => void): () => void {
  setQueryData(WATCH_KEY, 0, WATCH_TAGS);
  let seen = peek(WATCH_KEY).invalidatedAt;
  return subscribe(WATCH_KEY, () => {
    const state = peek(WATCH_KEY);
    if (state.invalidatedAt <= seen) return;
    seen = state.invalidatedAt;
    // Fresh again, so the next write marks it stale again (a stale entry ignores another invalidation's stamp).
    setQueryData(WATCH_KEY, 0, WATCH_TAGS);
    onChange();
  });
}
const DIM_KEY = "learnloop.desks.goalDim";

/** The learner's primary active goal (spec §12.1: goals_list, by priority). */
export function primaryGoalId(goals: GoalsListSnapshot["goals"] | null): string | null {
  const active = (goals ?? []).filter((goal) => goal.status === "active");
  active.sort((a, b) => (b.priority - a.priority) || a.id.localeCompare(b.id));
  return active[0]?.id ?? null;
}

function readDim(): boolean {
  try {
    return window.localStorage.getItem(DIM_KEY) !== "off";
  } catch {
    return true;
  }
}

function writeDim(on: boolean): void {
  try {
    window.localStorage.setItem(DIM_KEY, on ? "on" : "off");
  } catch {
    /* remembered per machine when storage allows */
  }
}

export interface WhyState {
  section: GoalLensSectionDto;
  /** The passage whose mark opened it (the section's other passages' marks stay at rest). */
  spanId?: string;
  extractionId: string;
  windowId: string;
  rect: { left: number; top: number; right: number; bottom: number };
}

export interface GoalLensState {
  goalId: string | null;
  goals: GoalsListSnapshot["goals"] | null;
  /** The chooser's protected labels by goal id (null until read, or when the read failed). */
  labels: Record<string, string> | null;
  band: GoalBandDto | null;
  indexFor: (extractionId: string) => LensIndex | null;
  dimOn: boolean;
  toggleDim: () => void;
  pathOpen: boolean;
  setPathOpen: (open: boolean) => void;
  why: WhyState | null;
  showWhy: (why: WhyState | null) => void;
  setDepth: (depth: ReadingPathDepth) => void;
  readAnyway: (extractionId: string, sectionId: string, on: boolean) => void;
  override: (learningObjectId: string, choice: DeliverablePathChoice, sectionRef?: string) => void;
  mapIt: () => void;
  addPhrase: (phrase: string) => void;
  /** The learner's words on what the goal's scope is missing or does not need (curriculum.set_scope, a correction). */
  correctScope: (text: string) => void;
  refresh: () => void;
}

/** `readings`: the readings shown in windows that are not paused (a paused window asks for nothing). */
export function useGoalLens({ transport, deskGoalId, off = false, readings, timers, mintId, onError }: {
  transport: GoalTransport;
  deskGoalId: string | null | undefined;
  /** The learner chose "no goal" for this desk: the lens is off. */
  off?: boolean;
  readings: readonly string[];
  timers: Timers;
  mintId: (prefix: string) => string;
  onError: (message: string) => void;
}): GoalLensState {
  const [goals, setGoals] = useState<GoalsListSnapshot["goals"] | null>(null);
  // Each goal's label as the chooser shows it: the learner's words with a held topic's name masked by the server.
  const [labels, setLabels] = useState<Record<string, string> | null>(null);
  const [band, setBand] = useState<GoalBandDto | null>(null);
  const [lenses, setLenses] = useState<Record<string, GoalLensDto>>({});
  const [generation, setGeneration] = useState(0);
  const [dimOn, setDimOn] = useState(readDim);
  const [pathOpen, setPathOpen] = useState(false);
  const [why, showWhy] = useState<WhyState | null>(null);
  const asked = useRef(new Set<string>());
  // Each lens request's ticket: a reply installs only while it is the latest asked for its reading under the goal
  // shown (an older reply, from another goal or before a depth or choice changed, is dropped).
  const tickets = useRef(new Map<string, number>());
  const ticket = useRef(0);
  const goalRef = useRef<string | null>(null);
  const [goalsAsked, setGoalsAsked] = useState(0);
  // The goal and path state each owed judgment was started for (once each: a judgment that does not start leaves
  // the band as it is, never a loop of starts).
  const started = useRef(new Set<string>());
  // The callers' callbacks may be new on every render: read through refs, so no effect runs again for them.
  const onErrorRef = useRef(onError);
  onErrorRef.current = onError;
  const report = useCallback((message: string) => onErrorRef.current(message), []);
  const judged = useRef(new Set<string>());

  useEffect(() => {
    let live = true;
    // A transport that cannot list goals (none wired) leaves the desks without a lens, never broken.
    Promise.resolve().then(() => transport.goals()).then((snapshot) => { if (live) setGoals(snapshot.goals); }, () => { if (live) setGoals((now) => now ?? []); });
    // A failed read leaves the labels unknown: the chooser then names goals neutrally, never by a raw sentence.
    if (transport.choices) {
      const choices = transport.choices;
      Promise.resolve().then(() => choices()).then((reply) => {
        if (live) setLabels(Object.fromEntries(reply.goals.map((goal) => [goal.goalId, goal.label])));
      }, () => { if (live) setLabels(null); });
    }
    return () => { live = false; };
  }, [transport, goalsAsked]);

  const goalId = off ? null : deskGoalId ?? (goals ? primaryGoalId(goals) : null);
  goalRef.current = goalId;

  // Another goal: nothing of the last one's stays shown, the why card included.
  useEffect(() => {
    setBand(null);
    setLenses({});
    asked.current.clear();
    tickets.current.clear();
    showWhy(null);
  }, [goalId]);

  // A write elsewhere in the app (an answer, a goal paused or ended, a source changed) reads the goals, the band
  // and the readings again: what a due check hides, and the goal itself, may have changed.
  useEffect(() => watchStateChanges(() => {
    setGoalsAsked((value) => value + 1);
    setGeneration((value) => value + 1);
  }), []);

  // A goal opened: start what it owes (coverage, then the path judgment) once per session, then read its band.
  // A refresh (a choice, a depth, the background work moving on) reads the band and the readings again.
  useEffect(() => {
    if (!goalId) return;
    let live = true;
    if (!judged.current.has(goalId)) {
      judged.current.add(goalId);
      transport.path({ goalId, judge: true }).catch(() => undefined);
    }
    asked.current.clear();
    transport.band({ goalId }).then((next) => { if (live) setBand(next); }, (error: { code?: string }) => {
      // The curriculum switched off: no band and no lens, as the Reader without it.
      if (live && error?.code !== "curriculum_disabled") report("Couldn’t open your goal. Choose it again to retry.");
    });
    return () => { live = false; };
  }, [goalId, transport, generation, report]);

  // The band again while its path is judged or its coverage checked in the background. A path owing a judgment
  // with nothing running (coverage just finished: the open's one curriculum.path started only the coverage) starts
  // it, once per path state; one that did not start is not polled for ever.
  useEffect(() => {
    if (!goalId || !band) return;
    const covering = Boolean(band.coverage?.covering);
    const owed = !covering && (band.status === "pending" || band.status === "stale");
    const key = `${goalId}|${band.path?.stateKey ?? ""}`;
    if (owed && !started.current.has(key)) {
      started.current.add(key);
      let live = true;
      transport.path({ goalId, judge: true }).then(() => { if (live) setGeneration((value) => value + 1); }, () => undefined);
      return () => { live = false; };
    }
    if (band.status !== "judging" && !covering) return;
    const handle = timers.set(() => setGeneration((value) => value + 1), BAND_RECHECK_MS);
    return () => timers.clear(handle);
  }, [goalId, band, timers, transport]);

  // The band again when the next check falls due: from then it hides what that check covers.
  useEffect(() => {
    const due = band?.nextCheckDue ? Date.parse(band.nextCheckDue) : NaN;
    if (!goalId || Number.isNaN(due)) return;
    const wait = Math.max(0, due - timers.now());
    const handle = timers.set(() => setGeneration((value) => value + 1), Math.min(wait + 1, LONGEST_TIMER_MS));
    return () => timers.clear(handle);
  }, [goalId, band, timers]);

  // One whole-reading goal.lens per reading in view; ranges are filtered here, never asked.
  const readingsKey = [...new Set(readings)].sort().join("|");
  useEffect(() => {
    if (!goalId || !band || band.status === "not_a_deliverable") return;
    const shown = new Set(readingsKey ? readingsKey.split("|") : []);
    // A reading no window shows (paused, closed) is asked again when it comes back: its levels may be old by then.
    for (const extractionId of [...asked.current]) if (!shown.has(extractionId)) asked.current.delete(extractionId);
    for (const extractionId of shown) {
      if (asked.current.has(extractionId)) continue;
      asked.current.add(extractionId);
      const mine = ++ticket.current;
      tickets.current.set(extractionId, mine);
      const current = () => goalRef.current === goalId && tickets.current.get(extractionId) === mine;
      transport.lens({ goalId, extractionId }).then(
        (lens) => { if (current()) setLenses((now) => ({ ...now, [extractionId]: lens })); },
        () => { if (current()) asked.current.delete(extractionId); },
      );
    }
  }, [goalId, band, readingsKey, transport]);

  const indexes = useMemo(() => {
    const out: Record<string, LensIndex | null> = {};
    for (const [extractionId, lens] of Object.entries(lenses)) out[extractionId] = indexLens(lens);
    return out;
  }, [lenses]);
  const indexFor = useCallback((extractionId: string) => indexes[extractionId] ?? null, [indexes]);
  // An open why card shows its section as the latest lens has it (a refresh may hold or settle it), and closes when
  // the section is no longer there.
  const whyNow = useMemo(() => {
    if (!why) return null;
    const section = indexes[why.extractionId]?.sections.find((each) => each.sectionId === why.section.sectionId);
    return section ? (section === why.section ? why : { ...why, section }) : null;
  }, [why, indexes]);

  const refresh = useCallback(() => setGeneration((value) => value + 1), []);
  const toggleDim = useCallback(() => setDimOn((on) => { writeDim(!on); return !on; }), []);

  const setDepth = useCallback((depth: ReadingPathDepth) => {
    if (!goalId) return;
    transport.setDepth({ goalId, depth }).then(refresh, () => report("Couldn’t change the depth. Open Path and try again."));
  }, [goalId, transport, refresh, report]);

  const readAnyway = useCallback((extractionId: string, sectionId: string, on: boolean) => {
    if (!goalId) return;
    transport.sectionChoice({ goalId, extractionId, sectionId, choice: on ? "read_anyway" : "none", operationId: mintId("glc") })
      .then(refresh, () => report("Couldn’t save this choice. Reopen Path and try again."));
  }, [goalId, transport, mintId, refresh, report]);

  const override = useCallback((learningObjectId: string, choice: DeliverablePathChoice, sectionRef?: string) => {
    if (!goalId) return;
    transport.override({ goalId, learningObjectId, choice, ...(sectionRef ? { sectionRef } : {}) })
      .then(refresh, () => report("Couldn’t save this choice. Reopen Path and try again."));
  }, [goalId, transport, refresh, report]);

  const mapIt = useCallback(() => {
    if (!goalId || !band) return;
    transport.setScope({ goalId, kind: "text", text: band.goal.sentence })
      .then(refresh, () => report("Couldn’t find reading for this goal. Try again or change the topics in Goals."));
  }, [goalId, band, transport, refresh, report]);

  const addPhrase = useCallback((phrase: string) => {
    if (!goalId) return;
    transport.scopeDecide({ goalId, phrase, decision: "create" })
      .then(refresh, () => report("Couldn’t add this topic. Reopen Path and try again."));
  }, [goalId, transport, refresh, report]);

  const correctScope = useCallback((text: string) => {
    if (!goalId) return;
    transport.setScope({ goalId, kind: "correction", text })
      .then(refresh, () => report("Couldn’t change the goal’s topics. Reopen Path and try again."));
  }, [goalId, transport, refresh, report]);

  return { goalId, goals, labels, band, indexFor, dimOn, toggleDim, pathOpen, setPathOpen, why: whyNow, showWhy, setDepth, readAnyway, override, mapIt, addPhrase, correctScope, refresh };
}
