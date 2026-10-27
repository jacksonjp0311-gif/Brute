# BRUTE_DEVIATIONS_013 addendum (post-release)

_`docs/research/BRUTE_DEVIATIONS_013.md` is hashed by the ledger, so it stays byte-identical to release `d8b449d`. Post-release notes go here._
## Addendum (post-release, 2026-10-26 ~22:50 EDT): #56 resolved

The push outage recorded as #56 (~10:56 EDT, "Invalid username or token", stale `GITHUB_TOKEN`) is resolved. git now uses the gh credential helper with `GITHUB_TOKEN`/`GH_TOKEN` unset. The 22 local commits went to `origin/plan/v0.11.0` as a plain fast-forward (7dc04c8..d8b449d). No force-push, no history rewrite, no MCP push_files. The release commit `d8b449d` was verified on a fresh GitHub clone before the tag. This addendum is appended after the tag and changes no criterion or result.

Erratum: this addendum was first appended to the ledger-hashed file in `fb76a27`, which made `verify_release_0110` fail on main ("ledger source changed"). The next commit restored that file byte-for-byte to its `d8b449d` content and moved the text here. Disclosed as deviation #58 in study-014. *Exact.*
