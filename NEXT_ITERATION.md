# Brute v0.69.0 → v0.70.0: next iteration

Previous: v0.69.0 study-073 (NOT CERTIFIED, 12/15). certify/33h removed the clique-preprocess memory wall; at N=true+3 it decided 3/20 cells (SJ×2, KR×1), 0 wrong; 14 memory_cap (often pysat int32 allocator) + 3 timeout. Tight N 8/10. Homing batches added ~400 steps/round and drove T into the SAT wall.

## Proposal for v0.70.0 (plan 074, to be locked)

**certify/34h = certify/33h bitset preprocess + plain separating-word policy (no 400-step homing batch).** Same certificate logic as certify/32p; the batch was heuristic only. Pre-plan pilot (disclosed in the plan; seed 12730101): B5 and HK at N=8 IDF in 940 steps (~310 s); KR IDF in 744 steps; JO still open at 300 s.

Question: with the batch removed, how many real decoders does Brute decide reset-free at loose N, soundly, and does tight-N hold?
