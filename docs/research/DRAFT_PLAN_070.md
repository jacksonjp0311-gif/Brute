# DRAFT plan 070 (v0.66.0): UNLOCKED, not pre-registered

Drafted 2026-11-03 EST by Grok Bot (agent). James has not reviewed it. Nothing in this file is locked: the locked plan will be `experiments/BRUTE_PLAN_070.json`, and only once James picks an option. The user's computer was offline; network access went through the box.

## Where v0.65.0 left things

- With resets (a fresh decoder per word), certify/32r certified all 5 real CPython decoders: 31/31 ID, 0 WRONG, 14/14 gates. Resets make the problem easier.
- **Reset-free certification is still Open.** In v0.64.0, certify/32p without resets decided 0/18.
- The guarantee depends on the declared N. An under-declared N can give a wrong ID.

## Options (pick one)

**A. Reset-free certification through a homing sequence (recommended).** A minimal machine has a homing sequence h, and the readings seen while applying h determine the state the machine ends in. Learn and certify the way Rivest-Schapire does: replace each reset by h, plus a state-identification step.
- Arm H: the same 5 targets without resets, declared N as in v0.65.0. Controls: certify/32r with resets (the v0.65.0 numbers) and certify/32p (v0.64.0).
- Risk: h must be learned or certified under the same N bound. The suite is longer, roughly |h| times the queries.
- Gates: sound, 0 WRONG; H decides at least 3 of 5 targets.
- Honest framing: still N-conditional; still not the SAT engine.

**B. Larger real targets with resets.** Examples: the full UTF-8 decoder over a coarse byte-class alphabet of about 6-8 classes, or the `html.parser` / `email.feedparser` tokenizer states.
- Risk: the suite grows as |Σ|^(N-n+1). Cap the declared slack at 1-2.

**C. Real noise.** Replace the injected flips with a real noisy channel, such as decoding over a lossy pipe or with timing-dependent reads.
- Risk: the noise may not be iid, which breaks the C20S assumption. Needs a pre-registered independence check.

## Process (as for v0.65.0)

LEAN. Hand truth committed before build_authorization. One run, capped at about 60 min. Official tests only after every test file is final. A fresh-clone verify, then a fast-forward of main. Run git and gh as `env -u GITHUB_TOKEN -u GH_TOKEN`.
