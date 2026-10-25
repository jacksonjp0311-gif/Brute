# Brute bridge v0.2 — operator ↔ Brute intercommunication

This is a secondary track, and the mind stays the goal. The bridge talks to `brute.api/1.2` by default (`--api 1.1` keeps v0.1
behaviour) and never imports `brute.core` or `brute.active`. Pre-registered criteria are in [BRIDGE_PLAN.md](BRIDGE_PLAN.md).

```
python -m bridge                                  # interactive REPL; type `help`
python -m bridge --script bridge/examples/demo.cmds --transcript t.jsonl --flags f.jsonl
python -m bridge.audit t.jsonl                    # B1/B2/B4/B5/B6 offline audit
python -m bridge.replay t.jsonl                   # B7 byte-identical replay against the API
python -m bridge --api 1.1 ...                    # frozen 1.1 service: split/models are UNSUPPORTED
python -m unittest tests.test_bridge              # about 21 s (most of it is core cost of study-004 experiments)
```

**Grammar.** `init x=0101 y=0011 [k=4] [attest=FAMILY]`, `observe a x=1 y=-`, `predict a [x|y]`, `why`, `vs`,
`retractions`, `scope`, `split [default=a|b]`, `models [default=a|b]`, `retry k=5`. Phrase aliases such as "what do you predict for sensor y after
action b?" are recognised. REPL extras: `raw <trace_id>`, `requests`, `decline qN`, `quit`.

**Answers.** Every claim is a fixed template filled only from JSON pointers into the logged API response. Each claim
carries its trace id and one evidence label: Exact, Observed, Simulated, Inferred, Rejected or Open. An unsupported
intent gets `UNSUPPORTED`, with zero claims and zero API calls.

**Brute → operator requests.** These are derived only from logged fields:
- CONTRADICTION_NOTICE
- SCOPE_ALERT (residual, legacy, attestation)
- REQUEST_OBSERVATION
- REQUEST_ACTION, fired only by a non-tied `experiment` answer. The next observe resolves it as satisfied or
  overridden (overridden is flagged); a newer request first marks it superseded. It is never emitted under 1.1.

**Flags.** Contradictions, scope alerts, unsupported intents, declined requests and duplicate retraction entries are
written to `bridge/flags.jsonl`.

**API 1.2 (v0.2).**
- `split` calls the read-only `experiment` op. Answers quote action, per-action scores, `tied`/`tie_break` and the
  rule string verbatim, all labelled Exact.
- `models` calls it with `counts:true` and reports row counts per action. Machine identities are not exposed, so the
  bridge says so; null counts are reported as null.
- `tests/bridge_corpus_004.py` drives the first mask-0.35 case of each study-004 family through split, models,
  predict and observe. It checks B11 against the recorded arm-A trace and B10 (experiment is read-only).
