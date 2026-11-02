# Pre-plan probes for study 058 (Observed; exploratory; never gated)

Run on the box on Nov 2 2026, 10:14-10:41 EST, BEFORE experiments/BRUTE_PLAN_058.json was written, on already-sealed
study-057 seeds 12410001-12410004 (and 12410008) only. No fresh seed was touched. Scripts and logs are copied here unchanged.

1. Forecast certificate at N = 20 (proto.py-proto7.py): a fixed-h disagreement query (does any rival with <= 20 states consistent
   with the trace predict differently on a fixed h-step word?) was SAT (a rival exists) on the passive prefix (h 1, 2, 4), SAT at
   COV_O length 205, and did not finish within about 3M conflicts on the full COV_O traces (230, 266). Finding even one consistent
   model at 18-20 states on full COV_O traces failed within 300k conflicts on 4/4 seeds (p3 logs); model-finding cost on 12410001
   grows 25k -> 1.25M conflicts as the prefix grows 176 -> 230 (p6/p7 logs). greedy_fold needed > 60 blocks on all seeds.
   Conclusion (Inferred): with 2-bit readings, a forecast proof at N = 20 costs about as much as identification. Rejected as the
   058 target.
2. Reading width (proto8.py, proto9.py): the frozen active14 identifier on the scale20 transitions with emissions replaced by
   random.Random(seed).randrange(m), passive prefix 176, 200 s wall deadline, K 400:
   m 16 (4-bit): ID on 4/4 seeds (36-64 s, 40-134 extra actions); m 8 (3-bit): ID on 3/4 (12410001 unknown at 200 s).
   Labels are the identifier's stop labels; they were NOT checked against the truth in the probe (study 058 checks them).
   With m 4 (the 2-bit worlds of studies 050-057), 7 versions decided almost nothing at B 2M conflicts.
