# Study 068 smoke results, published before the main run

Written 2026-11-03 at about 11:40 EST by executor-B. This note was drafted by the agent and has not been reviewed by James.

## What was run

The smoke used seed 12680301, which the plan sets aside for smoke only. It ran before the freeze, outside results/study-068, and is never gated. Raw output is in /tmp/s68/smoke1 (scratch, not committed).

## Results

| Target | Arm | Conflict budget | Outcome |
|---|---|---|---|
| U3, U4 | C and S | 2M (smoke) | IDU, stop "unknown": the budget ran out after 202 and 216 experiments |
| W16 | C and S | 2M (smoke) | AMB, stop "K_spent": all 400 experiments used, 556k conflicts |
| U3 | C | 8M (main) | AMB, stop "K_spent": 7.44M conflicts |
| U4 | C | 8M (main) | AMB, stop "K_spent": 5.24M conflicts |

What the smoke showed:

- **n_min matched the hand truth in every case.** Each least machine had the truth's minimal size: 6, 7 and 7.
- **No arm decided.** Even with 400 experiments, a rival with at most 12 states that differs in its future from the current state was still consistent with the trace.
- **Noise was fully corrected.** The noisy arms had 0 settled-bit errors.
- **The noisy and clean arms matched.** Each noisy arm's inner record equals the clean one once wall-time fields are removed. Before that fix, wall times inside `audit.calls[].wall`, `case_wall` and `chunk_wall_max` differed. The runner's strip rule now drops every key that is `wall` or ends in `_wall`, `_walls` or `_wall_max`. This was found and fixed before the freeze.

## Prediction and decision

**Prediction (Inferred):** the main run will fail GDEC68 and GMATCH68 on at least U3 and U4, because the locked K of 400 is too small at declared N 12 for these sparse decoder machines.

**Decision:** the locked plan's caps are NOT changed. The main run goes ahead once, exactly as pre-registered, and its result is published either way. Any change to K, N or the experiment design is a new plan, drafted for v0.65.0.
