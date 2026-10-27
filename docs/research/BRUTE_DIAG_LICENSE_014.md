# Exploratory diagnostic before v0.12.0: which transfer license survives out of bank?

**Label: Observed on SEEN data.** This is exploratory and was run before BRUTE_PLAN_014 existed. It re-reads the
sealed, already-scored study-013 transfer traces (288 target cases) and the 96 seen study-013 source libraries. It is
**not v0.12.0 evidence**. Its only role is to choose what v0.12.0 pre-registers, and v0.12.0 then tests that choice on
fresh seeds. Script: `scripts/diag_license_014.py`. Output: `results/diag-014/LICENSE_DIAG_SEEN.json` (75 s wall).

## Arms (decisions use learner-visible trace fields only)

| arm | rule |
|---|---|
| AT6 | frozen v0.11.0 AT: library alive and unanimous on c, c in SP8 support, after burn-in, at least 6 confirmations |
| BKu | bank unanimity: the union of the libraries of all 4 families (p) or of the 3 other families (n) |
| DL0 / DL1 | **bounded-region license**: AT's library condition with M = 0, AND the projection of the next code over every complete Moore machine with at most n_L + m states that is consistent with the target evidence (`RegionSpace(n_L+m)`; UNKNOWN counts as possible) is exactly {c} |
| BR1 | ablation: DL1 without the library-unanimity condition (n_L still comes from the library) |

## Results (S = SP8 first-certificate step minus the arm's first-certificate step; censor at 45)

| arm | false certs (p) | mean S (p) | false certs (n) | cases with false (n) | mean S (n) |
|---|---|---|---|---|---|
| AT6 | 0 | 6.64 | 3 | 1 | 0.02 |
| BKu | 0 | 20.64 | **537** | **152** | 13.52 |
| DL0 | 0 | 17.14 | 9 | 3 | 0.96 |
| **DL1** | **0** | **11.12** (241 helped, 0 hurt) | **0** | 0 | 0.15 |
| BR1 | 0 | 11.12 | 142 | 48 | 8.55 |

**Aliasing stress.** We tried all 20,736 (target case, wrong-family library at any of 24 offsets) pairs. AT6 licensed at
least one transfer in 600 of them, and in 480 of those 600 pairs it issued false certificates (**1,080 false**). On the
same 600 pairs DL1 issued **0 false** certificates while still making 2,832 transfer certificates. Over all 20,736 pairs
DL1 issued 0 false, including the 1,728 pairs where the target had more than n_L + 1 states, which is outside DL1's Exact
guarantee. DL0 issued 3,216 false in 1,128 pairs.

The stress pairs by (target from library) were ood4 from cycle3: 240, cycle3 from ood4: 192, switch3 from unaliased2:
72, unaliased2 from switch3: 72, and switch3 from cycle3: 24.

## What it means

- **Rejected (on seen data):** bank unanimity as a license. Out of bank it fails badly (537 false certificates).
- **Exact (lemma):** if the target has at most n_L + 1 states, DL1 never issues a false certificate. The bounded region
  contains the true machine, so a singleton projection is the true next code. UNKNOWN codes are counted as possible,
  which is conservative.
- **Observed (seen):** with margin 1, DL1 is sound in-bank, out-of-bank and under aliasing stress, and it gives a speedup
  of 11.12 steps. That is larger than AT6's 6.64.
- **Important disclosure (Observed, seen):** in the positive arm, BR1p equals DL1p exactly. On these traces the library's
  hypotheses add nothing beyond the **state-count prior** n_L. The library's tracking condition acts only as a **veto**:
  it is what keeps DL1n sound when n_L + 1 is below the true size (BR1n has 142 false certificates). So the "transfer"
  carried by DL1 is mostly a size bound plus a veto. It is not content-level transfer, and v0.12.0 must report it that
  way. BR1 is pre-registered as a reported ablation.
- **Margin 0 is not enough:** 9 false in DL0n and 3,216 false under stress.

## Heartbeat gaps in study 013 (G_HB background)

860 beats. Two gaps were over 10 s: **334.5 s and 93.8 s**. In both, the CLOCK_MONOTONIC gap equals the wall gap, so a
clock jump is ruled out (**Observed**). The watchdog process was not running during those gaps. Each beat did a write,
an fsync and /proc reads.

/proc/pressure/io on this box shows about 304 s of cumulative "full" stall, which is consistent with blocking I/O
(**Inferred**). Raising scheduling priority is unavailable because we run as uid 1000. Whether the cause was an fsync
stall or the host descheduling the VM is **Open**.

The v0.12.0 fix, `watchdog_014`, makes these changes:
- no per-beat fsync
- a background fsync thread
- a separate deadline/kill thread that does no disk I/O
- per beat it records CLOCK_BOOTTIME, CLOCK_MONOTONIC, process CPU time and the PSI io totals, so the next gap can be
  attributed
