# Plan amendment A1: BRUTE-0220-BETTING-CS-025 (stress gate restored to STRICT)

- **Amends:** `experiments/BRUTE_PLAN_025.json` (sha256 `d9a82d41…690f`, commit `4f6c4dd`, ledger `2e4168f`) and
  `docs/research/v0.22.0/PLAN_025.md`. Neither file is edited; this amendment and `experiments/BRUTE_PLAN_025_A1.json`
  supersede one clause.
- **Authority:** owner James, card t128s531, 2026-10-29 23:35 EDT ("Revise v0.22.0 to keep the stress gate strict, then
  build, run and release it"). Ledger `build_authorization_025`.
- **Timing (Exact):** committed and ledgered before any v0.22.0 build work, code, seed draw or data.

## The change

| clause | pre-registered (superseded) | A1 (in force) |
|---|---|---|
| GBC_headline b | 0 false on stress cases with eps <= eps_bar; stress above eps_bar reported, not gated | **0 false certificates on ALL 30 stress cases (eps 0.05), including eps above eps_bar. Strict gate**, as in study-024 GLS b |

## Reason (owner)

Not moving the goalposts right after v0.21.0 failed that exact clause. Study-024 GLS b failed on 3 RGL5 false
certificates in 1 of 30 stress cases at eps 0.05 > eps_bar (#118). Relaxing the clause in the very next plan would
read as fitting the gate to the last result. The soundness guarantee is still conditional on eps <= eps_bar; the strict
clause tests behaviour outside that condition and is kept as a gate anyway.

## Kept unchanged

Everything else in BRUTE_PLAN_025: arm RGB6 and `brute.certify/11`, the comparators, delta 0.01, eps_bar 0.02, family
bound and burn-in; GBC a, c, d, e; **G_HB on the monotonic clock** with wall-clock-only gaps reported separately; cases,
held-out ranges, stop rule, rate-math rule, release gates and process controls.
