// The Reader's one check-offer rule (reading-hardening, part 2), as a pure
// function: every offer path calls it (ReaderScreen.checkOffer.test.tsx drives
// each path through the real component).
import { describe, expect, it } from "vitest";
import { checkOffer, type SectionCheckOffer } from "./checkOffer";

const after: SectionCheckOffer = {
  kind: "section",
  readingPhase: "after_section",
  available: true,
  settled: false,
  pinned: false,
  position: "current",
  readingMoved: true,
  surface: "text",
  progress: 1,
  atLastPage: null,
  firstPassageShare: 0.25,
};

function offer(patch: Partial<SectionCheckOffer>) {
  return checkOffer({ ...after, ...patch });
}

describe("a resumed check after a section", () => {
  it("waits for reading in this visit on every surface, however far the marker stands", () => {
    for (const surface of ["text", "pdf", "watch"] as const) {
      expect(offer({ surface, readingMoved: false, progress: 1, atLastPage: true })).toEqual({
        offer: false, reason: "not_read_this_visit",
      });
    }
  });

  it("is offered once the learner reads at its point", () => {
    expect(offer({ surface: "text", progress: 0.7 }).offer).toBe(true);
    expect(offer({ surface: "pdf", atLastPage: true, progress: 0.1 }).offer).toBe(true);
    expect(offer({ surface: "watch", progress: 0.9 }).offer).toBe(true);
  });

  it("an auto-authored check is an after-section check: the text view no longer opens it at once", () => {
    // Auto-authored checks are placed after_section; a resume into their
    // section offers nothing until the learner reads.
    expect(offer({ surface: "text", readingMoved: false }).offer).toBe(false);
  });
});

describe("the original PDF", () => {
  it("offers nothing while its manifest is pending, on any section", () => {
    for (const position of ["behind", "current"] as const) {
      expect(offer({ surface: "loading", position, readingMoved: true })).toEqual({
        offer: false, reason: "surface_loading",
      });
    }
  });

  it("waits for the section's last page (D22), not 70 %", () => {
    expect(offer({ surface: "pdf", atLastPage: false, progress: 0.9 })).toEqual({
      offer: false, reason: "not_at_its_point",
    });
  });

  it("without page information falls back to 70 % of the section", () => {
    expect(offer({ surface: "pdf", atLastPage: null, progress: 0.69 }).offer).toBe(false);
    expect(offer({ surface: "pdf", atLastPage: null, progress: 0.7 }).offer).toBe(true);
  });

  it("a manifest that failed or is unavailable reads as the text view, still needing reading", () => {
    expect(offer({ surface: "text", readingMoved: false, progress: 1 }).offer).toBe(false);
    expect(offer({ surface: "text", readingMoved: true, progress: 1 }).offer).toBe(true);
  });
});

describe("sections behind and ahead", () => {
  it("a check left behind the reading position waits for reading in this visit", () => {
    expect(offer({ position: "behind", readingMoved: false })).toEqual({ offer: false, reason: "not_read_this_visit" });
    expect(offer({ position: "behind", readingMoved: true, progress: 0 })).toEqual({ offer: true, reason: "offered" });
  });

  it("a section ahead is never offered", () => {
    expect(offer({ position: "ahead" })).toEqual({ offer: false, reason: "ahead" });
  });
});

describe("before and during a section follow their own points", () => {
  it("before: at the section's start", () => {
    expect(offer({ readingPhase: "before_section", progress: 0.2, readingMoved: false }).offer).toBe(true);
    expect(offer({ readingPhase: "before_section", progress: 0.5 }).offer).toBe(false);
    // A one-passage-in-four section counts its whole first passage as the start.
    expect(offer({ readingPhase: "before_section", progress: 0.3, firstPassageShare: 0.5 }).offer).toBe(true);
  });

  it("during: from 45 %", () => {
    expect(offer({ readingPhase: "during_section", progress: 0.44 }).offer).toBe(false);
    expect(offer({ readingPhase: "during_section", progress: 0.45 }).offer).toBe(true);
  });
});

describe("what always wins", () => {
  it("a pinned check stays offered, even after a jump or while the original reloads", () => {
    expect(offer({ pinned: true, readingMoved: false, surface: "loading", position: "ahead" })).toEqual({
      offer: true, reason: "pinned",
    });
  });

  it("nothing is offered without a check, when checks are off, or once it is settled", () => {
    expect(offer({ readingPhase: null }).reason).toBe("no_check");
    expect(offer({ available: false, pinned: true }).reason).toBe("unavailable");
    expect(offer({ settled: true, pinned: true }).reason).toBe("settled");
  });
});

describe("RW1a's passage-scoped quick check", () => {
  it("is offered on an open inquiry the learner raised in this visit, never while skimming", () => {
    expect(checkOffer({ kind: "passage", raisedThisVisit: true, inquiryOpen: true, muted: false }).offer).toBe(true);
    expect(checkOffer({ kind: "passage", raisedThisVisit: false, inquiryOpen: true, muted: false }).reason).toBe("not_raised");
    expect(checkOffer({ kind: "passage", raisedThisVisit: true, inquiryOpen: false, muted: false }).reason).toBe("inquiry_closed");
    expect(checkOffer({ kind: "passage", raisedThisVisit: true, inquiryOpen: true, muted: true }).reason).toBe("muted");
  });
});
