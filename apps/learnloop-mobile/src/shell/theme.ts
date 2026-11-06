// Light and dark (mobile v2 §4.6): the system's choice by default, with a manual override from
// the Display sheet. The colours themselves live in styles.css, the one place they are defined;
// this only says which set applies. `theme.test.ts` checks both sets for WCAG AA contrast.
import { useCallback, useState } from "react";

export type ThemeChoice = "system" | "light" | "dark";

const KEY = "learnloop.theme";
export const THEME_CHOICES: readonly { readonly value: ThemeChoice; readonly label: string }[] = [
  { value: "system", label: "Match the phone" },
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" }
];

export function readThemeChoice(): ThemeChoice {
  try {
    const stored = localStorage.getItem(KEY);
    return stored === "light" || stored === "dark" ? stored : "system";
  } catch {
    return "system";
  }
}

/** `data-theme` on the root wins over `prefers-color-scheme`; none means the system decides. */
export function applyTheme(choice: ThemeChoice, root: HTMLElement = document.documentElement): void {
  if (choice === "system") delete root.dataset.theme;
  else root.dataset.theme = choice;
}

export function saveThemeChoice(choice: ThemeChoice): void {
  try {
    if (choice === "system") localStorage.removeItem(KEY);
    else localStorage.setItem(KEY, choice);
  } catch {
    // Storage refused: the choice holds until the app closes.
  }
  applyTheme(choice);
}

export function useThemeChoice(): [ThemeChoice, (choice: ThemeChoice) => void] {
  const [choice, setChoice] = useState<ThemeChoice>(readThemeChoice);
  const choose = useCallback((next: ThemeChoice) => {
    saveThemeChoice(next);
    setChoice(next);
  }, []);
  return [choice, choose];
}
