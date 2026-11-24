// RW4d (spec §7.8): whether comparisons can be kept here, and what to refresh
// after a keep or a remove (the reading's ⇄ marks). Provided by the Reader
// only while the prompt contract carries `compareKeep`; absent (null), the
// compare table and the tutor's comparison render exactly as RW4a's and RW1c's.
import { createContext, useContext } from "react";
import type { CompareKeepContractDto } from "../../api/dto";

export interface CompareKeepContextValue {
  settings: CompareKeepContractDto;
  /** A keep or a remove happened: the marks are read again. */
  onChanged: () => void;
  /** The source open in the Reader (its passage leads a reopened table). */
  openSourceId: string | null;
}

export const CompareKeepContext = createContext<CompareKeepContextValue | null>(null);

// A keep or a remove made in one window (a book's, or a Compare window on the desks) changes the marks of every
// reading it touched: each reading's marks read again, so a book open beside shows its ⇄ at once.
const keptChanges = new EventTarget();

/** A comparison was kept or removed somewhere: every reading's ⇄ marks are read again. */
export function announceKeptChange(): void {
  keptChanges.dispatchEvent(new Event("changed"));
}

export function onKeptChange(listener: () => void): () => void {
  keptChanges.addEventListener("changed", listener);
  return () => keptChanges.removeEventListener("changed", listener);
}

export function useCompareKeep(): CompareKeepContextValue | null {
  return useContext(CompareKeepContext);
}
