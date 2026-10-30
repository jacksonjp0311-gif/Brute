# BRUTE_PLAN_029: v0.26.0 query throughput (plan only)

Status: **preregistered (plan only; no build authorized, no code, no data)**. Parent study: BRUTE-0250-SOLVER-COST-028.

## Question
Can exact search raise its throughput (support queries answered per step) enough to finish worlds at 12 states, without any false certificate?

## Why (Observed in study 028; cause Inferred)
- S3 capped every query at <=10.03 s (GQB pass) but U at 12 states stayed equal to S2 (0.398 vs 0.399; diff -0.001 [-0.020, 0.019])
- X(S3)=0/12 at 12 and 16 states; >98% of S3 UNKNOWNs at 12-16 states are not-run queries, under 2% solver UNKNOWN
- S3 solve_support uses about 52 s of the 55 s step budget at 12-16 states
- S1 beats both exact arms on X at 8 states (7/12) and 12 states (3/12) but makes 3 false certificates on stress
- Inferred: The limit is the number and per-call cost of support queries, not single-query overruns.

## Arms
- **S4**: S3 plus throughput changes: (i) one incremental solver per step with assumption literals instead of a fresh solve per query; (ii) witness reuse, where a model found for one query is checked against later queries before solving; (iii) query batching, where k open queries are decided by one solve over a disjunction, splitting only on SAT
- **S3**: v0.25.0 arm, unchanged (reference)
- **S2**: v0.24.0 arm, unchanged
- **S1**: baseline, unchanged
- **S4_nowit**: ablation: S4 without witness reuse

Budget: 55 s per step, 10 s per query cap, as in study 028. Soundness: every S4 certificate rechecked by the frozen exact reference; any mismatch with S2/S3 truth on an answered query is a FAIL.

## Seeds (disjoint; drawn after a ledgered seedcheck_029)
scale8 9510001-9510012; scale12 9520001-9520012; scale16 9530001-9530012; control 9540001-9540006. Total of 51 cases (42 main plus 9 stress at eps 0.05).

## Gates
- **GSC4_headline**: a) 0 mismatches of S4 vs S2/S3 and vs truth on answered queries; b) U(S4, scale12) - U(S3, scale12) <= -0.15, paired seed-bootstrap 95% CI upper bound < 0; c) X(S4, scale12) >= 3/12; d) F(S4)=0 on main and stress
- **GTP**: median support queries answered per step at scale12: S4 >= 2x S3 (Observed ratio, seed-bootstrap CI lower bound > 1.5)
- **GQB**: S4 max query time <= 10.5 s
- **G10**: S4 U=0 on 6/6 controls
- **GS_ref**: mutation detection 20/20
- **GTI**: all tests pass
- **G_PROC**: process items
- **G_RT**: run <= 1800 s
- **G_recount**: exact F recount reproduces
- **ablation_informational**: S4 vs S4_nowit U difference, reported, not gated

## New items
- src: S4 search (new module; S3 module untouched)
- scripts: run_reference_029, make_gates_029, recount_029, verify_release_0260 (new files only)
- test: pre-freeze smoke that seals a 3-case block and runs make_gates_029 --check on the SEALED SCIENTIFIC/RESULTS files (fixes the #129 defect class)
- test: queries_answered_per_step reported per arm

## Failure rule
any gate miss is published as FAIL; no rerun, no reseeding, no threshold change after data.

## Limitations
- noise-free hard masks only for exact arms
- state counts above 16 not tested
- one hardware profile
