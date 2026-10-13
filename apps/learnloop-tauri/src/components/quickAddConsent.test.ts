// The deliberate Quick add path asks for consent only where the learner has not
// already said OK once to the provider (UX Phase 1, Q4; spec §10 item 1.7).
import { describe, expect, it } from "vitest";
import { initialConsentTicks } from "./quickAddConsent";

describe("initialConsentTicks", () => {
  it("ticks what the learner already agreed to, nothing else", () => {
    expect(
      initialConsentTicks([
        { kind: "network_fetch", stage: "extraction" },
        { kind: "external_ai_synthesis", stage: "synthesis", granted: true, grantedAt: "2026-10-13T09:00:00Z" }
      ])
    ).toEqual([false, true]);
  });
});
