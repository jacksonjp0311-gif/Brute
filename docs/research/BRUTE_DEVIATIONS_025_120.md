# Deviation #120 (study-025, v0.22.0): pre-data notes under the lean amendment A2

Written before any held-out data. The first two items are labelled **Exact**.

1. **Bit thresholds.** "666 / 1334 bits to activate" (HN_RECOUNT_025, BETTING_LEMMA_025 §4) are the least b at which the
   lemma's sufficient upper bound (1/(1-p_j))^b reaches 800. They are not the least b at which the exact mixture wealth
   K_j(0, b) reaches 800. With zero flips, the exact first reach is 789 bits at p = 1/100 and 1581 bits at p = 1/200
   (tests/test_bettingregion_0220 asserts ≥ 666 / 1334). Both readings agree that no level can activate within 178 bits.
   The conclusion is unchanged; only the wording is clarified.
2. **HN_RECOUNT pass key.** scripts/make_gates_025.py first read `hn['passed']`, but the file stores `"PASS": true`.
   This was fixed before the source freeze and before any data. Without the fix, GBC_lemma would have failed spuriously.
3. **Lean consequences (A2, owner card t130s540).**
   - The GBC a CP95 ≤ 0.02 clause is reported, not gated, because no n below 149 can reach it.
   - G12, G_HB and G_PROC a/b are dropped.
   - GTI is reduced to the 4 v0.22.0 test modules plus one fresh-clone short verify.
   - With 20 eps-0.02 cases, every CI is wider than in study-024.
