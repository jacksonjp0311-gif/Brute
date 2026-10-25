# Brute research record (inherited from BGR v0.90.0)

Brute v0.1.0 starts from the research record of **BGR (Bitwork Geometric Reasoning) v0.90.0**. That record stays in this repository as Brute's evidence base. It is presented under the Brute name, but **its contents are not edited**. The files are SHA-256 locked in `MANIFEST.sha256` and `experiments/SOURCE_FREEZE.json`, and the scripts and tests read them from their original paths. This page is a Brute-framed index around them. Provenance: `FORK.md`.

Every number below is quoted unaltered from the BGR files it links to.

| Record | Location (unchanged path) | What it is |
| --- | --- | --- |
| Original v0.90.0 README | [`docs/research/bgr-v0.90.0/README.md`](bgr-v0.90.0/README.md) | Byte-identical copy (sha256 `a0a725d1…312db`) of the README that Brute's root `README.md` replaced |
| Whitepaper | [`WHITEPAPER.md`](../../WHITEPAPER.md) | Formal argument: finite-prefix support, the adequacy boundary, the predictive quotient, and the impossibility witness |
| Claim boundaries | [`docs/CLAIM_BOUNDARIES.md`](../CLAIM_BOUNDARIES.md) | What BGR does and does not claim |
| Experiment protocol | [`docs/ETR_PROTOCOL.md`](../ETR_PROTOCOL.md) | The study protocol |
| BitWatts | [`docs/BITWATTS.md`](../BITWATTS.md) | Work accounting; physical energy unmeasured |
| Directory | [`docs/DIRECTORY.md`](../DIRECTORY.md) | The original file directory |
| Next iteration (BGR's) | Root `NEXT_ITERATION.md` as of the fork (tag `bgr-v0.90.0-fork`) | BGR's own roadmap; superseded for Brute by [`BRUTE_v0.1.0_PLAN.md`](../../BRUTE_v0.1.0_PLAN.md). The root file is now Brute's current proposal |
| Frozen study plan | [`experiments/PLAN.json`](../../experiments/PLAN.json) | Seeds, masks, and gates G1–G8 |
| Study-001 results | [`results/study-001/`](../../results/study-001/) | `RESULTS.json`, `SCIENTIFIC.json`, `SEAL.json`, `INDEPENDENT_AUDIT.json` |
| Gates | [`results/GATES.json`](../../results/GATES.json) | Passed, failed, and untested gates |
| Paired analysis | [`results/PAIRED_ANALYSIS.json`](../../results/PAIRED_ANALYSIS.json) | Bootstrap of 68–88 fewer false certificates on four-state worlds. **No generator script ships with it** (plan F9) |
| Reproducibility | [`results/REPRODUCIBILITY.json`](../../results/REPRODUCIBILITY.json), [`results/REPRODUCIBILITY_PRECHECK_INVALID.json`](../../results/REPRODUCIBILITY_PRECHECK_INVALID.json) | A matched rerun, plus the preserved timing-field precheck failure (plan F10) |
| Research ledger | [`results/RESEARCH_LEDGER.jsonl`](../../results/RESEARCH_LEDGER.jsonl) | Local hash-linked receipts. These are not external signatures |
| Charts | [`assets/BGR-v0.90.0-*.png`](../../assets/) | Frozen-study charts |

**Not carried over:** `baseline/BGR-v0.89.0.zip` (71,142,325 bytes, sha256 `2ae5e464…4c1e4a2`). See `FORK.md`.

**How Brute reads this record:** BGR's in-family soundness result is real. Its out-of-family behaviour is the problem Brute v0.1.0 exists to fix. The open questions are listed in the root README under "What Brute can't do yet".

## Brute's own record (studies 002–005)

| Record | Location | What it is |
| --- | --- | --- |
| Pre-registrations | `experiments/BRUTE_PLAN_00{2,3,4,5}.json` | Criteria frozen before code for each study (v0.1.0, v0.1.1, v0.2.0, v0.3.0) |
| Sealed results | `results/study-00{2,3,4,5}/` | Traces, seals, gates, paired analyses, independent audits, reproducibility reruns |
| Deviations | [`BRUTE_DEVIATIONS_002–005.md`](BRUTE_DEVIATIONS_005.md) | Every departure from a plan, and every failed gate |
| Discoveries | [`DISCOVERIES.md`](DISCOVERIES.md) | D1–D16, each with data, math and an evidence label |
| Design probes | [`v0.2.0/design_probe/`](v0.2.0/design_probe/), [`v0.3.0/design_probe/`](v0.3.0/design_probe/) | Pre-freeze probe code on earlier sealed traces (Simulated evidence, disclosed) |
| Earlier next-iteration notes | [`v0.1.0/`](v0.1.0/NEXT_ITERATION.md), [`v0.2.0/`](v0.2.0/NEXT_ITERATION.md), [`v0.3.0/`](v0.3.0/NEXT_ITERATION.md) | The proposals each release was planned from; the current one is the root `NEXT_ITERATION.md` (v0.4.0) |
