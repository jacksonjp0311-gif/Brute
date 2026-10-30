# v0.23.0 plan (BRUTE_PLAN_026, study BRUTE-0230-SCALE-026): SCALE, plan only

Pre-registered 2026-10-30 EDT under the LEAN process (owner card t130s540). No build is authorized. There is no code and no data yet.

**Question.** Does a smarter exact search (S2) keep the region exact on 8, 12 and 16 state worlds, where the frozen search (S1) is expected to run out of budget? S2 must give S1's answers wherever both finish, with 0 false certificates.

**S2 (new file `brute/scalesearch.py`).**
- Incremental SAT with assumptions.
- BFS-canonical symmetry breaking.
- Iterative state-count deepening.
- A passive state-merging witness, used only as a solver phase hint and never as a result.

**Cases, declared before the data.**
- Main: 84 cases. These are the scale8, scale12 and scale16 seeds (12 each) and the control_cycle3 seeds (6), each at eps 0 and at eps 0.02.
- Stress: 9 cases at eps 0.05.
- Total: 93 cases, on 176-step traces.
- Budgets: 10 s per exact query and 120 s per case. The main run is capped at 1800 s on 8 workers. If the cap is hit, the run seals as partial, the data gates fail, and it is never relaunched.

**Headline GSC.**
- (a) S2 == S1 on every query where both finish.
- (b) X(S2, scale12) >= X(S1, scale12) + 0.25, and X(S2, scale8) >= 0.9.
- (c) U(S2, scale16) <= 0.10.
- (d) 0 false certificates for S2 and for RGB6 on S2, on all 93 cases including stress (strict).
- (e) ID(S2, scale8, eps 0) >= 0.8.

**Other gates.**
- GS_ref12: a brute-force reference audits scale8, with a mutation test of 20/20.
- GAPI12: certify/12 adds search='s2'.
- G10: the cycle3 control.
- G_recount, GTI (lean), G_PROC (lean) and G_RT.

**Process (lean).**
- Kept: the plan locked before data, an exact recount, the strict stress gate, failures published, evidence labels, a push after each step, no force-push, and no Actions.
- Dropped: drills, the host-pause probe, the double clone, and the separate scoring-freeze wait.

**Limitations.**
- Random minimal machines are easier than adversarial ones.
- 16 states is still small.
- The same author writes S2 and its reference.
- This is not general intelligence.
