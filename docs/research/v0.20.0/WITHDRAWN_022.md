# WITHDRAWN: BRUTE-0200-FLAT-ANYTIME-022

Status: **WITHDRAWN before build** on 2026-10-28, owner request (James, card t125s484, 17:56 EDT):
"Drop the current v0.20.0 plan and design a stronger one first."

Withdrawn files (frozen, left byte-identical, not edited): `experiments/BRUTE_PLAN_022.json`,
`experiments/BRUTE_PLAN_FREEZE_022.json`, `docs/research/v0.20.0/PLAN_022.md` (plan commit 7869317, ledger bd4e16d).
No v0.20.0 code was written, no held-out seed in the 022 ranges was generated, nothing was run. Study 022 is void;
its seed ranges are retired and will not be reused.

## Reason

The plan's only lever was the crossing-budget schedule of the anytime margin (RGNA5, w(b) ∝ 1/(b ln²(b+1))).
A scratch check (Simulated; exact-rational DP, eps_bar 0.02, delta 0.01; scratch deleted, nothing committed) gave:

| bit | 1 | 5 | 10 | 20 | 28 | 40 | 56 | 88 | 120 | 176 |
|---|---|---|---|---|---|---|---|---|---|---|
| S5 (RGNA5) margin | 1 | 1 | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 13 |
| RGNA4 margin | 1 | 1 | 2 | 3 | 4 | 5 | 7 | 9 | 11 | 13 |

Total crossed probability 0.00943. The flat schedule moves the margin by at most 1 flip, at three of ten bits, and not at
all at the horizon. RGNB4 (planned horizon, m = 9 at bit 176) was 0.493 C_late at eps 0.02 against RGNA4 0.265, so a
1-flip shift is expected to give a small dC_late (Inferred) — a tweak, not a Phase 1 step. Gate GAS_flat (c)/(d) would
at best pass on a marginal gain. The plan is withdrawn openly rather than run.

Replacement: a stronger v0.20.0 design is pre-registered separately (see `docs/research/v0.20.0/` and the ledger).
