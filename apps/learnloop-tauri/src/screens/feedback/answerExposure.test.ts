// UX Phase 4 round 3 F1 (docs/reviews/ux-phase4-feedback-codex-review.md §9):
// the screen's half of the exposure invariant, on random timelines. The
// production gate (`AnswerExposureGate`) runs against a simulated clock and a
// simulated ledger: writes that land after a delay, fail, or land while their
// acknowledgement is lost; the answer wanted and not (hidden, covered); the
// learner present and away; machine sleeps with no ticks; and a crash (the
// run just stops). At every check, whenever the gate lets the answer be on
// screen, the ledger already holds a committed row stamped s <= now with
// now + one tick < s + G (G the renewal grace the readers add to the horizon).
// The readers' half (a committed row counts at every T in [s, s + D + G]) is
// `tests/test_ux_phase4_feedback.py::test_f1g_every_committed_display_row_counts_until_its_coverage_ends`.
import { describe, expect, it } from "vitest";
import contract from "./exposureContract.json";
import { AnswerExposureGate, EXPOSURE } from "./answerExposure";

const SECOND = 1000;
const MINUTE = 60 * SECOND;
const HOUR = 60 * MINUTE;

/** A small seeded PRNG (mulberry32): the runs are reproducible. */
function rng(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

interface Simulated {
  now: number;
  committed: Map<string, number>;
  inflight: { due: number; settle: () => void }[];
  /** The order in which each display id was first sent. */
  sent: Map<string, number>;
}

/** The simulated ledger: a write lands after `latency`, or fails (nothing
 *  written), or lands with its acknowledgement lost (a retry of the same id
 *  then reads the row it wrote). Stamps are floored to the second, as the
 *  sidecar's are. */
function ledger(sim: Simulated, random: () => number, failRate: number) {
  return (displayId: string) =>
    new Promise<{ recordedAt: string; alreadyRecorded: boolean }>((resolve, reject) => {
      if (!sim.sent.has(displayId)) sim.sent.set(displayId, sim.sent.size + 1);
      const latency = random() < 0.9 ? 20 + random() * 400 : 2 * SECOND + random() * 20 * SECOND;
      sim.inflight.push({
        due: sim.now + latency,
        settle: () => {
          const outcome = random();
          const existing = sim.committed.get(displayId);
          if (existing !== undefined) {
            resolve({ recordedAt: new Date(existing).toISOString(), alreadyRecorded: true });
            return;
          }
          if (outcome < failRate) {
            reject({ code: "display_not_recorded", retryable: true });
            return;
          }
          const stamp = Math.floor(sim.now / SECOND) * SECOND;
          sim.committed.set(displayId, stamp);
          if (outcome < failRate * 1.5) {
            reject({ code: "sidecar_unavailable", retryable: true });
            return;
          }
          resolve({ recordedAt: new Date(stamp).toISOString(), alreadyRecorded: false });
        }
      });
    });
}

async function settleDue(sim: Simulated): Promise<void> {
  const due = sim.inflight.filter((write) => write.due <= sim.now);
  sim.inflight = sim.inflight.filter((write) => write.due > sim.now);
  for (const write of due) write.settle();
  for (let i = 0; i < 6; i += 1) await Promise.resolve();
}

/** A committed row covers now, and (round 4) its write began after the last
 *  interruption (a lifecycle signal or a clock discontinuity): `interruptedAt`
 *  counts the writes begun before it. */
function coveredByLedger(sim: Simulated, interruptedAt = 0): boolean {
  for (const [id, stamp] of sim.committed) {
    if ((sim.sent.get(id) ?? 0) <= interruptedAt) continue;
    if (stamp <= sim.now && sim.now + EXPOSURE.tickMs < stamp + EXPOSURE.renewalGraceMs) return true;
  }
  return false;
}

describe("the full answer's exposure gate (round 3 F1)", () => {
  it("shares its numbers with the readers and renews before a row's grace ends", () => {
    expect(EXPOSURE).toEqual(contract);
    // A renewal due at renewAfter, checked a tick late, still lands before the gate hides.
    expect(EXPOSURE.renewAfterMs + EXPOSURE.tickMs).toBeLessThan(EXPOSURE.renewalGraceMs - EXPOSURE.showMarginMs);
    // The gate's own slack (a check a tick late) stays inside the grace.
    expect(EXPOSURE.tickMs).toBeLessThan(EXPOSURE.showMarginMs);
  });

  it.each(Array.from({ length: 24 }, (_, seed) => seed))(
    "never lets the answer be on screen without a committed row that covers it (seed %i)",
    async (seed) => {
      const random = rng(seed + 1);
      const sim: Simulated = { now: Date.UTC(2026, 9, 1, 8), committed: new Map(), inflight: [], sent: new Map() };
      const gate = new AnswerExposureGate(ledger(sim, random, 0.15 + random() * 0.3), () => sim.now);
      let wanted = true;
      let checks = 0;
      let shownChecks = 0;
      let interruptedAt = 0;
      const end = sim.now + (2 + Math.floor(random() * 3)) * 24 * HOUR;
      while (sim.now < end) {
        const roll = random();
        if (roll < 0.003) {
          // Asleep: no ticks, no events, for minutes to two days.
          sim.now += Math.floor(random() * 48 * HOUR);
        } else if (roll < 0.0035) {
          // A crash: this window's run ends here; nothing more is written.
          break;
        } else if (roll < 0.01) {
          // A lifecycle signal (hidden, pagehide, freeze, blur, minimized).
          gate.interrupt();
          interruptedAt = sim.sent.size;
        } else if (roll < 0.012) {
          // The wall clock goes back (up to five minutes): a discontinuity.
          sim.now -= Math.floor(random() * 5 * MINUTE);
          interruptedAt = sim.sent.size;
        } else if (roll < 0.05) {
          wanted = !wanted;
          if (wanted) gate.activity();
        } else if (roll < 0.1) {
          gate.activity();
        }
        sim.now += roll < 0.9 ? EXPOSURE.tickMs : Math.floor(random() * 30 * MINUTE);
        await settleDue(sim);
        const shown = gate.check(wanted) && wanted;
        checks += 1;
        if (shown) {
          shownChecks += 1;
          expect(coveredByLedger(sim, interruptedAt)).toBe(true);
        }
        if (gate.covered()) expect(coveredByLedger(sim, interruptedAt)).toBe(true);
      }
      expect(checks).toBeGreaterThan(0);
      // Not trivially safe: the answer is on screen for part of the run.
      if (checks > 200) expect(shownChecks).toBeGreaterThan(checks / 20);
    }
  );

  it("keeps an answer in use on screen, renewing before its grace ends", async () => {
    const random = rng(99);
    const sim: Simulated = { now: Date.UTC(2026, 9, 1, 8), committed: new Map(), inflight: [], sent: new Map() };
    const gate = new AnswerExposureGate(ledger(sim, random, 0), () => sim.now);
    let shown = 0;
    let checks = 0;
    for (let step = 0; step < (50 * HOUR) / EXPOSURE.tickMs; step += 1) {
      sim.now += EXPOSURE.tickMs;
      if (step % 120 === 0) gate.activity(); // every ten minutes
      await settleDue(sim);
      if (gate.check(true)) shown += 1;
      checks += 1;
    }
    // On screen all but the first check (its row is still being written).
    expect(checks - shown).toBeLessThanOrEqual(2);
    // About one row per renewal interval: 50 hours at 40 minutes, plus the first.
    expect(sim.committed.size).toBeGreaterThanOrEqual(70);
    expect(sim.committed.size).toBeLessThanOrEqual(80);
  });

  it("lets an unattended screen's row lapse: hidden as away, one row, then back on return", async () => {
    const random = rng(7);
    const sim: Simulated = { now: Date.UTC(2026, 9, 1, 8), committed: new Map(), inflight: [], sent: new Map() };
    const gate = new AnswerExposureGate(ledger(sim, random, 0), () => sim.now);
    for (let step = 0; step < (3 * HOUR) / EXPOSURE.tickMs; step += 1) {
      sim.now += EXPOSURE.tickMs;
      await settleDue(sim);
      gate.check(true);
    }
    expect(sim.committed.size).toBe(1);
    expect(gate.covered()).toBe(false);
    expect(gate.status()).toBe("away");
    gate.activity();
    gate.check(true);
    sim.now += SECOND;
    await settleDue(sim);
    expect(gate.check(true)).toBe(true);
    expect(sim.committed.size).toBe(2);
  });

  it("stops on a refusal (the self-grade's draft is done with) and keeps the answer hidden", async () => {
    const sim: Simulated = { now: Date.UTC(2026, 9, 1, 8), committed: new Map(), inflight: [], sent: new Map() };
    let calls = 0;
    const gate = new AnswerExposureGate(
      () => {
        calls += 1;
        return Promise.reject({ code: "disclosure_not_pending", retryable: false });
      },
      () => sim.now
    );
    gate.check(true);
    for (let i = 0; i < 6; i += 1) await Promise.resolve();
    sim.now += 10 * MINUTE;
    gate.activity();
    expect(gate.check(true)).toBe(false);
    expect(gate.status()).toBe("unavailable");
    expect(calls).toBe(1);
  });
});
