type DraftOwner = {
  freeze: () => void;
  flush: () => Promise<unknown>;
  resume: () => void;
};

const drafts = new Set<DraftOwner>();
let selecting = false;

// Which vault the sidecar writes to now (the Reader's retirement, review fix round: reading evidence bound to its
// vault). A write gathered on one vault and sent later (a debounced report, a retry, a window's cleanup) names the
// vault it was gathered in, and goes only while that vault is the one selected: never into the next one.
//
// The key is the vault's root as the app loaded it ("" before the app noted any, as in a test that never selects), or
// null from the moment a selection is sent until the app has loaded the vault it selected: nothing deferred goes then.
let noted = "";
let between = false;
const activeListeners = new Set<(key: string) => void>();

/** The vault writes go to now, or null while a selection is on its way. */
export function vaultKey(): string | null {
  return between ? null : noted;
}

/** The app loaded this vault (its root): it is the one writes go to, and whatever was kept for it is sent now. */
export function noteActiveVault(root: string | null | undefined): void {
  noted = root ?? "";
  between = false;
  for (const listener of [...activeListeners]) listener(noted);
}

/** Hears each vault the app loads (by its key): work kept for a vault while another was selected goes on then. */
export function onVaultActive(listener: (key: string) => void): () => void {
  activeListeners.add(listener);
  return () => { activeListeners.delete(listener); };
}

export function registerVaultDraft(owner: DraftOwner): () => void {
  drafts.add(owner);
  return () => { drafts.delete(owner); };
}

/** Every draft still belongs to the old vault until selection commits. */
export async function selectWithDraftFlush<T>(select: () => Promise<T>): Promise<T> {
  if (selecting) throw new Error("A vault change is already in progress.");
  selecting = true;
  const owners = [...drafts];
  try {
    for (const owner of owners) owner.freeze();
    const results = await Promise.allSettled(owners.map((owner) => owner.flush()));
    const failed = results.find((result) => result.status === "rejected");
    if (failed?.status === "rejected") throw failed.reason;
    // From here nothing gathered in the vault being left is sent until that vault is selected again.
    between = true;
    // Successful selection leaves the old owners frozen until they unmount.
    return await select();
  } catch (error) {
    between = false;
    for (const owner of owners) owner.resume();
    throw error;
  } finally {
    selecting = false;
  }
}
