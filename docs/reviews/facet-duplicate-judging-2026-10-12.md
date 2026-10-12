# Facet duplicates: LLM judges against embedding similarity (2026-10-12)

The owner suspected that many facets in the `linear_algebra` vault are duplicates. Slice 2 T5's report had found no duplicates by word overlap, and 13 "embedding-only mutual nearest" pairs that nobody had judged.

This study had two LLM judges label facet pairs blind, then compared their labels with the embedding similarity. The raw data is in `docs/reviews/data/facet-duplicate-judging-2026-10-12.json`.

## Method

- **Vault.** A backup copy of `fixtures/linear_algebra`: 39 facets, 741 possible pairs. The vectors are T5's stored `facet/definition` vectors (`qwen/qwen3-embedding-8b`). Cosine is mean-centred, computed with T5's `RegistryIndex`, so it matches the report.
- **Pairs.** 98 in total:
  - each facet's 3 nearest neighbours, which gave 73 pairs and included all 13 mutual-nearest pairs;
  - 25 random pairs from the rest, as controls.
- **Judges.** Claude Sonnet and Claude Haiku, run independently and blind to cosine. Each saw only the two full definition texts, in shuffled order.
- **Labels.**
  - `duplicate`: the same skill stated twice.
  - `near_duplicate`: the same core skill, with a different scope or framing (a special case, a worked instance, a bundled extra).
  - `related_distinct`.
  - `unrelated`.

  "Merge-worthy" means `duplicate` or `near_duplicate`.

## Results

**The judges agree on merge-worthiness.**
- They agree on 97 of 98 pairs (κ 0.95).
- On all four labels they agree on 85% (κ 0.68). The disagreements are almost all `related_distinct` versus `unrelated`, which doesn't matter for deduplication.
- The one merge disagreement is the zero vector in F^n against the overloaded symbol 0, at cosine 0.39.
- A Haiku-class judge is enough for this decision.

**About a quarter of the facets are redundant.** The 12 pairs both judges call merge-worthy form 5 clusters, covering 15 of the 39 facets. Merging every cluster would leave 29 facets.

| Cluster | Facets |
|---|---|
| "A vector space is a set with addition and scalar multiplication satisfying…": cites the axioms, lists them, an introductory version, the axiom list, and the "vectors/points" terminology | 5 |
| The zero vector in F^n: the length-n list, the additive identity, and the overloaded symbol 0 | 3 |
| Commutativity of addition in F^n stated twice, plus the coordinatewise-proof method it instantiates | 3 |
| Addition defined as an operation on a set | 2 |
| Complex field laws as a special case of the scalar laws over R or C | 2 |

**Embeddings shortlist well but give no usable cutoff.**
- AUC for merge-worthy against the rest: 0.91 (Sonnet's labels) and 0.92 (Haiku's).
- Merge-worthy pairs span cosine 0.29 to 0.83. The highest non-merge pair is at 0.70: complex addition against complex multiplication.
- No threshold separates them. This confirms R4: embeddings shortlist, and a judge decides.

**Recall of the shortlist.**
- Mutual nearest neighbours catch only 5 of the 12. Inside a cluster, each facet's single nearest neighbour is just one of its duplicates.
- Rank 1 from either side catches 10 of 12.
- Every merge-worthy pair is within rank 4.
- None of the 25 controls is merge-worthy.
- A top-4 shortlist per facet plus a judge finds all of them. Judging whole groups fits better than judging pairs and then linking them.

## Where the duplicates came from

Every facet in these clusters has `provenance.origin = sourceset_synthesis`, and all of them cite the same source extraction (`ext_01KY2ZX9193YPC73DT6HXFFNDC`), often from overlapping spans:
- the zero-vector facets come from spans 130–136;
- the vector-space facets come from spans 201–207.

They are duplicates minted within one run by different shards or inventory claims, not appends that missed existing facets.

Source-set synthesis consolidates concepts across shards: it folds identical titles, then runs a model-assisted near-duplicate pass. Facets get only the lexical near-duplicate gate (Jaccard ≥ 0.85 over title and claim tokens, `synthesis_gates.py`), and every duplicate here is worded too differently to trip it.

T5's nominations and the D2 mint gate compare candidates with facets already in the vault, which on a first ingest is empty. Nothing compares one run's candidate facets with each other on meaning.

## Regression set for the facet-identity stage

**Must merge.** These are the 12 agreed pairs, in the data file where both `sonnet` and `haiku` are merge-worthy.

**Must stay distinct.** These pairs are judged `related_distinct` by both judges at cosine ≥ 0.5:
- 0.70: complex addition (componentwise) vs complex multiplication (distributing, i² = −1);
- 0.58: the form a + bi vs embedding the reals and i² = −1;
- 0.57: arrow translation invariance vs the tip-to-tail sum construction;
- 0.57: the definition of a list vs list equality;
- 0.54: the complex multiplication procedure vs a proof strategy for complex-multiplication identities;
- 0.52 (two pairs): embedding the reals vs multiplication, and the definition of complex numbers vs the addition rule.

## Owner decisions (2026-10-12)

- Prevent duplicates at ingest instead of relying on later cleanup.
- An LLM judge alone is enough for a one-off cleanup of existing vaults.
- The judge's decisions apply live, `merge` and `absorb` alike, each with one-tap undo (option c). A cheap judge is enough. The candidates are GPT-6 Luna (Codex, on the owner's subscription), Claude Haiku (through OpenRouter) or the Decider, which works one pair at a time.

The stage is "Facet identity at mint time, and a dedupe command" in `docs/specs/implementation_handoffs.md` §4.
