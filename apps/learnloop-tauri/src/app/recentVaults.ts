// Recent-vaults persistence for the nav vault chip's dropdown. localStorage
// only — the list is a per-machine convenience, matching how the app treats
// every other learnloop.* key (tab, palette, backdrop) as best-effort state.

const KEY = "learnloop.recentVaults";
const MAX = 8;

// Normalize for dedupe only — stored strings stay verbatim so select_vault
// receives exactly what the OS picker / backend produced. Windows paths are
// case-insensitive, hence the lowercase.
function pathKey(path: string): string {
  return path.replace(/\\/g, "/").replace(/\/+$/, "").toLowerCase();
}

export function samePath(a: string, b: string): boolean {
  return pathKey(a) === pathKey(b);
}

// Basename for display. Mirrors StartScreen's vaultAlias split but without
// titleCase: the nav chip shows the folder name verbatim.
export function vaultName(path: string): string {
  const parts = path.replace(/\\/g, "/").split("/").filter(Boolean);
  return parts.length ? parts[parts.length - 1] : path;
}

// Parent-qualified label ("parent/name") for disambiguating duplicate basenames.
export function vaultNameWithParent(path: string): string {
  const parts = path.replace(/\\/g, "/").split("/").filter(Boolean);
  if (parts.length >= 2) return `${parts[parts.length - 2]}/${parts[parts.length - 1]}`;
  return parts.length ? parts[0] : path;
}

export function listRecentVaults(): string[] {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((entry): entry is string => typeof entry === "string" && entry.length > 0);
  } catch {
    return [];
  }
}

export function recordRecentVault(path: string): void {
  try {
    const next = [path, ...listRecentVaults().filter((p) => !samePath(p, path))].slice(0, MAX);
    localStorage.setItem(KEY, JSON.stringify(next));
  } catch {
    // best-effort: quota/privacy failures never break vault switching
  }
}

export function removeRecentVault(path: string): void {
  try {
    const next = listRecentVaults().filter((p) => !samePath(p, path));
    localStorage.setItem(KEY, JSON.stringify(next));
  } catch {
    // best-effort
  }
}
