# Brute bridge v0.1 — operator ↔ Brute intercommunication

This is a secondary track, and the mind stays the goal. The bridge only reads `brute.api/1.1` and never imports
`brute.core`. Pre-registered criteria are in [BRIDGE_PLAN.md](BRIDGE_PLAN.md).

```
python -m bridge                                  # interactive REPL; type `help`
python -m bridge --script bridge/examples/demo.cmds --transcript t.jsonl --flags f.jsonl
python -m bridge.audit t.jsonl                    # B1/B2/B4/B5/B6 offline audit
python -m bridge.replay t.jsonl                   # B7 byte-identical replay against the API
python -m unittest tests.test_bridge              # about 3 s
```

**Grammar.** `init x=0101 y=0011 [k=4] [attest=FAMILY]`, `observe a x=1 y=-`, `predict a [x|y]`, `why`, `vs`,
`retractions`, `scope`, `split`, `models`, `retry k=5`. Phrase aliases such as "what do you predict for sensor y after
action b?" are recognised. REPL extras: `raw <trace_id>`, `requests`, `decline qN`, `quit`.

**Answers.** Every claim is a fixed template filled only from JSON pointers into the logged API response. Each claim
carries its trace id and one evidence label: Exact, Observed, Simulated, Inferred, Rejected or Open. An unsupported
intent gets `UNSUPPORTED`, with zero claims and zero API calls.

**Brute → operator requests.** These are derived only from logged fields:
- CONTRADICTION_NOTICE
- SCOPE_ALERT (residual, legacy, attestation)
- REQUEST_OBSERVATION
- REQUEST_ACTION, which needs an `experiment` field. It is never emitted under 1.1.

**Flags.** Contradictions, scope alerts, unsupported intents, declined requests and duplicate retraction entries are
written to `bridge/flags.jsonl`.

**Plugging into v0.2.0.** When a response carries `experiment: {action, score, ...}`, the bridge will emit
REQUEST_ACTION and answer `split`. To use it:
1. Point `Bridge(service=...)` at the new service class.
2. Add any new fields as templates in `templates.py`.
