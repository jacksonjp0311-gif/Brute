# Roadmap toward general geometric reasoning

Brute is a sound, certificate-issuing learner for small hidden-state worlds. "General intelligence" is the
direction, not a claim: every step below must keep the property Brute is built on, **0 false certificates on
held-out data**. A version that trades soundness for reach fails. Evidence labels: Exact / Observed / Simulated /
Inferred / Rejected / Open. Everything below is **Open** until a pre-registered held-out study scores it.

The gaps between Brute and a mind-like reasoner, as of v0.10.0 (Inferred):

1. **No concepts.** Each world is learned from nothing. There is nothing reusable inside it.
2. **No transfer.** Structure seen in one world cannot speed up the next one. v0.10.0 runs the first test of this.
3. **Tiny scale.** The worlds have up to 8 states, 2 actions and 4 codes. Coverage at 7–8 states is near 0.
4. **Clean, synthetic data only.** Worlds are deterministic, observations are exactly masked bits, and nothing is noisy or real.

## v0.10.0: transfer, first test (this study)

Brute learns whole-machine **motifs** from one fully observed source world, then uses them on a held-out target
as a filter over relabelled copies. TR certifies only when SP8's published support agrees.

| Gate | Requirement |
|---|---|
| GT_a | 0 false transfer certificates |
| GT_b | Fewer steps to the first certificate than from scratch, mean ≥ 1 step, seed-paired 95% CI > 0 |
| GT_c | An unrelated-family source gives 0 false certificates and no significant help |

## v0.11.0: concept formation (sub-machine motifs)

- **Goal:** extract *parts* rather than whole machines. Examples are cycles, toggles, absorbing states and
  emission-class patterns. A part is kept only if it recurs across at least 2 source worlds. Each part is stated
  as a checkable clause over the region, so it is a sound restriction when it applies and is dropped when the
  evidence refutes it.
- **Gates:**
  1. 0 false certificates.
  2. The concept library found from family A sources compresses held-out family A worlds: the description
     length of the minimal consistent machine relative to the library falls, with a paired CI > 0.
  3. A held-out *composite* family, built from two part types never seen together, certifies faster than from
     scratch (CI > 0).
  4. A negative control as in GT_c.

## v0.12.0: transfer with applicability tests

- **Goal:** choose *which* motif or concept to apply from a library of several families, with no oracle family
  label. Applicability is decided by the target evidence alone, through elimination plus a stated likelihood
  margin. Wrong picks must cost steps, never soundness.
- **Gates:**
  1. 0 false certificates over a mixed held-out pool.
  2. The speed-up stays positive (CI > 0) when the library holds 4 or more families.
  3. Wrong-family selection rate ≤ 5%, with every wrong selection retracted before any false certificate.
  4. The negative control holds with the full library.

## v0.13.0: scale

- **Goal:** worlds with 16–32 states, 3 or more actions and 8 or more codes. Exact SAT regions stay the
  certificate source, with incremental solving and symmetry breaking, and concepts as region restrictions.
- **Gates:**
  1. 0 false certificates.
  2. Coverage ≥ 0.10 at n = 16 within 64 steps, with the concept library.
  3. Median query time ≤ 1 s per step on the 8-CPU box.
  4. The study fits the 2 h cap.

## v0.14.0: noisy and real data

- **Goal:** observation noise at a known rate ε, then a real sequential dataset, such as a logged device
  protocol or a puzzle-game trace. Certificates become **(1 − δ) certificates**, with δ pre-registered and
  checked by held-out frequency.
- **Gates:**
  1. Observed false-certificate rate ≤ δ, with a Clopper–Pearson upper bound ≤ 2δ.
  2. Coverage ≥ 0.5 × the clean-data coverage at ε = 0.01.
  3. On the real dataset, the predictions beat an n-gram baseline in log-loss, with a seed or segment-paired CI.

## What stays fixed

The following rules apply at every step:

- Pre-registration before any code.
- Held-out seeds.
- An enforced 2 h cap.
- A second implementation.
- An append-only ledger.
- No force-push.
- Failed gates are published as failed.
