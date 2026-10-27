# Brute v0.16.0 → v0.17.0: next iteration (pre-registered as BRUTE_PLAN_019 on `plan/v0.17.0`; ledger preregistration_019)

The previous note is in `docs/research/v0.16.0/NEXT_ITERATION_FROM_v0.15.0.md`. Labels are as in the README. Nothing here counts as evidence until it runs on fresh seeds.

## Where v0.16.0 leaves things (Observed, study-018, 10 of 12 gated pass)

- **Noise breaks the noiseless bounded region.** RG4 issued false certificates on 16/120 cases at eps 0.01 and 24/120 at eps 0.02.
- **The flip-tolerant region RGN4(m) is sound inside the attested bound.** 0 false on 240/240 noisy cases; CP95 upper bound 0.0124 (GNS a, b PASS).
- **It certifies too little.** C(RGN4) at eps 0.02 = 0.066 [0.051, 0.081] < 0.10 (GNS c FAIL); 0.058 at eps 0. The oracle margin (m = realized flips, 0 to 4 in these cases) reaches 0.316 with 0 false, so the loss is the worst-case margin m = 4 or 5 applied from the first reading.
- **GN0 failed on 2 burn-in slots** (RG4's SP8 passthrough), as #97 predicted.
- **All process gates passed**: audit 480/480 with mutation 20/20, GTI, kill drill, heartbeat (max gap 2.0 s). The rate math over-projected by 1.5–3.1x.

## What GNS clause (c) and GN0 mean

- **GNS (c)** is the usefulness half of the headline: being sound by abstaining everywhere is trivial, so the plan required RGN4 to certify on average at least 10% of the 88 (step, action) slots at eps 0.02, with the seed-clustered CI lower bound above 5%. It certified 6.6%, with a lower bound of 5.1%. The lower bound clears 5%, but the mean misses 10%.
- **GN0** is a consistency control: with the margin set to 0, the tolerant region is the same CNF as the frozen region, so on noiseless cases RGN4_0 should match RG4 slot for slot. It does after the burn-in. During the burn-in, RG4 (the frozen `rg_decide`) passes SP8 certificates through and RGN4_0 by design does not, so one case differs in 2 slots.

## Breadth or depth

v0.17.0 does both, with depth as the headline because the v0.16.0 headline failed on coverage:

1. **Depth (headline GNB): a sequential margin.** Replace the single worst-case m with a nondecreasing boundary m(b) on the number of observed bits b seen so far, built by exact alpha spending: cumulative probability, under Bin(eps_bar = 0.02), that the flip count crosses the boundary by bit b is at most delta · b / B (delta = 0.01). Because a certificate at step t depends only on readings up to t, a false certificate requires a crossing, so soundness keeps the same delta (*Exact*, lemma to be written before code). Worked boundary (*Exact*, exact rationals): B = 58 gives m = 2 from bit 2, 3 from bit 14, 4 from bit 35; B = 68 adds 5 from bit 57. The gain is expected to be modest and early only (*Inferred*); its size is *Open*.
2. **Breadth (GA3): a larger action alphabet.** 3 actions × 2-bit readings in ≤ 4-state worlds, noiseless and at eps 0.02, with RG4 and the sequential-margin arm generalised in new files; soundness gated, coverage reported.
3. **The same discipline:** seeds disjoint from every earlier range (85xxxxx), a numpy second implementation, rate math with the 1.75 factor, a source freeze, a scoring freeze ≥ 600 s before run_start, one held-out run under a 2 h cap, `brute.certify/7`.

## Fixes carried into BRUTE_PLAN_019

1. Commit the run_start ledger entry before any stream starts (the #100 item-1 dirty window), and fix the dirty-file parser that drops the first character.
2. Declare K_0160 (test_release_0160 version / API tests after the bump) in GTI.
3. Burn-in: RGN keeps burn-in 8 with no SP8 passthrough; GN0's successor compares only after the burn-in, and the full-run comparison is reported.

## No CI

Brute has no `.github` directory and uses no GitHub Actions; add no workflows.
