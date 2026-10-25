# Brute v0.6.0: pre-registered plan for study-008 (BRUTE-060-DRIFTSOUND-008)

**Status:** pre-registered. No v0.6.0 code, world, seed or run exists at the freeze commit.
The binding text is `experiments/BRUTE_PLAN_008.json`. If this page and the JSON differ, the JSON wins.
The ledger entry `preregistration_008` records the JSON's sha256. Every prediction below is **Inferred**.

## Targets and hypotheses

| Target | Hypothesis (short) | Gate |
|---|---|---|
| (a) drift-sound certification | One rule passes G1, G2, G3′ and G6b on the same held-out run | **GA1** (conjunction) |
| (b) breadth exactness without enumeration | An independent SAT encoding on CaDiCaL re-derives every breadth decision. Uniqueness is proved by UNSAT, and abstentions are witnessed by replayed counter-models. | **GX2′** |
| (c) v0.5.0 tamper-case defect | A new verify_release_060 turns every parse failure into a VerificationError. The frozen 050 files are untouched. | **GT1** |
| (d) exact model counting | The region size \|R_t\| is counted exactly within budget on ≥95% of sampled steps | **GMC** (separately gated) |

## Arms
- **R6, recency-opened edges.** Starts from A5 (Y1k). If a residual surprise > τ/2 or a window event happened within the last 8 steps, every edge confirmed only before that event is treated as unknown in the Y1k check. It targets G3′.
- **C6, coverage-tracked.** Certifies when Y1k certifies. It also certifies on the v0.2.0 tracked-state projection when the session has never had a surprise > τ/2, a window event or a contradiction. It targets G6b.
- **Frozen controls:** A5 (v0.5.0), A4 (v0.90 control source), A2 (G6b baseline), B5 (breadth).
- **Breadth versions:** BR6 and BC6.
- **Fixed constants:** τ6 = 1.645215321642, τ7 = 2.07944154168, factor 0.5, W = 8. None of these is tuned.

## Seeds
- **2x2 held-out:**
  - cycle3 1810001–024
  - switch3 1820001–024
  - unstructured3 1830001–024
  - unaliased2 1840001–024
  - ood4 1850001–024
  - perm4 1860001–024
  - ood5 1870001–024
  - drift4 1880001–048 (doubled)
- **Breadth:**
  - big6 1910001–024
  - sens3 1920001–024
  - act3 1930001–024
  - ood6s3 1940001–024
- **Smoke:** 980001–980030 only.
- `scripts/check_seeds_008.py` asserts disjointness from each other and from every range in plans 001–007, plus 901–903 and 1591001–1591384. It is run and ledgered before any smoke run, and the runner refuses out-of-range seeds.
- Every run, smoke included, gets `run_start`/`run_end` ledger entries with the start time and the seed set.

## Gates (frozen thresholds)

| Gate | Threshold | Prediction |
|---|---|---|
| **GA1** | PASS iff ONE arm in {R6, C6} passes G1, G2, G3′ and G6b | FAIL: R6 passes G3′ and fails G6b; C6 does the reverse |
| G1 | 0 false conditional and 0 false public certificates in-family (R6, C6, B5, BR6, BC6), all steps and actions | PASS (R6); C6 Open |
| G2 | 0 false conditional certificates on ood5 (R6, C6) and on ood6s3 (B5, BR6, BC6) | PASS (R6); C6 at risk |
| G3′ | Per arm: drift4 non-drift false = 0 AND total ≤ 0.5 × v0.90 control (A4), on 144 cases | R6 PASS, C6 FAIL |
| G6b | Per arm: pooled in_family_original coverage X − A2 ≥ −0.03 AND CI lower ≥ −0.05 | R6 FAIL, C6 PASS |
| **GX2′** | 0 mismatches, 0 failed witness replays, **checked ≥ 0.99** per family (big6, sens3, act3, ood6s3) × arm (B5, BR6, BC6); 0 disagreements with enumeration where it completes. Budget: 2,000,000 conflicts per query; a step over budget is unchecked. | PASS except a risk on big6 |
| **GT1** | 4 corruption modes × every study-008 JSON, RELEASE.json, SEAL and MANIFEST → VerificationError only. A regression test confirms the frozen 050 still raises JSONDecodeError, and the 050 file hashes are unchanged. | PASS |
| **GMC** | Every 4th post-burn-in step of A5 in_family_original cases: \|R_t\| counted on **≥ 95%**, 0 disagreements with blocking-clause count where ≤ 10^4, 0 sum-consistency violations | PASS on 2x2; breadth Open |
| G4 | 0 public certificates on ood5, drift4 and ood6s3; 0 wrong public certificates; none after the first alarm | — |
| G5 | ≤ 0.05 of cases with an alarm, per arm and per in-family family | — |
| G7 | log-loss ≤ ln4 (ood5, drift4) and ≤ ln8 (ood6s3); min p ≥ eps/m | — |
| G9 | Resume only after W = 8 calm residuals; no RESYNC_AMBIGUOUS; retraction only at contradiction | — |
| G10 | All cases complete; solver_unknown forecasts ≤ 1% per block | — |
| G11 | v060_reference audit: 0 mismatching traces; mutation 20/20 | — |
| G12 | Byte-identical rerun of cases with index ≡ 0 mod 3; identical counts | — |
| G13 | Frozen controls hash-checked; τ6 and τ7 unchanged | — |

## (d) budget rule and fallback
- **Counter:** pyganak==2.8.0 does the exact projected counting. If the pinned version's guarantee is probabilistic, its counts are labelled Inferred.
- **Budget:** 10 s per count, 120 s per case and 6 h for the whole study. A count over budget is UNKNOWN and is never imputed.
- **Fallback when GMC fails or the counter is unavailable:**
  1. GMC is published as FAIL or INFEASIBLE.
  2. Region sizes come from blocking-clause counts, which are Exact up to 10^4 and censored above that.
  3. pyapproxmc==4.4.0 estimates (ε = 0.8, δ = 0.2) are labelled Inferred.
- Counts are **never** used by certification, policy or alarms.

## What counts as failure
- Any gate below its threshold is FAIL and is published verbatim everywhere.
- GA1 fails if G3′ and G6b are passed only by **different** arms.
- One family or arm short on GX2′ fails target (b).
- No reruns, re-seeding or constant changes after run_start. The only exception is an infrastructure crash, rerun with identical code and seeds and ledgered as a deviation.
- **No auto-promotion.** The default stays Y1k + LU-R whatever the outcome. A rule that passes GA1 needs an owner decision and a fresh replication before it can become the default.

## v0.5.0 defect stays recorded
`tests/test_release_050.py::test_tampered_copies_fail` fails with JSONDecodeError (`scripts/verify_release_050.py:87`). Both files are frozen in BRUTE_RELEASE_FREEZE_050 and are not edited. v0.6.0 adds new files only.

## Process order
1. Plan, then the ledger entry.
2. Seed check, then the ledger entry.
3. Second implementation.
4. Implementation, with smoke runs on 980001–030 only.
5. Source freeze.
6. Scoring scripts, committed at least 10 min before run_start.
7. nohup runs.
8. Seal.
9. Gates.
10. Release verifier, then release on owner instruction.

Pinned versions: numpy==2.5.4 and python-sat==1.9.dev17. pyganak==2.8.0 and pyapproxmc==4.4.0 are added for GMC only.
