// F3 — Editable recipe tree + blast-radius panel (spec §7.2 / §9.2).
//
// The read-only "why not ready" recipe tree (KnowledgeModel.RecipeTree) renders
// the readiness *projection*; this is the editable *source* surface. It seeds
// from LearningObjectDetail.blueprints (the raw on-disk recipe structure) and
// keeps every edit in local state until "file as proposal", which compiles each
// changed blueprint into ONE task_blueprint proposal item (the write path that
// actually carries recipes — a learning_object update payload has no blueprints
// field and would silently drop them). A debounced preview shows the readiness
// blast radius of the pending edits.

import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { api } from "../../api/client";
import type {
  BlueprintReadinessPreviewDto,
  FacetSummaryDto,
  LoBlueprintDto,
  RecipeComponentDto,
} from "../../api/dto";
import { BlockBar, COLOR, Dim, Faint, FONT_MONO, HelpTooltip, Pill, SectionHeader, TermSelect } from "../term";

const CAPABILITIES = [
  "retrieval",
  "schema_interpretation",
  "procedure_execution",
  "method_selection",
  "coordination",
] as const;

const MODALITIES = ["hard", "path_specific", "facilitating", "instructional_order"] as const;

type Role = "all_of" | "any_of";

// -- Internal editable model (camelCase; serialized to snake_case on emit) -----

interface EditComponent {
  facet: string;
  capability: string;
  modality: string;
}
interface EditRecipe {
  id: string;
  composition: string;
  allOf: EditComponent[];
  anyOf: EditComponent[];
  integration: EditComponent | null;
}
interface EditBlueprint {
  id: string;
  weight: number;
  recipes: EditRecipe[];
}

function cloneComponent(c: RecipeComponentDto): EditComponent {
  return { facet: c.facet, capability: c.capability, modality: c.modality || "hard" };
}
function seed(blueprints: LoBlueprintDto[]): EditBlueprint[] {
  return blueprints.map((bp) => ({
    id: bp.id,
    weight: bp.weight,
    recipes: bp.recipes.map((r) => ({
      id: r.id,
      composition: r.composition || "conjunctive",
      allOf: (r.allOf ?? []).map(cloneComponent),
      anyOf: (r.anyOf ?? []).map(cloneComponent),
      integration: r.integration ? cloneComponent(r.integration) : null,
    })),
  }));
}

// -- Serialize to the snake_case on-disk YAML shape ---------------------------

function snakeComponent(c: EditComponent): Record<string, unknown> {
  return { facet: c.facet, capability: c.capability, modality: c.modality };
}
function snakeRecipe(r: EditRecipe): Record<string, unknown> {
  return {
    id: r.id,
    composition: r.composition || "conjunctive",
    all_of: r.allOf.map(snakeComponent),
    any_of: r.anyOf.map(snakeComponent),
    integration: r.integration ? snakeComponent(r.integration) : null,
  };
}
function snakeBlueprint(bp: EditBlueprint): Record<string, unknown> {
  return { id: bp.id, weight: bp.weight, recipes: bp.recipes.map(snakeRecipe) };
}

const shortFacet = (f: string): string => f.replace(/^facet_/, "");
const pct = (v: number | null | undefined): string => (v == null ? "—" : `${Math.round(v * 100)}%`);

// -- Component ----------------------------------------------------------------

export function RecipeTreeEditor({
  loId,
  blueprints,
  onGo,
}: {
  loId: string;
  blueprints: LoBlueprintDto[] | undefined;
  onGo?: (id: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<EditBlueprint[]>(() => seed(blueprints ?? []));
  const [original, setOriginal] = useState<EditBlueprint[]>(() => seed(blueprints ?? []));
  const [facets, setFacets] = useState<FacetSummaryDto[]>([]);
  const [rationale, setRationale] = useState("");
  const [filing, setFiling] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);
  const [filed, setFiled] = useState<{ batchId: string; count: number } | null>(null);

  // Re-seed when the inspected LO changes.
  useEffect(() => {
    const fresh = seed(blueprints ?? []);
    setDraft(fresh);
    setOriginal(seed(blueprints ?? []));
    setEditing(false);
    setRationale("");
    setFiled(null);
    setFileError(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loId]);

  useEffect(() => {
    if (!editing || facets.length) return;
    let alive = true;
    api
      .listFacets()
      .then((r) => alive && setFacets(r.facets))
      .catch(() => {
        /* autocomplete degrades to free text */
      });
    return () => {
      alive = false;
    };
  }, [editing, facets.length]);

  const mutate = useCallback((fn: (bps: EditBlueprint[]) => void) => {
    setDraft((prev) => {
      const next = structuredClone(prev) as EditBlueprint[];
      fn(next);
      return next;
    });
    setFiled(null);
  }, []);

  const changedIds = useMemo(() => {
    const origById = new Map(original.map((b) => [b.id, JSON.stringify(snakeBlueprint(b))]));
    const ids: string[] = [];
    for (const bp of draft) {
      if (origById.get(bp.id) !== JSON.stringify(snakeBlueprint(bp))) ids.push(bp.id);
    }
    return ids;
  }, [draft, original]);

  const hasBlueprints = (blueprints ?? []).length > 0;

  async function file() {
    if (!rationale.trim() || !changedIds.length) return;
    setFiling(true);
    setFileError(null);
    try {
      const edits = draft
        .filter((bp) => changedIds.includes(bp.id))
        .map((bp) => ({
          itemType: "task_blueprint" as const,
          operation: "update" as const,
          targetEntityId: loId,
          payload: { learning_object_id: loId, ...snakeBlueprint(bp) },
        }));
      const result = await api.proposeGraphEdits({ rationale: rationale.trim(), edits });
      const invalid = result.items.filter((it) => it.validationStatus === "invalid");
      if (invalid.length) {
        setFileError(
          invalid
            .map((it) => `${it.targetEntityId ?? it.itemType}: ${it.validationErrors.join("; ")}`)
            .join(" · ")
        );
      } else {
        setOriginal(structuredClone(draft) as EditBlueprint[]);
        setEditing(false);
        setRationale("");
        setFiled({ batchId: result.batchId, count: edits.length });
      }
    } catch (err) {
      setFileError(err instanceof Error ? err.message : String(err));
    } finally {
      setFiling(false);
    }
  }

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <SectionHeader style={{ flex: 1 }}>Recipe editor</SectionHeader>
        <HelpTooltip label="What is the recipe editor for?">
          Edits the blueprint recipes that define which combinations of facet–capability evidence can satisfy this learning object. Changes preview their readiness impact and are filed as reviewable proposals; nothing is applied immediately.
        </HelpTooltip>
      </div>
      <div>
          <div style={{ color: COLOR.textDim, fontSize: 11, lineHeight: 1.5, marginBottom: 10 }}>
            Edit the facet–capability requirements used for readiness and evidence attribution. Changes are filed as proposals for review.
          </div>
          <div style={ruleLegendStyle}>
            <span><b style={{ color: COLOR.amber }}>all_of</b> · every requirement</span>
            <span><b style={{ color: COLOR.cyan }}>any_of</b> · one alternative</span>
            <span><b style={{ color: COLOR.pink }}>integration</b> · coordinated evidence</span>
          </div>

          {!hasBlueprints ? (
            <Faint>No authored requirement blueprint is attached to this learning object. This editor revises existing blueprints; it does not create the first one.</Faint>
          ) : (
            <>
              <div style={{ display: "flex", alignItems: "center", gap: 8, margin: "6px 0 10px" }}>
                <button
                  type="button"
                  onClick={() => {
                    setEditing((v) => !v);
                    setFiled(null);
                    if (editing) setDraft(structuredClone(original) as EditBlueprint[]);
                  }}
                  style={{ ...toggleBtn, color: editing ? COLOR.amber : COLOR.amberLink }}
                >
                  {editing ? "× discard draft" : "edit requirements"}
                </button>
                {editing && changedIds.length > 0 ? (
                  <Pill color="amber">
                    {changedIds.length} blueprint{changedIds.length === 1 ? "" : "s"} changed
                  </Pill>
                ) : null}
              </div>

              <div style={{ display: "grid", gridTemplateColumns: editing ? "1fr 320px" : "1fr", gap: 16 }}>
                <div>
                  {draft.map((bp, bi) => (
                    <BlueprintEditor
                      key={bp.id}
                      bp={bp}
                      editing={editing}
                      facets={facets}
                      changed={changedIds.includes(bp.id)}
                      onWeight={(w) => mutate((bps) => (bps[bi].weight = w))}
                      onMutateRecipe={(ri, fn) => mutate((bps) => fn(bps[bi].recipes[ri]))}
                    />
                  ))}
                </div>
                {editing ? <BlastRadiusPanel loId={loId} draft={draft} onGo={onGo} /> : null}
              </div>

              {editing ? (
                <div style={fileBar}>
                  <input
                    value={rationale}
                    onChange={(e) => setRationale(e.target.value)}
                    placeholder="rationale (required) — why these requirement changes?"
                    style={rationaleInput}
                  />
                  <button
                    type="button"
                    disabled={filing || !rationale.trim() || !changedIds.length}
                    onClick={file}
                    style={{
                      ...toggleBtn,
                      color: !rationale.trim() || !changedIds.length ? COLOR.textFaint : COLOR.green,
                      borderColor: !rationale.trim() || !changedIds.length ? COLOR.border : COLOR.green,
                    }}
                  >
                    {filing ? "filing…" : "file proposal →"}
                  </button>
                </div>
              ) : null}

              {fileError ? (
                <div style={{ marginTop: 6, color: COLOR.red, fontSize: 12 }}>{fileError}</div>
              ) : null}
              {filed ? (
                <div style={{ marginTop: 6, fontSize: 12, color: COLOR.green }}>
                  Filed {filed.count} edit{filed.count === 1 ? "" : "s"} as batch{" "}
                  <span style={{ fontFamily: FONT_MONO, color: COLOR.text }}>{filed.batchId}</span> ·{" "}
                  <Faint>review in Proposals to apply</Faint>
                </div>
              ) : null}
            </>
          )}
      </div>
    </div>
  );
}

// -- One blueprint ------------------------------------------------------------

function BlueprintEditor({
  bp,
  editing,
  facets,
  changed,
  onWeight,
  onMutateRecipe,
}: {
  bp: EditBlueprint;
  editing: boolean;
  facets: FacetSummaryDto[];
  changed: boolean;
  onWeight: (w: number) => void;
  onMutateRecipe: (recipeIndex: number, fn: (r: EditRecipe) => void) => void;
}) {
  return (
    <div style={{ marginBottom: 12, border: `1px solid ${changed ? COLOR.amber : COLOR.border}`, background: COLOR.bgInput }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "7px 10px", fontSize: 11 }}>
        <Faint>requirement blueprint</Faint>
        <span style={{ fontFamily: FONT_MONO, color: changed ? COLOR.amber : COLOR.text, overflowWrap: "anywhere" }}>{bp.id}</span>
        <span style={{ flex: 1 }} />
        <Faint>weight</Faint>
        {editing ? (
          <input
            type="number"
            step={0.1}
            min={0}
            value={bp.weight}
            onChange={(e) => onWeight(Number(e.target.value))}
            style={{ ...numInput, width: 64 }}
          />
        ) : (
          <span style={{ fontFamily: FONT_MONO, color: COLOR.text }}>{bp.weight}</span>
        )}
      </div>
      {bp.recipes.map((recipe, ri) => (
        <RecipeEditor
          key={recipe.id}
          recipe={recipe}
          editing={editing}
          facets={facets}
          onMutate={(fn) => onMutateRecipe(ri, fn)}
        />
      ))}
    </div>
  );
}

// -- One recipe ---------------------------------------------------------------

function RecipeEditor({
  recipe,
  editing,
  facets,
  onMutate,
}: {
  recipe: EditRecipe;
  editing: boolean;
  facets: FacetSummaryDto[];
  onMutate: (fn: (r: EditRecipe) => void) => void;
}) {
  const move = (role: Role, idx: number) =>
    onMutate((r) => {
      const from = role === "all_of" ? r.allOf : r.anyOf;
      const to = role === "all_of" ? r.anyOf : r.allOf;
      const [c] = from.splice(idx, 1);
      if (c) to.push(c);
    });
  const remove = (role: Role, idx: number) =>
    onMutate((r) => (role === "all_of" ? r.allOf : r.anyOf).splice(idx, 1));
  const setModality = (role: Role, idx: number, modality: string) =>
    onMutate((r) => ((role === "all_of" ? r.allOf : r.anyOf)[idx].modality = modality));
  const add = (role: Role, c: EditComponent) =>
    onMutate((r) => (role === "all_of" ? r.allOf : r.anyOf).push(c));

  return (
    <div style={{ padding: "8px 10px", borderTop: `1px solid ${COLOR.border}`, borderLeft: `2px solid ${COLOR.borderStrong}` }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8, flexWrap: "wrap", fontSize: 11 }}>
        <Faint>evidence path</Faint>
        <span style={{ color: COLOR.textDim, overflowWrap: "anywhere" }}>{recipe.id}</span>
        <Pill color="slate" style={{ fontSize: 11 }}>
          {recipe.composition === "conjunctive" ? "all requirements" : recipe.composition.replace(/_/g, " ")}
        </Pill>
      </div>

      <RoleGroup label="all_of · every component required" empty="no required components">
        {recipe.allOf.map((c, i) => (
          <ComponentRow
            key={`${c.facet}:${c.capability}:${i}`}
            c={c}
            editing={editing}
            onRemove={() => remove("all_of", i)}
            onMove={() => move("all_of", i)}
            moveLabel="→ any_of"
            onModality={(m) => setModality("all_of", i, m)}
          />
        ))}
        {editing ? <AddComponent facets={facets} onAdd={(c) => add("all_of", c)} /> : null}
      </RoleGroup>

      <RoleGroup label="any_of · at least one satisfies" empty="no alternatives">
        {recipe.anyOf.map((c, i) => (
          <ComponentRow
            key={`${c.facet}:${c.capability}:${i}`}
            c={c}
            editing={editing}
            onRemove={() => remove("any_of", i)}
            onMove={() => move("any_of", i)}
            moveLabel="→ all_of"
            onModality={(m) => setModality("any_of", i, m)}
          />
        ))}
        {editing ? <AddComponent facets={facets} onAdd={(c) => add("any_of", c)} /> : null}
      </RoleGroup>

      <RoleGroup label="integration · explicit coordination factor" empty="none">
        {recipe.integration ? (
          <ComponentRow
            c={recipe.integration}
            editing={editing}
            onRemove={() => onMutate((r) => (r.integration = null))}
            onModality={(m) => onMutate((r) => r.integration && (r.integration.modality = m))}
          />
        ) : editing ? (
          <AddComponent
            facets={facets}
            label="set integration"
            onAdd={(c) => onMutate((r) => (r.integration = c))}
          />
        ) : null}
      </RoleGroup>
    </div>
  );
}

function RoleGroup({ label, empty, children }: { label: string; empty: string; children: ReactNode }) {
  const arr = Array.isArray(children) ? children.flat() : [children];
  const hasContent = arr.some((c) => c);
  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ fontSize: 11, color: COLOR.amber, fontFamily: FONT_MONO }}>{label}</div>
      {hasContent ? children : <Faint style={{ fontSize: 11 }}>{empty}</Faint>}
    </div>
  );
}

function ComponentRow({
  c,
  editing,
  onRemove,
  onMove,
  moveLabel,
  onModality,
}: {
  c: EditComponent;
  editing: boolean;
  onRemove?: () => void;
  onMove?: () => void;
  moveLabel?: string;
  onModality?: (m: string) => void;
}) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 7, padding: "4px 0", flexWrap: "wrap", fontSize: 11 }}>
      <span aria-hidden style={{ color: COLOR.cyan }}>●</span>
      <span style={{ color: COLOR.cyan }}>{shortFacet(c.facet)}</span>
      <Faint>·</Faint>
      <span style={{ color: COLOR.text }}>{c.capability}</span>
      {editing && onModality ? (
        <TermSelect value={c.modality} options={[...MODALITIES]} onChange={onModality} width={150} style={{ fontSize: 11, padding: "2px 6px" }} />
      ) : (
        <Pill color="slate" style={{ fontSize: 11 }}>{c.modality}</Pill>
      )}
      {editing && onMove && moveLabel ? (
        <button type="button" onClick={onMove} style={linkBtn} title="move between all_of / any_of">
          {moveLabel}
        </button>
      ) : null}
      {editing && onRemove ? (
        <button type="button" onClick={onRemove} style={{ ...linkBtn, color: COLOR.red }} title="remove">
          ×
        </button>
      ) : null}
    </div>
  );
}

// -- Add a component (facet autocomplete + capability picker) -----------------

function AddComponent({
  facets,
  onAdd,
  label = "add component",
}: {
  facets: FacetSummaryDto[];
  onAdd: (c: EditComponent) => void;
  label?: string;
}) {
  const [facet, setFacet] = useState("");
  const [capability, setCapability] = useState<string>(CAPABILITIES[0]);
  const [modality, setModality] = useState<string>("hard");
  const [q, setQ] = useState("");
  const [focus, setFocus] = useState(false);

  const matches = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return facets.slice(0, 8);
    return facets
      .filter((f) => f.id.toLowerCase().includes(needle) || f.title.toLowerCase().includes(needle))
      .slice(0, 8);
  }, [q, facets]);

  const ready = facet.trim().length > 0;
  return (
    <div style={{ marginTop: 4, display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap", position: "relative" }}>
      <div style={{ position: "relative" }}>
        <input
          value={facet || q}
          onChange={(e) => {
            setQ(e.target.value);
            setFacet("");
          }}
          onFocus={() => setFocus(true)}
          onBlur={() => setTimeout(() => setFocus(false), 120)}
          placeholder="facet id…"
          style={{ ...numInput, width: 180 }}
        />
        {focus && matches.length ? (
          <div style={suggestBox}>
            {matches.map((f) => (
              <div
                key={f.id}
                onMouseDown={() => {
                  setFacet(f.id);
                  setQ(f.id);
                  setFocus(false);
                }}
                style={suggestRow}
              >
                <span style={{ color: COLOR.text }}>{shortFacet(f.id)}</span>
                <span style={{ color: COLOR.textFaint, fontSize: 11 }}>
                  {f.title}
                </span>
              </div>
            ))}
          </div>
        ) : null}
      </div>
      <TermSelect value={capability} options={[...CAPABILITIES]} onChange={setCapability} width={180} style={{ fontSize: 11, padding: "2px 6px" }} />
      <TermSelect value={modality} options={[...MODALITIES]} onChange={setModality} width={150} style={{ fontSize: 11, padding: "2px 6px" }} />
      <button
        type="button"
        disabled={!ready}
        onClick={() => {
          if (!ready) return;
          onAdd({ facet: facet.trim(), capability, modality });
          setFacet("");
          setQ("");
        }}
        style={{ ...linkBtn, color: ready ? COLOR.green : COLOR.textFaint }}
      >
        + {label}
      </button>
    </div>
  );
}

// -- Blast-radius panel (debounced preview) -----------------------------------

function BlastRadiusPanel({
  loId,
  draft,
  onGo,
}: {
  loId: string;
  draft: EditBlueprint[];
  onGo?: (id: string) => void;
}) {
  const [preview, setPreview] = useState<BlueprintReadinessPreviewDto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const signature = useMemo(() => JSON.stringify(draft.map(snakeBlueprint)), [draft]);

  useEffect(() => {
    if (timer.current) clearTimeout(timer.current);
    setPending(true);
    timer.current = setTimeout(() => {
      let alive = true;
      api
        .previewBlueprintReadiness({ learningObjectId: loId, blueprints: draft.map(snakeBlueprint) })
        .then((r) => {
          if (!alive) return;
          setPreview(r);
          setError(null);
        })
        .catch((e) => {
          if (!alive) return;
          setError(e instanceof Error ? e.message : String(e));
        })
        .finally(() => alive && setPending(false));
      return () => {
        alive = false;
      };
    }, 400);
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signature, loId]);

  const cur = preview?.current.readiness ?? null;
  const prop = preview?.proposed.readiness ?? null;
  const delta = cur != null && prop != null ? prop - cur : null;
  const bnChanged =
    preview &&
    (preview.current.bottleneck?.facet !== preview.proposed.bottleneck?.facet ||
      preview.current.bottleneck?.capability !== preview.proposed.bottleneck?.capability);

  return (
    <div style={{ border: `1px solid ${COLOR.border}`, padding: "10px 12px", background: COLOR.bgInput, alignSelf: "start" }}>
      <SectionHeader style={{ marginTop: 0, marginBottom: 7 }}>Projected impact</SectionHeader>
      <div style={{ color: COLOR.textFaint, fontSize: 11, lineHeight: 1.45, marginBottom: 10 }}>
        Preview of how this draft would change readiness, the active bottleneck, and connected goals. Nothing is applied until the proposal is reviewed.
      </div>
      {error ? (
        <Faint style={{ color: COLOR.textFaint }}>preview unavailable · {error}</Faint>
      ) : !preview ? (
        <Faint>{pending ? "computing…" : "—"}</Faint>
      ) : (
        <>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
            <div>
              <div style={{ fontSize: 11, color: COLOR.textFaint }}>current</div>
              <div style={{ fontFamily: FONT_MONO, color: COLOR.cyan, fontSize: 16 }}>{pct(cur)}</div>
            </div>
            <span style={{ color: COLOR.textFaint }}>→</span>
            <div>
              <div style={{ fontSize: 11, color: COLOR.textFaint }}>proposed</div>
              <div style={{ fontFamily: FONT_MONO, color: COLOR.cyan, fontSize: 16 }}>{pct(prop)}</div>
            </div>
            {delta != null && Math.abs(delta) > 0.0005 ? (
              <Pill color={delta >= 0 ? "green" : "red"}>
                {delta >= 0 ? "+" : ""}
                {Math.round(delta * 100)}%
              </Pill>
            ) : (
              <Faint style={{ fontSize: 11 }}>no change</Faint>
            )}
          </div>
          {prop != null ? (
            <div style={{ marginBottom: 8 }}>
              <BlockBar value={prop} width={12} color={COLOR.cyan} />
            </div>
          ) : null}

          <div style={{ fontSize: 11, color: COLOR.textFaint }}>bottleneck</div>
          <div style={{ fontSize: 12, marginBottom: 8 }}>
            {preview.proposed.bottleneck ? (
              <span style={{ color: bnChanged ? COLOR.amber : COLOR.text }}>
                {shortFacet(preview.proposed.bottleneck.facet)} · {preview.proposed.bottleneck.capability}
                {bnChanged && preview.current.bottleneck ? (
                  <Faint>
                    {" "}
                    (was {shortFacet(preview.current.bottleneck.facet)} · {preview.current.bottleneck.capability})
                  </Faint>
                ) : null}
              </span>
            ) : (
              <Faint>none</Faint>
            )}
          </div>

          {preview.identifiabilityWarnings.length ? (
            <div style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 11, color: COLOR.textFaint }}>identifiability</div>
              {preview.identifiabilityWarnings.map((w, i) => (
                <div key={i} style={{ fontSize: 12, color: COLOR.amber, lineHeight: 1.4 }}>
                  ⚠ {w}
                </div>
              ))}
            </div>
          ) : null}

          {preview.affectedGoals.length ? (
            <div>
              <div style={{ fontSize: 11, color: COLOR.textFaint }}>affected goals</div>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 3 }}>
                {preview.affectedGoals.map((g) => (
                  <span
                    key={g.goalId}
                    onClick={() => onGo?.(g.goalId)}
                    role={onGo ? "button" : undefined}
                    style={{ cursor: onGo ? "pointer" : "default" }}
                  >
                    <Pill color="amber">{g.title}</Pill>
                  </span>
                ))}
              </div>
            </div>
          ) : null}
          {pending ? <Faint style={{ fontSize: 11 }}>updating…</Faint> : null}
        </>
      )}
    </div>
  );
}

// -- styles -------------------------------------------------------------------

const toggleBtn: CSSProperties = {
  fontFamily: FONT_MONO,
  fontSize: 11,
  background: "transparent",
  border: `1px solid ${COLOR.borderStrong}`,
  color: COLOR.amberLink,
  padding: "4px 9px",
  cursor: "pointer",
};

const linkBtn: CSSProperties = {
  fontFamily: FONT_MONO,
  fontSize: 11,
  background: "transparent",
  border: "none",
  color: COLOR.amberLink,
  cursor: "pointer",
  padding: "0 2px",
};

const numInput: CSSProperties = {
  fontFamily: FONT_MONO,
  fontSize: 12,
  background: COLOR.bgInput,
  color: COLOR.text,
  border: `1px solid ${COLOR.borderFocus}`,
  padding: "2px 6px",
  outline: "none",
};

const rationaleInput: CSSProperties = {
  ...numInput,
  flex: 1,
};

const fileBar: CSSProperties = {
  marginTop: 12,
  display: "flex",
  gap: 8,
  alignItems: "center",
  paddingTop: 10,
  borderTop: `1px solid ${COLOR.border}`,
};

const ruleLegendStyle: CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: "4px 16px",
  marginBottom: 10,
  color: COLOR.textDim,
  fontSize: 11,
};

const suggestBox: CSSProperties = {
  position: "absolute",
  top: "100%",
  left: 0,
  zIndex: 10,
  minWidth: 220,
  maxHeight: 200,
  overflowY: "auto",
  background: COLOR.bg,
  border: `1px solid ${COLOR.borderStrong}`,
  boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
};

const suggestRow: CSSProperties = {
  display: "flex",
  flexDirection: "column",
  padding: "4px 8px",
  cursor: "pointer",
  borderBottom: `1px solid ${COLOR.border}`,
};
