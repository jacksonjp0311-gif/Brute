# HANDOFF — pick this project up cold

_Kept current on the working branch during a release and on `main` at release. Last updated 2026-10-28 ~17:50 EDT (v0.19.0 release in progress on `plan/v0.19.0`)._

## Current version and state

<!-- V0190 -->
- **Releasing: v0.19.0** (study BRUTE-0190-ANYTIME-021, branch `plan/v0.19.0` from main `4a644a9`). **12 of 14 gated pass.** Fresh GitHub clone of `plan/v0.19.0@3f77b17`: short verify passed (469 receipts), `--long` GLV 12 cases / 0 mismatching / 165.0 s (cap 900 s), `tests.test_release_0190` 7 OK; record `docs/research/v0.19.0/FRESH_CLONE_VERIFY_0190.json`. Local `--long`: 12 / 0 / 152.0 s. #107 header says written ~17:35 EDT; the commit is earlier (see git log), kept (ledger-hashed).
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
