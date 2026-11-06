# Deviation #212: study 072 (BRUTE-0680-BREADTH-072), post-run disclosure

Written 2026-11-05 at about 22:30 EST by Grok Bot (resumed Brute session). The agent drafted this note; James has not reviewed it. All times are EST (UTC-5).

1. **The post-run steps stalled for about 75 minutes.** The main run sealed at 21:01 and finished in 375 s. Nothing was committed and no process ran until the session resumed at 22:15. The sealed results were untracked in the meantime. No result was changed or inspected selectively in that window. This is a process failure, disclosed here. The seal commit (d2c2b20) and the ledger entry run_end_072 were written at about 22:20, so the run_end timestamp in the ledger is the commit time, and the note says when the run actually ended.
2. **Wrong interpreter first.** The first recount call used the system python, which has no pysat, and failed on import. It wrote nothing. The box venv `/workspace/bgr/venv/bin/python` has pysat and was used for every step that counts.
3. **A `--help` call ran the gates once.** `scripts/make_gates_072.py` ignores `--help` and wrote `GATES_072.json`. That was the first and only real-data run of the gates script, and `--check` then reproduced the file. Nothing was altered in between.
4. **Pre-plan exploration (disclosed by the plan).** The oracle truth was run on the 8 targets and on the 5 older ones before the lock; no Brute arm ran on any new target before the freeze, except the ungated smoke (seed 12720301, SJ and KR, B and T, recount 0 wrong).
5. **What the run showed (Observed, 2 seeds per cell, N = oracle minimum size + 1, no resets, clean readings).**
   - Arm B (brute.certify/32h, unchanged) decided 14 of 16 plus1 cells, all recount-correct. It decided every seed on SJ, KR, B5, U32, U16B, EJ4 and the held-out HK. It missed both U8S seeds: memory cap at 1.8 GiB after 78 s and 114 s.
   - Arm T (textbook) decided 16 of 16 plus1 cells.
   - Steps, B over T, median 0.18 over the 14 cells where both decided. It is not uniform: SJ 1.54 (B used more steps, 403 against 261), KR 0.89, B5 0.15-0.30, HK 0.15-0.30, EJ4 0.18, U32 0.11-0.17, U16B 0.07. So the gain shows on the larger targets, and on the two smallest targets Brute used as many or more steps than the textbook.
   - Diagnostic plus3 (N = true + 3, one seed each): B decided 0 of 8. Seven were memory-cap kills (53-114 s) and one (SJ) was a 240 s timeout. So the memory limit, not the clock, ended Brute's search on all of them. Loose N is still Open for reset-free Brute.
   - 0 WRONG over all 30 decided records of B and T (14 for B and 16 for T, all plus1; all 8 plus3 records were killed).
6. **What this does not show.** N is the true size + 1, a generous declaration; the true sizes come from an oracle that shares CPython with the targets. Two seeds per cell, clean readings, 3-11 state targets. The 1.8 GiB cap is the runner's, not a property of Brute. The gate GSTEP72 is a median over 14 cells and hides the small-target cases in item 5.
