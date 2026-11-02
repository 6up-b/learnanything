// followups-nov1c D: the Reader's selection action "scope my deliverable from this
// passage". It sends the selected passage to the existing scope input
// (curriculum.set_scope, kind "passage", with the selection's spans), so the
// deliverable's resolver reads that passage (only it) to find the topics the deliverable
// needs. Honest copy: the model reads the passage and the learner reviews the result in
// the Guide; nothing else is read or changed.
//
// Shown only with a deliverable to scope (curriculum.deliverables answers: absent while the
// curriculum is off) and a selection that offers model actions: NotesRail hides it with
// the other model actions on a protected selection, and the server's own guard
// (deliverables.passage_texts: exam material, a reading held back, an unreadable
// predicate) refuses an exam-role or protected passage anyway, in its own words.
import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { DeliverableScopeDto } from "../../api/dto";
import { Faint } from "../../components/term";
import { SecondaryButton } from "../../components/goldenpath/shared";
import { errorMessage } from "../../errors";
import { scopeNotice, scopeSummary } from "./DeliverableScope";
import { MeaningLabel } from "./voices";

export const SCOPE_FROM_PASSAGE_COPY = {
  group: "DELIVERABLE",
  action: "scope my deliverable from this passage",
  actionFor: (title: string) => `scope “${title}” from this passage`,
  meaning: "LearnLoop's model reads this passage, and only it, to find the topics your deliverable needs and adds "
    + "them to its scope. Review them in the Guide.",
  failed: "Couldn't scope from that passage.",
} as const;

export interface ScopeFromPassageProps {
  extractionId: string | null;
  spanIds: string[];
  disabled?: boolean;
  onError: (message: string) => void;
}

export function ScopeFromPassage({ extractionId, spanIds, disabled = false, onError }: ScopeFromPassageProps) {
  const [deliverables, setDeliverables] = useState<DeliverableScopeDto[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  useEffect(() => {
    let alive = true;
    Promise.resolve()
      .then(() => api.curriculumDeliverables())
      .then((out) => {
        if (alive) setDeliverables(out.deliverables ?? []);
      })
      .catch(() => undefined); // the curriculum is off: no action
    return () => {
      alive = false;
    };
  }, []);
  // Never a whole document: an empty span list would read a syllabus whole (C3), so the
  // action needs a selection's spans.
  if (!extractionId || spanIds.length === 0 || !deliverables || deliverables.length === 0) return null;
  const scope = async (goalId: string) => {
    if (busy) return;
    setBusy(true);
    setNotice(null);
    try {
      const out = await api.curriculumSetScope({
        goalId, kind: "passage", extractionId, spanIds, context: { from: "reader_selection" },
      });
      setNotice(scopeNotice(out) ?? scopeSummary(out.scope));
      setDeliverables((current) => (current ?? []).map((entry) => (entry.goalId === goalId ? out.scope : entry)));
    } catch (error) {
      onError(errorMessage(error, SCOPE_FROM_PASSAGE_COPY.failed));
    } finally {
      setBusy(false);
    }
  };
  return (
    <div data-scope-from-passage="" style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <Faint style={{ fontSize: 10, letterSpacing: "0.14em" }}>{SCOPE_FROM_PASSAGE_COPY.group}</Faint>
      {deliverables.map((entry) => (
        <SecondaryButton key={entry.goalId} onClick={() => void scope(entry.goalId)} disabled={disabled || busy}>
          {deliverables.length === 1 ? SCOPE_FROM_PASSAGE_COPY.action : SCOPE_FROM_PASSAGE_COPY.actionFor(entry.title)}
        </SecondaryButton>
      ))}
      <MeaningLabel>{SCOPE_FROM_PASSAGE_COPY.meaning}</MeaningLabel>
      {notice ? <span data-scope-from-passage-notice=""><Faint style={{ fontSize: 11 }}>{notice}</Faint></span> : null}
    </div>
  );
}
