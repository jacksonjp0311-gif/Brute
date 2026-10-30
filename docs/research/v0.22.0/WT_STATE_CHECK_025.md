# /tmp/wt-state check before the v0.22.0 build

- **Checked:** `ls -ld /tmp/wt-state` on the box before any v0.22.0 build work: "No such file or directory". *Observed.*
- **Should it exist? No.** It is operator scratch, not a study input. It was lost in the 2026-10-28 ~12:19 EDT box
  restart during study-020 and has not existed since: deviation #105 addenda (`BRUTE_DEVIATIONS_020_ADDENDUM_2.md`
  item 6, `_ADDENDUM_3.md` item 6; committed `6d8f1fd`, 2026-10-28 12:37 EDT) and HANDOFF V0180 ("Lost in the
  restart: /tmp scratch incl. /tmp/wt-state (not deleted by the operator)"). *Exact* (tracked documents).
- **v0.21.0 cleanup:** removed only explicit scratch paths under `/tmp/s24`; none was `/tmp/wt-state`. *Exact* (command in the
  v0.21.0 session).
- **Action:** none. It is not recreated (no content to restore) and the standing rule "never delete /tmp/wt-state"
  stays in force should it reappear.
