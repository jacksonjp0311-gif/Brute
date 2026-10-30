# PLAN_034: v0.31.0, sound active identification (plan only)

Status: **preregistered (plan only; no build authorized, no code, no data)**. Study BRUTE-0310-SOUND-ACTIVE-ID-034. Parent: BRUTE-0300-ACTIVE-EXPERIMENTS-033.

## Branch taken
The user's rule: if A8 works, combine active experiments with an adaptive noise budget or extend A8 toward 16 states; if A8 does not work, diagnose why. A8 failed its headline (GAE8 a: WRONG 5/36; c: ID 5/12), so this plan takes the diagnose branch: it tests the 033 diagnosis on fresh seeds and a stop rule built from it. The noise combination (adaptive budget, active only after a contradiction, so clean traces pay nothing; the fix for v0.29.0's GNR7 regression) and 16 states are deferred to v0.32.0 and are conditional on GA9 passing.

## Question
Why did A8 name wrong machines, and does a stop rule that also rules out larger consistent machines (up to a declared state bound) make active identification sound while keeping its gain over passive traces?

## Why
Study 033 (Observed): A8 ID 5/12 at 12 states vs 0/12 for S5, S1 and A8_random (paired +0.417 [0.167, 0.667]); WRONG 5/36. Every WRONG stopped 'unique' at n_min below the truth's reachable size (11, 11, 11, 10 of 12; 6 of 8), and every 'unique' stop at the truth's size was ID. All 8 'indistinguishable' stops were same_future. Inferred: uniqueness at the least consistent size is an Occam certificate, not identification; and the residual AMB is start-state ambiguity.

## Hypotheses
- H1 (mechanism): (diagnosis, replication) on fresh seeds, every A8 WRONG has n_min below the truth's reachable size.
- H2 (sound stop): with a declared state bound N, a stop rule that rules out every behaviourally different consistent machine of size n_min..N gives WRONG 0 and keeps the active gain.
- H3 (start state): most remaining AMB is ambiguity in the start state only (same future behaviour from the current state).

## Arms
- **A9**: A8 (033) with a bounded stop rule. Declared bound N = the family's nominal size (8, 12 or 16; controls 3), given to every arm as a prior and stated in the report. Each round: (1) least consistent machine M1 (as A8); (2) search n = n_min..N for a consistent machine M2 that differs from M1 in behaviour from the current state: a bounded distinguishing-word encoding with word length <= N + n_M1 - 1 (complete for Moore machines); (3) if found, the shortest separating word by product BFS, execute it through the step-only wrapper, repeat; if none exists for every n <= N, stop ID_future; (4) then the same search from the start state; if none, ID. Up to K = 64 extra actions.
- **A9_random**: control for chosen vs more data: the passive prefix plus exactly A9's extra-action count of seeded random actions, then the A9 stop check without further actions.
- **A8**: frozen v0.30.0 arm, unchanged (brute/scalesearch8); replicates the 033 failure for H1.
- **S5**: passive v0.27.0 arm with the 031 identify probe, unchanged.
- **S1**: passive baseline with the identify probe, unchanged.

Labels: ID (a single behaviour class from the start state up to N, equal to the truth); IDF (identified from the current state on, start state still ambiguous; scored as not ID); AMB; WRONG (a single class not equal to the truth); IDU (budget). A8, S5 and S1 keep their 033 labels.

Budget: 120 s per arm per case; 10 s per SAT query hard cap; K = 64; eps 0. Soundness: every separating word re-simulated on M1 and M2; the truth rechecked on every extended trace; the A9 'no M2 up to N' verdicts rechecked by the reference on scale8.

## Seeds (fresh, 100x0001)
scale8 10010001-10010012, scale12 10020001-10020012, scale16 10030001-10030006 (informational), control 10040001-10040006, smoke 10090001-10090030; all eps 0. Drawn only after a ledgered seedcheck_034.

## Gates
- GA9 (headline): a) WRONG = 0 for A9, A9_random, S5 and S1 on every case; b) ID(A9, scale12) - ID(S5, scale12) >= +0.33 (4/12), paired seed-bootstrap 95% CI lower bound > 0; c) ID(A9, scale12) >= 5/12 (the 033 A8 level, now without wrong answers); d) IDU(A9, scale12) <= 2/12.
- GDIAG8: every A8 WRONG on the 36 cases has n_min below the truth's reachable size; if A8 has 0 WRONG the gate is reported 'not exercised' and counts as neither pass nor fail.
- GIDF9: ID + IDF for A9 at scale12 >= 8/12 (tests H3).
- GCH9: ID(A9, scale12) - ID(A9_random, scale12) >= +0.17, paired CI lower bound > 0.
- G_sound: 0 unsound separating words; truth consistent with every extended trace.
- G10: controls: ID 6/6 for A9 and S5.
- GS_ref: independent CNF reference on scale8 A9: same labels, same 'no M2 up to N' verdicts, mutation detection 20/20.
- GQB9: A9 max SAT query <= 10.5 s.
- G_RT: whole run <= 1800 s.
- G_recount: independent recount reproduces every label.
- GTI: all test modules pass.
- G_PROC: prereg -> build_authorization_034 -> seedcheck_034 -> source_freeze_034 -> run_start_034 -> run_end_034, commit-order file, main sealed.

Runtime: about 900-1500 s on 8 workers (36 cases, 5 arms, up to 120 s each; the bounded M2 search costs more than A8's); cap 1800 s, G_RT fails above it (Inferred).

Failure: any GA9 clause failing, GCH9, G_sound or G10 failing, any WRONG for A9; failures are published, not tuned.

## Next
- If GA9 passes: v0.32.0: A9 with an adaptive noise budget (0 flips until the exact search contradicts, then B(t)), so clean traces pay no cost; and A9 toward 16 states.
- If it fails: publish the failing clause; if GDIAG8 fails, the 033 diagnosis is Rejected and the next plan studies the WRONG cases directly.

## Limitations
- the declared bound N is a prior the arms are given; identification without a bound is impossible in general.
- noise-free only (eps 0).
- K = 64 and 120 s fixed in advance.
- greedy shortest word per pair, not optimal experiment design.
- one world family (worlds_026), one hardware profile, one author.
- 16 states informational only.
