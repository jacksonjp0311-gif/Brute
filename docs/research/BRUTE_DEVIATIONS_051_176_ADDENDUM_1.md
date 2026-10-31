# Deviation #176, addendum 1 (correction, written after #176 was ledgered)

Deviation #176 is ledger-hashed and stays as written. This addendum corrects one sentence in item 6.

- **Rejected as stated.** "...all five were in phase A's second round." The sealed records carry no start times (start and
  child_starts are null), so the ordering within phase A cannot be read from them. The question is Open.
- **Observed instead (sealed RESULTS).** The slowest chunk per arm on the firing records: API16S 11830007 50.7 s, 11830008
  54.3 s, 11830009 51.5 s, 11830010 49.0 s, and API16S_b 11830010 33.7 s. Three more API16S_b records came close to the 30 s guard
  without firing: 11830008 29.4 s, 11830009 28.7 s and 11830011 29.3 s. All other scale20 arms stayed at or under 8.7 s. Case walls
  ranged from 108.1 s to 352.2 s.
- **Inferred.** Chunk wall time at 20 states varies by about 10x for the same 12000-conflict chunk, so a 30 s chunk guard fires on
  load and not on the conflict count.
