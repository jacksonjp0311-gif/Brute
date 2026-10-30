# PLAN_035: v0.32.0, noisy active identification (plan only)

Status: **preregistered (plan only; no build authorized, no code, no data)**. Study BRUTE-0320-NOISY-ACTIVE-ID-035. Parent: BRUTE-0310-SOUND-ACTIVE-ID-034.

## Branch taken
The user's rule: if A9's headline passes, combine experiments with an adaptive noise budget or extend toward 16 states (the deferred branch); otherwise diagnose. GA9 passed on a-d (study 034: scale12 A9 ID 9/12 [0.47,0.91], WRONG 0/36, paired A9-S5 +0.75 [0.50,1.00]), so this plan takes the deferred branch: the headline is A9 with an adaptive noise budget on noisy traces. The 16-state extension is a secondary gate. It also fixes the query-cap overrun that failed GQB9 (10.888 s).

## Question
Can sound active identification survive reading noise if the noise budget stays at zero until the exact search contradicts the trace, and can it reach 16-state worlds once the per-query cap is enforced inside the solver?

## Why
Study 034 (Observed): A9 WRONG 0/36, scale12 ID 9/12 vs 0/12 passive; scale16 ID 0/6 (4 IDU at the query cap, 2 AMB with K=64 spent); GQB9 FAIL (one query 10.888 s because the 10 s cap is checked between solver calls). Study 032 (Observed): a fixed noise budget (S7, B_end 27) was sound but paid on clean traces (GNR7 FAIL, clean-12 U +0.362) and finished no noisy world (X_inf 0/12).

## Hypotheses
- H1_adaptive_noise: A10 (A9 + adaptive budget: B=0 until the exact search for size <= N is UNSAT on the current trace, then the smallest B with a consistent machine, raised only on new contradictions, capped at B_max) identifies noisy 12-state machines up to the flips it can explain, with WRONG 0 on cases whose true flip count is within B_max.
- H2_no_clean_cost: on clean traces the adaptive budget never leaves 0, so A10 and A9 give the same labels on every clean case.
- H3_sixteen: with an in-solver cap and K=128 for scale16, A10 identifies some 16-state machines (informational lower bound 2/12).
- H4_cap: a solver-side interrupt keeps every query under the 10.5 s bound.

## Arms
- **A10**: A9 (034) plus the adaptive noise budget. Flip literals are added only on reading positions; the budget B starts at 0; when the exact search over n <= N is UNSAT, B rises to the least value that is SAT (searched 1..B_max) and never falls. Separating words are executed and re-read r = 3 times (majority vote) once B > 0; at B = 0 they are executed once, as in A9. Stop rule as A9, with every rival search run under the current B. K = 64 extra actions at 8/12 states, K = 128 at 16 states.
- **A10_fixed**: ablation: A10 with B fixed at B_end from the declared rate (the v0.29.0 S7 rule) from the first round; tests whether adaptivity, not the budget itself, removes the clean cost.
- **A9**: frozen v0.31.0 arm (brute/scalesearch9), unchanged except it receives the in-solver cap hook from the host (no source change; the hook is the host's timer). On noisy traces A9 is expected to report AMB or IDU, never ID on a contradiction.
- **S7**: passive noisy v0.29.0 arm with the 031 identify probe, unchanged.
- **S5**: passive clean v0.27.0 arm with the identify probe, unchanged.

Query cap: the core stays host-agnostic: brute/ exposes an optional interrupt callback on each solve (no threads, no I/O); the runner in experiments/ arms a threading.Timer at 10 s that calls the solver's interrupt (CaDiCaL solve_limited with expect_interrupt). A query that is interrupted counts as unknown (IDU path), as before.

Noise: independent reading flips at eps 0.05 on noisy cases; eps 0 on clean cases and controls; the declared rate is given to A10_fixed and S7, B_max = B_end(eps) for A10.

Labels: ID (single behaviour class from the start state up to N, equal to the truth); IDF (from the current state on); AMB; WRONG; IDU (budget). A noisy case is 'within budget' if its true flip count is <= B_max at every step; WRONG is gated on within-budget cases and reported on the rest.

Budget: 120 s per arm per case at 8/12 states, 240 s at 16 states; 10 s per SAT query, enforced inside the solver; eps as declared.

## Seeds (fresh, 101x0001)
noisy scale8 10110001-10110012, noisy scale12 10120001-10120012, clean scale12 10130001-10130012, scale16 10140001-10140006, control 10150001-10150006, smoke 10190001-10190030. Drawn only after a ledgered seedcheck_035.

## Gates
- GA10 (headline): a) WRONG = 0 for A10 on every clean case and every within-budget noisy case; WRONG = 0 for S5 and S7 on the same cases; b) ID(A10, noisy_scale12) - ID(S7, noisy_scale12) >= +0.25 (3/12), paired seed-bootstrap 95% CI lower bound > 0; c) ID + IDF (A10, noisy_scale12) >= 4/12; d) IDU(A10, noisy_scale12) <= 3/12.
- GNR10: no clean cost: on clean_scale12 and controls, A10 labels equal A9 labels on every case and A10's final B is 0 on every clean case.
- GAD10: adaptivity: ID(A10, noisy_scale12) - ID(A10_fixed, noisy_scale12) >= 0 and ID(A10, clean_scale12) - ID(A10_fixed, clean_scale12) >= +0.17 with paired CI lower bound > 0.
- G16: (secondary) ID(A10, scale16_clean) >= 2/6 and WRONG 0; reported with Wilson CI; failing it does not fail the headline.
- GQB10: every SAT query of every arm <= 10.5 s wall (in-solver cap).
- G_sound: 0 unsound separating words (re-simulated with the recorded flips); truth consistent with every extended trace within budget.
- G10: controls: ID 6/6 for A10 and S5.
- GS_ref: independent CNF reference on noisy_scale8 A10: same labels, same 'no rival up to N under B' verdicts, same least B; mutation detection 20/20.
- G_RT: whole run <= 1800 s.
- G_recount: independent recount reproduces every label.
- GTI: all test modules pass.
- G_PROC: prereg -> build_authorization_035 -> seedcheck_035 -> source_freeze_035 -> run_start_035 -> run_end_035, commit-order file, main sealed.

Runtime: about 1000-1600 s on 8 workers (48 cases, 5 arms; 034 A9 means 0.45 s at 8, 6.9 s at 12, 46 s at 16 states; noisy search costs more, and 16 states get 240 s). The 1800 s cap is tight; G_RT fails above it (Inferred).

Failure: any GA10 clause, GNR10, GQB10, G_sound or G10 failing, or any A10 WRONG on a clean or within-budget case; failures are published, not tuned.

## Next
- If GA10 passes: v0.33.0: adaptive noise budget for action noise and a mis-declared rate; 16 states as the headline.
- If it fails: diagnose the failing clause: if GNR10 fails, adaptivity leaks budget onto clean traces; if GA10 b or c fails, noise cancels the active gain and the next plan studies repeated experiments (r) versus budget.

## Limitations
- the declared bound N and the noise rate are priors the arms are given.
- one noise model (independent reading flips at a correctly declared rate).
- majority re-reads (r=3) cost actions and are fixed in advance.
- K, 120 s / 240 s and B_max fixed in advance.
- greedy shortest word per pair, not optimal experiment design.
- one world family (worlds_026), one hardware profile, one author.
- 16 states secondary (6 cases).
