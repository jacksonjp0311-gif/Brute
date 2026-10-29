# Build authorisation: BRUTE-0210-STITCHED-LR-024

- **Owner:** James, card t126s506, 2026-10-29 04:15 EDT (America/New_York), relayed by the coordinating agent.
- **Question / answer:** "Build and run v0.21.0?" / "Build, run and release v0.21.0".
- **Scope:** build, run and release exactly per the frozen plan `experiments/BRUTE_PLAN_024.json`
  (sha256 `40841f85d7e6f7400825ea1c728d437ae0319be34688026058b9180bba1c31a5`; plan commit `52deedb`, ledger `e34c038`) and `docs/research/v0.21.0/PLAN_024.md`.
  Then pre-register v0.22.0 as a plan only (build NOT authorised), and stop.
- The frozen plan is not edited. Its `build_status` text ("not authorized; needs a separate owner instruction") records
  the state at the plan commit. This file and ledger entry `build_authorization_024` supersede that status.
- Ledger time is taken from the clock (`date -Iseconds`, G_PROC d), not typed.
