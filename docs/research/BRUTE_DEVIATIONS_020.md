# BRUTE study-020 deviations (BRUTE-0180-HORIZON-020)

Numbering continues project-wide (study-019 ended at #102). Every entry here is written BEFORE the code it governs and
before the source freeze; no held-out seed (8610001-8640048) has been generated, simulated or inspected. Later
deviations go in `BRUTE_DEVIATIONS_020_ADDENDUM_<k>.md` (this file is ledger-hashed and is never edited).

## #103 Pre-code design disclosures (horizon, flips, arms, metrics, per-bit rule, reference, streams)

Written after the seed check (`seedcheck_020`, 2026-10-28) and before `experiments/v0180_reference.py`,
`brute/perbit.py` and `experiments/brute_study_020.py` exist.

1. **Horizon governs; the copied `actions_per_case: 44` is the frozen study-013 learner constant.** BRUTE_PLAN_020
   copied `actions_per_case = 44` and `burn_in = 8` from plan 019 while `horizon.steps = 88` and `late_window =
   [45, 88]` define the study. The study runs **88 actions per case (89 readings, 176 action slots)**, burn-in 8. The
   frozen learner configuration is the study-013 plan dict with `actions_per_case_2x2` replaced by 88 in an in-memory
   copy (no frozen file is edited); every other frozen constant is asserted equal. The plan's `horizon.note` ("study-019
   traces were 28 steps after burn-in") is a **factual error in the plan**: study-019 traces had 44 actions (36 after
   burn-in). The question is unchanged: late-window coverage on traces twice as long. Label: Exact (definition);
   the plan text error is disclosed, not edited.
2. **Flips and boundary.** Flip array `default_rng([seed, round(1000*eps), 20]).random((89, 2)) < eps` (row 0 = the
   initial reading, unmasked bits only). B = observed bits over all 89 readings, fixed by the mask before the first
   action; RGN4 m = frozen `m_rule(B, 0.02, 0.01)`; RGNB4 boundary = frozen `brute.seqmargin.boundary(B, 0.02, 0.01)`
   (alpha spending over the 89-reading B, so m(b) at a given b may differ from study-019). Crossing recorded per case.
3. **Arms (plan `arms`).** SP8, RG4, RGN4, RGNB4, RGN4_or exactly as the frozen study-019 code paths (`rg_arm`,
   `noisy_supports`, `seqmargin_supports`, `cert_arm` rule = `rgn_decide`), run for 88 actions; RGN4_or shares RGN4
   supports when realized flips == m. RGNB4_0 and the alphabet3 block are **not** run (not in plan 020). RGNB4_bit =
   item 5. Label: Exact (definition).
4. **Metrics (fixing what "fraction of steps with a certificate" means).** The study-019 slot convention is kept: a
   step has 2 action slots; C over a window W = certificates in W's slots / (2 |W|). **C_late** = per case, certificates
   in steps 45..88 / 88, mean over cases. **C_early28** (GLH_early_control) = per case, certificates in steps 1..28 /
   56, mean over cases. C_full = certificates / 176 (reported). **C_curve** = per step t, mean over cases of
   certificates at t / 2 (reported). CI: case-level percentile bootstrap, 10000 resamples, numpy default_rng(20261028),
   95%; at a fixed eps a case is a seed. CP95 = the study-018 exact one-sided Clopper-Pearson upper bound by bisection.
5. **Per-bit partial certificates (RGNB4_bit, reported only).** At step t > burn-in, for action b with RGNB4 support S
   (not None, non-empty), bit j (bit 0 = high bit, as the reading order) is certified with value v iff every code in
   S has bit j = v. 4 bit slots per step (2 actions x 2 bits). Per-bit coverage = certified bits / 352 (full), / 176
   (late window). A false bit = certified value != latent bit. A full-code certificate implies both bits. Soundness:
   if the truth is in the region (no crossing, n* <= 4) the latent code is in S, so every certified bit is right
   (Exact, conditional, same lemma as GNB a). SAT UNKNOWN codes are kept in S (as the frozen supports). Implemented
   as `brute/perbit.py` (host-agnostic pure function). No `brute.certify/8` is added: per-bit is reported only and
   the frozen API is unchanged (GAPI8 = certify/7 hashes + its tests).
6. **GLH clauses as written.** (a) is unconditional: 0 false RGNB4 certificates on all 240 noisy main cases over all 88
   steps (crossing cases included; study-019 (a) excluded crossings, plan 020 does not). (b) CP95 of the RGNB4
   case-false rate over 240. (c) mean C_late(RGNB4) at eps 0.02 >= 0.10, (d) its CI lower > 0.05.
   **GLH_early_control**: C_early28(RGNB4, eps 0.02) lies inside the study-019 CI of C(RGNB4, eps 0.02),
   [0.04053, 0.065436] (GATES_019). Different seeds and a different window from the study-019 metric (44 steps, all
   slots); the comparison is the plan's and is scored as written. Prediction: Open.
7. **Other gates.** GS_a8: RGNB4 0 false at eps 0 on 120 cases. G_recount: every summary number recounted from the
   per-step traces for every arm (and the per-bit counts). GS_ref8: `experiments/v0180_reference.py` (numpy
   full-table enumeration, reusing the frozen v0170/v0160/v0120 reference functions; same author, NOT independent) on
   all 360 main cases: RG4, RGN4, RGNB4, RGN4_or supports, certifiers, summaries and the per-bit counts match; a
   mutation test catches 20/20 injected mutations. G10, G12 (repro set = main index % 3 == 0, 120 cases,
   byte-identical after stripping timing keys), G13, GTI (with K_0170 declared before the source freeze), G_RT
   (7200 s cap), G_HB (max heartbeat gap <= 10 s): as study-019.
8. **Streams.** `transfer` = 360 main + 120 stress cases (one checkpoint); `repro` = block `reproset`; `g11` =
   reference audit of every main case + mutation test; `gti` = the test suite. Workers and budgets by
   `scripts/rate_math_020.py` on smoke seeds, recorded in the source freeze; at most 8 worker processes in total.
9. **Fixes carried from v0.17.0.** Ledger receipts for produced artifacts name the ARTIFACT as source; the GTI stream
   of dry runs strips `SMOKE` from its environment.
