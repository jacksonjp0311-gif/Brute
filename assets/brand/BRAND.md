# Brute brand

## The symbol: *Withheld Aperture*

**Meaning.** "A reasoner that knows what it doesn't know." The mark is about precision and refusal, not ambition.

**Parts**
- **Aperture.** A bounded instrument ring: the declared hypothesis family, a finite and measured field of view.
- **Withheld segment.** A 60° gap in the upper right. This is where Brute abstains. At large sizes the gap carries a dashed hairline: the segment is *bounded but not asserted*. Brute knows where the missing part would go, and it will not draw it.
- **Certified core.** A single solid square cell at the exact centre. It stands for a discrete code that is certified only when every surviving explanation agrees.

**Construction** (64-unit grid; source: `build_brand.py`)
- Ring: centre (32, 32), radius 21, stroke 7, flat (butt) ends.
- Arc: from −15° clockwise through 300° to −75°. The gap spans −75° to −15° and is centred on −45°.
- Hairline: 0.9 units, dash 1.6/1.6, inset 6° from each gap edge. **Omitted in the small variant.**
- Core: a 9 × 9 square at (27.5, 27.5), or 10 × 10 in the small variant.
- Tile (on-dark versions): 64 × 64, corner radius 12.
- Small variant (`symbol-on-dark-small.svg`, used for 16/32 px and the favicon): stroke 8, no hairline.

**Files**

| File | Use |
| --- | --- |
| `symbol.svg` | Mark only, transparent, charcoal ring and deep-sage core, for light backgrounds |
| `symbol-on-dark.svg` | App-icon tile: charcoal field, bone ring, sage core |
| `symbol-on-dark-small.svg` | ≤ 32 px variant |
| `symbol-{16,32,64,128,256,512,1024}.png` | Renders of the tile (16/32 from the small variant) |
| `symbol-transparent-512.png` | Render of `symbol.svg` |
| `favicon.ico` | 16/32/48 |
| `lockup.svg` / `lockup.png` | Symbol + wordmark + descriptor |
| `og-card.svg` / `og-card.png` | 1280 × 640 social card |

## Palette

| Name | Hex | Role |
| --- | --- | --- |
| Charcoal | `#1b1e1c` | Field |
| Charcoal 2 | `#262a27` | Frames, rules on the field |
| Bone | `#eeeee6` | Ring, wordmark |
| Sage | `#b7c4b6` | Core, tagline |
| Deep sage | `#7f9483` | Hairlines, tick marks, meta text, core on light |

## Type

- **Wordmark:** "BRUTE" in IBM Plex Serif Medium, tracked +0.28 em, set in capitals.
- **Meta lines and descriptors:** IBM Plex Mono, tracked.
- **Tagline:** IBM Plex Serif Italic.

SVG text falls back to Georgia/serif and Menlo/monospace. Use the PNGs wherever exact rendering matters, as the README does.

## Clear space and minimum size

- **Clear space:** keep at least **0.5 × the ring diameter** (about 21 units on the 64 grid) free on every side. In the lockup, the gap between symbol and wordmark is 0.6 × the ring diameter.
- **Minimum size:** 16 px, small variant only. Below 48 px, never use the hairline variant.

## Misuse

- Don't close the gap, move it, mirror it, or fill it. The gap is the meaning.
- Don't rotate the mark, add a second gap, animate it as a spinner or loader, or put a glow, gradient, or shadow on it.
- No purple, neon, gold, or saturated hues. No emoji, robot or brain imagery, or node-and-edge "neural" motifs.
- Don't recolour the core to signal "confidence" levels. It is one exact cell.
- Don't set the wordmark in another typeface, or stretch or outline it.
- Don't use the symbol to imply capabilities the README's "What Brute can't do yet" section rules out.

## Rebuild

```bash
python3 assets/brand/build_brand.py     # writes the SVGs
assets/brand/render.sh assets/brand/og-card.svg assets/brand/og-card.png 1280 640   # headless Chrome
```

The PNG sizes were made by downscaling a 1024 px render with Pillow (LANCZOS).
