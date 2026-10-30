# PLAN_030: v0.27.0, symmetry-free exact search S5 (plan only)

Status: **preregistered (plan only; no build authorized, no code, no data)**. Study BRUTE-0270-SYMMETRY-FREE-030. Parent: BRUTE-0260-QUERY-THROUGHPUT-029.

## Question
Does removing symmetry-breaking clauses from S4 and making the per-query cap hard, as S5, let exact search finish 12-state worlds that S1 cannot?

## Why (Observed in study 029)
In study 029 the gated S4 matched S1 (U diff -0.019 at 12 states; GSC4 b, c FAIL). The descriptive arm S4_nosym reached U 0.079 [0.020, 0.149] and X 6/12 at 12 states, with F 0 and 0 mismatches vs S1 on 17,207 queries. That arm was seen after data, so it must be tested on fresh seeds before any claim. S4 also broke the 10.5 s query bound (15.33 s on scale16; GQB FAIL), and the inferred cause is an unchecked RegionK build or a Glucose chunk overrun.

## Arms
- **S5**: S4 with no symmetry-breaking clauses (S4_nosym promoted unchanged in search logic), plus a hard query cap: the region build inside a query checks the wall clock, and each solver chunk is bounded by a conflict budget sized so that a chunk cannot pass the remaining cap; a query that would pass the cap returns unknown
- **S4**: v0.26.0 arm, unchanged (control)
- **S1**: baseline, unchanged (headline comparator)
- **S5_softcap**: ablation: S5 with S4's soft cap (separates the cap fix from symmetry removal)

Budget: 55 s per step, 10 s per query cap, as in studies 028 and 029. Soundness: every S5 certificate rechecked by the frozen exact reference; any mismatch with S1/S4 or truth on an answered query is a FAIL.

## Seeds (fresh, 96x0001)
scale8 9610001-9610012, scale12 9620001-9620012, scale16 9630001-9630012, control 9640001-9640006, smoke 9690001-9690030. Main 42 plus stress 9 = 51 cases.

## Gates
- GSC5 (headline): a) 0 mismatches; b) U(S5) - U(S1) at 12 states <= -0.08, CI upper < 0; c) X(S5, scale12) >= 5/12; d) F(S5) = 0.
- GQB5: S5 max query <= 10.5 s. G10, GS_ref, GTI, G_PROC, G_RT (<= 1800 s), G_recount as in study 029.
- Informational: S5 vs S5_softcap, S5 vs S4, S5/S1 throughput.

## Failure
any GSC5 clause failing, GQB5 above 10.5 s, or any false certificate; failures are published, not tuned.

## Limits
- noise-free masks for the headline; eps 0.05 stress checks F only
- one hardware profile
- S4_nosym's 029 result was seen before this plan; only fresh seeds test it
- 16-state worlds are expected to remain mostly unknown

No build until a ledgered build_authorization_030.
