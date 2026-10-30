# PLAN_031: v0.28.0, 16 states and exact recovery (plan only)

Status: **preregistered (plan only; no build authorized, no code, no data)**. Study BRUTE-0280-SIXTEEN-STATE-ID-031. Parent: BRUTE-0270-SYMMETRY-FREE-030.

## Question
Building on S5, can exact search finish 16-state worlds, and can Brute recover the exact machine (ID) at 12 and 16 states, and is ID limited by search or by what the trace can tell apart?

## Why
Study 030 (Observed): S5 cleared 12 states (U 0.047 [0.004, 0.093] vs S1 0.200; X 5/12 [0.19, 0.68]; GSC5 PASS) but finished 0/12 at 16 states (U 0.240 [0.171, 0.308]). ID was 0/12 at 12 and 16 states for every arm even though identify ran on all 24 S5 cases there, and only 6/12 at 8 states where X was 12/12. Inferred: at 8 states some traces admit more than one consistent machine, so ID is bounded by identifiability as well as by search; the 030 instruments cannot separate the two. The hard cap did not explain the 030 gain (S5 vs S5_softcap -0.001 [-0.009, 0.006]). S5 was worse on noisy 12-state traces (stress U 0.585 vs S4 0.370; not gated).

## Arms
- **S6**: S5 plus two pre-declared changes aimed at 16 states: (1) one incremental solver per step, with each query's region clauses guarded by an activation literal and solved under assumptions, so learned clauses carry across queries and the per-query rebuild cost (S5 build_skips mean 118.9 at scale16) is removed; (2) queries ordered by ascending candidate-region size, so cheap queries spend budget first. Same hard cap as S5. Plus the identify probe below
- **S5**: v0.27.0 arm, unchanged in search (control); identify probe applied identically
- **S1**: baseline, unchanged (comparator)
- **S6_noorder**: ablation: S6 without query ordering (separates incremental reuse from ordering)

Identify probe: after search, identify asks for a second consistent machine that is not isomorphic to the first (blocking clause on the first machine's canonical relabelling). Each case gets one label: ID (exactly one class, equal to truth), AMB (two or more non-isomorphic consistent machines found: the trace does not identify the machine), WRONG (single class not equal to truth: a soundness failure), IDU (identify ran out of budget). Identify budget 60 s per case, outside the step budget, the same for every arm.

Budget: 55 s per step, 10 s per query cap, as in studies 028-030. Soundness: every S6 certificate rechecked by the frozen exact reference; any mismatch with S1/S5 or truth on an answered query is a FAIL; any WRONG is a FAIL.

## Seeds (fresh, 97x0001)
scale8 9710001-9710012, scale12 9720001-9720012, scale16 9730001-9730018, control 9740001-9740006, smoke 9790001-9790030. Main 48 plus stress 6 = 54 cases. A ledgered seedcheck_031 must confirm disjointness before any seed is drawn.

## Gates
- GSC6 (headline): a) 0 mismatches; b) U(S6) - U(S5) at 16 states <= -0.06, CI upper < 0; c) X(S6, scale16) >= 4/18; d) F(S6) = 0.
- GID6 (exact recovery): a) WRONG = 0 for every arm; b) ID(S6, scale12) >= 4/12; c) IDU(S6, scale12) <= 2/12.
- GQB6: S6 max query <= 10.5 s. G10 (U 0 and ID 6/6 on controls), GS_ref, GTI, G_PROC, G_RT (<= 1800 s), G_recount as in study 030.
- Informational: S6 vs S6_noorder U difference; S6 vs S1; ID/AMB/IDU at scale8 and scale16; stress U at eps 0.05 for all arms (030 showed S5 worse there); throughput ratios; reported, not gated.

## Failure
any GSC6 or GID6 clause failing, GQB6 above 10.5 s, any false certificate or WRONG identification; failures are published, not tuned.

## Limits
- noise-free masks for the headline; eps 0.05 stress gates F only
- one hardware profile, one author; no independent replication
- AMB depends on the identify budget; an AMB label is a lower bound on non-identifiability only when the second machine is found
- if S6 fails GSC6, 16 states remain open and the next bottleneck must be measured, not assumed

No build until a ledgered build_authorization_031.
