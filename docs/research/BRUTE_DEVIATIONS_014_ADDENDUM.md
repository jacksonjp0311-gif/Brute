# BRUTE_DEVIATIONS_014 addendum (#62, #63)

`docs/research/BRUTE_DEVIATIONS_014.md` is ledger-hashed (deviation_014) and stays unchanged. Entries after the
held-out run go here. Labels follow the project rule. Neither entry changes a gate, a threshold, a seed or a result.

**#62: scorer defect in a non-gated recount row (found after scoring, disclosed, not fixed).** `scripts/make_gates_014.py`
(frozen at the scoring freeze, 4375a5f) recounts false certificates for every arm in `GS_a.per_arm`. For the frozen
v0.11.0 control arms LXp and LXn it compares their certificates with the **SP8** trajectory actuals, but LX runs on its own
trajectory (it chooses different actions). So `GS_a.per_arm.LXp/LXn.recomputed_false` reads 1,723 / 1,503 while the
recorded count is 0. A recount against the LX trajectory's own actuals (`actuals(c)['DXp'|'DXn']`, the same trajectory DX
uses) gives **0 of 4,490 and 0 of 4,494** (Observed, run on the sealed SCIENTIFIC.json at 2026-10-27 ~00:55 EDT). LX is not
one of the gated GS_a arms (RG4, DLFp, DLFn, DXp, DXn), so no gate result changes (Exact: `per_arm_pass` lists only those
five). The scorer stays frozen; GATES_014.json is not regenerated with a fix. v0.13.0 scoring must recount every arm on
its own trajectory.

**#63: GLV long-verify case list.** `samples.long_verify` fixes 12 transfer cases but its wording ("offsets 1 and 2 of each
family at masks 0.1 and 0.6, offset 3 at 0.35 ...") describes 20. The list written in `scripts/verify_release_0120.py`
before the release freeze is 3 per family: offset 1 at mask 0.1, offset 2 at 0.6, offset 3 at 0.35 (12 cases, every
family and every mask). Each case is re-run from scratch with the frozen runner, compared to the sealed SCIENTIFIC case
(timing keys stripped) and audited by the second implementation, inside the 900 s cap.
