# Brute v0.21.0 pre-registration: BRUTE-0210-STITCHED-LR-024 (plan only)

**Status.** Pre-registered; **build is not authorized.** The JSON plan `experiments/BRUTE_PLAN_024.json` is the binding
text. This page summarizes it. Labels: Exact / Observed / Simulated / Inferred / Rejected / Open.

- **Why (Observed, v0.20.0).**
  - The anytime likelihood-ratio bound RGL4 is sound and certified 41.7% of late slots at eps 0.02.
  - The planned-horizon RGNB4 certified 53.0%, so RGL4 trails by 11.3 points [7.3, 15.5].
  - Early coverage (steps 1-28) is about 0 for every noise-robust arm.
- **Idea (Open).** **RGL5** stitches the LR test over horizons 28·2^k and spends delta/((k+1)(k+2)) per epoch. It
  stays anytime-valid by a union bound; an exact lemma and a DP reference come first.
- **Headline gate GLS.**
  - (a) 0 false certificates on noisy main cases, with CP95 ≤ 0.02.
  - (b) 0 false certificates on stress.
  - (c) dC_late against RGL4 ≥ +0.04, CI lower bound > 0.
  - (d) dC_late against RGNB4 CI lower bound > -0.06.
  - (e) The early prefix is unchanged.
- **Process gate G_PROC (lessons of #111-#114).**
  - The launcher refuses dry-run hooks.
  - The orchestrator logs its resolved directory.
  - Git-order inputs come from a tracked file written before the freeze, so the git-archive clean clone works.
  - Ledger times come from the clock.
- **Carried gates.** Everything from v0.20.0. G_HB stays at 10 s, with a host-pause probe reported beside it.
- **Size.** 360 main + 30 stress cases, plus a 60-case reproset, on fresh reserved seed ranges, drawn only after
  seedcheck_024.
- **Not in scope.** Code, seed draws or runs. Those need a new owner instruction.
