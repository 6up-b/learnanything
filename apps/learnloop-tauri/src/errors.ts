import type { CommandError } from "./api/dto";

const DEFAULT_ERROR_MESSAGE = "Something went wrong. Please try again.";

/**
 * Narrow an unknown rejection to the stable error envelope returned by the
 * Tauri bridge. Calls made outside that bridge (dialogs, events, browser APIs)
 * can still reject with strings or ordinary Error instances, so callers must
 * not cast every rejection to CommandError.
 */
export function getCommandError(error: unknown): CommandError | null {
  if (!error || typeof error !== "object") return null;
  const candidate = error as Partial<CommandError>;
  if (typeof candidate.code !== "string" || typeof candidate.message !== "string") return null;
  return {
    code: candidate.code,
    message: candidate.message,
    retryable: candidate.retryable === true,
    ...(candidate.details === undefined ? {} : { details: candidate.details })
  };
}

/** Return non-empty, user-safe copy for any JavaScript rejection shape. */
export function errorMessage(error: unknown, fallback = DEFAULT_ERROR_MESSAGE): string {
  const command = getCommandError(error);
  if (command?.message.trim()) return command.message.trim();
  if (error instanceof Error && error.message.trim()) return error.message.trim();
  if (typeof error === "string" && error.trim()) return error.trim();
  if (error && typeof error === "object" && "message" in error) {
    const message = (error as { message?: unknown }).message;
    if (typeof message === "string" && message.trim()) return message.trim();
  }
  return fallback;
}
