type DraftOwner = {
  freeze: () => void;
  flush: () => Promise<unknown>;
  resume: () => void;
};

const drafts = new Set<DraftOwner>();
let selecting = false;

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
    // Successful selection leaves the old owners frozen until they unmount.
    return await select();
  } catch (error) {
    for (const owner of owners) owner.resume();
    throw error;
  } finally {
    selecting = false;
  }
}
