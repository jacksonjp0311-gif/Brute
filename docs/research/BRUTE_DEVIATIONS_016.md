# Study-016 (v0.14.0) deviations and disclosures

Numbering continues project-wide. Study-015 ended at #74. Evidence labels: Exact / Observed / Simulated / Inferred /
Rejected / Open. Every entry below was written before the source freeze and before any held-out seed of
BRUTE_PLAN_016 was generated. Each has a `deviation_016` ledger entry.

**#75 (clarification): RSXL "no certificate before t" means RG4's certificate for the taken action.**
transfer_definition says RSXL acts with the SP8 choice "while RG4 has issued no certificate at any step < t". RG4 issues
a certificate per action per step, so the phrase has two readings: (a) no certificate for either action; (b) no
certificate for the action actually taken (RG4's first_cert_step, the speedup metric). The implementation and the
reference use (b): the action at step t is the SP8 choice when t <= f (f = RG4's first taken-action certificate step on
this trajectory) and the study-015 RSX choice afterwards. Only (b) makes the plan's own claim that S(RSXL4) == S(RG4)
hold by construction: under (b) the RSXL trajectory equals the SP8 trajectory through step f, so RG4 certifies first at
the same step on both. Under (a) a certificate on the untaken action could switch the rule before f and change the
evidence before RG4's first taken-action certificate. Both experiments/v0140_reference.py (committed first, ac717c4,
ledger 6f6f829) and brute/deferredsplit.py use (b), and the runner asserts the online switch step equals the replayed
RSXL4 first_cert_step + 1 on every case. Effect on gates: GDS clause S(RSXL4) == S(RG4) becomes an Exact consequence
of the rule, checked per case. Label: Exact (tests/test_study_016, smoke reference audits (True, None)).

**#76: g11 reference stream at 4 workers (rate math, before the source freeze).** stop_rule registers g11 at 2
workers / 2,400 s and says rate math is "as study-015", which allows one budget / worker change before the freeze for a
mandatory stream projected above 70% of its budget. RATE_MATH_016 (docs/research/v0.14.0/RATE_MATH_016.md) projects g11
at 2 workers above that line. g11 runs with 4 workers; the budget stays 2,400 s. scripts/run_study_016.py carries
G11_WORKERS = 4 from its first commit (no edit of a ledgered file). The worker ceiling holds: 4 (transfer) + 2 (gti) at
t0, then 2 (gti) + 2 (repro) + 4 (g11) = 8. Effect on gates: G_RT checks the unchanged budgets; no science changes.
This is the same change study-015 made as #72. Label: Exact (tests/test_scripts_016 expects g11 (4, 2400,
['transfer']); the smoke dry run shows g11 starting with 4 workers).

**#77 (disclosure): API signatures.** api_definition writes suggest_action(deferred=True) and
suggest4(observations, actions, certified_before). As with certify/3 (#68), SP8's LU-R choice needs the host's default
(passive) action as a tie-break, so the implementation is suggest_action(default_action=0, deferred=True) and
suggest4(observations, actions, certified_before=None, default_action=0). certified_before=None derives the flag from
the history; a bool overrides it. The returned dict also carries 'bounded_sizes' and 'step' (as certify/3). With the
optional arguments omitted the plan's calls work unchanged. Label: Exact (tests/test_api_certify4_0140 (ii) reproduces
every RSXL action and deferred flag on two smoke-api cases).

**#78 (disclosure): plan text typo.** stop_rule.cap says RUN_T0 is "written with the run_start_015 ledger entry". The
study-016 run writes RUN_T0 with the run_start_016 entry. No other reading is possible. Label: Exact.

**#79 (disclosure): DLF2 is built from a new class.** The frozen brute.boundedtransfer.BoundedTransfer accepts license
margin 0 or 1 only, so DLF2 (margin 2) runs through brute.deferredsplit.MarginTransfer: the frozen dlf_decide and
TransferTracker with the license region at min(n_L + margin, 4). Margin 1 is the frozen DLF decision. Label: Exact
(code); the margin-1 equality with the frozen class is checked by the reference audit of DLFp / DLFn vs RSXLp / RSXLn
through the same ref_dlf, not by a separate test.
