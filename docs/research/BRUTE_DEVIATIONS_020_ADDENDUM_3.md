# Study-020 deviations, addendum 3: post-run disclosures (#106)

Written 2026-10-28 ~13:55 EDT, after the seal (`8430b47`), scoring (`35a03bb`) and clean clone (`7053791`). Nothing frozen is
edited, no verdict is changed, and the ledger stays append-only. Deviation numbering continues after #105.

## #106 Post-run disclosures

1. **Run outcome (Exact, RUN_DONE_020.json).** Run end was at 13:43:58 EDT, 6740 s after RUN_T0 11:51:38 EDT. The cap is
   7200 s, so 460 s were left unused. The 6740 s include the dead interval of the box restart, about 12:19:42 to 12:37:58
   EDT (the 1083.5 s watchdog gap plus relaunch time; #105). Per-stream times from RUN_DONE:
   - transfer: 4467 s, which includes 1683 s charged for the pre-restart attempt;
   - gti: 5443 s;
   - repro: 1176 s;
   - g11: 402 s.

   No stream was stopped and no STOP file exists. The watchdog exited without killing anything.
2. **G_HB FAIL (Exact).** The maximum watchdog gap is 1083.5 s, against a limit of 10 s. Four more gaps exceed 10 s after
   the relaunch: 26.7 s, 57.5 s, 32.5 s and 28.5 s, at 13:20:00, 13:34:23, 13:42:37 and 13:43:20 EDT. The attribution
   (HEARTBEAT_ATTRIBUTION_020.json) gives 3 clock_step and 2 unattributed; it is Inferred and diagnostic only. The
   post-restart gaps coincide with periods when the operating agent was interrupted. Their cause is Open.
3. **GLH_early_control FAIL (Exact) and its mechanism (Exact from code; consequence Inferred).** The observed
   C_early28(RGNB4, eps 0.02) is 0.00253, CI [0.00119, 0.00417], well outside the study-019 CI [0.04053, 0.065436].
   - The pre-registered control assumed that steps 1-28 of an 88-step trace would reproduce study-019. They do not:
     `brute/seqmargin.boundary(B, eps_bar, delta)` spends the crossing budget linearly, as `delta*b/B` at bit b.
   - With B = 176 planned bits instead of study-019's 56, the margin m(b) at a given early b is larger, so fewer early
     certificates are issued.
   - The control was therefore mis-specified at pre-registration: it is not a frozen-code check across horizons. This is
     published as FAIL. It is not re-scored, and the rule is not changed.
   - GLH_horizon (a-d) PASS is unaffected.
4. **Ledger note errors (Exact).** Both are kept, append-only.
   - The `seal_020` receipt note carries the hand-typed time 13:47:00. The seal commit `8430b47` is at 13:45:00 EDT, and
     SEAL.json `sealed_at` is 13:44:28 EDT.
   - The `clean_clone_020` note says "at 35a03bb tree". The clean clone actually ran at HEAD `c3aca37`, which is the ledger
     commit on top of `35a03bb` (CLEAN_CLONE_020.json `commit`); the tracked content is otherwise identical.
5. **Stress block (Observed; reported, ungated).** RGNB4 issues 6 false certificates on 5 of 120 eps-0.05 cases. Eps 0.05
   exceeds eps_bar 0.02, so there is no guarantee there; mean P(flips > m) is 0.31.
   - Per-bit: 10 false bits on 8 cases.
   - RGN4_or: 0 false.
6. **Lost scratch.** The /tmp scratch (including /tmp/wt-state) was lost in the box restart; it was not deleted by the
   operator. The `brute-bridge` worktree and BGR-v0.90.0 are untouched.
