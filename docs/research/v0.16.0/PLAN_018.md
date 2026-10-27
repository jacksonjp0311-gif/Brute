# BRUTE_PLAN_018: v0.16.0 noisy observations (study BRUTE-0160-NOISY-OBSERVATION-018)

Readable summary of `experiments/BRUTE_PLAN_018.json` (frozen by `experiments/BRUTE_PLAN_FREEZE_018.json`). **The JSON wins if they differ.** Labels: Exact / Observed / Simulated / Inferred / Rejected / Open. No v0.16.0 code, world, seed or run exists at the pre-registration commit.

## Why breadth (decision, *Inferred*)

v0.12.0–v0.15.0 refined certification speed and coverage on the same noiseless, deterministic 2-bit worlds. Every certificate so far depends on every observed bit being right: one flipped bit can remove the true machine from the region, and the region can then force a wrong reading. Robustness to observation noise comes before any wider claim, and a larger alphabet changes the size of the problem rather than its kind. Larger alphabets are deferred to v0.17.0.

## Noise model (*Simulated*)

- Each observed (unmasked) bit is flipped independently with probability eps ∈ {0, 0.01, 0.02}. The stress level is 0.05. Actions are noise-free, and the latent reading is the scoring truth.
- The caller attests eps_bar = 0.02. The stress level 0.05 lies outside that bound and carries no guarantee.

## Tolerant region RGN4(m)

- **Construction.** Take the frozen CNF region, add one flip variable per observed bit, and require sum(flips) ≤ m.
- **Choosing m.** m is the smallest value with P(Bin(B, 0.02) > m) ≤ δ = 0.01, where B is the number of observed bits (*Exact* table: B 58 → 4, 90 → 5).
- **Conditional lemma (*Exact*).** If flips ≤ m and n* ≤ 4, the region issues no false certificate.
- **Unconditional bound.** Under the model, the chance that a case has any false certificate is at most δ per case. This is *Exact* as a probability statement and *Simulated* with respect to real sensors.

## Cases and seeds

- **Main block:** 120 target seeds × eps {0, 0.01, 0.02} at mask 0.35, giving 360 cases.
- **Stress block:** the same 120 seeds at eps 0.05 (120 cases, reported only).
- **Target seeds:** 8410001–8410024 (cycle3), 8420001–8420024 (switch3), 8430001–8430024 (unaliased2) and 8440001–8440048 (ood4).
- **Smoke seeds:** 8490001–8490030.
- **Seed check (*Exact*, checked at pre-registration):** the ranges are pairwise disjoint and do not overlap any of the 178 integer ranges in PLAN.json, BRUTE_PLAN_001…017 or the extra blocks. `check_seeds_018` re-asserts this before any run.

## Arms

| Arm | Role |
| --- | --- |
| SP8 | Frozen comparator |
| RG4 | Noise-unaware baseline, expected to be unsound under noise |
| **RGN4** | Headline arm |
| RGN4_0 | m = 0; must equal RG4 |
| RGN4_or | Oracle m, reported only |

## Gates

**GNS (headline), on the 240 noisy main cases.** All three clauses must hold:

- (a) 0 false certificates on every case with flips ≤ m;
- (b) the Clopper-Pearson 95% upper bound on the case-false rate is ≤ 0.05;
- (c) mean C(RGN4) at eps 0.02 is ≥ 0.10, with seed-clustered CI lower bound > 0.05.

Predictions: (a) *Exact* PASS, (b) *Inferred* PASS, (c) *Open*.

**Other gates:**

- **GN0:** RGN4_0 = RG4.
- **GS_a6:** RG4 issues 0 false certificates at eps 0.
- **G_recount**
- **GS_ref6:** the numpy exhaustive reference finds 0 mismatches, and the mutation check catches 20/20.
- **GAPI6:** `brute.certify/6` reports probabilistic soundness.
- **G10, G12, G13**
- **GTI:** declares K_060–K_0150 and K_096.
- **G_RT**
- **G_HB:** ≤ 30 s gap (prediction *Open*).

**Release gates:** GCC and GLV `--long` (12 cases, 900 s cap).

## Fix carried from study-017: g11 rate projection (`stop_rule.g11_rate_projection`)

Study-017's audit was projected at 27.0 worker-seconds per case but measured 46.4 (1.72×). The unaliased2 cases cost about 77 s each. The audit stopped at its budget with 308 of 432 cases done, so GS_ref5 failed (*Observed*). The new rule:

1. Measure the audit cost on smoke seeds in every family × eps cell (at least 2 cases per cell, plus stress), under the same concurrency as the held-out run.
2. Project the wall time from each cell's slowest smoke case, divided by the worker count and multiplied by 1.75.
3. If the projection exceeds 0.8 of the budget, raise the budget, raise workers (≤ 8 in total) or start g11 alongside transfer, all before the source freeze. Only if none of these fits, reduce the sample by a stated rule in a pre-freeze deviation. The sample is never cut once held-out data exist.
4. If the projection cannot fit under the 7,200 s cap, the run does not start.
5. g11 writes a PROGRESS ETA every 60 s. It is a warning only, and no mid-run change is allowed.
6. The same rule applies to gti, which used 0.962 of its budget in study-017.

`scripts/rate_math_018.py` exits non-zero on any overrun, and it is part of the source freeze.

## Operator waits (`stop_rule.operator_wait`)

During the run, poll live processes with short blocking checks of at most 240 s. In study-017, both heartbeat gaps ended within about 1 s of the operator's next action after a long idle wait (*Observed* timing; the cause is *Inferred*). G_HB itself is unchanged.

## Stop rule

The cap is 2 h from RUN_T0, with at most 8 workers. At the cap, every unfinished stream is stopped and sealed as it is, with no extension and no rerun. A gate with incomplete inputs is FAIL (STUDY_BUDGET).

## Not claimed

- The noise is iid, synthetic and bit-level only.
- eps_bar and FB are attestations made by the caller.
- Soundness is probabilistic (≤ δ per case).
- Readings are 2-bit with 2 actions.
- The audit is by the same author; there is no independent audit.
- The study is not evidence of general intelligence.
- No CI workflows are used.
