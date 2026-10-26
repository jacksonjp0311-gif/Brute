# BRUTE_PLAN_013 (v0.11.0): sound transfer (readable summary; the JSON wins)

Study `BRUTE-0110-SOUND-TRANSFER-013`, parent study-012. Frozen in experiments/BRUTE_PLAN_013.json before any v0.11.0 code.

**Headline gate GST.** Sound transfer means that at least one mechanism, AT or LX, meets all three conditions:
- its positive and wrong-family arms issue 0 false certificates;
- the wrong-family arm gives no significant help (CI lower bound <= 0);
- the positive arm gives a significant speedup (mean S >= 1 step, CI lower bound > 0).

**Arms on 288 transfer targets** (4 families x 24 seeds x 3 masks; positive and wrong-family library per target):

| arm | rule | soundness | speedup |
|---|---|---|---|
| DR | dual region: certify only if SP8 certifies and the library is refuted or forces the same code | Exact subset of SP8 | <= 0 by construction |
| AT | v0.10.0 transfer rule, allowed only after M_app = 6 confirmed informative library predictions | empirical (Open) | Inferred from seen data |
| LX | the library chooses the action; SP8 certifies unchanged | inherits SP8 | Open |
| TR, AT4 | v0.10.0 rule (M = 0) and AT with M = 4 | reported only | reported only |

**Other blocks.**
- **2x2:** 792 cases, unchanged arms. G6b is gated on SP8 only; window hulls are off G6b.
- **big78:** SP8_78 only, 288 cases. G78 needs 0 false certificates and at least 150 certificates (rule of three <= 0.02).
- **GTI:** declares K_080 and K_090 in advance.
- **GAPI:** a new host-agnostic interface, `brute/api/certify.py` (observations in, certified code or UNKNOWN out), with a test.

**Stop rule.** 2 h cap with a watchdog, and stream budgets set in `stop_rule`. Deviations start at #52.
