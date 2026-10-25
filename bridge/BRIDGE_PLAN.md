# Bridge v0.1: operator ↔ Brute intercommunication (pre-registration)

Committed **before any bridge code**. This is a secondary track. It is not the reasoner. It must not change
`brute/` or anything the v0.2.0 study depends on. It may only touch `bridge/`, `adapters/`, `tests/test_bridge_*`
and this document.

Labels: **Exact** (read straight from an API field) · **Observed** (a conjunction of recorded fields, with no
causal claim) · **Simulated** (comes from a scripted demo world, not a study) · **Inferred** (Brute's own uncertain
forecast, such as probabilities) · **Rejected** (a certificate Brute withdrew) · **Open** (the API has no field, so
there is no answer).

## What it is

- `python -m bridge` opens a REPL. `python -m bridge --script FILE` replays a command file.
- Every operator question maps to a fixed **intent**, and every intent maps to real `brute.api/1.1` calls
  (`BruteServiceV011.handle`).
- Every answer is a list of **claims** `{text, template, field_refs, trace_id, label}`:
  - `text` must equal the template filled from `field_refs`;
  - `field_refs` are JSON pointers into the raw request or response stored under `trace_id`.
- Unsupported questions get `UNSUPPORTED` with **zero claims**.
- **Two-way.** After each call, Brute can emit structured **requests** to the operator: `SCOPE_ALERT`,
  `CONTRADICTION_NOTICE`, `REQUEST_OBSERVATION` and `REQUEST_ACTION`. Each one has a trigger that is a pure function of
  cited fields, and it is rendered with the same claim machinery. Requests are never free-form.
- **Logs:**
  - the session transcript goes to JSONL (each command, its raw requests and responses, the answer and any requests);
  - notable events go to a `flags` JSONL channel (default `bridge/flags.jsonl`, gitignored at runtime).

## Intents (v0.1)

| intent | API call | answers from |
|---|---|---|
| init / observe | initialize / observe | status, evidence_count, refusal_text |
| predict `a` [channel] | predict | status, certificate, support (+ channel projection), probabilities, forecast_source |
| why | (none; cites the last predict trace) | status, reason, refusal_text, margin.states/support_size, surviving_rows |
| version_space | snapshot | surviving_rows, family_scope, evidence_count, saturated |
| retractions | snapshot | retractions[i].step/previous_value/reason |
| scope | snapshot | family_scope, margin.states, attestation_id, legacy_family_alive, residual.* |
| split (best action) | — | **UNSUPPORTED** under 1.1 (no field); answered only if a response carries an `experiment` field (v0.2.0 hook) |
| models (which models disagree) | — | **UNSUPPORTED** (the API exposes counts, not identities) |
| anything else | — | **UNSUPPORTED** |

`predict` is a real call. If the answer is CERTIFIED, the service records the certificate as issued, so a later
contradiction can retract it (Exact, `service_v011._predict`). The bridge says so in `help`.

## Brute → operator requests (triggers fixed here)

- `CONTRADICTION_NOTICE`: the response reason is `FAMILY_CONTRADICTED` and no earlier response in the session had
  it. Cites the status, the reason and the count of retractions.
- `SCOPE_ALERT`: the status is `OUT_OF_FAMILY` with reason `RESIDUAL_SURPRISE`, or `evidence.legacy_family_alive`
  goes from true to false, or `evidence.attestation_id` goes from non-null to null. Fires once per kind.
- `REQUEST_OBSERVATION`: the last observe request had at least one null channel **and** the next predict response is
  not CERTIFIED. It cites both fields and claims nothing causal (Observed).
- `REQUEST_ACTION`: only when a response carries a v0.2.0 `experiment` field. Under API 1.1 this field does not
  exist, so the expected count is **0** (Exact).
- **Flags.** Every CONTRADICTION_NOTICE and SCOPE_ALERT is flagged. So is every request the operator declines
  (`decline <id>`), and every UNSUPPORTED intent, which is tracked as an API gap.

## Acceptance criteria (frozen)

- **B1 Grounding.** 100% of rendered claims, in answers and in requests, have refs that resolve to non-null values in
  the cited trace, and `text == fill(template, refs)`. Measured on a corpus: study-002 replays (one case per family,
  mask 0.35) with every intent asked at every step, plus edge sessions. Pass means 0 violations.
- **B2 Unsupported.** 100% of unsupported intents (`split` under 1.1, `models`, unknown and free text) return
  `UNSUPPORTED` with exactly 0 claims and 0 API calls.
- **B3 Boundary (AST).**
  - `bridge/` imports only stdlib, `brute.api`/`brute.api.*`, `adapters.language*` and relative modules. It never
    imports `brute.core`, `brute.fallback`, `bgr*`, `experiments`, `scripts` or numpy.
  - Nothing in `brute/`, `bgr*`, `experiments/` or `scripts/` imports `bridge`.
  - File I/O happens only in `bridge/log.py`.
- **B4 Refusal passthrough.** Whenever a cited response has `refusal_text`, the answer contains it verbatim.
- **B5 No status upgrade.** No claim names a single reading (`x=?, y=?`) unless the cited response is CERTIFIED or the
  claim lists a support set or retraction.
- **B6 Request audit.** Recomputing triggers offline from the transcript reproduces the same requests exactly.
  `REQUEST_ACTION` count is 0 under 1.1.
- **B7 Offline audit and determinism.**
  - `bridge.audit` checks a transcript using stdlib only. It does not import brute.
  - Replaying a transcript's API requests on a fresh service gives byte-identical responses.
- **B8 Small and fast.** The bridge test suite runs in under 30 s. A single query is under 50 ms median.
- **B9 Core untouched.** `git diff main -- brute/ bgr*/ experiments/ results/` is empty on `bridge/v0.1`.

Failures are reported, not tuned away. Any change to a criterion goes in a dated deviation note below this line.

---

### Deviation note 2026-10-24 (implementation; the criteria B1–B9 are unchanged)

- **D1. `retry` in the corpus.** It is asked in one short edge session, not at the end of every study-002 replay.
  Under brute.api/1.1, `retry k=5` replays all evidence and costs about 3.5 s per call in Brute's core (profiled with
  cProfile: `bgr90/symbolic._update`). That cost is the reasoner's, not the bridge's.
- **D2. A claim's `trace_id`.** It is the trace that triggered the claim. Cross-trace refs, such as "it was true at
  trace t…", are allowed because each ref names its own trace. The checker also requires `trace_id` to be one of the
  cited traces.
- **D3. New flag `duplicate_retraction_entries`.** It fires when one response lists the same (step, value)
  retraction twice. It was found in the demo: two CERTIFIED `predict` calls at the same step each record an issuance.
  This is Observed API behaviour. The core was not changed.
- **D4. The attestation edge session uses an attested alternating world** (Simulated), because the study-002 drift4
  case at mask 0.35 never certifies within 44 steps.

---

# Bridge v0.2 addendum: brute.api/1.2 (pre-registered 2026-10-24, before any v0.2 code)

B1–B9 stay in force unchanged. In B9, "main" now means v0.2.0 (31a348e). One exception: the merge-readiness
`MANIFEST.sha256` regeneration (B14), which touches no file under `brute/ bgr*/ experiments/ results/`.

## Service
- The default service is `brute.api.service_v020.BruteServiceV020` (brute.api/1.2).
- `--api 1.1` keeps the frozen 1.1 service. The v0.1 behaviour, including UNSUPPORTED for split and models, must
  hold there unchanged.

## New or changed intents
- **`split [default=a|b]`**
  - Calls the read-only `experiment` op once, with `default_action` set to the stated default (`a` if omitted)
    and `counts:false`.
  - Answers only from `/response/experiment/*`. The rule string is quoted verbatim. The score's meaning is not
    glossed.
- **`models`** ("which models disagree")
  - Calls `experiment` with `counts:true`.
  - Answers with per-action counts from `per_action[i].counts`: rows admitting each reading, open rows, family
    rows and margin rows.
  - A fixed note says identities are not exposed.
  - If `counts` is null, a claim says so.
  - If the API has no `per_action`, the answer is UNSUPPORTED, as in v0.1.
- **New templates** (all Exact, because they restate API values):
  - experiment (action, score, rule)
  - experiment.score (per action)
  - experiment.tied (tied, tie_break)
  - counts.code
  - counts.rows
  - counts.margin
  - counts.none

## Requests (changed or new)
- **REQUEST_ACTION** fires on a response whose `experiment` object has `tied == false`, once per such response.
  A tie means Brute expresses no preference, because the action is just the operator's default; so a tie yields no
  request. Its claim cites `/response/experiment/action`, `/response/experiment/score` and `/response/experiment/tied`.
- **Resolution.** The next successful `observe` closes a pending REQUEST_ACTION.
  - If the observe uses the requested action, it is logged as satisfied in that turn's `resolved` list.
  - Otherwise it is logged as overridden, and a `request_action_overridden` flag cites both traces.
  - Resolutions are recomputed in the B6 audit.

## New criteria
- **B10 Read-only experiment.** Run each study-004-style session twice, once with and once without the `experiment`
  calls. Every response to a non-experiment request must be byte-identical between the two runs, ignoring
  `request_id`.
- **B11 Agreement with study-004.**
  - Corpus: 7 cases, the first case per family at mask 0.35 in `results/study-004/SCIENTIFIC.json.gz`, arm A.
  - At every step, the bridge's `split` (default = the recorded passive action) must return the recorded
    `action`, `scores` and `tied`.
  - The predict on the chosen action must return the recorded status and reason.
  - A mismatch is reported as a flag and in the report, never silently fixed.
- **B12 Request audit under 1.2.** The REQUEST_ACTION count must equal the number of non-tied experiment responses.
  The offline recompute must reproduce the requests and resolutions exactly. The 1.1 corpus must still give 0.
- **B13 Boundary.** The bridge may import `brute.api.service_v020`, alongside `service_v011` and `brute.api`.
  It never imports `brute.active`, `brute.core`, `brute.fallback` or `bgr*`. The B3 AST test is extended.
- **B14 Merge readiness.**
  - Regenerate `MANIFEST.sha256` with `scripts/make_manifest.py`, so that `test_manifest_matches_tracked_files`
    passes.
  - The full suite must have no failure that main 31a348e does not also have. The baseline is measured and
    recorded.
- **B8 restated.** The bridge suite must still run in under 30 s. The median wall time per `ask` must be under 50 ms,
  measured over the study-004 cycle3 session. `experiment` latency is reported separately, as core cost.
