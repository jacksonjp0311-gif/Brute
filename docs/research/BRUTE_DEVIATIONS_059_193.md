# Deviation #193 (study-059, v0.56.0): post-run record

Written after the gates (box-local EST, UTC-5, Nov 2 2026). It changes no threshold, seed, cap or gate and no sealed output.
Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

0. **Framing (kept prominent).** This is a **target change**: 4-bit random readings at 20 states, now read through iid bit noise.
   It says nothing new about the original 2-bit problem: **2-bit readings at 20 states stay Open.**
1. **Process (Exact).** deviation_192 (9088f71, ledger c950f98), freeze_059 (0b73c4f, 589 files, ledger 8390b88), main_run_059
   (ledger 5b5085c; launched once with nohup at 12:33:56 EST, pid 1874516, never relaunched), seal f507271 (SEAL.json written
   12:40 EST; ledger run_end_059 4e1fe46), recount 28f9b9b, reference ba960d1, tests 2f9283d, api_checks d3faa3f, gates b4ac3ed
   (ledgered after the fact as recount_059 137a7e8 .. gates_059 19f05b0).
2. **api_checks attempt 1 (Observed; disclosed).** The first api_checks_059 launch (about 12:43:30 EST, in the same shell call
   that started the official tests) was killed when the tool shell aborted; it wrote no output file. It was run again once at
   12:45:07 EST under nohup and passed. Nothing in the check depends on attempt count; it reads only sealed and frozen inputs.
3. **Time notes (Observed).** Runner total_elapsed_informational 385.5 s; launch-to-seal wall about 6.5 min. Smoke projected a
   worst case of 729.5 s; no cut (N59 = 12).
4. **Result (Observed; labels from the independent recount).** C4, N4_05, N4_10, N4_10b and NEG4 each decided 11/12 (all ID)
   Wilson 95% [0.65, 0.99]; WRONG 0 of 48 gated records [0.00, 0.074] and 0 of 60 overall. The one miss in every arm, 12590007,
   is IDU at n_min 19 after 2.0M conflicts. Exact McNemar N4_10 vs C4 and N4_05 vs C4: p = 1.00 (0/0 discordant).
5. **Why the arms are identical (Observed + Inferred).** Majority errors were 0 on every one of 2741 observations in each noisy arm,
   NEG4 included. With 0 majority errors the majority trace equals the clean trace, so certify/20n hands certify/20b exactly the C4
   input and every mask, round and conflict count matches C4. The noise layer is therefore tested for soundness of its repeat-read
   rule, not for any change in what the solver sees. Cost: k_max 63 (N4_05) and 81 (N4_10) reads per observation; reads 154255 and
   200685 vs 2741 for C4 (56x and 73x).
6. **Weak negative control (Observed).** NEG4 (eps 0.25 against eps_bar 0.10) had 0 majority errors at k up to 63, so it showed no
   WRONG. It does not show that violating the noise model breaks soundness at this k; that stays Open (risk stated in #192 item 11).
7. **Gates (Exact).** All 11 gated criteria pass: GS59_sound, GN_keep59, GN05_59, GMAJ59, GDET59 (12/12 identical), GFID59 (55/55
   exact), GHOST59, GS_ref (55/55 audited, 0 mismatches, 61 s, 20/20 mutations), G_recount, GTEST, G_PROC.
   certified_noisy_readbits4_N20 true; status phrase "certified (read_bits 4, iid bit noise eps <= eps_bar <= 0.15, N <= 20)".
   G_RT is checked at release.
8. **Scope (Exact + Inferred).** Conditional on the declared N = 20 and on iid bit noise with eps <= eps_bar: an ID is unique among
   machines with at most 20 states consistent with the majority trace, and the majority trace is wrong somewhere with probability
   at most delta = 0.001 (union bound, Inferred). A larger machine can copy the true machine on every visited state (Inferred).
   Random emissions only, repeat reads of an unchanged state, one transition-graph family, 12 seeds.
