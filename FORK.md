# Brute — fork provenance

Brute is a fork of **BGR (Bitwork Geometric Reasoning) v0.90.0**. This first commit is the unmodified v0.90.0 source; the only addition is this file. No fixes are implemented here.

| Field | Value |
| --- | --- |
| Source path (box) | `/workspace/bgr/BGR-v0.90.0` (extracted from `/workspace/bgr/BGR-v0.90.0.zip`) |
| Source path (James's PC) | `C:\Users\jacks\OneDrive\Desktop\BGR-v0.90.0` |
| BGR version | 0.90.0 (`RELEASE.json`) |
| Original `MANIFEST.sha256` sha256 | `ec2ac44f8aee9d739f51f5e895886b05c4aa4dab100de7c0468c8b302da3a548` |
| Original manifest check | 105/105 listed files matched before forking |
| Fork date | 2026-10-24 (America/New_York) |
| Files copied | 105 of the original 106 files on disk (plus this FORK.md). Every copied file is byte-identical to the original |

## Excluded from the fork

| Path | Bytes | sha256 | Reason |
| --- | ---: | --- | --- |
| `baseline/BGR-v0.89.0.zip` | 71142325 | `2ae5e464c94e6b870c704ea518509f6db4030343fe5d971888a365d647c1e4a2` | Nested archive chain: it holds v0.89, which holds v0.88, and so on back to v0.11, with the v0.47 branch duplicated. It is 66% of the 107.5 MB release. It is still available unchanged at `/workspace/bgr/BGR-v0.90.0/baseline/BGR-v0.89.0.zip` and matches `baseline/IDENTITY.json`. From here on, history lives in git |
| `__pycache__/`, `venv`, scratch copies | — | — | Build artifacts. They are not part of the release |

## Known consequence of the exclusion

- `python -m unittest discover -s tests`: **69 tests, OK** in the fork (2.8 s, Python 3.13.5, NumPy 2.5.4).
- `python -m scripts.verify_release` **fails in the fork** with `FileNotFoundError: baseline/BGR-v0.89.0.zip`. `verify()` asserts the baseline zip hash, and `MANIFEST.sha256` still lists that file. This is expected. It gets fixed in Brute v0.1.0 (see `BRUTE_v0.1.0_PLAN.md`, fix H1).
