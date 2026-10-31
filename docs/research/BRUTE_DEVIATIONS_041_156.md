# Deviation #156 (study-041, v0.38.0): release-time verifier addendum

Written at release time, after the gates and #155. Nothing here changes a gate, threshold, sealed file or frozen file.
Labels: Exact, Observed, Simulated, Inferred, Rejected, Open. Times are box-local EDT (UTC-4), 2026-10-31.

1. **Frozen verifier fails on the commit order (Observed).** `scripts/verify_release_0380.py` (frozen in a649dd2) passes
   items 1 to 4 and then fails item 5: `commit order: ada2447 is not an ancestor of 18cc782`.
2. **Cause (Exact).** COMMIT_ORDER_041 lists preregistration_041 (18cc782), seedcheck_041 (ada2447), then
   build_authorization_041, whose commit field names the plan it authorizes (18cc782). In study 040 the authorization came
   before the seedcheck, so the strict pairwise chain held; in 041 the seedcheck was ledgered first (00:19:12, then the
   authorization at 00:19:23), and the strict pairwise check reads the authorization's back-reference as a reversed link.
   The ledger times and the ledger order are correct; the frozen check does not allow a back-reference. The pre-freeze
   smoke did not run the release verifier against the real COMMIT_ORDER_041.
3. **Addendum (new file).** `scripts/verify_release_0380a.py` runs the frozen items 1 to 4 unchanged (it imports them) and
   replaces item 5 with a chain check that allows exactly one kind of non-ancestor pair: a build_authorization_041 entry that
   names the preregistration commit, where that commit is an ancestor of the previous entry. Every entry must still be an
   ancestor of the source freeze, and source freeze -> seal -> HEAD is checked strictly. On this tree it passes with 1
   authorization exception (Observed).
4. **Release verify command.** RELEASE.json `verify` now names the addendum. The frozen verifier's failure is published
   here and in the README and is not patched. Lesson: the pre-freeze test must run the release verifier against the real
   commit-order file, not only the gates.
