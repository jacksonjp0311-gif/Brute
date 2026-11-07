# Brute v0.70.0 → v0.71.0: next iteration

Previous: v0.70.0 study-074 (NOT CERTIFIED, 13/15). certify/34h dropped the ~400-step homing batch; at N=true+3 decided 5/20 cells (KR×2, B5×2, HK×1), 0 wrong; **0 memory_cap + 15 timeout** at 420 s. Tight N 8/10. GSTEP74 passed (median C/T ≈ 0.029). Headline short by 1 cell; held-out 0/4.

## Locked for v0.71.0 (plan 075)

**Same certify/34h API; raise per-job kill 420→900 s and MAIN_CAP 3300→4800 s.** Tests whether the timeout wall (not the algorithm) stopped the remaining loose-N cells. Gate thresholds unchanged (6/20 cells, ≥3 targets, held-out ≥1). Seeds 12750101 / 12750102. Standing go t143s742, t133s553, t139s684.
