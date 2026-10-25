"""Bridge v0.1: an operator <-> Brute query channel. Secondary track; not the reasoner.

Import-light on purpose: `bridge.claims`, `bridge.templates`, `bridge.triggers` and `bridge.audit`
use the standard library only, so a transcript can be audited without importing brute.
`bridge.session.Bridge` is the live channel over brute.api/1.1.
"""
BRIDGE_VERSION='bridge/0.1'
LABELS=('Exact','Observed','Simulated','Inferred','Rejected','Open')
