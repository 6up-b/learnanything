// Stands in for @tauri-apps/plugin-dialog's `open`. The native chooser becomes
// a pending request on the bridge; the walk driver shows it in the observation
// ("a file chooser is open") and answers it when the person runs
// `walk upload <file>` (a file from this person's folder) or closes it.
import { post } from "./bridge";

export type DialogFilter = { name: string; extensions: string[] };
export interface OpenDialogOptions {
  title?: string;
  filters?: DialogFilter[];
  defaultPath?: string;
  multiple?: boolean;
  directory?: boolean;
  recursive?: boolean;
  canCreateDirectories?: boolean;
}

export async function open(options: OpenDialogOptions = {}): Promise<string | string[] | null> {
  const answer = await post<{ paths: string[] | null }>("/dialog/open", options);
  if (answer.paths === null) return null;
  return options.multiple ? answer.paths : (answer.paths[0] ?? null);
}

export async function save(): Promise<string | null> {
  return null;
}
