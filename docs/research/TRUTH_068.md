# Study 068 ground truth: derivation by hand from the CPython v3.13.5 source

Written 2026-11-03 about 11:15 EST, before any Brute run on these targets, by executor-B (drafted, not reviewed by James). The tables are in `experiments/truth_068.py`. They were worked out by reading the source, not from Brute output.

Before plan 068 was written, an exploratory black-box probe ran (`/tmp/s67/probe2.py`, scratch, not committed). It fed the live decoder every byte string of length 6 or less and compared what came out after each. That probe gave only state counts: 6, 7 and 7. It gave no tables. The tables below come from the source. Before the run, `scripts/truthcheck_068.py` compares them with the live decoder (plan ground_truth.pre_run_check).

## Source files (raw.githubusercontent.com/python/cpython/v3.13.5, fetched 10:55 EST through the box)

| file | sha256 |
|---|---|
| Objects/unicodeobject.c | 3ae1c58a808d95253ae4d46787479beb69870ba55bcdc6578b329506549d83c0 |
| Objects/stringlib/codecs.h | d126faea1dcf3f3b19a256237e5e87bdaa006dbc5b26fb0b5267f9a1dcbab3b4 |
| Modules/_codecsmodule.c | 149a20c2d7aee22281ddd8756ae7eae685ae0ef21764138d41f367443182041e |
| Lib/codecs.py | 514b00fe93120b4face4508351aa9f1246ecc808c4da3e599dfee7430fe459f9 |
| Lib/encodings/utf_8.py | ba0cac060269583523ca9506473a755203037c57d466a11aa89a30a5f6756f3d |
| Lib/encodings/utf_16_le.py | 3aedaf3eb49769282daef1eaedfd4fa1c31fe5eebeff67fe2307c89dc2e2fd80 |

## Common wrapper

- `utf_8.IncrementalDecoder` and `utf_16_le.IncrementalDecoder` are `codecs.BufferedIncrementalDecoder`s (codecs.py 306-340).
- `decode(input, final=False)` decodes `self.buffer + input` with `final=False`. It keeps `data[consumed:]` as the new buffer and returns the str.
- With `final=False`, `_codecs_utf_8_decode_impl` (_codecsmodule.c 284) and `_codecs_utf_16_le_decode_impl` (326, byteorder = -1, so no BOM handling) pass a `consumed` pointer.
- So the hidden state is the undecoded buffer.
- The reading is a function of the last returned str. The Moore state is therefore (buffer, class of last output), with class none / char / fffd = codes 0 / 2 / 3.

## U3 and U4 (utf-8, `unicode_decode_utf8`, unicodeobject.c 4973; `utf8_decode`, codecs.h 23)

- A single ASCII byte takes the fast path (size 1, < 128) and returns that char.
- A byte 0x80 at the start of the data is below 0xC2, so it goes to `InvalidStart` (codecs.h 104). The replace handler (unicodeobject.c 5074) writes one U+FFFD and skips 1 byte.
- **Lead byte E1 (U3).**
  - With fewer than 2 bytes, it breaks out (ch = 0). Because `consumed` is set, the decoder stops at End and keeps the bytes.
  - With 2 bytes: if the 2nd is not a continuation byte, it goes to `InvalidContinuation1` (one U+FFFD, skip 1, then decode the 2nd byte again). E1 is neither E0 nor ED, so 80 is a valid 2nd byte; then it breaks and keeps both bytes.
  - With 3 bytes: a non-continuation 3rd byte goes to `InvalidContinuation2` (one U+FFFD, skip 2, then decode the 3rd byte again). E1 80 80 is the char U+1040.
- **Lead byte F1 (U4)** works the same way with one more continuation byte: `InvalidContinuation1/2/3` skip 1/2/3. F1 80 80 80 is U+40000.
- **U3 transitions:**

| from \ byte | 41 | 80 | E1 |
|---|---|---|---|
| buffer '' | 'A' to ('',char) | U+FFFD to ('',fffd) | '' to (E1,none) |
| buffer E1 | U+FFFD 'A' to ('',fffd) | '' to (E1 80,none) | U+FFFD to (E1,fffd) |
| buffer E1 80 | U+FFFD 'A' to ('',fffd) | U+1040 to ('',char) | U+FFFD to (E1,fffd) |

- **U4** is the same with F1, plus one more pending row (F1 80 80). In that row, 80 gives a char and 41 or F1 give U+FFFD.
- All 6 (U3) and 7 (U4) Moore states are reachable from ('',none).
- **They are pairwise distinct:**
  - States with different codes are distinct.
  - Among the code-0 states, ('',none) differs from the pending states on 41 (char vs U+FFFD).
  - (E1,none) and (E1 80,none) differ on 80 (none vs char).
  - In U4, the extra pending state (F1 80 80,none) differs from the other two on 80 (char vs none).
- So the truth's minimal sizes are 6 and 7.

## W16 (utf-16-le, `PyUnicode_DecodeUTF16Stateful`, unicodeobject.c 5843; `utf16_decode`, codecs.h 501)

- A code unit is (2nd byte << 8) | 1st byte.
- With an odd byte count, the last byte stays buffered: ch = 0 and `consumed`, so it goes to End.
- **Unit with high byte 41:** an ordinary char.
- **Unit with high byte DC:** a lone low surrogate. It goes to `IllegalEncoding` (5953): one U+FFFD over those 2 bytes.
- **Unit with high byte D8:** a high surrogate.
  - Fewer than 2 more bytes: `UnexpectedEnd`, q -= 2, End. The 2 bytes stay buffered, and so does a 3rd byte.
  - With 4 bytes, the 2nd unit is either:
    - a low surrogate (high byte DC): joined into one char;
    - not a low surrogate: `IllegalSurrogate` (5958). One U+FFFD over the first 2 bytes, then decode resumes at byte 2. A 41 unit gives a char; a D8 unit is buffered again.
- **Transitions:**
  - buffer '': any byte goes to (x,none).
  - (x): 41 to ('',char); DC to ('',fffd); D8 to (x D8,none).
  - (x D8): any byte to (x D8 z,none).
  - (x D8 z): DC to ('',char); 41 to ('',fffd), output U+FFFD plus a char; D8 to (x D8,fffd), with z D8 buffered.
- The value of a buffered low byte never changes a later reading: it only sets the low half of a unit, and surrogate tests read the high byte. So the states merge over x and z.
- All 7 states are reachable.
- **They are pairwise distinct:**
  - ('',none) vs (x): 41 gives none vs char.
  - (x) vs (x D8 z): 41 gives char vs U+FFFD.
  - (x D8) vs the others with code 0: 41 gives none vs not-none, and the next 41 gives U+FFFD.
  - ('',none) vs (x D8): the 2-step sequence 41 41 gives none,char vs none,fffd.
- So the truth's minimal size is 7.

## Caveats

- The start state ('',none) is transient: no action returns to it. An IDF record therefore never covers it (plan GMATCH68).
- The truth is for the box's CPython 3.13.5 only.
