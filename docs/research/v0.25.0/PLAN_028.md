# PLAN 028: v0.25.0, bounding the solver cost per step (plan only)

Study `BRUTE-0250-SOLVER-COST-028`. Parent: v0.24.0 (`BRUTE-0240-SCALE-REPLAY-027`). Status: **pre-registered. No build is authorized, and there is no code or data yet.**

## Why (Inferred from Observed `DIAGNOSIS_027`)

At 12-16 states, more than 99% of S2's unknowns are queries never run before the arm deadline. Solver UNKNOWNs are at most 0.4%.

- Single support calls overrun the 10 s budget: the per-case maximum averages 13-19 s, and the largest was 48 s.
- S2 makes only 1.3-1.5 steps per second, so no arm finishes 176 steps.
- The proven lower bound n_lo stalls below n.
- Capping the search at the true state count (S2_tight) did not help at 12 states (0/12). The bottleneck there is **solver cost per step**, not the search cap. At 8 states, the cap does matter.

## What S3 changes (new file `brute/scalesearch3.py`; S2 stays frozen)

1. A hard per-query budget: solve in conflict chunks of about 2000, with a time check between chunks. No threads and no child processes.
2. A deadline on the support chain.
3. n_lo deepening moves off each observe step. It runs only in identify, or from cheap bounds.
4. Informational per-phase timing (chain, solve, feasible).

S3_tight (n_max = n) is informational and not gated. S2 and S1 are frozen controls.

## Cases

The ranges are fresh and are drawn only after a ledgered `seedcheck_028`:

| Group | Seeds |
| --- | --- |
| scale8 | 9410001-012 |
| scale12 | 9420001-012 |
| scale16 | 9430001-012 |
| control | 9440001-006 |

There are 42 main cases at eps 0 and 9 stress cases at eps 0.05, which count toward F only. That is 51 in total, run on 8 workers within a 30 min cap (about 1000 s estimated).

## Criteria (locked before data)

- **GQB_budget:** the S3 maximum single query is at most 10.5 s on every main case.
- **GSC3 a:** 0 mismatches against exact truth.
- **GSC3 b:** U(S3, scale12) <= U(S2, scale12) - 0.15, paired over seeds, with a bootstrap CI that excludes 0.
- **GSC3 c:** X(S3, scale12) >= 3/12.
- **GSC3 d:** F = 0 on main and stress.
- **GSC3 e:** ID and certificates are reported per state count (descriptive).
- **Other gates:** G10, GAPI13, GS_ref13, GTI, G_PROC, G_RT and G_recount.

## Failure rules

On a reboot, seal what is there, fail the gates and do not relaunch. The resume clause is not approved. All failures are published.
