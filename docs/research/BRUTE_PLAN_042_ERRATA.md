# BRUTE_PLAN_042 erratum 1 (plan only, before any build code)

Labels: Exact, Observed. Time: box-local EDT, 2026-10-31.

1. **Pre-plan scan note is inexact (Observed).** The plan's `heldout_ranges.note` says no word-bounded `108[0-9]00NN` token
   is in tracked uncompressed text. A post-ledger scan finds one: `10870058`, a CPU jiffy counter in
   `results/study-023/HB_SENTINEL_023.jsonl` line 1188. It is not a seed and lies in the 1087 block, which plan 042 does not
   use (it uses 1081, 1082, 1086 and 1088). No declared seed collides (Exact). The plan file is not edited; seedcheck_042
   must list this hit and confirm it is outside every declared range.
