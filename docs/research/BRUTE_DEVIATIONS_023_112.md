# Study-023 deviation #112: the frozen clean-clone check (GCC) fails, and a git-clone rescoring is added

## What failed (Exact)

`scripts/clean_clone_023.py` is frozen in the scoring freeze. It builds its tree with `git archive`, which drops `.git`.
Run at e881b6b, it gave these results (`results/study-023/CLEAN_CLONE_023.json`):

| Step | Exit code |
|---|---|
| restore | 0 |
| make_paired_023 --check | 0 |
| make_reproducibility_023 --check | 0 |
| make_gates_023 --check | **1** |

**Why make_gates_023 failed.**
- GLR_lemma clause `lemma_committed_before_rgl4_code` reads git history. It looks for the lemma commit (e50967d) and the
  first `brute/lrregion.py` commit (9e0ca70).
- With no `.git`, both lookups return None, so the clause is False.
- The archive-tree GATES therefore differs from the committed GATES_023.json in GLR_lemma only. We compared every key:
  every other gate value is identical.
- The dry-run smoke check did not catch this, because it ran inside the repository, where `.git` exists.

**GCC is FAIL.** It is published and not re-scored. The frozen script is unchanged.

## Supplementary evidence (Observed, ungated)

A new file, `scripts/clean_clone_023_gitclone.py`, runs the same four steps inside a `git clone --no-local` at the
commit, where `.git` is present. Its output is `results/study-023/CLEAN_CLONE_023_GITCLONE.json`.

This does not turn GCC into a pass. It shows only that the GATES bytes reproduce from tracked inputs once git history is
available.

## Fix for v0.21.0

Any gate clause that reads git history must take its commits from a tracked file written before the freeze. Plan item
P-021-4 does this.
