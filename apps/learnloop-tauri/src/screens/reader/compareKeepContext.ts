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

export function useCompareKeep(): CompareKeepContextValue | null {
  return useContext(CompareKeepContext);
}
