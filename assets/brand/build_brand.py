"""Builds the Brute brand SVGs. Renders PNGs with headless Chrome + Pillow (see BRAND.md)."""
import math, pathlib
OUT = pathlib.Path(__file__).resolve().parent
CHAR, CHAR2, BONE, SAGE, SAGE_D = '#1b1e1c', '#262a27', '#eeeee6', '#b7c4b6', '#7f9483'
SERIF = "'IBM Plex Serif', 'Source Serif 4', Georgia, 'Times New Roman', serif"
MONO = "'IBM Plex Mono', 'DejaVu Sans Mono', Menlo, monospace"

def pt(r, deg, c=32.0):
    a = math.radians(deg); return round(c + r*math.cos(a), 3), round(c + r*math.sin(a), 3)

# Geometry on a 64-unit grid. Aperture ring r=21, stroke 7, flat ends.
# Withheld segment: 60 deg gap centred on -45 deg (upper right), from -75 to -15 deg.
R, W, G0, G1 = 21, 7, -75, -15
def mark(ring, core, ghost, x=0, y=0, s=1.0):
    a = pt(R, G1); b = pt(R, G0)
    ga, gb = pt(R, G0+6), pt(R, G1-6)
    return (f'<g transform="translate({x} {y}) scale({s})">'
            f'<path d="M {a[0]} {a[1]} A {R} {R} 0 1 1 {b[0]} {b[1]}" fill="none" stroke="{ring}" '
            f'stroke-width="{W}" stroke-linecap="butt"/>'
            # withheld segment drawn only as a hairline: bounded but not asserted
            f'<path d="M {ga[0]} {ga[1]} A {R} {R} 0 0 1 {gb[0]} {gb[1]}" fill="none" stroke="{ghost}" '
            f'stroke-width="0.9" stroke-dasharray="1.6 1.6"/>'
            # certified core: one exact square cell
            f'<rect x="27.5" y="27.5" width="9" height="9" fill="{core}"/></g>')

def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{title}"><title>{title}</title>{body}</svg>\n')

def write(name, text): (OUT/name).write_text(text, encoding='utf-8')

write('symbol.svg', svg(64, 64, mark(CHAR, SAGE_D, SAGE_D), 'Brute symbol'))
write('symbol-on-dark.svg', svg(64, 64,
      f'<rect width="64" height="64" rx="12" fill="{CHAR}"/>' + mark(BONE, SAGE, SAGE), 'Brute symbol'))

def wordmark(x, y, size, color):
    return (f'<text x="{x}" y="{y}" font-family="{SERIF}" font-size="{size}" font-weight="500" '
            f'letter-spacing="{size*0.28:.1f}" fill="{color}">BRUTE</text>')
lock_body = (f'<rect width="520" height="160" rx="14" fill="{CHAR}"/>' + mark(BONE, SAGE, SAGE, 28, 28, 1.6875)
             + wordmark(168, 98, 56, BONE)
             + f'<line x1="170" y1="116" x2="490" y2="116" stroke="{SAGE_D}" stroke-width="1"/>'
             + f'<text x="170" y="134" font-family="{MONO}" font-size="11" letter-spacing="2.2" fill="{SAGE}">'
               'ABSTAINS ON WHAT IT CANNOT VERIFY</text>')
write('lockup.svg', svg(520, 160, lock_body, 'Brute'))

ticks = ''.join(f'<line x1="{80+i*28}" y1="586" x2="{80+i*28}" y2="{578 if i%5 else 570}" '
                f'stroke="{SAGE_D}" stroke-width="1"/>' for i in range(41))
og = (f'<rect width="1280" height="640" fill="{CHAR}"/>'
      f'<rect x="40" y="40" width="1200" height="560" fill="none" stroke="{CHAR2}" stroke-width="2"/>'
      + mark(BONE, SAGE, SAGE, 96, 150, 5.0)
      + wordmark(500, 330, 128, BONE)
      + f'<line x1="504" y1="372" x2="1180" y2="372" stroke="{SAGE_D}" stroke-width="1.5"/>'
      + f'<text x="504" y="420" font-family="{SERIF}" font-size="32" font-style="italic" fill="{SAGE}">'
        'A reasoner that abstains on what it cannot verify.</text>'
      + f'<text x="504" y="470" font-family="{MONO}" font-size="16" letter-spacing="3" fill="{SAGE_D}">'
        'v0.1.0 · FORKED FROM BGR v0.90.0 · RESEARCH PREVIEW</text>'
      + f'<line x1="80" y1="586" x2="1200" y2="586" stroke="{SAGE_D}" stroke-width="1"/>' + ticks)
write('og-card.svg', svg(1280, 640, og, 'Brute: a reasoner that abstains on what it cannot verify'))
print('svgs written')

# Small-size variant (16-32 px, favicon): the dashed hairline is dropped because it aliases into noise.
def mark_small(ring, core):
    a = pt(R, G1); b = pt(R, G0)
    return (f'<path d="M {a[0]} {a[1]} A {R} {R} 0 1 1 {b[0]} {b[1]}" fill="none" stroke="{ring}" '
            f'stroke-width="{W+1}" stroke-linecap="butt"/><rect x="27" y="27" width="10" height="10" fill="{core}"/>')
write('symbol-on-dark-small.svg', svg(64, 64, f'<rect width="64" height="64" rx="12" fill="{CHAR}"/>' + mark_small(BONE, SAGE), 'Brute symbol'))
