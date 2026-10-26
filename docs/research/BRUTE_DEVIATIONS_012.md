# Study-012 (v0.10.0) deviations and disclosures

Numbering continues project-wide. Study-011 ended at #47 (docs/research/BRUTE_DEVIATIONS_011_R1.md).
Evidence labels: Exact / Observed / Simulated / Inferred / Rejected / Open.

**#48: branch base.** The owner asked for plan/v0.10.0 to come from main `13daa32`. The branch is `13daa32` plus
two commits that came before the plan:

- `6494a35`: the exploratory downgrade diagnostic. It contains scripts/diag_downgrade_012.py,
  results/diag-012/DOWNGRADE_DIAG_SEEN.json and docs/research/BRUTE_DIAG_DOWNGRADE_012.md.
- `a52313b`: the ledger receipts for that diagnostic.

Neither commit adds learner code. The order (diagnostic first) is the owner's. Exact:
`git merge-base --is-ancestor 13daa32 <plan commit>`.

**Disclosure (not a deviation): the transfer track was added before the freeze.** The owner's steering
(TRANSFER/ABSTRACTION track, ROADMAP_TO_GI.md) arrived while BRUTE_PLAN_012 was still unfrozen. The track is
therefore part of the frozen plan, so it needed no addendum.

**Disclosure (not a deviation): J10 differs from the NEXT_ITERATION.md proposal.** That proposal was a
surprise-gated hull, and surprise gating was **Rejected** on seen data by the diagnostic. J10 is instead the
exact jump-window *support* rule. This is recorded in plan `pre_freeze_disclosure`.

**#49: big78 stream budget 1800 s -> 2700 s (rate math, before the source freeze).** The big78 stream projected
~1390 s, ~77% of its frozen 1800 s budget, above the 70% trigger of stop_rule.rate_math
(docs/research/v0.10.0/RATE_MATH_012.md). The one permitted change was used: big78 budget 2700 s (~51%). Sample,
workers and every other budget are unchanged. Exact: scripts/run_study_012.py and scripts/make_gates_012.py both use 2700.

**Disclosure: the g11 stream carries GT_ref.** The independent transfer audit (experiments/v0100_reference) runs inside
the g11 stream after the mandatory 2x2 sample, so g11 depends on both 2x2 and transfer. The repro stream is one
process group (repro/2x2 then repro/transfer, one bash chain).

**Disclosure: exploratory seen-data runs before the source freeze.** Besides the pre-plan downgrade diagnostic:
(a) scripts/diag_transfer_seen_012.py on study-011 seen seeds (results/diag-012/TRANSFER_DIAG_SEEN.json): TRp 0 false
certificates; TRn 246 false certificates, all before the wrong library was eliminated (Observed, exploratory). It was run
after the plan freeze and did not change any frozen constant. (b) a scratch g11 timing (J10/SP8 audit ratio 2.0) used
only for rate math.

**Disclosure: smoke observations that bear on the gates (smoke seeds only).** big78: 0 certificates on all 6 timed
smoke cases, so G78_soundness is expected to pass VACUOUSLY. Transfer: TRn issued 4 false certificates on 2/8 smoke
targets before elimination, so GT_a and GT_c are at risk. The TR rule stays as frozen; no constant was tuned after seeing
these.

**Disclosure: GTI smoke.** The smoke GTI run at 1c43d68 (1149 s) failed clause (i) with 6 undeclared failures, all
caused (Inferred) by a stale MANIFEST.sha256; see RATE_MATH_012.md. No test, test list or GTI rule was changed.

**#50: GTI predicted FAIL; non-gated K_080 report added (before the source freeze).** The GTI smoke showed that the
three test_release_080 tests (version_consistent, fast_verify_passes, untampered_copy_passes) fail on the v0.10.0 tree
because RELEASE.json has said 0.9.0 since the v0.9.0 release (Observed: re-run alone at 5ae0891, AssertionError
'0.9.0' != '0.8.0' and missing key GA1_010). This is the same superseded-release pattern as K_060 / K_070, but the
frozen GTI criterion has no K_080 rule. **The gated criterion is NOT changed**: GTI_test_isolation is scored as frozen
and its plan prediction (PASS) is now Inferred FAIL. Added: scripts/gti_k080_012.py (frozen with the sources), run after
the seal, writes the non-gated report results/study-012/GTI_K080_012.json (does each test_release_080 failure pass on a
clean v0.8.0 worktree with the same runner, and would GTI pass with a K_080 rule). The other three smoke failures
(manifest test, release_090 short/untampered verify) were caused by the stale MANIFEST: after make_manifest at 5ae0891
test_manifest_matches_tracked_files and test_short_verify_passes pass (Observed). Smoke of the new script on the GTI
smoke output: K_080 rule applies (all 3 pass on clean v0.8.0).

**Disclosure (pre-freeze bug fix, not a deviation): superseded release freeze.** The first source-freeze attempt showed
that experiments/brute_common_012.check_freeze also verified BRUTE_RELEASE_FREEZE_090.json, which is superseded by
BRUTE_RELEASE_FREEZE_090_R1.json (scripts/verify_release_090.py changed under R1), so G13 could never pass. Fixed before
the freeze: the list is 070_R1, 080, 090_R1. No plan text changed.
