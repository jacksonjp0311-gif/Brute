# BRUTE_PLAN_021: v0.19.0 anytime-margin study (pre-registered)

Study `BRUTE-0190-ANYTIME-021`. The JSON `experiments/BRUTE_PLAN_021.json` wins if this page differs. Plan sha256 `4054f7ccc1fe76af80381240c4a3768a99d65db1678fdeafe627d68b3cc4a845`; criteria hash `21604395d1f14bb5088d3a8588d282551e8ad0fac3688873f2cb1d87b18100bb`.

**Build status:** authorized by the owner request of 2026-10-28 14:12 EDT; the build follows this commit.

## Question
Does a horizon-free (anytime) crossing budget keep the v0.18.0 soundness and late coverage while recovering the early coverage that the planned-horizon boundary gave up (#106)? (Open)

## Anytime margin (RGNA4)

- **name**: RGNA4
- **schedule**: cumulative crossing allowance after b observed bits A(b) = delta * (6 / pi_u^2) * sum_{j=1..b} 1/j^2, pi_u = 355/113 (a rational upper bound on pi), so A(b) < delta * (6/pi^2) * (pi^2/6) = delta for every b (Exact)
- **boundary_rule**: the frozen brute.seqmargin.boundary dynamic program (exact Fractions over the binomial(eps_bar) flip path, raise m(b) until the probability of a first crossing by bit b <= A(b)) with A(b) in place of delta*b/B; eps_bar 0.02, delta 0.01
- **horizon_free**: m(b) depends only on b, eps_bar and delta (no planned B); prefix-stable: the boundary computed to any length L agrees with the boundary to L' > L on 0..L (Exact by construction; tested)
- **region**: frozen brute.seqmargin.SeqMarginRegionSpace(4, boundary, k) with the anytime boundary; certificates = the frozen RGN rule (singleton support after burn-in 8)
- **soundness_lemma**: If the true machine has <= 4 states and the running flip count never exceeds m(b), the true machine survives and every certificate equals the noise-free reading (Exact; same lemma as v0.17.0 GNB). P(any crossing) <= sum of first-crossing probabilities <= lim A(b) < delta under iid flips with eps <= eps_bar (Exact). Written as docs/research/v0.19.0/ANYTIME_LEMMA_021.md before the study code.
- **why**: v0.18.0 Exact: the planned boundary spends delta*b/B, so a longer planned horizon raises early margins (#106). The anytime schedule spends most of delta on the first bits and needs no B.

## Arms
- **RGNA4**: HEADLINE: anytime-margin region (new brute/anytimemargin.py + frozen SeqMarginRegionSpace), every case
- **RGNB4**: frozen v0.17.0 planned-horizon sequential margin boundary(B), comparator, NOISY MAIN cases only (eps 0.01, 0.02; 240)
- **RG4**: frozen noise-unaware baseline, every case (reported)
- **RGN4_or**: oracle m = realized flips (evaluator-only), every case (reported)
- **SP8**: frozen comparator, every case
- **RGNA4_bit**: per-bit certificates from RGNA4 survivors (frozen brute.perbit rule), every case (reported)
- **dropped_from_study_020**: RGN4 (fixed margin; its comparison was settled in study-020) and RGNB4 on eps-0 and stress cases: removed to fit the 2 h cap with the added RGNA4 arm (rate math, Inferred)
- **not_in_scope**: 3 actions at 88 steps (NEXT_ITERATION item 3): deferred to v0.20.0 for cost; not run, not claimed

## Gated criteria
- **GAH_anytime**: {"a": "RGNA4 0 false certificates (recorded and recomputed) on all 240 noisy main cases (eps 0.01, 0.02) over all 88 steps, unconditional (crossings included)", "b": "CP95 upper bound on the RGNA4 case-false rate over those 240 cases <= 0.05", "c": "dC_early28(RGNA4 - RGNB4) at eps 0.02: paired mean > 0 and paired 95% CI lower bound > 0", "d": "C_late(RGNA4) at eps 0.02 >= 0.10 and its 95% CI lower bound > 0.05"} Prediction: Inferred: (a, b) hold; (c) holds because A(b) >= 0.6*delta from the first bit while the planned schedule has spent only delta*28/B by bit 28; (d) holds with C_late slightly below RGNB4's (A(b) < delta*b/B near b = B)
- **GAH_prefix_control**: #106 fixed by design. On every eps-0.02 main case, the RGNA4 supports, unknown counts and certificates at steps 1-28 of the 28-action prefix run are identical to steps 1-28 of the 88-step run (Exact identity), and anytime_boundary(512)[0..L] == anytime_boundary(L) for L in {0, 28, 56, 88, 176, 511}
- **GAH_frozen_control**: same-B frozen-code check (NEXT_ITERATION 4): the 95% CI of C_early28(RGNB4) at eps 0.02 intersects the study-020 CI [0.00119, 0.004167] (inclusive)
- **GS_a9_soundness**: RGNA4 0 false at eps 0 on all 120 eps-0 main cases over 88 steps
- **G_recount**: every arm's false and certificate counts, windows and RGNA4_bit recounted from the traces; realized flips and crossings consistent
- **GS_ref9_reference_audit**: numpy second implementation (experiments/v0190_reference.py, same author, no brute import) audits all 360 main cases (supports, anytime boundary, certificates, per-bit, prefix control, summaries), 0 mismatching; mutation test 20/20
- **GAPI9**: brute/api/certify7.py byte-identical to its study-019 freeze hash; new brute/api/certify8.py: streaming (observe one reading at a time, no planned length), additive, host-agnostic (no I/O, network, threads, child processes or global state), its supports equal the RGNA4 study supports on the smoke-api cases; its tests pass inside GTI
- **G10_compute**: 480 transfer cases + 120 prefix-control records, seal complete, every trace 88 steps (28 for prefix records), unknown > 0 fraction <= 1% for every support kind
- **G12_reproducibility**: repro set main[::6] (60 cases) re-run bit-identical (scientific sha of every case equal)
- **G13_frozen_controls_reproduce**: freeze chain holds; RG4 / RGNB4 / RGN4_or certificates recomputed by the frozen rules; frozen sources unchanged
- **GTI_test_isolation**: full suite passes with declared K_0180 (test_release_0180 version / API / short verify / untampered copy, allowed only if passing on a clean worktree of tag v0.18.0); undeclared failures []
- **G_RD_resume_drill**: smoke (pre-run): SMOKE=1 orchestrator on block smoke-drill with SKIP_GTI is SIGKILLed (orchestrator and every stream process group) 45 s after start and relaunched once; PASS iff (i) every stream completes after the relaunch, (ii) the resumed transfer SCIENTIFIC cases are byte-identical per case to an uninterrupted run of the same block, (iii) RUN_STATE spent includes the pre-kill time (charged, not excused), (iv) no checkpoint key appears twice. Recorded in results/smoke-021/RESUME_DRILL_021.json before the source freeze
- **G_RT_study_runtime**: every stream inside the 7200 s cap and not stopped; watchdog covers the whole run; kill drill latency <= 15 s
- **G_HB_heartbeat_gap**: max heartbeat gap <= 10 s over the whole run (frozen; restart gaps are reported separately and NOT excused)

## Reported only
- C_curve per step (RGNA4 vs RGNB4 trade-off)
- dC_late(RGNA4 - RGNB4) at eps 0.01 / 0.02
- per-bit coverage and false counts (RGNA4_bit)
- stress eps 0.05
- RG4 / RGN4_or / SP8 coverage
- anytime vs planned boundary table
- rate math projected vs observed
- heartbeat attribution (sentinel)

## Seeds
Held-out: {"cycle3": [8710001, 8710024], "switch3": [8720001, 8720024], "unaliased2": [8730001, 8730024], "ood4": [8740001, 8740048]}. Smoke: 8790001-8790030.

## Stop rule
- cap: 2 h 00 min (7200 s) wall clock from RUN_T0
- at_cap: every unfinished stream is stopped and sealed as is; NO extension and NO rerun
- scoring: every gate whose inputs are incomplete at the cap is FAIL (STUDY_BUDGET)
- rate_math: as study-020 (x 1.75 margin on the slowest smoke case per cell; the mean-based path is also published), on smoke seeds, before the source freeze
- restart: a restarted orchestrator resumes every stream from its checkpoint and charges the time already spent (as study-020)

## Process
- source freeze before the scoring freeze; scoring freeze >= 600 s before run_start
- one held-out run, launched detached (setsid nohup) with the independent watchdog and the heartbeat sentinel
- ledger sources name ARTIFACTS, not producing scripts
- declare K_0180 in the test-isolation rules
- strip SMOKE from the GTI environment in dry runs
- no GitHub Actions or workflows
- push after every step; no force-push

## What counts as failure
- any gated criterion not meeting its threshold is FAIL and is published as FAIL everywhere
- GAH (a), (b) or GS_a9 FAIL would refute the anytime lemma or the implementation
- GAH (c) FAIL means the anytime schedule does not recover early coverage
- GAH (d) FAIL means the horizon-free schedule costs too much late coverage

## Limitations
- 2 actions, 2-bit readings, n = 4 hypotheses
- iid bit-flip noise only, eps <= eps_bar attested by the caller
- coverage remains near zero for the first ~10 steps (burn-in 8 plus margin)
