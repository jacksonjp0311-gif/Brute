# Recorded deviations: Brute v0.5.0 / study BRUTE-050-REGION-007

Pre-registration: `experiments/BRUTE_PLAN_007.json`, committed at `5be08aa` on branch `plan/v0.5.0` (from main
`2998dba`). This file lists notes made at the freeze and every change made **after** the plan commit. Criteria are never
changed here; every criterion is reported as registered. Labels: Exact / Observed / Simulated / Inferred / Rejected / Open.
Times are EDT on 2026-10-25, set by the author's machine (git shows order, not attested wall time).

## Process chronology (Exact: git ancestry; commit times author-set)

| Step | Commit | Commit time |
| --- | --- | --- |
| Plan pre-registered (+ design probe on sealed study-006 seeds, disclosed in the plan) | `5be08aa` | 05:22:44 |
| Second implementation `experiments/v050_reference.py` (same author, no `brute` import) | `1b57efe` | 05:26:14 |
| Implementation | `fc2bed8`, `c8e8611`, `b693113` | 05:32:33–05:36:36 |
| Pre-freeze fix to the second implementation (Q1) | `0c86d90` | 05:50:13 |
| Pre-freeze infrastructure (Q2) | `d7054a1`, `b2c4209` | 05:51:06, 05:56:49 |
| Source freeze `BRUTE_SOURCE_FREEZE_007.json` (20 files) | `064a50e` | 05:56:51 |
| Scoring scripts `make_count/gates/paired/reproducibility_007` (own commit) | `50e9321` | 06:00:43 |
| Ledger `run_start_007` | `ebcc650` | 06:11:52 |
| Run launched via nohup (`scripts/run_study_007.sh`, 6 workers) | — | 06:13:54 (log) |
| Release tooling (verifier, release-freeze script, test) written during the run (Q5) | `2438a74` | 06:15:55 |
| Steering received; post-start additions (Q6) | `07a6c69`, `033c716`, `1c4dd00` | 06:20–06:24 |
| Main run sealed (888 jobs) | `51215e0` | 06:26:46 |
| RUN_DONE (repro subset, pack) 06:27:47; ledger `run_end_007` | `3073992`, `86bd7bc` | 06:31–06:32 |

The scoring scripts were committed 11.2 minutes before `run_start_007` (06:00:43 → 06:11:52) and 13.2 minutes before the
launch. Each has exactly one commit (`scripts/verify_release_050.py::git_order`). The run was never interrupted.

## Q0. Design probe and smoke runs (disclosed; smoke seeds asserted disjoint)

The plan's `pre_freeze_disclosure` records a timing-only probe with the frozen `brute/geometry.py` on sealed study-006
seeds. All smoke and dry runs of v0.5.0 code used seeds 901–903, outside every study-007 range.
`scripts/check_smoke_seeds_007.py` (written after the run start, see Q6) asserts by code that the recorded smoke seed sets
are disjoint from all 468 study-007 evaluation seeds (2x2, breadth, calibration, stress, scaling): **disjoint**
(*Exact* for the recorded seed sets; that no other run happened is the author's report). The smoke runs got one
retroactive ledger entry (`smoke_run_retroactive_007`) with their times and seed sets, not one entry each before they ran.

**Exception (Observed, author's report):** at ~05:25, while writing the second implementation, the author printed the
transition/emission tables of the four breadth worlds for **held-out seed 1710001** to check the generator by eye. No
learner ran and no outcome was computed. This touches one held-out seed per breadth family (4 of 96 breadth cases'
worlds were seen); it is a deviation from "no held-out data before the run", not a change of criteria.

## Q1. Second implementation changed after `brute/` files existed (pre-freeze, `0c86d90`)

The smoke count flagged 2 traces where the residual equalled the smoke τ7 at 12 d.p. The plan defines the alarm on the
residual rounded to 12 d.p.; the reference had reused the frozen v0.4.0 `_Alarm`, which compares the unrounded mean.
Fix: `_Alarm12` for the A5/M5 and breadth audits; the frozen A4 audit keeps the unrounded comparison. The plan's order
rule (reference before any `brute/` file) holds for `1b57efe` and is broken for this fix. *Exact* (git).

## Q2. Pre-freeze infrastructure (`d7054a1`, `b2c4209`)

Torn-line-tolerant checkpoint, SEAL binding the calibration traces, storage/run/freeze scripts, `.gitignore` entries. No
science change. *Exact.*

## Q3. One `run_start_007` receipt, two writers

`run_start_007` reached origin as `ebcc650` (06:11:52) from another working copy (an earlier, interrupted session of the
same author; same identity `Brute <brute@local>`). This clone had made an identical commit `f35e263` with the same receipt;
its push was rejected and it was rebased away, so the ledger holds a single `run_start_007` receipt. Which process wrote
`ebcc650` is not recorded beyond the commit itself (*Open*); its content is identical (*Exact*).

## Q4. Scoring notes (no script changed after `50e9321`)

- `make_count_007` ran 06:32–06:56 (nohup, 6 workers, `count_007`); `make_gates_007` ~06:58 (`gates_007`). Both are the
  committed versions (single commit each, checked by `verify_release_050`).
- The breadth reference (`v050_reference`, enumeration) stops at its own 160,000-row budget. It stopped on 20/19/20
  big6 traces (B5/BM5/BP5) and 15/1/15 act3 traces; steps after the stop are unchecked and counted. This is what makes
  **GX2 fail** (act3 checked 84.5% of steps, registered minimum 90%), with **0 mismatching steps** among the
  checked ones. The 90% floor was registered before data; it is not changed here. *Observed.*
- Not anticipated in the plan: act3 (3 actions, ≤4/≤5 states) blew the enumeration budget more often than design
  guessed; the plan's design note expected only big6 to be partly unchecked. *Inferred* cause: the third action raises
  the per-row branching of enumeration (|A|·n transitions per machine).

## Q5. Release tooling written during the run (`2438a74`)

`scripts/verify_release_050.py`, `scripts/make_release_freeze_050.py`, `tests/test_release_050.py` were committed at
06:15:55, after the run started. They contain no scoring logic and assert no study numbers (they regenerate gates and the
paired analysis with the committed scoring scripts and compare bytes). *Exact.*

## Q6. Steering after the run start; post-start, non-pre-registered additions

A review of v0.4.0 (`docs/research/v0.4.0/ERRATA.md`) arrived at 06:17, after `run_start_007` (06:11:52) and the launch
(06:13:54). It asked that, **before** study-007, (i) smoke runs use seeds asserted disjoint from held-out seeds by code,
(ii) every run including smoke get a ledger entry, (iii) the second implementation recompute forecast probabilities with
swap mutations, and (iv) scaling claims use a stated model with residuals. Decision: the run was **not** stopped
(restarting would rerun held-out data already in use and gain nothing in blindness); all four are applied after the
start and labelled post hoc:

- (i) `scripts/check_smoke_seeds_007.py` — disjoint, except the Q0 glance. Ledger `smoke_run_retroactive_007`.
- (ii) retroactive ledger entry for the smoke runs (not one per run, not before them).
- (iii) `experiments/v050_prob_reference.py` (no `brute`/`bgr` import): v0.90 latent predictive by exact partial-machine
  counting, 0.08 smoothing, ε reserve, taken **and** untaken branches, log-loss/surprise/min-p. On sealed study-007 A4,
  A5, M5: **0 of 1,728 arm traces mismatching, 130,602 forecasts; swap mutations 20/20, 0 false flags**
  (`results/study-007/PROB_SECOND_IMPLEMENTATION.json`, *Observed*). Breadth-arm probabilities (uniform-over-support
  codes) are covered only by the pre-registered G11/GX2 count, not by this recompute (*Open* beyond that).
- (iv) `scripts/scaling_fit.py` → `docs/research/v0.5.0/SCALING_FIT_007.json` (*Inferred*, post hoc).

None of these changes a criterion, a scoring script or a sealed artifact. Ledger `steering_after_run_start_007`.

## Q7. Post-gates diagnostic of the M5 non-drift false certificate (report only, no tuning)

G3′ fails for M5 on one step. Case drift4, seed 1700015, mask 0.1, step 14 (trace index 13); the world drifted at trace
indices 11, 22, 33, so this step is **two steps after a drift**, outside the "drift step" the G3′ definition exempts.
M5 had taken action 1 by the M tie-break (LU-R scores tied 0/0, projection volumes 4 vs 3), certified emission 1
(margin support {1}), the actual emission was 3. The certificate was **not public** (`UNATTESTED_SCOPE`); the
v0.90 control was also wrong there. A5 at the same step: POSSIBLE_SET, not certified. *Observed.*

Reading (*Inferred*): Y1k certifies on the fibre over the **latest** observation, a one-step horizon; a drift two steps
back whose evidence has not yet contradicted the region can leave a stale region. A3/A4/A5 hit this on the v0.3.0
extended block (2 non-drift), and A2 here; M changes which action is taken and so which trajectory is seen, and on this
seed it walked into such a window. The registered G3′ rule counts it, and the GM decision rule therefore returns
NOT DISTINGUISHED although the coverage CI excludes 0. Nothing is changed; this is an input to v0.6.0 (a multi-step
fibre was rejected in v0.4.0 as F2, which broke G3′ itself).

## Outcomes that stay on the record

From `results/study-007/GATES.json` (*Observed*; thresholds as registered):

- **12 of 15 gated criteria pass.** Failed: **GX2** (breadth exactness: 0 mismatches, but act3 checked 84.5% < 90%),
  **G3′** (M5: 1 non-drift false certificate on drift4; A5 passes with 6 total, 0 non-drift), **G6b** (M5 − A2
  −0.0796, CI95 [−0.0996, −0.0602]; predicted FAIL).
- **GX1 passes exactly:** A5 vs A4 on 25,344 steps, 0 mismatches, 0 excluded; A5 − A4 coverage = 0.
- **GX3 passes:** stress block, 257 forecasts with SAT budget exhaustion, all abstain with reason; 0 production
  certificates with an unknown answer.
- **GM: NOT DISTINGUISHED** by the registered rule (M5 − A5 +0.0262, CI95 [0.0109, 0.0425], but G3′ fails for M5).
  Breadth BM5 − B5 +0.0391 [0.0204, 0.0579]; the prediction "≤ +0.03" held for 2x2 only.
- BP5 (passive breadth) − B5 −0.0445 [−0.0603, −0.0303] (reported).
- Second implementation (same author, no `brute` import): 0 of 2,592 arm traces; mutation 20/20; post-hoc probability
  recompute 0 of 1,728 (Q6).
- Reproducibility: 296 of 296 rerun jobs byte-identical; calibration byte-identical.
