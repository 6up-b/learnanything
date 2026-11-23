// The goal lens's state on the desks (spec §12.1-§12.5): which goal, its band, one whole-reading goal.lens per
// reading in view (filtered client-side), dimming, the path view and the why card. Reads only; the writes are the
// learner's own choices (the depth, a path line's choice, read it anyway), through the RPCs that own them.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../../../api/client";
import type {
  DeliverablePathChoice,
  GoalBandDto,
  GoalLensDto,
  GoalLensInput,
  GoalLensSectionDto,
  GoalSectionChoiceDto,
  GoalSectionChoiceInput,
  GoalsListSnapshot,
  ReadingPathDepth,
} from "../../../api/dto";
import type { Timers } from "../keys/router";
import { indexLens, type LensIndex } from "./model";

/** The goal lens's calls; absent, the sidecar's. */
export interface GoalTransport {
  goals: () => Promise<GoalsListSnapshot>;
  band: (input: { goalId: string }) => Promise<GoalBandDto>;
  lens: (input: GoalLensInput) => Promise<GoalLensDto>;
  sectionChoice: (input: GoalSectionChoiceInput) => Promise<GoalSectionChoiceDto>;
  /** curriculum.path with judge: true starts the coverage and the path judgment the goal owes (background). */
  path: (input: { goalId: string; judge?: boolean }) => Promise<unknown>;
  setDepth: (input: { goalId: string; depth: ReadingPathDepth }) => Promise<unknown>;
  override: (input: { goalId: string; learningObjectId: string; choice: DeliverablePathChoice; sectionRef?: string }) => Promise<unknown>;
  /** "map it": the goal's own sentence as its first scope input (curriculum.set_scope; a pressed action). */
  setScope: (input: { goalId: string; kind: "text"; text: string }) => Promise<unknown>;
  /** "add it" on a phrase not in the library (curriculum.scope_decide: the learner's yes creates the LO). */
  scopeDecide: (input: { goalId: string; phrase: string; decision: "create" | "decline" }) => Promise<unknown>;
}

export const LIVE_GOAL_TRANSPORT: GoalTransport = {
  goals: () => api.goalsList(),
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
  const [band, setBand] = useState<GoalBandDto | null>(null);
  const [lenses, setLenses] = useState<Record<string, GoalLensDto>>({});
  const [generation, setGeneration] = useState(0);
  const [dimOn, setDimOn] = useState(readDim);
  const [pathOpen, setPathOpen] = useState(false);
  const [why, showWhy] = useState<WhyState | null>(null);
  const asked = useRef(new Set<string>());
  // The callers' callbacks may be new on every render: read through refs, so no effect runs again for them.
  const onErrorRef = useRef(onError);
  onErrorRef.current = onError;
  const report = useCallback((message: string) => onErrorRef.current(message), []);
  const judged = useRef(new Set<string>());

  useEffect(() => {
    let live = true;
    // A transport that cannot list goals (none wired) leaves the desks without a lens, never broken.
    Promise.resolve().then(() => transport.goals()).then((snapshot) => { if (live) setGoals(snapshot.goals); }, () => { if (live) setGoals([]); });
    return () => { live = false; };
  }, [transport]);

  const goalId = off ? null : deskGoalId ?? (goals ? primaryGoalId(goals) : null);

  // Another goal: nothing of the last one's stays shown.
  useEffect(() => {
    setBand(null);
    setLenses({});
    asked.current.clear();
  }, [goalId]);

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
    transport.band({ goalId }).then((next) => { if (live) setBand(next); }, (error: { code?: string; message?: string }) => {
      // The curriculum switched off: no band and no lens, as the Reader without it.
      if (live && error?.code !== "curriculum_disabled") report(error?.message ?? "Couldn't read your goal.");
    });
    return () => { live = false; };
  }, [goalId, transport, generation, report]);

  // The band again while its path is judged or its coverage checked in the background.
  useEffect(() => {
    if (!goalId || !band) return;
    const waiting = band.status === "judging" || band.status === "pending" || Boolean(band.coverage?.covering);
    if (!waiting) return;
    const handle = timers.set(() => setGeneration((value) => value + 1), BAND_RECHECK_MS);
    return () => timers.clear(handle);
  }, [goalId, band, timers]);

  // One whole-reading goal.lens per reading in view; ranges are filtered here, never asked.
  const readingsKey = [...new Set(readings)].sort().join("|");
  useEffect(() => {
    if (!goalId || !band || band.status === "not_a_deliverable") return;
    for (const extractionId of readingsKey ? readingsKey.split("|") : []) {
      if (asked.current.has(extractionId)) continue;
      asked.current.add(extractionId);
      transport.lens({ goalId, extractionId }).then(
        (lens) => setLenses((now) => ({ ...now, [extractionId]: lens })),
        () => asked.current.delete(extractionId),
      );
    }
  }, [goalId, band, readingsKey, transport]);

  const indexes = useMemo(() => {
    const out: Record<string, LensIndex | null> = {};
    for (const [extractionId, lens] of Object.entries(lenses)) out[extractionId] = indexLens(lens);
    return out;
  }, [lenses]);
  const indexFor = useCallback((extractionId: string) => indexes[extractionId] ?? null, [indexes]);

  const refresh = useCallback(() => setGeneration((value) => value + 1), []);
  const toggleDim = useCallback(() => setDimOn((on) => { writeDim(!on); return !on; }), []);

  const setDepth = useCallback((depth: ReadingPathDepth) => {
    if (!goalId) return;
    transport.setDepth({ goalId, depth }).then(refresh, (error: { message?: string }) => report(error?.message ?? "Couldn't set the depth."));
  }, [goalId, transport, refresh, report]);

  const readAnyway = useCallback((extractionId: string, sectionId: string, on: boolean) => {
    if (!goalId) return;
    transport.sectionChoice({ goalId, extractionId, sectionId, choice: on ? "read_anyway" : "none", operationId: mintId("glc") })
      .then(refresh, (error: { message?: string }) => report(error?.message ?? "Couldn't keep that choice."));
  }, [goalId, transport, mintId, refresh, report]);

  const override = useCallback((learningObjectId: string, choice: DeliverablePathChoice, sectionRef?: string) => {
    if (!goalId) return;
    transport.override({ goalId, learningObjectId, choice, ...(sectionRef ? { sectionRef } : {}) })
      .then(refresh, (error: { message?: string }) => report(error?.message ?? "Couldn't keep that choice."));
  }, [goalId, transport, refresh, report]);

  const mapIt = useCallback(() => {
    if (!goalId || !band) return;
    transport.setScope({ goalId, kind: "text", text: band.goal.sentence })
      .then(refresh, (error: { message?: string }) => report(error?.message ?? "Couldn't map this goal."));
  }, [goalId, band, transport, refresh, report]);

  const addPhrase = useCallback((phrase: string) => {
    if (!goalId) return;
    transport.scopeDecide({ goalId, phrase, decision: "create" })
      .then(refresh, (error: { message?: string }) => report(error?.message ?? "Couldn't add it."));
  }, [goalId, transport, refresh, report]);

  return { goalId, goals, band, indexFor, dimOn, toggleDim, pathOpen, setPathOpen, why, showWhy, setDepth, readAnyway, override, mapIt, addPhrase, refresh };
}
