// Algorithm-owned display constants, sourced from the sidecar's config payload
// so the frontend never duplicates algorithm opinions. The fallbacks mirror the
// backend defaults in src/learnloop/config.py and only apply before the first
// app snapshot arrives (or against a sidecar that predates these fields).

export interface AlgoDisplayConfig {
  /** Mastery mean above which the UI renders "strong" (green). */
  masteryStrongThreshold: number;
  /** Mastery mean above which the UI renders "developing" (amber); below is red. */
  masteryDevelopingThreshold: number;
  /** Surprise threshold τ (nats) used when a feedback bundle lacks its own. */
  tauFollowupNats: number;
  /** Operating point of the continuous follow-up gate score. */
  gateScoreThreshold: number;
  /** mvp-0.13: the answer surfaces offer "I'm stuck" (write what you can)
   *  instead of "I don't know". The sidecar decides (algorithm version +
   *  the `stuck_prompt.enabled` kill switch); false until it says so. */
  stuckPrompt: boolean;
  /** UX Phase 4's kill switch (`[ui] practice_feedback`, display only): the
   *  simple practice card, feedback, short-check results, repair step and
   *  session finish, or "classic" for the screens exactly as they were. */
  practiceFeedback: "simple" | "classic";
  /** Reader workbench RW2a's kill switch (`workbench.enabled`): the sidecar
   *  sends a `workbench` key only while it is on, so false until it says so,
   *  and off leaves every screen exactly as before RW2a. */
  workbench: boolean;
}

const DEFAULTS: AlgoDisplayConfig = {
  masteryStrongThreshold: 0.6,
  masteryDevelopingThreshold: 0.35,
  tauFollowupNats: 0.05,
  gateScoreThreshold: 0.5,
  stuckPrompt: false,
  practiceFeedback: "simple",
  workbench: false
};

let current: AlgoDisplayConfig = { ...DEFAULTS };

export function setAlgoConfig(config: unknown): void {
  const root = (config ?? {}) as {
    mastery?: { displayStrongThreshold?: unknown; displayDevelopingThreshold?: unknown };
    scheduler?: { followup?: { tauFollowupNats?: unknown; gateScoreThreshold?: unknown } };
    practice?: { stuckPrompt?: unknown };
    ui?: { practiceFeedback?: unknown };
    workbench?: { enabled?: unknown };
  };
  current = {
    masteryStrongThreshold: asNumber(root.mastery?.displayStrongThreshold, DEFAULTS.masteryStrongThreshold),
    masteryDevelopingThreshold: asNumber(root.mastery?.displayDevelopingThreshold, DEFAULTS.masteryDevelopingThreshold),
    tauFollowupNats: asNumber(root.scheduler?.followup?.tauFollowupNats, DEFAULTS.tauFollowupNats),
    gateScoreThreshold: asNumber(root.scheduler?.followup?.gateScoreThreshold, DEFAULTS.gateScoreThreshold),
    stuckPrompt: root.practice?.stuckPrompt === true,
    // The sidecar's default; only its other value turns it off.
    practiceFeedback: root.ui?.practiceFeedback === "classic" ? "classic" : "simple",
    workbench: root.workbench?.enabled === true
  };
}

/** The one prompt "I'm stuck" opens the answer box with (mirrors
 *  learnloop.attempts.stuck.STUCK_PROMPT_TEXT). */
export const STUCK_PROMPT_TEXT = "Write what you can, or what's confusing you";

export function algoConfig(): AlgoDisplayConfig {
  return current;
}

export type MasteryBand = "strong" | "developing" | "weak";

export function masteryBand(mastery: number): MasteryBand {
  if (mastery > current.masteryStrongThreshold) return "strong";
  if (mastery > current.masteryDevelopingThreshold) return "developing";
  return "weak";
}

/** Maps a mastery mean to the palette's green/amber/red for the given screen. */
export function masteryTone<T>(mastery: number, palette: { green: T; amber: T; red: T }): T {
  const band = masteryBand(mastery);
  return band === "strong" ? palette.green : band === "developing" ? palette.amber : palette.red;
}

function asNumber(value: unknown, fallback: number): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}
