# Brute v0.14.0 → v0.15.0: next iteration (proposal; to be pre-registered as BRUTE_PLAN_017 on `plan/v0.15.0`)

The previous note is in `docs/research/v0.14.0/NEXT_ITERATION_FROM_v0.13.0.md`. Labels are as in the README. Nothing here counts as evidence until it runs on fresh seeds. The longer path is in `docs/ROADMAP_TO_GI.md`.

## Where v0.14.0 leaves things (Observed, study-016, 11 of 14 gated pass)

- **Deferring the region split works.** RSXL4 issued 0 false in 14,491 certificates, matched RG4's first-certificate time on all 360 cases (Exact by construction, confirmed) and raised coverage by 0.049 [0.041, 0.057] (GDS PASS).
- **The library license fails in one known way.** Every false DLF / RSXL certificate in studies 015–016 (2 cases, 6 certificates) and all 48 stress false certificates were on pairs whose license bound n_L + 1 was below the target's true size. Inside the guarantee: 0 false.
- **A 4-state bound on a 5-state world is unsound** (RG4 155 false on ood5); RG5 is sound but slow.
- **One 285 s whole-box pause failed G_HB.** No stream was affected.

## Recommendation for v0.15.0 (Inferred)

1. **Bound-attested license (headline).** License a library answer only when the library's bound n_L + 1 is at least the caller-attested family bound FB; otherwise certify with RG4. Inside the attestation this is sound (*Exact* lemma). The gate checks 0 false on every wrong-family arm and on all stress pairs, on fresh seeds with ood4 doubled, and reports the speed it gives up (expected on unaliased2 targets, where DLFp's gain lived).
2. **Replicate GDS on fresh seeds** with the bound-attested license on the deferred-split trajectory (RSXLa): dC ≥ 0.03 over RG4, CI lower > 0, 0 false.
3. **Attested-bound ood5.** Report RG5 / RSXL5 on ood5 with FB = 5 attested.
4. **Heartbeat robustness.** Keep G_HB as is; add a per-beat record of every worker's CPU time so a whole-box pause can be told apart from a stall, and run the operator wait on a live process.
5. **Declare K_0130 / K_0140** in advance.

Deferred and still **Open**: sub-machine concepts, stochastic worlds, grounding beyond templates, and independent audit.

Nothing here shows general intelligence.
