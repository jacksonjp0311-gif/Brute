# Study-023 deviation #109 (written before the source freeze; Exact)

**Smoke blocks use the eps-based arm rule.** The plan gives RGNB4 and RGL4_prefix28 for "eps 0.02 main only". In the
held-out study eps 0.02 occurs only in the main block (stress is eps 0.05 only), so "eps 0.02" and "eps 0.02 main" pick
the same 120 held-out cases. Smoke blocks (smoke-transfer, smoke-api, smoke-drill) also run eps 0.02 cases. The runner
(`experiments/brute_study_023.arms_for`) and the reference (`experiments/v0200_reference.arms_for`, `audit_main`) now use
the eps rule only: RGNB4 and prefix28 iff eps == 0.02. The reference checks "stress iff eps 0.05" for main and stress
blocks and skips it for smoke blocks. The reference was committed at lemma_023 (e50967d) with the block rule, which
failed smoke cases; it is changed before the source freeze, and no held-out case is affected.
Found on the first smoke check (8990001 cycle3 eps 0.02, 8990003 switch3 eps 0, 8990005 unaliased2 eps 0.05: all three
audited with 0 mismatches after the change; walls 160.2 s, 46.9 s, 78.4 s single-process, Observed).
