<p align="center">
  <img src="assets/brand/lockup.png" alt="Brute" width="520">
</p>

<p align="center"><b>A reasoner that abstains on what it cannot verify, chooses experiments that let it verify more, certifies only what holds on every place the world could have jumped to, and decides with an exact constraint representation of what it knows.</b><br>
<sub>Brute v0.6.0 · forked from BGR v0.90.0 · research preview · not AGI</sub></p>

---

## v0.6.0 at a glance: 11 of 16 gated criteria pass; 5 fail, including both headline targets (a) and (b)

On the pre-registered study-008 (936 held-out cases, plan frozen at `89c2d3b` before any code) **11 of 16 gated criteria pass** (*Observed*). **Failed, and they stay failed:**

- **GA1 (target a, drift-sound certification): NOT MET.** Neither new rule passes G1 + G2 + G3′ + G6b. **G3′ fails for both:** R6 1 and C6 2 false certificates at non-drift steps on drift4, each one step after a drift, none public. **G6b fails for both:** R6 − v0.2.0 coverage **−0.101** [−0.113, −0.090], C6 − v0.2.0 **−0.072** [−0.084, −0.061] (≥ −0.03 required). The pre-registered prediction was FAIL (*Inferred*).
- **GX2′ (target b, non-enumeration exactness check): FAIL, incomplete coverage.** The CaDiCaL cross-check was far too slow: at the stop it had checked **46 of 288** breadth cases in ~8.8 h. The owner decided to stop it and release ([D21](docs/research/BRUTE_DEVIATIONS_008.md)). The frozen criterion needs ≥ 99% of steps checked for every family × arm, so it fails. On what was checked (46 big6 cases): **0 mismatching traces, 0 witness failures** (*Observed*). Even inside those 46 cases only 98.6% of steps were checkable within the per-query budget, which is below 0.99 (*Observed*).
- **G5 (false alarms ≤ 5% per family and arm): FAIL.** perm4 R6 and C6 had 4 of 72 cases (0.056). The same 4 cases (mask 0.1, alarm at step 8–9) also alarm in the frozen A4/A5 arms, so this comes from the shared τ6 alarm on fresh seeds, not the new rules (*Observed*).

**Passed:**

- **GT1 (target c):** a new verifier rejects all 56 corrupted-artifact cases with `VerificationError`. The frozen v0.5.0 verifier is untouched and still shows its recorded defect (*Exact*).
- **GMC (target d, gated separately):** exact model counting (pyganak) counted |R_t| on 3,232 of 3,240 sampled steps (99.75%), with 0 disagreements with an independent blocking-clause count and 0 sum-check violations. Counts never feed certification (*Observed*).
- **G1/G2 soundness:** 0 false certificates in family and out of family for every arm.
- G4, G7, G9, G10, G11, G12, G13.

## Overview

Brute is a small, exact reasoner for hidden finite-state worlds. It watches actions and masked sensor readings, keeps every hidden machine that is still consistent with the evidence (the *version space*, a region), and predicts the next reading **only** when every surviving explanation agrees (the region's projection onto that reading is a single point, and a larger margin bound agrees). Since v0.2.0 it also acts: it picks the action whose answers would let it certify most (a one-step lookahead). Since v0.3.0 a certificate must also hold on the *fibre* of the region over the latest observation (rule Y1k), so an unseen jump cannot leave a stale certificate standing. v0.4.0 added an exact constraint (H-) representation of the region and verified it against enumeration.

**v0.6.0** keeps the v0.5.0 SAT region engine and tests four things against a frozen plan: two drift-sound certification rules (R6, C6), a non-enumeration exactness check (a second SAT encoding solved by CaDiCaL), a verifier that turns every malformed artifact into `VerificationError`, and exact model counting as a separately gated feasibility study. Results are at the top of this page; the v0.5.0 description follows.

**v0.5.0 made the constraint region the engine.** `brute/region.py` (`RegionK`, `RegionSpace`) answers every learner query — support, saturation, Y1k fibre, lookahead — with SAT queries (pysat Glucose3) over complete Moore machines with k actions and s sensors, instead of enumerating machines. If the solver hits its conflict budget, the answer is UNKNOWN and the forecast becomes **ABSTAIN / SOLVER_BUDGET** — never a certificate (*Exact*, by construction and unit test; *Observed* on a stress block: 257 such forecasts, 0 certificates). On the pre-registered study-007 the SAT learner **A5 makes the same decision as the frozen enumeration learner A4 on all 25,344 steps** (GX1, 0 mismatches, 0 excluded). It also runs where enumeration cannot: **breadth families** with 6 states, 3 sensors or 3 actions, with **0 false certificates** in family and 0 public certificates out of family. A new experiment rule **M** (break lookahead ties toward the experiment expected to leave the smallest fibre-projection *volume*) raises coverage (+0.026, CI95 [0.011, 0.043] on 2x2; +0.039 [0.020, 0.058] on breadth) but costs one non-drift false certificate on drift4, so by the registered rule it is **NOT DISTINGUISHED**.

On study-007 (v0.5.0; 864 held-out cases + 24 stress cases) **12 of 15 gated criteria passed**. Three fail and stay failed: **GX2** (the breadth reference enumeration ran out of budget on too many act3 steps: 84.5% checked vs 90% registered; 0 mismatches where it ran), **G3′** (M5: 1 false certificate at a non-drift step on drift4), and **G6b** (M5 − v0.2.0 coverage −0.080, CI95 [−0.100, −0.060]; predicted to fail).

This release also carries the [v0.4.0 errata](docs/research/v0.4.0/ERRATA.md) from an outside review: v0.4.0's held-out discipline was broken once (96 study-006 cases ran before the scoring-script commit), its scaling exponents are withdrawn, and its audit did not recompute probabilities (a post-hoc recompute found 0 mismatches).

Brute is a fork of **BGR (Bitwork Geometric Reasoning) v0.90.0**, and that research is credited in full ([`FORK.md`](FORK.md)).

## Status

| | |
| --- | --- |
| Version | *Exact.* 0.6.0 (`RELEASE.json`, `pyproject.toml`, `brute.release_version_060.RELEASE_VERSION`). Earlier `release_version*` modules keep their own versions (earlier freezes) |
| Tests | *Observed* at release: see [Test suite at release](#test-suite-at-release) |
| Study | `BRUTE-060-DRIFTSOUND-008`. *Exact* (git ancestry): plan `89c2d3b` → reference `8863f06` → implementation `457db5a`/`6556186`/`ff4d0d8`/`6f6cd22` → pre-freeze fix `cae25ce` → source freeze `8e80615` → scoring scripts `08ac3f3` (08:38:46 EDT) → ledger `run_start_008` (08:49:16 EDT) → seal `c21ef12` (09:04:53 EDT). Scoring scripts unchanged since their single commit. Stream A (xcheck) was stopped by the owner at 17:44 EDT, after 46/288 cases. Commit times are the author's clock (*Observed*, not attested). Deviations: [`BRUTE_DEVIATIONS_008.md`](docs/research/BRUTE_DEVIATIONS_008.md) |
| Gates | *Observed.* **11 of 16 gated pass. GA1, G3′, G5, G6b and GX2′ fail.** GT1 and GMC pass ([`results/study-008/GATES_008_FINAL.json`](results/study-008/GATES_008_FINAL.json)) |
| Verifier | *Exact.* `python scripts/verify_release_060.py --fast` parses every artifact and raises `VerificationError` on any malformed file. It also checks seals, freezes, ledger chronology, the manifest, git order and version consistency, and regenerates the gates, paired analysis and reproducibility byte-for-byte |
| Interface | *Exact.* `brute.api` 1.0–1.5, unchanged (`BruteServiceV050`). The R6/C6 rules live in `brute/driftsound.py` as research arms and are not exposed in the API. The language adapter is template-only; no language model is connected |
| Storage | *Exact.* Sealed traces for studies 004–008 are committed as deterministic gzip; `python scripts/study00{4,5,6,7,8}_storage.py restore` rebuilds them and checks them against `SEAL.json` |
| Environment | *Exact.* Python 3.13.5, numpy 2.5.4, python-sat 1.9.dev17 (`requirements.txt`, `pyproject.toml`); model counting (reporting only) pyganak 2.8.0, pyapproxmc 4.4.0 (`requirements-gmc.txt`) |

Every result claim in this README (status, gates, scaling, findings, limits) carries a label; descriptive sections (How it works, Quickstart, Repository) describe code and are not evidence claims:

- **Exact**: proved or verified by the tests or by exact computation in this repository.
- **Observed**: measured in study-008 (`results/study-008/SCIENTIFIC.json`, sealed), or in earlier studies where stated.
- **Simulated**: a counterfactual predictor rescored on earlier sealed traces (design evidence, not pre-registered evidence).
- **Inferred**: reasoning or a model fitted after the fact, not measured.
- **Rejected**: considered and dropped, with the reason given.
- **Open**: unresolved.

## Study-008 (v0.6.0) against the pre-registered criteria (*Observed*)

New arms on the 2x2 families: **R6** (for 8 steps after a surprise, transitions confirmed only before it count as unknown) and **C6** (certify on the v0.2.0 tracked state while there has been no surprise). Controls are A5 (v0.5.0), A4 and A2 (frozen). The release default stays the v0.5.0 rule (Y1k, LU-R) whatever the outcome; there is no auto-promotion (*Exact*, plan `default_policy_rule`). Breadth arms are **BR6** and **BC6** (the breadth versions), plus B5. There are 648 2x2 cases and 288 breadth cases (24 held-out seeds × 3 mask rates per family). The plan is [`BRUTE_PLAN_008.json`](experiments/BRUTE_PLAN_008.json) ([readable](docs/research/v0.6.0/PLAN_008.md)), the gates are in [`GATES_008_FINAL.json`](results/study-008/GATES_008_FINAL.json), and the deviations are in [`BRUTE_DEVIATIONS_008.md`](docs/research/BRUTE_DEVIATIONS_008.md) (D1–D23).

| Criterion | Result | Key numbers |
| --- | --- | --- |
| **GA1 target (a): one of R6/C6 passes G1+G2+G3′+G6b** | **FAIL** (predicted FAIL) | no passing arm. Both R6 and C6 pass G1/G2, and both fail G3′ and G6b |
| G1 in-family soundness | PASS | 0 false certificates. 2x2 certificates: R6 3,516 and C6 4,321 (cycle3/switch3/unstructured3/unaliased2/ood4/perm4). Breadth certificates: B5 1,780, BR6 1,644 and BC6 1,875 (big6/sens3/act3) |
| G2 ood soundness | PASS | ood5: R6 0 of 39, C6 0 of 44. ood6s3: B5 0 of 505, BR6 0 of 486, BC6 0 of 550 |
| **G3′ drift4 (0 wrong at non-drift steps, total ≤ 50% of v0.90)** | **FAIL** | **R6** 20 false, **1 non-drift**. **C6** 26 false, **2 non-drift**. The limit is 86 (v0.90 had 172). All three non-drift events come one step after a drift (step 13 or 24) and none is public. A5 had 25 false certificates and the same step-13 event, so it would also fail here (reported, not gated) |
| G4 public safety | PASS | 0 public certificates out of family, 0 public false certificates, 0 public certificates after the first alarm |
| **G5 false alarms ≤ 5% per family and arm** | **FAIL** | perm4 R6 and C6 4 of 72 (0.0556). The same 4 cases alarm in A4/A5 (τ6 alarm). Every other family is 0 of 72 |
| **G6b R6/C6 − A2 ≥ −0.03, CI lower ≥ −0.05** | **FAIL** | **R6 −0.101235 [−0.112695, −0.089699]**, **C6 −0.072145 [−0.084144, −0.060724]** |
| G7 open world | PASS | log-loss ood5 0.644, drift4 1.095 (≤ ln 4), ood6s3 1.371 (≤ ln 8). Minimum p is 0.005 on 2x2 and 0.0025 on breadth |
| G9 retraction + resume | PASS | 273 retractions, with reasons that match the reference. 0 duplicates, 8 resumes, 0 rule violations |
| G10 compute | PASS | 936/936 cases. 0 production forecasts used an UNKNOWN solver answer |
| G11 second implementation (same author, not independent) | PASS | 0 mismatching of 1,872 arm traces; mutation test 20/20 detected, 0 false flags |
| G12 reproducibility | PASS | 312/312 rerun cases byte-identical. GMC recount on 120 cases is identical except for 11 timeout-only differences |
| G13 frozen controls | PASS | freeze chain holds; τ6 = 1.645215321642 and τ7 = 2.07944154168 are used by every case |
| **GX2′ target (b): xcheck ≥ 99% of steps per family × arm, 0 mismatches, agrees with enumeration** | **FAIL** (incomplete coverage) | Stopped by owner decision at **46/288** cases ([D21](docs/research/BRUTE_DEVIATIONS_008.md)). Checked fraction over all sealed cases: big6 0.630, sens3/act3/ood6s3 0.0. On what was checked: 0 mismatching traces, 0 witness failures, 0 disagreements with enumeration, and 49 UNKNOWN queries (*Observed*). Within the 46 checked cases the fraction was 0.986 < 0.99 |
| GT1 target (c): verifier parse errors | PASS | 56/56 corruption cases give `VerificationError`; 0 other exception types; 0 silent passes. The frozen `verify_release_050` still raises `JSONDecodeError` (unchanged) |
| GMC target (d): model counting feasibility (gated separately) | PASS | 3,232/3,240 sampled steps counted (0.997531). 8 are UNKNOWN (5 budget, 3 timeout) and get approxmc estimates labelled *Inferred*. 0 disagreements on 2,641 compared steps, 0 sum-check violations |

Reported, not gated (*Observed*):

- **Coverage contrasts.** C6 − A5 is **+0.023** [0.019, 0.027] and R6 − A5 is −0.003 [−0.004, −0.002]. On breadth, BC6 − B5 is +0.0038 [0.0017, 0.0065] and BR6 − B5 is −0.0051 [−0.0072, −0.0033].
- **Breadth model counts.** 1,881 of 2,016 sampled steps were counted (0.933), with 0 disagreements.
- **R_dev_xcheck_007** was not run, because it was queued after the stopped xcheck.

## Study-007 (v0.5.0) against the pre-registered criteria (*Observed*, kept for reference)

Arms on the eight 2x2 families (2 actions, 2 binary sensors, ≤4 states with a ≤5 margin): **A5** v0.5.0 (SAT region backend, v0.4.0 rules), **M5** A5 + projection-volume tie-break, **A4** frozen v0.4.0 (enumeration), **A2** frozen v0.2.0. Breadth families (pre-registered before any data): **big6** (≤6/≤7 states), **sens3** (3 sensors), **act3** (3 actions), **ood6s3** (declared out of family), with arms **B5** (active), **BM5** (active + M), **BP5** (passive). 2x2: 8 families × 24 held-out seeds × 3 mask rates = 576 cases; breadth 4 × 24 × 3 = 288; stress block 24 (tiny conflict budget).

| Criterion | Result | Key numbers |
| --- | --- | --- |
| **GX1 backend exactness, 2x2 (A5 vs A4, excluded ≤ 1%)** | **PASS** | **0 mismatches in 25,344 steps, 0 excluded**; A5 − A4 coverage 0 exactly |
| **GX2 backend exactness, breadth (vs second implementation)** | **FAIL** | **0 mismatching steps**, but the reference enumeration stopped at its 160,000-row budget on 15 act3 traces: act3 B5/BP5 84.5% of steps checked, registered minimum 90%. sens3, ood6s3 100%; big6 79–81% (reported, no floor) |
| **GX3 budget exhaustion ⇒ abstain** | **PASS** | stress block: 257 forecasts used an UNKNOWN answer, all ABSTAIN / SOLVER_BUDGET, 0 certificates; 0 production certificates with an UNKNOWN; unit tests pass |
| G1 in-family soundness (taken + public) | PASS | 0 false certificates in every arm and family: A5 3,945, M5 4,853 on 2x2 (cycle3/switch3/unstructured3/unaliased2/ood4/perm4); breadth B5 2,108, BM5 3,456, BP5 802 (big6/sens3/act3). Rule-of-three upper rate e.g. M5 cycle3 0.0028 |
| G2 ood soundness | PASS | ood5: A5 0 of 72, M5 0 of 186; ood6s3: B5 0 of 252, BM5 0 of 995, BP5 0 of 24 |
| **G3′ drift4 (0 wrong at non-drift steps, total ≤ 50% of v0.90)** | **FAIL** | A5 6 false, 0 non-drift; **M5 25 false, 1 non-drift** (two steps after a drift; not public; [Q7](docs/research/BRUTE_DEVIATIONS_007.md)); limit 36 (v0.90: 72). A2 14 (1 non-drift), A4 6 (0) |
| G4 public safety | PASS | 0 public certificates on ood5/drift4/ood6s3; 0 public false anywhere; 0 public after the first alarm |
| G5 in-family false alarms ≤ 5% per family and arm | PASS | 0 of 72 in every in-family family and arm (τ6 = 1.645 on 2x2; τ7 = 2.079 on breadth) |
| **G6b M5 − A2 ≥ −0.03, CI lower ≥ −0.05** | **FAIL** (predicted) | **−0.079591, CI95 [−0.099615, −0.060224]**; A5 − A2 = A4 − A2 −0.105401 [−0.117595, −0.093633] (reported) |
| G7 open world | PASS | log-loss ood5 A5 0.671 / M5 0.543; drift4 A5 1.043 / M5 1.091 (≤ ln 4); ood6s3 B5 1.380 / BM5 0.582 / BP5 1.444 (≤ ln 8); min p 0.005 (2x2), 0.0025 (breadth) |
| G9 retraction + resume | PASS | 242 retractions (29 falsified, 138 scope withdrawn, 75 unverifiable), reasons match the reference; 0 duplicates; 2 resumes, 0 rule violations |
| G10 compute | PASS | all 888 jobs present; 0 production forecasts with an UNKNOWN (2x2 101,376; breadth 124,416). Wall clock (informational, shared box): A4 104 s, A5 276 s, M5 344 s, B5 666 s, BM5 1,099 s |
| G11 second implementation (**same author, no `brute` import; not independent**) | PASS | **0 mismatching of 2,592 arm traces**; mutation test 20/20 injected errors detected, 0 false flags. Post-hoc (not registered): forecast probabilities recomputed on taken and untaken branches for A4/A5/M5, 0 of 1,728 traces, 130,602 forecasts, swap mutations 20/20 |
| G12 reproducibility | PASS | every third job rerun (296: 192 2x2, 96 breadth, 8 stress) byte-identical; calibration and traces byte-identical |
| G13 τ7 reproduces | PASS | τ7 = 2.07944154168 (450 in-family breadth calibration cases; argmax sens3 seed 1721016, mask 0.1) |
| GM projection-volume rule (decision, not gated) | **NOT DISTINGUISHED** | M5 − A5 **+0.026202, CI95 [0.010930, 0.042536]** (cycle3 +0.054, perm4 +0.028, unaliased2 +0.031, unstructured3 +0.036, switch3 +0.011, ood4 −0.003); breadth BM5 − B5 **+0.039131 [0.020403, 0.057874]** (act3 +0.091, big6 +0.039, sens3 −0.013). SUPPORTED needed G3′ to hold for M5; it does not |
| GR2′ scaling (reported, not gated) | — | see below |

Paired, seed-clustered bootstrap (2,000 resamples, seed 20261025; [`PAIRED_ANALYSIS.json`](results/study-007/PAIRED_ANALYSIS.json)). BP5 (passive) − B5 −0.044533 [−0.060310, −0.030285]: on breadth, experiments still buy coverage.

### Breadth coverage after burn-in (*Observed*, all-action coverage)

| Family | B5 / BM5 / BP5 | Note |
| --- | --- | --- |
| act3 (3 actions) | 0.061 / **0.152** / 0.009 | M's largest gain |
| big6 (≤6, margin ≤7) | 0.028 / **0.067** / 0.005 | beyond enumeration's reach for most steps |
| sens3 (3 sensors) | **0.138** / 0.125 / 0.081 | M slightly below B5 (−0.013, CI includes 0) |
| ood6s3 (declared out of family) | 0.031 / 0.121 / 0.003 | alarms in 21 / 9 / 24 of 72 cases; 0 false certificates |

### How the region backend scales (GR2′, *Observed* raw; fits *Inferred*)

Six cases per bound and alphabet, every step, SAT at n = 4..12, enumeration where it fits. **0 UNKNOWN answers at every n** (production conflict budget); enumeration agreed on every step where it ran (0 disagreements).

| n | Max clauses 2a2s / 2a3s / 3a2s | Enumeration max rows 2a2s / 2a3s / 3a2s | Case seconds mean (max), 2a2s |
| --- | --- | --- | --- |
| 4 | 2,323 / 3,139 / 2,399 | 87 / 69 / 2,078 | 0.04 (0.05) |
| 6 | 4,420 / 5,622 / 4,603 | 2,709 / 3,784 / budget (6 of 6 exhausted) | 0.22 (0.29) |
| 8 | 7,209 / 8,797 / 7,579 | not run | 0.72 (1.60) |
| 10 | 10,738 / 12,712 / 11,399 | not run | 0.49 (0.83) |
| 12 | 15,055 / 17,415 / 16,135 | not run | 0.51 (0.65) |

Fits ([`SCALING_FIT_007.json`](docs/research/v0.5.0/SCALING_FIT_007.json), `scripts/scaling_fit.py`, post hoc, *Inferred*): clause maxima are fitted by a cubic y = c0 + c1·n + c2·n² + c3·n³ (2a2s: 13 + 275.7n + 68.5n² + n³, R² 0.99988); with 4 parameters on 5 values of n this is close to interpolation and is **not** evidence for the degree. A power law gives exponents 1.71 / 1.57 / 1.74 with residuals that curve (+0.02 at n = 4, −0.02 at n = 6–8, +0.02–0.03 at n = 12), so it is mis-specified. Enumeration has only two uncensored n values and is **not fitted**. **Time is noisy and non-monotone** (2a2s n = 8 mean 0.72 s vs n = 12 0.51 s; 3a2s n = 6 7.3 s mean / 14.9 s max, because its case time includes the enumeration side that exhausted its budget). The representation grows polynomially in size (*Exact*: O(T·n² + n³) clauses by construction); SAT time is not guaranteed polynomial (*Exact*, NP-hard in general). **GR2′ rests on 5 bounds × 6 cases per alphabet.**

Findings and their math: [`docs/research/DISCOVERIES.md`](docs/research/DISCOVERIES.md) D22–D25.

## Study-006 (v0.4.0) against its pre-registered criteria (*Observed*, kept for reference)

Arms: **A4** v0.4.0 active (v0.3.0 Y1k + LU-R + τ6 + resume; identical to A3 except after a resume), **P4** v0.4.0 passive, **A3** v0.3.0, **A2** frozen v0.2.0, **E2** v0.2.0 + forced untaken-branch checks (mechanism arm), **D2** depth-2 lookahead candidate, **F2** two-step-fibre candidate, **C** frozen v0.1.1 control, plus the v0.90 control. 8 families × 24 new held-out seeds × 3 mask rates = 576 cases; D7/D8 block 384 drift4 seeds × 3 masks = 1,152 cases.

| Criterion | Result | Key numbers |
| --- | --- | --- |
| G1 in-family soundness (A4, P4; taken + counterfactual + public) | PASS | A4 0 false of 2,686 taken + 736 counterfactual; P4 0 of 804 + 873; D2 0 of 4,305 + 372; F2 0 of 4,863 + 630; every arm 0 public false |
| G2 ood5 false certificates = 0 | PASS | A4 0 of 180; P4 0 of 5; v0.90 control 79 of 165 |
| G3′ drift4: 0 wrong at non-drift steps and total ≤ 50% of v0.90 | PASS | A4 13 of 104, all at drift steps, 0 stale; P4 1 of 15 (1 stale counterfactual, errata E5); limit 36 (v0.90: 72). A2 25 (2 non-drift, 2 stale) |
| G4 public safety | PASS | 0 public certificates on ood5/drift4; 0 public false anywhere; 0 public after the first alarm |
| **G5 in-family false-alarm cases ≤ 5%, per family and per arm** (any-step reading, deviation P3) | **PASS** (failed in v0.3.0) | ood4 A4 1/72 (0.014), perm4 2/72 (0.028), others 0. **v0.3.0 τ on the same seeds: ood4 also 1/72**, perm4 14/72 — the recalibration matters on perm4, not on ood4 here |
| G6 active coverage gain (A4 − P4 ≥ 0.05, CI > 0, no family < −0.01) | PASS | **+0.059182, CI95 [0.050153, 0.068635]**; perm4 (reported, not pooled) +0.036 [0.015, 0.060] |
| **G6b′ coverage non-inferiority vs v0.2.0 (A4 − A2 ≥ −0.03, CI lower ≥ −0.05)** | **FAIL** (pre-registered as expected) | **−0.103781, CI95 [−0.115972, −0.091898]**; A4 − A3 = 0 exactly |
| G7′ open-world no regression | PASS | ood5 A4 0.5999 / C 0.6253 / A2 0.5758; drift4 A4 1.0076 / C 1.0151 / A2 1.0186; all ≤ ln 4; min p 0.005 |
| G8 passive equivalence | PASS | P4 vs C: 0 non-resync differences in all 8 families; A4 in-family log-loss below C in every family |
| G9 retraction semantics + de-duplication | PASS | 103 retractions (12 falsified, 66 scope withdrawn, 25 unverifiable); 0 duplicates; resume rule 0 violations in 6 resumes |
| G10 compute budget | PASS | peak 106,246 of 160,000 rows (A4/P4 incl. lookahead); 0 exhaustions. Wall clock (informational): A4 146 s, D2 991 s |
| G11 second implementation (**same author, no `brute` import; not independent**) | PASS | **0 mismatching of 2,880 arm traces**; mutation test 20/20 injected errors detected, 0 false flags. In the v0.90 regime it checked forecast probabilities only for sum/floor/source (errata E3); post-hoc recompute: 0/1,152 A4+P4 traces, 88,038 forecasts, swap mutations 20/20 |
| G12 reproducibility | PASS | rerun `CALIBRATION_006.json` and `SCIENTIFIC.json` byte-identical |
| G13 τ6 reproduces | PASS | τ6 = 1.645215321642 (1,500 in-family calibration cases; argmax ood4 seed 1515061, mask 0.35) |
| **GR1 exactness on sealed study-004/005 traces (development set)** | **PASS** | ConstraintRegion vs enumeration, 4 arms × 504 traces, taken + counterfactual: **0 mismatches in 778,840 items** |
| **GR1b exactness on study-006** | **PASS** | A4 252,080 + P4 199,220 items (576 traces each), D2 9,640 + F2 9,378 (96-case subsample): **0 mismatches in 470,318** |
| G14′ D7/D8 powered (decision, not gated) | **OPEN** | R = S(E2)/S(A2) = 48/76 = **0.632, CI95 [0.418, 0.907]**; M and P1 hold. CONFIRMED needs CI upper < 0.75; FALSIFIED needs CI lower > 0.5. Main 72-case drift4 block (not registered): R = 3/2 = 1.5 with 266/2,000 zero-denominator resamples (errata E7) |
| G15 depth-2 lookahead D2 (candidate, not gated) | FAIL (predicted) | G1/G2/G3′ hold; D2 − A2 **−0.071 [−0.085, −0.057]** (needs ≥ −0.03) |
| G16 two-step fibre F2 (candidate, not gated) | FAIL (predicted) | F2 − A2 −0.033 [−0.040, −0.026]; **G3′ breaks**: 2 non-drift false, 2 stale on drift4 |

Paired, seed-clustered bootstrap (2,000 resamples, seed 20261025; [`PAIRED_ANALYSIS.json`](results/study-006/PAIRED_ANALYSIS.json)). Power analysis (pre-registered, *Simulated* on study-005 seeds): N = 384 seeds gives power ≥ 0.9 under the observed-effect and half-effect scenarios.

### Study-006 coverage after burn-in (*Observed*)

| Family | Dual coverage P4 / A4 / A2 / D2 / F2 / E2 | C (v0.1.1) |
| --- | --- | --- |
| cycle3 | 0.078 / **0.136** / 0.316 / 0.148 / 0.273 / 0.266 | 0.193 |
| switch3 | 0.126 / **0.179** / 0.293 / 0.232 / 0.259 / 0.263 | 0.180 |
| unstructured3 | 0.045 / **0.109** / 0.222 / 0.154 / 0.179 / 0.154 | 0.084 |
| unaliased2 | 0.050 / **0.151** / 0.238 / 0.190 / 0.210 / 0.141 | 0.074 |
| ood4 | 0.002 / **0.022** / 0.047 / 0.037 / 0.032 / 0.078 | 0.003 |
| perm4 (new) | 0.017 / **0.053** / 0.101 / 0.119 / 0.094 / 0.079 | 0.033 |

### Study-006 GR2 scaling of the constraint region (*Observed*, not gated; superseded by GR2′ above)

84 cases (7 families × 3 masks × 4 seeds), every step, enumeration at n = 2..6 vs `ConstraintRegion` at n = 2..12. Enum-vs-SAT: **0 disagreeing steps** among steps both sides decided. Excluded and reported: enumeration exhausted the 160,000-row budget in 10 cases at n = 6 (251 steps); SAT hit its 20,000-conflict per-query budget at n = 8 (5 steps), 10 (8) and 12 (4) (deviation P2).

| n | Enum mean / max peak rows | Enum mean / max case time | SAT max variables / clauses | SAT mean / median case time |
| --- | --- | --- | --- | --- |
| 2 | 4.2 / 12 | <0.001 s | 130 / 899 | 0.013 s |
| 4 | 435 / 4,053 | 0.01 s / 0.15 s | 268 / 2,369 | 0.076 s |
| 5 | 8,560 / 103,870 | 0.77 s / 19.8 s | 343 / 3,338 | 0.138 s |
| 6 | 33,516 / 159,434 (10 exhausted) | 2.20 s / 63.3 s | 422 / 4,471 | 0.97 s / 0.16 s |
| 8 | not run (beyond budget) | — | 592 / 7,253 | 1.24 s / 0.33 s |
| 10 | not run | — | 778 / 10,763 | 1.29 s / 0.34 s |
| 12 | not run | — | 980 / 15,049 | 2.34 s / 0.72 s |

**Caveats (deviation P5).** Times are wall clock on one shared 8-CPU box. SAT time is **noisy and non-monotone** in n and mask (e.g. mask 0.6, n = 12: 5.5 s mean; mask 0.1, n = 12: 0.79 s, below n = 10's 3.02 s); SAT maxima of ~63–70 s occur at n ≥ 6, but n = 6 had 0 unknown queries; conflict-budget hits are at n = 8/10/12 only (errata E6). ~~The log-log slopes — enum peak rows vs n 8.5, enum time 8.7, SAT clauses 1.6, SAT mean time 3.1~~ are **withdrawn** (errata E2: power law mis-specified for enumeration, n = 6 censored; small-n slope for clauses). Refit with residuals, *Inferred*: enumeration peak rows exponential, ×6.9 per state (n = 2..5, residual SD 1.56 in log); clause maxima cubic, 13 + 271n + 67n² + n³. The representation is polynomial in size; SAT solving time is not guaranteed polynomial (*Exact*, NP-hard in general).

Findings and their math: [`docs/research/DISCOVERIES.md`](docs/research/DISCOVERIES.md) D17–D21.

## Test suite at release

*Observed* on the release branch tree at `3d9f587` (`python -m unittest discover -s tests`, 294 s): **213 tests, 204 pass, 1 failure, 8 errors.**

- **8 of 9 are by construction.** These frozen earlier-release tests check their own version, or verify the current tree as their release: `test_release_011/020/030::test_fast_verify_passes`, `test_brute_repro::test_verify_fails_under_tampered_results`, and `test_release_040::{test_fast_verify_passes, test_git_order, test_untampered_copy_passes, test_version_consistent}`. `test_release_040` is "version-parameterised", but its verifier is pinned to study-006 and its freezes, so it errors once `RELEASE.json` says 0.5.0. They can't be edited (frozen), and they pass on their own tags.
- **1 is a real defect in the v0.5.0 test/verifier pair.** In `tests/test_release_050.py::test_tampered_copies_fail`, the tamper case for `results/study-007/SECOND_IMPLEMENTATION_COUNT.json` corrupts the JSON. The verifier then rejects the tampered copy by raising an uncaught `JSONDecodeError` instead of `VerificationError`. The tampered copy still does not verify, but the error is of the wrong type. Both files were frozen in `BRUTE_RELEASE_FREEZE_050` before this run showed the problem, so the defect is recorded rather than patched. It is listed for v0.6.0.
- The other 4 `test_release_050` tests pass. These are the version check, the untampered-copy control, git order, and fast verify, plus the other tamper cases.
- `scripts/verify_release_050.py --fast` passes on the branch and in a fresh clone after `study00{4,5,6,7}_storage.py restore`.

## Study-005 (v0.3.0) against its pre-registered criteria (*Observed*, kept for reference)


| Criterion | Result | Key numbers |
| --- | --- | --- |
| G1 in-family soundness, A3 and P3, taken + counterfactual, public | PASS | 0 false of 2,635 taken + 574 counterfactual certificates (A3); 0 of 729 + 771 (P3); 0 public false. Every other arm also 0 |
| G2 ood5 false certificates = 0 | PASS | A3 0 of 113 (+4 counterfactual); P3 0 of 8; v0.90 control 85 of 174 |
| **G3′ drift4: 0 wrong at non-drift steps and total ≤ 50% of v0.90** | **PASS** (failed in v0.2.0) | A3 9 of 62, all at drift steps, 0 stale; P3 0 of 6; limit 44.5 (v0.90: 89). v0.2.0 A2 on the same seeds: 15, 1 non-drift, 2 stale. Extended 216-case block (not gated): A3 38 false / 2 non-drift / 4 stale; A2 62 / 14 / 15; E2 38 / 12 / 14 — the G3′ "0 non-drift" clause would fail there |
| G4 public safety | PASS | 0 public certificates on ood5/drift4; 0 public false anywhere |
| **G5 in-family false-alarm cases ≤ 5%, scored per family** (the plan text does not say per family or pooled; the scoring script and studies 003–005 use per family, the stricter reading; pooled would be 5/360 = 0.014) | **FAIL** | ood4 5 of 72 (0.069) in A3 and P3; identical in frozen v0.1.1, A2, P2 (unchanged alarm rule and τ). Other families 0 |
| G6 active coverage gain (A3 − P3 ≥ 0.05, CI > 0, no family < −0.01) | PASS | **+0.064352, CI95 [0.055054, 0.073922]**; every family CI excludes 0 |
| **G6b coverage non-inferiority vs v0.2.0 (A3 − A2 ≥ −0.03, CI lower ≥ −0.05)** | **FAIL** (pre-registered as expected) | **−0.098264, CI95 [−0.110885, −0.087267]** (design −0.094) |
| G7 open-world no regression (A3, P3 ≤ C; ≤ ln 4; min p ≥ 0.005; A3 ≤ A2 + 0.05) | PASS | ood5 A3 0.63875 / P3 = C 0.648728 / A2 0.628252; drift4 A3 1.162304 / P3 1.163681 / A2 1.170786 / C 1.181917 |
| G8 passive equivalence (P3 ≡ P2 except RESYNC; A3 in-family ≤ C + 0.05) | PASS | A3 in-family log-loss below C in every family |
| G9 retraction semantics + de-duplication | PASS | 81 retractions (9 falsified, 47 scope withdrawn, 25 unverifiable); 0 duplicates; 0 RESYNC_AMBIGUOUS issued |
| G10 compute budget | PASS | peak 100,230 of 160,000 rows; 0 exhaustions; wall clock A3/C 1.19 |
| G11 "independent audit" (as registered) — in fact a **second implementation by the same author, no `brute` import**; not independent or third-party | PASS | 504 + 216 cases, 139,392 arm-steps replayed. The registered report stops at the first mismatch, so its "0 mismatches" means "ran to completion". Errata count (`scripts/audit_count_030.py`, scans everything): **0 mismatching of 3,168 arm traces** (*Observed*, E4 in the [errata](docs/research/v0.3.0/ERRATA.md)); a mutation test catches 8 of 8 injected errors |
| G12 reproducibility | PASS | rerun `CALIBRATION_CHECK.json` and `SCIENTIFIC.json` byte-identical |
| G13 τ reproduces | PASS | τ = 1.433141502274 |
| G14 D7/D8 single-mechanism test (decision, not gated) | **OPEN** | S(A2) 17, S(E2) 14, S(A3) 4 (stale false certificates, main + extended); CONFIRMED needed S(E2) ≤ 8.5, FALSIFIED S(E2) ≥ 17. S(E2) − S(A2) −3 [−12, +6] |

Paired, seed-clustered bootstrap (2,000 resamples, seed 20261025; [`PAIRED_ANALYSIS.json`](results/study-005/PAIRED_ANALYSIS.json)). Deviations: [`BRUTE_DEVIATIONS_005.md`](docs/research/BRUTE_DEVIATIONS_005.md).

### Study-005 coverage after burn-in (*Observed*)

| Family | Dual coverage P3 / A3 / A2 (v0.2.0) / E2 | RESYNC abstentions (A3) | Log-loss C / A3 |
| --- | --- | ---: | --- |
| cycle3 | 0.075 / **0.143** / 0.331 / 0.289 | 608 | 0.1846 / **0.1764** |
| switch3 | 0.115 / **0.180** / 0.289 / 0.277 | 397 | 0.2169 / **0.1939** |
| unstructured3 | 0.052 / **0.122** / 0.190 / 0.139 | 113 | 0.1619 / **0.1475** |
| unaliased2 | 0.041 / **0.129** / 0.218 / 0.137 | 170 | 0.0954 / **0.0877** |
| ood4 | 0.004 / **0.032** / 0.070 / 0.117 | 67 | 0.3755 / **0.3666** |

C (frozen v0.1.1, passive, `GATES.json` G6 `C_v011_coverage_post`) for context: cycle3 0.199, switch3 0.172, unstructured3 0.084, unaliased2 0.061, ood4 0.010 — in cycle3 A3 is below this passive control, so part of the G6 gain wins back coverage Y1k removed (review L2; *Observed*).

Findings and their math: [`docs/research/DISCOVERIES.md`](docs/research/DISCOVERIES.md) D11–D16. Study-005 deviations: [`BRUTE_DEVIATIONS_005.md`](docs/research/BRUTE_DEVIATIONS_005.md).

## What Brute can't do yet

- **It still pays for safety with coverage, and neither new rule fixes that.** G6b fails a fourth time. R6 is 0.101 below v0.2.0 in family and C6 is 0.072 below, against a −0.03 limit. C6 does recover some coverage (+0.023 over A5, CI above 0), but only about a quarter of the gap. *Observed.*
- **Its certificates can still be stale one step after a drift.** R6, C6 and the v0.5.0 default A5 each issued a false certificate one step after a drift (drift4 seed 1880047, step 13; C6 also seed 1880006, step 24). The drift-sound rules were meant to remove exactly this case, and they did not. Whether a one-step-late surprise signal is the whole cause is *Inferred* / *Open*.
- **Its false-alarm rate fails on perm4.** 4 of 72 fresh perm4 cases alarm under the shared τ6 alarm (also in A4/A5). The alarm threshold was calibrated once and is not re-tuned. *Observed.*
- **Breadth exactness is still not checked everywhere.** The non-enumeration check (CaDiCaL, second encoding) was correct wherever it ran (0 mismatches on 46 big6 cases), but at ~5 cases per hour it covered only 46 of 288 cases before the owner stopped it. Even inside big6 it could check only 98.6% of steps within its per-query budget. sens3, act3 and ood6s3 have no non-enumeration check at all. *Observed.*
- **SAT time has no guarantee.** 0 production forecasts needed an UNKNOWN answer, but the cross-check hit 49 UNKNOWN queries on big6 alone, and SAT is NP-hard. *Exact* / *Observed*.
- **Model counts are measured but not used.** |R_t| is exactly countable on 99.75% of sampled 2x2 steps and 93.3% of breadth steps. Nothing uses the counts yet: no count-weighted forecast or experiment choice has been tested. *Observed* / *Open*.
- **Breadth is still small:** ≤6 states (margin ≤7), ≤3 sensors or ≤3 actions, deterministic Moore machines. *Exact.*
- **It still pays ln 200 = 5.298 on every contradiction step.** *Exact* (ε reserve design).
- **It does not grow its own model class.** Families and caps are fixed by hand. *Exact.*
- **Public certificates need an outside attestation.** *Exact.*
- **The language adapter is templates only.** No free-form questions. *Exact.*
- **Its held-out discipline is self-reported and was bent again.** A pre-registered stream was stopped partway on an owner decision ([D21](docs/research/BRUTE_DEVIATIONS_008.md)). Only the progress count was looked at, and it is scored as FAIL on the frozen criterion, but the run is incomplete. The xcheck gate input is a wrapper-written partial report ([D22](docs/research/BRUTE_DEVIATIONS_008.md)), and packing was done by hand after the run script exited non-zero ([D23](docs/research/BRUTE_DEVIATIONS_008.md)). Commit times are the author's clock. *Observed* / author's report.
- **Its audit is not independent.** G11 and the xcheck are second implementations by the same author on the same machine. No third party has replicated anything. *Exact.*
- **Its test suite is still red by construction.** Frozen earlier-release tests assert older version strings and fail after every bump (see [Test suite at release](#test-suite-at-release)). *Observed.*
- **It is not AGI,** and nothing here shows general intelligence. *Exact.*

The longer path is in [`docs/ROADMAP.md`](docs/ROADMAP.md); open items for the next study are in [`HANDOFF.md`](HANDOFF.md).

## Quickstart

Requires Python 3.11+, NumPy and python-sat (pinned in `requirements.txt`). No GPU, network, or model weights.

```bash
git clone https://github.com/jacksonjp0311-gif/Brute.git && cd Brute
python -m pip install -r requirements.txt
for k in 4 5 6 7; do python scripts/study00${k}_storage.py restore; done   # gitignored raw traces from the committed gzip
python -m unittest discover -s tests            # see Status for the count
python scripts/verify_release_050.py --fast      # seals, freezes, regenerated gates/paired, ledger chronology, manifest, git order
python scripts/verify_release_050.py             # also re-runs the study-007 second-implementation count (same author; ~25 min on 6 workers)
python -m unittest tests.test_release_050         # version-parameterised release tests incl. tamper checks
```

A minimal API session:

```python
from brute.api import BruteService
s = BruteService()
s.handle({"api_version": "brute.api/1.0", "session_id": "demo", "op": "initialize",
          "observation": {"x": 0, "y": 0}, "family": {"max_states": 4}})
s.handle({"api_version": "brute.api/1.0", "session_id": "demo", "op": "observe",
          "action": "a", "observation": {"x": 0, "y": None}})
print(s.handle({"api_version": "brute.api/1.0", "session_id": "demo", "op": "predict", "action": "b"}))
```

An active experiment through API 1.2 (read-only; it changes no evidence):

```python
from brute.api.service_v020 import BruteServiceV020
s = BruteServiceV020()
s.handle({"api_version": "brute.api/1.2", "session_id": "demo", "op": "initialize",
          "observation": {"x": 0, "y": 0}, "family": {"max_states": 4}})
print(s.handle({"api_version": "brute.api/1.2", "session_id": "demo", "op": "experiment"}))
```

A v0.3.0 session through API 1.3 (experiment responses now carry `check`, `proposal` and `no_proposal_reason`; a certificate that fails the fibre test comes back from `predict` as ABSTAIN / RESYNC_AMBIGUOUS):

```python
from brute.api.service_v030 import BruteServiceV030
s = BruteServiceV030()
s.handle({"api_version": "brute.api/1.3", "session_id": "demo", "op": "initialize",
          "observation": {"x": 0, "y": 0}, "family": {"max_states": 4}})
print(s.handle({"api_version": "brute.api/1.3", "session_id": "demo", "op": "experiment"}))
```

The exact constraint region (v0.4.0, `brute/geometry.py`):

```python
from bgr90.symbolic import mask_for_observation
from brute.geometry import ConstraintRegion
R = ConstraintRegion(6, [mask_for_observation((0, 0)), mask_for_observation((0, None))], [0])   # n<=6, one step
print(R.feasible, R.support(0), R.support(1), R.saturated(), R.size); R.close()
```

The v0.5.0 SAT-backed learner through API 1.5 (a forecast that needed an UNKNOWN solver answer comes back ABSTAIN / SOLVER_BUDGET):

```python
from brute.api.service_v050 import BruteServiceV050
s = BruteServiceV050()
s.handle({"api_version": "brute.api/1.5", "session_id": "demo", "op": "initialize",
          "observation": {"x": 0, "y": 0}, "family": {"max_states": 4}})
s.handle({"api_version": "brute.api/1.5", "session_id": "demo", "op": "observe",
          "action": "a", "observation": {"x": 0, "y": None}})
print(s.handle({"api_version": "brute.api/1.5", "session_id": "demo", "op": "predict", "action": "b"}))
```

To rerun calibration and a study in a scratch directory and compare bytes with the sealed files (study-006 took about 25 minutes on this box; study-005 about 4 minutes on 4 workers):

```bash
python scripts/make_reproducibility_007.py         # every third study-007 job (296)
python scripts/make_reproducibility_006.py
python scripts/make_reproducibility_005.py --workers 4
```

## How it works

1. **Family support** (`brute/core`, `BruteLearner`): the exact symbolic support over n≤4 Moore machines (inherited from `bgr90`).
2. **Margin gate:** an n≤5 support must agree before Brute certifies. If the two disagree, it abstains with MARGIN_DISAGREES.
3. **Saturation check:** if every surviving explanation uses all 4 states, the bound may be the reason they agree, so Brute abstains with BOUND_SATURATED.
4. **Residual surprise:** a windowed (W=8) surprise test, with τ = 1.433141502274 calibrated on separate seeds (`CALIBRATION.json`), raises OUT_OF_FAMILY.
5. **Contradiction and retraction:** when no machine fits, Brute answers OUT_OF_FAMILY and withdraws issued certificates with a reason (falsified by observation, scope withdrawn, or unverifiable because masked).
6. **Fallback forecast (v0.1.1, `brute/fallback.py`):** after contradiction it forecasts from the n≤5 margin support (uniform over it, with the ε reserve) while that support is consistent, otherwise from a one-step suffix-frequency table. `forecast_source` names which.
7. **Active experiment (v0.2.0, `brute/active.py`):** for each action a and each possible reading c in the n≤4 support, intersect copies of the n≤4 and n≤5 regions with obs(a)=c and count the actions b that would then be CERTIFIED; take the action with the highest mean count (ties: the default action). Certification is unchanged.
8. **Window rebuild (v0.2.0):** after a contradiction, a fresh n≤4 learner restarted at each contradiction restricts the suffix-1 forecast (`forecast_source = window_n4`) when the margin support is gone.
9. **Fibre-robust certification (v0.3.0, `brute/changepoint.py`, rule Y1k):** a CERTIFIED forecast for action b must also be constant on the union, over every surviving n≤4 machine and every visited state that matches the latest observation, of that state's known successor reading under b (an unknown edge from the current state counts as any reading). Otherwise ABSTAIN with `RESYNC_AMBIGUOUS`, never issued.
10. **LU-R (v0.3.0):** the lookahead of step 7 with the step-9 test applied to each hypothetical answer.
11. **Open-world reserve:** ε = 0.02 is spread over all readings, so no probability falls below 0.005.
12. **`brute.api`:** versioned JSON request and response schemas (`brute/api/schema/*.v1.json`) and a service that never raises.
13. **Language adapter:** template rendering plus a checker that rejects any sentence not grounded in a response field.
14. **Resumable alarm (v0.4.0, `brute/resume.py`):** τ6 = 1.645215321642, calibrated on 1,500 in-family cases only; while the alarm is set, W consecutive residuals ≤ τ6 with the family and margin both supported clear it and certification may resume (conditional only; attestation is never re-enabled; contradiction never resumes).
15. **Constraint region (v0.4.0, `brute/geometry.py`):** the version space as CNF over complete ≤n Moore machines with canonical first-visit symmetry breaking (a fundamental domain of the S_n relabelling); support = projection, saturation = emptiness of a sub-region, fibre = certificate test, observation = cut. Verified decision-identical to enumeration (GR1, GR1b).
16. **Region backend (v0.5.0, `brute/region.py`, `brute/region_learner.py`):** `RegionK` generalises the constraint region to k actions and s sensors; `RegionBruteLearner` (A5) answers support, saturation, Y1k and LU-R lookahead with SAT queries under a per-query conflict budget. A query that returns UNKNOWN makes the forecast ABSTAIN / `SOLVER_BUDGET` (never CERTIFIED). Decision-identical to A4 on every study-007 step (GX1).
17. **Projection-volume tie-break M (v0.5.0, policy `M`):** when LU-R scores tie, take the action a with the smaller V(a) = mean over its possible readings c of Σ_b log2 |Y1k fibre projection for b| in the region cut by obs(a)=c (an infeasible or UNKNOWN branch counts as the maximum, 4 bits) — the experiment expected to leave the least fibre ambiguity. Certification is unchanged.
18. **Breadth learner (v0.5.0, `brute/breadth.py`):** B5/BM5/BP5 on k-action, s-sensor families (big6, sens3, act3) with τ7 = 2.079 calibrated on in-family breadth cases.
19. **Drift-sound rules (v0.6.0 research arms, `brute/driftsound.py`, not the default):** R6 (rule RO) treats as UNKNOWN in the Y1k check every transition edge whose confirming traversals all lie before the latest surprise (residual > τ/2 or a window-tier event), as long as that surprise is within the last W = 8 steps. C6 (rule CT) also certifies a code when the v0.2.0 tracked-state projection is a single code and the session has had no surprise, window event or contradiction. Neither rule has a tuned constant.
20. **Second-encoding exactness check (v0.6.0, `brute/xcheck_sat.py`, `experiments/v060_xcheck.py`):** an independent CNF encoding (no `brute.region` import) solved with CaDiCaL re-decides support, saturation and Y1k on breadth traces, with witness checking. It is far too slow for the full study as built: about 5 cases per hour.
21. **Model counting (v0.6.0, `brute/modelcount.py`, reporting only):** exact |R_t| with pyganak, checked against a blocking-clause count and against the per-reading sum identity; approxmc estimates are given only for UNKNOWN counts and are labelled *Inferred*. Counts never feed a decision.
22. **Hardened verifier (v0.6.0, `scripts/verify_release_060.py`):** every artifact read goes through one parser that raises `VerificationError` on any malformed, truncated, empty or key-missing file (GT1).

## Repository

| Path | Contents |
| --- | --- |
| `brute/core`, `brute/evaluation.py` | The v0.1.0 learner and evaluator (study-002 freeze) |
| `brute/api`, `adapters/language` | The API contract, service, and template language adapter (release freeze) |
| `brute/fallback.py`, `brute/api/service_v011.py` | v0.1.1 learner and API 1.1 (study-003 freeze) |
| `brute/active.py`, `brute/api/service_v020.py`, `brute/release_version.py` | v0.2.0 learner and API 1.2 (study-004 freeze) |
| `brute/changepoint.py`, `brute/api/service_v030.py`, `brute/release_version_030.py` | v0.3.0 learner and API 1.3 (study-005 freeze) |
| `brute/resume.py`, `brute/geometry.py`, `brute/api/service_v040.py`, `brute/release_version_040.py` | v0.4.0 learner (A4/P4, D2/F2 candidates), constraint region and API 1.4 (study-006 freeze) |
| `brute/region.py`, `brute/region_learner.py`, `brute/breadth.py`, `brute/api/service_v050.py`, `brute/release_version_050.py` | v0.5.0 SAT region backend (A5/M5), breadth learner (B5/BM5/BP5) and API 1.5 (study-007 freeze) |
| `brute/driftsound.py`, `brute/xcheck_sat.py`, `brute/modelcount.py`, `brute/release_version_060.py` | v0.6.0 research arms R6/C6 (BR6/BC6), second SAT encoding (CaDiCaL), model counting (study-008 freeze) |
| `experiments/BRUTE_PLAN_008.json` | The study-008 pre-registration (`89c2d3b`, [readable](docs/research/v0.6.0/PLAN_008.md)); `BRUTE_SOURCE_FREEZE_008.json` and `BRUTE_RELEASE_FREEZE_060.json` lock v0.6.0 code |
| `results/study-008/` | Sealed traces (gzip), seal, seed check, second-implementation count (same author), B5 enumeration, partial xcheck report (46/288, D21/D22) and its raw checkpoint, model counts, gates, GT1, paired analysis, reproducibility |
| `experiments/BRUTE_PLAN_007.json` | The study-007 pre-registration (`5be08aa`); `BRUTE_SOURCE_FREEZE_007.json` and `BRUTE_RELEASE_FREEZE_050.json` lock v0.5.0 code |
| `results/study-007/` | Sealed traces (gzip), seal, calibration (τ7), scaling (GR2′), second-implementation count (same author), post-hoc probability recompute, gates, paired analysis, reproducibility |
| `experiments/BRUTE_PLAN_006.json` | The study-006 pre-registration (`5fa3628`); `BRUTE_SOURCE_FREEZE_006.json` and `BRUTE_RELEASE_FREEZE_040.json` lock v0.4.0 code |
| `results/study-006/` | Sealed traces (gzip), seal, calibration, second-implementation count (same author), GR1/GR1b exactness, GR2 scaling, gates, paired analysis, reproducibility |
| `experiments/BRUTE_PLAN_005.json` | The study-005 pre-registration (`25fa47b`); `BRUTE_SOURCE_FREEZE_005.json` and `BRUTE_RELEASE_FREEZE_030.json` lock v0.3.0 code |
| `results/study-005/` | Sealed traces (gzip), seal, calibration check, second-implementation audit (same author), gates, paired analysis, reproducibility |
| `experiments/BRUTE_PLAN_004.json` | The study-004 pre-registration (`c0ac594`); `BRUTE_SOURCE_FREEZE_004.json` and `BRUTE_RELEASE_FREEZE_020.json` lock v0.2.0 code |
| `results/study-004/` | Sealed traces (gzip), seal, calibration check, second-implementation audit (same author), gates, paired analysis, reproducibility |
| `experiments/BRUTE_PLAN_003.json` | The study-003 pre-registration; `BRUTE_SOURCE_FREEZE_003.json` and `BRUTE_RELEASE_FREEZE_011.json` lock v0.1.1 code. Earlier plans and locks are kept |
| `results/study-003/` | Sealed results, calibration check, second-implementation audit (same author), gates, paired analysis, reproducibility, witness audit, drift stress |
| `results/study-002/` | Sealed results, calibration, audit, gates, paired analysis, reproducibility, API replay, exploratory |
| `results/study-001/`, `bgr*/` | Inherited BGR v0.90 evidence and code, byte-identical |
| `results/RESEARCH_LEDGER.jsonl` | Local unsigned SHA chain of research events |
| `docs/research/` | Inherited research record, [`BRUTE_DEVIATIONS_002.md`](docs/research/BRUTE_DEVIATIONS_002.md), [`BRUTE_DEVIATIONS_003.md`](docs/research/BRUTE_DEVIATIONS_003.md), [`BRUTE_DEVIATIONS_004.md`](docs/research/BRUTE_DEVIATIONS_004.md), [`BRUTE_DEVIATIONS_005.md`](docs/research/BRUTE_DEVIATIONS_005.md), [`BRUTE_DEVIATIONS_006.md`](docs/research/BRUTE_DEVIATIONS_006.md), [`BRUTE_DEVIATIONS_007.md`](docs/research/BRUTE_DEVIATIONS_007.md), [v0.4.0 errata](docs/research/v0.4.0/ERRATA.md), [`DISCOVERIES.md`](docs/research/DISCOVERIES.md) |

## Credit and provenance

Brute is derived from BGR v0.90.0 (Bitwork Geometric Reasoning). The original README, CHANGELOG, RELEASE.json, and NEXT_ITERATION are preserved under [`docs/research/bgr-v0.90.0/`](docs/research/bgr-v0.90.0/). Study-001 results and ledger entries are unchanged.
