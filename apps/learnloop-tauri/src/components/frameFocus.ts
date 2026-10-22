// UX Phase 2 fix round 5: after a pointer activation of a place, an
// Under-the-hood tool or a ⋯ row, the focus goes to the frame body (the
// simple shell's `main.frame-body`, tabIndex -1). Otherwise it stays on the
// clicked chrome control, and the screens' target rule (`screenLeavesKey`)
// rightly leaves every key aimed at a control that is not theirs, so a mouse
// user's next Enter, digit or j/k would do nothing. A keyboard activation
// (Enter or Space: a click with `detail` 0) keeps the focus where it is.
export function focusFrameBodyAfterPointer(event: { detail: number }): void {
  if (event.detail === 0) return;
  document.querySelector<HTMLElement>("main.frame-body")?.focus({ preventScroll: true });
}
