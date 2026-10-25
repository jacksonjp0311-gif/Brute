# Recorded deviations: Brute v0.4.0 / study BRUTE-040-GEOMETRY-006

Pre-registration: `experiments/BRUTE_PLAN_006.json`, committed at `5fa3628` on branch `plan/v0.4.0` (from main
`73a3a5a`). This file lists notes made at the freeze and every change made **after** the plan commit. Criteria are never
changed here; every criterion is reported as registered. Labels: Exact / Observed / Simulated / Inferred / Rejected / Open.

## Process chronology (Exact: git ancestry and commit times; times EDT, 2026-10-25)

| Step | Commit | Commit time |
| --- | --- | --- |
| Plan pre-registered (with design-probe files) | `5fa3628` | 02:26:16 |
| Second implementation (same author, no `brute` import) | `2eba00b` | 02:26:41 |
| Implementation | `2811904` | 02:54:21 |
| Pre-freeze fix (storage, freeze script, GR2 conflict budget) | `b5e7077` | 02:58:20 |
| Source freeze `BRUTE_SOURCE_FREEZE_006.json` (20 files) | `70a3c43` | 02:58:37 |
| Scoring scripts `make_gates_006`, `make_paired_006`, `make_reproducibility_006` | `d9ddbe6` | 03:08:51 |
| Ledger `run_start_006` (run started 03:20:15) | `71a7edb` | 03:20:15 |
| Run finished 03:32:58; seal + ledger `run_end_006` | `454094c` | 03:39:53 |
| Count, GR1b, paired, GR1, GR2 | `d4f96ad`..`b42bb1b` | 04:26–04:27 |
| Reproducibility rerun; gates | `e6f65e2`, `f6d9014` | 04:48, 04:49 |

The scoring scripts were committed **11.4 minutes before** the run started (03:08:51 → 03:20:15; the box clock was
checked against GitHub's HTTP `Date` header). Each scoring script has exactly one commit and is unchanged since
(`scripts/verify_release_040.py::git_order`). Commit times are set by the author's machine; git shows order, not wall
time, so the 11.4-minute gap is *Observed* on one clock, not independently attested.

The plan and the second implementation are 25 s apart. The second implementation was written from the plan before any
`brute/` v0.4.0 code (author's own report); git shows only that it is an ancestor of every v0.4.0 `brute/` commit.

## P0. Design probes run on sealed study-004/005 seeds before the plan (disclosed in the plan)

*Exact* for the committed probe files (hashes in the plan's `pre_freeze_disclosure`); **author's own report** for the
statement that they ran only on sealed study-004/005 seeds (and the study-005 extended drift4 block for the power
analysis) and that no study-006 or calibration seed was generated before `5fa3628`. These probes set the design
estimates labelled *Simulated* in the plan (G6b′ expected to fail; D2 and F2 predicted to fail; power analysis N = 384).

## P1. `observed` field added to the D2/F2 trace records (pre-freeze)

D2 and F2 run on a 96-case subsample in full detail and are otherwise stored compactly. The implementation stores the
observation vector in the D2/F2 records (`experiments/brute_study_006.py`, `rec['observed']`) so that GR1b can replay
them from the trace. Added in `2811904`, before the freeze. It changes no decision. *Exact.*

## P2. GR2 per-query conflict budget (pre-freeze, `b5e7077`)

During the GR2 smoke run (smoke data only, `/tmp`), one SAT `support` query at n=10/12 ran for more than 6 minutes.
Before the freeze, `ConstraintRegion` gained `conf_budget=None` (exact by default; GR1 and GR1b use no budget and are
exact) and GR2 uses `GR2_CONF_BUDGET = 20000` conflicts per query. A query that exceeds the budget is counted as
`unknown` and its step is excluded from the enum-vs-SAT agreement count and reported. The plan text for GR2 predates
this budget, so this is a scoring-scope deviation for GR2 (not gated). Result: unknown steps at n=8 (3 cases, 5 steps,
8 queries), n=10 (3 cases, 8 steps, 15 queries) and n=12 (1 case, 4 steps, 8 queries); the enumeration side excludes
251 steps at n=6 in 10 row-budget-exhausted cases. *Exact* (code), *Observed* (counts).

## P3. G5 scored on the any-step (stricter) reading

`make_gates_006` counts a case as a false-alarm case if a RESIDUAL_SURPRISE alarm occurs at **any** step, including
burn-in. The plan says "fraction of that family's cases with >=1 RESIDUAL_SURPRISE alarm" and does not exclude burn-in.
Both readings are reported in `GATES.json`; in family they coincide (ood4 A4 1/72 either way). *Observed.*

## P4. Release-verification files rode along in the seal commit

`git add -A` in the seal commit `454094c` also added `scripts/verify_release_040.py`, `scripts/make_release_freeze_040.py`
and `tests/test_release_040.py`. These read no study numbers and contain no scoring logic (they regenerate gates and
paired analysis with the committed scoring scripts and compare bytes). They were written during the run, before any
result was looked at (author's report). They are locked in `experiments/BRUTE_RELEASE_FREEZE_040.json`. *Exact* (what
the commit contains).

## P5. GR2 timing is noisy and its slopes rest on few points

GR2 times are wall clock on one shared 8-CPU box with parallel workers. SAT time is **non-monotone** in n and mask (for
example mask 0.6: n=12 5.52 s mean case time; mask 0.1: n=12 0.79 s, below n=10 3.02 s), and SAT maxima (about
63–70 s for n ≥ 6) are dominated by conflict-budget hits. The log-log slopes in `GR2.json` are fitted on 5 (enum,
n=2..6) or 8 (SAT, n=2..12) points with 4 cases per (family, mask) cell. They are *Observed* descriptive fits; any
trend claim drawn from them is *Inferred*.

## P6. Reproducibility rerun timing

`make_reproducibility_006` ran after the scoring chain (count, GR1b, GR2, GR1, paired) rather than directly after the
seal, because of session interruptions. It re-runs calibration and the study from the frozen source and compares bytes;
the order does not affect the comparison. Both `CALIBRATION_006.json` and `SCIENTIFIC.json` are byte-identical.
*Observed.*

## P7. Session interruptions

The work was interrupted three times (02:59, 03:49, 04:40 EDT). Every step was committed and pushed before moving on;
no step was rerun after its output existed (each output refuses to overwrite). Background jobs survived the
interruptions. *Exact* (git), author's report (process).

## Outcomes that stay on the record

- **G6b′ fails, as pre-registered:** pooled A4 − A2 = −0.103781, CI95 [−0.115972, −0.091898]. *Observed.*
- **G15 (D2) and G16 (F2) candidates fail, as predicted:** D2 − A2 −0.070833 [−0.085186, −0.05733]; F2 − A2
  −0.032639 [−0.040201, −0.025616], and F2 also breaks G3′ (2 non-drift false certificates, 2 stale). *Observed.*
- **G14′ (D7/D8) is OPEN** by the decision rule. *Observed.*
- **Resume is barely exercised:** 3 resumes per arm (ood4 1, perm4 2) and 0 certificates after any resume. *Observed.*
