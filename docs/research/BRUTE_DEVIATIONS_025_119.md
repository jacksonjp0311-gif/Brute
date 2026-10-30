# Deviation #119: spec readings and small process notes before any v0.22.0 run (v0.22.0)

Label: **Exact** for what was done; the readings themselves are disclosed choices, not results.

1. **RGB6 definition (BRUTE_PLAN_025 method.definition).** The plan feeds the betting confidence sequence the mismatches
   of the leading hypothesis. That count is ≤ the true flip count, so the plan's wording is unsound and is not built
   (BETTING_LEMMA_025 §1, Rejected). Built instead: the level-0 RGL4-form bound T_0 (delta_a0 = delta_L0 = 1/400) feeds a
   fixed 4-point λ-mixture betting test for each grid rate p_j ∈ {1/100, 1/200} (delta_cj = 1/800), sticky activation,
   and per-level LR offsets at delta_Lj = 1/800. "Upper end eps_hat_u" is the least active grid rate (cap eps_bar).
   The split is delta/2 for count/betting and delta/2 for LR, as the plan asks. "Predictable plug-in" is replaced by a fixed
   mixture because the per-bit flips are never observed (§1). Fixed in the lemma before any RGB6 code.
2. **Exact pre-run consequence.** With ≤ 178 observed bits no adaptive level can activate (BETTING_LEMMA_025 §4), so
   RGB6 = T_0 ≥ T_RGL4 in this study. GBC c is predicted to fail. It is published, not forced, and no threshold changes.
3. **Arms.** BRUTE_PLAN_025 lists RGB6, RGL5, RGL4, RGNB4, RGN4_or, RG4 and SP8. RGNA4, a study-024 arm, is not run. The
   case-level anytime_boundary fields (delta 0.01) stay so that the frozen v0200 common audit runs unchanged.
4. **Prefix controls.** prefix28 (RGL4) and prefix28_rgl5 are carried at eps 0.02. prefix28_rgb6 (RGB6 on the first 28
   actions) is added as the prefix-stability evidence for RGB6. GBC e is read as: RGB6 certificates in steps 1-28 that
   RGL4 does not issue at the same slot are counted, and e passes iff that count is 0 or all such certificates are true.
5. **Stress clause.** Plan amendment A1 (owner card t128s531): GBC b is strict, with 0 RGB6 false certificates on all 30
   stress cases.
6. **Smoke seeds.** BRUTE_PLAN_025 lists no smoke range. 9190001-9190030 are declared here with the study-024 layout
   (9190001-008 smoke targets, 009-012 API, 013-015 kill drill, 016-030 spare). scripts/check_seeds_025.py
   (seedcheck_025) checks they are disjoint from every plan's held-out ranges.
7. **Flip array tag.** noise_model is "as BRUTE_PLAN_024", which is "as 023", so the tag-23 generator is reused unchanged.
8. **Process slip (minor).** Five `git add` staging commands before this file ran without `env -u GITHUB_TOKEN -u GH_TOKEN`.
   `git add` is local and does not authenticate. Every commit and push went through the env-stripped helper
   `/tmp/s24/c.sh`. Fixed from here on (staging also env-stripped).
