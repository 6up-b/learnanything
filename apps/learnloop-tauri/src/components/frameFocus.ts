// UX Phase 2 fix rounds 5 and 6: after a pointer activation of a place, an
// Under-the-hood tool or a ⋯ row, the clicked chrome control lets go of the
// focus, which returns to the document body, as in base. Otherwise it stays on
// the control, and the screens' target rule (`screenLeavesKey`) rightly leaves
// every key aimed at a control that is not theirs, so a mouse user's next
// Enter, digit or j/k would do nothing. Round 5 moved the focus to the frame
// body (tabIndex -1) instead. That made every click on plain content focus
// `main`, so the Reader's intent box ignored the next key and keyboard
// scrolling stopped (round 6). A keyboard activation (Enter or Space: a click
// with `detail` 0) keeps the focus where it is.
export function releaseFocusAfterPointer(event: { detail: number; currentTarget: EventTarget | null }): void {
  if (event.detail === 0) return;
  if (event.currentTarget instanceof HTMLElement) event.currentTarget.blur();
}
