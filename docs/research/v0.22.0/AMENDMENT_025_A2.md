# Plan amendment 025-A2: lean process (v0.22.0)

Label: **Exact** (what is declared). Locked before any held-out data. File: `experiments/BRUTE_PLAN_025_A2.json`.

**Authorization.** Owner card t130s540, answered by James at 2026-10-29 23:45 EDT: "switch to the LEAN process now,
including v0.22.0". Follow-up at 23:50 EDT: "Push us there don't stop".

**Kept.** The plan and amendments stay locked before data. Every false certificate gets an exact recount. The strict
stress gate (A1) stays. Failures are published, and evidence labels are used. We push after every step, never force-push
and add no Actions. The ledger stays append-only, with times from `date -Iseconds`. The lemma and the reference come
before the RGB6 code; that is already done (55dd41f, 8f31080 < 19987c8).

**Dropped.**
- the kill and resume drills
- the host-pause probe
- the watchdog, the heartbeat sentinel and G_HB
- the launcher and first-log-line controls
- the separate 600 s scoring-freeze wait
- the git-archive clean clone (one fresh GitHub clone, with a short verify plus the tests, is kept)
- the full-suite GTI runner
- the G12 re-run
- the rate-math file

**Cases (declared before data).** Block `lean` has 90 cases:
- **main (60):** every 6th seed of each held-out family range, at eps 0, 0.01 and 0.02. That is 4 + 4 + 4 + 8 = 20 seeds × 3.
- **stress (30):** the unchanged study-025 set (the first quarter of each range, at eps 0.05).

**Cap.** 1800 s, enforced by `timeout`, with 8 workers. Estimate: about 960 s raw, ×1.75 = about 1670 s (Inferred). If
the cap is hit, the run seals partial, the data gates FAIL with INCOMPLETE_INPUT, and there is no relaunch.

**Criteria changes forced by the sample size.** GBC a keeps "0 false on all noisy main" (40 cases). Its CP95 ≤ 0.02 clause
cannot be met below n = 149: 0/40 gives 0.0722 (Exact). So that clause is reported, not gated. The clause is dropped
because no n below 149 can meet it. This is not tuning, and it is disclosed here before data. All other headline
thresholds are unchanged, including the strict b. With 20 eps-0.02 cases the CIs are wider.
