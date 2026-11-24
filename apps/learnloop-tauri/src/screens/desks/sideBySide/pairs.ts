// Side by side on the desks (spec §21.1: the v1 Reader's CA6 second pane becomes "two windows in view, or a pair",
// §5.2). The book windows themselves are unchanged; what the second pane did between the two books lives here:
//
// * the pair: which window was opened beside which (Ctrl+\ or a list's "side by side"), each keeping its own book,
//   place and anchors;
// * follow along (on by default, as in CA6; Ctrl+Shift+L turns it off for the pair): when one window crosses into a
//   new section, the other moves once, to the first of its book's judged correspondents for that section, at its
//   jump locator; a search hit never moves a window, and with none the other window stays put and says so;
// * a window moved by following is never answered back: its own crossing that the move caused moves nothing;
// * the leader is whichever window the learner moved last (each crossing it makes is its own).
//
// Records: follow_along_moved (salience only), as the second pane recorded it.
import type { CorrespondentsDto } from "../../../api/dto";
import { firstJudgedIn, targetOf } from "../../reader/sideBySide";

interface Pair {
  windows: [string, string];
  follow: boolean;
  /** A move asked for: a later crossing (of either window) supersedes it. */
  seq: number;
  /** The section a following window was moved to: its crossing there is the move's, not the learner's. */
  moved: Map<string, string>;
}

export interface PairWindow {
  sourceId: string;
  extractionId: string;
}

export interface PairDeps {
  /** The window's book, or null when it is no longer a book window on the desk. */
  windowOf: (windowId: string) => PairWindow | null;
  correspondents: (input: { extractionId: string; sectionId: string; searchFallback: boolean }) => Promise<CorrespondentsDto>;
  jump: (windowId: string, spanId: string) => void;
  notice: (text: string) => void;
  record: (event: "follow_along_moved", payload: Record<string, string>) => void;
}

export const PAIR_COPY = {
  staysPut: "no matching section here · stays put",
  followOn: "follow along on for this pair",
  followOff: "follow along off for this pair",
} as const;

export class DeskPairs {
  private byWindow = new Map<string, Pair>();
  /** Each book window's section in view, as last reported: a report is a crossing only when it differs (a window's
   *  first report, as it opens, is where it is, not a move of the learner's). */
  private sections = new Map<string, string>();

  constructor(private readonly deps: PairDeps) {}

  /** Two windows side by side: the second opened beside the first. */
  pair(first: string, second: string): void {
    this.drop(first);
    this.drop(second);
    const pair: Pair = { windows: [first, second], follow: true, seq: 0, moved: new Map() };
    this.byWindow.set(first, pair);
    this.byWindow.set(second, pair);
  }

  partnerOf(windowId: string): string | null {
    const pair = this.live(windowId);
    if (!pair) return null;
    return pair.windows[0] === windowId ? pair.windows[1] : pair.windows[0];
  }

  following(windowId: string): boolean {
    return Boolean(this.live(windowId)?.follow);
  }

  /** Ctrl+Shift+L: following on or off for this window's pair. */
  toggleFollow(windowId: string): void {
    const pair = this.live(windowId);
    if (!pair) return;
    pair.follow = !pair.follow;
    pair.seq += 1;
    this.deps.notice(pair.follow ? PAIR_COPY.followOn : PAIR_COPY.followOff);
  }

  /** A window's section in view moved: the other window of its pair follows, once. */
  async crossed(windowId: string, section: { extractionId: string; sectionId: string } | null): Promise<void> {
    const before = this.sections.get(windowId);
    if (section) this.sections.set(windowId, `${section.extractionId}\u0000${section.sectionId}`);
    else this.sections.delete(windowId);
    const pair = this.live(windowId);
    if (!pair || !section || before === undefined || before === this.sections.get(windowId)) return;
    const caused = pair.moved.get(windowId);
    pair.moved.delete(windowId);
    // The crossing the move itself caused: the moved window does not lead.
    if (caused === section.sectionId) return;
    if (!pair.follow) return;
    const partner = this.partnerOf(windowId);
    const book = partner ? this.deps.windowOf(partner) : null;
    if (!partner || !book) return;
    const mine = ++pair.seq;
    let view: CorrespondentsDto;
    try {
      view = await this.deps.correspondents({ extractionId: section.extractionId, sectionId: section.sectionId, searchFallback: false });
    } catch {
      return;
    }
    // A later crossing, a toggle, or the pair gone: this answer no longer applies.
    if (mine !== pair.seq || this.live(windowId) !== pair || !pair.follow) return;
    const hit = firstJudgedIn(view, book.sourceId);
    if (!hit) {
      this.deps.notice(PAIR_COPY.staysPut);
      return;
    }
    const target = targetOf(hit);
    if (!target.spanId) return;
    pair.moved.set(partner, target.sectionId);
    this.deps.jump(partner, target.spanId);
    this.deps.record("follow_along_moved", {
      extraction_id: section.extractionId, section_id: section.sectionId, leader_window: windowId,
      moved_window: partner, target_extraction_id: target.extractionId, target_section_id: target.sectionId, target_span_id: target.spanId,
    });
  }

  /** The pair this window is in, while both windows are still books on the desk. */
  private live(windowId: string): Pair | null {
    const pair = this.byWindow.get(windowId);
    if (!pair) return null;
    if (!pair.windows.every((id) => this.deps.windowOf(id))) {
      this.drop(windowId);
      return null;
    }
    return pair;
  }

  private drop(windowId: string): void {
    const pair = this.byWindow.get(windowId);
    if (!pair) return;
    for (const id of pair.windows) this.byWindow.delete(id);
  }
}
