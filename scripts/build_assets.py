"""Generate the ASCII-art SVGs used in README.md.

    python scripts/build_ascii.py

Writes assets/terminal.svg (a neofetch-style terminal with an ASCII planet and the
profile info) and assets/astronaut.svg (floating ASCII astronaut). Every glyph sits on an explicit character grid (per-character x
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


# ── terminal: a neofetch-style window with an ASCII planet ───────────────────

USER = "kyle@github"
INFO = [  # (key, value) — the right-hand column of the neofetch output
    ("OS", "Full-Stack Engineer"),
    ("Host", "github.com/kylev202"),
    ("Kernel", "TypeScript · Rust · Python · JavaScript"),
    ("Frontend", "React · Vite · Tauri"),
    ("Backend", "FastAPI · SQLite"),
    ("Tooling", "Git · GitHub Actions · VS Code"),
    ("Project", "Arbora — local-first study assistant"),
    ("Focus", "on-device RAG · local-first sync · FSRS"),
    ("Values", "local-first · privacy-first"),
    ("Web", "kylev202.github.io/2026Portfolio"),
    ("LinkedIn", "linkedin.com/in/duykhiemvu"),
    ("Email", "kylevu858@gmail.com"),
]
PLANET_RAMP = " .,-:~^/[uo8NM"  # dark → bright, in the spirit of classic neofetch logos


def planet_art(cols, rows, cw, lh):
    """Ray-cast a lit sphere with a tilted ring; returns rows of brightness (0..1)."""
    R = 86.0
    r_in, r_out = 1.35 * R, 2.1 * R
    tilt, spin = math.radians(72), math.radians(-28)  # ring plane: tipped toward us, turned up-right
    n = (math.sin(tilt) * math.sin(spin), -math.sin(tilt) * math.cos(spin), math.cos(tilt))
    light = (-0.55, -0.5, 0.67)  # ~unit vector, from the upper left
    grid = []
    for r in range(rows):
        line = []
        for c in range(cols):
            vals = []
            for sx, sy in ((0.3, 0.3), (0.7, 0.3), (0.3, 0.7), (0.7, 0.7)):  # 4x supersampling
                x = (c + sx - cols / 2) * cw
                y = (r + sy - rows / 2) * lh
                zs = math.sqrt(R * R - x * x - y * y) if x * x + y * y < R * R else None
                zr = -(n[0] * x + n[1] * y) / n[2]
                d = math.sqrt(x * x + y * y + zr * zr)
                ring = None
                if r_in < d < r_out:
                    t = (d - r_in) / (r_out - r_in)
                    if not 0.55 < t < 0.63:  # the gap in the ring
                        ring = 0.5 + 0.25 * math.sin(t * 19) ** 2 - 0.2 * t
                if ring is not None and (zs is None or zr > zs):
                    vals.append(ring)
                elif zs is not None:
                    lam = max(0.0, (x * light[0] + y * light[1] + zs * light[2]) / R)
                    vals.append(0.04 + 0.96 * lam**1.5)
                else:
                    vals.append(0.0)
            line.append(sum(vals) / len(vals))
        grid.append(line)
    return grid


def terminal():
    w, h = 880, 430
    bar = 34
    fs, lh = 14, 21.0
    p_cw, p_lh, p_fs = 7.0, 12.5, 11.6
    body = []

    # window chrome
    body.append(f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="8" fill="none" stroke="#30363D"/>')
    body.append(f'<rect x="1" y="1" width="{w - 2}" height="{bar}" rx="7" fill="#161B22"/>')
    body.append(f'<rect x="1" y="{bar - 6}" width="{w - 2}" height="7" fill="#161B22"/>')
    body.append(f'<line x1="1" x2="{w - 1}" y1="{bar + 1}" y2="{bar + 1}" stroke="#30363D"/>')
    for i, fill in enumerate(("#F0F6FC", "#8B949E", "#484F58")):
        body.append(f'<circle cx="{20 + i * 20}" cy="{bar / 2 + 1}" r="6" fill="{fill}"/>')
    body.append(f'<text x="{w / 2}" y="{bar / 2 + 5}" font-size="13" fill="#8B949E">{USER}: ~</text>')

    def prompt(y):
        return (
            f'<text class="s" x="24" y="{y:g}" font-size="{fs}">'
            f'<tspan fill="#F0F6FC" font-weight="700">{USER}</tspan><tspan fill="#8B949E">:</tspan>'
            f'<tspan fill="#C9D1D9">~</tspan><tspan fill="#8B949E">$ </tspan></text>'
        )

    # $ neofetch — typed one character at a time
    y = bar + 30
    body.append(prompt(y))
    x0 = 24 + (len(USER) + 4) * fs * 0.6  # after "user:~$ "
    for i, ch in enumerate("neofetch"):
        body.append(
            f'<text class="s a" style="animation-delay:{0.35 + i * 0.07:.2f}s" x="{x0 + i * fs * 0.6:g}" '
            f'y="{y:g}" font-size="{fs}" fill="#F0F6FC">{ch}</text>'
        )
    out_t = 1.15

    # the planet logo
    grid = [line for line in planet_art(52, 30, p_cw, p_lh) if max(line) * len(PLANET_RAMP) >= 1]  # drop blank rows
    ix, iy = 400, y + 30
    info_mid = iy - 14 + (len(INFO) + 3) * lh / 2
    py0 = info_mid - len(grid) * p_lh / 2
    art = []
    for r, line in enumerate(grid):
        tones = {}
        for c, b in enumerate(line):
            ch = PLANET_RAMP[min(int(b * len(PLANET_RAMP)), len(PLANET_RAMP) - 1)]
            if ch != " ":
                tones.setdefault(min(int(b * 6), 5), []).append((24 + c * p_cw + p_cw / 2, ch))
        for tone, glyphs in sorted(tones.items()):
            art.append(text_row(glyphs, py0 + (r + 0.8) * p_lh, p_fs, gray(0.25 + 0.75 * (tone + 0.5) / 6)))
    body.append(f'<g class="a" style="animation-delay:{out_t}s">{"".join(art)}</g>')

    # the info column
    lines = [
        f'<tspan fill="#F0F6FC" font-weight="700">{USER}</tspan>',
        f'<tspan fill="#484F58">{"-" * len(USER)}</tspan>',
    ]
    lines += [
        f'<tspan fill="#F0F6FC" font-weight="700">{escape(k)}</tspan><tspan fill="#8B949E">: </tspan>'
        f'<tspan fill="#C9D1D9">{escape(v)}</tspan>'
        for k, v in INFO
    ]
    for i, l in enumerate(lines):
        body.append(
            f'<text class="s a" style="animation-delay:{out_t + 0.08 * i:.2f}s" x="{ix}" '
            f'y="{iy + i * lh:g}" font-size="{fs}">{l}</text>'
        )
    # palette blocks, as neofetch prints them — in grayscale
    sy = iy + len(lines) * lh + 2
    blocks = "".join(
        f'<rect x="{ix + i * 28}" y="{sy - 14:g}" width="28" height="18" fill="{gray(i / 7)}"/>' for i in range(8)
    )
    body.append(f'<g class="a" style="animation-delay:{out_t + 0.08 * len(lines):.2f}s">{blocks}</g>')

    # fresh prompt with a blinking cursor
    end_t = out_t + 0.08 * (len(lines) + 2)
    fy = h - 24
    body.append(
        f'<g class="a" style="animation-delay:{end_t:.2f}s">{prompt(fy)}'
        f'<rect class="cur" x="{x0:g}" y="{fy - 13}" width="{fs * 0.6:g}" height="17" fill="#F0F6FC"/></g>'
    )

    css = (
        ".s{text-anchor:start}"
        "@keyframes in{from{opacity:0}to{opacity:1}}.a{animation:in .12s ease-out both}"
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}.cur{animation:blink 1.1s step-end infinite}"
    )
    label = f"Terminal running neofetch for {USER}: " + "; ".join(f"{k}: {v}" for k, v in INFO)
    return svg(w, h, label, css, "\n".join(body), rx=8)


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
    (ASSETS / "terminal.svg").write_text(terminal(), encoding="utf-8")
    (ASSETS / "astronaut.svg").write_text(astronaut(), encoding="utf-8")
    print("wrote assets/terminal.svg, assets/astronaut.svg")


if __name__ == "__main__":
    main()
