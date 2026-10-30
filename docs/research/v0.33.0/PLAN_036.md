# PLAN_036: v0.33.0, repeated reads versus noise budget (plan only)

Status: **preregistered (plan only; no build authorized, no code, no data)**. Study BRUTE-0330-REPEATED-READS-036. Parent: BRUTE-0320-NOISY-ACTIVE-ID-035.

## Branch taken
The user's rule: if GA10 passes, take 16 states or a generality step; otherwise diagnose. GA10 failed on a-d (study 035: noisy12 A10 ID 0/12 [0,0.24], IDU 12/12 [0.76,1]; paired ID(A10)-ID(S7) 0.00 [0,0]), so this plan diagnoses. Plan 035 next_if_fail: 'if GA10 b or c fails, noise cancels the active gain and the next plan studies repeated experiments (r) versus budget'. This plan does that and adds a bisection least-budget search.

## Question
If every reading is repeated r times and majority-voted before the solver sees it, does the residual flip count fall low enough that the least noise budget is found inside the 10 s query cap, so that active identification works on noisy traces, and what do the extra reads cost?

## Why
Study 035 (Observed): on all 24 noisy cases A10's B = 0 search was UNSAT and the upward least-B search (B = 1, 2, ...) hit the 10 s cap after 9-12 queries, below the true flip count (13-23 in 177 readings), so B stayed 0 and A10 stopped IDU. A10_fixed (B = 27 from the start) was IDU on every case, clean included. Inferred: the UNSAT proofs just below the least B are the hard queries, and their hardness grows with B. At eps 0.05 a 3-read majority flips with probability 3e^2-2e^3 = 0.00725 (about 1.3 expected flips in 177 readings) and a 5-read majority with probability 0.00116 (about 0.2) (Exact arithmetic; Inferred effect).

## Hypotheses
- H1_repeat: A11_r3 (A10 on a majority-of-3 trace, least B by bisection) identifies noisy 12-state machines: ID(A11_r3) - ID(A10) >= +0.25 at noisy12 with WRONG 0 within budget.
- H2_r_vs_budget: more repeats lower the final B and the capped-query count monotonically (r = 1, 3, 5), at a read cost linear in r.
- H3_no_clean_cost: on clean traces the majority equals the single reading, so A11_r3 labels equal A9 labels on every clean case and its final B is 0.
- H4_cap: arming the host timer at 9.5 s keeps every query of every arm, S7 included, under 10.5 s.

## Arms
- **A11_r3**: new file brute/scalesearch11.py: A10 logic with two changes. (1) Every reading, on the base trace and on every executed separating word, is taken r = 3 times at the same position (the world wrapper re-reads the current output without stepping) and the majority is the reading the solver sees; the solver never sees the raw reads. (2) The least B is found by bisection over [0, B_max(r)] (first B = 0, then B_max(r), then midpoints), not by the upward chain; B never falls and is re-bisected only on a new contradiction. B_max(r) = the declared-rate B_end rule applied to the majority flip rate. Stop rule, K and the rival searches as A10.
- **A11_r5**: A11 with r = 5.
- **A11_r3_up**: ablation: A11_r3 with A10's upward least-B search instead of bisection; separates the effect of repeats from the effect of the search order.
- **A10**: frozen v0.32.0 arm (brute/scalesearch10), r = 1, unchanged (control; its 035 behaviour is the prediction).
- **S7**: passive noisy v0.29.0 arm with the identify probe, unchanged; reported and in GQB11.
- **S5**: passive clean v0.27.0 arm, unchanged; gated only on clean cases and controls (declared before data, because 035 showed it answers WRONG on noisy traces by design); its noisy labels are reported.

Query cap: as 035 (host-side threading.Timer calling the solver's interrupt; brute/ stays host-agnostic), but the timer is armed at 9.5 s instead of 10 s for every arm, to absorb the interrupt latency that let S7 reach 10.538 s in 035. An interrupted query counts as unknown (IDU path).

Noise: independent reading flips at eps 0.05 on every raw read on noisy cases (repeats are independent draws); eps 0 on clean cases and controls; the declared rate is given to every noise-aware arm.

Cost accounting: reads (raw world output reads), steps (world actions) and extra actions are reported per arm; a repeated read costs one read and no step.

Labels: as 035: ID, IDF, AMB, WRONG, IDU. A noisy case is 'within budget' for an arm if the true flip count of the trace that arm's solver sees is <= its B_max at every step; WRONG is gated on within-budget cases and reported on the rest.

## Cases (declared before data)
noisy_scale8 12 (seeds 10210001-10210012), noisy_scale12 12 (10220001-10220012), clean_scale12 12 (10230001-10230012), noisy_scale12_extra 6 (10240001-10240006), control 6 (10260001-10260006); smoke 10290001-10290030. Total 48. fresh 102x00NN ranges; pre-plan scan (Observed, 2026-10-30 19:18 EDT): 0 tokens matching 1021-1024/1026/1029 followed by 00NN in tracked text and 0 in the sealed .gz archives (1025 skipped: one 10250013 token in an archive). Drawn only after a ledgered seedcheck_036.

## Gates
- **GR11_headline**: a: WRONG = 0 for A11_r3 and A11_r5 on every clean case and every within-budget noisy case; WRONG = 0 for S7 on its within-budget noisy cases and for S5 on clean cases. b: ID(A11_r3, noisy_scale12) - ID(A10, noisy_scale12) >= +0.25 (3/12), paired seed-bootstrap 95% CI lower bound > 0. c: ID + IDF (A11_r3, noisy_scale12) >= 4/12. d: IDU(A11_r3, noisy_scale12) <= 3/12.
- **GBIS11**: search order: IDU(A11_r3, noisy_scale12) <= IDU(A11_r3_up, noisy_scale12); reported with the paired difference and CI.
- **GRB11**: (secondary, r versus budget) mean final B and mean capped queries are non-increasing in r over A10 (r=1), A11_r3, A11_r5 on the 18 pooled noisy-12 cases; reads per case reported with Wilson/bootstrap CIs; failing it does not fail the headline.
- **GNR11**: no clean cost: on clean_scale12 and controls, A11_r3 and A11_r5 labels equal the in-run A10 labels (A10 is the clean reference because GNR10 showed A10 = A9 on every clean case) and their final B is 0 on every clean case.
- **GQB11**: every SAT query of every arm, S7 included, <= 10.5 s wall.
- **G_sound**: 0 unsound separating words (re-simulated against the majority trace with the recorded flips); truth consistent with every extended majority trace within budget.
- **G10**: controls: ID 6/6 for A11_r3, A11_r5 and S5.
- **GS_ref**: independent CNF reference on noisy_scale8 A11_r3: same labels, same 'no rival up to N under B' verdicts and the same least B; at least 1 audited verdict with B > 0, otherwise GS_ref is reported as 'raised-B not exercised' and fails; mutation detection 20/20.
- **G_RT**: whole run <= 1800 s.
- **G_recount**: independent recount reproduces every label.
- **GTI**: all test modules pass.
- **G_PROC**: prereg -> build_authorization_036 -> seedcheck_036 -> source_freeze_036 -> run_start_036 -> run_end_036, commit-order file, main sealed.

## Runtime
about 900-1500 s on 8 workers (48 cases, 6 arms; 035 mean case wall 52.9 s with A10 IDU at the cap on every noisy case; repeats add reads, not clauses). The 1800 s cap is tight; if the pre-freeze projection exceeds 1500 s, noisy_scale12_extra is dropped by a ledgered pre-run deviation before the freeze, never after (Inferred).

## Failure and next steps
- Counts as failure: any GR11 clause, GNR11, GQB11, G_sound, G10 or GS_ref failing, or any A11 WRONG on a clean or within-budget case; failures are published, not tuned.
- If it passes: v0.34.0: A11 at 16 states as the headline, then action noise and a mis-declared rate.
- If it fails: diagnose the failing clause: if b fails with IDU still high, replace the per-B UNSAT chain with an incremental cardinality encoding or a MaxSAT least-B solve; if b fails with AMB, repeats cost too many actions against K; if a fails, the majority trace's within-budget rule is wrong.

## Limitations
- repeated reads assume the noise is independent per read; correlated or sticky noise is untested.
- the declared bound N and the noise rate are priors the arms are given.
- r in {3, 5}, K, 120 s and B_max fixed in advance.
- no 16-state cases (deferred to the pass branch).
- greedy shortest word per pair, not optimal experiment design.
- one world family (worlds_026), one hardware profile, one author.

## What Brute can't do yet (carried from v0.32.0)
- It identifies no noisy world: A10 IDU 24/24. *Observed.*
- It identifies no 16-state world. *Observed.*
- A fixed noise budget costs every clean 12-state case (A10_fixed IDU 12/12). *Observed.*
- The in-solver cap overshot on S7 (10.538 s). *Observed.*
- The reference audit has not exercised a raised-B verdict. *Inferred.*
- The N prior, action noise and a mis-declared rate are untested. *Open.*
