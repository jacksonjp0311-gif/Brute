# Brute v0.7.0: pre-registered plan for study-009 (BRUTE-070-SYNCPLAN-009)

**Status:** pre-registered. No v0.7.0 code, world, seed or run exists at the freeze commit.
The binding text is `experiments/BRUTE_PLAN_009.json`. If this page and the JSON differ, the JSON wins.
The ledger entry `preregistration_009` records the JSON's sha256 and the canonical-JSON sha256 of its `criteria` block. Every prediction below is **Inferred** unless marked otherwise.

## Targets and hypotheses

| Target | Hypothesis (short) | Gate |
|---|---|---|
| (a0) why the v0.6.0 event is late | The event is a window **mean**: from a calm window one maximally surprising step cannot cross τ/2, so the certificate issued one step after a drift is stale. Diagnostic on sealed study-008 drift4 traces, **Observed on seen data, exploratory, not gated**. | none (R_diag_lag_008) |
| (a) surprise timing fix | A rule with **synchronous** events (at the very step that is surprising or falsifies a certificate) passes G1, G2, G3′ and G6b on the same held-out run | **GA1′ (JSON key GA1_prime)** (conjunction) |
| (b) incremental cross-check | The incremental, symmetry-broken CaDiCaL encoding re-derives every breadth decision on ≥ 99% of steps per family × arm with 0 mismatches inside a declared budget; a no-symmetry spot check also finds 0 mismatches | **GX2″** |
| (c) planning by model counts | Choosing actions to minimise expected surviving (machine, state) pairs (1–2 step lookahead) beats LU-R on coverage or time to first certificate, with 0 false certificates, and counts never touch certification | **GP1** |
| (d) test isolation | One interpreter per test module removes the test_study_005 order dependence without editing a frozen file | **GTI** |

**Exact** (arithmetic on the frozen formulas): every published 2x2 code keeps ≥ eps/4 = 0.005 (8 codes: 0.0025), so one surprise is ≤ 5.298317 (2x2) or ≤ 5.991465 (breadth), while the v0.6.0 event needs a window sum > 8 × τ/2 = 6.580861 (2x2) or 8.317766 (breadth).

## Event triggers
- **E1:** the v0.6.0 event, unchanged (residual > τ/2 or a window event).
- **E2:** the taken action's conditional certificate is falsified by the observation at that step. No constant.
- **E3:** single-step surprise > τ (τ6 for 2x2, τ7 for breadth). No new constant. **Exact:** τ6 > ln 4 and τ7 > ln 8 (by ~2e-13), so a uniform forecast never fires E3.
- Alarms, resume, probabilities and LU-R are **not** changed by E2/E3.

## Arms
- **S7, synchronous recency-opened.** R6 with events E1 ∪ E2 ∪ E3. Targets G3′.
- **SC7, synchronous coverage-tracked with recency-expiring calm.** Certifies when Y1k certifies, or on the tracked-state projection when no E1/E2/E3 event happened in the last W = 8 steps and t ≥ burn-in; while an event is recent it uses the S7 path. Targets GA1.
- **BS7, BSC7:** the same rules on breadth worlds with τ7.
- **P7, count planner.** The frozen A5 learner; only the action choice changes, to argmin of E2(a) (2-step, when explicit enumeration of ≤ 10^4 machines finishes within 3 s) or E1(a) = Σ_c n_{a,c}² / N_a. Ties and any UNKNOWN count go to the A5 LU-R choice.
- **Frozen comparators:** R6, C6 (v0.6.0), A5 (v0.5.0, planning comparator), A4 (v0.90 control), A2 (G6b baseline), B5 (breadth, GX2″ subject).
- **Fixed constants:** τ6 = 1.645215321642, τ7 = 2.07944154168, factor 0.5, W = 8. None is tuned; the diagnostic cannot change them.

## Seeds (all disjoint from every earlier range; max prior 1940024)
- **2x2 held-out:**
  - cycle3 2010001–024
  - switch3 2020001–024
  - unstructured3 2030001–024
  - unaliased2 2040001–024
  - ood4 2050001–024
  - perm4 2060001–024
  - ood5 2070001–024
  - drift4 2080001–048 (doubled)
- **Breadth:**
  - big6 2110001–024
  - sens3 2120001–024
  - act3 2130001–024
  - ood6s3 2140001–024
- **Planning block:** seeds xx0001–xx0008 of cycle3, switch3, unstructured3, unaliased2, ood4 and ood5 × 3 masks = 144 cases (subset of the held-out block, no new seeds).
- **Spot sample:** random.Random(20261027), 6 cases per breadth family, B5 only (24 cases), drawn and ledgered before run_start.
- **Smoke:** 2190001–2190030 only. Study-008 seeds are used only for the diagnostic and development, never as v0.7.0 evidence.
- `scripts/check_seeds_009.py` asserts disjointness (parsed from experiments/PLAN.json and BRUTE_PLAN_002–008, plus 901–903 and 1591001–1591384), is run and ledgered before any smoke run, and the runner refuses out-of-range seeds.

## Gates (frozen thresholds)

| Gate | Threshold | Prediction |
|---|---|---|
| **GA1′ (JSON key GA1_prime)** | PASS iff ONE arm in {S7, SC7} passes G1, G2, G3′ and G6b on the same run | FAIL: S7 passes G3′ and fails G6b; SC7 fails G3′ |
| G1 | 0 false conditional and 0 false public certificates in-family (S7, SC7, P7, B5, BS7, BSC7), all steps and actions | PASS (S7, BS7, P7); SC7/BSC7 likely, Open |
| G2 | 0 false conditional certificates on ood5 (S7, SC7, P7) and ood6s3 (B5, BS7, BSC7) | PASS (S7, BS7, P7); SC7/BSC7 at risk |
| G3′ | Unchanged. Per arm (S7, SC7): drift4 non-drift false = 0 AND total ≤ 0.5 × v0.90 control (A4), 144 cases | S7 PASS (low confidence), SC7 FAIL |
| G6b | Unchanged. Per arm: pooled in_family_original coverage X − A2 ≥ −0.03 AND 95% CI lower ≥ −0.05 | S7 FAIL (~ −0.10 to −0.13), SC7 FAIL (~ −0.04 to −0.09, Open) |
| G5 | Unchanged: ≤ 0.05 of cases with an alarm (2x2: ≤ 3 of 72), per arm and in-family family. **Exact attribution:** the v0.6.0 perm4 failure (4/72) came from the shared τ6 alarm (same cases alarm in A4/A5), not from R6/C6; E2/E3 do not touch alarms; τ6 is not recalibrated and the threshold is not loosened | PASS except perm4 Open (one perm4 FAIL fails every 2x2 arm) |
| **GX2″** | (i) symmetric incremental harness: 0 mismatches, 0 failed witness replays on B5, BS7, BSC7; (ii) **checked ≥ 0.99** per family (big6, sens3, act3, ood6s3) × arm; (iii) budget 30 min wall on 4 workers; (iv) no-symmetry spot check: 0 mismatches, 0 failed replays, ≥ 64 checked steps per family (30 min, 2 workers). 2,000,000 conflicts per query; over budget is unchecked. Independence caveat: same author, shares RegionK's symmetry idea | PASS; big6 spot non-vacuity at risk |
| **GP1** | (i) coverage P7 − A5 97.5% CI lower > 0 OR T_cert P7 − A5 97.5% CI upper < 0 (40 seeds, alpha split); (ii) 0 false certificates (and 0 public on ood5); (iii) planned fraction ≥ 0.80; (iv) A5 replay of P7's history reproduces every forecast field; (v) 200-decision count audit (rng 20261028): 0 disagreements, ≥ 100 checked by both sources; (vi) all 144 cases within budget | FAIL (coverage near 0; T_cert Open; (iii) at risk); (ii), (iv), (v) PASS |
| **GTI** | One subprocess per test module (pinned venv): every failure in the 14 frozen-version ids listed in the JSON, or a test_release_060 test in {test_version_consistent, test_fast_verify_passes, test_untampered_copy_passes} that passes at tag v0.6.0; test_study_005 6/6; same tests run and skipped as plain discover; no frozen file changed; every new test passes | PASS |
| G_RT | Every held-out stream within 3 h 00 min of run_start_009 | PASS (planning block is the largest unknown) |
| G4 | 0 public certificates on ood5, drift4 and ood6s3; 0 wrong public certificates; none after the first alarm | PASS |
| G7 | Log-loss ≤ ln 4 (ood5, drift4; P7 ood5) and ≤ ln 8 (ood6s3); min p ≥ eps/m | PASS |
| G9 | Resume only after W = 8 calm residuals; no RESYNC_AMBIGUOUS; retraction only at contradiction | PASS |
| G10 | All cases complete; solver_unknown forecasts ≤ 1% per block | PASS |
| G11 | v070_reference audit of S7, SC7, BS7, BSC7, P7: 0 mismatching traces; mutation 20/20 with ≥ 4 in P7 action choices | PASS |
| G12 | Byte-identical rerun of cases with index ≡ 0 mod 3; P7 may differ only from its first budget fallback (reported) | PASS; P7 timeout divergences possible |
| G13 | Frozen controls, modelcount and adopted incremental files hash-checked; τ6 and τ7 unchanged | PASS |

**Observed pre-freeze** (pinned venv, plain discover, main df0fec1): 234 tests, 2 failures and 15 errors = the 14 allowed frozen-version ids + 3 test_study_005 order errors. test_release_060 passed in full.

## (c) budget rule and fallback
- **Counts:** per-code fibre counts as defined by the frozen brute/modelcount.py; explicit enumeration first, else pyganak==2.8.0.
- **Budget:** 2 s per count, 15 s per decision, 150 s of counting per case, 60 min for the planning block (6 workers).
- **Fallback:** any UNKNOWN count or exhausted budget takes the A5 LU-R choice and is recorded with its reason; never imputed.
- Counts influence the **action choice only**, never certification, probabilities, alarms or resume.

## Stop rule (3 h)
- The cap runs 3 h 00 min from the run_start_009 ledger time. Stream budgets: 2x2 45 min, breadth 45 min, planning 60 min, GX2″ symmetric and spot 30 min each; at most 8 workers.
- A progress projection is written at +30 min; nothing changes because of it.
- At the cap: SIGTERM, then SIGKILL after 60 s; ledger `stop_009`; no extension, no rerun.
- Every gate with incomplete inputs is scored **FAIL (STUDY_BUDGET)**, and G_RT is FAIL.

## What counts as failure
- Any gate below its threshold is FAIL and is published verbatim everywhere.
- GA1′ (JSON key GA1_prime) fails if G3′ and G6b are passed only by **different** arms.
- One family or arm short on GX2″, or a spot-check failure, fails target (b). Any GP1 clause failing fails target (c).
- The diagnostic is never evidence for or against a gate.
- No reruns, re-seeding, threshold or constant changes after run_start. The only exception is an infrastructure crash, rerun with identical code and seeds, ledgered as a deviation and still inside the cap.
- **No auto-promotion.** The default stays Y1k + LU-R whatever the outcome.

## Carried defects stay recorded
- The frozen v0.1–v0.5 release checks and test_brute_repro tamper test keep failing as listed; their files are not edited.
- `experiments/brute_study_006.py` sets S5.FULL at import, so test_study_005 errors after a module that imports it. Both files are frozen (BRUTE_SOURCE_FREEZE_005/006) and are **not** edited; target (d) isolates them per process.

## Open
Adversarial drift (a jump consistent with the latest observation), τ6 calibration on perm4, breadth counting and planning, a mechanical proof that symmetry breaking preserves every xcheck query, and third-party replication.

## Process order
1. Plan, then the ledger entry.
2. Seed check and spot-sample draw, then the ledger entry.
3. Diagnostic a0 on sealed study-008 data, then the ledger entry.
4. Second implementation (v070_reference).
5. Adopted files checked out byte-identical; implementation, with smoke runs on 2190001–030 only.
6. Source freeze.
7. Scoring scripts, committed at least 10 min before run_start.
8. nohup runs under the 3 h stop rule.
9. Seal.
10. Gates.
11. Release verifier, then release on owner instruction.

Pinned versions: Python 3.13.5, numpy==2.5.4, python-sat==1.9.dev17, pyganak==2.8.0, pyapproxmc==4.4.0. Brand rules unchanged: charcoal/sage; no purple, neon, emoji, mascots or gold.
