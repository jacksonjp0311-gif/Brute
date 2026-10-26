# Plan 012 (v0.10.0), readable summary

`experiments/BRUTE_PLAN_012.json` is authoritative and wins on any difference. The study id is
BRUTE-0100-SUPPORT-TRANSFER-012.

## The three tracks

**J10 (2x2 block, 792 cases).** J10 is SP8 with one extra check: each certificate is kept only if the **exact
jump-window support** supW4 is that single code. J9 used a fibre hull for this check. The gates are G1, G2,
G3L, G3′, G6b, GH and **GJ10**, where GJ10 requires J10 to beat J9 on coverage with a paired CI. GA1_012 and
G6b are predicted to FAIL (H_gap): J10 is not expected to reach SP8-level coverage.

**7–8 states (big78, 144 cases).** This block runs on random 7- and 8-state Moore machines with a state bound of
8 (margin 9). The arms are J10_78 and SP8_78. Its gates are G78_soundness (0 false certificates) and
G78_containment.

**Transfer / abstraction (288 target cases, 96 source worlds).** Brute learns minimal whole-machine motifs from
one fully observed source world. The motif is abstract: it does not fix state labels, action labels or emission
codes. Each motif is expanded into the relabelled hypotheses, which the target's observations then filter. TR
certifies only when every survivor agrees **and** SP8's published support contains the agreed code. The pairs
are:

- **Positive:** a source from the same family as the target.
- **Negative control:** a source from a rotated, unrelated family.

The transfer gates are:

- **GT_a:** 0 false certificates.
- **GT_b:** the mean step saving is ≥ 1 and its CI lower bound is > 0.
- **GT_c:** the negative control has 0 false certificates and its CI lower bound is ≤ 0, meaning it gives no
  significant help.
- **GT_ref:** the second implementation reproduces every transfer decision.

## Process

The g11 optional phase is now a **fixed list of 54 cases**, stamped `optional_done` or `stopped_own_budget`. The
cap is ≤ 2 h, enforced by the watchdog. Seeds are 5010001–5190030, all fresh.
