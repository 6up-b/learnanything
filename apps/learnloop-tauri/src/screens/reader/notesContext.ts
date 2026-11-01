// Curriculum C2 (spec §10): whether the learner's notes take part here, and what to read
// again after a link, a hide or a keep (the reading's › marks, the path's note lines).
// Provided by the Reader only while the prompt contract carries `notes` (notes.enabled on
// and tend installed); absent (null), the Reader, the path and Compare are today's exactly.
import { createContext, useContext } from "react";
import type { NotesContractDto } from "../../api/dto";

export interface NotesContextValue {
  settings: NotesContractDto;
  /** A link, a hide or a keep happened: the marks and note lines are read again. */
  onChanged: () => void;
  /** Bumped on every change, so a surface holding notes reads them again. */
  revision: number;
}

export const NotesContext = createContext<NotesContextValue | null>(null);

export function useNotes(): NotesContextValue | null {
  return useContext(NotesContext);
}
