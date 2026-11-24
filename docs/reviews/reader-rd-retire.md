# Reader workbench v2, RD-retire: parity rows

The parity matrix (spec §21.1) lists, for each surface of the old Reader, where it lives on the desks and the proof that
it does. RD-retire deletes `ReaderScreen` once every row passes its proof. Each section below is one branch's rows.

## reader/rd7b-inline-checks-ui

| Old Reader surface | On the desks | Proof |
|---|---|---|
| Cold follow-ups (RW6b) (§21.1, "Unchanged (commitments), and hosted inline (§12.6)") | Unchanged: a follow-up is a `test_me_later` commitment, served by Today as before (the RW6b tests still pass). Hosted inline: a due follow-up shows its closed marker before its host passage and opens on the desks through `check.begin_inline`, on the item Today would serve, cold; RW6b's serve-time gate holds it on both surfaces, because the inline opening serves only what the serving view's `servable` allows. | `tests/test_reader_rd7b_cold_followup_parity.py`: a due cold follow-up opens inline, cold, on Today's item; under the gate (an exposure since its valuation) Today holds it and the inline opening refuses with `nothing_to_serve`. The desks' side (marker, check now, card, veils) is in `screens/desks/checks/deskChecks.test.tsx` and the harness's `checks` run. |
