# Deviation #115: spec readings and small process notes before any v0.21.0 run (v0.21.0)

Label: **Exact** for what was done; the readings themselves are disclosed choices, not results.

1. **"Planned-horizon LR threshold" (BRUTE_PLAN_024 method.definition).** The plan does not name the function. It is read
   as the planned-count threshold of study-023's RGNB4, `brute.seqmargin.boundary(B_k, eps_bar, delta_k)` with
   B_k = 2·H_k, applied as a running maximum M(i) and combined with the unchanged RGL4 witness part (delta_L = 0.005).
   delta_k = (delta/2)/((k+1)(k+2)). Fixed in docs/research/v0.21.0/STITCHED_LEMMA_024.md before any RGL5 code.
   "A certificate is kept only while every later epoch's test also holds" is met because the support at every step is
   recomputed under the current (never smaller) bound; nothing is cached across epochs.
2. **GLS (e).** RGL5 differs from RGL4 on steps 1-28 by construction (its bound uses delta_0 = 1/400 at B = 56, not m_a).
   The plan's "or a pre-declared bound" branch is taken: e1-e3 in STITCHED_LEMMA_024.md, declared before any code.
3. **Smoke seeds.** BRUTE_PLAN_024 lists no smoke range. 9090001-9090030 were declared in STITCHED_LEMMA_024.md and are
   checked disjoint from every plan's held-out ranges by scripts/check_seeds_024.py (seedcheck_024).
4. **Flip array tag.** noise_model is "as BRUTE_PLAN_023", so the tag-23 flip generator is reused unchanged (new seeds give
   new flips). The frozen v0200_reference audit reads the same generator.
5. **Process slip (minor).** Two `git add` commands (authorization and lemma staging) ran without
   `env -u GITHUB_TOKEN -u GH_TOKEN`. `git add` is local and does not authenticate; every commit and push went through the
   env-stripped helper. Fixed from then on.
6. **Stress size.** check_seeds_024 counts stress as first quarter per family (30), as BRUTE_PLAN_024 cases.stress fixes.
