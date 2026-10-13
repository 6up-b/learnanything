// Plain failure lines for Add and the book card (docs/specs/ux_learnloop_v1.md
// §6.7, §7.9): one sentence, the action is on the control that failed, and the
// raw message stays in details. Unknown codes get a generic line.

import type { CommandError } from "../api/dto";

export interface PlainError {
  line: string;
  /** The backend's own words, for details ▸ only. */
  details: string | null;
  retryable: boolean;
}

const LINES: Record<string, string> = {
  unsupported_source: "LearnLoop can't open this yet — it reads PDFs, web pages, arXiv, YouTube, Markdown, text and subtitles.",
  invalid_page_range: "Those pages don't look right — try a page or a range like 3-27.",
  chatgpt_not_signed_in: "Sign in with ChatGPT first, then connect.",
  chatgpt_no_models: "Your ChatGPT account lists no models LearnLoop can use.",
  openrouter_key_missing: "Add your OpenRouter key first, then connect.",
  ai_not_connected: "Connect an AI first: Continue with ChatGPT, or add an OpenRouter key.",
  not_ready: "This book is still being prepared. Try again in a minute.",
  source_not_found: "That book is no longer in your library.",
  nothing_to_retry: "There is nothing to try again for this book.",
  stale_app_binary: "LearnLoop needs a restart to finish updating.",
  stale_sidecar_schema: "LearnLoop needs a restart to finish updating."
};

// Codes whose backend message is already a plain sentence written for the learner.
const OWN_WORDS = new Set(["library_folder_in_use", "chatgpt_models_unavailable"]);

function asCommandError(error: unknown): CommandError | null {
  if (error && typeof error === "object" && "code" in error && "message" in error) {
    return error as CommandError;
  }
  return null;
}

export function plainError(error: unknown, fallback = "Something went wrong."): PlainError {
  const command = asCommandError(error);
  const raw = command?.message ?? (error instanceof Error ? error.message : typeof error === "string" ? error : null);
  const retryable = Boolean(command?.retryable);
  if (command && OWN_WORDS.has(command.code)) {
    return { line: command.message, details: null, retryable };
  }
  const known = command ? LINES[command.code] : undefined;
  if (known) {
    // A refused page range names the bad part; keep it, in brackets.
    const line = command?.code === "invalid_page_range" && raw ? `${known} (${raw})` : known;
    return { line, details: command?.code === "invalid_page_range" ? null : raw, retryable };
  }
  return { line: `${fallback} Try again.`, details: raw, retryable: true };
}
