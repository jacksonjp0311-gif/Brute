# Deviation #155 (study-041, v0.38.0): post-run record

Written after the main run, recount, reference, tests and gates. Nothing here changes a gate, threshold, sealed file or
frozen file; no gate is re-read. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open. Times are box-local EDT
(UTC-4), 2026-10-31.

1. **Run (Observed).** One main run, started 00:35:49 (ledger a24ceb5, frozen source a649dd2, freeze ledger 2d9021f),
   294/294 jobs (240 replays, 18 fresh cases), 157.4 s of 1800 s, normal exit about 00:38:28; one checkpoint snapshot
   pushed (2b71565); sealed 5221d1c (ledger 1799529). Nothing was relaunched or resumed. 15 hard kills over 2066 logged calls;
   max call 10.012 s (bound 10.5 s).
2. **Recount gap (Observed; the main failure of this release).** RECOUNT_041 FAILS with 25 mismatches, every one BAD_stop
   on a part-c replay whose stop is AMB (E1 6, E2 6, E3 6, E4 7). A stop-check replay ends with AMB when the frozen
   stop_check14 finds a rival machine at n_min; active runs never end that way (they spend more actions, ending ID / IDF /
   K_spent / unknown), so the frozen label rule copied from the active-run recount (lab14) has no AMB-at-stop branch and
   returns BAD_stop. The smoke block did not expose this: its two scale14 traces ended unknown or IDF under every variant,
   and the synthetic complete block was built from those same records. Lesson: the pre-freeze test must include a record of
   every stop the runner can emit.
3. **Cascade (Exact, from scripts/make_gates_041 as frozen).** GAUD_sem, G_sound and G10 all require the recount to pass
   (rc_ok), so they FAIL with it. Their own conditions hold on the data (Observed): GAUD_sem 0 replay contradictions, 0 fresh
   contradictions, 0 WRONG, 0 label mismatches; G_sound 0 unsound words of 21 in study and recount, 0 truth inconsistencies;
   G10 every arm ID on all 6 controls. They stay FAILED; the literal plan branch "if GAUD_sem fails, A15/A15_cube are withdrawn
   from every later study" is taken as written.
4. **AMB records checked two other ways (Observed, post-hoc, not a gate).** All 25 AMB records end with a SAT future query
   at their n_min (the recount's own _ends_sat helper, run once in a scratch shell). The independent CNF reference
   (REFERENCE_041, PASS) re-checked the 12 E1 / E2 AMB records among its 20 decided records: 0 mismatches.
5. **GPERM16 (Observed; a real failure).** Fresh perm12: A14 decided 11/12; A15 and A15_cube agree on 10/11 (Wilson
   [0.62, 0.98]); on 10710005 both returned unknown where A14 gave ID at 12. The GINC15 loss replicates on unseen data.
   (On the case A14 left unknown, A15 and A15_cube gave ID; that gain is reported, not scored.)
6. **Nothing else changed.** No rerun, no tuning, no edit to a frozen or sealed file. The resume clause was not approved and
   not used.

What this deviation does not do: it does not pass any gate, re-read GAUD_sem, or fix the recount; a fixed recount is
pre-registered for v0.39.0 (BRUTE_PLAN_042), as a new file.
