# BRUTE deviations 019, addendum 1

Study BRUTE-0170-SEQUENTIAL-MARGIN-019. Written before the source freeze and before any held-out case was run. Every
observation here is from smoke seeds (8590001-030) only. No criterion, threshold, seed range, arm or metric changes.

## #102 Implementation: the recorded per-step bound after a contradiction

**What happened (Observed, smoke dry run 2026-10-27 11:37 EDT).** The SMOKE=1 orchestrator dry run stopped its transfer
stream on smoke stress case cycle3 / 8590002 / eps 0.05 with `VerificationError: RGNB4 per-step bound`. The region was
contradicted (no machine with <= 4 states fits within the bound) at step 43. A contradicted or budget-exhausted region
space is sticky (#101): `observe` returns without rebuilding. Because of that, `SeqMarginRegionSpace.m_bound` keeps the
value from the last build. At step 44 the space reported m = 4, but the plan bound bd[b_44] = 5.

**Change (in files that are not ledger-hashed and not frozen; `brute/seqmargin.py` is unchanged).**
1. `experiments/brute_study_019.py` gains `plan_bound(r, bd, bits, T)`. It checks that the solver's m equals bd[bits[i]]
   on every step whose space was still live (every earlier status was `supported`), and it records bd[bits[i]] at every
   step. This is the bound the plan defines and the bound the second implementation (`experiments/v0170_reference.py`,
   unchanged) already expects. It is used for RGNB4 and RGNB4_3.
2. `brute/api/certify7.py` reports the same plan bound (bd at the observed-bit count of readings 0..t-1) rather than the
   space's `m_bound`. Supports, certificates and status are unchanged.
3. `tests/test_study_0170.py::test_bound_after_contradiction` pins the case. It also checks that certify7 equals the
   runner there.

**Effect.** None on any certificate (Exact): a contradicted or exhausted step has support None and certifies nothing.
Before this change the runner refused such a case. After it, such cases are recorded. They can occur at eps 0.05 (stress,
ungated) and, rarely, at eps 0.02 when flips exceed the boundary.
