// An answer's proposed change to a pad (spec §8.4): a previewed diff, the inserted lines in green, with
// "accept" and "not this". The desks supply the proposals and the accept (writing blocks with
// `provenance: tutor` into the desk's running pad); without a handler, accept says where it would land and
// is not offered.
import { useState } from "react";

export interface ProposedDiff {
  id: string;
  /** The pad it would change, by its title. */
  target: string;
  /** "Put a check in your scratchpad as a cell", "Add this derivation to your pad". */
  label: string;
  /** The lines it would insert. */
  lines: string[];
  onAccept?: () => Promise<void> | void;
  onDecline?: () => void;
}

export function DiffProposal({ proposal }: { proposal: ProposedDiff }) {
  const [state, setState] = useState<"open" | "accepting" | "accepted" | "declined" | "failed">("open");
  if (state === "declined") return <div className="desk-diff declined" data-diff={proposal.id}>not this · nothing was written</div>;
  return (
    <div className={`desk-diff ${state}`} data-diff={proposal.id}>
      <div className="head">◇ {proposal.label} to “{proposal.target}” · preview of up to six nonblank lines</div>
      <div className="lines">
        {proposal.lines.map((line, index) => <div key={index} className="ins">+ {line}</div>)}
      </div>
      {state === "accepted" ? <div className="done">Reply queued for “{proposal.target}”.</div> : null}
      {state === "failed" ? <div className="done">Couldn’t add the reply. Open the running pad and try again.</div> : null}
      {state === "open" || state === "failed" ? (
        <div className="acts">
          {proposal.onAccept ? (
            <button type="button" onClick={() => {
              setState("accepting");
              void Promise.resolve(proposal.onAccept?.()).then(() => setState("accepted"), () => setState("failed"));
            }}>accept</button>
          ) : (
            <span className="later">Copying to this pad is unavailable. Open a pad to write your own note.</span>
          )}
          <button type="button" onClick={() => {
            proposal.onDecline?.();
            setState("declined");
          }}>not this</button>
        </div>
      ) : null}
    </div>
  );
}
