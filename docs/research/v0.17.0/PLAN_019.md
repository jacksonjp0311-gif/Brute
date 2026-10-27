# BRUTE_PLAN_019: v0.17.0 sequential margin and a 3-action block (readable summary)

`experiments/BRUTE_PLAN_019.json` is the frozen plan; if this summary differs, the JSON wins. Study BRUTE-0170-SEQUENTIAL-MARGIN-019, branch `plan/v0.17.0` from main `e92a7c4` (v0.16.0 released).

## Why

The v0.16.0 tolerant region RGN4 was sound under iid observation noise (0 false certificates in 240 noisy cases) but covered only 0.066 of slots at eps 0.02, below the 0.10 bar (GNS clause c FAIL, *Observed*). It used one worst-case flip budget m (4 or 5) from the first reading on. The oracle margin reached 0.316 (*Observed*), so the loss is in the margin.

## Headline arm RGNB4 (sequential margin)

- At step t, RGNB4 allows at most m(b_t) flipped bits among the b_t observed bits seen so far.
- The boundary m(b) is the smallest nondecreasing integer sequence whose exact crossing probability under Bernoulli(0.02) flips stays within 0.01 · b / B by bit b (linear alpha spending, exact rationals).
- Example (*Exact*): for B = 58, m is 1 from bit 1, 2 from bit 2, 3 from bit 14, and 4 from bit 35.
- Soundness (*Exact*, conditional): with no crossing and n* ≤ 4, every certificate is correct. The per-case probability of a false certificate is ≤ 0.01 under the iid model.

## Gates (12 gated)

| Gate | Threshold (short) | Prediction |
| --- | --- | --- |
| **GNB (headline)** | (a) 0 false without crossing; (b) CP95 ≤ 0.05; (c) dC(RGNB4 − RGN4) at eps 0.02, CI lower > 0; (d) C(RGNB4) ≥ 0.10, CI lower > 0.05 | a *Exact* PASS; b, c *Inferred* PASS; d *Open*, leaning FAIL |
| GNB_post_burn | RGNB4_0 = RG4 after burn-in on eps 0; RGNB4 0 false on eps 0 | *Inferred* PASS |
| GA3 | 3-action block: RG4_3 0 false at eps 0; RGNB4_3 0 false without crossing; CP95 ≤ 0.10 | *Inferred* PASS |
| GS_a7, G_recount, GS_ref7, GAPI7, G10, G12, G13, GTI, G_RT, G_HB | as study-018, extended to the new arms and block | *Inferred* / *Exact* PASS |

## Cases and seeds (*Exact*)

- Main block: 120 two-action seeds (8510001–8540048) × eps {0, 0.01, 0.02} = 360 cases, plus 120 stress cases at eps 0.05.
- Alphabet3 block: 48 rand4a3 seeds (8550001–8550048) × eps {0, 0.02} = 96 cases, with random actions.
- Smoke seeds: 8590001–8590030. All ranges are disjoint from every earlier one (all ≤ 8490030).

## Process

- The order is unchanged: seeds, reference, implementation, rate math (factor 1.75), source freeze, then a scoring freeze ≥ 600 s before run_start, one run under a 2 h cap, then seal, gates and release.
- New: the run_start ledger entry is committed before any stream starts (deviation #100 item 1).
- Deviations start at #101.
- No CI workflows.
