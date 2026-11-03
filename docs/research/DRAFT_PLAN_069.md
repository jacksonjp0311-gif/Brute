# DRAFT plan 069 (v0.65.0): UNLOCKED, needs a judgment call

Status: **draft, not locked, not pre-registered.** It is written as a Markdown draft, not as BRUTE_PLAN_069.json, so nothing in it binds a run. Drafted by Grok Bot on 2026-11-03 EST after v0.64.0.

## Why v0.64.0 failed (Inferred, deviation #208)

- Brute ran without resets.
- The real decoders are sparse, so many 12-state rivals agree with every experiment on the visited path.
- K 400 never refuted them all (AMB), and on U3 the 8M conflict budget ran out first (IDU).
- The least machine was right every time. What was missing was distinguishing power, not soundness.

## Target (proposed)

A larger stdlib state machine, driven through its public interface only. Pre-plan probe counts (Observed, black-box, not Brute):

| Codec | Bytes | Moore states |
|---|---|---|
| euc_jp | 41/8F/A1 | 13 |
| gb18030 | 41/81/30 | 8 |

Proposal: euc_jp is the main target. gb18030 and the v0.64.0 U3 are held out. As in v0.64.0, the ground truth is written by hand from the CPython source (Modules/cjkcodecs) before the build.

## The judgment call (James): pick one

- **A. Resets (recommended).** Each experiment starts from a fresh `codecs.getincrementaldecoder(...)()` object.
  - This is still the public interface.
  - It turns the problem into reset-based identification, where distinguishing is far easier.
  - It needs a small new certify entry that accepts reset experiments. That is new API, in a new file.
- **B. Smaller declared N** (e.g. N 8 on gb18030).
  - No new API.
  - The guarantee shrinks with N, and it cannot reach euc_jp at 13 states.
- **C. Larger K / B** (e.g. K 2000, B 32M) with no resets.
  - No new API.
  - The v0.64.0 diagnosis suggests this still ends AMB.

## Arms, if A is chosen

- C: noise-free.
- S: iid 30% injected noise with SPRT re-reads.
- 3 seeds each.
- Declared N 16.
- Held-out targets as above.

## Gates (same shape as plan 068)

- sound (0 WRONG against the hand truth);
- decided;
- GEQ;
- determinism;
- fidelity (public interface only);
- ghost;
- process;
- honest match on all reachable states.

## Honest framing

A 13-state decoder is still a small real target. Resets would make the problem easier, and the release must say so.
