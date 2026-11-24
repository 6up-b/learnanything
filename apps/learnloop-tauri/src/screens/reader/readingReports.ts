// How far each section was read, reported to the backend (round-2 review F3, re-review F7), bound to the vault it was
// read in (the Reader's retirement, review fix round: blocker 2 and major 5).
//
// A book's report is gathered for a moment, sent, and retried a few times when it fails; what the backend has not
// acknowledged outlives the book's window: closing the book leaves it here, and leaving the Reader (the desks
// unmounting), changing vaults or that vault loading again sends it once more. It is sent only while the vault it was
// read in is the one selected (app/vaultTransition.ts): the app flushes it before a vault change, and nothing sent
// after the change can reach the next vault, a timed retry or a closing window's included; what still failed is kept
// for its own vault and sent when that vault is selected again.
import { api } from "../../api/client";
import type { ReaderMarkProgressResultDto } from "../../api/dto";
import { onVaultActive, registerVaultDraft, vaultKey } from "../../app/vaultTransition";

export const SEEN_REPORT_MS = 1500;
// Timed retries of a failed progress save (leaving the Reader always retries).
const SEEN_RETRY_LIMIT = 3;

/** One book's reading-progress saves: the newest count per section, the counts the backend acknowledged and the ones
 * on their way, and the book's timed retry. It outlives leaving the book, so a retry set before the learner left sends
 * that book's newest counts. */
export interface SeenSave {
  extractionId: string;
  /** The vault the reading was done in (`vaultKey()` when the book opened): the only vault it is ever sent to. */
  vault: string | null;
  wanted: Record<string, { spansSeen: number; spanCount: number }>;
  acknowledged: Record<string, number>;
  sending: Record<string, number>;
  /** The passages the learner's own reading observed, per section, and the sections
   *  whose last passage was among them. The backend unions them, so each goes until it is acknowledged; an
   *  answered report acknowledges every id it carried, the ones the backend left out as not the section's too,
   *  so none is sent again. */
  passages: Record<string, Set<string>>;
  acknowledgedPassages: Set<string>;
  sendingPassages: Set<string>;
  ends: Set<string>;
  acknowledgedEnds: Set<string>;
  sendingEnds: Set<string>;
  attempts: number;
  timer: number | null;
  /** Whether a mounted book still holds it; once none does, it is kept only while it owes the backend something. */
  held: boolean;
  inflight: Set<Promise<unknown>>;
}

/** What hears an acknowledged save: the book, the section and the backend's answer (whose progress says whether the
 *  section is finished: from algorithm tag mvp-0.63 its end, carried by the save, finishes it). */
export type SeenSaved = (extractionId: string, sectionId: string, result: ReaderMarkProgressResultDto | null) => void;

/** Every save a mounted book holds, and every one a closed book left owing the backend. */
const kept = new Set<SeenSave>();

export function seenSaveFor(saves: Map<string, SeenSave>, extractionId: string): SeenSave {
  let save = saves.get(extractionId);
  if (!save) {
    save = {
      extractionId, vault: vaultKey(),
      wanted: {}, acknowledged: {}, sending: {}, passages: {}, acknowledgedPassages: new Set(),
      sendingPassages: new Set(), ends: new Set(), acknowledgedEnds: new Set(), sendingEnds: new Set(),
      attempts: 0, timer: null, held: true, inflight: new Set(),
    };
    saves.set(extractionId, save);
    kept.add(save);
  }
  return save;
}

function owes(save: SeenSave): boolean {
  if (save.timer !== null || save.inflight.size > 0) return true;
  for (const [sectionId, counts] of Object.entries(save.wanted)) if (counts.spansSeen > (save.acknowledged[sectionId] ?? 0)) return true;
  for (const ids of Object.values(save.passages)) for (const spanId of ids) if (!save.acknowledgedPassages.has(spanId)) return true;
  for (const sectionId of save.ends) if (!save.acknowledgedEnds.has(sectionId)) return true;
  return false;
}

function settle(save: SeenSave): void {
  if (!save.held && !owes(save)) kept.delete(save);
}

/** A book's window closed: its saves stay only while they owe the backend something. */
export function releaseSeenSaves(saves: Map<string, SeenSave>): void {
  for (const save of saves.values()) {
    save.held = false;
    settle(save);
  }
}

/** Send a book's counts that are neither acknowledged nor on their way, if the vault they were read in is the one
 * selected now (else they wait for it). A failed save is tried again a few times (a busy database, a restarting
 * sidecar) with whatever the book's newest counts are by then; after that it waits for the next change, or for the
 * learner leaving the book or the Reader. `onSaved` hears each count the backend acknowledged, a retry's included
 * (RW7a Codex re-review F3: what reads the progress back waits for it). */
export function sendSeenCounts(saves: Map<string, SeenSave>, extractionId: string, onSaved?: SeenSaved): void {
  const save = saves.get(extractionId);
  if (save) sendSave(save, onSaved);
}

function sendSave(save: SeenSave, onSaved?: SeenSaved): Promise<unknown>[] {
  if (save.vault === null || save.vault !== vaultKey()) return [];
  const { extractionId } = save;
  const sent: Promise<unknown>[] = [];
  const sectionIds = new Set([...Object.keys(save.wanted), ...Object.keys(save.passages), ...save.ends]);
  for (const sectionId of sectionIds) {
    const counts = save.wanted[sectionId];
    const countNew = counts !== undefined
      && counts.spansSeen > Math.max(save.acknowledged[sectionId] ?? 0, save.sending[sectionId] ?? 0);
    const passages = [...(save.passages[sectionId] ?? [])]
      .filter((spanId) => !save.acknowledgedPassages.has(spanId) && !save.sendingPassages.has(spanId));
    const end = save.ends.has(sectionId) && !save.acknowledgedEnds.has(sectionId) && !save.sendingEnds.has(sectionId);
    if (!countNew && passages.length === 0 && !end) continue;
    if (countNew) save.sending[sectionId] = counts.spansSeen;
    for (const spanId of passages) save.sendingPassages.add(spanId);
    if (end) save.sendingEnds.add(sectionId);
    const request: Promise<unknown> = api.readerNoteReadingProgress({
      extractionId, sectionId,
      ...(counts ? { spansSeen: counts.spansSeen, spanCount: counts.spanCount } : {}),
      ...(passages.length > 0 ? { seenSpanIds: passages } : {}),
      ...(end ? { reachedEnd: true } : {}),
    })
      .then((result) => {
        if (counts) save.acknowledged[sectionId] = Math.max(save.acknowledged[sectionId] ?? 0, counts.spansSeen);
        for (const spanId of passages) save.acknowledgedPassages.add(spanId);
        if (end) save.acknowledgedEnds.add(sectionId);
        save.attempts = 0;
        onSaved?.(extractionId, sectionId, result ?? null);
      })
      .catch(() => {
        if (save.timer !== null || save.attempts >= SEEN_RETRY_LIMIT) return;
        save.attempts += 1;
        save.timer = window.setTimeout(() => {
          save.timer = null;
          sendSave(save, onSaved);
          settle(save);
        }, SEEN_REPORT_MS * 2 ** save.attempts);
      })
      .finally(() => {
        if (counts && save.sending[sectionId] === counts.spansSeen) delete save.sending[sectionId];
        for (const spanId of passages) save.sendingPassages.delete(spanId);
        if (end) save.sendingEnds.delete(sectionId);
        save.inflight.delete(request);
        settle(save);
      });
    save.inflight.add(request);
    sent.push(request);
  }
  return sent;
}

/** Sends every report of the vault selected now that the backend has not acknowledged, a book's that is closed
 * included, past any retry limit (leaving the Reader, a vault change); resolves once each has an answer, never
 * rejects: what failed stays kept for its vault. */
export async function flushReadingReports(): Promise<void> {
  const key = vaultKey();
  const sent: Promise<unknown>[] = [];
  for (const save of [...kept]) {
    if (save.vault !== key) continue;
    if (save.timer !== null) {
      window.clearTimeout(save.timer);
      save.timer = null;
    }
    sent.push(...sendSave(save), ...save.inflight);
  }
  await Promise.allSettled(sent);
}

// Before a vault change the app flushes what was read in the vault being left (its answer lands in that vault); after
// the change nothing of it goes until that vault is selected again, and then it goes.
registerVaultDraft({ freeze: () => undefined, flush: flushReadingReports, resume: () => undefined });
onVaultActive(() => void flushReadingReports());
