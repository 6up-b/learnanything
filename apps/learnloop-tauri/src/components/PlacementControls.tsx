import { useState } from "react";
import { api } from "../api/client";
import type { CommandError, LearningObjectPlacementDto, PlacementReport } from "../api/dto";
import { COLOR, Faint, FONT_MONO, Pill, SectionHeader } from "./term";

// Learner field F2 (spec §5.2): starting new material without ceremony.
// "I know this", "too easy" and "I don't know this" are routing preferences,
// labelled as such: they act immediately and never write evidence. An LO
// marked assumed known shows "assumed (not tested)" until its first ordinary
// review checks it. "Check what I already know" is optional and never prompted.

export const ASSUMED_LABEL = "assumed (not tested)";

const linkStyle = (inactive: boolean) =>
  ({
    fontFamily: FONT_MONO,
    fontSize: 11,
    color: inactive ? COLOR.textFaint : COLOR.amberLink,
    textDecoration: "underline",
    textUnderlineOffset: 2,
    cursor: inactive ? "default" : "pointer",
    whiteSpace: "nowrap"
  }) as const;

function day(iso: string | null | undefined): string {
  return iso ? iso.slice(0, 10) : "";
}

/** "I know this" on a practice card: assumes the card's LO known (not tested). */
export function KnowThisAction({
  practiceItemId,
  onDone,
  onError
}: {
  practiceItemId: string;
  /** Called once the LO is marked assumed (the caller moves on). */
  onDone: () => void;
  onError: (message: string) => void;
}) {
  const [busy, setBusy] = useState(false);
  const run = async () => {
    if (busy) return;
    setBusy(true);
    try {
      await api.placementSelfReport({ report: "know_this", practiceItemId });
      onDone();
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <span
      role="button"
      onClick={() => void run()}
      title="skip this topic for now: it is assumed known (not tested), and its first review in two weeks is the check. A routing preference, not a grade."
      style={linkStyle(busy)}
    >
      {busy ? "…" : "✓ I know this"}
    </span>
  );
}

/** The LO inspector's placement section: label plus the three controls. */
export function PlacementSection({
  learningObjectId,
  placement,
  onChanged,
  onQuickCheck,
  onError
}: {
  learningObjectId: string;
  placement: LearningObjectPlacementDto;
  /** Re-fetch after a self-report. */
  onChanged: () => void;
  /** Start "Check what I already know" over these LOs (needs a session). */
  onQuickCheck?: (learningObjectIds: string[]) => void;
  onError: (message: string) => void;
}) {
  const [busy, setBusy] = useState(false);
  if (!placement.active) return null;

  const report = async (value: PlacementReport) => {
    if (busy) return;
    setBusy(true);
    try {
      await api.placementSelfReport({ report: value, learningObjectIds: [learningObjectId] });
      onChanged();
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div data-testid="placement-section">
      <SectionHeader>Starting point</SectionHeader>
      {placement.assumed ? (
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
          <Pill color="purple">{ASSUMED_LABEL}</Pill>
          <Faint>
            {placement.firstReviewIsDue
              ? "its first review is due — that review is the check"
              : `first review ${day(placement.firstReviewDue)} is the check`}
          </Faint>
        </div>
      ) : (
        <Faint>
          {placement.lastOutcome === "failed"
            ? "the first review missed, so this is back to learning"
            : placement.lastOutcome === "returned" || placement.returnedByLearner
              ? "you said you don't know this yet, so it is being taught"
              : "learning: practice is the placement"}
        </Faint>
      )}
      <div style={{ display: "flex", gap: 14, marginTop: 8, flexWrap: "wrap" }}>
        {placement.assumed ? (
          <span
            role="button"
            onClick={() => void report("dont_know_this")}
            title="return this topic to learning now; nothing about your record changes"
            style={linkStyle(busy)}
          >
            ✗ I don&apos;t know this
          </span>
        ) : (
          <span
            role="button"
            onClick={() => void report("know_this")}
            title="assume this topic known (not tested); its first review in two weeks is the check"
            style={linkStyle(busy)}
          >
            ✓ I know this
          </span>
        )}
        {onQuickCheck ? (
          <span
            role="button"
            onClick={() => onQuickCheck([learningObjectId])}
            title={`optional: up to ${placement.quickCheckK} questions in about ${placement.quickCheckBudgetMinutes} minutes, results at the end`}
            style={linkStyle(busy)}
          >
            ? Check what I already know
          </span>
        ) : null}
      </div>
    </div>
  );
}
