# DRAFT plan 071 (v0.67.0): UNLOCKED, not preregistered

Drafted 2026-11-03 at about 13:35 EST by Grok Bot. The agent drafted this; James has not reviewed it. The user's computer was offline, so network access went through the box.

**Why:** study 070 was not certified. The kernel OOM killer SIGKILLed 7 of 51 certify/32h jobs. On the 44 sealed records, an exploratory and ungated check met every data-gate criterion at tight N. At N 12, certify/32h was IDU or OOM, while the textbook baseline decided 5/5.

**Proposed (to lock in a new BRUTE_PLAN_071.json):**
1. Re-run reset-free certification on the same 5 real decoders with fresh seeds. Keep arm B (certify/32h, unchanged) and the textbook baseline arm T (baseline/32t, unchanged), and hold out gb18030.
2. Memory budget: the runner gets a per-job RLIMIT_AS cap (for example 3 GB) and at most 3 workers. Hitting the cap is recorded as a KILL record, not an error, so the frozen liveness rule can complete. The plan states this in advance.
3. Measure the main N (true+1) and the loose N (12) separately. The loose-N arm is diagnostic, because it is where Brute currently loses to the textbook method.
4. Gate: at least 3 of 5 targets decided by B on at least 2 of 3 seeds, 0 WRONG, every job sealed (KILL allowed), and a B-vs-T table published with the gain reported against T.
5. Possible engine change (would need a new file): use T's homing-output partition as extra constraints in B's SAT encoding to cut memory at loose N, ungated until preregistered.

**What Brute can't do yet:** certify reset-free (Open); decide at a loose declared N; bound its memory; handle real noise.
