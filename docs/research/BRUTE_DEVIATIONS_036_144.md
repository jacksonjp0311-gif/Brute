# Deviation #144 (study-036, v0.33.0): build choices fixed before the source freeze

Written before the source freeze and frozen with it. Nothing here changes a threshold in BRUTE_PLAN_036. Each item records
a choice the plan left open, a reading of a criterion, or a process slip, made before any main case was run. Labels:
Exact, Observed, Simulated, Inferred, Rejected, Open. Times are box-local EDT (UTC-4).

1. **Authorization (Exact).** build_authorization_036 was ledgered at 2026-10-30T19:21:23-04:00 EDT under James's
   STANDING GO t133s553 (ledger 76b30d5), plan BRUTE_PLAN_036 at plan/v0.33.0 3ab989d. seedcheck_036 PASS
   (results/diag-036/SEEDCHECK_036.json, commit 0a9ae7c, ledger 0eac98d: 739 files scanned, 16/16 negatives refused,
   48 cases) before any 036 seed was used.
2. **Base trace (Exact).** For A11_r3 and A11_r5 the base trace is the per-position, per-bit majority of r raw reads: the
   step read plus r - 1 re-reads. Every executed word is read r times at every B, also at B = 0. The raw reads are stored
   (base_readings, raw) and the recount rebuilds the majority from them.
3. **K, reads and reads per step (Exact; reading).** K = 64 counts steps (actions), not reads. reads = r x (steps + 1)
   for A11 arms; reads_per_step is reported as reads / (steps + 1), so A10 and S7 give about 1.0 and A11 gives r.
4. **B_max per r (Exact).** B_max(r) = flip_budget(354, majority_rate(0.05, r)) with the frozen scalesearch7 rule over
   354 bits ((176 + 1) x 2): r3 = 6, r5 = 2; A10 and S7 keep 27 (r = 1); S5 has 0.
5. **Plan arithmetic (Exact; correction, no threshold changed).** The plan text says the expected majority flips are about
   1.3 per 177 readings for r = 3. That counted readings, not bits: the majority flip rate at eps 0.05 and r = 3 is
   0.00725 per bit, so about 2.6 flips are expected over 354 bits. B_max is computed by the frozen rule over bits
   (item 4), so the correction changes no number in the design.
6. **bmin11 (Exact).** search 'bisect' (A11_r3, A11_r5): probe B_max first (UNSAT gives stop 'none'; a capped probe gives
   'unknown'), then bisect over midpoints. Every probe is recorded as [B, True/False/None] (None = capped). search 'up'
   (A11_r3_up) uses the frozen bmin10 upward search 1..B_max.
7. **Query cap (Exact).** QUERY_S = 9.5 s per SAT query for all arms (host TimerHook from the 035 module), so a query that
   overshoots the cap by the interrupt latency stays under the GQB11 bound of 10.5 s. S6._RegionID is patched with the
   9.5 s hook host-side; no frozen brute/ file is changed. FLIP_EXTRA = 3000. Solver g3 for the arms (as #142 item 3).
8. **Reference (Exact; disclosure).** The CNF reference reuses the frozen experiments/v0320_reference.py; no
   v0330_reference.py was written. scripts/run_reference_036.py audits A11_r3 (B_max 6), rebuilds the majority base from
   the world flips, audits the probes, and adds a 'probe' mutation kind (seed 330). GS_ref needs raised_B_decided > 0,
   otherwise it fails with reason 'raised-B not exercised'.
9. **Gates (Exact).** As scripts/make_gates_036.py. GRB11 is reported under 'secondary'. Wilson 95% CIs on every count;
   paired seed-bootstrap 95% CIs on contrasts; bootstrap CIs on cost (B_final, capped, steps, reads, reads_per_step,
   used).
10. **Dev trial (Observed; not gated, no tuning).** Before the smoke, smoke-range seeds 10290030 (control) and 10290029
   (noisy_scale8) were run in-process (scratch /tmp/s37/try.py). Control: all arms ID in 0.5 s. noisy_scale8 (case wall
   82.9 s): A11_r5 ID (194 steps, 975 reads); A11_r3 IDU with probes [6 SAT], [3 UNSAT], [5 capped] and truth flips 5;
   A11_r3_up IDU; A10 IDU (truth flips 11); S7 IDU; S5 IDU (one query 10.34 s with the 9.5 s hook in place:
   the interrupt latency on S5 is larger than on the g3 arms, still under the 10.5 s bound; Observed, not tuned).
   The cd195 reference decided B = 3 UNSAT quickly on that trace (Inferred: a candidate diagnosis for v0.34, a direct
   least-B solve). No design value changed after this trial. Unit tests used old seeds only (10050001, 10090005).
11. **Smoke (Observed).** Smoke block 10290001-10290008, launched 19:41:08 EDT, 8 workers, wall 61.7 s, output
   /tmp/smoke036 (outside results/study-036). results/diag-036/PREFREEZE_SMOKE_GATES_036.json, PASS: recount 0
   mismatches (146 words checked, 0 unsound); reference on 2 cases: 27 decided, 25 at raised B, 0 mismatches, 20/20
   mutations; gates --check reproduces on the relabelled block (its gates read INCOMPLETE because 8 of 48 cases exist,
   as in 035; the 48-case path is covered by tests/test_scripts_036.py). Labels: A11_r3 ID 3, IDF 1, IDU 4; A11_r5 ID 7,
   IDF 1; A11_r3_up ID 4, IDF 1, IDU 3; A10 ID 2, IDF 1, IDU 5; S7 ID 1, IDU 7; S5 ID 1, AMB 2, WRONG 4, IDU 1.
12. **Runtime (Inferred; no amendment).** Mean case wall by key: noisy12 58.6 s, noisy12_extra 60.6 s, clean12 42.2 s,
   noisy8 49.0 s, control 0.5 s; projection for 48 cases: serial 2164 s, ideal parallel 271 s, greedy 8-worker makespan
   302 s. The plan rule drops noisy_scale12_extra only if the projection exceeds 1500 s; it does not, so all 48 cases stay.
13. **Clock (Observed).** At build authorization the box was about 6 s ahead of GitHub's Date header; at 19:45:30 EDT it
   was about 9 s ahead (23:45:21 GMT). No stall in the run tooling. One anomaly: after a 200 s tool wait started near
   19:41:08, `date` read 19:41:25 and the smoke log still showed 1/8, while the files show the smoke finished at 19:42;
   the next read (19:44:49) matched GitHub to the second. Inferred: the wait returned early or the box paused; no data
   was affected (the smoke ran once, sealed, and was never relaunched).
14. **Process slips (Observed).** The v0.32 fresh-clone unittest was run twice (disclosed from the 035 release). A
   perf_counter import inside a function in scalesearch11 was moved to module level before any seed was used.
