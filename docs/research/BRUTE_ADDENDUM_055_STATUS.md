# Addendum to v0.52.0 (study 055): the status wording "sound but not certified" is wrong

_Written 2026-10-31T21:21:26-04:00 (EDT). New file; RELEASE.json, README.md, CHANGELOG.md, deviation #184, GATES_055 and every frozen file are left as committed. This addendum overrides their status wording._

**What the frozen rule says (Exact).** BRUTE_PLAN_055 certification_rule: "If every gate except GS20C_gain55 passes, certify/20c is published as sound but not certified." make_gates_055.py (freeze 055) computes sound_not_certified_20c = not certified and every gated gate except GS20C_gain55 passes.

**What happened (Exact).** GATES_055 (8a680bc): GS20C_gain55, GCOMPAT20C55 and G_PROC fail, so sound_not_certified_20c = false. GATES_055 and RELEASE.json's flag are correct. The phrase "published sound but not certified" in the RELEASE.json api text and commit 75ff4ba, the README claim row and bullet, the CHANGELOG title, HANDOFF, the v0.52.0 tag message and the GitHub release notes is wrong: the plan's condition for that status is not met.

**Correct status (Exact).** certify/20c has **no certification status** under plan 055: not certified, and not "sound but not certified". Nothing at 20 states is certified; certify/20t, certify/16n and certify/16e are unchanged.

**What still holds (Observed).** No soundness evidence failed: WRONG 0/30 [0.00, 0.11] (GS20C_sound55), 0 audit mismatches on 5/5 decided records with 20/20 mutations (GS_ref), 343 recounted words 0 unsound (G_sound), every pruned cube checked UNSAT (GCUBE55). The two extra failures are not soundness failures: GCOMPAT20C55 is agreement with certify/16e at 16 states, and G_PROC is a ledger event name. Saying certify/20c "gave no wrong answer in this study" is fine; calling it the plan's "sound but not certified" status is not.

**Why GCOMPAT20C55 is 4/6 (Observed; reading Inferred).** The 052 rule asks two IDF answers to be the same machine from the current state s1. On 12270003 and 12270005 both arms said IDF and each matched its own trace, but the arms stopped at different steps (252 vs 265; 209 vs 223), so s1 is a different state on each side. On 12270003 the two machines are identical from state 0, so this is a comparison artefact (Inferred). On 12270005 the machines differ from state 0 too; Open. The cube split changes which model the solver returns first, which changes the next action chosen, so the traces diverge (Inferred).

**Why G_PROC failed (Exact).** The order clause looks for a ledger event named exactly prefreeze_smoke_055. The first smoke was ledgered as prefreeze_smoke_055_attempt1 (it failed only on the ghost loop), and the fix was checked by prefreeze_ghost_recheck_055. Under the 19:39 EDT instruction "Do not rerun anything" no second full smoke was run, so no event has the required name. No event was added after the fact.
