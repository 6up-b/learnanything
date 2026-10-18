// Reader workbench RW2b: "ⓘ where this goes" on every free-text box (UX
// §4.10; spec W5, G62). A quiet toggle; the line says where that box's text
// is routed, and that it never grades. Static: no motion, no dialog.
import { useState } from "react";
import { quietLink } from "../../components/PlainParts";
import { MeaningLabel } from "../reader/voices";
import { HELP_COPY, WHERE_THIS_GOES, type WhereThisGoesBox } from "./helpModel";

export function WhereThisGoes({ box }: { box: WhereThisGoesBox }) {
  const [open, setOpen] = useState(false);
  return (
    <span data-where-this-goes={box}>
      <button type="button" style={{ ...quietLink, fontSize: 10 }} aria-expanded={open} onClick={() => setOpen((value) => !value)}>
        {HELP_COPY.whereThisGoes}
      </button>
      {open ? (
        <div>
          <MeaningLabel>{WHERE_THIS_GOES[box].line}</MeaningLabel>
        </div>
      ) : null}
    </span>
  );
}
