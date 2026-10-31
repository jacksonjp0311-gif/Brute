# HANDOFF — pick this project up cold

_Kept current on the working branch during a release and on `main` at release. Last updated 2026-10-31 (v0.40.0 RELEASED)._

## Current version and state

<!-- V0400 -->
- **v0.40.0: RELEASED** 2026-10-31 (EDT), https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.40.0 (annotated tag at `69a8d47`, ledger release_043 `2bc983a`). Fresh-clone verify of the tag passed: verify_release_0400 (7 links, 0 exceptions) and 34 tests. Built on branch `plan/v0.40.0` (BRUTE_PLAN_043, A16 vs frozen A14 on fresh lowobs12 plus a scale16 replication; LEAN; STANDING GO t133s553, build authorization ledger `817d2ac`). Maintainer order: lowobs first; certify/16 after the N-free stop.
  - **Run complete (Observed).** 60/60 arm jobs (30 cases), 159.7 s of 1800 s, normal exit about 02:51:49 EDT, run once; 1 checkpoint snapshot (`e7bae0d`); nothing relaunched; resume clause not approved, not used. Hard per-call cap: 0 kills, max call 9.596 s. Box clock about 2 s ahead of GitHub's Date header at 02:59 EDT.
  - **PASS (10/11):** GREP16 (A16 scale16_rep ID 9/12 [0.47, 0.91], A14 1/12 [0.01, 0.35]), GLO_sem, GQB18, G_sound (354 words, 0 unsound), G10, GS_ref (10 decided, 0 mismatches, 20/20), GTI, G_PROC, G_RT, G_recount. **FAIL:** GLO (lowobs12 A16 ID+IDF 0/12 [0, 0.24], A14 0/12, gain 0). Secondary GT17 0.81 [0.72, 0.90], GPH18, GLO_cause reported only.
  - **Branch taken:** next_if_fail (GLO fails, GREP16 passes): a lowobs budget/K audit using GLO_cause, not a new encoding. The N-free stop waits.
  - **Deviations:** #159 (pre-run: seedcheck erratum adjudicated by check_seeds_043b, recount adapter, GS_ref scope, prefreeze PASS term), #160 (post-run).
  - **Chain:** plan `d9b8538` -> authorization `817d2ac` -> worlds/seedcheck code `8e4e6ad` -> seedcheck `486d6ab` (FAILED) -> 043b `b0a20c2` -> code `28f76a4` -> tests/freeze tooling `b448616` -> pre-freeze smoke `65ce3fe` -> #159 `6be601a` -> freeze `2408c8f` -> run start `4490ba8` -> seal `122f7a1` -> recount `73fb1b7` -> reference `3e11414` -> tests `fb365a1` -> gates `ccff3bf` -> #160 `1351860` -> RELEASE.json and docs `cd65f11` -> HANDOFF `39eb1a5` -> tag -> fresh-clone verify -> this RELEASED note; `main` fast-forwarded here.
  - **No CI:** no `.github`, no workflows. The `brute-bridge` worktree and BGR-v0.90.0 were not touched.

<!-- V0390 -->
- **v0.39.0: RELEASED** (previous) 2026-10-31 (EDT), https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.39.0 (annotated tag `675e20d` -> `384e401`, ledger release_042 `9330d99`). main fast-forwarded `9f7558c..` the HANDOFF RELEASED ledger commit. Built on branch `plan/v0.39.0` (BRUTE_PLAN_042, A16 vs frozen A14 on fresh scale16; LEAN; STANDING GO t133s553, build authorization ledger `2c1ed4b`). Next: BRUTE_PLAN_043 (v0.40.0, plan only).
  - **Run complete (Observed).** 60/60 arm jobs (30 cases), 240.1 s of 1800 s, normal exit about 02:10:35 EDT, run once; 1 checkpoint snapshot (`a6603b9`); nothing relaunched; resume clause not approved, not used. Hard per-call cap: 0 kills, max call 9.515 s. Box clock about 5 s ahead of GitHub's Date header at 02:24 EDT.
  - **PASS (11/11):** G16 (A16 scale16 ID 8/12 [0.39, 0.86], A14 0/12 [0, 0.24], gain 8), G16_sem, GPERM17 (11/11 [0.74, 1.00]), GQB17, G_sound (311 words, 0 unsound), G10, GS_ref (9 decided, 0 mismatches, 20/20 mutations), GTI, G_PROC, G_RT, G_recount. Secondary GT16 0.82 [0.71, 0.95], GRR041, GPH17 reported only.
  - **Fresh clone (Observed, ledger `2e762dd`, about 02:28 EDT):** restore + verify_release_0390 passed (chain 7 links, 1 authorization exception); run_tests_0390 passed 5 modules, 36 tests (scratch output). Release notes written fresh from GATES_042.
  - **Deviations:** #157 (pre-run), #158 (post-run: reference path error before any check, interrupted commit chain, next step vs next_if_pass).
  - **Chain:** plan `c5cf6bd` -> erratum `29ef4d5` -> authorization `2c1ed4b` -> seedcheck `8247cf7` -> A16 `fa3da46` -> common/runner `0f4a56a` -> recount `9cd9409` -> reference `e5af6e0` -> gates `4cfd873`/`8445e48` -> tooling `538622b`..`c8eedf1`/`d708dea` -> tests `da9a212` -> pre-freeze smoke `e6ea45d` -> #157 `6ef93ad` -> freeze `4af660b` -> run start `405f17b` -> seal `719953c` -> recount `ca43ced` -> reference `6af5717` -> tests `f33750b` -> gates `d774d8c` -> #158 `4302227` -> RELEASE.json and docs `e657553`.
  - **No CI:** no `.github`, no workflows. The `brute-bridge` worktree and BGR-v0.90.0 were not touched.

<!-- V0380 -->
- **v0.38.0: RELEASED** (previous) 2026-10-31 (EDT), https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.38.0 (tag v0.38.0 -> e33a542, ledger release_041). Built on branch `plan/v0.38.0` (BRUTE_PLAN_041, ENCODING AUDIT; LEAN; STANDING GO t133s553, build authorization ledger `55c87e4`). Next: BRUTE_PLAN_042 (v0.39.0, plan only).
  - **Run complete (Observed).** 294/294 jobs (240 replays, 18 fresh cases), 157.4 s of 1800 s, normal exit about 00:38:28 EDT, run once; 1 checkpoint snapshot (`2b71565`); nothing relaunched; resume clause not approved, not used. Hard per-call cap: 15 kills, max call 10.012 s. Box clock about 10 s ahead of GitHub's Date header at 00:35 EDT.
  - **PASS (8/13):** GAUD_loc (fixed-colour clique: E2 loses the GINC15 decisions 3/3 repeats, E1 matches A14 3/3), GAUD_stab (10/10 [0.72, 1.00]), GAUD_time (E3/E0 mean 16.11 [5.13, 31.74]), GQB16, GS_ref (E1/E2 part c, 20 decided, 0 mismatches, 20/20 mutations), GTI, G_PROC, G_RT. **FAIL:** G_recount (25 AMB replays not covered by the frozen recount), GAUD_sem, G10, G_sound (each requires the recount; own conditions hold), GPERM16 (10/11 [0.62, 0.98], 10710005).
  - **Deviations:** #154 (pre-run), #155 (post-run), #156 (release-time: the frozen verify_release_0380 fails its commit-order item because the build authorization names the plan it authorizes; verify with the addendum verify_release_0380a).
  - **Fresh clone (Observed, ledger b4d4ec8, about 01:29 EDT):** restore + verify_release_0380a passed; run_tests_0380 passed (scratch output). The release notes were first published from a stale notes file and corrected with gh release edit about 01:26 EDT.
  - **Soundness (Observed):** 0 WRONG, 0 unsound separating words of 21 (study and recount), 0 truth inconsistencies, controls 6/6 ID in every arm; G10 and G_sound fail only because they require G_recount.
  - **Chain:** plan `18cc782` -> seedcheck `ada2447` -> authorization `55c87e4` -> encaudit16 `2317f61` -> proxy `a647be6` -> common `5bb6385` -> runner `e34a624` -> tests `fd0a628` -> recount `8e46c45` -> reference `2839145` -> test runner `cb5e04f` -> gates `5041256` -> tooling `27f9c6f`/`4dd310c`/`bb26a0c`/`7fccafc`/`0f2febb` -> pre-freeze smoke `bb29ed4` -> #154 `27e70eb` -> freeze `a649dd2` -> run start `a24ceb5` -> seal `5221d1c` -> recount `d9e27fd` -> reference `2fcb46c` -> tests `4aaab70` -> gates `40d1484` -> #155 `67371f6` -> RELEASE.json and docs `c478ea1`.
  - **No CI:** no `.github`, no workflows. The `brute-bridge` worktree and BGR-v0.90.0 were not touched.

<!-- V0370 -->
- **v0.37.0: RELEASED** (previous) 2026-10-31 (EDT) as tag `v0.37.0` (annotated `70f53e9` -> `1026db1`, https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.37.0). main was fast-forwarded `9bcddc4..1026db1`. A fresh clone of the tag restored, verified (commit chain 6) and ran 11 test modules (77 tests): 10 ok, test_scalesearch15_0370 fails the same 3 GINC15 checks as the official suite, with the test output on its scratch default; ledger `82ecd12`. Built on branch `plan/v0.37.0` (BRUTE_PLAN_040, APARTNESS + CUBE; LEAN; STANDING GO t133s553, build authorization ledger `43b9592`). Next: BRUTE_PLAN_041 (v0.38.0 encoding audit, plan only).
  - **Run complete (Observed).** 42/42 cases, 126/126 jobs, 374.1 s of 1800 s, normal exit about 23:43:37 EDT 2026-10-30, run once. 2 checkpoint snapshots were pushed (`66b9a3a`, `c2f4f3a`). Nothing was relaunched. The resume clause was NOT approved and was not needed. The agent session was interrupted while the reference audit ran; the audit finished on its own, was checked complete and committed as is, not rerun (#153 item 2). Pre-freeze projection 391.6 s; no runtime amendment. The box clock read about 10 s ahead of GitHub's Date header at 00:00:34 EDT.
  - **PASS (7/12):** GREP15 (scale14 A15_cube 9 vs A14 9 [0.47, 0.91]), G_sound (1019 words, 0 unsound), G10, GS_ref (A15_cube scale14: 9 decided, 3 not reached, 123 verdicts, 0 mismatches, mutations 20/20), G_PROC, G_RT (374.1 s), G_recount. **FAIL:** GC15_headline (a passes; b passes: ID+IDF(A15_cube, scale16) 7/12 [0.32, 0.81]; c: ID(A15_cube) - ID(A14) scale16 +0.083 [-0.167, 0.333]; d: capped cases 9/12 [0.47, 0.91]), GFAM15 (lowobs12 0/12 [0, 0.24], exercised), GINC15 (3/60 sealed 039 checks unknown where A14 decided), GQB15 (max 11.014 s, A15_cube lowobs12 10630011), GTI (test_scalesearch15_0370 fails on the GINC15 cases; 11 modules, 77 tests). Secondary GCAP15, GSYM15 reported only.
  - **Headline numbers (Observed).** scale16: A15_cube 3/4/0/0/5; A15 1/2/0/0/9; A14 2/2/0/0/8. scale14: A15_cube = A14 8/1/0/0/3; A15 6/1/0/0/5. lowobs12: IDU 12 for every arm. Controls ID 6/6 for every arm.
  - **Mechanism (Observed / Inferred).** The cube split rescued 4 capped scale16 cases (153 cube calls: 0 SAT, 144 UNSAT, 9 capped); the encoding without it lost 2 A14 decisions (10610003, 10610007). Plan 040 branches fire: GINC15 failed, so v0.38.0 is an encoding audit, not a new arm; GFAM15 failed while b passed, so the gain is family-specific.
  - **Deviations:** #152 (pre-run), #153 (post-run).
  - **Chain:** plan `401172b` -> authorization `43b9592` -> seedcheck `7d4317b` -> scalesearch15 `349a77b` -> worlds `69eaf29` -> common `117af5e` -> runner `aba4b63` -> tooling `a1e9563`/`c01b646`/`67d3960` -> tests `610a592`/`7c51f35` -> pre-freeze smoke `d80c798` -> #152 `06c41d0` -> freeze `9001029` -> run start `f0cf26d` -> seal `b1da397` -> recount `68bda8d` -> reference `fc93389` -> tests `1a092da` -> gates `bfae53d` -> #153 `798a93e` -> RELEASE.json and docs `39e86b4`.
  - **No CI:** no `.github`, no workflows. The `brute-bridge` worktree and BGR-v0.90.0 were not touched.

<!-- V0360 -->
- **v0.36.0: RELEASED** (previous) 2026-10-30 as tag `v0.36.0` (annotated `d099b5d` -> `f7f7d0d`, https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.36.0). main was fast-forwarded `8cd2eda..f7f7d0d`. A fresh clone of the tag restored, verified (commit chain 6) and passed 10/10 test modules (70 tests) with the test output on its scratch default; ledger `b3f53ee`. Built on branch `plan/v0.36.0` (BRUTE_PLAN_039, CLEAN SCALE; LEAN; STANDING GO t133s553, build authorization ledger `0f90554`).
  - **Run complete (Observed).** 54/54 cases, 162/162 jobs, 309.6 s of 1800 s, normal exit about 22:41:47 EDT, run once. 2 checkpoint snapshots were pushed (`0d20c04`, `963501f`). Nothing was relaunched. The resume clause was NOT approved and was not needed. Pre-freeze projection 312.1 s; no runtime amendment. The box clock read about 7 s ahead of GitHub's Date header at 22:56:00 EDT.
  - **PASS (12/13):** GFAM14 (perm12 A14 12/12 [0.76, 1]), GREP14 (scale12 12 vs A9 11), GCH14 (+0.292 [0.125, 0.458]), GINC14 (36 sealed 034 cases, 307 verdicts, 0 mismatches), GQB14 (max 9.563 s), G_sound (743 words, 0 unsound), G10, GS_ref (A14 scale14: 8 decided, 4 not reached, 114 verdicts, 0 mismatches, mutations 20/20), GTI (10 modules, 70 tests), G_PROC, G_RT, G_recount. **FAIL:** GC14_headline (a passes; b: ID+IDF(A14, scale16) 0/12 [0, 0.24]; c: ID(A14) - ID(A9) scale16 -0.083 [-0.25, 0]; d passes: scale14 8/12 [0.39, 0.86]). Secondary GK14, GACT14 reported only.
  - **Headline numbers (Observed).** scale16: A14, A14_k64 IDU 12 (all capped); A14_random 0/0/4/0/8; A9 1/0/0/0/11. scale14: A14 = A14_k64 = A9 7/1/0/0/4; A14_random 0/0/10/0/2. scale12: A14 10/2/0/0/0; A14_k64 and A9 9/2/1/0/0; A14_random AMB 12. perm12: A14 ID 12 (0.67 extra actions on average). Controls ID 6/6 for every arm.
  - **Mechanism (Observed / Inferred).** Every A14 scale16 case stopped 'unknown' with the n = 16 rival query at the 9 s cap and K_spent 0. Plan 039 branches fire: caps dominant (v0.37.0 tests a per-size cube split / symmetry-free fixed-start encoding) and 14 states is the current ceiling. perm12 was nearly passive; a harder second family is Open.
  - **Deviations:** #150 (pre-run), #151 (post-run).
  - **Chain:** plan `d2ebf63` -> authorization `0f90554` -> seedcheck `a7212f9` -> release tooling `46a8a0c`/`24f3e4c` -> freeze tooling `cc1acdf` -> gates fix `02e7a20` -> script tests `a1fdafe` -> pre-freeze smoke `3979ecb` -> #150 `cc0a495` -> freeze `afc8eff` -> run start `aef5112` -> seal `44f79e3` -> recount `879d6ac` -> reference `cd54bae` -> tests `66c8652` -> gates `12ab5d2` -> #151 `12815da` -> RELEASE.json and docs `40caebc`.
  - **No CI:** no `.github`, no workflows. The `brute-bridge` worktree and BGR-v0.90.0 were not touched.

<!-- V0350 -->
- **v0.35.0: RELEASED** (previous) 2026-10-30 as tag `v0.35.0` (annotated `c1fda2b` -> `4d4c3e3`, https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.35.0). main was fast-forwarded `eefc66c..4d4c3e3`. A fresh clone of the tag restored, verified (commit chain 6) and passed 9/9 test modules (64 tests) with the test output on its scratch default; ledger `1b74a12`. Built on branch `plan/v0.35.0` (BRUTE_PLAN_038, INCREMENTAL LEAST-B; LEAN; STANDING GO t133s553, build authorization ledger `bbda857`).
  - **Run complete (Observed).** 42/42 cases, 451.0 s of 1800 s, normal exit 21:48:03 EDT, run once. 2 checkpoint snapshots were pushed (`9d59f40`, `f4d4b79`). The agent session was interrupted while polling after the run had finished; nothing was relaunched (#149 item 2). The resume clause was NOT approved and was not used. The box clock read about 7 s ahead of GitHub's Date header at 22:00:36 EDT.
  - **PASS (10/12):** GSAFE13 (Exact: sealed 036 WRONG trace AMB under confirm13, same as A12), GINC13 (13/13 sealed 037 reference items, 0 mismatches), GQB13 (max 9.711 s, S7), G_sound (999 words, 82 from confirmations, 0 unsound), G10, GS_ref (343 decided, 322 at raised B, 25 confirmation items, 0 mismatches, mutations 20/20), GTI (9 modules, 64 tests), G_PROC, G_RT, G_recount. **FAIL:** GR13_headline (a passes; b: IDU(A12_r3) - IDU(A13_r3) noisy12 0.00 [0, 0]; c: ID+IDF(A13_r5) 1/12 [0.01, 0.35]; d: capped-confirmation cases A13_r5 clean12 8/12 [0.39, 0.86]), GNR13 (18 clean12 label differences against A11_r3). Secondary GH2 (36 vs 34, bar 6) and GPR13 (11 vs 10 capped probes) fail.
  - **Headline numbers (Observed).** noisy12: A13_r5 1/0/0/0/11; A13_r3, A12_r5, A12_r3, A11_r3, S7 IDU 12. noisy8: A13_r5 = A12_r5 2/8/1/0/1; A13_r3 IDU 12. clean12: A13 and A12 arms 0/0/3/0/9; A11_r3 7/1/3/0/1. Controls ID 6/6 for every arm.
  - **Mechanism (Observed / Inferred).** Every clean12 B_max confirmation that ran hit the 9 s cap (8/8 per A13 arm), as the pre-freeze smoke had shown (#148 item 11). Incremental reuse did not reduce capped probes. Plan 038's MaxSAT branch fires on b and d; per the owner (21:48 EDT) v0.36.0 pivots instead to the clean B = 0 line toward 16 states plus a second world family; noise at 12 states and MaxSAT stay Open.
  - **Deviations:** #148 (pre-run), #149 (post-run).
  - **Chain:** plan `e070773` -> authorization `bbda857` -> seedcheck `12d0fde` -> A13 `1796a72` -> runner `f294fbf`/`1fb01fc` -> recount `c0851ac` -> reference `a44fe94` -> gates `fd455a3` -> release tooling `901acf8` -> pre-freeze smoke `54d49a2` -> #148 `97447a1`/`ee78778`/`91bc6df` -> freeze `e5f45a0` -> run start `6000c37` -> seal `b78314c` -> recount `bbb3111` -> reference `37024f1` -> tests `53fba90` -> gates `bbd1023` -> #149 `4f64c6b` -> RELEASE.json `96da542` -> docs `1454b5f`.
  - **No CI:** no `.github`, no workflows. The `brute-bridge` worktree and BGR-v0.90.0 were not touched.

<!-- V0340 -->
- **v0.34.0: RELEASED** (previous) 2026-10-30 as tag `v0.34.0` (annotated `6593ee9` -> `ce937d9`, https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.34.0). main was fast-forwarded `94bd491..ce937d9`. A fresh clone of the tag restored, verified (commit chain 6) and passed 8/8 test modules (57 tests) with the test output on its scratch default; ledger `7318c5a`. Built on branch `plan/v0.34.0` (BRUTE_PLAN_037, SOUND NOISY STOP; LEAN; STANDING GO t133s553, build authorization ledger `b789fb9`).
  - **Run complete (Observed).** 42/42 cases, 443.1 s of 1800 s, normal exit, run once. 2 checkpoint snapshots were pushed (`4bb4b36`, `e2b381c`). Nothing was relaunched. The resume clause was NOT approved and was not needed. The box clock read about 5 s ahead of GitHub's Date header at 20:39:09 EDT.
  - **PASS (9/11):** GSAFE12 (Exact: sealed 036 WRONG trace now AMB), GQB12 (max 10.332 s), G_sound (678 words, 0 unsound), G10, GS_ref (240 decided, 225 at raised B, 54 confirmation items, 0 mismatches, mutations 20/20), GTI (8 modules, 57 tests), G_PROC, G_RT, G_recount. **FAIL:** GR12_headline (a passes; b: IDU(A11_r3) - IDU(A12_r3) noisy12 0.00 [0, 0]; c: ID+IDF(A12_r5) 0/12; d: ID(A12_r5) - ID(A11_r5) -0.42 [-0.67, -0.17]), GNR12 (20 clean12 label differences: B_max confirmation capped). Secondary GPR12 passes.
  - **Headline numbers (Observed).** noisy12: A12_r5 0/0/1/0/11; A12_r3 0/0/0/0/12; A12_r3_nostop 1/0/0/0/11; A11_r3 0/0/0/0/12; A11_r5 5/0/1/0/6; S7 IDU 12. noisy8: A12_r5 4/7/0/0/1. clean12: A12_r5 and A12_r3 0/0/1/0/11; A12_r3_nostop = A11_r3 8/2/1/0/1. Controls ID 6/6 for every arm.
  - **Mechanism (Observed / Inferred).** The B_max confirmation (one SAT query over n = 1..N) hit the 9 s cap on 10/12 clean12 cases even at least B 0; the least-B chain still capped on every noisy12 A12_r3 case (first probe capped 6/12, down from 12/12). Plan 037's b branch fires: v0.35.0 tests an incremental totalizer / MaxSAT least-B solve.
  - **Deviations:** #146 (pre-run), #147 (post-run) and its erratum.
  - **Chain:** plan `de168d1` -> authorization `b789fb9` -> seedcheck `18b3e90` -> A12 `20f8fd8` -> runner `4dfb973` -> recount `4eff368` -> reference `d82e850` -> gates `19d737c`/`4dc608a` -> release tooling `5d85377` -> pre-freeze smoke `726c7c6` -> #146 `eb34849`/`fbd6865` -> freeze `d9402a1` -> run start `730e9b3` -> seal `116e9e9` -> recount `794e56d` -> reference `d1b5860` -> tests `57d5da4` -> gates `15c64a1` -> #147 `ac0d829` -> erratum `a994746` -> RELEASE.json `96776d2` -> docs `76bbd90`.
  - **No CI:** no `.github`, no workflows. The `brute-bridge` worktree and BGR-v0.90.0 were not touched.

<!-- V0330 -->
- **v0.33.0: RELEASED** (previous) 2026-10-30 as tag `v0.33.0` (annotated `b797b0e` -> `f96c738`, https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.33.0). main was fast-forwarded `0e52483..f96c738`. A fresh clone of the tag restored, verified (commit chain 6) and passed 7/7 test modules (48 tests); ledger `77845a8`. Built on branch `plan/v0.33.0` (BRUTE_PLAN_036, REPEATED READS; LEAN; STANDING GO t133s553, build authorization ledger `ed8452b`).
  - **Run complete (Observed).** 48/48 cases, 420.3 s of 1800 s, normal exit, run once. 3 checkpoint snapshots were pushed (`43b5e2f`, `21fdeca`, `0bfe2b7`). Nothing was relaunched. The resume clause was NOT approved and was not needed. The box clock read about 7 s ahead of GitHub's Date header at 19:58:35 EDT.
  - **PASS (8/11):** GNR11, G_sound (674 words, 0 unsound), G10, GS_ref (88 decided, 75 at raised B, 0 mismatches, mutations 20/20), GTI (7 modules, 48 tests), G_PROC, G_RT, G_recount. **FAIL:** GR11_headline (a: A11_r3 WRONG 1 on noisy_scale8 10210002; b: ID(A11_r3) - ID(A10) noisy12 +0.17 [0, 0.42]; c: ID+IDF 2/12; d: IDU 10/12), GBIS11 (IDU 10 vs 9 for the upward ablation), GQB11 (A11_r3_up 10.513 s). Secondary GRB11 fails.
  - **Headline numbers (Observed).** noisy12: A11_r3 2/0/0/0/10; A11_r5 4/1/2/0/5; A11_r3_up 3/0/0/0/9; A10 and S7 IDU 12; S5 WRONG 12. noisy8: A11_r5 ID 8/12 [0.39, 0.86]. clean12: every A11 arm equals A10 (6/3/2/0/1). Controls ID 6/6 for every arm.
  - **Mechanism (Observed / Inferred).** The majority cut the truth's flips to 0-5, but the first bisection probe at B_max = 6 hit the 9.5 s cap on 9 of 10 A11_r3 IDU cases. The WRONG stopped at least B 1 below the truth's 2 flips. Per the plan, v0.34.0 is a diagnose plan.
  - **Deviations:** #144 (pre-run) and #145 (post-run).
  - **Chain:** plan `3ab989d` -> authorization `ed8452b` -> seedcheck `0a9ae7c` -> A11 `9b5260c` -> runner `528a47d` -> recount `5ce8af9` -> reference `fe4d776` -> gates `fb7825d` -> release tooling `58fe718` -> pre-freeze smoke `34456cb` -> #144 `f095643` -> freeze `730aef4` -> run start `e972a23` -> seal `d89c1ea` -> recount `40f009d` -> reference `faaf741` -> tests `088da1e` -> gates `bff753f` -> #145 `7e16c0a` -> RELEASE.json `02d6dcb` -> docs `887e1cb`.
  - **No CI:** no `.github`, no workflows. The `brute-bridge` worktree and BGR-v0.90.0 were not touched.

<!-- V0320 -->
- **v0.32.0: RELEASED** (previous) 2026-10-30 as tag `v0.32.0` (annotated `a8a2316` -> `872fac2`, https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.32.0). main was fast-forwarded `9491aee..872fac2`. A fresh clone of the tag restored, verified (commit chain 8) and passed 6/6 test modules (42 tests); ledger `1bff998`. Built on branch `plan/v0.32.0` (BRUTE_PLAN_035, NOISY ACTIVE IDENTIFICATION; LEAN; STANDING GO t133s553, build authorization ledger `6941bf9`).
  - **Run complete (Observed).** 48/48 cases, 342.7 s of 1800 s, normal exit, run once. 2 checkpoint snapshots were pushed (`aafa3c7`, `ade7093`). Nothing was relaunched. The resume clause was NOT approved and was not needed. The session was interrupted after the run, before the reference commit; REFERENCE_035.json was complete and was committed without a rerun (#143 item 2). The box clock matched GitHub's Date header at 19:04:42 EDT.
  - **PASS (9/11):** GNR10, GAD10, G_sound (116 words, 0 unsound), G10, GS_ref (12/12 decided, 0 mismatches, mutations 20/20), GTI (6 modules, 42 tests), G_PROC, G_RT, G_recount. **FAIL:** GA10_headline (a: S5 WRONG 15 on noisy; b: ID(A10) - ID(S7) noisy12 0.00 [0, 0]; c: ID+IDF 0/12; d: IDU 12/12), GQB10 (S7 10.538 s; bound 10.5 s). Secondary G16 fails (A10 ID 0/6).
  - **Headline numbers (Observed).** noisy12 and noisy8: A10, A10_fixed and S7 IDU 12/12 [0.76, 1] each; A9 WRONG 12/12 on both; S5 WRONG 9 (noisy12) and 6 (noisy8). clean12: A10 = A9 ID 7/12 [0.32, 0.81], IDF 4, AMB 1, WRONG 0; A10_fixed and S7 IDU 12; S5 AMB 12. GAD10 clean12 +0.58 [0.33, 0.83]. Controls ID 6/6 for every arm.
  - **Mechanism (Observed / Inferred).** On all 24 noisy cases B = 0 was UNSAT, then the upward least-budget search hit the 10 s cap after 9-12 queries, below the true flip count (13-23), so B stayed 0 and A10 stopped IDU. The UNSAT proofs just below the least B are the hard queries (Inferred). Per the plan's next_if_fail, v0.33.0 is a diagnose plan.
  - **Deviations:** #142 (pre-run) and #143 (post-run).
  - **Chain:** plan `a66b74a` -> authorization `6941bf9` -> seedcheck `154d4c9` -> A10 `984f653` -> runner `be50919` -> recount `5d55043` -> reference `57a44b3` -> gates `cf6788f` -> release tooling `9441ba5` -> pre-freeze smoke `dc8b99c` -> #142 `f8d4b6d` -> freeze `1764462` -> run start `3588e27` -> run end `10f47c4` -> seal `6ea1450` -> recount `bf38714` -> reference `3cce54f` -> tests `0f1b0d7` -> gates `76a0ddf` -> #143 `f190bd5` -> RELEASE.json `1767081` -> docs `c20aa14`.
  - **No CI:** no `.github`, no workflows. The `brute-bridge` worktree and BGR-v0.90.0 were not touched.

<!-- V0310 -->
- **v0.31.0: RELEASED** (previous) 2026-10-30 as tag `v0.31.0` (annotated `819b0d5` -> `4093709`, https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.31.0). main was fast-forwarded `3740ace..4093709`. A fresh clone of the tag restored, verified (commit chain 6) and passed 5/5 test modules (34 tests); ledger `1b8da7f`. Built on branch `plan/v0.31.0` (BRUTE_PLAN_034, SOUND ACTIVE IDENTIFICATION; LEAN; STANDING GO t133s553, build authorization ledger `b84deba`).
  - **Run complete (Observed).** 36/36 cases, 124.8 s of 1800 s, normal exit, run once. 1 checkpoint snapshot was pushed (`ffdb5b5`). Nothing was relaunched. The resume clause was NOT approved and was not needed. The box clock read about 9 s ahead of GitHub's Date header at 18:05:34 EDT, with no stall.
  - **PASS (11/12):** GA9_headline (a-d), GDIAG8, GIDF9, GCH9, G_sound, G10, GS_ref, GTI (5 modules, 34 tests), G_PROC, G_RT, G_recount. **FAIL:** GQB9 (A9 max query 10.888 s; bound 10.5 s).
  - **Headline numbers (Observed).**
    - 12 states: A9 ID 9/12 [0.47, 0.91], IDF 1, AMB 1, WRONG 0, IDU 1. A9_random ID 0/12 (AMB 11, IDU 1). A8 ID 8/12 (WRONG 1). S5 ID 0/12 (AMB 12). S1 ID 0/12 (AMB 11, IDU 1).
    - Paired ID(A9) - ID(S5) +0.75 [0.50, 1.00]; ID(A9) - ID(A9_random) +0.75 [0.50, 1.00].
    - WRONG: A9 0/36; A8 2/36, both below the truth's size (GDIAG8).
    - 407 separating words re-simulated, 0 unsound.
  - **Deviations:** #140 (pre-run) and #141 (post-run; it also corrects the run_end note's "about 4 min" to about 2 min).
  - **Chain:** plan `52b50be` -> authorization `b84deba` -> seedcheck `3426af5` -> A9 `211f9b7` -> runner `8ddfe0b` -> recount `1649b71` -> reference `604a6d2` -> gates `eb6b61d` -> tooling `f78c07a` -> release tooling `9480b23` -> pre-freeze test `96e54de` -> #140 `7f19efd` -> freeze `389e837` -> run start `5ab16bd` -> seal `adb8563` -> gates `b630337` -> #141 `c2f5094` -> RELEASE.json `1193bea` -> docs `9d8e813`.
  - **No CI:** no `.github`, no workflows. The `brute-bridge` worktree and BGR-v0.90.0 were not touched.

<!-- V0300 -->
- **v0.30.0: RELEASED** (previous) 2026-10-30 as tag `v0.30.0` (annotated `b386465` -> `bcecd4c`, https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.30.0). main was fast-forwarded `5a9854f..bcecd4c`. A fresh clone of the tag restored, verified and passed 4/4 test modules (27 tests). (BRUTE_PLAN_033, ACTIVE EXPERIMENTS; LEAN; STANDING GO t133s553, build authorization ledger `cf62a8c`).
  - **Run complete (Observed).** 36/36 cases, 116.0 s of 1800 s, normal exit, run once. 1 checkpoint snapshot was pushed (`4b67a3b`). Nothing was relaunched. The resume clause was NOT approved and was not needed. The box clock matched GitHub's Date header (0 s at 17:09:41 EDT).
  - **PASS (9/10):** GCH8, G_sound, G10, GS_ref, GQB8 (max query 10.24 s), GTI (4 modules, 27 tests), G_PROC, G_RT, G_recount. **FAIL:** GAE8_headline (a: WRONG 5; c: ID 5/12; b and d pass).
  - **Headline numbers (Observed).**
    - 12 states: A8 ID 5/12 [0.19, 0.68], AMB 3, WRONG 4, IDU 0; A8_random, S5 and S1 ID 0/12, AMB 12/12.
    - Paired ID(A8) - ID(S5) +0.417 [0.167, 0.667]; ID(A8) - ID(A8_random) +0.417 [0.167, 0.667].
    - A8 extra actions at 12 states: mean 17.4 (11.2 on ID cases), max 38 of K = 64.
    - Separation soundness: 109 words re-simulated, 0 unsound; truth consistent on every round.
  - **Mechanism (Inferred).** Every WRONG stopped 'unique' below the truth's size (uniqueness at n_min is not identification). All 8 'indistinguishable' stops are same_future (start-state ambiguity).
  - **Deviations:** #138 (pre-run) and #139 (post-run).
  - **Chain:** plan `af07e35` -> authorization `cf62a8c` -> seedcheck `0e8bb67` -> A8 `fa0c690` -> runner `8661d42` -> recount/reference `51317f4` -> gates `1b7c264` -> tooling `23c033a` -> release tooling `c3e6f05` -> smoke fix and pre-freeze test `8b23acf` -> #138 `ac26d3c` -> freeze `09afb81` -> run start `9970615` -> seal `9b50062` -> gates `b3d604b` -> #139 `2c5f225` -> RELEASE.json `bfc65f0` -> docs `28cc77d`.
  - **No CI:** no `.github`, no workflows. The `brute-bridge` worktree and BGR-v0.90.0 were not touched.

<!-- V0290 -->
- **v0.29.0: RELEASED** (previous) 2026-10-30 as tag `v0.29.0` (`4429c6e`, https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.29.0). main was fast-forwarded. A fresh clone of the tag restored, verified and passed 5/5 test modules on branch `plan/v0.29.0` (study BRUTE-0290-ROBUST-PERCEPTION-032, LEAN, standing go t133s553, build authorization ledger `7d4242f`)
  - **Run complete (Observed).** 48/48 cases, 1246.3 s of 1800 s, normal exit. 5 checkpoint snapshots were pushed (last `0ec1f9b`). Nothing was relaunched. The resume clause was NOT approved and was not needed. The box clock was checked against the GitHub Date header 10 times and did not stall (#137 item 3).
  - **PASS (6/9):** GQB7 (S7 max query 9.35 s), GS_ref (0 mismatches, mutations 20/20), GTI (5/5 modules), G_PROC, G_RT, G_recount. **FAIL:** GRP7_headline (d; a, b, c and e pass), GNR7, G10.
  - **Headline numbers (Observed).**
    - U_inf at noisy 12 states: S7 0.467 [0.437, 0.499], S7_contra 0.673, S5 0.576 [0.542, 0.609], S1 0.644 [0.560, 0.749]. Paired S7 - S5 -0.109 [-0.154, -0.054]; S7 - S1 -0.178 [-0.283, -0.084].
    - X_inf at noisy 12 states: 0/12 for every arm (bar 3/12).
    - Clean 12 states: U(S7) - U(S5) +0.362 [0.348, 0.377]. Controls: S7 U 0.085, with 0/6 finished.
    - F_truth: S7 0, S7_contra 0, S5 0, S1 12. Contradiction verdicts: S1 4, S7_contra 3, S5 0, S7 0.
  - **Mechanism (Inferred).** The fixed budget (B_end 27) applies on clean traces too, so S7 searches a wider space.
  - **Deviations:** #136 (pre-run) and #137 (post-run).
  - **Chain:** plan `5a00625` -> authorization `7d4242f` -> seedcheck `cad2416` -> S7 `47e3006` -> runner `d2eeb34` -> tooling `7885e02` -> release tooling `6143c15` -> pre-freeze test `7429720` -> #136 `b0c86e9` -> freeze `fd17c82` -> run_start `fb5519c` -> run_end `c67472e` -> seal `cbc801e` -> recount `9975157` -> reference `6e4684b` -> tests `39e671a` -> gates `7c4d197` -> #137 `86ffb89` -> RELEASE.json `9c091a2` -> docs `d080911`.
  - **No CI:** no `.github`, no workflows. The `brute-bridge` worktree and BGR-v0.90.0 were not touched.

<!-- V0280 -->
- **v0.28.0: RELEASED** (previous) 2026-10-30 as tag `v0.28.0` (annotated `7b59641` -> `1131c8f`), main fast-forwarded `b917b4c..1131c8f`, https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.28.0. A fresh clone of the tag passed restore, verify_release_0280 and run_tests_0280 (7/7 modules; ledger `7cc6dbb`). Released (study BRUTE-0280-SIXTEEN-STATE-ID-031, LEAN, standing go t133s553, build authorization ledger `4a0eb8d`)
  - **Run complete (Observed).** 54/54 cases, 1028.1 s of 1800 s, normal exit. 4 checkpoint snapshots were pushed (last `6131470`). Nothing was relaunched. The resume clause was NOT approved and was not needed.
  - **PASS (6/9):** G10 (6/6 controls), GS_ref (mutations 20/20), GTI (7/7 modules; 67 counted tests, all OK), G_PROC, G_RT, G_recount. **FAIL:** GSC6_headline (b and c; a and d pass), GID6 (b; a and c pass), GQB6 (10.857 s on one stress case; bound 10.5).
  - **Headline numbers (Observed).**
    - U at 16 states: S6 0.222 [0.158, 0.288], S6_noorder 0.226, S5 0.218 [0.157, 0.281], S1 0.336 [0.289, 0.381]. Paired S6 - S5 +0.004 [-0.008, 0.016] (bar -0.06).
    - X at 8/12/16 states: S6 12/12, 6/12, 0/18; S5 12/12, 6/12, 0/18; S1 11/12, 2/12, 0/18.
    - Identify probe at 12 states: S6 ID 0/12, AMB 11/12, NR 1/12; WRONG 0 for every arm.
    - F: 0 for all arms, main and stress. Stress U: S1 0.370, S5 0.568, S6 0.568.
  - **Mechanism (Inferred).** S6 removed build cost but hit the per-query cap more (cap stops per scale16 case 45.8 vs 1.3), so solve time did not fall. AMB comes from unexercised truth transitions in the traces.
  - **Deviations:** #134 (pre-run) and #135 (post-run).
  - **Chain:** plan `ec7bd75` -> authorization `4a0eb8d` -> seedcheck `059fe1a` -> runner `2a3790b` -> tooling `3688135` -> release tooling `76d3476` -> diag `f4bd80e` -> pre-freeze test `f48aac0` -> #134 `fd80635` -> freeze `e74469a` -> run_start `1ba5397` -> run_end `e27bde1` -> seal `b3b8519` -> recount `5877d4d` -> reference `4f2c9fc` -> tests `6afab8f` -> gates `604d19c` -> #135 `d086433` -> RELEASE.json `435280f` -> docs `91b48d5`.
  - **No CI:** no `.github`, no workflows. The `brute-bridge` worktree and BGR-v0.90.0 were not touched.

<!-- V0270 -->
- **v0.27.0: RELEASED** (previous) 2026-10-30 as tag `v0.27.0` (annotated `77c5b08` -> `9cf2969`), main fast-forwarded `91f2406..9cf2969`, https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.27.0. A fresh clone of the tag passed restore, verify_release_0270 and run_tests_0270 (6/6 modules; ledger `fae4f59`). Released (study BRUTE-0270-SYMMETRY-FREE-030, LEAN, standing go t133s553, build authorization ledger `30ccd58`)
  - **Run complete (Observed).** 51/51 cases, 978.9 s of 1800 s, normal exit. 4 checkpoint snapshots were pushed (last `189826c`). The host interrupted the agent at 14:47 EDT, after the run had ended; nothing was rerun. The resume clause was NOT approved and was not needed.
  - **PASS (8/8):** GQB5 (S5 max query 8.52 s), GSC5_headline (a-d), G10 (6/6 controls), GS_ref (mutations 20/20), GTI (55 tests run, 54 counted, all OK), G_PROC, G_RT, G_recount. **FAIL:** none.
  - **Headline numbers (Observed).**
    - U at 12 states: S5 0.047 [0.004, 0.093], S5_softcap 0.048, S4 0.172 [0.113, 0.232], S1 0.200 [0.144, 0.256]. Paired S5 - S1 -0.153 [-0.198, -0.110] (bar -0.08).
    - X at 8/12/16 states: S5 12/12, 5/12, 0/12; S1 8/12, 1/12, 0/12.
    - ID at 12 and 16 states: 0/12 for every arm; at 8 states S5 6/12.
    - F: 0 for all arms, main and stress.
  - **Ablation (Observed, descriptive).** S5_softcap equals S5 within noise, so the gain comes from removing symmetry clauses, not the hard cap.
  - **Deviations:** #132 (pre-run) and #133 (post-run).
  - **Chain:** plan `803a920` -> authorization `30ccd58` -> seedcheck `2f34fcd` -> diag `6bea49a` -> S5 `3377447` -> runner `8ded63f` -> scoring `d55b77b` -> tooling `01a7910` -> pre-freeze test `0d264d7` -> #132 `88b33d8` -> freeze `f68ac76` -> run_start `a40eeef` -> run_end `734812d` -> seal `6bbaa4f` -> recount `bf780a1` -> reference `ad0a2cb` -> tests `fb10d83` -> gates `04a4c5d` -> #133 `29d8e59` -> RELEASE.json `34b0c6a` -> docs `09bc503`.
  - **No CI:** no `.github`, no workflows. The `brute-bridge` worktree and BGR-v0.90.0 were not touched.

<!-- V0260 -->
- **v0.26.0: RELEASED** (previous) 2026-10-30 as tag `v0.26.0` (annotated `027cc5a` -> `81f8415`), https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.26.0. A fresh clone of the tag passed restore, verify_release_0260 and run_tests_0260 (6/6 modules). Released (study BRUTE-0260-QUERY-THROUGHPUT-029, LEAN, standing go t133s553, build authorization ledger `78336bd`, amendment A1 `34ce968`)
  - **Run complete (Observed).** 51/51 cases, 1345.9 s of 1800 s, normal exit. 5 checkpoint snapshots were pushed. The resume clause was NOT approved and was not needed.
  - **PASS:** G10, GAPI14 (certify/14; stream 4/4), GS_ref14 (mutations 20/20), GTI (58 tests run, all OK), G_PROC, G_RT, G_recount. **FAIL:** GSC4_headline (b and c; a and d pass), GTP, GQB.
  - **Headline numbers (Observed).**
    - U at 12 states: S4 0.161 [0.095, 0.230], S1 0.180 [0.112, 0.246], S3 0.439. Paired S4 - S1 -0.019 [-0.035, -0.006] (bar -0.08).
    - X at 12 states: S4 2/12, S1 1/12, S3 0/12.
    - Throughput S4/S1: median 1.056 (bar 2).
    - S4 max query 15.33 s (bound 10.5).
    - F: 0 for all arms.
  - **Diagnosis (Observed, descriptive).** Symmetry clauses are the main cost: S4_nosym had U 0.079 and X 6/12 at 12 states, with F 0.
  - **Deviations:** #130 (pre-run) and #131 (post-run).
  - **Chain:** plan `c06bcfe` -> authorization `78336bd` -> diag `86856da` -> A1 `34ce968` -> seedcheck `6bc7579` -> S4 `e04d202` -> runner `47d73a4` -> scoring `89f85e6` -> tooling `232e052` -> pre-freeze test `e93e3e6` -> #130 `5a775b9` -> freeze `7337c11` -> run_start `263204d` -> run_end `d1752d6` -> seal `0fb95ef` -> recount `b82ee07` -> api `448f12c` -> reference `2cf72ca` -> tests `f4a906f` -> gates `417036b` -> #131 `86c91c8` -> RELEASE.json `faedde7` -> docs `701fbbd`.
  - **No CI:** no `.github`, no workflows. The `brute-bridge` worktree and BGR-v0.90.0 were not touched.

<!-- V0250 -->
- **v0.25.0: RELEASED** 2026-10-30. Tag object `6dd318c` points to `bfda373`; main fast-forwarded `30a2c02..bfda373`; https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.25.0. Fresh-clone verify passed (verify_release_0250b, 43/43 tests) (study BRUTE-0250-SOLVER-COST-028, LEAN, standing go t133s553, build authorization `13e570c`)
  - **Run complete (Observed).** 51/51 cases, 1053.8 s of 1800 s, normal exit. 4 checkpoint snapshots were pushed. The resume-after-reboot clause was NOT approved and was not needed.
  - **PASS:** GQB (S3 max query 10.03 s), G10 (S3 0 UNKNOWN on 6/6 controls), GAPI13 (certify/13; stream 4/4), GS_ref13 (mutation 20/20), GTI (43/43), G_PROC, G_RT, G_recount. **FAIL:** GSC3_headline (b and c; a and d pass).
  - **Headline numbers (Observed).**
    - U at 12 states: S3 0.398 [0.333, 0.450], S2 0.399; paired diff -0.001 [-0.020, 0.019] (bar -0.15).
    - X(S3): 1/12, 0/12, 0/12 at 8/12/16 states.
    - False certificates: S3, S3_tight and S2 0; S1 3 (stress).
    - Clause a: 0 mismatches (15,380 vs S2).
  - **Diagnosis (Inferred).** S3 removed per-query overruns, but steps per second did not rise. More than 98% of its UNKNOWNs at 12-16 states are not run.
  - **Deviations:** #128 (pre-run) and #129 (post-run). Under #129 the frozen make_gates_028 hit a KeyError on wall-clock fields, so gates are scored by the addendum make_gates_028b and verified with verify_release_0250b.
  - **Chain:** plan `914ce05` -> authorization `13e570c` -> seedcheck `d930593` -> S3 `e5dc91f` -> certify13 `946309d` -> runner `246a591` -> scoring `48e3cf3` -> tooling `4c8add6` -> #128 `32495af` -> freeze `fb84e6a` -> run_start `c215ed5` -> run_end `b781e55` -> seal `86ae1a2` -> recount `679ab9c` -> reference `80adbd6` -> api `9214a43` -> tests `10ec8ac` -> gates `1b13aed` -> #129 `ea5b81a` -> RELEASE.json `23fbfeb` -> docs `be47753`.
  - **No CI:** no `.github`, no workflows. The `brute-bridge` worktree and BGR-v0.90.0 were not touched.

<!-- V0240 -->
- **v0.24.0: RELEASED** 2026-10-30 (tag `v0.24.0` (annotated, object `f5b7655`) -> `03f4e3f`; main fast-forwarded `7746fa1..03f4e3f` (no force); https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.24.0; one fresh GitHub clone of the tag passed restore + verify_release_0240 + 27 unit tests; study BRUTE-0240-SCALE-REPLAY-027, LEAN, standing go t133s553, build authorization `e55a639`)
  - **Run complete (Observed).** 93/93 cases, 1454.3 s of 1800 s, normal exit. 5 checkpoint snapshots were pushed. The resume-after-reboot clause was NOT approved and was not needed.
  - **PASS:** GAPI12 (6/6 stream equal), GS_ref12 (mutation 20/20), GTI (27/27), G_PROC, G_RT, G_recount. **FAIL:** GSC_headline (b, c and e; a and d pass) and G10 (control UNKNOWNs at eps 0.02).
  - **X (Wilson 95% CI), main block:**
    - S1: 9/24, 1/24, 2/24 at 8/12/16 states.
    - S2: 3/24 [0.043, 0.310], 0/24 [0, 0.138], 0/24 [0, 0.138].
    - S2_tight (eps 0, informational): 9/12, 0/12, 0/12.
    - U(S2, scale16) 0.590.
  - **Recovery and soundness.**
    - scale8 eps-0 ID: S2 1/12 [0.015, 0.354]; S2_tight 4/12 [0.138, 0.609].
    - Clause a: 24,568 compared, 0 mismatches.
    - False certificates: S2 0, RGB6 0, S2_tight 0, S1 3.
  - **Diagnosis (Inferred, `results/study-027/DIAGNOSIS_027.json`).** At 12-16 states:
    - over 99% of UNKNOWNs are not run (arm deadline);
    - n_lo stalls below n;
    - single support calls exceed the 10 s budget (per-case max 13-19 s on average);
    - S2_tight (n_max = n) does not fix 12 states.
    - The bottleneck is solver cost per step, not the search cap.
  - **Chain:** plan `9f49ab1` -> authorization `e55a639` -> seedcheck `4e00fad` -> code + #126 `5d924b7` -> scoring `0da7e3f` -> tooling `d99a930` -> freeze `5261f4e` -> run_start `d119d25` -> run_end `0952c8f` -> seal `32eb7d9` -> recount `d817f28` -> reference `13d6af1` -> tests `fd472dd` -> api `71db876` -> gates `f8167f1` -> #127 `d66b54c` -> RELEASE.json `e118656` -> docs `448e215`.
  - **No CI:** no `.github`, no workflows. The `brute-bridge` worktree and BGR-v0.90.0 were not touched.
  - **Next:** the v0.25.0 plan (`BRUTE_PLAN_028`) targets solver cost per step. Plan only.

<!-- V0230 -->
- **v0.23.0: RELEASED** 2026-10-30 (tag `v0.23.0` (annotated, object `1b398de`) -> `ddffd12`; main fast-forwarded `c750fef..ddffd12` (no force); https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.23.0; one fresh GitHub clone of the tag passed `verify_release_0230` and 27/27 tests). Study BRUTE-0230-SCALE-026, LEAN. **2 of 8 gated pass (GTI, G_PROC).**
  - **The run was interrupted (Observed).** The box rebooted at about 10:22 EDT, about 10 minutes into the detached run. 38 of 93 cases were sealed as PARTIAL. The run was not relaunched (standing rule). See deviation #125.
  - **FAIL (INCOMPLETE_INPUT):** GSC_headline, G10, GS_ref12, G_RT, G_recount. **GAPI12 FAIL:** stream check had no scale8 case; probe, source scan and certify/11 unchanged all pass.
  - **Descriptive, 38 cases:** recount PASS (S2 0 false certificates, RGB6 0, S1 2); clause a 8771 compared, 0 mismatches; X(S2,scale16) 0/24 [0, 0.138]; U(S2,scale16) 0.566; certificates S1 14, S2 0.
  - **Chain:** plan `7a6acdd` -> authorization `835161f` -> seedcheck `234dc08` -> #123 `ccdf0df` -> S2 `b41b82d` -> scripts `f205e20` -> #124 `8d67e13` -> freeze `9837d1d` -> run_start `bc30b93` -> interrupted `e2ed8db` -> seal `fe7b757` -> gates `965879b` -> #125 `d0c82f2` -> release freeze `66d296e` -> RELEASE `d04c7b9`.
  - **Environment:** the reboot wiped /tmp (including /tmp/wt-state, not deleted by the agent) and the venv `/workspace/bgr/venv`. The venv was rebuilt from the pyproject pins.
  - **No CI:** no `.github`, no workflows. The `brute-bridge` worktree and BGR-v0.90.0 were not touched.
  - **Next:** the v0.24.0 plan (`BRUTE_PLAN_027`): a fresh-seed rerun of the 026 design with a pre-registered resume policy. Plan only; build not authorized.

<!-- V0220 -->
- **v0.22.0: RELEASED** 2026-10-30 (tag `v0.22.0` (annotated, object `5d68568`) -> `df79133`; main fast-forwarded `d9333c5..df79133` (no force); https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.22.0; one fresh GitHub clone of `plan/v0.22.0@551d60e` passed `verify_release_0220_r1` and the tests; `docs/research/v0.22.0/FRESH_CLONE_VERIFY_0220.json`). LEAN process (A2). Study BRUTE-0220-BETTING-CS-025. **11 of 12 gated pass; GBC_headline fails (c, d).**
  - **Headline GBC (betting confidence sequence RGB6, `brute.certify/11` method betting): FAIL.** Clauses a, b and e pass; c and d fail.
    - RGB6 had 0 false certificates on 40 noisy main cases and 0 on 30 stress cases at eps 0.05 (exact recount).
    - No betting level activated in any of the 90 cases. RGB6 = its level-0 bound.
    - C_late at eps 0.02: RGB6 0.315 [0.226, 0.413], RGL4 0.320, RGL5 0.332, RGNB4 0.418, oracle 0.806. dC RGB6-RGL4 -0.0045 [-0.0108, 0.0]; RGB6-RGNB4 -0.102 [-0.195, -0.015].
  - **PASS:** G_recount, GBC_lemma, GAS_frozen_control, GS_a11, GS_ref11 (90/90, mutation 20/20), GAPI11, G10, G13, GTI (lean), G_PROC (lean), G_RT (1365.8 s of 1800 s).
  - **Chain:** plan `4f6c4dd` -> authorization `b23f13c` -> A1 `1f49928` -> lemma `55dd41f` -> reference `8f31080` -> seedcheck `44db0c9` -> #119 `53ea79a` -> RGB6 code `19987c8` -> A2 `15cc245` -> process `35e4333` -> #120 `e96b3aa` -> freeze `d1390e5` -> run_start `20c1a65` -> run_end `e489213` -> #121 `30428fd` -> seal `72b52e8` -> gates `0a98405` -> tooling `be8d077` -> release freeze `b9fd583`.
  - **Deviations:** #119, #120 (pre-run), #121 (api_check t0), #122 (release verifier key).
  - **No CI:** no `.github`, no workflows. The `brute-bridge` worktree and BGR-v0.90.0 were not touched.
  - **Next:** the v0.23.0 plan (`BRUTE_PLAN_026`, SCALE: 8-16 state worlds, smarter exact search) on branch `plan/v0.23.0`, plan only; build not authorized.

<!-- V0210 -->
- **v0.21.0: RELEASED** 2026-10-29 (tag `v0.21.0` (annotated, object `73e28e7`) -> `7f30e92`; main fast-forwarded `4d4c39b..7f30e92` (no force); https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.21.0; fresh GitHub clone of `plan/v0.21.0@138ea6f` passed short, --long (GLV 12/0, 296.1 s of 900) and `tests.test_release_0210` 12 OK; `docs/research/v0.21.0/FRESH_CLONE_VERIFY_0210.json`). Study BRUTE-0210-STITCHED-LR-024. **12 of 14 gated pass; GLS and G_HB fail.**
  - **Headline GLS (stitched likelihood-ratio bound RGL5, `brute.certify/10` method stitched): FAIL.** Clauses a and e pass; b, c and d fail.
    - RGL5: 0 false certificates on 240 of 240 noisy main cases; CP95 0.0124; prefix28 identical on 120 of 120 eps 0.02 cases.
    - C_late at eps 0.02: RGL5 0.419 [0.378, 0.462]; RGL4 0.411 [0.372, 0.453]; RGNB4 0.455 [0.401, 0.509]; oracle RGN4_or 0.836 [0.802, 0.868].
    - (c) dC_late RGL5 - RGL4: +0.0076 [0.0032, 0.0128], bar mean >= 0.04. (d) dC_late RGL5 - RGNB4: -0.036 [-0.066, -0.007], bar CI lower > -0.06.
    - (b) 3 RGL5 false certificates in 1 of 30 stress cases (switch3 9020005, eps 0.05 > eps_bar 0.02; outside the attested condition). RGL4 0 on stress.
    - C_early28 at eps 0.02: RGL5 0.0043 [0.0012, 0.0082]; RGL4 0.0036; RGNB4 0.0036; oracle 0.053.
  - **FAIL: G_HB.** 2891 beats, max gap 35.829 s, 2 gaps over 10 s (clock_step 2, Inferred). The pre-run 600 s probe had 0 gaps.
  - **PASS:** G_recount, GLS_lemma, GAS_frozen_control (RGL4 CI overlaps study-023), GS_a10, GS_ref10 (mutation 20/20), GAPI10 (`brute.certify/10` new; /9 to /1 unchanged), G10, G12 (30/30), G13, GTI (K_0200_113; tooling after run_end), G_RT, G_PROC. Release gate GCC PASS.
  - **Run.** RUN_T0 05:53:57 EDT; RUN_DONE 07:31:26 EDT at 5850 s of 7200 s. Streams: transfer 5220 s, gti 3843 s, repro 598 s, g11 624 s. No stop.
  - **Chain:** plan `52deedb` -> authorization `a138b00` -> lemma `35bb890` -> reference `eedd13a` -> RGL5 code `6215a53` -> process `b6d7edd` -> commit order `e3bba8c` -> rate math `d07cce8` (#117 cut) -> source freeze `5850088` -> scoring freeze `2a6aba7` -> run_start `a5b6954` -> seal `612d651` -> gates `47b83a4` -> #118 `58b93fb` -> clean clone `7871cab` -> tooling `fca0f18` -> release freeze `41ec9b2`.
  - **Deviations:** #115, #116, #117 (pre-run), #118 (run outcome).
  - **No CI:** no `.github`, no workflows. The `brute-bridge` worktree and BGR-v0.90.0 were not touched.
  - **Next:** the v0.22.0 plan (`BRUTE_PLAN_025` on branch `plan/v0.22.0`, plan only; build not authorized).

<!-- V0200 -->
- **v0.20.0: RELEASED** 2026-10-28 (tag `v0.20.0` → `c42e6f4`; main fast-forwarded; https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.20.0; fresh-clone verify passed short and --long with `verify_release_0200_r1`). Study BRUTE-0200-LR-ANYTIME-023. **12 of 13 gated pass.**
  - **Headline GLR (likelihood-ratio anytime bound): PASS, clauses a-e.**
    - RGL4: 0 false certificates on 240 of 240 noisy main cases; CP95 0.0124.
    - C_late at eps 0.02: 0.417 [0.376, 0.459].
    - dC_late vs RGNA4: +0.192 [0.162, 0.223].
    - prefix28 identical on 120 of 120 cases.
    - RGL4 still trails RGNB4 (C_late 0.530) and has C_early28 0.0024.
  - **FAIL: G_HB.** 2511 beats, max gap 47.558 s, 6 gaps over 10 s (clock_step 4, unattributed 2).
  - **FAIL: release gate GCC (#112).** The frozen git-archive clean clone cannot evaluate GLR_lemma's git-history clause.
    A supplementary git-clone rescoring passes byte for byte (ungated).
  - **PASS:** G_recount, GLR_lemma, GAS_frozen_control, GS_a10, GS_ref10 (mutation 20/20), GAPI10 (`brute.certify/9` is
    new; /8 to /1 unchanged), G10, G12 (60/60), G13, GTI (tooling after run_end), G_RT.
  - **Run.**
    - RUN_T0 20:45:20 EDT.
    - A false-start orchestrator ran at 20:45:20 because leaked SMOKE/STUDY_DIR_023 made it read the dry-run directory.
      It was relaunched at 20:46:01 with the same RUN_T0 (#111); the 41 s counted against the cap.
    - RUN_DONE 22:12:21 EDT at 5221 s of 7200 s.
    - Streams: transfer 4475 s, gti 3627 s, repro 705 s, g11 589 s. No stop.
  - **Chain:** plan `f88ad1e` → lemma `e50967d` → implementation `9e0ca70` `cc53f4d` → rate math `56566e7` (#110) →
    source freeze `6bbe5ba` → scoring freeze `2d73745` → run_start `fb64c86` → run_end `5c2f0e3` → seal `7ac0edc` →
    gates `91f4af6` → #111 `d3b7020` → clean clone `bfc6c49` → #112 `40ad4c0` → git-clone rescoring `3add4b9` →
    tooling `7435c9f` → release freeze `3a30555` → release `fc7e082` → #113 verifier r1.
  - **#113.** The frozen `verify_release_0200` rejects dual-role commit `9e0ca70`. Verify with `scripts/verify_release_0200_r1.py`.
  - **K_0190 declared.** v0.21.0 must declare K_0200.
  - **No CI:** no `.github`, no workflows. The `brute-bridge` worktree and BGR-v0.90.0 were not touched.
  - **#114.** Five post-run ledger notes carry hand-typed times; git commit times are authoritative.
  - **Next:** `NEXT_ITERATION.md` and the v0.21.0 plan (`BRUTE_PLAN_024` on branch `plan/v0.21.0`, plan only; build not authorized).

<!-- V0190 -->
- **Released: v0.19.0** — tag `v0.19.0` (annotated, object `bbd1c61`) on `f0bbfb6`, release https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.19.0; `main` fast-forwarded `4a644a9..f0bbfb6` (no force) (study BRUTE-0190-ANYTIME-021, branch `plan/v0.19.0` from main `4a644a9`). **12 of 14 gated pass.** Fresh GitHub clone of `plan/v0.19.0@3f77b17`: short verify passed (469 receipts), `--long` GLV 12 cases / 0 mismatching / 165.0 s (cap 900 s), `tests.test_release_0190` 7 OK; record `docs/research/v0.19.0/FRESH_CLONE_VERIFY_0190.json`. Local `--long`: 12 / 0 / 152.0 s. #107 header says written ~17:35 EDT; the commit is earlier (see git log), kept (ledger-hashed).
  - **ANYTIME (headline GAH_anytime): FAIL on clause (c).** (a) RGNA4 0 false on 240/240 noisy main cases; (b) CP95 upper 0.0124; (d) C_late eps 0.02 = 0.265 [0.215, 0.317]. (c) dC_early28(RGNA4 - RGNB4, eps 0.02) = -0.0040 [-0.0068, -0.0018], bar > 0. dC_late -0.228.
  - **FAIL: GTI** (6 undeclared failures in `tests/test_release_0190.py`; release tooling `0977173` was committed before run_start; #107).
  - **PASS:** G_recount, GAH_prefix_control, GAH_frozen_control, GS_a9, GS_ref9 (480 audited, mutation 20/20), GAPI9 (`brute.certify/8` new, /7../1 unchanged), G10, G12 (60/60), G13, G_RD, G_RT, G_HB (max gap 3.294 s). Release gates: GCC PASS; GLV below.
  - **Run:** run_start 16:02:34 EDT; RUN_DONE 17:22:35 EDT at 4801 s of 7200 s. Streams: gti 3638 s, transfer 4130 s, repro 244 s, g11 669 s. No stop.
  - **Chain:** plan `a51275e` → implementation `94d49b7` `30595c3` `df915e5` → tooling `0977173` → rate math `162d714` → source freeze `07beaa0` → scoring freeze `0894fcc` → run_start `ea114fe` → run_end `9c2a7fa` → seal `ffda8a1` → gates `ff96381` → #107 `c2b8633` → clean clone `e0441ab` → release freeze `08e18fc`.
  - **No CI:** no `.github`, no workflows. `brute-bridge` worktree and /tmp/wt-state untouched.
  - **Next:** `NEXT_ITERATION.md` (flatter anytime schedule GAS, 3 actions at 88 steps, GTI tooling-order rule).

<!-- V0180 -->
- **Released: v0.18.0** — tag `v0.18.0` (annotated) on `71e80a1`, release https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.18.0; `main` fast-forwarded `375a904..71e80a1` (no force); fresh GitHub clone of `plan/v0.18.0@71e80a1`: short verify passed (448 receipts), `--long` GLV 12 cases / 0 mismatching / 177.8 s (cap 900 s), `tests.test_release_0180` 7 OK; record `docs/research/v0.18.0/FRESH_CLONE_VERIFY_0180.json` (`d1a03ec`; its run_at field reads 13:53–14:06, actual 13:52:54–14:03:44 EDT). Study BRUTE-0180-HORIZON-020, branch `plan/v0.18.0` from main `375a904`. **10 of 12 gated pass.**
  - **HORIZON (headline GLH_horizon): PASS.** (a) RGNB4 0 false on 240/240 noisy main cases, 0 crossings; (b) CP95 upper 0.0124; (c) C_late eps 0.02 = 0.482 ≥ 0.10; (d) CI [0.430, 0.537], lower > 0.05. dC_late vs RGN4 +0.053 [0.043, 0.063].
  - **FAIL: GLH_early_control** (C_early28 0.00253 vs study-019 CI [0.0405, 0.0654]; boundary spends delta·b/B, so B = 176 raises early margins; #106) and **G_HB** (max gap 1083.5 s from the box restart, plus 4 gaps of 27–58 s after relaunch).
  - **PASS:** G_recount, GS_a8, GS_ref8 (480 audited, 0 mismatching, mutation 20/20), GAPI8 (`brute.certify/7` unchanged), G10, G12 (120/120), G13, GTI (733 tests, undeclared []), G_RT (streams inside the cap). Release gates: GCC PASS; GLV PASS (12 cases, 0 mismatching).
  - **Run:** run_start 11:51:38 EDT; box restart ~12:19:42 killed every process; resumed 12:37:58 from checkpoints under the frozen rule (#105); RUN_DONE 13:43:58 EDT at 6740 s of 7200 s (dead interval counted). Streams: transfer 4467 s, gti 5443 s, repro 1176 s, g11 402 s.
  - **Chain:** plan `8048c95` → seeds `5e6407a` → #103 `b5ec732` → reference `5ac2ec9` → implementation `2549157` → rate math `44ca110` → source freeze `152c379` → scoring freeze `adc4d2a` → run_start `668a588` → #105 `6d8f1fd` → seal `8430b47` → gates `35a03bb` → clean clone `7053791` → #106 `fc648cf` → tooling `b2c68a0` → release freeze `d20cf05` → RELEASE.json `1abaabe`.
  - **Ledger notes (#106):** seal_020 note time reads 13:47:00 (commit 13:45:00); clean_clone_020 ran at `c3aca37`. Kept (append-only).
  - **K_0180 (expected, 0.18.0 tree):** v0.19.0 must declare K_0180.
  - **Lost in the restart:** /tmp scratch incl. /tmp/wt-state (not deleted by the operator). `brute-bridge` worktree untouched.
  - **No CI:** no `.github`, no workflows.
  - **Next:** `NEXT_ITERATION.md` (anytime margin GAH, streaming `brute.certify/8`). Not pre-registered or built.

<!-- V0170 -->
- **Released: v0.17.0** — tag `v0.17.0` on `1cc76e1`, release https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.17.0; `main` fast-forwarded `e92a7c4..1cc76e1` (no force); fresh-clone short verify of `plan/v0.17.0@1cc76e1` passed (428 receipts) (study BRUTE-0170-SEQUENTIAL-MARGIN-019, branch `plan/v0.17.0` from main `e92a7c4`). **12 of 13 gated pass.**
  - **SEQUENTIAL MARGIN (headline GNB): FAIL on clauses (c) and (d).** (a) RGNB4 0 false on 240/240 noisy cases, 0 crossings; (b) CP95 upper 0.0124 ≤ 0.05; (c) dC(RGNB4 − RGN4) eps 0.02 = +0.0017 [−0.0005, +0.0041], CI lower not > 0; (d) C(RGNB4) eps 0.02 = 0.052 [0.041, 0.065] < 0.10.
  - **PASS:** GNB_post_burn_control, GA3 (CP95 0.0605), GS_a7, G_recount, GS_ref7 (336 gated, 0 mismatching, mutation 20/20), GAPI7 (`brute.certify/7`), G10, G12 (152/152), G13, GTI (691 tests, undeclared []), G_RT, G_HB (637 beats, max gap 2.006 s). Release gates: GLV `--long` 15 cases / 0 mismatching / 77.6 s; GCC PASS.
  - **Reported only:** C at eps 0 / 0.02: RG4 0.453 / 0.249, RGN4 0.054 / 0.051, RGNB4 0.055 / 0.052, RGN4_or 0.339 (eps 0.02), SP8 0.153 / 0.076. RG4 case-false 26/120 at eps 0.02. Stress: RGNB4 8/120 false, RGN4 9/120, RGN4_or 0. Alphabet3: RG4_3 20/48 false at eps 0.02; C(RGNB4_3) 0.012.
  - **Run:** run_start 12:19:16 EDT; RUN_DONE after 1274 s (cap 7200 s); no stream stopped. Rate math projected 1514 / 679 / 366 / 1582 s, observed 923 / 348 / 248 / 995 s (transfer / repro / g11 / gti).
  - **Chain:** plan `c11a852` → #102 `5ca467c` → rate math/smokes `2f552bc` → source freeze `5f6bde1` → scoring freeze `f597096` → run_start `13aa9b8` → seal `76fbe07` → gates `5a3cca8` → clean clone `b4e6d46` → correction receipts `09a0eee` → release tooling `20eec72` → release freeze `85b9969` → RELEASE.json `576e564` (ledger `2f3aebb`).
  - **Ledger note:** run_end_019, seal_019, gates_019, clean_clone_019 each have a first receipt naming the script and a correction receipt naming the artifact; both kept (append-only).
  - **K_0170 (expected, 0.17.0 tree):** v0.18.0 must declare K_0170.
  - **No CI:** no `.github`, no workflows.
  - **Next:** `NEXT_ITERATION.md` (horizon headline GLH, per-bit certificates reported). v0.18.0 is pre-registration only; do not build it without a new owner request.
<!-- V0160 -->
- **Released: v0.16.0** (study BRUTE-0160-NOISY-OBSERVATION-018, branch `plan/v0.16.0` from main `c255873`). **10 of 12 gated pass.**
  - **NOISE SOUNDNESS (headline GNS): FAIL on clause (c) only.** (a) RGN4 0 false certificates on 240/240 noisy cases, all with realized flips ≤ m (m = 4 on 460 of 480 cases, 5 on 20); (b) one-sided CP95 upper bound of the case-false rate 0.0124 ≤ 0.05; (c) C(RGN4) at eps 0.02 = 0.066 [0.051, 0.081], required mean ≥ 0.10 and CI lower > 0.05. *Observed.*
  - **FAIL: GN0** (RGN4_0 ≠ RG4 on main/cycle3/8410024/0.0 in 2 slots, steps 6 and 8, both in burn-in where RG4 passes SP8 through; 0 slots differ after burn-in; RGN4 0 false on eps 0). Predicted Inferred FAIL in #97 item 3.
  - **PASS:** GS_a6, G_recount, GS_ref6 (480/480 audited, 0 mismatching, mutation 20/20), GAPI6 (`brute.certify/6`), G10, G12 (120/120 byte-identical), G13, GTI, G_RT (kill drill 0.226 s), G_HB (442 beats, max gap 2.011 s). Release gates: GLV `--long` 12 cases / 0 mismatching; GCC PASS.
  - **Reported only:** coverage at eps 0 / 0.01 / 0.02: RG4 0.441 / 0.335 / 0.235, RGN4 0.058 / 0.059 / 0.066, RGN4_or 0.440 / 0.381 / 0.316, SP8 0.147 / 0.107 / 0.075. Case-false at eps 0.01 / 0.02: RG4 and RGN4_0 16 / 24 of 120; RGN4, RGN4_or, SP8 0. Stress eps 0.05 (outside eps_bar): RGN4 9/120, RG4 46/120, RGN4_or 0.
  - **Run:** run_start 10:37:53 EDT; RUN_DONE after 882 s (cap 7,200 s); no stream stopped; watchdog exited without killing. Rate math projected 984 / 377 / 585 / 1352 s, observed 425 / 164 / 186 / 881 s (transfer / repro / g11 / gti).
  - **Chain (Exact, git ancestry):** plan `9beb459` (ledger `34901f8`) → seeds `503d61a` → #97 `a74cbaf` → reference `f6ef422` → implementation `f646cca` → process `18885f4` → #98–#99 `6f22051` → smokes `7ec7f08` → source freeze `c350ba5` (ledger `68d0601`) → scoring freeze `5b77da4`/`f9df9bc` → run_start `138cfee` → run_end `012294c` → seal `e86f1df` (`365055e`) → gates `f0f0010` (`ad6b437`) → clean clone `560e177` (`695a1fd`) → tooling `8933d3a`, `c1fc976` (`0b39f05`) → release freeze `b83b1f2` (`fa97faa`) → release record `e5713fa`.
  - **Deviations:** #97 `docs/research/BRUTE_DEVIATIONS_018.md`; #98–#99 `_ADDENDUM_1`; post-run disclosures #100 (GTI dirty-ledger window, scoring_scripts_commit, REQUIRED_KEYS, kill-drill provenance, rate math; no rescoring) `_ADDENDUM_2`.
  - **K_0160 (expected, 0.16.0 tree):** v0.17.0 must declare K_0160 (test_release_0160 version / API / RELEASE.json key tests after the bump).
  - **No CI:** Brute has no `.github` directory and uses no GitHub Actions minutes; add no workflows.
  - **RELEASE STATUS: RELEASED.** Release commit `49a19f9`, annotated tag `v0.16.0`. Fresh GitHub clone of `plan/v0.16.0`@49a19f9 (storage restore 004–018): short verify rc 0; `--long` GLV 12 cases / 0 mismatching / 178.7 s, rc 0; `tests.test_release_0160` 7/7 OK (88.6 s); finished 11:16:58 EDT. `main` fast-forwarded c255873 → 49a19f9 (no force). Release: https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.16.0 . No CI workflows.
<!-- /V0160 -->

<!-- V0150 -->
- **Released: v0.15.0** (study BRUTE-0150-BOUNDED-LOOKAHEAD-017, branch `plan/v0.15.0` from main `d1f462b`). **9 of 13 gated pass.**
  - **BOUNDED LOOKAHEAD (headline GRL): PASS.** RGLX4 0 false in 13,755; TV = S(RGLX4) − S(RG4) +2.84 [2.21, 3.46] (17.09 vs 14.25); 208 sooner, 51 later, 101 equal. Per family: unaliased2 3.72, switch3 3.42, cycle3 2.78, ood4 2.13. *Observed.*
  - **GDS2 PASS:** RSXL4 0 false in 13,906; S equal to RG4 on every case; dC +0.037 [0.030, 0.043].
  - **FAIL: GS_ref5** (g11 stopped by its 2400 s stream budget at 08:07:41 EDT: 308/432 audited, 0 mismatching, 124 not reached (52 ood4 + 72 stress), mutation not reached; cost 46.4 vs 27.0 projected worker-s per case), **GTI** (only undeclared failure the #96 stale literal; 586 = 586), **G_RT** (clause i: g11 stopped; kill drill 0.224 s), **G_HB** (gaps 425.668 s and 316.471 s, sentinel "unattributed"; both ended within ~1 s of the operator's next tool call; cause Inferred).
  - **PASS:** GS_a5, GS_b5 (432/432), G_recount, GAPI5 (`brute.certify/5`), G10, G12 (144/144), G13. Release gates: GLV `--long` 18 cases, 0 mismatches, 465.7 s of 900 s; GCC PASS.
  - **Reported only:** coverage SP8 0.130, RGL4 0.399, RG4 0.402, RGLX4 0.434, RSXL4 0.439, DLFp 0.451; DLFa = RG4 (12,736, 0 false); DLFn 5, RSXLn 5, EB 141 false (outside guarantee); ood5 RG4 148 false in 446, RG5 0/174, RSXL5 0/50; stress DLF/RSXL 120 each, all outside the exact bound; RGLX lookahead ~8.3 ms per step.
  - **Run:** run_start 07:15:33 EDT; RUN_DONE 3,463 s after RUN_T0 (cap 7,200 s); watchdog did not fire.
  - **Chain (Exact, git ancestry):** plan `908fe9b` (ledger `c0a793d`) → deviations #86–#91 `f720f1b` → seeds `5506eff` → reference `5c88600` → implementation `356ecfd` → rate math + #92–#95 `460271b` → smokes `5361010` → source freeze `0b3ad52` (ledger `35e30f5`) → #96 `b25f53d` → scoring `b7ec1ef` (ledger `cd545a7`/`b80caac`) → run_start `cf71514` → seal `3e4f0e8` (ledger `2b8792e`) → GATES `911f06c` (ledger `5d0055a`) → tooling `9174956` → release freeze `9f0d6dc` → RELEASE.json receipt `7545ec8` → addendum 3 `c1e5592` → clean clone `fa658bf`.
  - **Deviations:** #86–#91 `docs/research/BRUTE_DEVIATIONS_017.md`; #92–#95 `_ADDENDUM_1`; #96 `_ADDENDUM_2`; post-run disclosures (g11 budget, heartbeat/idle, GTI as #96; no rescoring) `_ADDENDUM_3`.
  - **K_0150 (expected, 0.15.0 tree):** v0.16.0 must declare K_0150 (test_release_0150 version / API / RELEASE.json key tests after the bump) and K_096.
  - **No CI:** Brute has no `.github` directory and uses no GitHub Actions minutes; add no workflows.
  - **RELEASE STATUS: RELEASED.** Release commit `90210a6`, annotated tag `v0.15.0`. Fresh GitHub clone of `plan/v0.15.0`@90210a6 (storage restore 004–017): short verify rc 0; `--long` GLV 18 cases / 0 mismatching / 491.0 s, rc 0; `tests.test_release_0150` 7/7 OK (151.2 s); finished 09:14:43 EDT. `main` fast-forwarded d1f462b → 90210a6 (no force). Release: https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.15.0 . No CI workflows.
<!-- /V0150 -->

<!-- V0140 -->
- **Released: v0.14.0** (tag `v0.14.0` → `36d8488`; https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.14.0) (study BRUTE-0140-DEFERRED-SPLIT-016, branch `plan/v0.14.0` from main `ffa045b`). **11 of 14 gated pass.**
  - **DEFERRED SPLIT (headline GDS): PASS.** RSXL4 0 false in 14,491 (clause i); S(RSXL4) = S(RG4) on 360/360 cases, 13.69 [12.61, 14.74] (clause ii, Exact by construction and confirmed); dC = C(RSXL4) − C(RG4) +0.049 [0.041, 0.057] (clauses iii/iv); 224 cases up, 65 down, 71 equal. Per family: switch3 0.081, cycle3 0.058, ood4 0.038, unaliased2 0.030.
  - **FAIL: GS_a4** (DLFn 2 false, RSXLn 2 false, both ood4 seed 8240010 mask 0.6, true n 4, libraries (unaliased2, min_n 2) and (ood4, 4); RG4/RG5/RSXL4/RSXLp/DLFp/DLF2p/DLF2n/RSX4 0), **GS_c4** (clauses i/ii; iii passes, DLFn − RG4 0.017 [0, 0.05]), **G_HB** (one 285.065 s gap, 04:41:38–04:46:23 EDT; d_monotonic = d_boottime, watchdog CPU +0.001 s, no file written; Inferred whole-box pause; addendum #80).
  - **PASS:** G_recount, GS_b4 (432/432), G_alias4_stress (984 pairs; AT6 2,736 false, RSXL 0), GS_ref4 (432/432, mutation 20/20), GAPI4 (4/4), G10, G12 (144/144), G13, GTI (533 = 533 tests; failures only K_060–K_0120), G_RT (kill drill 0.223 s). Release gates: GLV `--long` 18 cases, 0 mismatches, 217 s of 900 s; GCC PASS.
  - **Reported only:** coverage SP8 0.146, RG5 0.235, RG4 0.408, RSXL4 0.457, DLFp 0.464, RSX4 0.471, EB 0.479, RSXLp 0.518; S over SP8 RG4 13.69, RSXLp/DLFp 15.13 (TV +1.44), RSX4 9.01 (TV −4.68), EB 16.97 (111 false), RG5 6.81; DLF2 = RG4 everywhere (Exact); ood5 RG4 155 false in 457 (49 of 72 cases, 148 before the 4-state region empties), RG5 0 in 111; stress DLF 48 / RSXL 48 false in 25,920 pairs, all outside the exact license bound.
  - **8140016 diagnosis (seen data, `afb89a9`):** license bound 3 < true n 4 (unaliased2 library, min_n 2); inside the guarantee DLFp 0/1,542 and RSXp 0/1,854 false; outside DLFn 1/3, RSXn 1/2; 72 cases had a license bound below true n.
  - **Run:** run_start 04:34:02 EDT, RUN_DONE 05:12:48 EDT (2,326 s of 7,200 s). Watchdog did not fire; no stream stopped.
  - **Chain (Exact, git ancestry):** plan `498d768` (ledger `4b87380`) → seeds `35b9840` → diagnosis `afb89a9` → reference `ac717c4` → implementation `97f9800`/`62bea00` → smokes `75d57d4` → source freeze `c7ed80e` (ledger `ecad32d`) → scoring `0e9113c` (ledger `cc8525d`/`32ebaba`) → run_start `65d2fb5` → run end `83c2116` → seal `6a82c35` (ledger `da091a2`) → GATES `cc10159` (ledger `ba8fedf`) → tooling `cce6642` → release freeze `ece2474` → RELEASE.json receipt `3109ad4` → addendum `35bca5a` → clean clone `0d29822`.
  - **Deviations #75–#79:** `docs/research/BRUTE_DEVIATIONS_016.md`; **#80–#83:** `docs/research/BRUTE_DEVIATIONS_016_ADDENDUM.md`.
  - **K_0130 (Observed, 0.14.0 tree):** tests.test_release_0130 4 of 7 fail (version, embeddable API answers, short verify, untampered copy). v0.15.0 must declare K_0130 and K_0140.
  - **Deviations #84–#85:** `docs/research/BRUTE_DEVIATIONS_016_ADDENDUM_2.md` (#84 corrects the G_HB threshold quoted in #80 to <= 30 s; verdict unchanged).
  - **RELEASED.** Release commit `36d8488` (tag `v0.14.0`). Fresh GitHub clone at `36d8488` (Observed 05:28–05:36 EDT): storage restore 004–016 OK, `verify_release_0140` short rc 0, `--long` rc 0, `tests.test_release_0140` 7/7 OK. main fast-forwarded (no force). Release: https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.14.0. Next: v0.15.0 under BRUTE_PLAN_017 on `plan/v0.15.0`.
<!-- /V0140 -->

<!-- V0130 -->
- **Released: v0.13.0** (study BRUTE-0130-REGION-SPLIT-015, branch `plan/v0.13.0` from main `8c86587`). **11 of 15 gated pass.**
  - **REGION SPLIT (headline GRS): FAIL.** RSX4 0 false in 11,005 (clause i PASS), but TV_RSX = S(RSX4) − S(RG4) −5.27 [−5.99, −4.59] (clauses ii/iii FAIL); later on 220 of 288 cases, equal on 40, earlier on 28. Per family: cycle3 −4.24, switch3 −3.96, ood4 −4.15, unaliased2 −8.75. RSXp TV −1.55.
  - **FAIL: GS_a3** (DLFn 1 false, RSXn 1 false, both ood4 seed 8140016 mask 0.35; RG4/RSX4/RSXp/DLFp 0), **GS_c3** (RSXn 1 false; CI clause passes, 0.05 [0, 0.16]), **GEB** (EB 91 false in 11,355; EB2 8).
  - **PASS:** G_recount, GS_b3 (360/360), G_alias3_stress (576 pairs; AT6 2,664 false, DLF 0), GS_ref3 (360/360, mutation 20/20), GAPI3 (4/4), G10, G12 (120/120), G13, GTI (488 tests; failures only K_060–K_0110), G_RT (kill drill 0.209 s), G_HB (max gap 2.03 s). Release gates: GLV `--long` 15 cases, 0 mismatches, 172 s; GCC PASS.
  - **Reported only:** S over SP8 RG4 10.51 [9.64, 11.33], RSX4 5.24, RSXp 8.97, DLFp 12.39; coverage SP8 0.166, RG4 0.370, RSX4 0.434, RSXp 0.507; ood5 RG4 121 false in 381, RG5 0 in 132.
  - **Run:** run_start 02:20:13 EDT, RUN_DONE 02:50:57 EDT (1,844 s of 7,200 s). Watchdog did not fire.
  - **Chain (Exact, git ancestry):** plan `9642783` (ledger `61584ee`; HANDOFF `c6bfcb3`, recorded as `preregistration_commit` in RELEASE.json) → seeds `f6fbb92` → reference `f95a176`/`305b739` → implementation `6815770`/`3cd15e4`/`0f95f92`/`744969b` → make_freeze `069cbca` → source freeze `f67bcaf` (ledger `1c144d1`) → scoring `58e42fd` (ledger `31edbe0`, 02:09:54 EDT) → run_start `6406522` → run end `eb2f7d2` → seal `f1668a7` → GATES `c21b405` → tooling `e25943f` → release freeze `9e785b1` → clean clone `8e6923c`.
  - **Deviations #64–#73:** `docs/research/BRUTE_DEVIATIONS_015.md`; **#74:** `docs/research/BRUTE_DEVIATIONS_015_ADDENDUM.md` (TEST_SUITE `tracked_tree_dirty=true`, cause Open).
  - **K_0120 (Observed, 0.13.0 tree):** tests.test_release_0120 4 of 7 fail (version, embeddable API answers, short verify, untampered copy). v0.14.0 must declare K_0120 and K_0130.
  - **RELEASED 2026-10-27 ~03:18 EDT:** release commit `d1f6c71`. On the branch and on a fresh GitHub clone of `d1f6c71`, `verify_release_0130` passed both short and `--long` (GLV: 15 cases, 0 mismatches, 170 s), and `tests.test_release_0130` passed 7/7 (100 s). main was fast-forwarded to `d1f6c71` with no force. Annotated tag `v0.13.0` (tag object `2ee29f7`) points to `d1f6c71`. GitHub release: https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.13.0
<!-- /V0130 -->

<!-- V0120 -->
- **Released: v0.12.0** (study BRUTE-0120-BOUNDED-TRANSFER-014, branch `plan/v0.12.0` from main). **15 of 16 gated pass.**
  - **BOUNDED TRANSFER (headline GST2): PASS.** GS_a: 0 false in RG4 9,809, DLFp 11,434, DLFn 9,810, DXp 11,761, DXn 10,100. G_alias_stress: 600 stress pairs, AT6 2,016 false, DLF 0; all 20,736 pairs 336 DLF licenses, 0 false. GS_d: TV(DLFp) over RG4 1.64 [1.27, 2.01], all on unaliased2 (6.57). GS_c: TV(DLFn) 0.05 [0.00, 0.15]. GS_rg: RG4 S 10.86 [9.83, 11.84]. *Observed.*
  - **FAIL: GS_x** (DXp − DLFp −0.007 [−0.59, 0.57]).
  - **PASS:** GS_a, GS_b, GS_c, GS_d, GS_rg, GST2, G_alias_stress, GS_ref (288/288, mutation 20/20), GAPI2 (`brute.certify/2`, 5/5), G10, G12 (96/96), G13, GTI (440 tests; failures only the declared K_060–K_0100 sets), G_RT, G_HB (max gap 2.0 s). Release gates: GLV `--long` 12 cases, 0 mismatches, 117 s of 900 s; GCC clean clone PASS.
  - **Run:** run_start 00:14:04 EDT, RUN_DONE after 1,655 s of 7,200 s. Watchdog did not fire.
  - **Chain (Exact, git ancestry):** plan `ef865e7` → seeds `f87f5bc` → reference `89ff5b8` → implementation `7323b44`/`0b81c76`/`76a9e8d`/`516fe34` → source freeze `b4f0fc8` → scoring `4375a5f` (ledger `3688d06`, 00:02:31 EDT) → run_start `fad500d` → run end `89be4ed` → seal `12455f0` → GATES_014 `27bfe45` → release tooling `ee1a1c8` → deviation/release ledger `8c7c9b2` → release freeze → ledger `f59caf7` → clean clone → ledger `028d9cb` → release docs.
  - **Deviations #59–#61:** `docs/research/BRUTE_DEVIATIONS_014.md`; **#62–#63:** `docs/research/BRUTE_DEVIATIONS_014_ADDENDUM.md`. Erratum to #62: the "~00:55 EDT" time on the LX recount is approximate; the recount ran before 00:50 EDT.
  - **K_0110 (Observed, 0.12.0 tree):** tests.test_release_0110 4 of 7 fail (version, API name, two verify tests needing RELEASE.json key GST). Declared in RELEASE.json; v0.13.0 must declare K_0110 and K_0120.
  - **RELEASED 2026-10-27 ~01:03 EDT:** release commit `2a1f110`. `verify_release_0120` passed short and `--long` on the branch and on a fresh GitHub clone of `2a1f110` (GLV 12 cases, 0 mismatches, 119 s); `tests.test_release_0120` 7/7 on the fresh clone (67 s). main was fast-forwarded to `2a1f110` (not forced). Annotated tag `v0.12.0` (object `3c1a88f`) points to `2a1f110`. Post-tag commits on main are docs only (this HANDOFF update). [GitHub release](https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.12.0). Default learner unchanged (Y1k, LU-R); RGn, DLF and DX are research arms; `brute.certify/2` is the embeddable API.
  - **Next: v0.13.0 per `NEXT_ITERATION.md`** (region-split experiments, evidence-derived bound, family bound 5, own-trajectory recount).
<!-- /V0120 -->

<!-- V0110 -->
- **Previous: v0.11.0** (study BRUTE-0110-SOUND-TRANSFER-013, branch `plan/v0.11.0` from main b935fff + diagnostic `e0aa431`, deviation #52). **22 of 26 gated pass.**
  - **TRANSFER (headline GST): FAIL.** GS_d PASS: ATp mean S 6.64 steps, seed-paired CI95 [5.73, 7.54], 146 helped / 0 hurt, 0 false in 10,202. **GS_a FAIL and GS_c FAIL:** ATn issued 3 false transfer-rule certificates in 1/288 cases (switch3 seed 6120009; one cycle3 hypothesis aliased for 7 confirmations). **GS_e FAIL:** LXp S −1.32 [−2.19, −0.50]; LX had 0 false certificates. GS_b PASS: DR ⊆ SP8 exactly, S 0. GS_ref PASS: 288/288.
  - **API:** GAPI PASS. `brute/api/certify.py` implements `brute.certify/1` (observations in, CERTIFIED answer or UNKNOWN out; host-agnostic). `verify_release_0110` checks it.
  - **PASS:** G1, G2, G3L, G3′ strict, G6b (SP8 − A2 −0.0104 [−0.0165, −0.0047]), GH, G4, G5, G7, G9, G10, G11, G12, G13, GTI (K_080/K_090 declared), G_RT (R_G_RT_strict true), G78_soundness (0 of 360), G78_containment, GS_b, GS_d, GS_ref, GAPI. Release gates: GLV `--long` PASS (33 cases, 66 traces, 0 mismatches, 53.7 s of 900 s); GCC clean clone PASS (`results/study-013/CLEAN_CLONE_013.json`).
  - **Run:** run_start 11:10:34 EDT, hard cap 13:10:34 EDT, RUN_DONE 11:46:22 EDT (2,148 s of 7,200 s). The watchdog did not fire. Every stream completed. The GTI stream used 79% of its budget (disclosure). There were heartbeat gaps of 335 s and 94 s.
  - **Chain (Exact, git ancestry):** plan `bb1d96e` → seeds `780be3b` → reference `eed2ada` → implementation `084076a`/`3871e78`/`7dc04c8` → source freeze `e6fc10c` → scoring `22bdb9f` (ledgered 10:57–10:59 EDT; erratum `aab5046`) → run_start `9d588d0` → seal `5f45ed4` → run_end/seal ledger `af4b384` → GATES_013 `ad1ba6a` → release tooling `a56a177` → deviation/release ledger `d5bf4ce` → release freeze `8890884`/`ed53fdf` → clean clone `d9ca7bc` → release docs.
  - **Deviations #52–#57:** `docs/research/BRUTE_DEVIATIONS_013.md`.
  - **RELEASED 2026-10-26 ~22:50 EDT:** release commit `d8b449d`. Deviation #56 (push outage from ~10:56 EDT, stale GITHUB_TOKEN; see `docs/research/BRUTE_DEVIATIONS_013_ADDENDUM.md`) was RESOLVED at ~22:40 EDT: gh credential helper, `env -u GITHUB_TOKEN -u GH_TOKEN`. The 22-commit backlog went out as a plain fast-forward (7dc04c8..d8b449d), with no force and no history rewrite. `verify_release_0110` passed short and `--long` on the branch and on a fresh GitHub clone of `d8b449d` (GLV 33 cases, 66 traces, 0 mismatches). `tests.test_release_0110` passed 7/7 on the fresh clone (129 s). main was fast-forwarded b935fff..d8b449d (not forced). The annotated tag `v0.11.0` (object `f97197b`) points to `d8b449d`. Post-tag commits on main are docs only: `fb76a27` (HANDOFF Released), `f83c5c2` (restored the ledger-hashed deviations file and moved the note to the addendum; deviation #58) and this line fix. [GitHub release](https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.11.0). The default learner is unchanged (Y1k, LU-R); DR, AT and LX are research arms. Standing rule since v0.11.0: on a push or auth failure, keep working locally and push the backlog when access returns.
  - **Next: v0.12.0 per `NEXT_ITERATION.md`.** Make the transfer license disagreement-based against the full region, add an aliasing stress block, use discriminating library experiments, and add `brute.certify/2`.
<!-- /V0110 -->

<!-- V0100 -->
- **Released: v0.10.0** (study BRUTE-0100-SUPPORT-TRANSFER-012, branch `plan/v0.10.0` = main 13daa32 + diagnostic, deviation #48). **18 of 24 gated pass.**
  - **TRANSFER:** GT_b PASS (TRp mean S 20.18 steps, seed-paired CI95 [19.18, 21.17]; 270 helped / 0 hurt; 0 false in 20,027). GT_ref PASS (288/288, 0 mismatches). **GT_a FAIL** (TRn 167 false transfer-rule certificates in 50/288 cases). **GT_c FAIL** (the same certificates, plus S_n 4.53 [3.37, 5.73] > 0).
  - **Other FAIL:** G6b (J10−A2 −0.1657 [−0.1767, −0.1551]), GA1_012 (via G6b), G3′ strict (J10 1 at lag 1), GTI as frozen (3 test_release_080 failures, deviation #50; R_GTI_K080 passes).
  - **PASS:** G1, G2, G3L, GJ10 (+0.0090 [0.0059, 0.0122]), GH, G4, G5, G7, G9, G10, G11, G12, G13, G78_soundness, G78_containment, G_RT (R_G_RT_strict true), GT_b, GT_ref. Release gates: GLV `--long` PASS (33 cases, 0 mismatches, ~21 s); GCC clean clone PASS (`results/study-012/CLEAN_CLONE_012.json`).
  - Run: run_start 09:09:06 EDT, hard cap 11:09:06 EDT, RUN_DONE 09:37:26 EDT (1,700 s of 7,200 s). The watchdog did not fire. Every stream completed (g11 optional 108/108).
  - Chain (Exact, git ancestry): diagnostic `6494a35` → plan + ROADMAP_TO_GI `0cccf0d` → seed check `9f4d4db` → reference `a44a8da` → implementation `2564201`/`1c43d68`/`4628617`/`2fb806c`/`7e77621` → source freeze `b40f263` → scoring `22ce7f7` (ledgered 08:57:44 EDT) → run_start `9b0babe` → seal `c07d773` → run_end/seal ledger `1af2976` → GATES_012 `1080654` → release tooling `be6a4ea` → deviation #51 + release_0100 ledger `90c3d1d` → release freeze `fb4ffd1` → clean clone `173465a`.
  - Deviations #48–#51 and disclosures: `docs/research/BRUTE_DEVIATIONS_012.md`. The pyproject bump to 0.10.0 makes the frozen test_release_090 version and verify tests fail (the K_090 analogue of K_080); v0.11.0 must declare it.
  - **RELEASED 2026-10-26 ~10:03 EDT:** release commit `c2794cf`. `verify_release_0100` passed short and `--long` on the branch (GLV 21 s of 900 s) and on a fresh GitHub clone of `c2794cf` in /tmp/fc0100 (GLV 19 s). `tests.test_release_0100` passed 6/6 on the fresh clone (108 s). main was fast-forwarded 13daa32..c2794cf (not forced). The annotated tag `v0.10.0` (object `7b33add`) points to `c2794cf`. This HANDOFF commit is the only post-tag commit on main. [GitHub release](https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.10.0). The default learner is unchanged (Y1k, LU-R); J10, TRp and TRn are research arms. Scratch deleted.
  - **Next: v0.11.0 per `NEXT_ITERATION.md`** (sound transfer: intersect the prior with the full region, or verify the library before it licenses certificates; library for experiment choice; declare K_080 and K_090; big78 power). Pre-register BRUTE_PLAN_013 on `plan/v0.11.0` from main before any code.
<!-- /V0100 -->

- **Previous: v0.9.0** (study BRUTE-090-WINDOW-011, branch `plan/v0.9.0` from origin/main f79c925 ⊃ 70cb351, deviation #40). **15 of 17 gated pass.**
  - **FAIL:** G6b (J9−A2 coverage −0.1918, 95% CI [−0.2073, −0.1772]), GA1_011 (J9 does not reach SP8-level coverage).
  - **PASS:** G1, G2, G3L, G3′ strict (first strict pass: J9 0, SP8 16, control 323 ≤ limit 161.5), GH, G4, G5, G7, G9, G10, G11, G12, G13, GTI, G_RT.
  - Release gates (not in GATES_011): GLV `--long` PASS (33 cases, 66 traces, 0 mismatches, 363 s of 900 s); GCC clean clone PASS (`results/study-011/CLEAN_CLONE_011.json`, 24.9 s).
  - Run: run_start 06:48:41 EDT, hard cap 08:48:41 EDT, RUN_DONE 07:18:53 EDT (1,812 s of 7,200 s). Watchdog did not fire. g11 optional rest stopped at its 1,500 s budget (960/1,152 traces, 0 mismatches), so R_G_RT_strict is false (reported only).
  - Chain (Exact, git ancestry): lag diagnostic `a5ef9c8` → plan `7950513` → seed check `06249f7` → reference `d5c6a54` → implementation `8eeb810`/`4c4800b`/`052ec9d` → scoring scripts `13b12ee` → source freeze `f658e13` → scoring_freeze ledger 06:38:21 EDT → run_start → seal `6ae2cc4` → GATES_011 `ed2b042` → release tooling `34724b9` → release freeze R1 `804a433` → clean clone `9cddb66` → deviation #47 `d737a66`.
  - Deviations #40–#42: `docs/research/BRUTE_DEVIATIONS_011.md`; #43–#47: `docs/research/BRUTE_DEVIATIONS_011_R1.md`.
  - **RELEASED 2026-10-26 ~07:53 EDT:** release commit `05ed794`. `verify_release_090` passed short and `--long` on the branch (GLV 324 s of 900 s) and on a fresh clone of `05ed794` in /tmp/fc090 (GLV 316 s); `tests.test_release_090` 6/6 OK on the fresh clone (74 s). main fast-forwarded f79c925..05ed794 (not forced); annotated tag `v0.9.0` (object `2a9f627`) → `05ed794`; ledger 204 receipts. This HANDOFF commit is the only post-tag commit on main; [GitHub release](https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.9.0). Default learner unchanged (Y1k, LU-R); J9 is a research arm.
  - **Next: v0.10.0 per `NEXT_ITERATION.md`** (J10 surprise-gated window hull; seen-data downgrade diagnostic first; 7–8 states in one family; g11 optional-rest stamp). Pre-register BRUTE_PLAN_012 on `plan/v0.10.0` from main before any code.
- **Previous: v0.8.0** released (tag `v0.8.0`), 12 of 17 gated pass; its record follows.
- **Released: v0.8.0** (study BRUTE-080-ALIGN-010, branch `plan/v0.8.0`). **12 of 17 gated pass.**
  - **FAIL:** GA1_010 (target a), G3′ (SP8 3 non-drift false certificates), G6b (J8 coverage 0), GD (clause i, 2/7 silent-jump class), G_RT (clause i: the g11_2x2 optional phase hit its own budget).
  - **PASS:** G1, G2, G4, G5, G7, G9, G10, G11, G12, G13, GX2_010, GTI.
  - Run: start 05:03:17 EDT, hard cap 07:03:17 EDT, RUN_DONE 05:36:07 EDT (1,970 s). The watchdog did not fire.
  - Chain: plan `881f0a6` → source freeze `5470c48` → scoring `39d255b` → run_start `19f3a88`/MANIFEST `687f28a` → run_end `eb85feb` → seal `1bdebc9` → ledger seal/gates `3cfac6c`/`0422ac0` → sealed run state `7b8a06d` → merge of main `b1e628d` → release docs and freeze.
  - **RELEASED 2026-10-26 ~05:55 EDT:**
    - Release commit `3bce08c`.
    - Deviations #38 (superseding ledger receipt for the frozen harness) and #39 (pre-publication verifier fix: note-less receipts dated by commit).
    - Ledger 172 entries; final release commit `70cb351`.
    - `verify_release_080` passed on the branch, on a fresh clone and as main. `tests.test_release_080` 5/5 OK (109 s).
    - main fast-forwarded a86298b..70cb351 (not forced).
    - Annotated tag v0.8.0 (object `9fa656c`) -> `70cb351`.
    - [GitHub release](https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.8.0).
  - Next: v0.9.0 per `NEXT_ITERATION.md`. First a lag diagnostic on seen data, then pre-register BRUTE_PLAN_011 on a new branch from main.
- **Previous: v0.7.0** released (tag `v0.7.0`), 9 of 17 gated pass; its record follows.
- **Released: v0.7.0** (study BRUTE-070-SYNCPLAN-009, branch `plan/v0.7.0`). **9 of 17 gated pass.**
  - **FAIL:** GA1′ (target a), G3′, G6b, GP1 (target c); STUDY_BUDGET: GX2″ (target b; symmetric part complete, 0 mismatches; spot 6/24), G11 (no output), GTI (target d, never ran in-cap), G_RT.
  - **PASS:** G1, G2, G4, G5, G7, G9, G10, G12, G13.
  - Run: start 20:04:06 EDT, cap 23:04:06, stop rule fired 23:22:42 EDT (late; DEVIATIONS_009 entry 21). No stream relaunched.
  - Done in order: run-end commit `4cdeeb4`; deviations 21–25 `af60688`; pack `30bb932`; ledger run_end_009 + SEAL `327d4fd`; ledger seal_009 `8888b88`; paired + repro; GATES_009 `a50f751` + ledger gates_009; docs + RELEASE.json/pyproject 0.7.0.
  - **RELEASED 2026-10-26 ~00:57 EDT:** GATES_009_FINAL + TEST_SUITE_009_FINAL `db6f6bb`; ledger gates_final_009 + MANIFEST `ee21407`; verify_release_070 --fast passed on branch, fresh clone and merge; `--no-ff` merge `d016a81` on main; annotated tag v0.7.0 (object `e5ae50b`) -> `d016a81`; [GitHub release](https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.7.0). 9/17 gated pass. Next: v0.8.0 per NEXT_ITERATION.md (pre-register BRUTE_PLAN_010 on a new branch from main first).
- **Previous: v0.6.0** released (tag `v0.6.0`), 11 of 16 gated pass; its record follows.
- **Released: v0.6.0** (study BRUTE-060-DRIFTSOUND-008, `plan/v0.6.0` → main, tag `v0.6.0`). **11 of 16 gated pass.**
  - **FAIL:** GA1 (target a), G3′, G5, G6b and GX2′ (target b, incomplete coverage).
  - **PASS:** G1, G2, G4, G7, G9, G10, G11, G12, G13, GT1 (target c) and GMC (target d).
  - Gates: `results/study-008/GATES_008_FINAL.json`. Deviations: `docs/research/BRUTE_DEVIATIONS_008.md` D1–D26.
  - D21: stream A (xcheck) stopped by owner decision at 17:44 EDT with 46/288 cases. Scored FAIL on the frozen criterion; no results were inspected.
  - D22: partial wrapper `scripts/make_xcheck_partial_008.py`.
  - D23: pack was run by hand.
  - D24: observations made during scoring, report only.
- **Previous: v0.5.0** (tag `v0.5.0` → merge `8e03e03`). 12 of 15 gated pass; GX2, G3′ and G6b fail. Tags never move.
- Default learner is still the v0.5.0 rule (Y1k, LU-R). R6/C6 are research arms only (plan `default_policy_rule`).

## Branches (origin `github.com/jacksonjp0311-gif/Brute`, public on purpose: James asked for it 2026-10-25 01:13 EDT)

| Branch | Head | State |
| --- | --- | --- |
| `main` | tag v0.9.0 (fast-forward of `plan/v0.9.0`) plus this HANDOFF | Released code and record |
| `plan/v0.9.0` | see `git log` | v0.9.0 working branch (merged) |
| `plan/v0.8.0` | see `git log` | v0.8.0 working branch (merged) |
| `plan/v0.7.0` | see `git log` | v0.7.0 working branch (merged) |
| `verify/xcheck-incremental` | `c2bf07e` | Post-release incremental xcheck verification (not v0.6.0 evidence); 3 files adopted by v0.7.0 |
| `plan/v0.6.0` | see `git log` | v0.6.0 working branch (merged) |
| `plan/v0.5.0` | `d0516a0` | v0.5.0 working branch (merged) |
| `plan/v0.4.0` | `5e7d208` | v0.4.0 working branch (merged) |
| `bridge/v0.2`, `bridge/v0.1` | `cced586`, `9c88a3a` | Bridge work; **unmerged; do not edit or merge without a decision** |

## v0.6.0 progress (commit order is the chronology evidence)

1. DONE 07:2x EDT: branch `plan/v0.6.0` from main `ed66489`. `89c2d3b`: BRUTE_PLAN_008.json + PLAN_008.md. Targets:
   - a: GA1, one arm of R6/C6 passes G1+G2+G3′+G6b.
   - b: GX2′, xcheck with SAT/CaDiCaL, checked ≥0.99 per family×arm, 0 mismatches.
   - c: GT1, verify_release_060 / test_release_060, with the frozen 050 files untouched.
   - d: GMC, its own gate.
   - Predictions (Inferred): GA1 FAIL, GT1 PASS.
2. DONE `1bc702f`: ledger preregistration_008 + MANIFEST.
3. DONE: seed check; implementation; smoke; source freeze `8e80615`; scoring scripts `08ac3f3`; run_start_008 08:49 EDT;
   GT1 tooling `29cd0d1`; main SEAL `c21ef12`; stream C (G11, enumeration, repro, GMC recount) done 10:49 EDT; stream B (GMC) done.
4. DONE 17:44 EDT: owner stopped stream A (xcheck) at 46/288 (`b02b0c3` checkpoint, D21–D23). Then, in order:
   - pack `287d619`;
   - ledger run_end_008 + seal_008 `3a5e193`;
   - wrapper `1202c53`;
   - XCHECK_008.json `87ad393`;
   - paired + reproducibility;
   - GATES_008 (ledger gates_008 `c4a7c1b`);
   - GT1_008 + GATES_008_FINAL (ledger `1cd90f4`).
5. DONE: RELEASE.json/pyproject 0.6.0; README/CHANGELOG/HANDOFF/D24; retroactive receipt for pre-freeze fix `cae25ce` (D25); verify_release_060 git_order fix and
   release freeze `BRUTE_RELEASE_FREEZE_060_R1.json` superseding `BRUTE_RELEASE_FREEZE_060.json` (D26);
   ledger release_freeze_060_r1/release_060; MANIFEST; verify_release_060 --fast; tests; ff-merge to main; tag v0.6.0; gh release.

### Open for the next study (Inferred / Open)

- The xcheck needs to run about 50x faster to finish breadth in a working day. Options: incremental solving, sampling steps under a pre-registered rule, or moving off a shared box. GX2′ is still open.
- Stale certificates one step after a drift remain in R6, C6 and A5 (D24b). The surprise signal may arrive one step late.
- The perm4 false-alarm cases under τ6 (D24a) need a pre-registered look at alarm calibration on perm4.
- Neither rule gets close on G6b; the coverage/safety trade-off is still open.
- Model counts are available but unused.
- `experiments/brute_study_006.py` sets `S5.FULL` when it is imported, which makes `test_study_005` fail in full-suite runs (Observed). Both files are frozen; v0.7.0 target (d) isolates it per process instead of editing them.

## v0.5.0 progress (commit order is the chronology evidence)

1. DONE: branch `plan/v0.5.0` from main `2998dba`; timing probe (frozen geometry, sealed 006 seeds): 2x2 SAT + LU-R ~0.1-0.7 s/case; n<=6/7 ~1-10 s.
2. DONE `5be08aa` (ledger `64f8c79`, ~05:22): `experiments/BRUTE_PLAN_007.json` pre-registered (A5/M5/A4/A2 on 2x2; B5/BM5/BP5 on
   big6/sens3/act3/ood6s3; GX1-3, G1-G5, G6b(M5), G7, G9-G13; SOLVER_BUDGET; M = projection-volume tie-break; #SAT etc. Open).
3. DONE `1b57efe` (ledger `a5215ee`, ~05:26): `experiments/v050_reference.py` second implementation (no brute import) +
   `tests/test_v050_reference.py` (k=2 generalised enumeration == frozen reference). Process notes for DEVIATIONS_007 in
   `docs/research/v0.5.0/PROCESS_NOTES.md`.
4. DONE (pre-freeze, ~05:27-05:41): `fc2bed8` brute/region.py (RegionK/RegionSpace, tri-state Glucose3), brute/region_learner.py
   (A5/M5), brute/breadth.py (B5/BM5/BP5), experiments/worlds_007 / brute_common_007 / brute_study_007 (per-case checkpoint);
   `c8e8611` brute_calibrate_007 + scaling_007; `b693113` api 1.5 service + schemas v1_5 + release_version_050 + tests/test_v050_impl.py
   (8 tests OK). Smoke (seeds 901-903 only): A5 vs A4 on all 8 2x2 families x 3 rates = 3168 steps, 0 mismatches (Observed);
   breadth per-case 0.2-6 s; scaling n=12 cases < 1 s.
4b. Smoke count (324 arm traces, 24/24 mutations detected) flagged 2 traces: residual == smoke tau7 at 12 d.p.; plan says
   rounded residual > tau, reference used frozen unrounded _Alarm. Pre-freeze fix `0c86d90` (_Alarm12 in v050_reference, A4 audit
   unchanged; disclosed in PROCESS_NOTES). `d7054a1`: run/storage/freeze scripts, torn-line-tolerant checkpoint. Recount 05:56: 0/324 mismatching, mutation 24/24, 0 false flags (Observed, smoke).
5. DONE `064a50e` source freeze 007 (20 files, chains 002-006; ledger `0ea8085`, ~05:57).
6. DONE `50e9321` (06:00) scoring scripts 007 in their own commit (dry-run on smoke seeds only); ledger scoring_scripts_007.
   DONE run_start_007 on origin as ebcc650 (06:11:52; local duplicate push rejected, rebased; identical receipt 5cefd253).
7. RUNNING since 06:14 EDT: `PYTHONPATH=. W=6 nohup bash scripts/run_study_007.sh >> /tmp/w7/run007.log 2>&1 &`
   (resumable: rerun same command; each stage resumes from its checkpoint). NEXT: on RUN_DONE commit SEAL/calibration/scaling/gz, ledger run_end_007.
8. 06:17 steering (v0.4.0 review /workspace/brute-review/v0.4.0/REVIEW.md) arrived AFTER run_start; run not stopped (decision:
   held-out data already in use; restart would be redoing work). Post-start, non-pre-registered additions (disclose in DEVIATIONS_007):
   DONE `07a6c69` experiments/v050_prob_reference.py (2x2 v090 probabilities recomputed taken+untaken by partial-machine counting,
   no brute/bgr import; swap mutations; smoke dry-run 0/216 mismatches, 20/20 detected) + scripts/check_smoke_seeds_007.py
   (smoke seeds 901-903 disjoint from 468 evaluation seeds; 05:25 glance seed 1710001 overlaps -> deviation).
   DONE `033c716` ledger smoke_run_retroactive_007 + steering_after_run_start_007.
   DONE `1c4dd00` scripts/scaling_fit.py + docs/research/v0.5.0/SCALING_FIT_006.json (power/exponential/cubic, residuals by n).
   DONE `91ae0d8` post-hoc v0.90 probability recompute on sealed study-006 A4+P4: 0/1152 traces, 88,038 forecasts, mutation 20/20.
   DONE main `47480f7` v0.4.0 errata (docs/research/v0.4.0/ERRATA.md E1-E10; DEVIATIONS_006 P8 + P1/P2 notes; CHANGELOG,
   README, HANDOFF corrected; MANIFEST regenerated; verify_release_040 --fast passed; tag v0.4.0 still 5c02a7b).
   DONE merge main -> plan `0e29dc2`; ledger errata_040 `e972b8c` (receipt b00d1d20...).
9. DONE run: sealed 06:25 (`51215e0`), RUN_DONE 06:27:47 (`3073992`), ledger run_end_007 `86bd7bc`. SCALING_FIT_007 `feeeb1d`.
   DONE paired + reproducibility (296/296 identical) `d88d4bb`, ledger `2ceb87e`. DONE PROB recompute 0/1728, 20/20 `ffeb0c4`.
   DONE count `9c7737e` (0/2592 arm traces, mutation 20/20; breadth reference budget-stopped on some big6/act3 traces), ledger `7ddaf45`.
   DONE `16d60cf` release freeze list also locks post-start audit scripts.
   DONE gates `dab2012`, ledger `cda5c49`: 12/15 gated pass; FAIL GX2 (0 mismatches, act3 checked 84.5% < 90%), G3' (M5 1 non-drift
   false cert on drift4; A5 passes), G6b (predicted). GM NOT DISTINGUISHED (M5-A5 CI > 0 but G3' fails for M5). GX3 PASS.
10. DONE M5 non-drift diagnostic (DEVIATIONS_007 Q7, report only); DEVIATIONS_007 complete `a02e9c7`+.
   DONE README `e86c9f9`; CHANGELOG/DISCOVERIES D22-D25/ROADMAP/NEXT_ITERATION (v0.6.0) `5d19d36`.
   DONE RELEASE.json + pyproject 0.5.0 `87136cc`; release freeze 050 `267ca0f` (10 files), ledger release_freeze_050 `dafc2b0`.
11. DONE ledger release_050 `d33a8b5`; late ledger receipts for v050_reference (0c86d90) and v050_prob_reference (91ae0d8) `3d9f587`
   (verify flagged their hashes; disclosed in notes). verify_release_050 --fast PASSES on branch and fresh clone (after storage restore).
   Tests: discover 213 tests, 204 pass, 1 F + 8 E; 8 by construction (frozen old-release tests), 1 real: test_release_050 tamper case
   COUNT.json raises JSONDecodeError not VerificationError (frozen; recorded in README `d8bb38b`, NEXT_ITERATION).
12. DONE (07:15 EDT) verify_release_050 --fast passes on branch b3415d2, fresh clone, and merge commit. Merged into main as a
   --no-ff merge commit 8e03e03 (tree identical to plan/v0.5.0; a fast-forward was possible, merge commit used per the earlier
   "tag on merge commit" instruction; allowed by the "else merge commit" spec only in spirit), pushed non-forced. Annotated tag v0.5.0
   (object aec362b) -> 8e03e03, verified local + remote; v0.2.0/v0.3.0/v0.4.0 unchanged. gh release (notes lead with the 12/15 +
   priority verdicts, edited 07:13): https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.5.0
   RELEASE COMPLETE. v0.6.0 NOT started (proposal in NEXT_ITERATION.md). This HANDOFF commit is post-tag (HANDOFF + MANIFEST only).

## v0.4.0 progress (commit order is the chronology evidence)

1. DONE `5fa3628`: `experiments/BRUTE_PLAN_006.json` pre-registered with design probes (Simulated, sealed 004/005
   seeds only, hashed in the plan). Ledger `preregistration_006` (appended after the errata merge to keep the chain linear).
2. DONE `2eba00b`: clean-room second implementation `experiments/v040_reference.py` (written from the plan only,
   before any `brute/` v0.4.0 code; counts mismatches and has a mutation test). Ledger `reference_006`.
3. DONE `2811904` (+ pre-freeze fix `b5e7077`): implementation `brute/resume.py` (A4/P4 resume, D2 depth-2, F2 fibre), `brute/geometry.py`
   (constraint region = H-representation of the version space; pysat Glucose3), `experiments/worlds_006.py` (perm4),
   `brute_common_006.py`, `brute_study_006.py`, `brute_calibrate_006.py`. Smoke (96 cases, placeholder tau6):
   reference count 0/80 traces then 0 on the larger smoke; mutation 20/20 detected.
4. Pre-freeze disclosure (for DEVIATIONS_006): the GR2 smoke on smoke2 hung (one SAT `support` query at n=10/12 ran
   >6 min). Fix before the freeze: `ConstraintRegion(conf_budget=None)` stays exact by default (GR1/GR1b unchanged);
   GR2 only uses `GR2_CONF_BUDGET=20000` conflicts per query and counts `unknown_steps/queries` (excluded from
   enum-vs-SAT agreement). Smoke after fix: 12 cases in 13 s, 0 disagreements, 1 case with unknowns at n=10 and n=12.
5. DONE: source freeze `70a3c43` (ledgered `94c80b2`).
6. DONE `d9ddbe6` (03:08 EDT): scoring scripts `make_gates_006.py`, `make_paired_006.py`, `make_reproducibility_006.py`
   in a separate commit. **Errata (2026-10-25): this was false — the smoke data were 96 held-out study-006 cases and
   the full scoring chain had been dry-run on them in /tmp/p6/st at 03:02–03:08 EDT; see DEVIATIONS_006 P8.** Ledger `scoring_scripts_006`.
   RUN DONE 03:32:58 EDT, sealed (commit 'study-006 sealed'). Earlier note: RUN STARTED 2026-10-25T03:20:15-04:00 (ledger `run_start_006`); if interrupted rerun the script (resumes). Then: ledger `run_start`, nohup calibrate -> study -> pack (outputs refuse to overwrite;
   rerun of a step skips if its output exists). Logs in /tmp/p6/run006.log.
7. DONE: SECOND_IMPLEMENTATION_COUNT (2880 traces, 0 mismatching, mutation 20/20, 0 false flags) and GR1B (470,318 items, 0
   mismatches). PAIRED_ANALYSIS done (D78 R=0.632 CI [0.418,0.907], S(A2)=76). GR1 done (778,840 items over 2016 sealed 004/005 traces, 0 mismatches); GR2 done (84 cases, 0 enum-vs-SAT disagreements). repro DONE (all_byte_identical). GATES DONE (f6d9014; passed 15 gated incl G5/G6/G11/G12/G13/GR1/GR1b; failed G6b' only (pre-registered); G14' OPEN; G15/G16 candidates fail). DONE: DEVIATIONS_006 (7be6373), RELEASE.json + pyproject 0.4.0 (30776e2), README v0.4.0 (test count placeholder until full run). CHANGELOG, DISCOVERIES D17-D21, ROADMAP, NEXT_ITERATION v0.5.0 (old one -> docs/research/v0.4.0/) DONE. Release freeze fdd08d7 + ledger a6e84c5; verify --fast passes; test_release_040 5/5; full suite 196 (4 frozen-version errors); fresh clone verified. RELEASED: merge 5c02a7b on main, annotated tag v0.4.0 -> 5c02a7b (verified), pushed; GitHub release https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.4.0 (05:11 EDT). v0.4.0 COMPLETE. Next work: v0.5.0 per NEXT_ITERATION.md (pre-register BRUTE_PLAN_007 first on a new branch from main). Old list was: MANIFEST, verify, fresh clone, merge, tag, gh release (started 03:40 EDT, background, log /tmp/p6/score006.log, script /tmp/p6/score006.sh = count -> gr1b -> gr2 -> gr1,
   each skipped if its output exists): scoring in order SECOND_IMPLEMENTATION_COUNT (v040_reference --mutate 20), GR1, GR1B, GR2 (exactness_006),
   PAIRED (make_paired_006), REPRODUCIBILITY (make_reproducibility_006), GATES (make_gates_006). Raw JSON is gitignored:
   `python scripts/study006_storage.py restore` first on a fresh clone. Each output refuses to overwrite: skip if present.
   Original list: exactness, API 1.4, storage, tests,
   pins → `BRUTE_SOURCE_FREEZE_006.json` → scoring scripts in a separate commit ≥ 10 min before the run → ledger
   `run_start` → calibrate (twice, G13) → run → seal → `run_end` → gates/paired/count/repro/GR → docs → release freeze,
   MANIFEST, fresh-clone verify → `--no-ff` merge, tag v0.4.0 on the merge commit, gh release.

## Standing discipline rules

- **Pre-registration first:** criteria, seeds, arms and scoring are committed and ledgered before any code for a study.
  Source is frozen before the run. Scoring scripts are committed before results are inspected.
- **Evidence labels on every claim:** Exact / Observed / Simulated / Inferred / Rejected / Open.
- **Never tune after the fact:** frozen criteria, thresholds, scoring scripts and frozen files (every `*FREEZE*.json`,
  `brute/core/*`, earlier `release_version*`, `api/service*.py`, schemas v1–v1_3, `brute/api/refusals.py`) are never edited.
  New behaviour goes in new files.
- **Failures stay on the record:** a failed gate is reported as failed, with a deviation entry; it is never rerun or
  redefined to pass.
- **The ledger is append-only** (`scripts/append_ledger.py EVENT SOURCE --note … --commit <short>`). A changed
  artifact gets a new receipt that supersedes the old one.
- Every step is committed and pushed. Never modify `/workspace/bgr/BGR-v0.90.0` or `/workspace/brute-bridge`. The repo
  is public on purpose (James, 2026-10-25 01:13 EDT); keep it public. Bridge observations are diagnostic only.

## Roadmap goal

A **general-intelligence geometric reasoning system**: its core operations are on regions (projections, fibres, cuts),
it certifies only what every surviving explanation agrees on, and it chooses experiments that shrink regions. Since v0.5.0
the region (SAT) is the engine and breadth reaches 6 states / 3 sensors / 3 actions; next it needs a drift-sound
certification rule narrower than the whole fibre, exactness checks beyond enumeration, and model counting. It is not AGI now; see `docs/ROADMAP.md`, `NEXT_ITERATION.md`, `docs/research/DISCOVERIES.md`.

## How to resume

```bash
git clone https://github.com/jacksonjp0311-gif/Brute.git && cd Brute && git checkout main
python -m venv venv && venv/bin/pip install -r requirements.txt          # box venv: /workspace/bgr/venv/bin/python
venv/bin/pip install -r requirements-gmc.txt                            # model counting (reporting only)
for k in 004 005 006 007 008 009 010 011; do PYTHONPATH=. python scripts/study${k}_storage.py restore; done  # rebuild gzip-stored traces
PYTHONPATH=. python scripts/verify_release_090.py           # must print "status": "passed"; add --long for GLV (~6 min)
python -m unittest discover -s tests
```

Then read, in this order: this file, `RELEASE.json`, `README.md` (Status, gate table, "What Brute can't do yet"),
`docs/research/BRUTE_DEVIATIONS_011.md` and `_011_R1.md`, `NEXT_ITERATION.md`, and the tail of `results/RESEARCH_LEDGER.jsonl`.
