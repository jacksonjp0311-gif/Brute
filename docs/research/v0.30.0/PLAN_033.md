# PLAN_033: v0.30.0, active experiments (plan only)

Status: **preregistered (plan only; no build authorized, no code, no data)**. Study BRUTE-0300-ACTIVE-EXPERIMENTS-033. Parent: BRUTE-0290-ROBUST-PERCEPTION-032. Roadmap phase 4.

## Question
Can Brute pick its own actions to tell apart the machines that a passive trace cannot (active experiments, roadmap phase 4), so that 12-state worlds are exactly identified, soundly, where passive search leaves them ambiguous?

## Why
Studies 031 and 032 (Observed). In 031 the identify probe on S6 at 12 states gave ID 0/12, AMB 11/12 [0.646, 0.985], IDU 0/12, WRONG 0/12. S1 gave ID 0/12 at 12 states and 4/12 at 8 states. Inferred: the 176-step passive trace never exercises some truth transitions, so two or more non-isomorphic machines stay consistent. In 032, X_inf at noisy 12 states was 0/12 for every arm (S7, S7_contra, S5, S1). Better search on a fixed passive trace has not identified any 12-state world. The remaining lever is the data itself.

## Arms
- **A8**: active: the same seeded passive 176-step prefix as every arm, then up to K = 64 extra actions chosen by Brute. Each round: (1) exact SAT search (S5 encoding, symmetry-free) for a least consistent machine M1, then a second consistent machine M2 not isomorphic to M1 (the 031 blocking clause); if none, stop with ID or WRONG; (2) BFS the product of M1 and M2 from their current states for the shortest input word w on which their output sequences differ (exists because they are non-isomorphic and minimal; else stop and report); (3) execute w on the world through the step-only wrapper, append the real readings, repeat until a single class remains or K is spent. Sound by construction: a model is eliminated only by real observations, and every final certificate is the S5 certificate on the extended trace
- **A8_random**: descriptive control for chosen vs more data: the same passive prefix plus exactly the number of extra actions A8 used on that seed (capped at K), drawn from the seeded random policy; then the same identify probe
- **S5**: passive v0.27.0 arm with the 031 identify probe on the 176-step trace, unchanged
- **S1**: passive baseline with the identify probe, unchanged (comparator)

World access: a step-only wrapper over experiments/worlds_026.py: reset(seed) then step(action) -> reading; arms never see latent state, transitions or the true machine; the truth is used only by the scorer.

Labels: per case, as in 031: ID (exactly one class, equal to truth), AMB (two or more non-isomorphic consistent machines remain), WRONG (single class not equal to truth: a soundness failure), IDU (budget ran out). A8 also records rounds, extra actions used, and each distinguishing word.

Budget: experiment plus identify budget 120 s per case, the same for every arm; 10 s per SAT query hard cap; K = 64 extra actions; eps 0 (noise is out of scope here). Soundness: every distinguishing word is rechecked by simulation of M1 and M2 (outputs must differ), and the true machine is rechecked to stay consistent with the extended trace after every round.

## Seeds (fresh, 99x0001)
scale8 9910001-9910012, scale12 9920001-9920012, scale16 9930001-9930006 (informational), control 9940001-9940006, smoke 9990001-9990030; all eps 0. Drawn only after a ledgered seedcheck_033.

## Gates
- GAE8 (headline): a) WRONG = 0 for every arm on every case; b) ID(A8, scale12) - ID(S5, scale12) >= +0.33 (4/12), paired seed-bootstrap 95% CI lower bound > 0; c) ID(A8, scale12) >= 6/12; d) IDU(A8, scale12) <= 2/12 (so an ID shortfall is not just budget).
- GCH8: ID(A8, scale12) - ID(A8_random, scale12) >= +0.17, paired CI lower bound > 0 (chosen data beats more data).
- G_sound: every distinguishing word rechecked (M1 and M2 outputs differ); truth consistent with every extended trace; 0 failures.
- G10: controls: ID 6/6 for A8 and S5. GS_ref: exact reference on A8 (scale8): 0 label mismatches, mutation detection 20/20. GQB8: A8 max SAT query <= 10.5 s. G_RT: whole run <= 1800 s. G_recount, GTI and G_PROC as in 032.
- Informational: ID/AMB at scale8 and scale16; extra actions used per ID; rounds; A8 vs S1; reported, not gated.

## Failure
any GAE8 clause failing, GCH8 or G_sound failing, any WRONG label; failures are published, not tuned.

## Limits
- noise-free only (eps 0); active experiments on noisy worlds are not tested
- K = 64 and the 120 s budget are fixed in advance and not tuned
- the shortest distinguishing word for one pair is greedy, not an optimal experiment design over all surviving models
- A8_random matches A8's action count per seed, so it inherits A8's stopping time
- one world family (worlds_026), one hardware profile, one author; no independent replication
- 16-state identification is informational only

No build until a ledgered build_authorization_033.
