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
