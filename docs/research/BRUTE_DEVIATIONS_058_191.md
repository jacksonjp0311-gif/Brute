# Deviation #191 (study-058, v0.55.0): post-run record

Written after the gates (box-local EST, UTC-5, Nov 2 2026). It changes no threshold, seed, cap or gate and no sealed output.
Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

0. **Framing (kept prominent).** This is a **target change**. certify/20b decides fresh 20-state worlds when every state emits a
   random 3- or 4-bit reading. It says nothing new about the original 2-bit problem: **2-bit readings at 20 states stay Open**
   (B2 0/12, B2R 0/12 here, as in every 050-057 study).
1. **Process (Exact).** deviation_190 (e1aeed2, ledger 60b9f86), freeze_058 (846709d, 558 files, ledger 4208e7e), main_run_058
   (ledger d8cc97e; launched once with nohup at 11:16:41 EST, pid 1832133, never relaunched), seal 8f7ff0d (SEAL.json written
   11:50:13 EST; ledger run_end_058 acb69eb), recount a1d905d, reference 36e9e1f, tests 21f6209, api_checks a33fc77, gates 3d3da7b.
2. **Time notes (Observed).** The 11:43 EST status message said the main run started 11:29; the ledger and the launch shell
   record 11:16:41 EST. The runner's total_elapsed_informational is 1236.0 s while launch-to-seal wall is about 2012 s; the
   runner field is informational only and gates nothing. ps etime on the box also read inconsistently during the run. Open: why
   the two elapsed figures differ.
3. **Result (Observed; labels from the independent recount).** B4 11/12 (9 ID, 2 IDF) Wilson 95% [0.65, 0.99]; B3 4/12 (3 ID,
   1 IDF) [0.14, 0.61]; B2R 0/12 [0.00, 0.24]; B2 0/12 [0.00, 0.24]. Exact McNemar B4 vs B2R p = 0.00098 (11/0 discordant), B3 vs
   B2R p = 0.125 (4/0). WRONG 0 of 60. The one B4 miss, 12530010, is IDU at n_min 19 after 2.0M conflicts.
4. **Margin (Observed).** Decided B4 records used 0.60-1.68M of B = 2M conflicts (B3: 1.23-1.76M). The result is budget-
   sensitive: a smaller B would decide fewer. Readings collide: B4 worlds had 10-14 distinct codes among 20 states (16 possible),
   B3 had 5-8 (8 possible); decisions do not need injective readings.
5. **Cost (Observed, informational).** Conflicts per arm: B4 14.9M, B3 22.2M, B2R 24.1M, B2 24.0M; B4 and B4_b canon58 identical
   on 12/12 (GDET58), no wall guard fired.
6. **Gates (Exact).** All 10 gated criteria pass: GS58_sound, GB_gain58, GB3_58, GDET58, GFID58, GHOST58, GS_ref (26/26 audited,
   0 mismatches, 45 s, 20/20 mutations), G_recount, GTEST, G_PROC. certified_readbits_N20 true; status phrase "certified
   (read_bits 3 and 4, N <= 20)". G_RT is checked at release (#190 item 3).
7. **Scope (Exact + Inferred).** Conditional on the declared N = 20: an ID or IDF is unique among machines with at most 20 states
   consistent with the trace. Inferred reason: a larger machine can copy the true machine on every visited state. Noise-free
   traces only; random emissions only (not adversarial or structured readings); one transition-graph family (worlds_050
   scale20); 12 seeds. Question C (read_bits 2 == certify/16e) is answered on 6 small worlds only (#190 item 4).
