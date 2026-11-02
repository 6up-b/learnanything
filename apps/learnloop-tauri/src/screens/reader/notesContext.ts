// Curriculum C2 (spec §10): whether the learner's notes take part here, and what to read
// again after a link, a hide or a keep (the reading's › marks, the path's note lines).
// Provided by the Reader only while the prompt contract carries `notes` (notes.enabled on; C2b:
// the vault's own notes, in every vault); absent (null), the Reader, the path and Compare are
// today's exactly.
import { createContext, useContext } from "react";
import type { NoteLinkDto, NotesContractDto } from "../../api/dto";

/** A link the learner hid this session: kept on screen with *undo* (Codex review F5). */
export interface HiddenNote {
  link: NoteLinkDto;
  /** The learner's hide row: *undo* keeps it after all. */
  hiddenId: string;
}

export interface NotesContextValue {
  settings: NotesContractDto;
  /** A link, a hide or a keep happened: the marks and note lines are read again. */
  onChanged: () => void;
  /** Bumped on every change, so a surface holding notes reads them again. */
  revision: number;
  /** The links hidden this session, by the hidden link's id: a refresh no longer lists
   *  them, so every surface keeps their card (with *undo*) until undone (Codex review F5). */
  hidden: ReadonlyMap<string, HiddenNote>;
  remember: (link: NoteLinkDto, hiddenId: string) => void;
  forget: (linkId: string) => void;
}

export const NotesContext = createContext<NotesContextValue | null>(null);

export function useNotes(): NotesContextValue | null {
  return useContext(NotesContext);
}
