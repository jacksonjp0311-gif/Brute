# Brute changelog

## v0.39.0: arm A16 (apartness clauses plus the cube split, no fixed-colour clique) against frozen A14 on fresh clean 16-state worlds (study BRUTE-0390-A16-SCALE16-042, LEAN process)

**11 of 11 gates pass (G16, G16_sem, GPERM17, GQB17, G_sound, G10, GS_ref, GTI, G_PROC, G_RT, G_recount). Secondary GT16, GRR041 and GPH17 reported only.** All 60 arm jobs (30 cases) ran once and were sealed (240.1 s of 1800 s). *Observed*

### Timeline (EDT, 2026-10-31)

- Plan `c5cf6bd` (preregistration ledger `92c2085`, 01:30:47); erratum 1 `29ef4d5` (ledger `9bb7b2e`); build authorization (ledger `2c1ed4b`, 01:32:21); seedcheck `8247cf7` (ledger `c0f381b`, 01:38:29); A16 `fa3da46`; common and runner `0f4a56a`; recount `9cd9409`; reference `e5af6e0`; gates `4cfd873`, fix `8445e48`; release tooling `538622b`..`c8eedf1`; freeze tooling `d708dea`; tests `da9a212`; prefreeze smoke `6c40060`, `9d9fb8e`, result `e6ea45d` (LPT projection 128.2 s, no cut); recount_041b `b6f67f2`; #157 `28b7269`, `6ef93ad` (ledger `4c060b3`); source freeze `4af660b` (ledger `ae64fea`).
- Run start (ledger `405f17b`, 02:06:30); runner to about 02:10:35; snapshot `a6603b9`; seal `719953c` (ledger `d0e1bd3`); recount `ca43ced` (PASS, ledger `24767aa`); reference `6af5717` (ledger `0354cb1`); tests `f33750b` (ledger `35e9d62`); RECOUNT_041B `4655c34`; gates `d774d8c` (ledger `cbed51f`); #158 `4302227` (ledger `d86ba08`).

### Results (recount labels; Wilson 95% in GATES_042.json)

| key | A16 ID | A16 AMB | A16 IDU | A14 ID | A14 AMB | A14 IDU | WRONG |
|---|---|---|---|---|---|---|---|
| scale16 (12) | 8 [0.39, 0.86] | 1 | 3 [0.09, 0.53] | 0 [0, 0.24] | 1 | 11 [0.65, 0.99] | 0 |
| perm12 (12) | 12 [0.76, 1.00] | 0 | 0 | 11 [0.65, 0.99] | 0 | 1 | 0 |
| control (6) | 6 [0.61, 1.00] | 0 | 0 | 6 [0.61, 1.00] | 0 | 0 | 0 |

- G16 PASS (A16 8/12 >= 6, gain 8 >= 3). GPERM17 11/11 agree [0.74, 1.00]. GQB17 max 9.515 s, 0 kills, 1494 calls. G_sound 311 words, 0 unsound. GS_ref 9 decided, 0 mismatches, 20/20 mutations. IDF 0 everywhere. *Observed*
- Secondary: GT16 call wall A16/A14 0.82 [0.71, 0.95] (scale16 0.73 [0.62, 0.85]); GRR041 re-recount of sealed 041 with the AMB rule: 25 BAD_stop -> AMB, 0 mismatching cases. Deviations #157, #158.

## v0.38.0: an encoding audit of A15 (five encodings E0-E4 replayed on sealed traces, hard per-call cap) and a fresh GINC15 replication (study BRUTE-0380-ENCODING-AUDIT-041, LEAN process)

**8 of 13 gates pass (GAUD_loc, GAUD_stab, GAUD_time, GQB16, GS_ref, GTI, G_PROC, G_RT). GAUD_sem, G10, G_sound, G_recount and GPERM16 FAIL. Secondary GCLS16 and GPH16 reported only.** All 294 jobs (240 replays, 18 fresh cases) ran once and were sealed (157.4 s of 1800 s). *Observed*

### Timeline (EDT, 2026-10-31)

- Plan `18cc782` (preregistration ledger `7f96b72`, 00:11:14); seedcheck `ada2447` (ledger `ad779d5`, 00:19:12); build authorization (ledger `55c87e4`, 00:19:23); encaudit16 `2317f61`; solver proxy `a647be6`; common `5bb6385`; runner `e34a624`; tests `fd0a628`, `7fccafc`; recount `8e46c45`; reference `2839145`; test runner `cb5e04f`; gates `5041256`; prefreeze script `27f9c6f`; storage `4dd310c`; release tooling `bb26a0c`; freeze tooling `0f2febb`; pre-freeze sealed-smoke gates `bb29ed4` (projection 565.1 s, no reduction); #154 `27e70eb`; source freeze `a649dd2` (ledger `2d9021f`).
- Run start (ledger `a24ceb5`, 00:35:49); runner to about 00:38:28; snapshot `2b71565`; seal `5221d1c` (ledger `1799529`); recount `d9e27fd` (FAIL, ledger `ec8bf54`); reference `2fcb46c` (ledger `c7827c8`); tests `4aaab70` (ledger `373c6c9`); gates `40d1484`; #155 `67371f6`.

### Results (Wilson / bootstrap 95% in GATES_041.json)

| part | E0 (A14) | E1 apartness | E2 clique | E3 (A15) | E4 (A15_cube) |
|---|---|---|---|---|---|
| a: 30 sealed 039 A14 decisions, decided | 30/30 | 30/30 | 28/30 | 28/30 | 28/30 |
| b: 2 GINC15 traces x 3 repeats, decided | 6/6 | 6/6 | 3/6 | 0/6 | 0/6 |
| c: 12 sealed 040 scale16 traces, decided | 2/12 | 10/12 | 10/12 | 10/12 | 12/12 |
| mean per-trace call-wall ratio vs E0 (a, c) | 1 | 1.11 [1.01, 1.24] | 4.18 [2.53, 6.46] | 16.11 [5.13, 31.74] | 10.41 [4.13, 20.78] |

- GAUD_loc PASS: the fixed-colour clique (E2) reproduces the GINC15 loss in 3/3 repeats; E1 matches E0 in 3/3. GAUD_stab 10/10 [0.72, 1.00]. GQB16 max 10.012 s, 15 hard kills. Fresh: every arm ID 11/12 perm12 [0.65, 0.99] and 6/6 controls; GPERM16 10/11 agree [0.62, 0.98] (10710005). *Observed*
- G_recount FAIL: 25 part-c replays stop AMB, which the frozen recount does not cover; GAUD_sem, G10, G_sound fail through it (#155). The frozen verify_release_0380 fails its commit-order item (the build authorization names the plan it authorizes); verify with the addendum verify_release_0380a (#156). Deviations #154, #155, #156.

## v0.37.0: an apartness-clique SAT encoding (A15) and a per-size cube split on capped queries (A15_cube) for clean active identification at 16 and 14 states and a one-bit-observation family (study BRUTE-0370-APART-CUBE-040, LEAN process)

**7 of 12 gates pass (G10, GREP15, GS_ref, G_PROC, G_RT, G_recount, G_sound). GC15_headline FAILS on c and d (a and b pass); GFAM15, GINC15, GQB15 and GTI FAIL. Secondary GCAP15 and GSYM15 reported only.** All 42 cases (126 jobs) ran once and were sealed (374.1 s of 1800 s). *Observed*

### Timeline (EDT, 2026-10-30)

- Plan `401172b` (preregistration ledger `a9219a1`, 23:08:30); build authorization (ledger `43b9592`, 23:08:41); seedcheck `7d4317b` (ledger `7de9f3a`); scalesearch15 `349a77b`; worlds `69eaf29`; common `117af5e`; runner `aba4b63`; tooling `a1e9563`, `c01b646`, `67d3960`; tests `610a592`, `7c51f35`; pre-freeze sealed-smoke gates `d80c798` (projection 391.6 s, no amendment); #152 `06c41d0`; source freeze `9001029` (ledger `efe3520`).
- Run start (ledger `f0cf26d`, 23:37:20); runner to about 23:43:37; snapshots `66b9a3a`, `c2f4f3a`; seal `b1da397` (ledger `c14e217`); recount `68bda8d`; reference `fc93389` (finished during an agent interruption, checked complete, not rerun); tests `1a092da`; gates `bfae53d`; #153 `798a93e`.

### Results (ID / IDF / AMB / WRONG / IDU per 12 cases; Wilson 95% in GATES_040.json)

| family | A15_cube | A15 | A14 |
|---|---|---|---|
| scale16 | 3/4/0/0/5 | 1/2/0/0/9 | 2/2/0/0/8 |
| scale14 | 8/1/0/0/3 | 6/1/0/0/5 | 8/1/0/0/3 |
| lowobs12 | 0/0/0/0/12 | 0/0/0/0/12 | 0/0/0/0/12 |
| control (6) | 6/0/0/0/0 | 6/0/0/0/0 | 6/0/0/0/0 |

- b: ID+IDF(A15_cube, scale16) 7/12 [0.32, 0.81] (bar 4). c: ID(A15_cube)-ID(A14) scale16 +0.083 [-0.167, 0.333] (bar +0.25, CI lower > 0). d: capped cases 9/12 [0.47, 0.91] (bar 6). GREP15 scale14 9 vs 9 [0.47, 0.91]. GFAM15 0/12 [0, 0.24]. GINC15 3/60. GQB15 max 11.014 s. *Observed*
- Branches fired (Inferred): GINC15 failed, so an encoding audit, not a new arm; GFAM15 failed while b passed, so the gain is family-specific. Deviations #152, #153.

## v0.36.0: one incremental SAT instance per candidate size (A14) for clean active identification at 12, 14 and 16 states plus a second world family (study BRUTE-0360-CLEAN-SCALE-039, LEAN process)

**12 of 13 gates pass (GFAM14, GREP14, GCH14, GINC14, GQB14, G_sound, G10, GS_ref, GTI, G_PROC, G_RT, G_recount). GC14_headline FAILS on b and c (a and d pass). Secondary GK14 and GACT14 reported only.** All 54 cases (162 jobs) ran once and were sealed (309.6 s of 1800 s). *Observed*

### Timeline (EDT, 2026-10-30)

- Plan `d2ebf63`; build authorization (ledger `0f90554`, 22:11:22, standing go t133s553, ledger 76b30d5); seedcheck `a7212f9` (ledger `2587d4c`); release tooling `46a8a0c`, `24f3e4c`; freeze tooling `cc1acdf`; gates fix `02e7a20`; script tests and smoke `a1fdafe`; pre-freeze sealed-smoke gates `3979ecb` (22:26, projection 312.1 s, no amendment); #150 `cc0a495`; source freeze `afc8eff` (ledger `c066e4c`).
- Run start (ledger `aef5112`, 22:36:33); runner to about 22:41:47; snapshots `0d20c04`, `963501f`; seal `44f79e3` (ledger `33608a0`); recount `879d6ac`; reference `cd54bae`; tests `66c8652`; gates `12ab5d2`; #151 `12815da`.

### Results (ID / IDF / AMB / WRONG / IDU per 12 cases; Wilson 95% in GATES_039.json)

| family | A14 | A14_k64 | A14_random | A9 (frozen) |
|---|---|---|---|---|
| scale16 | 0/0/0/0/12 | 0/0/0/0/12 | 0/0/4/0/8 | 1/0/0/0/11 |
| scale14 | 7/1/0/0/4 | 7/1/0/0/4 | 0/0/10/0/2 | 7/1/0/0/4 |
| scale12 | 10/2/0/0/0 | 9/2/1/0/0 | 0/0/12/0/0 | 9/2/1/0/0 |
| perm12 | 12/0/0/0/0 | 12/0/0/0/0 | 10/0/2/0/0 | 12/0/0/0/0 |
| control (6) | 6/0/0/0/0 | 6/0/0/0/0 | 6/0/0/0/0 | 6/0/0/0/0 |

- b: ID+IDF(A14, scale16) 0/12 [0.00, 0.24] (bar 4); capped 12/12. c: ID(A14)-ID(A9) scale16 -0.083 [-0.25, 0.00]. d: scale14 8/12 [0.39, 0.86]. GCH14 +0.292 [0.125, 0.458]. GQB14 max 9.563 s. *Observed*
- Branches fired (Inferred): caps dominant at n = 16 (per-size cube split or symmetry-free fixed-start encoding); 14 states is the current ceiling. Deviations #150, #151.

## v0.35.0: an incremental totalizer (A13: one incremental SAT instance per step for the least-B search, and a single-query B_max confirmation at n = N) for active identification on noisy traces (study BRUTE-0350-INCREMENTAL-LEASTB-038, LEAN process)

**10 of 12 gates pass (GSAFE13, GINC13, GQB13, G_sound, G10, GS_ref, GTI, G_PROC, G_RT, G_recount). GR13_headline FAILS on b, c and d (a passes); GNR13 FAILS. Secondary GH2 and GPR13 fail.** All 42 cases ran once and were sealed (451.0 s of 1800 s). *Observed*

### Timeline (EDT, 2026-10-30)

- Plan `e070773` (ledger `23c5a63`); build authorization (ledger `bbda857`, 20:58, standing go t133s553, ledger 76b30d5); seedcheck `12d0fde` (ledger `f8aa0e7`, before any seed); A13 `1796a72`; tests `7616856`; common `41cb3fd`; runner `f294fbf`, `1fb01fc`; recount `c0851ac`; CNF reference `a44fe94`; gates `fd455a3`; checkpoint and storage `dda4057`, `5803493`, `424df2b`; release tooling `fd616ef`, `53093fe`, `901acf8`, `41b982f`; freeze tooling `de7725c`, `fbe6225`; smoke tooling `e900aef`; script tests `91d8dce`; #148 `97447a1`, `ee78778`, `91bc6df`; pre-freeze sealed-smoke gates `54d49a2` (21:21-21:31); source freeze `e5f45a0` (ledger `0ca5360`).
- Run start (ledger `6000c37`, 21:40:30); runner 21:40:42-21:48:03; 2 pushed checkpoint snapshots `9d59f40`, `f4d4b79`; agent session interrupted while polling after the run (run unaffected, nothing relaunched; #149 item 2); seal `b78314c` (run end ledger `e6cca77`); recount `bbb3111`; reference `37024f1`; tests `53fba90`; gates `bbd1023`; #149 `4f64c6b`; RELEASE.json `96da542`.

### Results (labels per case x [Wilson 95% CI]; capped-confirmation cases Wilson; reads and B_final means with seed-bootstrap 95% CI)

| arm / key | ID | IDF | AMB | WRONG | IDU | capped-confirmation cases | reads mean [CI] | B_final mean [CI] |
|---|---|---|---|---|---|---|---|---|
| A13_r5 / noisy_scale8 | 2 [0.05,0.45] | 8 [0.39,0.86] | 1 [0.01,0.35] | 0 [0.00,0.24] | 1 [0.01,0.35] | 1/12 [0.01,0.35] | 976 [939,1025] | 0.25 [0.00,0.50] |
| A13_r3 / noisy_scale8 | 0 [0.00,0.24] | 0 [0.00,0.24] | 0 [0.00,0.24] | 0 [0.00,0.24] | 12 [0.76,1.00] | 10/12 [0.55,0.95] | 574 [554,596] | 2.08 [1.33,2.83] |
| A12_r5 / noisy_scale8 | 2 [0.05,0.45] | 8 [0.39,0.86] | 1 [0.01,0.35] | 0 [0.00,0.24] | 1 [0.01,0.35] | 1/12 [0.01,0.35] | 972 [937,1021] | 0.25 [0.00,0.50] |
| A12_r3 / noisy_scale8 | 0 [0.00,0.24] | 0 [0.00,0.24] | 0 [0.00,0.24] | 0 [0.00,0.24] | 12 [0.76,1.00] | 10/12 [0.55,0.95] | 562 [544,584] | 1.67 [1.00,2.25] |
| A11_r3 / noisy_scale8 | 5 [0.19,0.68] | 1 [0.01,0.35] | 0 [0.00,0.24] | 0 [0.00,0.24] | 6 [0.25,0.75] | n/a | 546 [534,560] | 0.83 [0.25,1.42] |
| S7 / noisy_scale8 | 0 [0.00,0.24] | 0 [0.00,0.24] | 0 [0.00,0.24] | 0 [0.00,0.24] | 12 [0.76,1.00] | n/a | 177 [177,177] | 27.00 [27.00,27.00] |
| A13_r5 / noisy_scale12 | 1 [0.01,0.35] | 0 [0.00,0.24] | 0 [0.00,0.24] | 0 [0.00,0.24] | 11 [0.65,0.99] | 7/12 [0.32,0.81] | 973 [922,1034] | 0.33 [0.08,0.58] |
| A13_r3 / noisy_scale12 | 0 [0.00,0.24] | 0 [0.00,0.24] | 0 [0.00,0.24] | 0 [0.00,0.24] | 12 [0.76,1.00] | 0/12 [0.00,0.24] | 532 [531,536] | 0.17 [0.00,0.50] |
| A12_r5 / noisy_scale12 | 0 [0.00,0.24] | 0 [0.00,0.24] | 0 [0.00,0.24] | 0 [0.00,0.24] | 12 [0.76,1.00] | 9/12 [0.47,0.91] | 959 [915,1011] | 0.42 [0.08,0.83] |
| A12_r3 / noisy_scale12 | 0 [0.00,0.24] | 0 [0.00,0.24] | 0 [0.00,0.24] | 0 [0.00,0.24] | 12 [0.76,1.00] | 0/12 [0.00,0.24] | 532 [531,536] | 0.33 [0.00,0.83] |
| A11_r3 / noisy_scale12 | 0 [0.00,0.24] | 0 [0.00,0.24] | 0 [0.00,0.24] | 0 [0.00,0.24] | 12 [0.76,1.00] | n/a | 531 [531,531] | 0.00 [0.00,0.00] |
| S7 / noisy_scale12 | 0 [0.00,0.24] | 0 [0.00,0.24] | 0 [0.00,0.24] | 0 [0.00,0.24] | 12 [0.76,1.00] | n/a | 177 [177,177] | 27.00 [27.00,27.00] |
| A13_r5 / clean_scale12 | 0 [0.00,0.24] | 0 [0.00,0.24] | 3 [0.09,0.53] | 0 [0.00,0.24] | 9 [0.47,0.91] | 8/12 [0.39,0.86] | 1054 [988,1119] | 0.00 [0.00,0.00] |
| A13_r3 / clean_scale12 | 0 [0.00,0.24] | 0 [0.00,0.24] | 3 [0.09,0.53] | 0 [0.00,0.24] | 9 [0.47,0.91] | 8/12 [0.39,0.86] | 632 [592,672] | 0.00 [0.00,0.00] |
| A12_r5 / clean_scale12 | 0 [0.00,0.24] | 0 [0.00,0.24] | 3 [0.09,0.53] | 0 [0.00,0.24] | 9 [0.47,0.91] | 8/12 [0.39,0.86] | 1054 [988,1119] | 0.00 [0.00,0.00] |
| A12_r3 / clean_scale12 | 0 [0.00,0.24] | 0 [0.00,0.24] | 3 [0.09,0.53] | 0 [0.00,0.24] | 9 [0.47,0.91] | 8/12 [0.39,0.86] | 632 [592,672] | 0.00 [0.00,0.00] |
| A11_r3 / clean_scale12 | 7 [0.32,0.81] | 1 [0.01,0.35] | 3 [0.09,0.53] | 0 [0.00,0.24] | 1 [0.01,0.35] | n/a | 632 [592,672] | 0.00 [0.00,0.00] |
| S7 / clean_scale12 | 0 [0.00,0.24] | 0 [0.00,0.24] | 0 [0.00,0.24] | 0 [0.00,0.24] | 12 [0.76,1.00] | n/a | 177 [177,177] | 27.00 [27.00,27.00] |
| A13_r5 / control | 6 [0.61,1.00] | 0 [0.00,0.39] | 0 [0.00,0.39] | 0 [0.00,0.39] | 0 [0.00,0.39] | 0/6 [0.00,0.39] | 885 [885,885] | 0.00 [0.00,0.00] |
| A13_r3 / control | 6 [0.61,1.00] | 0 [0.00,0.39] | 0 [0.00,0.39] | 0 [0.00,0.39] | 0 [0.00,0.39] | 0/6 [0.00,0.39] | 531 [531,531] | 0.00 [0.00,0.00] |
| A12_r5 / control | 6 [0.61,1.00] | 0 [0.00,0.39] | 0 [0.00,0.39] | 0 [0.00,0.39] | 0 [0.00,0.39] | 0/6 [0.00,0.39] | 885 [885,885] | 0.00 [0.00,0.00] |
| A12_r3 / control | 6 [0.61,1.00] | 0 [0.00,0.39] | 0 [0.00,0.39] | 0 [0.00,0.39] | 0 [0.00,0.39] | 0/6 [0.00,0.39] | 531 [531,531] | 0.00 [0.00,0.00] |
| A11_r3 / control | 6 [0.61,1.00] | 0 [0.00,0.39] | 0 [0.00,0.39] | 0 [0.00,0.39] | 0 [0.00,0.39] | n/a | 531 [531,531] | 0.00 [0.00,0.00] |
| S7 / control | 6 [0.61,1.00] | 0 [0.00,0.39] | 0 [0.00,0.39] | 0 [0.00,0.39] | 0 [0.00,0.39] | n/a | 177 [177,177] | 27.00 [27.00,27.00] |

- GR13 a: recounted WRONG 0 for A13_r5 and A13_r3 on all 42 gated cases, no label mismatch: PASS. b: IDU(A12_r3) - IDU(A13_r3) noisy12 0.00 [0.00, 0.00] (bar 0.25, lower > 0): FAIL. c: ID + IDF(A13_r5, noisy12) 1/12 [0.01, 0.35] (bar 5): FAIL. d: capped-confirmation cases A13_r5 clean12 8/12 [0.39, 0.86] (bar <= 2): FAIL.
- GSAFE13 (Exact): the sealed v0.33.0 WRONG trace (noisy_scale8 10210002) gives AMB under confirm13 (future SAT at n = 8, rival n 8), the same verdict as A12. PASS. GINC13: 13 decided items of the sealed 037 reference set, 13 at raised B, 0 mismatches (2 skipped where A12 was capped). PASS.
- GNR13: B_final 0 on every clean case, but 18 label differences (A13 IDU where A11_r3 ID/IDF on 9 clean12 cases per A13 arm): every B_max confirmation that ran on clean12 hit the 9 s cap (8/8 per A13 arm, walls 9.01-9.25 s; the pre-freeze smoke had shown it, #148 item 11). FAIL.
- GH2 (secondary): capped-confirmation cases A12 36 vs A13 34 (bar 6): FAIL. GPR13 (secondary): capped least-B probes A13_r3 11 vs A12_r3 10: FAIL. GQB13: max 9.711 s (S7; A13 9.249 s). G_sound: 999 words, 82 from confirmations, 0 unsound. GS_ref: A13_r3 noisy8, 343 decided (322 at raised B), 25 confirmation items, 0 mismatches, mutations 20/20. G_RT 451.0 s.

### What Brute can't do yet

- It cannot yet identify a noisy 12-state machine with a sound stop: A13_r5 ID+IDF 1/12, A13_r3 0/12. *Observed.*
- An incremental totalizer does not bring the least-B or confirmation queries under the 9 s cap at 12 states. *Observed.*
- Its B_max confirmation costs more than the cap even on clean 12-state traces with B 0. *Observed.*
- Its soundness still assumes the declared size N and the declared noise rate. *Exact / Open.*
- 16-state worlds and other world families were not tested this release. *Open.*

Deviations #148 (pre-run), #149 (post-run). Verify: `python scripts/study038_storage.py restore && PYTHONPATH=. python scripts/verify_release_0350.py`.

## v0.34.0: a sound noisy stop (A12: doubling-then-bisection least-B search and a confirmation at B_max before any ID claim) for active identification on noisy traces (study BRUTE-0340-SOUND-NOISY-STOP-037, LEAN process)

**9 of 11 gates pass (GSAFE12, GQB12, G_sound, G10, GS_ref, GTI, G_PROC, G_RT, G_recount). GR12_headline FAILS on b, c and d (a passes); GNR12 FAILS. Secondary GPR12 passes.** All 42 cases ran once and were sealed (443.1 s of 1800 s). *Observed*

### Timeline (EDT, 2026-10-30)

- Plan `de168d1` (20:09; ledger `9d6a70e`); build authorization (ledger `b789fb9`, 20:10, standing go t133s553, ledger 76b30d5); seedcheck `18b3e90` (ledger `dbbc74a`, 20:21, before any seed); A12 `20f8fd8`; tests `e79f245`; common `b4b4bf4`; runner `4dfb973`; recount `4eff368`; CNF reference `d82e850`; gates `19d737c`, `4dc608a`; checkpoint and storage `1ec9a8c`; release tooling with the scratch-default test runner `5d85377`; freeze and smoke tooling `90fe99c`; script tests `18ce605`; #146 `eb34849`, `fbd6865`; pre-freeze sealed-smoke gates `726c7c6`; source freeze `d9402a1` (20:39; ledger `115b0cc`).
- Run start (ledger `730e9b3`, 20:39:17); 2 pushed checkpoint snapshots `4bb4b36`, `e2b381c`; seal `116e9e9` (run end ledger `47654af`, 20:47); recount `794e56d`; reference `d1b5860`; tests `57d5da4`; gates `15c64a1`; #147 `ac0d829` and erratum `a994746`; RELEASE.json `96776d2`.

### Results (labels per case, ID / IDF / AMB / WRONG / IDU; Wilson 95% CI; paired contrasts and means seed-bootstrap 95% CI)

| arm | B_max | noisy12 (n=12) | noisy12 ID CI | noisy12 IDU CI | noisy12 reads/case | noisy8 (n=12) | clean12 (n=12) | controls ID |
|---|---|---|---|---|---|---|---|---|
| A12_r5 | 2 | 0 / 0 / 1 / 0 / 11 | [0, 0.24] | [0.65, 0.99] | 993 [940, 1053] | 4 / 7 / 0 / 0 / 1 | 0 / 0 / 1 / 0 / 11 | 6/6 |
| A12_r3 | 6 | 0 / 0 / 0 / 0 / 12 | [0, 0.24] | [0.76, 1] | 536 [531, 545] | 0 / 0 / 0 / 0 / 12 | 0 / 0 / 1 / 0 / 11 | 6/6 |
| A12_r3_nostop | 6 | 1 / 0 / 0 / 0 / 11 | [0.01, 0.35] | [0.65, 0.99] | 536 [531, 545] | 6 / 3 / 0 / 0 / 3 | 8 / 2 / 1 / 0 / 1 | 6/6 |
| A11_r3 (v0.33.0) | 6 | 0 / 0 / 0 / 0 / 12 | [0, 0.24] | [0.76, 1] | 531 [531, 531] | 0 / 1 / 0 / 0 / 11 | 8 / 2 / 1 / 0 / 1 | 6/6 |
| A11_r5 (v0.33.0) | 2 | 5 / 0 / 1 / 0 / 6 | [0.19, 0.68] | [0.25, 0.75] | 982 [926, 1044] | 8 / 4 / 0 / 0 / 0 | 8 / 2 / 1 / 0 / 1 | 6/6 |
| S7 (passive) | 27 | 0 / 0 / 0 / 0 / 12 | [0, 0.24] | [0.76, 1] | 177 | 0 / 0 / 0 / 0 / 12 | 0 / 0 / 0 / 0 / 12 | 6/6 |

- GR12 a: recounted WRONG 0 for A12_r5 and A12_r3 on all 42 gated cases, no label mismatch: PASS. b: IDU(A11_r3) - IDU(A12_r3) noisy12 0.00 [0.00, 0.00] (bar 0.25, lower > 0): FAIL. c: ID + IDF(A12_r5) 0/12 (bar 5): FAIL. d: ID(A12_r5) - ID(A11_r5) -0.42 [-0.67, -0.17] (bar >= -1/12): FAIL.
- GSAFE12 (Exact): the sealed v0.33.0 WRONG trace (noisy_scale8 10210002) now gives AMB: future mode UNSAT for n = 1..7, SAT at n = 8. PASS.
- GNR12: B_final 0 on every clean case, but 20 label differences (A12_r5 and A12_r3 IDU where A11_r3 ID/IDF on 10 clean12 cases each): the B_max confirmation hit the 9 s cap. FAIL. A12_r3_nostop: no differences.
- GPR12 (secondary): capped least-B probes A12_r3 11 against A11_r3 12; first probe capped 6/12 against 12/12: PASS. GQB12: max 10.332 s (S7). G_sound: 678 words, 18 from confirmations, 0 unsound. GS_ref: A12_r3 noisy8, 240 decided (225 at raised B), 54 confirmation items, 0 mismatches, mutations 20/20. G_RT 443.1 s.

### What Brute can't do yet

- It cannot yet identify a noisy 12-state machine with a sound stop: A12_r5 ID 0/12, A12_r3 0/12. *Observed.*
- Its B_max confirmation query costs more than the 9 s cap at 12 states, even on clean traces. *Observed.*
- Its per-B least-budget chain still hits the cap on every noisy 12-state A12_r3 case. *Observed.*
- Its soundness still assumes the declared size N and the declared noise rate. *Exact / Open.*

Deviations #146 (pre-run), #147 and its erratum (post-run). Verify: `python scripts/study037_storage.py restore && PYTHONPATH=. python scripts/verify_release_0340.py`.

## v0.33.0: repeated reads (A11: a per-bit majority of r reads with a smaller noise budget B_max(r) and a bisection least-B search) for active identification on noisy traces (study BRUTE-0330-REPEATED-READS-036, LEAN process)

**8 of 11 gates pass (GNR11, G_sound, G10, GS_ref, GTI, G_PROC, G_RT, G_recount). GR11_headline FAILS on a, b, c and d; GBIS11 FAILS; GQB11 FAILS (A11_r3_up query 10.513 s; bound 10.5 s). Secondary GRB11 fails.** All 48 cases ran once and were sealed (420.3 s of 1800 s). *Observed*

### Timeline (EDT, 2026-10-30)

- Plan `3ab989d` (19:20; ledger `67513fa`); build authorization (ledger `ed8452b`, 19:21, standing go t133s553, ledger 76b30d5); seedcheck `0a9ae7c` (ledger `0eac98d`, 19:32, before any seed); A11 `9b5260c`; runner `528a47d`; recount `5ce8af9`; CNF reference `fe4d776`; gates `fb7825d`; tooling `6707700`; release tooling `58fe718`, `8794035`, `3c09232`; pre-freeze sealed-smoke gates `34456cb`; #144 `f095643`, `fb2199a`; source freeze `730aef4` (19:46; ledger `2a393ff`).
- Run start (ledger `e972a23`, 19:47:07); 3 pushed checkpoint snapshots `43b5e2f`, `21fdeca`, `0bfe2b7`; seal `d89c1ea` (run end ledger `bd46789`, about 19:54); recount `40f009d`; reference `faaf741`; tests `088da1e`; gates `bff753f`; #145 `7e16c0a`; RELEASE.json `02d6dcb`.

### Results (labels per case, ID / IDF / AMB / WRONG / IDU; Wilson 95% CI; paired contrasts and mean B seed-bootstrap 95% CI; rps = reads per step)

| arm | rps | noisy12 (n=12) | noisy12 ID CI | noisy12 IDU CI | noisy12 mean B_final | noisy12_extra (n=6) | noisy8 (n=12) | clean12 (n=12) | controls ID |
|---|---|---|---|---|---|---|---|---|---|
| A11_r3 (B_max 6) | 3 | 2 / 0 / 0 / 0 / 10 | [0.05, 0.45] | [0.55, 0.95] | 0.25 [0, 0.67] | 0 / 0 / 1 / 0 / 5 | 2 / 2 / 0 / 1 / 7 (B 1.0 [0.33, 1.83]) | 6 / 3 / 2 / 0 / 1 | 6/6 |
| A11_r5 (B_max 2) | 5 | 4 / 1 / 2 / 0 / 5 | [0.14, 0.61] | [0.19, 0.68] | 0.33 [0, 0.75] | 2 / 1 / 0 / 0 / 3 | 8 [0.39, 0.86] / 4 / 0 / 0 / 0 | 6 / 3 / 2 / 0 / 1 | 6/6 |
| A11_r3_up (upward least-B) | 3 | 3 / 0 / 0 / 0 / 9 | [0.09, 0.53] | [0.47, 0.91] | 0.33 | 0 / 0 / 1 / 0 / 5 | 4 / 3 / 0 / 1 / 4 (B 2.25) | 6 / 3 / 2 / 0 / 1 | 6/6 |
| A10 (v0.32.0) | 1 | 0 / 0 / 0 / 0 / 12 | [0, 0.24] | [0.76, 1] | 0 | 0 / 0 / 0 / 0 / 6 | 0 / 0 / 0 / 0 / 12 | 6 / 3 / 2 / 0 / 1 | 6/6 |
| S7 (passive, B = 27) | 1 | 0 / 0 / 0 / 0 / 12 | [0, 0.24] | [0.76, 1] | 27 | 0 / 0 / 0 / 0 / 6 | 0 / 0 / 0 / 0 / 12 | 0 / 0 / 0 / 0 / 12 | 6/6 |
| S5 (passive, clean) | 1 | 0 / 0 / 0 / 12 / 0 (not gated) | [0, 0.24] | [0, 0.24] | - | 0 / 0 / 0 / 5 / 1 | 0 / 0 / 0 / 5 / 7 | 1 / 0 / 10 / 0 / 1 | 6/6 |

Reads per case, noisy12: A10 177, A11_r3 559 [536, 588], A11_r5 998 [951, 1049].

- GR11 a: A11_r3 recounted WRONG 1 (noisy_scale8 10210002, within budget): FAIL. b: ID(A11_r3) - ID(A10) noisy12 +0.17 [0.00, 0.42] (bar 0.25, lower > 0): FAIL. c: ID + IDF 2/12 (bar 4): FAIL. d: IDU 10/12 (bar <= 3): FAIL.
- Reported, not gated: ID(A11_r5) - ID(A10) noisy12 +0.33 [0.08, 0.58]; ID(A11_r5) - ID(A11_r3) +0.17 [-0.17, 0.50]; ID(A11_r3) - ID(S7) +0.17 [0, 0.42].
- GBIS11: IDU(A11_r3) 10/12 against IDU(A11_r3_up) 9/12, paired +0.08 [0, 0.25]: FAIL. GQB11: A11_r3_up 10.513 s on noisy_scale12_extra 10240002 (A11_r3 9.58, A11_r5 9.62, A10 9.84, S5 9.90, S7 10.06): FAIL. GRB11 (secondary): FAIL.
- GNR11: A11 labels equal A10 labels on every clean case, B_final 0: PASS. G_sound: 674 words re-simulated, 0 unsound. GS_ref: 12 noisy_scale8 A11_r3 cases, 88 decided (75 at raised B), 1 undecided, 0 mismatches, mutations 20/20. G_RT 420.3 s.
- Diagnosis (Observed): the majority of 3 reads cut the truth's base flips from 13-20 to 0-5, but on 9 of 10 A11_r3 IDU cases the first bisection probe, at B_max = 6, hit the 9.5 s query cap. The one WRONG stopped ID at least B 1 while the truth needed 2 flips on that trace; the model matched the truth's future from the final state but not from the start state. *Observed / Inferred.*

### What Brute can't do yet

- It still mostly cannot identify a 12-state machine from noisy readings: A11_r3 ID 2/12, A11_r5 ID 4/12. *Observed.*
- Its least-budget ID claim is not sound under noise: one WRONG when the truth needed more flips than the least SAT budget. *Observed / Inferred.*
- Probing B_max first at 12 states is as hard as the queries it was meant to avoid (9 of 10 IDU cases capped on the first probe). *Observed.*
- Its in-solver cap still overshoots (10.513 s against 10.5 s). *Observed.*
- Its soundness still assumes the declared size N and the declared noise rate. *Exact / Open.*

Deviations #144 (pre-run) and #145 (post-run). Verify: `python scripts/study036_storage.py restore && PYTHONPATH=. python scripts/verify_release_0330.py`.

## v0.32.0: adaptive noise budget (A10: A9 with B = 0 until the exact search contradicts the trace) for active identification on noisy traces (study BRUTE-0320-NOISY-ACTIVE-ID-035, LEAN process)

**9 of 11 gates pass (GNR10, GAD10, G_sound, G10, GS_ref, GTI, G_PROC, G_RT, G_recount). GA10_headline FAILS on a, b, c and d; GQB10 FAILS (S7 query 10.538 s; bound 10.5 s). Secondary G16 fails (A10 ID 0/6).** All 48 cases ran once and were sealed (342.7 s of 1800 s). *Observed*

### Timeline (EDT, 2026-10-30)

- Plan `a66b74a` (18:11); build authorization (ledger `6941bf9`, 18:12, standing go t133s553, ledger 76b30d5); seedcheck `154d4c9` (ledger `c75bda0`, 18:32, before any seed); A10 `984f653`, `5bea1cf`; runner `be50919`; recount `5d55043`; CNF reference `57a44b3`, fix `461e1c3` (pre-data); gates `cf6788f`; tooling `5ec021e`, `1751321`; release tooling `9441ba5`; pre-freeze sealed-smoke gates `dc8b99c`; #142 `f8d4b6d`; source freeze `1764462` (18:53).
- Run start (ledger `3588e27`, 18:53:55); 2 pushed checkpoint snapshots `aafa3c7`, `ade7093`; run end (ledger `10f47c4`); seal `6ea1450`; recount `bf38714`; reference `3cce54f`; tests `0f1b0d7`; gates `76a0ddf`; #143 `f190bd5`.

### Results (labels per case, ID / IDF / AMB / WRONG / IDU; Wilson 95% CI on ID, WRONG and IDU; paired contrasts seed-bootstrap 95% CI; mean extra actions)

| arm | noisy12 ID | WRONG | IDU | noisy8 ID / IDF / AMB / WRONG / IDU | clean12 ID / IDF / AMB / WRONG / IDU | scale16 ID / AMB / IDU | controls ID | extra actions clean12 / noisy |
|---|---|---|---|---|---|---|---|---|
| A10 | 0/12 [0, 0.24] | 0 [0, 0.24] | 12 [0.76, 1] | 0 / 0 / 0 / 0 / 12 | 7 [0.32, 0.81] / 4 / 1 / 0 / 0 | 0 / 0 / 6 | 6/6 | 22.2 / 0 |
| A10_fixed (B = 27 from the start) | 0/12 | 0 | 12 | 0 / 0 / 0 / 0 / 12 | 0 / 0 / 0 / 0 / 12 | 0 / 0 / 6 | 6/6 | 0 / 0 |
| A9 (v0.31.0, not noise-aware) | 0/12 | 12 [0.76, 1] (not gated) | 0 | 0 / 0 / 0 / 12 / 0 | 7 / 4 / 1 / 0 / 0 | 0 / 0 / 6 | 6/6 | 22.2 / 0 |
| S7 (passive, noise budget) | 0/12 | 0 | 12 | 0 / 0 / 0 / 0 / 12 | 0 / 0 / 0 / 0 / 12 | 0 / 0 / 6 | 6/6 | 0 |
| S5 (passive, clean) | 0/12 | 9 [0.47, 0.91] | 3 | 0 / 0 / 0 / 6 / 6 | 0 / 0 / 12 / 0 / 0 | 0 / 4 / 2 | 6/6 | 0 |

- GA10 a: A10 and S7 recounted WRONG 0 on all 48 cases (all within budget); S5 WRONG 15 of 24 noisy cases: FAIL. b: ID(A10) - ID(S7) at noisy12 0.00 [0.00, 0.00] (bar 0.25): FAIL. c: ID + IDF 0/12 (bar 4): FAIL. d: IDU 12/12 (bar <= 3): FAIL.
- GNR10: A10 labels equal A9 labels on all 18 clean12 and control cases; B_final 0 on every clean case: PASS. GAD10: ID(A10) - ID(A10_fixed) clean12 +0.58 [0.33, 0.83] (bar 0.17), noisy12 0.00 (bar >= 0): PASS.
- Diagnosis (Observed): on all 24 noisy cases the B = 0 search was UNSAT, then the upward least-budget search hit the 10 s cap after 9-12 queries, below the true flip count (13-23 in 177 readings), so B stayed 0, no word was executed and A10 stopped IDU.
- GQB10: S7 10.523 s and 10.538 s on noisy_scale8 10110001 and 10110003; A10 max 10.289 s: FAIL. G_sound: 116 words re-simulated, 0 unsound. GS_ref: 12/12 noisy_scale8 A10 cases decided, 0 mismatches, mutations 20/20 (B = 0 verdicts only). G_RT 342.7 s.

### What Brute can't do yet

- It cannot identify a machine from noisy readings: A10 finished 0 of 24 noisy worlds because the least-budget search is capped before the true flip count. *Observed / Inferred.*
- Its in-solver cap still overshoots (S7 10.538 s against 10.5 s). *Observed.*
- It does not finish 16-state worlds (A10 ID 0/6, all IDU). *Observed.*
- Raised-budget verdicts were never exercised on main data, so the reference audit checked only B = 0. *Inferred.*
- Its soundness still assumes the declared size N and the declared noise rate. *Exact / Open.*

Deviations #142 (pre-run) and #143 (post-run). Verify: `python scripts/study035_storage.py restore && PYTHONPATH=. python scripts/verify_release_0320.py`.

## v0.31.0: sound active identification (A9: stop only when no consistent rival remains at any size up to the declared N) for hidden machines (study BRUTE-0310-SOUND-ACTIVE-ID-034, LEAN process)

**11 of 12 gates pass (GA9_headline, GDIAG8, GIDF9, GCH9, G_sound, G10, GS_ref, GTI, G_PROC, G_RT, G_recount). GQB9 FAILS (one A9 query took 10.888 s; bound 10.5 s).** All 36 cases ran once and were sealed (124.8 s of 1800 s). *Observed*

### Timeline (EDT, 2026-10-30)

- Plan `52b50be` (ledger `ea170d2`, 17:17); build authorization (ledger `b84deba`, 17:18, standing go t133s553); seedcheck `3426af5` (ledger `5576d08`, 17:24, before any seed); A9 `211f9b7`; runner `8ddfe0b`; recount `1649b71`; CNF reference `604a6d2`; gates `eb6b61d`; tooling `f78c07a`; release tooling `9480b23`; pre-freeze sealed-smoke gates `96e54de`; #140 `7f19efd`; source freeze `389e837` (17:55).
- Run start (ledger `5ab16bd`, 17:56:34); 1 pushed checkpoint snapshot `ffdb5b5`; run end (ledger `75b3eae`); seal `adb8563`; recount `3f3f052`; reference `74dd224`; tests `898bf08`; gates `b630337`; #141 `c2f5094`.

### Results (labels per case; Wilson 95% CI; paired contrasts seed-bootstrap 95% CI; IDF = identified up to the start state)

| arm | scale12 ID | IDF | AMB | WRONG | IDU | scale8 ID / IDF / AMB / WRONG | scale16 ID / AMB / WRONG / IDU | controls ID | actions used, scale12 mean |
|---|---|---|---|---|---|---|---|---|---|
| A9 | 9/12 [0.47, 0.91] | 1 | 1 | 0 [0, 0.24] | 1 | 8 / 4 / 0 / 0 | 0 / 2 / 0 / 4 | 6/6 | 28.8 (29.2 on ID cases) |
| A9_random (same count, random inputs) | 0/12 [0, 0.24] | 0 | 11 | 0 | 1 | 3 / 0 / 9 / 0 | 0 / 4 / 0 / 2 | 6/6 | 28.8 |
| A8 (v0.30.0 rule) | 8/12 [0.39, 0.86] | 0 | 2 | 1 [0.01, 0.35] | 1 | 8 / 0 / 4 / 0 | 1 / 2 / 1 / 2 | 6/6 | 31.9 (29.5 on ID cases) |
| S5 (passive) | 0/12 [0, 0.24] | 0 | 12 | 0 | 0 | 3 / 0 / 9 / 0 | 0 / 6 / 0 / 0 | 6/6 | 0 |
| S1 (passive) | 0/12 [0, 0.24] | 0 | 11 | 0 | 1 | 3 / 0 / 9 / 0 | 0 / 5 / 0 / 1 | 6/6 | 0 |

- GA9 a: recounted WRONG 0 for A9, A9_random, S5 and S1 on all 36 cases: PASS. b: paired ID(A9) - ID(S5) at 12 states +0.75 [0.50, 1.00] (bar 0.33, CI lower > 0): PASS. c: ID(A9) 9/12 (bar 5): PASS. d: IDU(A9) 1/12 (bar <= 2): PASS.
- GCH9: ID(A9) - ID(A9_random) at 12 states +0.75 [0.50, 1.00] (bar 0.17): PASS. GIDF9: ID + IDF (A9, 12 states) 10/12 [0.55, 0.95] (bar 8): PASS.
- GDIAG8: A8 WRONG 2 of 36 (scale16 10030003, n_min 14 of 16; scale12 10020007, n_min 11 of 12). Both stopped 'unique' below the truth's size: PASS. This replicates the #139 diagnosis.
- G_sound: 407 separating words re-simulated (235 A9), 0 unsound; the truth stayed consistent with every round. G10: controls ID 6/6 for A9 and S5. GS_ref: CNF reference 12/12 scale8 A9 cases decided, 77 verdicts and 46 words checked, 0 mismatches, mutations 20/20. GQB9: A9 max query 10.888 s on scale12 10020005 (bound 10.5): FAIL.
- IDF (Observed): all 5 A9 IDF answers match the truth on every future input. Only the start state is undetermined.

### What Brute can't do yet

- It does not finish 16-state worlds even with sound experiments (A9 ID 0/6: 4 IDU, 2 AMB with the budget spent). *Observed.*
- It cannot resolve start-state ambiguity (5 IDF cases). *Observed.*
- Its per-query time cap can overshoot (10.888 s against a 10.5 s bound). *Observed / Inferred.*
- Its soundness assumes the declared size N bounds the truth. An unknown or wrong N is untested. *Exact / Open.*
- Experiments are still untested with noise. *Open.*

Deviations #140 (pre-run) and #141 (post-run). Verify: `python scripts/study034_storage.py restore && PYTHONPATH=. python scripts/verify_release_0310.py`.

## v0.30.0: active experiments (A8: Brute chooses inputs that separate two consistent machines) for identifying hidden machines (study BRUTE-0300-ACTIVE-EXPERIMENTS-033, LEAN process)

**9 of 10 gates pass (GCH8, G10, GQB8, GS_ref, GTI, G_PROC, G_RT, G_recount, G_sound). GAE8 (headline) FAILS on clauses a (5 WRONG) and c (ID 5/12, bar 6).** All 36 cases ran once and were sealed (116.0 s of 1800 s). *Observed*

### Timeline (EDT, 2026-10-30)

- Plan `af07e35` (ledger 16:39); build authorization (ledger `cf62a8c`, 16:42, standing go t133s553); seedcheck `0e8bb67` (ledger `ab6ff21`, 16:55, before any seed); A8 `fa0c690`; runner `8661d42`; recount and CNF reference `51317f4`; gates `1b7c264`; tooling `23c033a`; release tooling `c3e6f05`; smoke-found runner fix and pre-freeze sealed-smoke gates `8b23acf`; #138 `dec7b5d`/`ac26d3c`; source freeze `09afb81` (17:05).
- Run start (ledger `9970615`, 17:05:54); 1 pushed checkpoint snapshot `4b67a3b`; run end (ledger `8f2910e`); seal `9b50062`; recount `ec0049e`; reference `8a9d525`; tests `a4867b1`; gates `b3d604b`; #139 `2c5f225`.

### Results (labels per case; Wilson 95% CI; paired contrasts seed-bootstrap 95% CI)

| arm | scale12 ID | AMB | WRONG | IDU | scale8 ID / AMB / WRONG | scale16 ID / AMB / IDU | controls ID | actions used, scale12 mean |
|---|---|---|---|---|---|---|---|---|
| A8 | 5/12 [0.19, 0.68] | 3 | 4 [0.14, 0.61] | 0 | 7 / 4 / 1 | 1 / 1 / 4 | 6/6 | 17.4 (11.2 on ID cases) |
| A8_random (same count, random inputs) | 0/12 [0, 0.24] | 12 | 0 | 0 | 3 / 9 / 0 | 0 / 3 / 3 | 6/6 | 17.4 |
| S5 (passive) | 0/12 [0, 0.24] | 12 | 0 | 0 | 3 / 9 / 0 | 0 / 6 / 0 | 6/6 | 0 |
| S1 (passive) | 0/12 [0, 0.24] | 12 | 0 | 0 | 3 / 9 / 0 | 0 / 4 / 2 | 6/6 | 0 |

- GAE8 a: recounted WRONG 5 for A8 (scale12 9920002, 9920005, 9920009, 9920012; scale8 9910012), 0 for every other arm: FAIL. b: paired ID(A8) - ID(S5) at 12 states +0.417 [0.167, 0.667] (bar 0.33, CI lower > 0): PASS. c: ID(A8) 5/12 (bar 6): FAIL. d: IDU(A8) 0/12 (bar <= 2): PASS.
- GCH8: ID(A8) - ID(A8_random) at 12 states +0.417 [0.167, 0.667] (bar 0.17): PASS. Chosen inputs, not more data, made the difference.
- G_sound: 109 separating words re-simulated, 0 unsound; the truth stayed consistent with every round and every final trace. G10: controls ID 6/6 for A8 and S5. GS_ref: CNF reference 12/12 scale8 cases decided, 0 mismatches, mutations 20/20. GQB8: max query 10.24 s (bar 10.5).
- Mechanism (Inferred, deviation #139): every WRONG stopped 'unique' at a size below the truth's (11/12, 11/12, 11/12, 10/12, 6/8). Uniqueness at the least consistent size is not identification. All 8 'indistinguishable' stops are same_future: start-state ambiguity that no input can resolve.

### What Brute can't do yet

- Its active stop rule claims identification too early: 5 of 36 A8 answers named a machine smaller than the truth. *Observed / Inferred.*
- It cannot resolve start-state ambiguity: 8 cases end with two machines that agree on every future input. *Observed.*
- It does not finish most 16-state worlds even with experiments (IDU 4/6 under the 10 s per-query cap). *Observed.*
- Active experiments were tested only without noise; combining them with the noise budget is untested. *Open.*

Deviations #138 (pre-run) and #139 (post-run). Verify: `python scripts/study033_storage.py restore && PYTHONPATH=. python scripts/verify_release_0300.py`.

## v0.29.0: exact search S7 (S5 plus a noise-budgeted flip encoding) for robust perception on noisy traces (study BRUTE-0290-ROBUST-PERCEPTION-032, LEAN process)

**6 of 9 gates pass (GQB7, GS_ref, GTI, G_PROC, G_RT, G_recount). GRP7 (headline) FAILS on clause d; GNR7 and G10 FAIL.** All 48 cases ran and were sealed (1246.3 s of 1800 s). *Observed*

### Timeline (EDT, 2026-10-30)

- Plan `5a00625` (15:50); build authorization (ledger `7d4242f`, 15:51, standing go t133s553); seedcheck `cad2416` (ledger `25ce5a7`, 16:01, before any seed); S7 `47e3006`; runner `d2eeb34`; reference, recount, gates and tooling `7885e02`; release tooling `6143c15`; pre-freeze sealed-smoke gates test `7429720`; #136 `b0c86e9`; source freeze `fd17c82`.
- Run start (ledger `fb5519c`, 16:09:44); 5 pushed checkpoint snapshots (last `0ec1f9b`); run end `c67472e` (16:30); seal `cbc801e`; recount `9975157`; reference `6e4684b`; tests `39e671a`; gates `7c4d197`; #137 `86ffb89`.

### Results (noisy cases at eps 0.05, clean cases at eps 0; X Wilson 95% CI, U seed-bootstrap 95% CI)

| arm | U_inf noisy 8 | U_inf noisy 12 | U_inf noisy 16 | X_inf noisy 12 | U clean 12 | U clean 16 | controls U / X | F_truth | contradiction verdicts |
|---|---|---|---|---|---|---|---|---|---|
| S7 | 0.443 [0.404, 0.486] | 0.467 [0.437, 0.499] | 0.495 [0.455, 0.541] | 0/12 [0, 0.242] | 0.407 [0.356, 0.460] | 0.444 [0.407, 0.479] | 0.085 / 0/6 | 0 | 0 |
| S7_contra (ablation) | 0.524 [0.452, 0.596] | 0.673 [0.567, 0.791] | 0.591 [0.542, 0.648] | 0/12 | 0.045 [0.003, 0.094] | 0.316 [0.258, 0.369] | 0 / 6/6 | 0 | 3 (9820003, 9820007, 9820010) |
| S5 | 0.524 [0.451, 0.596] | 0.576 [0.542, 0.609] | 0.590 [0.541, 0.648] | 0/12 | 0.044 [0.003, 0.094] | 0.320 [0.265, 0.369] | 0 / 6/6 | 0 | 0 |
| S1 | 0.561 [0.465, 0.669] | 0.644 [0.560, 0.749] | 0.643 [0.543, 0.793] | 0/12 | 0.219 [0.176, 0.269] | 0.383 [0.342, 0.426] | 0 / 6/6 | 12 | 4 (9810001, 9820003, 9820007, 9830002) |

- GRP7 a: F_truth(S7) 0 on 45 checked cases (27 noisy within B, 18 clean and control); 3 noisy 8-state cases were outside B (S7 F_truth 0 there too): PASS. b: paired U_inf(S7) - U_inf(S5) at noisy 12 states -0.109 [-0.154, -0.054]: PASS. c: vs S1 -0.178 [-0.283, -0.084]: PASS. d: X_inf(S7) 0/12 (bar 3/12): FAIL. e: S7 grammar_contradicted 0: PASS.
- GNR7: clean 12-state U(S7) - U(S5) +0.362 [0.348, 0.377] (bar <= +0.05, CI upper <= +0.08): FAIL; S5_in_S7 0 mismatches in 5566 eps-0 comparisons.
- G10: S7 on controls U 0.085 [0.042, 0.129], F_truth 0: FAIL. GQB7: S7 max query 9.35 s (S7_contra 10.68 s, informational). GS_ref: 0 mismatches over 3526 exact S7 answers, mutations 20/20; 0 codes decided impossible.
- Mechanism (Inferred, counters): the budget B_end 27 applies on clean traces too. S7/S5 throughput is 0.53 at clean 12 states and 0.10 on controls.

### What Brute can't do yet

- It finishes no noisy world (X_inf 0/12 at 12 states for every arm). *Observed.*
- A fixed noise budget costs it on clean traces (+0.362 U at 12 states; controls no longer finish). *Observed / Inferred.*
- It is sound only inside the declared budget; 3/12 noisy 8-state traces exceeded it. *Observed / Exact.*
- It was not shown that S7's noisy answers exclude anything (the reference confirmed 0 impossible codes). *Observed.*
- One noise model at a correctly declared rate; mis-declared rates and burst noise are untested. *Open.*
- Passive traces still leave 12-state machines ambiguous; active experiments are only pre-registered (v0.30.0). *Observed / Open.*

Deviations #136 (pre-run) and #137 (post-run). Verify: `python scripts/study032_storage.py restore && PYTHONPATH=. python scripts/verify_release_0290.py`.

## v0.28.0: exact search S6 (S5 with one incremental solver per trace and query ordering) and a trace-only identify probe (study BRUTE-0280-SIXTEEN-STATE-ID-031, LEAN process)

**6 of 9 gates pass (G10, GS_ref, GTI, G_PROC, G_RT, G_recount). GSC6 (headline) FAILS on clauses b and c; GID6 FAILS on b; GQB6 FAILS.** All 54 cases ran and were sealed (1028.1 s of 1800 s). *Observed*

### Timeline (EDT, 2026-10-30)

- Plan `ec7bd75` (15:04); build authorization (ledger `4a0eb8d`, 15:06, standing go t133s553); seedcheck `059fe1a` (ledger `1ff404d`, 15:16, before any seed); runner `2a3790b`; scoring and tooling `3688135`; release tooling `76d3476`; scratch diagnosis `f4bd80e`; pre-freeze sealed-smoke gates test `f48aac0`; #134 `fd80635`; source freeze `e74469a`.
- Run start (ledger `1ba5397`, 15:23:36); 4 pushed checkpoint snapshots (last `6131470`); run end `e27bde1` (15:41); seal `b3b8519`; recount `5877d4d`; reference `4f2c9fc`; tests `6afab8f`; gates `604d19c`; #135 `d086433`.

### Results (main block, eps 0; X and ID Wilson 95% CI, U seed-bootstrap 95% CI)

| arm | X scale8 | X scale12 | X scale16 | U scale12 | U scale16 | ID scale8 | ID scale12 | max query main/stress (s) | F main/stress |
|---|---|---|---|---|---|---|---|---|---|
| S6 | 12/12 [0.758, 1] | 6/12 [0.254, 0.746] | 0/18 [0, 0.176] | 0.033 [0.001, 0.090] | 0.222 [0.158, 0.288] | 4/12 [0.138, 0.609] | 0/12 [0, 0.242] | 9.98 / 10.86 | 0/0 |
| S6_noorder (ablation) | 12/12 | 6/12 | 0/18 | 0.036 [0.002, 0.094] | 0.226 [0.162, 0.292] | 4/12 | 0/12 | 9.98 / 9.96 | 0/0 |
| S5 | 12/12 | 6/12 | 0/18 | 0.030 [0.001, 0.080] | 0.218 [0.157, 0.281] | 4/12 | 1/12 [0.015, 0.354] | 7.39 / 8.35 | 0/0 |
| S1 | 11/12 [0.646, 0.985] | 2/12 [0.047, 0.448] | 0/18 | 0.151 [0.085, 0.221] | 0.336 [0.289, 0.381] | 4/12 | 0/12 | 23.15 / 27.70 | 0/0 |

- GSC6 a: 0 mismatches (21,345 vs S1, 23,232 vs S5; 21,966 truth-checked, 0 missing). b: paired U(S6) - U(S5) at 16 states +0.004 [-0.008, 0.016] (bar <= -0.06, CI below 0): FAIL. c: X(S6, scale16) 0/18 (bar 4/18): FAIL. d: F(S6) 0 on main and stress: PASS.
- GID6 a: WRONG 0 for every arm: PASS. b: ID(S6, scale12) 0/12 (bar 4/12): FAIL; S6 labels at 12 states AMB 11, NR 1. c: IDU + NR 1/12 (bar <= 2/12): PASS. The probe found unexercised truth transitions in 11/12 scale12 and 18/18 scale16 traces.
- GQB6: S6 max query 10.857 s on stress/scale16/9730003 (bound 10.5): FAIL. G10: controls 6/6 with U 0 and ID. GS_ref: 0 mismatches, mutations 20/20.
- Mechanism (descriptive, from counters): S6 build time per scale16 case 0.14 s vs S5 2.39 s, solve time 54.2 s vs 51.4 s, cap stops 45.8 vs 1.3. Throughput S6/S5 at 16 states median 0.99, mean 0.98 [0.95, 1.01]. Ordering had no effect (U(S6) - U(S6_noorder) -0.004 [-0.017, 0.007]).
- Stress (eps 0.05) U over both scales: S1 0.370 [0.147, 0.578], S5 0.568 [0.455, 0.666], S6 0.568 [0.451, 0.667], S6_noorder 0.566; at 16 states S1 X 2/3, S5/S6 0/3.

### What Brute can't do yet

- It does not finish 16-state worlds (0/18 for every arm). *Observed.*
- An incremental solver does not lower 16-state unknowns; rebuild cost was not the bottleneck. *Observed / Inferred.*
- It cannot single out 12- or 16-state machines from one passive trace: a second least machine exists in most cases. *Observed / Inferred.*
- The symmetry-free line (S5, S6) is worse than S1 on noisy traces. *Observed.*
- The per-query cap can overrun under load (10.86 s vs 10.5 s). *Observed.*

Deviations #134 (pre-run) and #135 (post-run). Verify: `python scripts/study031_storage.py restore && PYTHONPATH=. python scripts/verify_release_0280.py`.

## v0.27.0: exact search S5 without symmetry-breaking clauses, hard per-query cap (study BRUTE-0270-SYMMETRY-FREE-030, LEAN process)

**8 of 8 gates pass (GQB5, GSC5_headline, G10, GS_ref, GTI, G_PROC, G_RT, G_recount).** All 51 cases ran and were sealed (978.9 s of 1800 s). *Observed*

### Timeline (EDT, 2026-10-30)

- Plan `803a920` (13:56); build authorization (ledger `30ccd58`, 13:58, standing go t133s553); seedcheck `2f34fcd` (overlap concern cleared before any seed); scratch overrun diagnosis `6bea49a`; S5 `3377447`; runner `8ded63f`; scoring `d55b77b`; tooling `01a7910`; pre-freeze sealed-smoke gates test `0d264d7`; #132 `88b33d8`; source freeze `f68ac76`.
- Run start (ledger `a40eeef`, 14:28:58); 4 pushed checkpoint snapshots (last `189826c`); run end `734812d`; seal `6bbaa4f`; recount `bf780a1`; reference `ad0a2cb`; tests `fb10d83`; gates `04a4c5d`; #133 `29d8e59`.

### Results (main block, eps 0; X and ID Wilson 95% CI, U seed-bootstrap 95% CI)

| arm | X scale8 | X scale12 | X scale16 | U scale12 | U scale16 | ID scale8 | max query (s) | F main/stress |
|---|---|---|---|---|---|---|---|---|
| S5 | 12/12 [0.758, 1] | 5/12 [0.193, 0.680] | 0/12 [0, 0.242] | 0.047 [0.004, 0.093] | 0.240 [0.171, 0.308] | 6/12 [0.254, 0.746] | 8.52 | 0/0 |
| S5_softcap (ablation) | 12/12 [0.758, 1] | 5/12 [0.193, 0.680] | 0/12 [0, 0.242] | 0.048 [0.004, 0.098] | 0.242 [0.172, 0.311] | 6/12 [0.254, 0.746] | 8.38 | 0/- |
| S4 | 9/12 [0.468, 0.911] | 1/12 [0.015, 0.354] | 0/12 [0, 0.242] | 0.172 [0.113, 0.232] | 0.303 [0.247, 0.358] | 4/12 [0.138, 0.609] | 10.16 | 0/0 |
| S1 | 8/12 [0.391, 0.862] | 1/12 [0.015, 0.354] | 0/12 [0, 0.242] | 0.200 [0.144, 0.256] | 0.324 [0.271, 0.376] | 4/12 [0.138, 0.609] | 21.03 | 0/0 |

- GSC5 a: 0 mismatches (19,925 vs S1, 20,242 vs S4; 19,302 truth-checked). b: paired U(S5) - U(S1) at 12 states -0.153 [-0.198, -0.110] (bar <= -0.08, CI below 0): PASS. c: X(S5, scale12) 5/12 (bar 5/12): PASS. d: F(S5) 0 on main and stress: PASS.
- GQB5: S5 max query 8.52 s (bound 10.5): PASS. G10: controls 6/6 with U 0. GS_ref: 0 mismatches, mutations 20/20.
- ID at 12 and 16 states: 0/12 [0, 0.242] for every arm. Controls ID 6/6 for every arm.
- Descriptive: U(S5) - U(S5_softcap) at 12 states -0.001 [-0.009, 0.006], so the gain comes from removing symmetry clauses, not from the hard cap. Throughput S5/S1 at 12 states median 2.02, mean 2.01 [1.64, 2.39]. Stress (eps 0.05) U at 12 states: S5 0.585, S4 0.370, S1 0.371.

Deviations #132 (pre-run) and #133 (post-run). Verify: `python scripts/study030_storage.py restore && PYTHONPATH=. python scripts/verify_release_0270.py`.

## v0.26.0: exact search S4 (S1 plus throughput changes), API brute.certify/14 (study BRUTE-0260-QUERY-THROUGHPUT-029, LEAN process)

**7 of 10 gates pass (G10, GAPI14, GS_ref14, GTI, G_PROC, G_RT, G_recount). GSC4 (headline) FAILS on clauses b and c; GTP and GQB FAIL.** All 51 cases ran and were sealed (1345.9 s of 1800 s). *Observed*

### Design change before data (amendment A1, *Exact*)

S1 beat S2 and S3 at 8 and 12 states in v0.24.0 and v0.25.0, so S4 was built on S1, not S3. S4 = S1's encoding and first-visit symmetry plus one reused solver per step, witness reuse, batched queries and a 10 s per-query cap. The headline is against S1. A scratch diagnosis (`results/diag-029/S1_COST_029.json`) named symmetry-breaking clauses as what costs S2/S3 (and S1) the most.

### Timeline (EDT, 2026-10-30)

- Plan `c06bcfe`; build authorization (ledger `78336bd`, 12:59, standing go t133s553); scratch diagnosis `86856da`; amendment A1 `34ce968`; seedcheck `6bc7579`; S4 + certify/14 `e04d202`; runner `47d73a4`; scoring `89f85e6`; tooling `232e052`; pre-freeze sealed-smoke gates test `e93e3e6`; #130 `5a775b9`; source freeze `7337c11`.
- Run start (ledger `263204d`, 13:25:43); 5 pushed checkpoint snapshots; run end `d1752d6`; seal `0fb95ef`; recount `b82ee07`; API check `448f12c`; reference `2cf72ca`; tests `f4a906f`; gates `417036b`; #131 `86c91c8`.

### Results (main block, eps 0; X Wilson 95% CI, U seed-bootstrap 95% CI)

| arm | X scale8 | X scale12 | X scale16 | U scale8 | U scale12 | U scale16 | TP scale12 (answers/s) |
|---|---|---|---|---|---|---|---|
| S4 | 9/12 [0.468, 0.911] | 2/12 [0.047, 0.448] | 0/12 [0, 0.242] | 0.038 [0, 0.086] | 0.161 [0.095, 0.230] | 0.377 [0.312, 0.431] | 8.73 |
| S1 | 9/12 [0.468, 0.911] | 1/12 [0.015, 0.354] | 0/12 [0, 0.242] | 0.040 [0, 0.086] | 0.180 [0.112, 0.246] | 0.396 [0.339, 0.443] | 7.76 |
| S3 (frozen control) | 2/12 [0.047, 0.448] | 0/12 [0, 0.242] | 0/12 [0, 0.242] | 0.124 [0.052, 0.210] | 0.439 [0.387, 0.484] | 0.531 [0.503, 0.555] | 5.39 |
| S4_nowit (ablation) | 9/12 | 1/12 | 0/12 | 0.048 | 0.193 [0.125, 0.259] | 0.393 | 7.83 |
| S4_nosym (descriptive) | 12/12 [0.758, 1] | 6/12 [0.254, 0.746] | 0/12 [0, 0.242] | 0.000 | 0.079 [0.020, 0.149] | 0.327 [0.263, 0.382] | 13.18 |

- GSC4 b: paired U(S4) - U(S1) at 12 states -0.019, CI [-0.035, -0.006] (bar <= -0.08 with CI below 0): FAIL. c: X(S4, scale12) 2/12 (bar 5/12): FAIL. a: 0 mismatches (19,392 vs S1, 15,838 vs S3; 17,470 truth-checked). d: F(S4) 0 (main and stress): PASS.
- GTP: TP(S4)/TP(S1) at 12 states, median 1.056, mean 1.119 [1.054, 1.199] (bar median 2, CI lower 1.5): FAIL.
- GQB: S4 max query 15.33 s on scale16 9530003 (also 12.27 s and 11.07 s on two other scale16 cases; bound 10.5): FAIL.
- False certificates (exact recount): 0 for every arm, main and stress (S1 included).
- Recovery (ID, eps 0): scale8 3/12 [0.089, 0.532] for S4, S1, S4_nowit and S4_nosym, 1/12 for S3; 0/12 at 12 and 16 states for every arm; controls 6/6.
- Ablations: witness reuse lowers U at 12 states by 0.032 [0.020, 0.045] (S4 vs S4_nowit). Removing symmetry clauses lowers it by 0.082 [0.046, 0.118] (S4_nosym vs S4), *Observed*, descriptive.

Deviations #130 (pre-run) and #131 (post-run). Verify: `python scripts/study029_storage.py restore && PYTHONPATH=. python scripts/verify_release_0260.py`.

## v0.25.0: exact search S3 with a hard per-query budget, API brute.certify/13 (study BRUTE-0250-SOLVER-COST-028, LEAN process)

**8 of 9 gates pass (GQB, G10, GAPI13, GS_ref13, GTI, G_PROC, G_RT, G_recount). GSC3 (headline) FAILS on clauses b and c.** All 51 cases ran and were sealed (1053.8 s of 1800 s). *Observed*

### Timeline (EDT, 2026-10-30)

- Plan `914ce05` (11:47); build authorization `13e570c` (11:48, standing go t133s553; resume-after-reboot clause NOT approved); scratch S2 ablation `bd587ab`; seedcheck `d930593`; S3 portfolio selection `e5dc91f`; certify/13 + tests `946309d`; runner `246a591`; scoring `48e3cf3`; tooling `4c8add6`; #128 `32495af`, `d9ad217`; source freeze `fb84e6a`.
- Run start `c215ed5` (12:32:46); 4 pushed checkpoint snapshots; run end `b781e55`; seal `86ae1a2`; recount `679ab9c`; reference `80adbd6`; API check `9214a43`; tests `10ec8ac`; gates `1b13aed` (scored by the addendum make_gates_028b, #129); #129 `ea5b81a`.

### Results (main block, eps 0; X Wilson 95% CI, U seed-bootstrap 95% CI)

| arm | X scale8 | X scale12 | X scale16 | U scale8 | U scale12 | U scale16 | max query s (8/12/16) |
|---|---|---|---|---|---|---|---|
| S3 | 1/12 [0.015, 0.354] | 0/12 [0, 0.242] | 0/12 [0, 0.242] | 0.135 [0.058, 0.216] | 0.398 [0.333, 0.450] | 0.554 [0.524, 0.583] | 10.03 / 10.01 / 10.01 |
| S2 | 3/12 [0.089, 0.532] | 0/12 [0, 0.242] | 0/12 [0, 0.242] | 0.158 [0.086, 0.229] | 0.399 [0.315, 0.465] | 0.559 [0.525, 0.590] | 18.00 / 16.53 / 17.61 |
| S1 | 7/12 [0.320, 0.807] | 3/12 [0.089, 0.532] | 0/12 [0, 0.242] | 0.067 [0.019, 0.126] | 0.158 [0.097, 0.218] | 0.412 [0.354, 0.466] | 8.76 / 11.14 / 26.33 |
| S3_tight (informational) | 5/12 | 0/12 | 0/12 | 0.392 | 0.610 | 0.588 | 10.58 / 10.00 / 10.00 |

- GSC3 b: paired U(S3) - U(S2) at 12 states -0.0011, CI [-0.0199, 0.0193] (bar <= -0.15 with CI below 0): FAIL. c: X(S3, scale12) 0/12 (bar 3/12): FAIL.
- Clause a: S3 vs S2 15,380 compared, vs S1 16,043, 0 mismatches; 14,234 exact S3 supports contain the true next code. False certificates (exact recount): S3 0, S3_tight 0, S2 0 (main and stress); S1 3 (stress, eps 0.05; not gated).
- Controls: S3 0 UNKNOWN on 6/6 (G10 PASS); S2 2 solver UNKNOWNs.
- Recovery (ID, eps 0): scale8 S3 3/12 [0.089, 0.532], S2 1/12, S3_tight 2/12; 0/12 at 12 and 16 states for every exact arm; controls 6/6.
- Diagnosis (*Inferred*): S3's unknowns at 12-16 states are >98% not-run queries; S3 spends ~52 s of its 55 s arm budget in support solves at 12-16 states; capping each query removed the overruns (S3 observe max 2.2 s vs S2 46.4 s) but did not raise steps per second. The bottleneck is the number and cost of support queries per step, not single-query overruns.

Deviations #123, #124, #126, #128 (pre-run) and #129 (post-run: frozen make_gates_028 KeyError on wall-clock fields, fixed by addendum). Verify: `python scripts/study028_storage.py restore && PYTHONPATH=. python scripts/verify_release_0250b.py`.

## v0.24.0: full replay of the 8-16 state scale study, informational S2_tight (study BRUTE-0240-SCALE-REPLAY-027, LEAN process)

**6 of 8 gates pass (GAPI12, GS_ref12, GTI, G_PROC, G_RT, G_recount). GSC (headline) FAILS on clauses b, c and e; G10 FAILS.** All 93 cases ran and were sealed (1454.3 s of 1800 s). *Observed*

### Timeline (EDT, 2026-10-30)

- Plan `9f49ab1`; build authorization `e55a639` (10:46, standing go t133s553; resume-after-reboot clause NOT approved); seedcheck `4e00fad`; study code + #126 `5d924b7`; scoring `0da7e3f`; tooling `d99a930`; source freeze `5261f4e`.
- Run start `d119d25` (about 10:55:50); 5 pushed checkpoint snapshots; run end `0952c8f`; seal `32eb7d9`; recount `d817f28`; reference `13d6af1`; tests `fd472dd`; API check `71db876`; gates `f8167f1`; #127 + diagnosis `d66b54c`.

### Results (main block; Wilson 95% CIs)

| arm | scale8 X | scale12 X | scale16 X | U scale16 |
|---|---|---|---|---|
| S1 | 9/24 [0.212, 0.573] | 1/24 [0.007, 0.202] | 2/24 [0.023, 0.258] | 0.420 |
| S2 | 3/24 [0.043, 0.310] | 0/24 [0.000, 0.138] | 0/24 [0.000, 0.138] | 0.590 |
| S2_tight (eps 0 only, informational) | 9/12 [0.468, 0.911] | 0/12 [0.000, 0.242] | 0/12 [0.000, 0.242] | 0.589 |

- Clause a: 24,568 S2 queries compared with exact truth, 0 mismatches. False certificates (exact recount): S2 0, RGB6 0, S2_tight 0, S1 3 (eps 0.02).
- scale8 eps-0 recovery (ID): S2 1/12 [0.015, 0.354]; S2_tight 4/12 [0.138, 0.609]. ID at 12 and 16 states: 0/12 for both.
- Certificates: S1 13, S2 0, RGB6 0, S2_tight 5046 (3043 on scale8 eps 0).
- Diagnosis (informational, *Inferred*): at 12-16 states more than 99% of UNKNOWNs are not-run queries (arm deadline); solver UNKNOWNs are 0.25-0.36%. The proven lower bound n_lo never reaches n (mean 10.25 for S2 at both 12 and 16 states). Single support calls run 13-19 s on average at the per-case maximum (up to 48 s), well over the nominal 10 s query budget. Tightening n_max to n does not help at 12 states (2.1 vs 1.5 steps/s, 0 full cases). The bottleneck is solver cost per step, not the search cap. The cap matters only at 8 states.

Deviations #123, #124, #126 (pre-run) and #127 (post-run process events). Verify: `python scripts/study027_storage.py restore && PYTHONPATH=. python scripts/verify_release_0240.py`.

## v0.23.0: exact search S2 at 8-16 states, API brute.certify/12 (study BRUTE-0230-SCALE-026, LEAN process)

**2 of 8 gates pass (GTI, G_PROC). GSC (headline), G10, GAPI12, GS_ref12, G_RT and G_recount FAIL with INCOMPLETE_INPUT.** A host reboot at about 10:22 EDT stopped the detached run after 38 of 93 cases. The run was not relaunched (standing rule; deviation #125). *Observed*

### Timeline (EDT, 2026-10-30)

- Plan `7a6acdd` (00:34); build authorization `835161f` (09:06, card t133s553); seedcheck `234dc08`; #123 `ccdf0df`; S2 code `b41b82d`; scoring scripts `f205e20`; #124 `8d67e13`; source freeze `9837d1d`.
- Run start `bc30b93` (10:12:09); reboot about 10:22; interruption `e2ed8db`; partial seal `fe7b757`; gates `965879b`; #125 `d0c82f2`; release freeze `66d296e`.

### Descriptive results on the 38 sealed cases (they decide no gate)

- False certificates (exact recount, PASS): S2 0, RGB6 0, S1 2 (1 main, 1 stress).
- Clause a: 8771 S2 queries compared with exact truth, 0 mismatches (11293 excluded as inexact).
- X (exact-complete cases): S2 scale16 0/24 [0.000, 0.138]; S1 scale16 1/24 [0.007, 0.202]; S1 and S2 scale12 0/8 [0.000, 0.324]. scale8 had no cases.
- U (unknown fraction): S2 scale16 0.566, scale12 0.513; S1 0.454 and 0.390; RGB6 0.595 and 0.550.
- Certificates: S1 14, S2 0, RGB6 0. ID: no eps-0 scale8 or scale12 case; scale16 ID 0 of 12.
- Mean case wall 121.9 s.

Deviations #123, #124 (pre-run) and #125 (host interruption). Verify: `python scripts/study026_storage.py restore && PYTHONPATH=. python scripts/verify_release_0230.py`.

## v0.22.0: betting confidence sequence RGB6, API brute.certify/11 (study BRUTE-0220-BETTING-CS-025, LEAN process)

**11 of 12 gated criteria pass. GBC (headline) FAILS on clauses c and d.** *Observed*. The scoring rules were fixed before the data (*Exact*).

### Timeline (author's clock, EDT)

- **Pre-registration.** Plan `4f6c4dd` (2026-10-29 08:08). Build authorisation 23:39 (card t128s531). A1 `1f49928` made the stress gate strict. Lemma `55dd41f` and reference `8f31080` came before the RGB6 code `19987c8`.
- **Lean switch.** A2 `15cc245` (23:54; owner card t130s540, 23:45) cut the run to 60 main + 30 stress cases under a 30 min cap. It dropped the drills, the host-pause probe, the double clone, G12 and G_HB. Process scripts `35e4333`, #120 `e96b3aa`, source + scoring freeze `d1390e5` (23:58:38).
- **Run.** RUN_T0 23:58:50; exit 0 at 00:22:55 (Oct 30); 1365.8 s of 1800 s.
- **After.** run_end `e489213`, #121 `30428fd`, seal `72b52e8`, gates `0a98405`, tooling `be8d077`, release freeze `b9fd583`.

### Results (eps 0.02, 20 cases, CI95 bootstrap)

| arm | C_late | C_early28 |
|---|---|---|
| RGB6 (betting, new) | 0.315 [0.226, 0.413] | 0.0027 [0.0, 0.0071] |
| RGL5 (stitched) | 0.332 [0.239, 0.436] | 0.0027 [0.0, 0.0071] |
| RGL4 (lr) | 0.320 [0.228, 0.420] | 0.0027 [0.0, 0.0071] |
| RGNB4 (planned B) | 0.418 [0.289, 0.551] | 0.0018 [0.0, 0.0045] |
| RGN4_or (oracle) | 0.806 [0.709, 0.893] | 0.026 [0.008, 0.048] |

- dC_late RGB6 - RGL4: -0.0045 [-0.0108, 0.0] (bar mean >= 0.04 and CI lower > 0: FAIL). dC_late RGB6 - RGNB4: -0.102 [-0.195, -0.015] (bar CI lower > -0.06: FAIL). dC_late RGB6 - RGL5: -0.017 [-0.035, -0.003].
- Betting activation: 0 of 90 cases reached K >= 800 at any level, so RGB6 ran as its level-0 bound (delta 1/400) throughout (*Observed*; predicted in #120).
- False certificates (exact recount): RGB6 0 on 40 noisy main cases (CP95 0.0722, reported, not gated) and 0 on 30 stress cases (clause b PASS, strict). RGL4 1 on stress (ood4 9140009), RG4 31.
- Deviations #119, #120 (pre-run), #121 (an api_check t0 bug, fixed in a new r1 file before the gates), #122 (a release verifier key bug, r1). Verify: `PYTHONPATH=. python scripts/verify_release_0220_r1.py` (#122: the frozen verify_release_0220 reads the wrong COMMIT_ORDER key).

## v0.21.0: stitched likelihood-ratio bound RGL5, API brute.certify/10 (study BRUTE-0210-STITCHED-LR-024)

**12 of 14 gated criteria pass. GLS (headline) FAILS on clauses b, c and d. G_HB FAILS. Release gate GCC PASSES.** *Observed*; scoring rules were fixed before the data (*Exact*).

### Timeline (author's clock, EDT, 2026-10-29)

- **Pre-registration.** Plan `52deedb` (2026-10-28 22:52). Owner build authorisation 04:15 (card t126s506). Lemma `35bb890` and reference `eedd13a` before RGL5 code `6215a53`.
- **Preparation.** Process `b6d7edd`, commit order `e3bba8c`, rate math `d07cce8` (#117: reproset 60 -> 30, streams re-split). Source freeze `5850088` (05:43:02), scoring freeze `2a6aba7` (05:43:17), host-pause probe 600 s with 0 gaps.
- **Run.** RUN_T0 05:53:57; RUN_DONE 07:31:26 (5850 s of 7200 s); transfer 5220 s, gti 3843 s, repro 598 s, g11 624 s; no stop.
- **After.** Seal `612d651`, gates `47b83a4`, #118 `58b93fb`, clean clone `7871cab` (PASS), tooling `fca0f18`, release freeze `41ec9b2`.

### Results (eps 0.02, 120 cases, CI95 bootstrap)

| arm | C_late | C_early28 |
|---|---|---|
| RGL5 (stitched, new) | 0.419 [0.378, 0.462] | 0.0043 [0.0012, 0.0082] |
| RGL4 (frozen lr) | 0.411 [0.372, 0.453] | 0.0036 [0.0006, 0.0073] |
| RGNB4 (planned B) | 0.455 [0.401, 0.509] | 0.0036 [0.0009, 0.0071] |
| RGNA4 (anytime margin) | 0.197 [0.152, 0.246] | 0.0007 [0.0, 0.0019] |
| RGN4_or (oracle) | 0.836 [0.802, 0.868] | 0.053 [0.039, 0.069] |

- dC_late RGL5 - RGL4: +0.0076 [0.0032, 0.0128] (bar >= 0.04: FAIL). dC_late RGL5 - RGNB4: -0.036 [-0.066, -0.007] (bar CI lower > -0.06: FAIL).
- False certificates: RGL5 0 on 240 noisy main cases (CP95 0.0124); 3 in 1 of 30 stress cases (eps 0.05 > eps_bar; clause b FAIL). RGL4, RGNA4, RGN4_or 0 on stress.
- G_HB FAIL: max gap 35.829 s, 2 gaps over 10 s (clock_step, Inferred).
- Deviations #115-#118. Verify: `PYTHONPATH=. python scripts/verify_release_0210.py [--long]`.

## v0.20.0: likelihood-ratio anytime bound RGL4, API brute.certify/9 (study BRUTE-0200-LR-ANYTIME-023)

**12 of 13 gated criteria pass. GLR (headline) PASSES on all five clauses. G_HB FAILS. Release gate GCC FAILS (#112).** *Observed*; scoring rules were fixed before the data (*Exact*).

### Timeline (author's clock, EDT, 2026-10-28)

- **Pre-registration.** Plan `f88ad1e` (ledger preregistration_023, 18:34:14). Owner build authorisation 18:57 (card t126s492). Seed check. Lemma `e50967d` before the RGL4 code.
- **Preparation.**
  - Implementation `9e0ca70`, `cc53f4d`.
  - Rate math `56566e7`. The mean path before the cut was 7357.7 s, so the pre-declared contingency #110 cut stress to 30 cases (the first quarter of each family). The mean path after the cut was 5632.1 s.
  - Drills: kill 0.224 s; resume clauses i-iv passed; API check passed.
- **Freezes.** Source `6bbe5ba`. Scoring `2d73745` at 20:34:31, 649 s before run_start.
- **Held-out run.**
  - run_start `fb64c86`. RUN_T0 20:45:20 EDT; 2 h cap to 22:45:20.
  - A false-start orchestrator ran at 20:45:20 and was relaunched at 20:46:01 with the same RUN_T0 (#111). The 41 s counted against the cap.
  - RUN_DONE 22:12:21 (5221 s). No stream stopped.
- **After the run.**
  - Seal `7ac0edc`, gates `91f4af6`, #111 `d3b7020`.
  - Clean clone FAIL `bfc6c49` (#112 `40ad4c0`); supplementary git-clone rescoring PASS `3add4b9`.
  - Release tooling `7435c9f`, committed after run_end (GTI clause vi). Release freeze `3a30555`.

### Results

- **GLR PASS (a-e).**
  - RGL4: 0 false certificates on 240 noisy main cases; CP95 0.0124.
  - C_late at eps 0.02: 0.417 [0.376, 0.459].
  - dC_late vs RGNA4: +0.192 [0.162, 0.223].
  - prefix28 identical on all 120 cases.
- **Pass:** G_recount, GLR_lemma, GAS_frozen_control (RGNA4 C_late 0.225 [0.185, 0.268] vs study-021 [0.215, 0.317]), GS_a10, GS_ref10 (360 gated, 0 mismatching, mutation 20/20), GAPI10, G10, G12 (60/60), G13, GTI, G_RT.
- **FAIL: G_HB.** 2511 beats, max gap 47.558 s, 6 gaps over 10 s (clock_step 4, unattributed 2).
- **Reported only:**
  - RGNB4 C_late at eps 0.02 is 0.530 (dC_late of RGL4 vs RGNB4: -0.113).
  - C_early28 at eps 0.02: RGL4 0.0024, RGNA4 0.0003.
  - Stress: RGL4 0 false of 30, C_late 0.487.

### Deviations

#110 (stress cut), #111 (false start), #112 (GCC FAIL), #113 (the frozen release verifier rejected dual-role commit `9e0ca70`; `verify_release_0200_r1` fixes only that check).

## v0.19.0: anytime sequential margin RGNA4, streaming API brute.certify/8 (study BRUTE-0190-ANYTIME-021)

**12 of 14 gated criteria pass. GAH_anytime (headline) FAILS on clause (c); its soundness and late-coverage clauses pass. GTI FAILS (#107).** *Observed*; scoring rules fixed before the data (*Exact*).

### Timeline (author's clock, EDT, 2026-10-28)

- **Pre-registration.** Plan `a51275e` (ledger preregistration_021, 14:17:42); seed check; reference before code.
- **Preparation.** Implementation `94d49b7`, `30595c3`, `df915e5`; drills (kill 0.224 s, resume i-iv, API 4/4); release tooling `0977173`; rate math `162d714` (critical path did not fit; mean path 4864.9 s).
- **Freezes.** Source `07beaa0`; scoring `0894fcc` (15:51:56, 638 s before run_start).
- **Held-out run.** run_start `ea114fe`, 16:02:34 EDT, 2 h cap; RUN_DONE 17:22:35 (4801 s); no stream stopped.
- **After the run.** run_end `9c2a7fa`; seal `ffda8a1`; GATES_021 `ff96381`; #107 `c2b8633`; clean clone `e0441ab` PASS; release freeze `08e18fc`.

### Code

- `brute/anytimemargin.py` (RGNA_n, horizon-free boundary δ·6/(π²b²)), `brute/api/certify8.py` (brute.certify/8, streaming); `experiments/v0190_reference.py` (second implementation).
- Release: `scripts/verify_release_0190.py` (short, `--long`), `tests/test_release_0190.py`, `scripts/make_release_freeze_0190.py`.

### Results (*Observed*)

- **GAH_anytime FAIL (c).** RGNA4 0 false on 240/240 noisy main cases, CP95 0.0124; C_late eps 0.02 = 0.265 [0.215, 0.317]; dC_early28 vs RGNB4 -0.0040 [-0.0068, -0.0018]; dC_late -0.228.
- **Controls.** GAH_prefix_control and GAH_frozen_control PASS (RGNB4 C_early28 0.0060, CI overlaps study-020); RGN4_or C_late 0.832; RGNB4 0.493.
- **Stress (eps 0.05, no guarantee).** RGNA4 0 false on 120; RG4 false on 48.
- **Process.** GS_ref9 PASS (480 audited, mutation 20/20), G12 60/60, G_RT PASS, G_HB PASS (3.3 s), GTI FAIL (6 release tests, #107); GCC PASS.


## v0.18.0: long-horizon test of the sequential margin, per-bit partial certificates (study BRUTE-0180-HORIZON-020)

**10 of 12 gated criteria pass. GLH_horizon (headline) PASSES; GLH_early_control and G_HB FAIL.** *Observed*; scoring rules fixed before the data (*Exact*).

### Timeline (author's clock, EDT, 2026-10-27/28)

- **Pre-registration.** Plan `8048c95` (ledger preregistration_020, 2026-10-27); seed check `5e6407a`; deviations #103 `b5ec732`; numpy reference `5ac2ec9`.
- **Preparation.** Implementation `2549157`; rate math, smoke dry run and kill drill `44ca110`.
- **Freezes.** Source `152c379`; scoring `adc4d2a` (11:41:13 EDT, 625 s before run_start).
- **Held-out run.** run_start `668a588`, 11:51:38 EDT, 2 h cap. A box restart killed every process at ~12:19:42 (1683 s in); deviation #105 `6d8f1fd`; resumed from checkpoints at 12:37:58 under the frozen resume rule (cap not extended, stream budgets charged). RUN_DONE 13:43:58 EDT after 6740 s; no stream stopped.
- **After the run.** Seal `8430b47`; GATES_020 `35a03bb`; clean clone `7053791` PASS; #106 `fc648cf`; release tooling `b2c68a0`; release freeze `d20cf05`; RELEASE.json `1abaabe`.

### Code

- `experiments/brute_study_020.py`, `experiments/brute_common_020.py`: 88-step runner for RG4 / RGN4 / RGNB4 / RGN4_or / SP8; `brute/perbit.py`: per-bit partial certificates.
- `experiments/v0180_reference.py`: numpy second implementation.
- Release: `scripts/verify_release_0180.py` (short, `--long`), `tests/test_release_0180.py`, `scripts/make_release_freeze_0180.py`. API unchanged: `brute.certify/7`.

### Results (*Observed*)

- **GLH_horizon PASS.** RGNB4 0 false on 240/240 noisy main cases, 0 crossings, CP95 upper 0.0124; C_late eps 0.02 = 0.482 [0.430, 0.537]; dC_late(RGNB4 − RGN4) +0.053 [0.043, 0.063]. GS_a8: 0 false at eps 0.
- **GLH_early_control FAIL.** C_early28 0.00253 [0.00119, 0.00417] vs study-019 CI [0.0405, 0.0654]; mechanism: the boundary spends delta·b/B (#106).
- **Controls.** RGN4_or C_late 0.849; RG4 false on 15 / 28 of 120 cases at eps 0.01 / 0.02; SP8 C_late 0.055 at eps 0.02.
- **Per-bit (reported).** Late per-bit coverage 0.596 [0.545, 0.646] at eps 0.02; 0 false bits on main; stress 10 false bits on 8 cases.
- **Stress (eps 0.05, no guarantee).** RGNB4 false on 5/120, RGN4 4/120, RGN4_or 0.
- **Process.** GS_ref8 PASS (480 audited, mutation 20/20), G12 120/120, GTI PASS (733 tests), G_RT PASS, G_HB FAIL (1083.5 s); GCC PASS.


## v0.17.0: sequential flip margin RGNB4, 3-action alphabet block, brute.certify/7 (study BRUTE-0170-SEQUENTIAL-MARGIN-019)

**12 of 13 gated criteria pass. GNB (headline) FAILS on its coverage clauses (c) and (d); its soundness clauses pass.** *Observed*; scoring rules fixed before the data (*Exact*).

### Timeline (author's clock, EDT, 2026-10-27)

- **Pre-registration.** Plan `c11a852` (ledger preregistration_019).
- **Preparation.** Deviation #102 (per-step bound after a contradiction) `5ca467c`; rate math, smoke dry runs and kill drill `2f552bc`.
- **Freezes.** Source `5f6bde1`; scoring `f597096` (receipts `8f6d2fe`, ≥ 600 s before run_start).
- **Held-out run.** run_start `13aa9b8`, 12:19:16 EDT, under a 2 h cap; RUN_DONE 12:40:27 EDT after 1274 s. No stream stopped; watchdog exited without killing; heartbeat max gap 2.006 s.
- **After the run.** Seal `76fbe07`; GATES_019 `5a3cca8`; clean clone `b4e6d46` PASS; artifact-source correction receipts `09a0eee`; release tooling `20eec72`; release freeze `85b9969`; RELEASE.json `576e564` (ledger `2f3aebb`).

### Code

- `experiments/brute_study_019.py`: RGNB4 (sequential boundary m(b_t), exact alpha spending, eps_bar 0.02, delta 0.01), RGNB4_0, and the alphabet3 block (RG4_3, RGN4_3, RGNB4_3).
- `brute/api/certify7.py`: `brute.certify/7`, 2 or 3 actions, probabilistic soundness conditional on running flips ≤ m(b) and n* ≤ family_bound.
- `experiments/v0170_reference.py`: numpy second implementation.
- Release: `scripts/verify_release_0170.py` (short, `--long`), `tests/test_release_0170.py`, `scripts/make_release_freeze_0170.py`.

### Results (*Observed*)

- **Soundness holds.** RGNB4 0 false certificates on 240/240 noisy main cases, 0 crossings, CP95 upper 0.0124 (GNB a, b PASS).
- **Coverage is not recovered (GNB c, d FAIL).** dC(RGNB4 − RGN4) at eps 0.02 = +0.0017 [−0.0005, +0.0041]; C(RGNB4) = 0.052 [0.041, 0.065] < 0.10. C(RGNB4) is 0.055 even at eps 0 (RG4 0.453).
- **Oracle and baseline.** RGN4_or C 0.339 at eps 0.02 with 0 false; RG4 false on 26/120 eps 0.02 cases.
- **GA3 PASS.** RG4_3 0 false at eps 0; RGNB4_3 0 case-false at eps 0.02 (CP95 0.0605); RG4_3 false on 20/48 at eps 0.02; C(RGNB4_3) 0.012.
- **Stress (eps 0.05, no guarantee).** RGNB4 false on 8/120, RGN4 9/120, RGN4_or 0.
- **Process.** GS_ref7 PASS (mutation 20/20), G12 152/152 byte-identical, GTI PASS (691 tests), G_RT, G_HB PASS; GLV `--long` 15 cases / 0 mismatching / 77.6 s; GCC PASS.

## v0.16.0: noisy observations, tolerant bounded region RGN4(m), brute.certify/6 (study BRUTE-0160-NOISY-OBSERVATION-018)

**10 of 12 gated criteria pass. GNS (headline) FAILS on its coverage clause (c) only; GN0 FAILS as predicted before the run.** *Observed*; scoring rules fixed before the data (*Exact*).

### Timeline (author's clock, EDT, 2026-10-27)

- **Pre-registration.** Plan `9beb459` (ledger `34901f8`); seed check `503d61a`; deviations #97 `a74cbaf`; numpy reference `f6ef422`.
- **Preparation.** Implementation `f646cca`; process scripts (parallel clean-tag GTI, as_completed) `18885f4`; deviations #98–#99 `6f22051`; rate math, kill drill and smokes `7ec7f08`.
- **Freezes.** Source `c350ba5` (ledger `68d0601`); scoring `5b77da4` / `f9df9bc` (10:27:07–10:27:22 EDT, 631 s before run_start).
- **Held-out run.** run_start `138cfee`, 10:37:53 EDT, under a 2 h cap; RUN_DONE 10:52:34 EDT after 882 s. No stream stopped; watchdog exited without killing; heartbeat max gap 2.0 s.
- **After the run.** Run end `012294c`; seal `e86f1df` (ledger `365055e`); GATES_018 `f0f0010` (ledger `ad6b437`); clean clone `560e177` PASS; release tooling `8933d3a`; RELEASE.json fix `c1fc976` (ledger `0b39f05`); release freeze `b83b1f2` (ledger `fa97faa`); release record ledger `e5713fa`. Deviations: #97 `BRUTE_DEVIATIONS_018.md`, #98–#99 `_ADDENDUM_1`, post-run disclosures #100 `_ADDENDUM_2`.

### Code

- `brute/noisyregion.py`: `NoisyRegionSpace(4, m)`, a bounded region that keeps every hypothesis explaining the observations with at most m flipped bits; `m_rule(B, eps_bar, delta)`; the RGN decision rule (region singleton after burn-in 8, no SP8 passthrough).
- `experiments/brute_study_018.py`: noise model (iid flips of observed bits, eps 0 / 0.01 / 0.02, stress 0.05) and arms SP8, RG4, RGN4, RGN4_0, RGN4_or.
- `brute/api/certify6.py`: `brute.certify/6` with a probabilistic soundness record (delta 0.01, conditional on flips <= m and n* <= 4).
- `experiments/v0160_reference.py`: numpy exhaustive second implementation of the tolerant region.
- Process: `scripts/run_tests_0160.py` (clean-tag release tests in parallel), `scripts/rate_math_018.py`, watchdog, heartbeat sentinel.
- Release: `scripts/verify_release_0160.py` (short, `--long`), `tests/test_release_0160.py`, `scripts/make_release_freeze_0160.py`.

### Results (*Observed*)

- **Soundness under noise holds.** RGN4 0 false certificates on all 240 noisy main cases; realized flips <= m on 240/240 (m = 4 on 460 of 480 cases, 5 on 20); one-sided CP95 upper bound on the case-false rate 0.0124 (GNS a, b PASS).
- **Coverage does not (GNS c FAIL).** C(RGN4) at eps 0.02 = 0.066 [0.051, 0.081]; the pre-registered bar was mean >= 0.10 with CI lower > 0.05. C(RGN4) is 0.058 even at eps 0, so the loss comes from the margin m, not from the flips themselves.
- **The noise-blind baseline is unsound.** RG4 false on 16/120 cases at eps 0.01 and 24/120 at eps 0.02 (0.20 [0.13, 0.27]); RGN4_0 (m = 0) the same. Coverage RG4 0.235 at eps 0.02.
- **The oracle margin shows the room left.** RGN4_or (m = realized flips) 0 false, C 0.316 at eps 0.02 (reported; a host does not know its flips).
- **GN0 FAIL (predicted in #97 item 3).** RGN4_0 differs from RG4 on one eps-0 case (main/cycle3/8410024) in 2 burn-in slots where RG4 passes SP8 certificates through; 0 differing slots after burn-in.
- **Stress eps 0.05 (outside eps_bar, reported).** RGN4 false on 9/120 cases, RG4 46/120, RGN4_or 0.
- **Audit and process.** GS_ref6 PASS (480/480 audited, 0 mismatches; mutation 20/20); G12 120/120; GTI PASS (10 clean-tag runs in parallel; the run_start ledger line was appended at 10:37:53 and committed at 10:38:15 EDT, and the GTI stream started inside that 22 s window, so TEST_SUITE records a dirty tree, *Observed*, no verdict depends on it); G_RT PASS (kill drill 0.226 s); G_HB PASS. No CI workflows (Brute has no `.github` directory).

## v0.15.0: bounded-region lookahead RGLX / RGL, deferred-split replication GDS2, attested license DLFa, RSXL5 on ood5, heartbeat sentinel, brute.certify/5 (study BRUTE-0150-BOUNDED-LOOKAHEAD-017)

**9 of 13 gated criteria pass; GRL (headline) PASS; GS_ref5, GTI, G_RT and G_HB FAIL.** *Observed*; scoring rules fixed before the data (*Exact*).

### Timeline (author's clock, EDT, 2026-10-27)

- **Pre-registration.** Plan `908fe9b` (ledger `c0a793d`, 05:38:54 EDT); deviations #86–#91 `f720f1b`; seed check `5506eff`; numpy reference `5c88600`.
- **Preparation.** Implementation `356ecfd`; rate math and deviations #92–#95 `460271b`; smokes, mutation smoke 20/20, kill drill `5361010`.
- **Freezes.** Source `0b3ad52` (ledger `35e30f5`); deviation #96 `b25f53d`; scoring `b7ec1ef` (ledger `cd545a7`, `b80caac`, 07:04:51 EDT).
- **Held-out run.** run_start `cf71514`, 07:15:33 EDT, under a 2 h cap; RUN_DONE 3,463 s after RUN_T0. g11 stopped at its 2400 s stream budget (08:07:41 EDT); watchdog did not fire; two heartbeat gaps (425.7 s, 316.5 s).
- **After the run.** Seal `3e4f0e8` (ledger `2b8792e`); GATES_017 `911f06c`; release tooling `9174956`; release freeze `9f0d6dc`; RELEASE.json receipt `7545ec8`; addendum 3 `c1e5592`; clean clone `fa658bf` PASS.

### Code

- `brute/boundedlookahead.py`: bounded-region lookahead chooser RGLX (lookahead on the RG4 region until the first certificate, then RSX) and RGL (lookahead throughout).
- `experiments/brute_study_017.py`: study runner, including the RSXL5 (ood5) and DLFa (attested license) arms.
- `brute/api/certify5.py`: `brute.certify/5` (`suggest5(rule='rglx')`).
- `experiments/v0150_reference.py`: numpy exhaustive second implementation with lookahead scores.
- `scripts/hbsentinel_017.py`, `scripts/hb_attribution_017.py`: heartbeat sentinel and gap attribution (#90, diagnostic).
- Release: `scripts/verify_release_0150.py` (short, `--long`), `tests/test_release_0150.py`, `scripts/make_release_freeze_0150.py`.

### Results (*Observed*)

- **Headline GRL PASS.** RGLX4 0 false in 13,755; TV +2.84 [2.21, 3.46] (S 17.09 vs 14.25); 208 sooner, 51 later, 101 equal; unaliased2 3.72, switch3 3.42, cycle3 2.78, ood4 2.13.
- **GDS2 PASS.** RSXL4 0 false in 13,906; dC +0.037 [0.030, 0.043].
- **Coverage.** SP8 0.130, RGL4 0.399, RG4 0.402, RGLX4 0.434, RSXL4 0.439, DLFp 0.451.
- **Soundness.** Every gated arm 0 false. Outside the guarantee: DLFn 5, RSXLn 5, EB 141. DLFa = RG4 everywhere.
- **ood5.** RG4 148 false in 446; RG5 0 in 174; RSXL5 0 in 50.
- **Stress.** 25,920 pairs: AT6 1,510 false; DLF 120 and RSXL 120, all outside the exact license bound.
- **Audit.** GS_ref5 FAIL: 308/432 audited, 0 mismatches, 124 not reached (STUDY_BUDGET); cost 46.4 vs 27.0 projected worker-s per case.
- **GTI FAIL** exactly as declared in #96 (586 = 586 tests). **G_RT FAIL** (g11 stopped; kill drill 0.224 s). **G_HB FAIL** (gaps 425.7 s and 316.5 s, ending at the operator's next action; cause *Inferred*).
- **Release.** G12 144/144; GLV `--long` 18 cases, 0 mismatches, 466 s; GCC PASS. No CI workflows (Brute has no `.github` directory).

## v0.14.0: deferred region split RSXL, DLF re-gate with doubled ood4, DLF2, ood5 bound-violation report, 8140016 diagnosis, brute.certify/4 (study BRUTE-0140-DEFERRED-SPLIT-016)

**11 of 14 gated criteria pass; GDS (headline) PASS; GS_a4, GS_c4 and G_HB FAIL.** *Observed*; scoring rules fixed before the data (*Exact*).

### Timeline (author's clock, EDT, 2026-10-27)

- **Pre-registration.** Plan `498d768` (ledger `4b87380`); seed check `35b9840`; seen-data diagnosis of the v0.13.0 false certificate `afb89a9`; numpy reference `ac717c4`.
- **Preparation.** Implementation `97f9800`; rate math, deviations #75–#79, dry run and kill drill `62bea00`; smokes `75d57d4`.
- **Freezes.** Source `c7ed80e` (ledger `ecad32d`); scoring `0e9113c` (ledger `cc8525d`, `32ebaba`).
- **Held-out run.** run_start `65d2fb5`, 04:34:02 EDT, under a 2 h cap; RUN_DONE 05:12:48 EDT after 2,326 s. No stream stopped; watchdog did not fire; one 285 s heartbeat gap.
- **After the run.** Run end `83c2116`; seal `6a82c35`; GATES_016 `cc10159`; release tooling `cce6642`; release freeze `ece2474`; addendum `35bca5a` (#80–#83); clean clone `0d29822` PASS.

### Code

- `brute/deferredsplit.py`: deferred region-split chooser RSXL (SP8 until the first RG4 certificate, then RSX) and the margin-2 license DLF2.
- `brute/api/certify4.py`: `brute.certify/4` (`suggest_action(deferred=True)`).
- `experiments/v0140_reference.py`: numpy exhaustive second implementation.
- Release: `scripts/verify_release_0140.py` (short, `--long`), `tests/test_release_0140.py`, `scripts/make_release_freeze_0140.py`.

### Results (*Observed*)

- **Headline GDS PASS.** RSXL4 0 false in 14,491; S(RSXL4) = S(RG4) on every case (13.69 [12.61, 14.74]); dC +0.049 [0.041, 0.057].
- **Coverage.** SP8 0.146, RG5 0.235, RG4 0.408, RSXL4 0.457, DLFp 0.464, RSX4 0.471, EB 0.479, RSXLp 0.518.
- **Speed over SP8.** RG4 13.69; RSXLp, DLFp 15.13 (TV +1.44 [1.12, 1.76]); RSX4 9.01 (TV −4.68); EB 16.97; RG5 6.81.
- **Soundness.** DLFn 2 and RSXLn 2 false, all on ood4 seed 8240010, mask 0.6 (GS_a4, GS_c4 FAIL); every other gated arm 0. EB 111 false.
- **ood5.** RG4 155 false in 457; RG5 0 in 111.
- **Stress.** 25,920 pairs: AT6 2,736 false on 984 stress pairs; DLF 48 and RSXL 48 false, all outside the exact license bound.
- **Heartbeat.** G_HB FAIL: one 285.065 s gap; whole-box pause (*Inferred*).

## v0.13.0: region-split experiments RSX, evidence-derived bound EB, ood5 block, own-trajectory recount, brute.certify/3 (study BRUTE-0130-REGION-SPLIT-015)

**11 of 15 gated criteria pass; GRS (headline) FAIL; GS_a3, GS_c3 and GEB FAIL.** *Observed*; scoring rules fixed before the data (*Exact*).

### Timeline (author's clock, EDT, 2026-10-27)

- **Pre-registration.** Plan `9642783` (ledger `61584ee`, 01:05:51 EDT; HANDOFF `c6bfcb3`); seed check `f6fbb92`; numpy exhaustive reference `f95a176`/`305b739`.
- **Preparation.** Implementation `6815770`; process scripts `3cd15e4`; smoke, kill drill and mutation smoke `0f95f92`; rate math `744969b` (deviation #72, g11 on 4 workers via `run_study_015_R1.py`).
- **Freezes.** make_freeze `069cbca`; source `f67bcaf` (ledger `1c144d1`); scoring `58e42fd` (ledger `31edbe0`, 02:09:54 EDT).
- **Held-out run.** run_start `6406522`, 02:20:13 EDT, under a 2 h cap; RUN_DONE 02:50:57 EDT after 1,844 s. No stream stopped; watchdog did not fire; max heartbeat gap 2.03 s.
- **After the run.** Run end `eb2f7d2`; seal `f1668a7`; GATES_015 `c21b405`; release tooling `e25943f` (deviation #74 addendum); release freeze `9e785b1`; clean clone `8e6923c` PASS.

### Code

- `brute/regionsplit.py`: region-split action chooser RSX (action that splits the bounded region most evenly) and the evidence-derived bound EB / EB2.
- `brute/api/certify3.py`: `brute.certify/3` (adds `suggest_action` with reasons).
- `experiments/v0130_reference.py`: numpy exhaustive second implementation (bounded supports n = 1..5 on SP8 and RSX trajectories).
- Release: `scripts/verify_release_0130.py` (short, `--long`), `tests/test_release_0130.py`, `scripts/make_release_freeze_0130.py`.

### Results (*Observed*)

- **Headline GRS FAIL.** RSX4 0 false in 11,005 certificates, but TV_RSX = S(RSX4) − S(RG4) −5.27 [−5.99, −4.59]; negative in every family (cycle3 −4.24, switch3 −3.96, ood4 −4.15, unaliased2 −8.75). RSXp TV −1.55.
- **Speed over SP8.** RG4 10.51 [9.64, 11.33]; RSX4 5.24 [4.28, 6.17]; RSXp 8.97 [8.00, 9.88]; DLFp 12.39 [11.52, 13.22].
- **Coverage.** Certificate fraction SP8 0.166, RG4 0.370, RSX4 0.434, RSXp 0.507.
- **Soundness.** RG4, RSX4, RSXp, DLFp 0 false. DLFn and RSXn 1 false each, both on ood4 seed 8140016, mask 0.35 (GS_a3, GS_c3 FAIL). EB 91 false in 11,355 (GEB FAIL); EB2 8 false. RG2 400, RG3 173 false; RG5 0.
- **ood5.** RG4 121 false in 381 certificates; RG5 0 false in 132.
- **Stress.** 576 stress pairs: AT6 2,664 false, DLF on the RSX trajectory 0.
- **Exactness.** GS_ref3 360/360, mutation 20/20; G_recount PASS (every arm on its own trajectory); G12 120/120; GLV `--long` 15 cases, 0 mismatches (172 s); GTI 488 tests, failures only K_060–K_0110.
- **Disclosure #74.** TEST_SUITE_015 records `tracked_tree_dirty=true`; cause Open; frozen files byte-identical; GTI scored as recorded.

## v0.12.0: bounded transfer (RGn, DLF, DX), aliasing stress block, brute.certify/2, heartbeat fix (study BRUTE-0120-BOUNDED-TRANSFER-014)

**15 of 16 gated criteria pass; GST2 (headline) PASS; GS_x FAIL.** *Observed*; scoring rules fixed before the data (*Exact*).

### Timeline (author's clock, EDT, 2026-10-26/27)

- **Before the plan.** License diagnostics on sealed study-013 (seen data): `BRUTE_DIAG_LICENSE_014.md`, `_014B.md` (bank unanimity Rejected, 537 false).
- **Pre-registration and preparation.** Plan `ef865e7`; seed check `f87f5bc`; numpy exhaustive reference `89ff5b8`; implementation `7323b44`/`0b81c76`/`76a9e8d`/`516fe34`; rate math (deviation #61, g11 on 4 workers).
- **Freezes.** Source `b4f0fc8`. Scoring `4375a5f` (ledgered 00:02:31 EDT).
- **Held-out run.** run_start 00:14:04 EDT under a 2 h cap; RUN_DONE after 1,655 s. Watchdog did not fire; max heartbeat gap 2.0 s.
- **After the run.** Seal `12455f0`; GATES_014 `27bfe45`; release tooling `ee1a1c8`; deviations #62–#63 addendum; release freeze `BRUTE_RELEASE_FREEZE_0120.json`; clean clone `CLEAN_CLONE_014.json` PASS.

### Code

- `brute/boundedtransfer.py`: bounded-region certification RGn and the disagreement-based license DLF (library unanimous, answer in SP8 support, bounded region at min(n_L + 1, 4) states a singleton).
- `brute/api/certify2.py`: `brute.certify/2` (`Certifier2`, `certify2`) with reasons on UNKNOWN.
- `experiments/v0120_reference.py`: numpy exhaustive second implementation; `scripts/watchdog_014.py` heartbeat fix.
- Release: `scripts/verify_release_0120.py` (short, `--long`), `tests/test_release_0120.py`, `scripts/clean_clone_014.py`, `scripts/make_release_freeze_0120.py`, `brute/release_version_0120.py`.

### Results (*Observed*)

- **Soundness.** 0 false certificates in every gated arm (RG4 9,809; DLFp 11,434; DLFn 9,810; DXp 11,761; DXn 10,100).
- **Aliasing stress.** 600 stress pairs: AT6 2,016 false, DLF 0. All 20,736 pairs: 336 DLF licenses, 0 false. DLF0 (margin 0): 3,576 false.
- **Speed.** RG4 S 10.86 [9.83, 11.84]; DLFp S 12.50 [11.43, 13.52]; TV(DLFp) 1.64 [1.27, 2.01] (unaliased2 only); TV(DLFn) 0.05 [0.00, 0.15]; DX − DLF −0.007 [−0.59, 0.57] (GS_x FAIL).
- **Exactness.** GS_ref 288/288, mutation 20/20; G12 96/96; GLV `--long` 12 cases, 0 mismatches.
- **Disclosure #62.** The frozen scorer's non-gated recount of LX uses the SP8 trajectory (1,723 / 1,503 "false"); on LX's own trajectory it is 0 / 4,490 and 0 / 4,494. No gate changes.

## v0.11.0: sound-transfer arms DR / AT / LX with wrong-family controls; embeddable API brute.certify/1 (study BRUTE-0110-SOUND-TRANSFER-013)

**22 of 26 gated criteria pass.** Four fail, all in the transfer track: GST (headline), GS_a and GS_c (ATn, 3 false certificates in 1 of 288 cases) and GS_e (LX speedup, S −1.32 [−2.19, −0.50]). *Observed*. The scoring rules were fixed before the data (*Exact*).

### Results (*Observed*)

- **Transfer.** GS_d PASS: ATp S 6.64 [5.73, 7.54], 0 false in 10,202. GS_b PASS: DR ⊆ SP8 exactly, S 0. GS_ref PASS (288/288). The ATn false certificates come from one cycle3-library hypothesis aliased with a switch3 target (seed 6120009) for 7 confirmations.
- **API.** GAPI PASS: `brute/api/certify.py` (`brute.certify/1`), host-agnostic, observations in → CERTIFIED answer or UNKNOWN out; `verify_release_0110` checks the interface and an UNKNOWN on one observation.
- **Other.** First pass of G6b on the SP8 arm (−0.0104 [−0.0165, −0.0047]). G3′ strict PASS. GTI PASS (K_080/K_090 declared). G78 soundness with power (0 of 360). G1, G2, G3L, GH, G4, G5, G7, G9, G10, G11, G12, G13 and G_RT (R_G_RT_strict true) all pass.
- **Runtime.** 2,148 s of 7,200 s; every stream complete. Kill drill 0.225 s. GLV `--long` 33 cases, 66 traces, 0 mismatches, 53.7 s of 900 s. GCC PASS.

### Timeline (author's clock, EDT)

- Seen-data applicability diagnostic `e0aa431` → plan `bb1d96e` → seeds `780be3b` → reference `eed2ada` → implementation `084076a`/`3871e78`/`7dc04c8` → rate math (no change) → source freeze `e6fc10c` (ledger `70c179f`) → scoring scripts `22bdb9f` (scoring_freeze_013 10:57:34–10:59:50 EDT; erratum `aab5046`) → run_start 11:10:34 (`9d588d0`) → RUN_DONE 11:46:22 → seal `5f45ed4` → run_end/seal ledger `af4b384` → GATES_013 `ad1ba6a` → release tooling `a56a177` → deviations/release ledger `d5bf4ce` → release freeze `8890884`/`ed53fdf` → clean clone `d9ca7bc`.
- Deviations #53–#57 (retroactive smoke receipt, storage file in a later commit, ledger commit-field typo with erratum, push outage from ~10:56 EDT, watchdog/orchestrator start order): `docs/research/BRUTE_DEVIATIONS_013.md`. Erratum: the release-freeze commit message and its ledger note say "10 files"; the freeze holds 9 (`study013_storage.py` is already in the source freeze). *Exact.*
- Default learner unchanged (Y1k, LU-R). DR, AT and LX are research arms.

## v0.10.0: first transfer test (TRp/TRn), J10 exact jump-window support, 7–8 state worlds, ROADMAP_TO_GI (study BRUTE-0100-SUPPORT-TRANSFER-012)

**18 of 24 gated criteria pass.** Six fail: GT_a and GT_c (transfer soundness and negative control), G6b, GA1_012 (headline), G3′ strict, and GTI as frozen. *Observed*; scoring rules were fixed before the data (*Exact*).

### Timeline

All times are the author's clock, EDT.

- **Before the plan.** Seen-data downgrade and transfer diagnostics (exploratory, sealed study-011) `6494a35`.
- **Pre-registration and preparation.** Plan, freeze and `docs/ROADMAP_TO_GI.md` `0cccf0d`; seed check `9f4d4db`; second implementation `experiments/v0100_reference.py` `a44a8da`; implementation `2564201`, `1c43d68`; smoke, kill drill (0.257 s), RATE_MATH_012 and deviation #49 `4628617`/`5ae0891`; deviation #50 `2fb806c`; pre-freeze fix `7e77621`.
- **Freezes.** Source frozen at `b40f263`. Scoring scripts at `22ce7f7`, ledgered 08:57:44 EDT (682 s before run_start).
- **Held-out run** (`scripts/run_study_012.py` plus the independent `scripts/watchdog_012.py`). Started 09:09:06 EDT under a hard 2 h cap (11:09:06 EDT). RUN_DONE 09:37:26 EDT (1,700 s). The watchdog did not fire, and every stream completed.
- **After the run.** Seal `c07d773` (38 digests verified before commit); GATES_012 `1080654`; release tooling `be6a4ea`; release freeze `BRUTE_RELEASE_FREEZE_0100.json` `fb4ffd1`; clean clone `173465a`. Deviations #48–#51 are in `docs/research/BRUTE_DEVIATIONS_012.md` (#51: .gitignore patterns for study-012 were added after the run and before the seal commit).

### Code

- **Transfer**: TRp (a motif library from a same-family, fully observed source, used as a filter over relabelled copies), TRn (a negative control with a rotated, unrelated-family library), and a second-implementation transfer audit.
- **J10**: SP8 plus an exact jump-window support. Research arm, not the default.
- **big78**: J10_78 and SP8_78 on 7–8 state worlds.
- **Release.** `scripts/verify_release_0100.py` (short and `--long`), `tests/test_release_0100.py`, `scripts/clean_clone_012.py`, `scripts/study012_storage.py`, `scripts/make_release_freeze_0100.py`, `brute/release_version_0100.py`.

### Results (*Observed*)

- **Transfer.** GT_b PASS: TRp mean S 20.18 steps, seed-paired CI95 [19.18, 21.17]; 270/288 helped, 0 hurt; ood4 largest (32.0). TRp: 0 false certificates in 20,027. GT_ref PASS: 288/288, 0 mismatches. GT_a FAIL: TRn 167 false certificates (all from the transfer rule, out of 322) in 50/288 cases, and the library was disabled in all 288 cases. GT_c FAIL: TRn false certificates, and S_n 4.53 [3.37, 5.73] > 0.
- **Coverage.** GJ10 PASS: J10 − J9 +0.0090 [0.0059, 0.0122]. G6b FAIL: J10 − A2 −0.1657 [−0.1767, −0.1551]; GA1_012 fails through it.
- **Drift.** G3L PASS (J10 0 at lag ≥ 2). G3′ strict FAIL (J10 1 at lag 1; J9 1; SP8 16; control 318).
- **7–8 states.** G78_soundness PASS (0 of 193 certificates false) and G78_containment PASS (0 exceptions in 25,344), but coverage is 0.1–1.6%.
- **Soundness and safety.** G1, G2, G4, G5, G7, G9, GH and G10 all pass.
- **Exactness and reproducibility.** G11: mandatory and optional 108/108, 0 mismatches, mutation 20/20. G12: 264/264 and 96/96. GLV `--long`: 33 cases, 0 mismatches, ~21 s. GCC: PASS.
- **Runtime.** G_RT PASS; R_G_RT_strict is true for the first time. Max heartbeat gap 44 s.
- **GTI.** FAILS as frozen on the 3 declared test_release_080 failures; R_GTI_K080 passes. The 0.10.0 bump also turns the test_release_090 version and verify tests red (to be declared in v0.11.0).

## v0.9.0: selective window hull (J9), G_RT mandatory vs optional, clean-clone and --long verify, 7–8 state feasibility (study BRUTE-090-WINDOW-011)

**15 of 17 gated criteria pass.** Two fail: G6b and GA1_011 (headline target). *Observed*; scoring rules were fixed before the data (*Exact*).

### Timeline

All times are the author's clock, EDT.

- **Before the plan.** Lag diagnostic on seen data (sealed studies 008–010, exploratory) `a5ef9c8`/`0c3f348`: 23/28 stale certificates at lag 1.
- **Pre-registration and preparation.** Plan `7950513` (`experiments/BRUTE_PLAN_011.json`); seed check `06249f7`; second implementation `experiments/v090_reference.py` `d5c6a54`; implementation `8eeb810`, `4c4800b`, `052ec9d`; kill drill and scoring scripts `13b12ee` (0.228 s); rate math `6cf27bd`.
- **Freezes.** Source frozen at `f658e13` (30 files). Scoring scripts (at `13b12ee`, deviation #43) ledgered 06:38:21 EDT.
- **Held-out run** (`scripts/run_study_011.py` + independent `scripts/watchdog_011.py`). Started 06:48:41 EDT under a hard 2 h cap (08:48:41 EDT). RUN_DONE 07:18:53 EDT (1,812 s). The watchdog did not fire.
- **After the run.** Seal `6ae2cc4` (26 files); GATES_011 `ed2b042`; release tooling and RELEASE.json; release freeze `BRUTE_RELEASE_FREEZE_090_R1.json` (supersedes `_090`, deviation #44). Clean-clone gate GCC PASS. Deviations #40–#42 in `docs/research/BRUTE_DEVIATIONS_011.md`, #43–#47 in `docs/research/BRUTE_DEVIATIONS_011_R1.md` (#47: the #42 ledger receipt names the wrong commit; file restored and continued in R1).

### Code

- **`brute/jumpwindow.py`**: J9, SP8 certification plus a selective K=4 window hull (`JumpWindowRegionK`, `WindowSyncLearner`). Research arm, not the default.
- **`experiments/v090_reference.py`**: second implementation by row enumeration, with a mutation test.
- **Run control.** `scripts/run_study_011.py` (mandatory vs optional streams), `scripts/watchdog_011.py`, `scripts/run_tests_090.py` (GTI), `scripts/seal_011.py`, `scripts/feasibility_011.py` (7–8 states).
- **Release.** `scripts/verify_release_090.py` (short and `--long`), `tests/test_release_090.py` (tamper matrix, tracked-files test), `scripts/clean_clone_011.py`, `scripts/study011_storage.py`, `scripts/make_release_freeze_090{,_r1}.py`, `brute/release_version_090.py`.

### Results (*Observed*)

- **Soundness and safety.** G1/G2: 0 false certificates for J9 and SP8. G4: 0 public false certificates. G5: 0 alarms.
- **Drift.** G3L: J9 0 non-drift false certificates at lag ≥ 2 (and 0 at lag 1); SP8 7 at lag ≥ 2 (power informative). Strict G3′: J9 0, SP8 16, control 323, the first strict pass for any arm. J9's 8 false certificates are all at drift steps.
- **Coverage.** G6b fails: J9 − A2 −0.1918 [−0.2073, −0.1772]. J9 − SP8 −0.1660 [−0.1803, −0.1520]. SP8 − A2 −0.0109 [−0.0172, −0.0054].
- **Hull.** GH: 595 checked, 0 exceptions. 38% (cycle3) and 68% (drift4) of hull steps admit every code.
- **Exactness and reproducibility.** G11: mandatory 0 mismatches, mutation 20/20; optional rest 960/1,152 traces, 0 mismatches (stopped at its budget). G12: 264/264. GLV `--long`: 33 cases, 66 traces, 0 mismatches, 363 s.
- **Runtime.** G_RT passes under the plan-011 mandatory/optional rule; R_G_RT_strict (v0.8.0 reading) false. One 78 s heartbeat gap.
- **Feasibility (ungated).** n6–n8 all feasible, millisecond median solve times.

## v0.8.0: jump-hull certification, aligned lookahead, a silent-jump diagnostic, a hard 2 h cap with a watchdog (study BRUTE-080-ALIGN-010)

**12 of 17 gated criteria pass.** Five fail: GA1_010 (target a), G3′, G6b, GD and G_RT. **G11, GX2_010 and GTI pass, inside the cap.** *Observed*; scoring rules were fixed before the data (*Exact*).

### Timeline

All times are the author's clock, EDT.

- **Pre-registration and preparation.**
  - Criteria pre-registered at `881f0a6` (`experiments/BRUTE_PLAN_010.json`).
  - Seed check `c80bdd7`.
  - GD classifier replay on sealed study-009 `299babf`.
  - Second implementation `experiments/v080_reference.py` `385ea23`.
  - Implementation `2360559`…`8c7fdf2`.
  - Smoke runs and kill drills smoke-1/2/3. The watchdog fix is in DEVIATIONS_010 #28.
- **Freezes.** Source frozen at `5470c48`. Scoring scripts frozen at `39d255b` (ledger scoring_freeze_010, 04:52:47 EDT).
- **Held-out run** (`scripts/run_study_010.py` + independent `scripts/watchdog_010.py`).
  - Started 05:03:17 EDT under a hard 2 h cap (07:03:17 EDT).
  - RUN_DONE at 05:36:07 EDT (1,970 s). The watchdog did not need to fire.
- **After the run.**
  - Seal `1bdebc9` (47 files).
  - GATES_010 ledgered at `0422ac0`.
  - Sealed run state committed at `7b8a06d`.
  - main merged in at `b1e628d`.
  - Release freeze `BRUTE_RELEASE_FREEZE_080.json`.
  - Deviations are in `docs/research/BRUTE_DEVIATIONS_010.md` (#27–#39; #38 is a superseding ledger receipt for the frozen harness, #39 a pre-publication verifier fix).

### Code

- **`brute/jumphull.py`**: J8, which is S7 plus a one-step jump hull. A certificate survives only if Y1k on the region without its last transition gives the same single code. It is a research arm, not the default.
- **`brute/align.py`**: SP8 / BSP8, which is SC7 / BSC7 certification with the aligned lookahead LU-C. It is a research arm, not the default.
- **`experiments/v080_reference.py`, `scripts/run_reference_010.py`**: an independent second implementation with a mutation test.
- **`experiments/v080_xcheck.py`**: incremental symmetric CaDiCaL cross-check plus a spot check.
- **Run control.** `scripts/run_study_010.py` (checkpointed streams, per-stream budgets, hard cap), `scripts/watchdog_010.py` (an independent process that SIGSTOPs the orchestrator and kills its descendants), `scripts/run_tests_080.py` (GTI) and `scripts/seal_010.py`.
- **Release.** `scripts/verify_release_080.py`, `tests/test_release_080.py`, `scripts/study010_storage.py`, `scripts/make_release_freeze_080.py` and `brute/release_version_080.py`.

### Results (*Observed*)

- **Soundness and safety.** G1/G2: 0 false certificates for every arm. G4 passes. G5: max 2/72 on perm4.
- **G3′.** J8 0 non-drift false certificates; SP8 3; SC7 4.
- **G6b.** SP8 − A2 −0.0167 [−0.0228, −0.0113], a pass and the first in the project. J8 − A2 −0.2242 [−0.2381, −0.2110]: J8 coverage is 0.
- **Reported contrasts.** SP8 − SC7 +0.0345 [0.0272, 0.0420]. BSP8 − BSC7 +0.0195 [0.0100, 0.0297].
- **GD.** Clause (i) fails: 1/4 and 1/3 silent-jump class against the 0.8 threshold. Clause (ii) passes.
- **Exactness and second implementation.** G11: 648/648 + 144/144 traces with 0 mismatches; mutation 20/20. GX2_010: 100% of steps, 0 mismatches.
- **Reproducibility.** G12: 216/216 + 96/96.
- **G_RT.** Clause (i) fails: the optional g11_2x2 phase hit its own budget. Clauses (ii) and (iii) pass; kill latency 0.239 s.

## v0.7.0: synchronous drift events, incremental symmetric xcheck, a count planner, per-module test isolation (study BRUTE-070-SYNCPLAN-009)

**9 of 17 gated criteria pass. GA1′ (target a), GP1 (target c), G3′ and G6b fail on the data; GX2″ (target b), GTI (target d), G11 and G_RT fail STUDY_BUDGET** because the 3 h stop rule fired (*Observed*; scoring rule fixed before data, *Exact*).

Timeline (commit and ledger times are the author's clock):

- Criteria pre-registered at `3825ad3` (`experiments/BRUTE_PLAN_009.json`); seed check, lag diagnostic a0 on sealed study-008, second implementation `experiments/v070_reference.py`.
- Source frozen at `f9b94e7`; scoring scripts frozen at `b49cc37` (ledger scoring_freeze_009, 19:53 EDT).
- Held-out run (`scripts/run_study_009.py`) started 20:04:06 EDT; 3 h cap 23:04:06 EDT; the stop rule fired at 23:22:42 EDT (late, DEVIATIONS_009 entry 21). gx2_spot stopped by its 30 min stream budget (6/24 cases); g11 stopped by the cap with no output; GTI never started.
- Pack `30bb932`, ledger run_end_009 + study SEAL `327d4fd`, paired + reproducibility, GATES_009 `a50f751`, final-tree test run and GATES_009_FINAL, release freeze `BRUTE_RELEASE_FREEZE_070.json`. Deviations: `docs/research/BRUTE_DEVIATIONS_009.md` (entries 1–25).

Code:

- **`brute/syncevent.py`**: research arms S7/SC7 (2x2) and BS7/BSC7 (breadth): certificates are withdrawn on synchronous events E1 ∪ E2 ∪ E3. Not the default.
- **`brute/planner.py`**: P7, an experiment planner that scores actions with exact model counts (forked per-count 2 s limit, 150 s per case). Not the default.
- **Adopted byte-identical from `verify/xcheck-incremental` (c2bf07e):** `brute/xcheck_sat_incremental.py`, `experiments/v060_xcheck_incremental.py`, `tests/test_xcheck_sat_incremental.py`; `experiments/v070_xcheck.py`.
- **`scripts/run_tests_070.py`**: GTI runner, one fresh interpreter per test module.
- **`scripts/run_study_009.py`**: Python orchestrator with per-stream budgets, a 3 h cap and seal-partial.
- **`scripts/verify_release_070.py`, `tests/test_release_070.py`, `scripts/make_gates_final_009.py`, `scripts/study009_storage.py`, `brute/release_version_070.py`.**

Results (*Observed*): G1/G2 0 false certificates for every arm; S7 4 / SC7 5 non-drift false certificates on drift4; G6b S7 −0.0989, SC7 −0.0503; GP1 coverage −0.035; GX2″ symmetric check 100% of breadth steps, 0 mismatches, 316 s; G5 0 alarms everywhere; G12 360/360.

## v0.6.0: drift-sound certification rules, a non-enumeration exactness check, a hardened verifier, model counting (study BRUTE-060-DRIFTSOUND-008)

**11 of 16 gated criteria pass. GA1 (target a), GX2′ (target b), G3′, G5 and G6b fail.** GT1 (target c) and GMC
(target d) pass.

Timeline:

- Criteria pre-registered at `89c2d3b` (`experiments/BRUTE_PLAN_008.json`).
- Second implementation `8863f06` (`experiments/v060_reference.py`, same author, no `brute` import).
- Implementation `457db5a`/`6556186`/`ff4d0d8`/`6f6cd22`; pre-freeze fix `cae25ce`.
- Source frozen at `8e80615`.
- Scoring scripts committed alone at `08ac3f3` (08:38:46 EDT); ledger `run_start_008` at 08:49:16 EDT; sealed at `c21ef12`.
- Stream A (xcheck) stopped by owner decision at 17:44 EDT after 46/288 cases.
- Criteria and scoring scripts were not changed afterwards. Deviations are in `docs/research/BRUTE_DEVIATIONS_008.md` (D1–D26). The release freeze is `experiments/BRUTE_RELEASE_FREEZE_060_R1.json`, which supersedes `BRUTE_RELEASE_FREEZE_060.json` (D26).

Code:

- **`brute/driftsound.py`** (`DriftSoundLearner`, research arms R6 = rule RO and C6 = rule CT, breadth BR6/BC6).
  - R6: for W = 8 steps after a surprise, transition edges confirmed only before it are treated as unknown in the Y1k check.
  - C6: also certify on the v0.2.0 tracked-state projection while the session has had no surprise.
  - Not the default. The release default stays the v0.5.0 rule.
- **`brute/xcheck_sat.py`, `experiments/v060_xcheck.py`**: a second CNF encoding solved with CaDiCaL, with witness
  checks, that re-decides breadth traces without enumeration.
- **`brute/modelcount.py`**: exact |R_t| (pyganak 2.8.0), a blocking-clause cross-count, sum checks, and approxmc
  estimates for UNKNOWN counts only. Reporting only; the pins are in `requirements-gmc.txt`.
- **`scripts/verify_release_060.py`, `tests/test_release_060.py`, `scripts/make_gt1_008.py`**: every artifact is
  parsed through one guard that raises `VerificationError`. This fixes the v0.5.0 `JSONDecodeError` defect in the
  new verifier; the frozen v0.5.0 pair is unchanged. `brute.release_version_060`.
- **`scripts/make_xcheck_partial_008.py`** (post-stop wrapper, D22): turns the partial xcheck checkpoint into the
  frozen report schema with full-denominator fractions, so the unchanged gate script scores incomplete coverage as FAIL.

Study-008 results (*Observed*):

- **Failed:**
  - **GA1:** no arm passes G1+G2+G3′+G6b.
  - **G3′:** R6 had 20 false certificates with 1 at a non-drift step; C6 had 26 with 2. Each non-drift event comes one step after a drift. The limit is 86.
  - **G6b:** R6 − A2 −0.101235 [−0.112695, −0.089699]; C6 − A2 −0.072145 [−0.084144, −0.060724].
  - **G5:** perm4 R6 and C6 4/72 = 0.0556. The same 4 cases alarm in A4/A5 (D24).
  - **GX2′:** incomplete coverage, 46/288 cases. On what was checked: 0 mismatching traces, 0 witness failures, 0 disagreements with enumeration. big6 within the checked cases was 0.986 < 0.99.
- **Passed:**
  - G1/G2: 0 false certificates in every arm, including ood5 (R6 0/39, C6 0/44) and ood6s3 (B5 0/505, BR6 0/486, BC6 0/550).
  - G4.
  - G7: log-loss ood5 0.644, drift4 1.095, ood6s3 1.371.
  - G9: 273 retractions, 8 resumes, 0 violations.
  - G10: 0 production forecasts used an UNKNOWN answer.
  - G11: 0/1,872 mismatching traces, mutation 20/20.
  - G12: 312/312 byte-identical; GMC recount 120 cases, 11 timeout-only differences.
  - G13.
  - **GT1:** 56/56 corruptions give `VerificationError`.
  - **GMC:** 3,232/3,240 counted (0.997531), 0 disagreements, 0 sum violations.
- **Reported, not gated:** C6 − A5 coverage +0.023 [0.019, 0.027]; R6 − A5 −0.003; breadth counts 1,881/2,016;
  R_dev_xcheck_007 not run.

## v0.5.0: the constraint region as the engine; breadth families; projection-volume tie-break (study BRUTE-050-REGION-007)

Criteria pre-registered at `5be08aa` (`experiments/BRUTE_PLAN_007.json`); second implementation `1b57efe`
(`experiments/v050_reference.py`, same author, no `brute` import); implementation `fc2bed8`/`c8e8611`/`b693113`;
pre-freeze fix to the reference `0c86d90` and infrastructure `d7054a1`/`b2c4209`; source frozen at `064a50e`; scoring
scripts committed alone at `50e9321` (06:00:43 EDT), ledger `run_start_007` 06:11:52 EDT (11.2 min later), sealed at
`51215e0`. Criteria and scoring scripts unchanged afterwards. Deviations: `docs/research/BRUTE_DEVIATIONS_007.md` (Q0–Q7).

- **`brute/region.py`** (`RegionK`, `RegionSpace`): the constraint region for k actions and s sensors with tri-state
  SAT answers (True / False / UNKNOWN under a per-query conflict budget).
- **`brute/region_learner.py`** (`RegionBruteLearner`, arms A5 and M5): the v0.4.0 rules with every version-space query
  on the region; **SOLVER_BUDGET** overlay — a forecast that used an UNKNOWN answer is ABSTAIN, never CERTIFIED; policy
  `M` (projection-volume tie-break for LU-R ties).
- **`brute/breadth.py`** (B5/BM5/BP5) and pre-registered breadth families big6 (≤6/≤7), sens3 (3 sensors), act3
  (3 actions), ood6s3 (declared out of family); τ7 = 2.07944154168 calibrated on 450 in-family breadth cases.
- **API 1.5** (`brute/api/service_v050.py`, schemas `*.v1_5.json`); `brute.release_version_050`.
- **Study-007 (Observed):** 12 of 15 gated criteria pass. **GX1** A5 = A4 on all 25,344 steps (0 mismatches, 0
  excluded). **GX3** 257 budget-hit forecasts, all abstain. G1/G2 0 false certificates in every arm, incl. breadth
  and ood6s3. **Failed:** GX2 (0 mismatches, act3 only 84.5% of steps checkable by the reference, 90% registered),
  G3′ (M5 1 non-drift false certificate on drift4), G6b (M5 − A2 −0.0796 [−0.0996, −0.0602], predicted).
  **GM NOT DISTINGUISHED:** M5 − A5 +0.0262 [0.0109, 0.0425], BM5 − B5 +0.0391 [0.0204, 0.0579], but G3′ fails for M5.
  Second implementation 0/2,592 arm traces, mutation 20/20. Reproducibility 296/296 byte-identical.
- **GR2′ scaling (Observed raw, Inferred fits, not gated):** 0 UNKNOWN answers at n = 4..12 in three alphabets; clause
  maxima 2,323 → 15,055 (2a2s, n = 4 → 12); cubic fit near-interpolating (5 n values); power exponents 1.57–1.74 with
  curved residuals; enumeration too censored to fit; time noisy and non-monotone.
- **Process (post-start, labelled post hoc; review of v0.4.0):** `scripts/check_smoke_seeds_007.py` (smoke seeds
  901–903 disjoint from all 468 evaluation seeds; one held-out seed's world tables were printed by eye at 05:25, Q0);
  retroactive ledger entry for smoke runs; `experiments/v050_prob_reference.py` recomputes v0.90 forecast probabilities
  on taken and untaken branches (study-007 A4/A5/M5: 0/1,728 traces, 130,602 forecasts, swap mutations 20/20; also
  applied to study-006 as v0.4.0 errata E3); `scripts/scaling_fit.py` (stated models with residuals).
- `BRUTE_RELEASE_FREEZE_050.json` locks the scoring scripts, release verifier/test and the post-start audit scripts.
- `scripts/verify_release_050.py`, `tests/test_release_050.py` (version-parameterised, tamper cases).

## v0.4.0 errata (2026-10-25, docs and new post-hoc checks only; tag `v0.4.0` and sealed results unchanged)

From an external read-only review; details in `docs/research/v0.4.0/ERRATA.md`, new deviation P8 in
`docs/research/BRUTE_DEVIATIONS_006.md`, ledger `errata_040`. No number in the sealed results changed.

- **H1 (high).** Study code and the full scoring chain (incl. PAIRED R = 0.571 on 96 D7/D8 cases) ran on 96 **held-out**
  study-006 cases at 02:29–03:08 EDT, **before** the scoring-script commit `d9ddbe6`. "Committed before any study-006
  run", "smoke data only, not study data" and "before any v0.4.0 code" are withdrawn. GR1b's held-out status is
  weakened for the 16 overlapping cases; 96/576 cases were not blind when the scoring scripts were committed.
- **M1.** GR2 exponents "n^1.6 vs n^8.5" and "O(n^2 T)" withdrawn. Refit with residuals (*Inferred*): enumeration rows
  ≈ exponential (×6.9 per state, n=2..5, censored n=6 excluded); clauses ≈ cubic polynomial, O(T·n² + n³).
- **M2.** G11 checked forecast probabilities only for sum/floor/source in the v0.90 regime. Post-hoc recompute
  (`experiments/v050_prob_reference.py`): 0/1,152 A4+P4 traces mismatching, 88,038 forecasts, mutation 20/20.
- **M3.** GR1 is a development-set check (study-004/005 traces already used by design probes).
- **L1–L6.** P4 had 1 stale counterfactual certificate; n=6 SAT maxima were not budget hits; main D7/D8 block R = 1.5
  with 266/2,000 zero denominators; test suite red by construction; reference-vs-plan order *Open*; "before any code"
  qualified.

## v0.4.0: geometric representation of the version space (study BRUTE-040-GEOMETRY-006)

Criteria pre-registered at `5fa3628` (`experiments/BRUTE_PLAN_006.json`) before any `brute/` v0.4.0 code (design probes
ran earlier, P0); second implementation
`2eba00b`; implementation `2811904` + pre-freeze fix `b5e7077`; source frozen at `70a3c43`; scoring scripts committed
alone at `d9ddbe6` (03:08:51 EDT), ledger `run_start_006` at 03:20:15 EDT (11.4 min later), sealed at `454094c`.
Criteria and scoring scripts unchanged afterwards. **Errata: the scoring chain had been dry-run on 96 held-out cases
before `d9ddbe6` (P8).** Deviations: `docs/research/BRUTE_DEVIATIONS_006.md` (P0–P8).

- **`brute/geometry.py::ConstraintRegion`** — the version space as CNF over complete ≤n Moore machines (pysat Glucose3,
  canonical first-visit symmetry breaking); support = projection, saturation = sub-region emptiness, Y1k = fibre,
  observation = cut. **GR1** 0 mismatches in 778,840 items on 2,016 sealed study-004/005 traces; **GR1b** 0 in 470,318
  on study-006 (*Observed*; GR1 is development-set, GR1b weakened for 16 cases, errata). **GR2** scaling: ~~clauses ~n^1.6 vs enumeration rows ~n^8.5~~ (withdrawn, errata M1); SAT time noisy and
  non-monotone, 17 budget-unknown steps at n = 8–12, slopes on 5–8 points (*Observed*, not gated). Not used by the
  learner (*Exact*).
- **`brute/resume.py`** — A4/P4: v0.3.0 Y1k + LU-R with τ6 = 1.645215321642 (in-family calibration, G13) and a
  resumable alarm; D2 (two-step lookahead) and F2 (two-step fibre) candidates.
- **`brute/api/service_v040.py`** — API 1.4 (`schema/*.v1_4.json`): predict responses gain `resumed` and `alarm_resumes`; `tau` defaults to τ6.
- **perm4** — a new held-out family (each action a permutation of 4 states, one aliased emission pair), pre-registered before its data.
- **Results (*Observed*).** 15 of 16 gated criteria pass; **G6b′ fails** (A4 − A2 −0.104 [−0.116, −0.092],
  pre-registered). G5 passes (ood4 1/72; v0.3.0 τ also 1/72 on these seeds; perm4 2/72 vs 14/72). G15 (D2) and G16 (F2)
  fail; F2 breaks G3′. **G14′ D7/D8 OPEN**: R = 0.632 [0.418, 0.907] at N = 384 (power-analysed). Resume: 3 per arm,
  0 certificates after resume. G11 second implementation by the same author: 0 of 2,880 traces mismatching, mutation
  20/20. G12 byte-identical rerun.
- **Release hygiene.** `pyproject.toml` 0.4.0 with numpy 2.5.4 and python-sat 1.9.dev17 pinned;
  `scripts/verify_release_040.py` and `tests/test_release_040.py` read the version from `RELEASE.json`; fresh-clone
  checks restore the gitignored traces first (`scripts/study006_storage.py restore`).


## v0.3.0 errata (2026-10-25, docs and new checks only; tag `v0.3.0` and sealed results unchanged)

After an independent cold review (`docs/research/v0.3.0/ERRATA.md`). No criterion, scoring script, frozen file or sealed
result changed.

- G11 is reworded everywhere as a **second implementation by the same author, no `brute` import**, not an independent
  audit. New `scripts/audit_count_030.py` reports a real mismatch count (scans every arm trace; the frozen reference stops
  at the first mismatch) and has a mutation test (`tests/test_audit_mutation_030.py`). Result: 0 mismatching of 3,168 arm traces (*Observed*).
- G3′ headline now sits next to the extended-block result (A3 38 false / 2 non-drift / 4 stale on 216 cases).
- Process claims softened to what git shows (parent order, not time); P0 relabelled; DISCOVERIES D13 retitled to the
  OPEN verdict; G5 per-family wording clarified; evidence labels added to the README Status table; "not AGI" is Exact.
- `tests/test_tamper_by_version.py`: each release verifier (v0.1.0–v0.3.0) on its own tag tree passes and catches
  tampering. `scripts/check_order_030.py`: scoring scripts precede the sealed results and are unchanged.
- `requirements.txt` pins numpy 2.5.4 (the tested environment); `pyproject.toml` version 0.3.0. Quickstart restores the
  gitignored traces before the tests.

## v0.3.0: fibre-robust certification (study BRUTE-030-CHANGEPOINT-005)

Criteria pre-registered at `25fa47b` before any v0.3.0 code (pre-freeze probe code disclosed, deviation P0); source
frozen at `f7f3bd3` before the run; scoring scripts committed at `a1889b6`, the git parent of the sealed results (same
timestamp, so "before results were seen" is the author's report, not verifiable; errata E3). Criteria were not changed
afterwards. Deviations are in `docs/research/BRUTE_DEVIATIONS_005.md`.

- **Y1k certification** (`brute/changepoint.py::ChangePointBruteLearner`): a CERTIFIED forecast stays certified only if
  it is constant on the fibre of the n≤4 region over the latest observation (known edges; an unknown edge from the
  current state counts as any code); otherwise ABSTAIN with `RESYNC_AMBIGUOUS` (never issued).
- **LU-R experiments:** the v0.2.0 one-step lookahead scored with the Y1k gate. Optional `CHECK_RUN k` (0 in v0.3.0;
  k=3 only for the mechanism arm E2).
- **brute.api 1.3** (`BruteServiceV030`, `request/response.v1_3.json`): `RESYNC_AMBIGUOUS`, `experiment.check`,
  `proposal: NO_PROPOSAL` with `no_proposal_reason` after OUT_OF_FAMILY (bridge O3).
- **Version:** `brute/release_version_030.py` = 0.3.0 (earlier version files stay frozen).
- **Storage (D1):** sealed traces committed as deterministic gzip; `scripts/study005_storage.py restore`.
- **Study tooling:** five-arm runner (A3, P3, A2, P2, E2 + C and v0.90 controls) plus a 216-case extended drift4 block,
  τ calibration check, second implementation by the same author (no `brute` import), gates/paired/reproducibility generators with
  `--check`, `verify_release_030` (`--frozen` runs the unmodified v0.2.0 verifier on the raw v0.2.0 tree). Locks:
  `BRUTE_SOURCE_FREEZE_005`, `BRUTE_RELEASE_FREEZE_030`.
- **Results (Observed): 12 of 14 gated criteria pass; G5 and G6b fail.**
  - **G3′ passes:** drift4 A3 9 false certificates, all at drift steps, 0 stale (v0.2.0 A2: 15, 1 non-drift, 2 stale;
    v0.90: 89). 0 false certificates in family and on ood5 (taken, counterfactual, public), every arm.
  - G6 dual coverage gain A3 − P3 **+0.064352**, CI95 [0.055054, 0.073922].
  - **G6b fails (pre-registered risk):** A3 − A2 −0.098264, CI95 [−0.110885, −0.087267].
  - **G5 fails:** ood4 5 of 72 cases raise a residual-surprise alarm (0.069 > 0.05), identically in v0.1.1 and v0.2.0.
  - ood5 log-loss A3 0.63875, P3 = C 0.648728; drift4 A3 1.162304, P3 1.163681, A2 1.170786, C 1.181917.
  - G14 (D7/D8 single-mechanism test, not gated): **OPEN** — S(A2) 17, S(E2) 14, S(A3) 4.
  - Second implementation (same author, no `brute` import) ran to completion over 139,392 arm-steps (it stops at the
    first mismatch; errata count in E4); reproducibility byte-identical; τ reproduces.
- **Tests:** see README Status (measured on a fresh clone). Expected errors are frozen earlier-release version checks
  that fail by construction on the RELEASE.json bump (N1).

## v0.2.0: active experimentation and window rebuild (study BRUTE-020-ACTIVE-004)

Criteria pre-registered at `c0ac594` before any v0.2.0 code; source frozen at `8bf8759` before the run. Criteria were not
changed afterwards. Deviations and implementation notes are in `docs/research/BRUTE_DEVIATIONS_004.md`.

- **X1 active experimentation** (`brute/active.py::ActiveBruteLearner.experiment`): a one-step certifiability lookahead
  (LU) over copies of the n≤4 and n≤5 regions. Certification rules are unchanged.
- **X2 window rebuild:** a `window_n4` forecast tier after contradiction (n≤4 learner restarted at each contradiction).
- **X3 issuance de-duplication:** `record_issued` records a (step, certificate) pair once; fixes the bridge
  double-issuance bug (B1). Study-003 had 0 duplicates (Exact check, 504 cases).
- **X4 brute.api 1.2** (`BruteServiceV020`, `request/response.v1_2.json`): a read-only `experiment` op and response field
  (`action`, `score`, `scores`, `rule`, `tie_break`, `tied`, optional per-action `counts`).
- **X5 version:** `brute/release_version.py` = 0.2.0 (`brute.version` 0.1.1 and `brute.__version__` 0.1.0 stay frozen).
- **X6 clone hygiene:** `.gitattributes` `*.ps1 -text` (fixes 2 of the 3 tests failing on a fresh clone of main, B2),
  regenerated MANIFEST, README test count measured on a fresh clone.
- **Storage (D1):** the 133 MB sealed traces are committed as deterministic gzip; `scripts/study004_storage.py`
  restores and checks them against `SEAL.json`.
- **Study tooling:** three-arm runner (A active, P passive, C frozen v0.1.1), τ calibration check, second implementation by the same author (no `brute` import)
  gates/paired/reproducibility generators with `--check`, `verify_release_020` (runs the frozen
  v0.1.1 and v0.1.0 verifiers with `--frozen`). Locks: `BRUTE_SOURCE_FREEZE_004`, `BRUTE_RELEASE_FREEZE_020`.
- **Results (Observed): 12 of 13 gated criteria pass; G3′ fails.**
  - Dual coverage gain A − P pooled **+0.115355**, CI95 [0.10409, 0.127123]; every family CI excludes 0.
  - 0 false certificates in family (taken, counterfactual, public) and on ood5, both arms.
  - **drift4: A 24 wrong of 221, 3 at non-drift step 13 → G3′ fails;** P 1 of 16 (passes); v0.90 81.
  - ood5 log-loss A 0.665014, P = C 0.67712; drift4 A 1.034239, P 1.056963, C 1.06755, suffix-1 1.181247.
  - Independent audit 0 mismatches; reproducibility byte-identical; τ reproduces.
- **Tests:** see README Status (measured on a fresh clone). 2 expected errors are frozen earlier-release version checks
  that fail by construction on the RELEASE.json bump (N1).

## v0.1.1: open-world fallback forecast (study BRUTE-011-FALLBACK-003)

Pre-registered at `1585a77` before any v0.1.1 code. The owner chose G3′ over G3 before the freeze. Criteria were not
changed afterwards. Deviations are listed in `docs/research/BRUTE_DEVIATIONS_003.md`.

- **F0 freeze hygiene:** the study-001, study-002 and v0.1.0 release locks are unchanged. New code is in new files.
  `brute.version.RELEASE_VERSION = '0.1.1'`; `brute.__version__` stays `0.1.0` (amendment A3).
- **F1 fallback forecast** (`brute/fallback.py::FallbackBruteLearner`): after the n≤4 family is contradicted, it
  forecasts from the n≤5 margin support while that support is consistent, otherwise from suffix-1, always with the ε
  reserve. It does not certify more than before. Before a contradiction it is identical to v0.1.0, verified on 15,840
  in-family steps.
- **F3 brute.api 1.1** (`BruteServiceV011`, `request/response.v1_1.json`): `forecast_source` and per-retraction reasons
  (`falsified_by_observation`, `scope_withdrawn`, `unverifiable_masked`).
- **F4 witness audit** (`scripts/witness_audit.py`): n≤5 divergent witnesses, each verified by replay.
- **Study tooling:** a two-arm lockstep runner, a τ calibration check, a second implementation by the same author (no `brute` import),
  gates/paired/reproducibility/R4 generators with `--check`, and `verify_release_011` (pre-registration order check;
  `--frozen-v010` runs the frozen v0.1.0 verifier on `git archive v0.1.0`). Locks: `BRUTE_SOURCE_FREEZE_003`,
  `BRUTE_RELEASE_FREEZE_011`.
- **Results (Observed):** all 11 gated criteria pass.
  - ood5 log-loss 0.624547 (v0.1.0: 1.480828; ln 4 = 1.386294).
  - drift4 log-loss 1.155589 (v0.1.0: 1.298329; suffix-1: 1.167906).
  - False certificates: 0 in family, 0 on ood5, 4 on drift4, all at perturbation steps (v0.90 control: 83 and 71).
  - Coverage is unchanged from v0.1.0.
  - The original G3 would fail (4 wrong drift4 certificates).
- **Tests:** 127 tests, 126 pass. 1 expected error: the frozen v0.1.0 tamper test fails on the version bump (A3, D2)


## v0.1.0: verified abstention (study BRUTE-010-ABSTENTION-002)

Pre-registered at `d402c75` before implementation. Criteria were not changed afterwards; deviations are listed in
`docs/research/BRUTE_DEVIATIONS_002.md`.

- **F1 contradiction and retraction:** OUT_OF_FAMILY when no machine fits; certificates falsified by an observation are
  withdrawn with receipts.
- **F2 margin gate:** a certificate needs an n≤4 family support and an n≤5 margin support that agree.
- **F3 saturation:** abstain when every surviving machine uses the full state bound.
- **F4 residual surprise:** windowed test with W=8 and τ=1.433141502274, calibrated on separate seeds.
- **F5 named family:** an explicit family-contradicted event; every certificate names its family and is checked against
  the surviving belief.
- **F6 coverage:** coverage, selective risk and abstentions by reason per family, with a consistent burn-in.
- **F7 open-world reserve:** ε=0.02, so the minimum probability is 0.005, replacing the 1e-12 floor.
- **F8 v0.89 comparison:** the per-step v0.89 score is recorded and scored on its valid steps.
- **F9 generators:** GATES, PAIRED_ANALYSIS, API_REPLAY and EXPLORATORY each have a generator with `--check`.
  `verify_release` raises `VerificationError` (survives `python -O`) and asserts no study numbers.
- **F10 timing:** all wall-clock fields are `*_informational` and stripped from SCIENTIFIC.json. Calibration and
  scientific results rerun byte-identical (`REPRODUCIBILITY.json`).
- **F11 public path:** a public certificate requires an explicit scope attestation (`ScopeAttestation`).
- **F12 hygiene:** the baseline zip is optional and checked only if present; MANIFEST is built from tracked files;
  `package_release` uses `git archive`; `pyproject.toml` added.
- **F13 defaults:** a single `DEFAULT_MAX_PREFIXES` (160000) is used by the family, the margin and the API.
- **brute.api v1:** JSON request and response schemas, a service, alphabet, refusals.
- **adapters/language:** template-only renderer and grounding checker.
- **Tests:** 104 (69 inherited, 35 new).
- **Results:** 0 false certificates in all 7 families (v0.90 control: 156). Gates C1–C5, C7, C10 and C11 pass.
  **C6 fails** (ood5 log-loss 1.504767 > ln 4). Coverage fell sharply against v0.90.
- Not done: F14 (`learner_witness_audit`, the bounded n≤5 witness audit); its F2 target is covered indirectly by
  the margin gate and the API replay of the study-001 false certificates. No language model is connected.

The BGR v0.90.0 changelog is preserved at `docs/research/bgr-v0.90.0/CHANGELOG.md`.
