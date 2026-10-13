// The Reader's key bar, in plain words (UX Phase 1 re-test #9: "release ctrl
// capture box union · alt+drag sweep blocks" meant nothing to a learner). What
// each key does is said as what the learner gets: releasing ctrl selects what
// the boxes drew, so it is part of the ctrl+drag line, not a key of its own.

export type ReaderKey = { key: string; label: string };

export function readerKeyBarKeys(pdfSurface: boolean): ReaderKey[] {
  return pdfSurface
    ? [
        { key: "drag", label: "select text" },
        { key: "ctrl+drag", label: "select by drawing boxes" },
        { key: "alt+drag", label: "select whole paragraphs" },
        { key: "alt", label: "clear selection" },
        { key: "right-click", label: "tag" },
      ]
    : [
        { key: "drag", label: "select text" },
        { key: "ctrl+drag", label: "select by drawing boxes" },
        { key: "alt", label: "clear selection" },
        { key: "right-click", label: "tag" },
      ];
}
