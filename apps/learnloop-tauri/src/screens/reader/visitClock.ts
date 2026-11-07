// A Reader visit's clock (reader workbench RW1a; moved here so the phone's Reader keeps the same one, mobile v2
// V4, Codex review F8). Pure: no API, no React. A visit's time since it opened is either active or idle: a gap
// shorter than VISIT_IDLE_MS between two touches (scrolling, selecting, typing) is active, a longer one idle. Its
// close reports both in whole seconds (`reader_view_closed`), which the router's activity clock reads
// (`router_objective.price.activity_spans`, `decision_state._reader_visits`).

/** A gap this long without scrolling, selecting or typing counts as idle. */
export const VISIT_IDLE_MS = 120_000;

export interface VisitClock {
  lastActive: number;
  active: number;
  idle: number;
}

/** The gap since the last touch, counted as active or idle; `now` is the new last touch. */
export function accrueVisit(visit: VisitClock, now: number): void {
  const gap = now - visit.lastActive;
  if (gap < VISIT_IDLE_MS) visit.active += gap;
  else visit.idle += gap;
  visit.lastActive = now;
}

/** The close event's two numbers, in whole seconds. */
export function visitSeconds(visit: VisitClock): { active_seconds: number; idle_seconds: number } {
  return { active_seconds: Math.round(visit.active / 1000), idle_seconds: Math.round(visit.idle / 1000) };
}
