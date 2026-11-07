# Brute v0.70.0 → v0.71.0: next iteration

Previous: v0.70.0 study-074 (NOT CERTIFIED, 13/15). certify/34h dropped the ~400-step homing batch; at N=true+3 it decided 5/20 cells (KR×2, B5×2, HK×1), 0 wrong; **0 memory_cap + 15 timeout**. Tight N 8/10. GSTEP74 passed (median C/T ≈ 0.029). Headline short by 1 cell; held-out 0/4.

## Proposal for v0.71.0 (plan 075, to be locked)

**Attack the timeout wall at loose N without reintroducing the memory wall.** Evidence from 074: removing the batch replaced memory_cap with timeouts and gained +2 cells / +1 target. Decided cells finished in ~66–310 s of compute; 15 C3 cells and 2 C1 cells hit the 420 s SIGKILL with no memory_cap. Options to pre-register (choose one before data):

- **A (time):** raise per-job kill (e.g. 900 s) and keep MAIN_CAP lean by fewer parallel workers or a staged job set; same certify/34h API.
- **B (algorithm):** certify/35h — a small additive policy/encoding change aimed at finishing the remaining targets inside 420 s (must not reintroduce the homing-batch step bloat).
- **C (N ladder):** keep 420 s / 2.0 GiB and test N=true+2 as an intermediate loose rung (new gate thresholds locked before data).

Standing go: t143s742 (C-bridge, real unmodified software), t133s553 (lean), t139s684 (keep going). Prefer the smallest change that can clear GHEAD (≥6/20 cells, ≥3 targets) and ideally GHELD, with 0 wrong. Lock plan 075 BEFORE any gated data.
