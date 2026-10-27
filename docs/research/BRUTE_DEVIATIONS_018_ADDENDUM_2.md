# BRUTE study-018 deviations, addendum 2 (post-run disclosures, #100)

Written after the seal (`e86f1df`), GATES_018 (`f0f0010`) and the clean clone (`560e177`). Nothing here rescores
anything: every gate verdict stays as `results/study-018/GATES_018.json` records it (10 of 12 gated pass; GNS and GN0
FAIL). `BRUTE_DEVIATIONS_018.md` (#97) and `_ADDENDUM_1.md` (#98-#99) are ledger-hashed and unchanged.

## #100 Post-run disclosures

1. **GTI ran while the run_start ledger line was uncommitted.** `run_start_018` was appended to
   `results/RESEARCH_LEDGER.jsonl` at 10:37:53 EDT (recorded against HEAD `f9df9bc`) and committed as `138cfee` at
   10:38:15 EDT. The GTI stream started inside that 22 s window, so `TEST_SUITE_018.json` records
   `tracked_tree_dirty: true` with head `f9df9bc`. The only dirty file was the ledger, which no test reads as an input
   to a verdict; all five GTI clauses pass. *Observed.* The listed path is `esults/RESEARCH_LEDGER.jsonl`: the dirty-file
   parser drops the first character of a `git status --porcelain` line. Cosmetic defect, *Observed*; fix it in new code
   for v0.17.0 and record the run_start commit before starting streams.
2. **RELEASE.json `scoring_scripts_commit`.** `verify_release_0160` requires this commit to be strictly after the source
   freeze `c350ba5` and strictly before the seal `e86f1df`, and the scoring files at it to equal the current files. The
   first draft named `18885f4` (process scripts, before the source freeze), which the verifier rejected. RELEASE.json
   now names `5b77da4` (ledger commit `scoring_freeze_018`). This is a data correction in RELEASE.json (`c1fc976`); the
   verifier was not changed. *Exact.*
3. **Verifier required keys.** Before the release freeze, `verify_release_0160` failed on `PROGRESS_G11_018.json`, which
   has no `schema` key; its REQUIRED_KEYS entry was set to `cases_done` (a key the file does have) in tooling commit
   `8933d3a`, before `BRUTE_RELEASE_FREEZE_0160.json`. *Exact.*
4. **Kill drill evidence.** `results/study-018/KILL_DRILL_018.json` is the pre-run drill on smoke seeds (block
   smoke-drill, 0.226 s), copied into the sealed directory at the seal. *Exact.*
5. **Rate math over-projected.** Projected vs observed stream wall time (s): transfer 984 / 425, repro 377 / 164,
   g11 585 / 186, gti 1352 / 881. The 1.75 factor and the slowest-case rule made the projection 1.5-3.1x conservative.
   *Observed.*
