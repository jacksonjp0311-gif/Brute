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
    it as pending; tests/test_release_060.py writes `results/study-008/GT1_008.json`, after which GATES_008 is
    regenerated (no other input changes) and GT1 enters the gate table.
16. **G12** GMC recount: count fields R, blocking, pairs, fibre compared per key/step; timing fields ignored; a difference
    is allowed only if one side is UNKNOWN with a timeout/budget reason (each listed).

## C. Operations

17. The held-out run, the xcheck, the GMC counts, the second implementation and the repro re-run run as three parallel
    streams on one shared 8-CPU box (`scripts/run_study_008.sh`); all wall-clock figures are informational.
18. A resume message from the orchestrating agent described the scoring/run files as uncommitted; they were already
    committed and pushed (through c13f8c5). Nothing was redone.
