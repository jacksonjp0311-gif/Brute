# BGR v0.90: Finite-Trace Model Adequacy, Symbolic Hidden-State Expansion, and Predictive-State Equivalence

**Status:** Exact conditional algorithm with independently checked experiment; not a universal model-adequacy theorem or AGI result. Prior work includes finite Moore-machine minimization and version-space reasoning. Our finite-prefix impossibility witness is an application of established identifiability limits, not a novel claim of mathematical priority.

## 1. Exact finite-family support

For a Moore machine with hidden state set \(Q\), actions \(A=\{0,1\}\), emissions \(e:Q\to\{0,1\}^2\), and deterministic transitions \(\delta:Q\times A\to Q\), the learner receives a trace \(D=(o_0,a_1,o_1,\ldots,a_T,o_T)\) with each \(o_t\in\{0,1,?\}^2\). It never receives the true state coordinates, state count, transition law or complete observations masked by the evaluator.

The v0.89 solver enumerated every complete machine up to n=3. The complete labelled n=4 class has \(4^{2\cdot 4}\cdot4^4=16{,}777{,}216\) instances with fixed initial state index but otherwise labelled hidden coordinates, making naive extension expensive.

v0.90 instead stores *partial accessible machines*. Let the discovered hidden path states be numbered \(0,\ldots,k-1\) **in order of first occurrence**. Its symbolic record consists of (i) known transition edges, (ii) allowed output sets for each introduced hidden state, (iii) current hidden coordinate and (iv) number of introduced states. An unknown edge is completed by choosing an introduced state or a fresh state \(k\) when \(k<4\); unknown emissions remain set-valued. A masked observation intersects the allowed output set without guessing missing bits.

**Support completeness proposition (conditional):** for every observation-consistent complete deterministic Moore machine with \(|Q|\le4\), there is a corresponding partial machine in the prefix version space, up to hidden-state relabeling by encounter order. Conversely every partial machine has at least one completion within the permitted class. Induction over observations establishes these facts: the initial state maps to 0; a known edge is used, and each previously unknown transition either targets a previously introduced state or introduces one fresh state; the emission constraint is intersected with the observed bits. An exhausted resource budget voids inference, **not** the proof.

Therefore the support of the next full emission is exactly the union over all consistent \(\le4\)-state completions, as long as the solver completes without hitting its work limit. It is **not** a probability distribution.

The independent reference uses a different scalar representation with sets of allowed codes and independently reconstructs each prefix's predictions from the original action/observation history. Additional n=1/2 tests compare directly against complete-machine enumeration.

## 2. Epistemic boundary: finite evidence cannot prove unrestricted adequacy

If \(H_4(D)\) is the supported machine set with bound n≤4, unanimity \(\{e(\delta(q,a)):h\in H_4(D)\}=\{y\}\) proves only the conditional statement **“all surviving n≤4 deterministic models predict y.”** It does not prove that the physical world is one of these models.

**Constructive indistinguishability:** let a finite history contain k actions and partially observed outputs. Construct k+1 distinct hidden states, one for each visited time, and a new sink state. Define the observed action edges along this chain, and choose each state's full output to agree with the visible bits. At the last state, assign the next queried action to the sink. Two complete deterministic machines differing only by assigning sink emission 00 or 11 both fit the entire history but disagree on the next emission. Thus no finite trace can universally certify the next output when the machine state-count upper bound is not independently established.

This does not prohibit an accurate prediction or a valid certificate within an externally verified finite model family. It proves why absence of observed contradiction alone is insufficient to upgrade *conditional* claims to universal claims.

The project stores **two kinds** of output: a conditional certificate within the declared finite grammar, and an externally scoped public certificate. Without a validated scope flag, all public certificates abstain. This conservative choice is deliberately **not** celebrated as a learned out-of-distribution detector: zero public errors can result from universal abstention.

## 3. Exact predictive-state quotient

For a fixed complete deterministic Moore machine, define equivalence \(p\sim q\) iff for every future action word \(w\in A^*\), the output reached from p after w equals the output reached from q. Standard partition refinement starts by grouping states with equal current output, then recursively refines by successor-block indices for both actions until stable. The stable equivalence classes are precisely the predictive states, and the accessible quotient is canonically traversed from the initial class.

An independent test enumerates every action word through length n for each state pair of n≤4 reference machines. This is sufficient to distinguish any inequivalent states in a finite n-state deterministic Moore machine; agreement with a stable partition implies agreement for all lengths. A second test permutes hidden state indices and confirms identical canonical fingerprints. **A shared present emission is not enough**: two states with the same sensor output can differ in a later action-dependent output.

This quotient is calculated on complete *reference* machines. Identifying it exactly from noisy, partially observed evidence without knowing the grammar remains unsolved.

## 4. Registered study, exact results

Study `BGR-090-OPEN-SCOPE-AND-PREDICTIVE-QUOTIENT-001` uses 7 environment families, 24 previously unused world seeds per family, three independently masked sensor rates per seed (.1,.35,.6), 44 actual actions per case, no within-case reset, and the same reference actions/observations for baseline and expanded model. The learner sees neither true hidden state nor teacher emissions hidden by the masks. Every case was independently reconstructed.

| Family | Cases | Old n≤3 conditional false claims | Expanded n≤4 conditional false claims | n≤4 contradiction at end |
| --- | ---: | ---: | ---: | ---: |
| Four in-scope families, n=2/3 | 288 | 0 | 0 | 0 |
| Previously OOD four-state | 72 | **78** | **0** | **0** |
| Five-state | 72 | 65 | **64** | 72 |
| Nonstationary four-state | 72 | 106 | **76** | 68 |
| **Total** | **504** | **249** | **140** | **140** |

On true four-state worlds the legacy solver contradicted evidence in **71/72** runs. The new n≤4 symbolic engine remained consistent in all **72/72** and issued **1,529** correct conditional unanimity certificates. Across all 504 cases, the independent reference verified **6,103** conditional certificates, including the **140** errors outside grammar, from **22,176** action observations.

The expanded public scope gate withheld **all** outward-facing certificates because the study did not furnish an external proof of the grammar. It would be dishonest to claim this demonstrates calibrated anomaly detection; withholding everything achieves zero public errors without detecting an out-of-grammar world in advance.

The n=4 symbolic solver peaked at **4,089** partial constraint rows across the whole study and had no configured 160,000-row resource exhaustion. This row count is not directly comparable to labelled full-machine enumerations as a memory/CPU speed ratio. It is evidence that the compact representation was practical on this particular cohort.

The held-out complete-machine quotient procedure was checked against an independent future-word oracle for 120 reference worlds, and 17 had a smaller minimal predictive-state count than their nominal hidden-state labels.

A posthoc unadjusted paired world-clustered bootstrap estimates old minus expanded false certificates on n=4 target worlds at **78 total**, with a 95% interval of **[68,88]** for a sample of 24 matched seed clusters (three mask rates each). It is not a confidence statement about every possible hidden environment.

## 5. Audit, reproducibility and preserved failure

- SHA-256 source lock taken **before** first use of held-out seeds. Predictions are computed before observing the actual emission; masked observations only update the candidate constraints after actions occur.
- The independent reference replays all cases, checks the exact complete support set and status after each observation and recomputes the errors against full teacher emissions, which are evaluator-only.
- A full second study run reproduced **all 504 cases and scientific summaries**, after excluding only wall-time measurements.
- A reporting defect in `experiments/run_study.no_time` failed to exclude the top-level `total_elapsed_informational`, so the initial raw `SCIENTIFIC.json` hashes disagreed. This failed byte-equality precheck and the precisely normalized comparison are both preserved. **We did not modify source, seeds, or original study after discovering the defect.**
- A separate mathematical test constructs 120 randomized finite-history counterexample pairs, illustrating that model-family validation is necessary to justify public certainty.
- Both the symbolic and independent solvers use the same underlying synthetic world generator for reference truth, so this is **independent-code internal verification, not outside laboratory replication**.

## 6. Open problems and the next discriminating test

The arbitrary-state upper bound remains a prior assumption. A support solver for n≤4 is not open-world learning, and its current response to n=5/stochastic/nonstationary counterexamples is ultimately contradiction or abstention. The numeric predictive mixture uses the old n≤3 posterior with a small smoothing contribution over n≤4 support; it is heuristic, not a normalized uniform prior over all n=4 completions or a calibrated Bayesian posterior.

The next experiment must handle an *adaptive set of model families* (deterministic, stochastic, delayed, state-dependent and multi-target) while maintaining evidence provenance; then acquire reusable predictive-state abstractions and improve held-out goal outcomes in truly differently structured environments. Strong baseline comparisons, matched computation budgets, safe refusal, and a sealed no-reset protocol remain mandatory. There is **no verified general intelligence** in this release.
