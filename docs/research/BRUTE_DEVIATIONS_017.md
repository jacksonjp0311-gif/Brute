# Study-017 (v0.15.0) deviations and disclosures

Numbering continues project-wide. Study-016 ended at #85 (BRUTE_DEVIATIONS_016_ADDENDUM_2.md). Evidence labels:
Exact / Observed / Simulated / Inferred / Rejected / Open. Every entry below was written before any v0.15.0 code
(reference, learner or runner) existed, before the source freeze, and before any held-out seed of BRUTE_PLAN_017 was
generated. Later entries, if any, go in BRUTE_DEVIATIONS_017_ADDENDUM.md (this file is ledgered and never edited).

**#86 (disclosure): stale module name in the frozen plan.** second_implementation.file and process_controls.order (3)
and (4) name `brute/attestedlicense.py`. The plan's freeze_rule file list, api_definition and arms name the new module
for the bounded-lookahead chooser `brute/boundedlookahead.py` (the attested-license headline was retired before the
freeze, #85). Read every `brute/attestedlicense.py` as `brute/boundedlookahead.py`: the reference is committed before
it and before `brute/api/certify5.py`. The attested-license rule (DLFa) lives in `brute/boundedlookahead.py` too
(function `attested_license_bound`). Label: Exact (no other file of that name is created).

**#87 (disclosure): stale source-seed base in transfer_definition.pairs.** The text says the positive library of
target family f is source seed `8250000 + 24 x index(f) + offset`; 8250001-8250096 is the study-016 source range.
heldout_ranges_transfer.sources is 8350001-8350096 and seed_assertion_plan requires every v0.15.0 seed to be inside its
own declared range. Read the base as 8350000. scripts/check_seeds_017.source_seed derives the base from the plan's
source range (as in study-016), so no literal 8250000 appears in code; tests/test_seeds_0150 asserts
source_seed('cycle3', 1) == ('cycle3', 8350001). Label: Exact.

**#88 (clarification): the RGL lookahead score.** H_rgl says: choose the action a that maximises "the support-weighted
fraction of outcomes o (readings consistent with the RG4 region after a) after which the RG4 region forces the next
reading for SP8's next action". Two parts cannot be implemented as written, learner-visibly and soundly:
(i) "SP8's next action" after a hypothetical outcome o needs a simulated copy of the SP8 learner advanced by (a, o)
for every candidate (a, o); that is not part of any frozen API and would make the chooser depend on learner internals.
Read it as "for some next action b in {0, 1}" (the region forces the next reading for at least one action);
(ii) "support-weighted": the RG4 region (brute.region.RegionSpace, SAT-based) enumerates no rows, so there is no weight
per outcome. Read it as uniform over the outcomes in the region's support.
Definition used by the reference and the implementation. At step t <= burn_in: the SP8 LU-R choice (rule 'sp8').
At t > burn_in, for each action a let O_a = the RegionSpace(4) support for a (region_supports, UNKNOWN codes counted as
possible). num_a = |{o in O_a : the region extended by the fully observed step (a, o) is feasible and its support for
some b in {0, 1} is a single code with 0 unknowns}|, den_a = |O_a| (num_a = den_a = 0 if O_a is None or empty; an
extended region whose feasibility or support is UNKNOWN does not force and adds 1 to unknown_a). score_a = num_a /
den_a (0 if den_a = 0), compared exactly as fractions. If score_0 == score_1 (including both 0) the SP8 choice (rule
'sp8'); else the argmax (rule 'rgl'). Arms: RGLX4 = RGL while RG4 has not certified the taken action at an earlier step
on this trajectory (the deferral reading of #75), then the frozen RSX choice (brute.regionsplit.rsx_choose on the n = 4
support sizes); RGL4 = RGL for the whole run. Both certified by RG4 (frozen rg_decide). Each step records
'lookahead' = {'num': [n0, n1], 'den': [d0, d1], 'unknown': [u0, u1]} or None (not computed: burn-in, or after the
switch in RGLX). The reference checks num / den by exhaustive enumeration whenever unknown == 0 (UNKNOWN never occurred
at n = 4 in studies 014-016: Observed). The plan's "greedy" variant (take an action that is certifiable now) is not run:
Open. Effect on gates: none (GRL threshold unchanged). Label: Exact (definition); Inferred that the effect is small.

**#89 (clarification): RSXL5 on ood5.** arms_by_block lists RSXL5 for the ood5 block, but transfer_definition defines
only RSXL (with RG4). Define RSXL5 = the RSXL rule with FB = 5: the SP8 choice while RG5 (frozen rg_decide with the
RegionSpace(5) support) has not certified the taken action at an earlier step, then rsx_choose on the RegionSpace(5)
support sizes; certified by RG5 on that trajectory. Bounded supports n = 1..5 are recorded on it. RSXL4 on main cases
keeps using the frozen study-016 runner function (brute_study_016.rsxl_trajectory) so it replicates byte for byte; the
generalised trajectory function is tested to equal it at n = 4 on smoke seeds. Label: Exact (definition).

**#90 (disclosure): heartbeat diagnostics (owner request, ungated).** watchdog_definition says the thin watchdog_017
wrapper reuses watchdog_014 unchanged (study paths only) and that "each heartbeat additionally records CLOCK_BOOTTIME,
CLOCK_MONOTONIC and the summed CPU time of every study worker". watchdog_014 already records wall, CLOCK_MONOTONIC,
CLOCK_BOOTTIME, its own CPU and PSI io per beat. Adding worker CPU inside the watchdog would change its logic, which the
same sentence forbids. Resolution: the watchdog stays byte-identical (sha256-checked wrapper); a separate, independent
sentinel process `scripts/hbsentinel_017.py` (started next to the watchdog, never kills anything) ticks every 0.25 s
on CLOCK_MONOTONIC and every 2 s appends to `HB_SENTINEL_017.jsonl`: wall, monotonic, boottime, the largest loop gap
since the last line, the summed utime+stime of every orchestrator descendant (from /proc), and the /proc/stat aggregate
(user, system, idle, iowait, steal ticks). After the run `scripts/hb_attribution_017.py` writes
`HEARTBEAT_ATTRIBUTION_017.json` (R_heartbeat_attribution): for every watchdog gap > 10 s, d_wall, d_monotonic,
d_boottime, the overlapping sentinel loop gap, worker CPU and steal over the gap, files written during the gap, and a
class: 'clock_step' (|d_wall - d_monotonic| > 1 s: the wall clock jumped; the gap is not a stall), 'suspend'
(d_boottime - d_monotonic > 1 s: kernel suspend), 'box_pause' (the sentinel also stalled for >= 50% of the gap and
worker CPU advanced < 10% of gap x workers: the whole box stopped), 'watchdog_stall' (the sentinel did not stall: only
the watchdog was descheduled), else 'unattributed'. The classes are Inferred readings of clock evidence, not proofs.
G_HB is unchanged: largest gap in HEARTBEAT_017.jsonl <= 30 s; a box pause still FAILs it. Label: Exact (G_HB
unchanged); Inferred (attribution classes).

**#91 (disclosure): arms carried from study-016.** arms_by_block lists the new arms; transfer_definition keeps the
study-016 reported arms (RSX trajectory / RSX4, RSXLp / RSXLn, DLF2p / DLF2n, EB) and the stress block. All are kept
(reported, ungated) so G13 can check that RG4 / DLF / RSX / RSXL reproduce through the frozen v0.14.0 code. RG5 is also
recorded on main cases (as study-016). Label: Exact.
