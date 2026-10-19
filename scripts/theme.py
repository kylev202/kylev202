"""Shared look for every generated SVG: palette, type, and the terminal-window chrome.

Every card on the profile is drawn through `window()` / `panel()` so borders, radii,
title bars and colours stay identical. Text is laid out on an exact monospace grid
(one x position per glyph), so alignment holds whatever monospace font the viewer has.
"""

from xml.sax.saxutils import escape

MONO = "ui-monospace, 'Cascadia Mono', 'SF Mono', Menlo, Consolas, 'DejaVu Sans Mono', 'Liberation Mono', monospace"

BG = "#0D1117"  # card body (= GitHub dark canvas)
BAR = "#161B22"  # title bars, tiles
BORDER = "#30363D"
HI = "#F0F6FC"  # headings, numbers
TEXT = "#C9D1D9"  # body copy
MUTED = "#8B949E"  # labels
DIM = "#484F58"  # rules, punctuation
FAINT = "#21262D"  # grid lines

W = 880  # every full-width asset shares this width so they scale in lockstep
BAR_H = 34
RADIUS = 8
USER = "kyle@github"


def gray(b):
    """0..1 → a neutral grey between near-black and white."""
    v = round(40 + max(0.0, min(1.0, b)) * 215)
    return f"#{v:02X}{v:02X}{v:02X}"


def glyph_text(glyphs, y, size, fill, extra=""):
    """glyphs: [(x_centre, ch)] → one <text> with a position per character."""
    xs = " ".join(f"{x:.1f}".rstrip("0").rstrip(".") for x, _ in glyphs)
    chars = escape("".join(ch for _, ch in glyphs))
    return f'<text text-anchor="middle" x="{xs}" y="{y:g}" font-size="{size}" fill="{fill}"{extra}>{chars}</text>'


def line(x, y, runs, size, cw=None):
    """Lay out one monospace line starting at x.

    runs: [(text, fill)] or [(text, fill, bold)]. Returns (svg, end_x).
    """
    cw = cw or size * 0.6
    out, col = [], 0
    for run in runs:
        text, fill = run[0], run[1]
        bold = len(run) > 2 and run[2]
        glyphs = [(x + (col + i) * cw + cw / 2, ch) for i, ch in enumerate(text) if ch != " "]
        if glyphs:
            out.append(glyph_text(glyphs, y, size, fill, ' font-weight="700"' if bold else ""))
        col += len(text)
    return "".join(out), x + col * cw


def text_width(text, size):
    return len(text) * size * 0.6


def prompt(cmd=""):
    """Runs for `kyle@github:~$ cmd`."""
    runs = [(USER, HI, True), (":", MUTED), ("~", TEXT), ("$ ", MUTED)]
    return runs + ([(cmd, TEXT)] if cmd else [])


def pill(x, y, label, size=12):
    """A bordered tag like [ rust ]; y is the text baseline. Returns (svg, width)."""
    w = text_width(label, size) + 18
    svg, _ = line(x + 9, y, [(label, TEXT)], size)
    return f'<rect x="{x:g}" y="{y - size - 3:g}" width="{w:g}" height="{size + 10}" rx="4" fill="{BAR}" stroke="{BORDER}"/>' + svg, w


def _svg(w, h, label, css, inner):
    return (
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
        f'role="img" aria-label="{escape(label)}" font-family="{MONO}">\n'
        f"<style>text{{white-space:pre}}{css}</style>\n{inner}\n</svg>\n"
    )


def panel(w, h, body, css="", label=""):
    """A bordered card without a title bar."""
    inner = (
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{RADIUS}" fill="{BG}" stroke="{BORDER}"/>\n' + body
    )
    return _svg(w, h, label, css, inner)


def window(w, h, title, body, css="", label=""):
    """A terminal window: rounded card, title bar with three grey dots, centred title."""
    dots = "".join(
        f'<circle cx="{20 + i * 20}" cy="{BAR_H / 2 + 1}" r="6" fill="{c}"/>' for i, c in enumerate((HI, MUTED, DIM))
    )
    inner = (
        f'<clipPath id="win"><rect width="{w}" height="{h}" rx="{RADIUS}"/></clipPath>\n'
        f'<g clip-path="url(#win)"><rect width="{w}" height="{h}" fill="{BG}"/>'
        f'<rect width="{w}" height="{BAR_H}" fill="{BAR}"/></g>\n'
        f'<line x1="0" x2="{w}" y1="{BAR_H + .5}" y2="{BAR_H + .5}" stroke="{BORDER}"/>\n'
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{RADIUS}" fill="none" stroke="{BORDER}"/>\n'
        f"{dots}\n"
        f'<text x="{w / 2}" y="{BAR_H / 2 + 5}" text-anchor="middle" font-size="13" fill="{MUTED}">{escape(title)}</text>\n'
        + body
    )
    return _svg(w, h, label or title, css, inner)


# shared animation snippets
FADE_IN = "@keyframes in{from{opacity:0}to{opacity:1}}.a{animation:in .12s ease-out both}"
BLINK = "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}.cur{animation:blink 1.1s step-end infinite}"
