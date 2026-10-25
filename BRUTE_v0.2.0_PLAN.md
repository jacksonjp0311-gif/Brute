# Brute v0.2.0 plan: active experimentation, window rebuild (study BRUTE-020-ACTIVE-004)

Frozen criteria: [`experiments/BRUTE_PLAN_004.json`](experiments/BRUTE_PLAN_004.json). The commit that adds it is the
pre-registration record. It comes before any v0.2.0 code. Design evidence is in
[`docs/research/v0.2.0/design_probe/`](docs/research/v0.2.0/design_probe/) and was produced on the study-003 seeds, which
are design data only. Every claim carries a label: **Exact**, **Observed**, **Simulated**, **Inferred**, **Rejected** or
**Open**.

## 1. Failure modes carried from v0.1.1

| # | Failure mode | Evidence | Label |
| --- | --- | --- | --- |
| FM1 | **Low coverage.** In-family coverage is 0.09–0.20, against 0.34–0.52 for v0.90. Every margin abstention has a verified n≤5 witness, so the gate itself is sound. | study-003 R3 | Observed |
| FM2 | **Coverage depends on the action sequence.** The passive sequence is fixed, so it never asks the question that would separate the surviving n≤4 machines from the n≤5 ones. | design probe: lookahead lifts dual coverage by +0.12 to +0.15 | Simulated |
| FM3 | **Drift forecasts are only as good as suffix-1.** drift4 scores 1.1556 against 1.1679, and the CI includes 0. After a jump, the n≤5 margin is the wrong model. | study-003 | Observed |
| FM4 | **Double issuance in API 1.1.** `service_v011._predict` calls `record_issued` on every CERTIFIED predict, so a second predict at the same step lists the retraction twice. Reported by the bridge track (bridge/v0.1 @ 9c88a3a). | code reading | Exact |
| FM5 | **A fresh clone fails 3 tests.** `.gitattributes` sets `*.ps1 eol=crlf`, so checkout writes CRLF while MANIFEST records LF. Two tests fail on that. The third is the known A3 version error. The README "126 pass" count was measured in the authoring tree. | reproduced on a fresh worktree of main 7a52671 | Exact |
| FM6 | **No experiment hook for the bridge** (REQUEST_ACTION / split). | bridge request | Exact |

## 2. Fixes and exact file targets

All new code goes in new files. `brute/core/*`, `brute/fallback.py`, `brute/version.py`, `brute/api/service*.py` (1.0,
1.1) and every file in an existing freeze stay byte-identical.

| Fix | File | What |
| --- | --- | --- |
| X1 active experimentation | `brute/active.py` (`ActiveBruteLearner(FallbackBruteLearner)`, `experiment()`) | **LU rule:** one-step certifiability lookahead, uniform over the n≤4 support, with ties going to the passive action. Certification code is not touched. |
| X2 window rebuild | `brute/active.py` (`window_n4` tier) | Fresh n≤4 learner from the contradiction step, restarted on its own contradiction. It refines suffix-1 only where v0.1.1 would use suffix-1. It never certifies. |
| X3 issuance de-duplication | `brute/active.py::record_issued` | Records (step, certificate) at most once, with a test. |
| X4 brute.api 1.2 | `brute/api/service_v020.py`, `brute/api/schema/request.v1_2.json`, `response.v1_2.json` | `experiment` op and field, plus `window_n4` as a source. |
| X5 version | `brute/release_version.py` (`RELEASE_VERSION='0.2.0'`), `RELEASE.json` | Same pattern as A3. |
| X6 clone hygiene | `.gitattributes` (`*.ps1 -text`), `MANIFEST.sha256`, README test count | Recorded as a deviation, because `.gitattributes` is inherited. |
| Study tooling | `experiments/brute_common_004.py`, `brute_study_004.py`, `brute_calibrate_004.py`, `v020_independent_reference.py`; `scripts/make_gates_004.py`, `make_paired_004.py`, `make_reproducibility_004.py`, `make_freeze_004.py`, `make_release_freeze_020.py`, `verify_release_020.py` | |
| Tests | `tests/test_brute_active.py`, `tests/test_api_contract_v020.py`, `tests/test_study_004.py`, `tests/test_release_020.py` | |

**Not attempted (Open):** 5-state certificates against a 6-state margin. The design margin peak is already 102,806 rows
at n≤5. An n≤6 margin is expected to exceed the 160,000-row budget (*Inferred*). Measure before planning.

## 3. Policy design evidence (Simulated, study-003 seeds, 72 cases per family)

**Dual coverage** counts both actions at every post-burn-in step, so it does not depend on the policy. A is the active
policy and P is passive.

| family | P dual | LU dual | gain | P ll | LU ll | false certs (taken / dual) |
| --- | --- | --- | --- | --- | --- | --- |
| cycle3 | 0.1971 | 0.3173 | +0.120 | 0.1930 | 0.1609 | 0 / 0 |
| switch3 | 0.1678 | 0.2953 | +0.128 | 0.2327 | 0.1877 | 0 / 0 |
| unstructured3 | 0.1040 | 0.2417 | +0.138 | 0.1395 | 0.1191 | 0 / 0 |
| unaliased2 | 0.0793 | 0.2315 | +0.152 | 0.1131 | 0.0938 | 0 / 0 |
| ood4 | 0.0046 | 0.0413 | +0.037 | 0.4137 | 0.3927 | 0 / 0 |
| ood5 | 0.0010 | 0.0210 | | 0.6245 | 0.6032 | 0 / 0 |
| drift4 | 0.0052 | 0.0172 | | 1.1556 | **1.1729** | 4 → **13** (1 non-drift) / 14 |

- **Volume bisection was worse (Rejected).** Entropy (H), support-size (S), family-only (F) and margin-only (M)
  policies were mixed. H's dual coverage changed by +0.04 on cycle3 but by −0.03 on unaliased2, and its on-policy
  coverage fell everywhere.
- **LU and LP are identical.** LP weights codes by published probability. It gave the same results as LU on every
  case (DISCOVERIES D4).
- **Lookahead wall-clock** is about 3× passive on cycle3 and 2× on unstructured3.
- **The window tier** lowered passive drift4 log-loss from 1.1556 to 1.142.

## 4. Order of work (owner sequence)

1. Freeze `BRUTE_PLAN_004.json` together with this plan, DISCOVERIES and ROADMAP in one commit, and record its hash in
   the ledger.
2. Implement X1–X6 and the tests.
3. Build the study tooling, write the source freeze and run the calibration check (G13).
4. Run study-004 and seal it.
5. Score the gates, then run the paired bootstrap, the reproducibility rerun (G12) and the independent audit (G11).
6. Write the deviations doc and update README, CHANGELOG, RELEASE.json, "What Brute can't do yet" and ROADMAP.
7. Run `verify_release_020`, then merge with `--no-ff` to main and tag v0.2.0. A gate failure still ships as a release,
   with the failure documented.

## 5. Risks (pre-registered)

- **R-a G3′ on arm A (Simulated, 1 event).** The active policy can sit on a well-known region exactly when drift4
  jumps. On design data it produced one wrong certificate at step 13, the step after a jump. A non-drift false
  certificate fails G3′ for A.
- **R-b G7(b) drift4 (Simulated).** Before the window tier, A drift4 log-loss regressed: 1.1729 against 1.1556 for C.
- **R-c G6(c) ood4 (Simulated).** The ood4 gain is small (+0.037) but positive. It has to stay ≥ −0.01.
- **R-d Compute.** Lookahead copies of the n≤5 margin can reach about 10⁵ rows. A copy that exceeds the budget scores 0;
  it does not crash the run.
- **R-e Selection effects (Inferred).** The active policy changes which states are visited, so on-policy metrics are
  not comparable to passive ones. Dual coverage and log-loss on the taken action are what the gates use.

## 6. Geometric framing (Inferred / Open)

- **The version space as a region.** Surviving rows are points in the space of n≤k Moore machines that agree with the
  evidence. Each observation intersects the region with a constraint. Certification means the region's projection onto
  the queried coordinate (the next code for action b) is a single point, and the n≤5 margin region projects to the same
  point. *Exact* as a restatement of the gate order.
- **Active experimentation picks the cut.** Entropy policies bisect volume; LU chooses the cut most likely to collapse
  a projection. The design evidence favours targeted collapse (*Simulated*, D1).
- **Roadmap beyond enumeration (Open).** Row enumeration is the representation limit: n≤6 does not fit in 160,000
  rows. Candidate representations:
  - quotient/partition lattices, with regions as sets of Myhill–Nerode partitions;
  - SAT/BDD encodings of the transition table, with projections by model counting;
  - interval or zonotope abstractions over code probabilities.

  The tracking is in [`docs/ROADMAP.md`](docs/ROADMAP.md) and [`NEXT_ITERATION.md`](NEXT_ITERATION.md).

## 7. Bridge items

- **B1, double issuance:** fixed by X3. API 1.1 is frozen and keeps the behaviour, which is documented. Study-003 counts
  are unaffected (*Exact* by code reading). This is verified on the sealed traces in `BRUTE_DEVIATIONS_004.md`.
- **B2, failing tests:** fixed by X6, and the README count is corrected.
- **B3, the experiment field:** delivered by X4.
