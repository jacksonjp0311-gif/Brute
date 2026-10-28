# ANYTIME_LEMMA_021: the horizon-free crossing boundary (RGNA4)

Study BRUTE-0190-ANYTIME-021. Written after the plan freeze (preregistration_021) and before `brute/anytimemargin.py`,
`brute/api/certify8.py` and the study runner. Labels: Exact / Observed / Simulated / Inferred / Rejected / Open.

## Definitions
- eps_bar = 0.02, delta = 0.01, pi_u = 355/113 (a rational with pi_u > pi).
- Allowance after b observed bits: A(b) = delta * (6 / pi_u^2) * sum_{j=1..b} 1/j^2.
- Boundary m_a(0) = 0; for b >= 1, m_a(b) is the smallest integer >= m_a(b-1) such that
  crossed(b-1) + P(running flips after b bits > m_a(b) and no earlier crossing) <= A(b), under iid Bernoulli(eps_bar) flips.
  This is the dynamic program of the frozen `brute.seqmargin.boundary`, with A(b) in place of delta*b/B.

## Statements
1. **A(b) < delta for every b (Exact).** sum_{j>=1} 1/j^2 = pi^2/6 and pi_u > pi, so A(b) < delta * (6/pi^2) * (pi^2/6) = delta.
2. **The program terminates (Exact).** crossed(b-1) <= A(b-1) < A(b); taking m_a(b) = b leaves no mass above it, so the loop stops.
3. **Prefix stability, no horizon (Exact by construction).** m_a(b) depends only on b, eps_bar and delta; the boundary
   computed to length L agrees with the boundary computed to any L' > L on 0..L. No planned B is used.
4. **Crossing probability (Exact).** P(running flips ever exceed m_a(b) at some bit b) = lim crossed(b) <= lim A(b) < delta
   for eps = eps_bar; for eps <= eps_bar it is no larger (the crossing event is monotone in the flip sequence and
   Bernoulli(eps) flips are stochastically dominated by Bernoulli(eps_bar) flips; the same argument as v0.17.0 GNB).
5. **Conditional soundness (Exact; v0.17.0 lemma reused).** If the true machine has <= family_bound states and the running
   flips never exceed m_a(b), the true machine is in every support, and every RGN-rule certificate equals the noise-free
   reading. Combined with 4: P(any false RGNA4 certificate) < delta under the attested noise model.

## Pre-run disclosure: the plan's Inferred prediction for GAH (c) and (d) is contradicted by an Exact computation
The plan predicted (Inferred) that spending most of delta early would lower the early margins. Computing both boundaries
(Exact, `experiments/v0190_reference.py ref_anytime_boundary` and frozen `ref_boundary`; no held-out data used) for
B = 116 (study-020 median order of B):

| bit b | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 40 | 50 | 60 | 80 | 100 | 116 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| anytime m_a(b) | 1 | 2 | 2 | 3 | 3 | 4 | 4 | 5 | 5 | 6 | 7 | 8 | 9 | 10 |
| planned m(b), B = 116 | 2 | 2 | 3 | 3 | 3 | 3 | 4 | 4 | 4 | 5 | 5 | 6 | 6 | 7 |

- The anytime margin is smaller only for b <= 12 and larger from about b = 24 on (Exact for this B; the same pattern
  holds for B = 110 and 124).
- The reason: m(b) grows when the **marginal** allowance A(b) - A(b-1) is small. Under 1/j^2 spending that marginal is
  delta*0.61/b^2, which falls below the planned delta/B by bit 9 (Exact arithmetic).
- Supports are monotone in m. Most certifiable steps (t > burn-in 8) already have more than 12 observed bits, so on
  most steps RGNA4 supports contain the RGNB4 supports (Inferred). So clauses (c) dC_early28 > 0 and the late-coverage
  part of the plan's prediction are expected to FAIL (Inferred). Clause (d) (C_late >= 0.10) is Open.
- **No change is made** to the frozen plan, the schedule or any criterion. RGNA4 is run and scored exactly as
  pre-registered, and every failure is published. A better horizon-free schedule, whose marginal spending decays more
  slowly (for example delta*c/(b(b+1)) blocks, or doubling epochs), is a v0.20.0 question. It is not tested here.
- Cost risk (Inferred): a larger m enlarges the hypothesis region, so RGNA4 may cost more than RGNB4 per case. The
  pre-run rate math measures this on smoke seeds.
