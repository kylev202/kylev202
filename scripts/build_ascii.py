"""Generate the ASCII-art SVGs used in README.md.

    python scripts/build_ascii.py

Writes assets/banner.svg (ASCII dunes + title) and assets/astronaut.svg (floating
ASCII astronaut). Every glyph sits on an explicit character grid (per-character x
positions), so the art stays aligned whatever monospace font the viewer has.
"""

import math
import random
from pathlib import Path
from xml.sax.saxutils import escape

ASSETS = Path(__file__).resolve().parent.parent / "assets"
MONO = "ui-monospace, 'Cascadia Mono', 'SF Mono', Menlo, Consolas, 'DejaVu Sans Mono', 'Liberation Mono', monospace"
BG = "#0D1117"  # GitHub dark canvas, so the art blends in


def gray(b):
    v = round(40 + b * 215)
    return f"#{v:02X}{v:02X}{v:02X}"


def text_row(glyphs, y, size, fill, extra=""):
    """glyphs: [(x_center, ch)] — one <text> with per-character x positions."""
    xs = " ".join(f"{x:g}" for x, _ in glyphs)
    chars = escape("".join(ch for _, ch in glyphs))
    return f'<text x="{xs}" y="{y:g}" font-size="{size}" fill="{fill}"{extra}>{chars}</text>'


def svg(w, h, label, css, body, rx=6):
    return (
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
        f'role="img" aria-label="{escape(label)}">\n'
        f"<style>text{{font-family:{MONO};text-anchor:middle;white-space:pre}}{css}</style>\n"
        f'<clipPath id="c"><rect width="{w}" height="{h}" rx="{rx}"/></clipPath>\n'
        f'<g clip-path="url(#c)"><rect width="{w}" height="{h}" fill="{BG}"/>\n{body}\n</g>\n</svg>\n'
    )


def smooth(e0, e1, x):
    t = min(max((x - e0) / (e1 - e0), 0.0), 1.0)
    return t * t * (3 - 2 * t)


# ── banner: ASCII desert dunes with a winding river ──────────────────────────

W, H = 880, 280
CW, LH, FS = 5.4, 9.0, 9
COLS, ROWS = int((W - 4) // CW), int(H // LH)
RAMP = " .`',:;-~=+*o#%&@"  # dark → bright
TONES = 9  # fill colours are quantised so each row needs only a handful of <text> runs
HORIZON = 0.42  # as a fraction of banner height


def make_dunes():
    """Layers far → near; each is (base y, [(peak x, half-width, height)…])."""
    rng = random.Random(11)
    layers = []
    for base, w in [(0.03, 0.07), (0.10, 0.11), (0.20, 0.16), (0.34, 0.24), (0.52, 0.34)]:
        peaks, x = [], -rng.uniform(0, w)
        while x < 1 + w:
            peaks.append((x, w * rng.uniform(0.8, 1.2), w * rng.uniform(0.35, 0.6)))
            x += w * rng.uniform(1.1, 1.7)
        layers.append((HORIZON + base, peaks))
    return layers


DUNES = make_dunes()


def crest(layer, x):
    """Top edge of a dune layer at x, plus the peak that forms it."""
    base, peaks = DUNES[layer]
    best, top = None, base
    for px, w, h in peaks:
        u = (x - px) / (w * (1.25 if x < px else 0.7))  # gentle windward side, steep slip face
        y = base - h * max(0.0, 1 - abs(u)) ** 1.4
        if y < top:
            best, top = (px, w, h), y
    return top, best


def river(y):
    """River centre x and half-width at height y (perspective: meanders tighten far away)."""
    t = (y - HORIZON) / (1 - HORIZON)
    x = 0.5 + (0.02 + 0.16 * t) * math.sin(1.4 / (t + 0.12) + 0.3)
    return x, 0.002 + 0.045 * t**1.4


def brightness(x, y):
    if y < HORIZON:  # sky glowing toward the horizon
        return 0.03 + 0.40 * math.exp(-(HORIZON - y) * 9)

    t = (y - HORIZON) / (1 - HORIZON)
    if y > HORIZON + 0.015:
        rx, half = river(y)
        d = abs(x - rx)
        if d < half:
            return 0.80 + 0.2 * (1 - d / half)
        if d < half + 0.006 + 0.01 * t:
            return 0.12  # dark bank

    layer = max((k for k in range(len(DUNES)) if y >= crest(k, x)[0]), default=None)
    if layer is None:
        return 0.30
    top, peak = crest(layer, x)
    depth = y - top
    lit = peak is None or x < peak[0]
    if lit:
        b = max(0.28, 0.72 - 2.2 * depth)
        if depth < 0.012:
            b = 0.92
    else:
        b = 0.10 + 0.06 * math.exp(-depth / 0.04)
        if depth < 0.010:
            b = 0.55
    haze = 1 - layer / (len(DUNES) - 1)
    return b + (0.32 - b) * 0.55 * haze


def banner():
    rng = random.Random(7)
    rows, stars = [], []
    for r in range(ROWS):
        y_n = (r + 0.5) / ROWS
        by_tone = {}
        for c in range(COLS):
            x_px = 2 + c * CW + CW / 2
            b = (brightness(x_px / W, (r + 0.3) / ROWS) + brightness(x_px / W, (r + 0.7) / ROWS)) / 2
            # carve a soft clearing in the sky for the title
            e = ((x_px / W - 0.5) / 0.30) ** 2 + ((y_n - 0.24) / 0.15) ** 2
            b *= smooth(0.5, 1.2, e)
            if y_n < HORIZON - 0.08 and e > 1.2 and rng.random() < 0.018:
                stars.append((x_px, (r + 0.8) * LH, rng.choice("*+.")))
                continue
            ch = RAMP[min(int(b * len(RAMP)), len(RAMP) - 1)]
            if ch == " ":
                continue
            tone = min(int(b * TONES), TONES - 1)
            by_tone.setdefault(tone, []).append((x_px, ch))
        for tone, glyphs in sorted(by_tone.items()):
            rows.append(text_row(glyphs, (r + 0.8) * LH, FS, gray((tone + 0.5) / TONES)))

    for n, (x, y, ch) in enumerate(stars):
        rows.append(text_row([(x, ch)], y, FS, "#E6EDF3", f' class="tw t{n % 4}"'))

    title_y = H * 0.22
    rows.append(f'<text x="{W / 2}" y="{title_y:g}" font-size="26" fill="#F0F6FC">Welcome to Kyle\'s GitHub</text>')
    rows.append(f'<text x="{W / 2}" y="{title_y + 32:g}" font-size="20" fill="#C9D1D9">&lt;/&gt;<tspan class="cur">_</tspan></text>')

    css = (
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}.cur{animation:blink 1.1s step-end infinite}"
        "@keyframes tw{0%,100%{opacity:.35}50%{opacity:1}}.tw{animation:tw 3.2s ease-in-out infinite}"
        ".t1{animation-delay:.8s}.t2{animation-delay:1.6s}.t3{animation-delay:2.4s}"
    )
    return svg(W, H, "Welcome to Kyle's GitHub — ASCII desert dunes with a winding river", css, "\n".join(rows))


# ── astronaut: floating in an ASCII starfield ────────────────────────────────

ASTRONAUT = [
    r"        _..._        ",
    r"      .'     '.      ",
    r"     /  .---.  \     ",
    r"    |  /#####\  |    ",
    r"    |  |#####|  |    ",
    r"    |  \#####/  |    ",
    r"     \  '---'  /     ",
    r"   .--'-.___.-'--.   ",
    r"  /  |  [===]  |  \  ",
    r" /  /|  [o o]  |\  \ ",
    r"(__/ |  [___]  | \__)",
    r"     |---------|     ",
    r"     |    |    |     ",
    r"     |    |    |     ",
    r"    (____)(____)     ",
]


def astronaut():
    s = 260
    cw, lh, fs = 7.2, 13.0, 12
    rng = random.Random(42)
    body = []

    for n in range(46):  # starfield
        x, y = rng.uniform(6, s - 6), rng.uniform(10, s - 4)
        ch = rng.choice("....··+*")
        cls = f' class="tw t{n % 4}"' if ch in "+*" else ""
        body.append(text_row([(round(x, 1), ch)], round(y, 1), 10, "#8B949E", cls))

    w = len(ASTRONAUT[0]) * cw
    x0, y0 = (s - w) / 2, (s - len(ASTRONAUT) * lh) / 2
    art = []
    for r, line in enumerate(ASTRONAUT):
        tones = {}
        for c, ch in enumerate(line):
            if ch != " ":
                tones.setdefault("#6E7681" if ch == "#" else "#F0F6FC", []).append((x0 + c * cw + cw / 2, ch))
        for fill, glyphs in tones.items():
            art.append(text_row(glyphs, y0 + (r + 0.8) * lh, fs, fill))
    body.append(f'<g class="float">{"".join(art)}</g>')

    css = (
        "@keyframes float{0%,100%{transform:translate(0,-6px) rotate(-6deg)}50%{transform:translate(0,6px) rotate(5deg)}}"
        f".float{{transform-origin:{s / 2}px {s / 2}px;animation:float 7s ease-in-out infinite}}"
        "@keyframes tw{0%,100%{opacity:.3}50%{opacity:1}}.tw{animation:tw 3s ease-in-out infinite}"
        ".t1{animation-delay:.75s}.t2{animation-delay:1.5s}.t3{animation-delay:2.25s}"
    )
    return svg(s, s, "An ASCII astronaut floating among the stars", css, "\n".join(body))


def main():
    (ASSETS / "banner.svg").write_text(banner(), encoding="utf-8")
    (ASSETS / "astronaut.svg").write_text(astronaut(), encoding="utf-8")
    print("wrote assets/banner.svg, assets/astronaut.svg")


if __name__ == "__main__":
    main()
