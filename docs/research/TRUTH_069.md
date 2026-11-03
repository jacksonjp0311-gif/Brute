# Study 069 ground truth: derivation by hand from the CPython v3.13.5 source

Written 2026-11-03 at about 11:40 EST by Grok Bot (s69). Drafted, not reviewed by James. It was written before any run of brute.certify/32r and before build_authorization_069. The tables are in `experiments/truth_069.py`.

- U3, U4 and W16 are imported unchanged from `experiments/truth_068.py`; their derivation is in TRUTH_068.md.
- EJ and GB were worked out by reading the source below. The only black-box input was the state counts 13 and 8 from the v0.64.0 exploratory probe, which gave no tables.

## Source files (raw.githubusercontent.com/python/cpython/v3.13.5, fetched 11:30 EST through the box)

| file | sha256 |
|---|---|
| Modules/cjkcodecs/multibytecodec.c | 3fb630daaeddd658740c14fa4343bf1f946ff7299afcee7efd1d9bb0e5bf91c2 |
| Modules/cjkcodecs/cjkcodecs.h | c73cb514b08f1f0bb3be5ed675c538a8dbdb39eab5a1842849623e1331c5a323 |
| Modules/cjkcodecs/_codecs_jp.c | e41484049adac46605165e00d5ea22b7ff9eac76519331913526f228b3112696 |
| Modules/cjkcodecs/_codecs_cn.c | 8b28def11821d71acb90ef3e74d7d6d597246daf4c196415107d19ebeeb73e55 |
| Modules/cjkcodecs/mappings_jp.h | 09012ff9eb963073d42a8bce375c05484219537caa0cc2aa74baa63d5f3f1658 |
| Modules/cjkcodecs/mappings_cn.h | 5c75da57e7fcbb06106a64b03a7fc1f6e76fd9668306c66f71a6485e8eb550aa |
| Lib/encodings/euc_jp.py | b453a439787b0efa031e43416a7d852a6be705c985e1200693eb96d87ea79cdc |
| Lib/encodings/gb18030.py | 6c10b4dc49bc63724e539137ede6936304fcca1c97c28d16d89f381e10849521 |

## Common wrapper (multibytecodec.c)

- The `MultibyteIncrementalDecoder.decode` implementation is at line 1159. It decodes `pending + input`.
- `decoder_feed_buffer` (line 897) loops over the codec's `decode`:
  - It stops on 0 or `MBERR_TOOFEW`. `REQUIRE_INBUF(n)` returns TOOFEW when fewer than n bytes are left (cjkcodecs.h 137).
  - Any positive return e goes to `multibytecodec_decerror`, which writes U+FFFD under `replace` and skips e bytes.
- With `final=False`, leftover bytes go to `pending` through `decoder_append_pending`.
- So the hidden state is the pending buffer. A Moore state is (pending, class of last output), with classes none / char / fffd = codes 0 / 2 / 3.
- A fresh decoder object is the start state ('', none).

## EJ: euc_jp, bytes 41 / 8F / A1 (DECODER(euc_jp), _codecs_jp.c 382)

- **41 (< 0x80):** outputs 'A' and consumes 1 byte.
- **8F:** `REQUIRE_INBUF(3)`, then `TRYMAP_DEC(jisx0212, c2^0x80, c3^0x80)`.
  - c2 can be 41, 8F or A1, so the row is 0xC1, 0x0F or 0x21. All three `jisx0212_decmap` rows are `{0,0,0}` (mappings_jp.h 1060), so the map is NULL.
  - So any 3 bytes starting with 8F give `return 1`: one U+FFFD, skip the 8F, and decode the 2nd byte again.
- **A1:** `REQUIRE_INBUF(2)`. There is a special case for A1 C0, which these bytes never reach.
  - Then `TRYMAP_DEC(jisx0208, 0x21, c2^0x80)`. Row 0x21 is `__jisx0208_decmap+0`, bottom 33, top 126 (mappings_jp.h 534).
  - c2 = A1 gives column 0x21, which is mapped (U+3000), so 2 bytes are consumed.
  - c2 = 41 or 8F gives column 0xC1 (> 126) or 0x0F (< 33): `return 1`, so one U+FFFD and skip 1.
- **Pending buffers reachable:** '', 8F, A1, 8F 41, 8F 8F, 8F A1.
- **Transitions:**

| pending \ byte | 41 | 8F | A1 |
|---|---|---|---|
| '' | 'A' to ('',char) | '' to (8F,none) | '' to (A1,none) |
| 8F | '' to (8F 41,none) | '' to (8F 8F,none) | '' to (8F A1,none) |
| A1 | FFFD 'A' to ('',fffd) | FFFD to (8F,fffd) | U+3000 to ('',char) |
| 8F 41 | FFFD 'A' 'A' to ('',fffd) | FFFD 'A' to (8F,fffd) | FFFD 'A' to (A1,fffd) |
| 8F 8F | FFFD to (8F 41,fffd) | FFFD to (8F 8F,fffd) | FFFD to (8F A1,fffd) |
| 8F A1 | FFFD FFFD 'A' to ('',fffd) | FFFD FFFD to (8F,fffd) | FFFD U+3000 to ('',fffd) |

- **Count:** 13 Moore states: 3 with pending '', plus 5 non-empty pendings x 2 output classes (none, fffd). Pending A1 never follows an output of class char, and ('',none) is the start only.
- **Distinguishability:** every pair of pendings is apart within 2 bytes, and the output class separates the rest. This is checked by `scripts/truthcheck_069.py`.

## GB: gb18030, bytes 41 / 81 / 30 (DECODER(gb18030), _codecs_cn.c 265)

- **41 and 30 (< 0x80):** each outputs one char.
- **81:** `REQUIRE_INBUF(2)`.
  - **c2 = 30 (in 30..39):** `REQUIRE_INBUF(4)`. The sequence is valid only if c3 is in 81..FE and c4 is in 30..39, so only 81 30 81 30, which gives lseq 0 and outputs U+0080 (first BMP range). Anything else is `return 1`: FFFD, skip 1.
  - **c2 = 41 or 81:** goes to `GBK_DECODE`. `gb2312_decmap` row 0x01 is NULL, but `gbkext_decmap` row 0x81 is `__gbkext_decmap+0`, 64..254, with 0x8141 to 19972 and 0x8181 to 20118 (not UNIINV). That is a char, and 2 bytes are consumed.
- **Pending buffers reachable:** '', 81, 81 30, 81 30 41, 81 30 30, 81 30 81.
  - 81 30 41 and 81 30 30 behave identically: the next byte makes the 4-byte sequence invalid, then '0' and x are both one char, and then y is decoded from ''. So they merge into one state, (81 30 x, none).
- **Transitions:**

| pending \ byte | 41 | 81 | 30 |
|---|---|---|---|
| '' | char to ('',char) | to (81,none) | char to ('',char) |
| 81 | GBK char to ('',char) | GBK char to ('',char) | to (81 30,none) |
| 81 30 | to (81 30 x,none) | to (81 30 81,none) | to (81 30 x,none) |
| 81 30 x | FFFD '0' x 'A' to ('',fffd) | FFFD '0' x to (81,fffd) | FFFD '0' x '0' to ('',fffd) |
| 81 30 81 | FFFD '0' GBK to ('',fffd) | FFFD '0' GBK to ('',fffd) | U+0080 to ('',char) |

- **Count:** 8 Moore states: ('',none), ('',char), ('',fffd), (81,none), (81,fffd), (81 30,none), (81 30 x,none), (81 30 81,none).
