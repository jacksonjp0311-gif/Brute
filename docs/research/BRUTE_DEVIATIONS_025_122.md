# Deviation #122 (v0.22.0 release): verifier read the wrong key in COMMIT_ORDER_025, fixed in a new r1 file

Logged 2026-10-30 EDT, after gates_025 and release_freeze_0220, before any fresh-clone verify or tag.

1. **What happened (Observed).** `scripts/verify_release_0220.py`, frozen by BRUTE_RELEASE_FREEZE_0220, raised
   `KeyError: 'events'` in its commit-chain step. `experiments/COMMIT_ORDER_025.json` stores the list under `entries`.
   Its unit tests (`tests/test_release_0220`) did not exercise the chain step.
2. **Fix.** New files, with the frozen originals left as they are:
   - `scripts/verify_release_0220_r1.py` reads `entries`, and also checks the new BRUTE_RELEASE_FREEZE_0220_R1.
   - `tests/test_release_0220_r1.py` runs the chain on the real repo.
   - `scripts/make_release_freeze_0220_r1.py` writes `experiments/BRUTE_RELEASE_FREEZE_0220_R1.json`.
   RELEASE.json names both release freezes, and r1 is the verifier of record.
3. **Effect (Inferred).** None on any study gate. GATES_025 and PAIRED_ANALYSIS_025 are unchanged. Before this was
   committed, a scratch run of r1 passed every step, including a 14-link ancestor chain.
