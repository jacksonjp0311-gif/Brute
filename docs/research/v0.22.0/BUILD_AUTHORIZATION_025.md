# Build authorisation: BRUTE-0220-BETTING-CS-025

- **Owner:** James, card t128s531, 2026-10-29 23:35 EDT (America/New_York), relayed by the coordinating agent.
- **Question / answer:** "How should I build v0.22.0?" / "Revise v0.22.0 to keep the stress gate strict, then build, run and release it".
- **Context (relayed):** James first picked "as planned", then asked for an opinion, and switched to this option.
- **Scope:** first a superseding plan amendment (`experiments/BRUTE_PLAN_025_A1.json`, `docs/research/v0.22.0/AMENDMENT_025_A1.md`)
  that restores the stress false-certificate clause as a STRICT gate (0 false certificates on all stress cases, including
  eps above eps_bar), committed and ledgered before any build work or data. Everything else in the frozen plan
  `experiments/BRUTE_PLAN_025.json` (plan commit `4f6c4dd`, ledger `2e4168f`) is kept, including the monotonic-clock G_HB.
  Then build, run and release v0.22.0 under the full discipline, and pre-register v0.23.0 as a plan only (build NOT authorised).
- The frozen plan files are not edited. This file and ledger entry `build_authorization_025` supersede the plan's
  `build_status` text.
- Ledger time is taken from the clock (`date -Iseconds`), not typed.
