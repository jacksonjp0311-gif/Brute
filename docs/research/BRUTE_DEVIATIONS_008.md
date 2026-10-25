# BRUTE study-008 (v0.6.0): deviations and implementation choices

Plan: `experiments/BRUTE_PLAN_008.json` (frozen at 89c2d3b, criteria hash 2f6ee48a...). Each entry says what changed or
what the plan left open, when it was decided (EDT), and whether held-out data had been seen. **No entry was decided after
held-out data were seen** unless it says so explicitly. Labels: Exact / Observed / Simulated / Inferred / Rejected / Open.

## A. Before the source freeze (8e80615, ledger source_freeze_008)

1. **Reference fix cae25ce** (pre-freeze, smoke data only): a bug in the v060_reference wrapper was fixed before the
   source freeze; the fix is in the freeze metadata as `pre_freeze_fix`.
2. **plan_view inheritance**: rule constants not restated in BRUTE_PLAN_008 (W, eps, burn-in) are read through
   `plan_view`, which inherits them from the frozen 007 plan unchanged (eps = 0.02, W = 8).
3. **xcheck (GX2') on Unchecked steps** adopts the recorded trace values so later steps can be checked; such steps are
   not counted as checked. It reuses frozen v050_reference helpers (same author).
4. **GMC encoding**: pyganak is run with `symmetry=True`; counting is two-phase (phase 1: |R_t| at every sampled step,
   phase 2: pairs/fibre counts), fixed after the smoke run exhausted the per-case budget in single-phase order. The
   per-case budget counts counter time only. The plan's 6 h total cap is shared by the 2x2 GMC and the breadth GMC
   report via `--budget-start`; the G12 GMC recount of the repro subset has its own cap.
5. **Smoke seeds** 980001-980024 (2x2 980001-980016, breadth 980017-980024) of the plan's 980001-980030 range; the
   smoke code assertion holds.
6. **requirements-gmc.txt** pins pyganak==2.8.0 and pyapproxmc==4.4.0 (separate from the core pins).
7. **R_dev_xcheck_007** (not gated) is run on every 4th breadth case of study-007 (`--every 4`), because one big6 case
   costs about 700 CPU-s (Observed, 2-case dev run). tau7 for study-007 is read from that study's RESULTS calibration.
8. **Ledger SOURCE** for each event is the file the event is about (the script or artifact path).

## B. Scoring choices fixed in scripts/make_gates_008.py (08ac3f3, ledger scoring_scripts_008, before run_start)

9. **G3'**: the plan threshold says "taken action"; the drift_definition text mentions taken or counterfactual. The gate
   is evaluated on the taken action (threshold wording); counterfactual false certificates and their non-drift count are
   reported next to it, as is the study-007 coding (not on a drift step). NON-DRIFT = step > 12 and step not in {12,23,34}.
10. **G7** minimum probability threshold = eps / 2^s (2x2: 0.02/4, breadth: 0.02/8), plan "eps/m".
11. **G9** retraction reasons are checked against the plan wording via the frozen reference functions
    (`ref_reason` for 2x2, `k_reason` for breadth); the reasons falsified_by_observation / scope_withdrawn /
    unverifiable_masked are all valid outcomes, the check is that each recorded reason equals the reference's.
12. **G10** production arms: R6, C6, A5 (2x2) and B5, BR6, BC6 (breadth). A2/A4 are controls.
13. **GX2' (iv)** is trace-level and conservative: a trace flagged by exactly one of xcheck and enumeration is a
    disagreement even if the flagged step lies outside the other's checked range. XCHECK_008 records the results file
    path but not its sha; the gate checks it covers every sealed breadth case.
14. **GMC (i)** coverage is computed over the EXPECTED sampled steps (360 in_family_original A5 cases x 9 steps); a case
    missing from the report counts as UNKNOWN.
15. **GT1** cannot be evaluated before verify_release_060 exists (plan step 10, after the gates). GATES_008.json lists
    it as pending. `scripts/make_gt1_008.py` (committed 29cd0d1, during the run, before any study-008 output was read)
    runs the GT1 corruption matrix + the frozen-050 regression and writes `results/study-008/GT1_008.json`; the committed
    `make_gates_008.py --output GATES_008_FINAL.json` then writes the final table (GATES_008.json is NOT overwritten).
    verify_release_060 regenerates GATES_008_FINAL byte-for-byte and checks GATES_008 equals it outside GT1.
    The matrix does not need an untampered pass; tests/test_release_060.py checks both afterwards.
16. **G12** GMC recount: count fields R, blocking, pairs, fibre compared per key/step; timing fields ignored; a difference
    is allowed only if one side is UNKNOWN with a timeout/budget reason (each listed).

## C. Operations

17. The held-out run, the xcheck, the GMC counts, the second implementation and the repro re-run run as three parallel
    streams on one shared 8-CPU box (`scripts/run_study_008.sh`); all wall-clock figures are informational.
18. A resume message from the orchestrating agent described the scoring/run files as uncommitted; they were already
    committed and pushed (through c13f8c5). Nothing was redone.
19. `results/study-008/GMC_BUDGET_START` (epoch 1792933084 = 08:58:04 EDT, the start of the shared 6 h counting cap,
    written by stream B) was committed separately (0acdc5c) when noticed untracked; the main SEAL.json was committed
    as soon as it was written (c21ef12), before the ledger run_end/seal entries, which follow RUN_DONE.
20. GT1 tooling (verify_release_060, test_release_060, make_gt1_008, release_version_060) was committed at 29cd0d1
    while the held-out run was in progress; it reads no result values and contains no scoring rule.

## D. Stream A stop and release scoring (decided 2026-10-25 ~17:44 EDT, after the main study was sealed)

21. **Stream A (GX2' xcheck) stopped by owner decision.** James decided, after a full day of waiting, to stop the
    `experiments.v060_xcheck` stream (PIDs 917088, 917131-917133, started 08:58 EDT) and release with what exists. The
    processes were killed at 17:44 EDT (run008.log: "17:44:05 a stream failed"). At the stop the checkpoint held **46 of 288**
    breadth cases (~8.8 h of wall clock, ~5.2 cases/h with 3 workers, i.e. roughly 2 more days to finish at that rate).
    **No result values were inspected to make this decision**; it was based on the progress count and rate only.
    The partial checkpoint was committed as-is (b02b0c3). GX2' is scored on the frozen criterion: the plan requires
    checked fraction >= 0.99 for every family x arm (big6/sens3/act3/ood6s3 x B5/BR6/BC6) and coverage of every breadth
    case, so GX2' is **FAIL (incomplete coverage)**. No new pass criterion is introduced. The mismatch count on the 46
    checked cases (all big6, the first family in case order) is reported as Observed only.
    Consequence: R_dev_xcheck_007 (not gated; it runs after the xcheck in stream A) was never started and is absent.
22. **Partial-checkpoint wrapper** `scripts/make_xcheck_partial_008.py` (written after the stop, reads only the
    checkpoint and the sealed RESULTS case list): it writes `results/study-008/XCHECK_008.json` in the frozen report
    schema using the frozen `v060_xcheck.summarize`, but with `per_family_arm` counted over ALL 288 sealed breadth cases
    (steps of unchecked cases count as unchecked), so the committed, unchanged `make_gates_008.py` scores clause (iii) and
    `covers_every_breadth_case` as FAIL. The within-checked-cases summary is kept under `checked_cases_only` (Observed).
    The file carries `partial: true` and the stop note. make_gates_008.py is not edited.
23. **run_study_008.sh exited non-zero** after the kill (stream A failed), so its final `pack` and `RUN_DONE` lines were
    not printed by the script. The pack step (`scripts/study008_storage.py pack`) was run by hand with the same command,
    and RUN_DONE is recorded by the ledger `run_end_008` entry, whose note states the stop.
24. **Observations made while scoring (report only, nothing rescored).** These were seen after GATES_008_FINAL was
    written with the committed scripts:
    - (a) **G5 failure, not predicted.** perm4 R6 and C6 each have 4 of 72 alarm cases (0.0556 > 0.05). The same
      4 cases (seeds 1860001, 1860008, 1860010, 1860022, all at mask 0.1, first alarm at step 8-9) also alarm in the
      frozen A4 and A5 arms. A2 has 0. So the failure comes from the shared tau6 residual alarm on these fresh
      seeds, not from the R6/C6 rule. *Observed*; the cause is *Inferred*.
    - (b) **G3' non-drift events.** All three non-drift false certificates (R6 1, C6 2) come exactly one step after a
      drift step (drift4 seed 1880047 step 13, seed 1880006 step 24). A5 has the same seed-1880047 event. *Observed*.
    - (c) **big6 inside the checked cases.** Within the 46 checked cases, big6 checked 2903/2944 = 0.986 of steps,
      below 0.99. GX2' would have failed on clause (iii) even if only these cases had been registered. *Observed*.
    No threshold, case set or scoring rule was changed because of (a)-(c).
