# Deviation #114: ledger note times for four post-run entries ran ahead of the clock (v0.20.0)

Label: **Exact**. The ledger and git agree on everything below.

- **What happened.**
  - The ISO times in the notes of four ledger entries were typed by hand. They were not read from the clock, and each
    is later than the real commit:

    | Ledger entry | Note time | Git commit time |
    |---|---|---|
    | `release_tooling_0200` | 22:38:00 | 22:23:14 |
    | `release_0200` | 22:46:00 | 22:25:40 |
    | `docs_0200` | 22:46:30 | 22:25:43 |
    | `deviation_023_113` | 22:58:00 | 22:33:16 |
    | `docs_0200_r1` | 22:58:30 | 22:33:20 |

  - All times are EDT on 2026-10-28.
  - The `docs_0200` and `docs_0200_r1` entries name the ledger commits `3132030` and `0d169c8`. Those commits hold the
    same HANDOFF.md bytes as `fc7e082` and `ca5b925` respectively.
- **Effect.**
  - No gate or verifier input changes. The only ledger times a gate reads are scoring_freeze_023 → run_start_023 (the
    10-minute rule), and both were set before the run.
  - The ledger is append-only, so those lines stay as written. Git committer times are the authoritative record for
    these entries.
- **Fix from now on.** Ledger note times come from `date -Iseconds`.
