"""Generate every static SVG on the profile.

    python scripts/build_assets.py

All profile copy lives in the PROFILE section just below — edit it there and re-run.
The look (palette, type, window chrome) comes from scripts/theme.py, shared with
scripts/profile_stats.py, so the static cards and the live stats stay in sync.

Writes to assets/:
  terminal.svg            neofetch-style intro with an ASCII planet
  link-*.svg              terminal-style link buttons
  section-*.svg           numbered section headers (`01  kyle@github:~$ whoami`)
  about.svg               about card with an animated braille-dot cat
  project-*.svg           featured project cards
  stack.svg               the tech stack as a `tree` listing
  footer.svg              `exit` / logout sign-off
"""

import math
import textwrap
from pathlib import Path

from theme import (
    BAR, BAR_H, BLINK, BORDER, DIM, FADE_IN, FAINT, HI, MUTED, TEXT, USER, W,
    glyph_text, gray, line, panel, pill, prompt, text_width, window,
)

ASSETS = Path(__file__).resolve().parent.parent / "assets"

# ── PROFILE ──────────────────────────────────────────────────────────────────

INFO = [  # neofetch column in the intro terminal
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

LINKS = ["portfolio", "linkedin", "email", "arbora", "repos"]  # README wires up the hrefs

SECTIONS = [  # (slug, command, label)
    ("about", "whoami", "about"),
    ("projects", "ls ~/projects", "featured work"),
    ("stack", "tree ~/stack", "tech stack"),
    ("stats", "./stats --last-year", "activity"),
]

ABOUT = {
    "name": "Kyle Vu",
    "tagline": "full-stack engineer · local-first · privacy-first",
    "bio": (
        "I build practical, well-crafted software — tools that make learning and everyday "
        "work easier. I care about local-first architecture, thoughtful UX, and getting the "
        "details right."
    ),
    "list": [
        ("now", "growing Arbora, a study assistant that never phones home"),
        ("next", "exploring on-device RAG and local-first sync"),
        ("into", "spaced repetition (FSRS), desktop apps with Tauri"),
        ("ask me", "about Tauri, FSRS, or study tooling"),
    ],
}

PROJECTS = [
    {
        "slug": "arbora",
        "name": "Arbora",
        "tagline": "a study assistant that never phones home",
        "desc": (
            "Turns documents and lectures into grounded, cited notes, flashcards, and quizzes, "
            "then schedules review with FSRS spaced repetition. Everything stays on your device."
        ),
        "tags": ["tauri", "rust", "react", "fastapi", "sqlite"],
        "url": "github.com/kylev202/Arbora",
    },
    {
        "slug": "portfolio",
        "name": "2026Portfolio",
        "tagline": "selected work, in one place",
        "desc": (
            "Projects, background, and ways to get in touch — served as a static site on "
            "GitHub Pages."
        ),
        "tags": ["typescript", "github pages"],
        "url": "kylev202.github.io/2026Portfolio",
    },
]

STACK = [
    ("languages", ["TypeScript", "JavaScript", "Rust", "Python"]),
    ("frontend", ["React", "Vite", "Tauri"]),
    ("backend", ["FastAPI", "SQLite"]),
    ("tooling", ["Git", "GitHub Actions", "VS Code"]),
]
PRINCIPLES = ["local-first by default", "privacy is a feature", "sweat the details"]


# ── intro terminal ───────────────────────────────────────────────────────────

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
        row = []
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
            row.append(sum(vals) / len(vals))
        grid.append(row)
    return grid


def delayed(svg, t):
    return f'<g class="a" style="animation-delay:{t:.2f}s">{svg}</g>'


def terminal():
    h, fs, lh = 430, 14, 21.0
    p_cw, p_lh, p_fs = 7.0, 12.5, 11.6
    body = []

    # $ neofetch — typed one character at a time
    y = BAR_H + 30
    svg, x0 = line(24, y, prompt(), fs)
    body.append(svg)
    for i, ch in enumerate("neofetch"):
        body.append(delayed(line(x0 + i * fs * 0.6, y, [(ch, HI)], fs)[0], 0.35 + i * 0.07))
    out_t = 1.15

    # the planet logo, vertically centred on the info column
    grid = [row for row in planet_art(52, 30, p_cw, p_lh) if max(row) * len(PLANET_RAMP) >= 1]
    ix, iy = 400, y + 30
    py0 = iy - 14 + (len(INFO) + 3) * lh / 2 - len(grid) * p_lh / 2
    art = []
    for r, row in enumerate(grid):
        tones = {}
        for c, b in enumerate(row):
            ch = PLANET_RAMP[min(int(b * len(PLANET_RAMP)), len(PLANET_RAMP) - 1)]
            if ch != " ":
                tones.setdefault(min(int(b * 6), 5), []).append((24 + c * p_cw + p_cw / 2, ch))
        for tone, glyphs in sorted(tones.items()):
            art.append(glyph_text(glyphs, py0 + (r + 0.8) * p_lh, p_fs, gray(0.25 + 0.75 * (tone + 0.5) / 6)))
    body.append(delayed("".join(art), out_t))

    # the info column
    rows = [[(USER, HI, True)], [("-" * len(USER), DIM)]]
    rows += [[(k, HI, True), (": ", MUTED), (v, TEXT)] for k, v in INFO]
    for i, runs in enumerate(rows):
        body.append(delayed(line(ix, iy + i * lh, runs, fs)[0], out_t + 0.08 * i))
    sy = iy + len(rows) * lh + 2  # palette blocks, as neofetch prints them — in greyscale
    blocks = "".join(f'<rect x="{ix + i * 28}" y="{sy - 14:g}" width="28" height="18" fill="{gray(i / 7)}"/>' for i in range(8))
    body.append(delayed(blocks, out_t + 0.08 * len(rows)))

    # fresh prompt with a blinking cursor
    fy = h - 24
    svg, cx = line(24, fy, prompt(), fs)
    cursor = f'<rect class="cur" x="{cx:g}" y="{fy - 13}" width="{fs * 0.6:g}" height="17" fill="{HI}"/>'
    body.append(delayed(svg + cursor, out_t + 0.08 * (len(rows) + 2)))

    label = f"Terminal running neofetch for {USER}: " + "; ".join(f"{k}: {v}" for k, v in INFO)
    return window(W, h, f"{USER}: ~", "\n".join(body), FADE_IN + BLINK, label)


# ── link buttons ─────────────────────────────────────────────────────────────

def link_button(name):
    w, h, fs = 160, 40, 13
    label = f"./{name}"
    x = (w - text_width(label + " ↗", fs)) / 2
    svg, _ = line(x, 25, [("./", DIM), (name, TEXT), (" ↗", MUTED)], fs)
    return panel(w, h, svg, label=name)


# ── section headers ──────────────────────────────────────────────────────────

def section_header(index, cmd, label):
    h, fs = 52, 14
    num, end_x = line(24, 32, [(f"{index:02d}", MUTED, True), ("  ", DIM)] + prompt(cmd), fs)
    tag = label.upper()
    spacing = fs * 0.6 * 1.35  # letter-spaced label
    tag_x = W - 24 - len(tag) * spacing
    tag_svg = glyph_text([(tag_x + i * spacing + spacing / 2, ch) for i, ch in enumerate(tag) if ch != " "], 32, 12, MUTED)
    rule = f'<line x1="{end_x + 16:g}" x2="{tag_x - 16:g}" y1="27.5" y2="27.5" stroke="{DIM}" stroke-dasharray="2 5"/>'
    return panel(W, h, num + rule + tag_svg, label=f"{index:02d} — {label}")


# ── about card ───────────────────────────────────────────────────────────────

# Braille-dot cat for the about card. Shapes are outlined in a 736×736 design space,
# then sampled onto a braille grid (2×4 dots per cell) and drawn as round dots.
CAT = {
    "head": [(205, 212), (515, 212), (515, 420), (492, 442), (230, 442), (205, 420)],
    "ear_l": [(206, 222), (214, 150), (238, 106), (268, 86), (296, 98), (322, 148), (348, 222)],
    "ear_r": [(398, 222), (424, 148), (446, 100), (470, 86), (496, 104), (510, 150), (514, 222)],
    "body": [(288, 436), (442, 436), (478, 652), (214, 652)],
    "eye_l": (305, 324, 50, 42),  # cx, cy, rx, ry
    "eye_r": (443, 324, 46, 42),
    "pupil_l": (324, 334, 11, 14),
    "pupil_r": (436, 328, 11, 14),
    "whiskers_l": [((222, 378), (156, 378)), ((226, 398), (160, 410)), ((236, 418), (186, 448))],
    "whiskers_r": [((494, 376), (580, 372)), ((498, 396), (586, 414)), ((494, 418), (556, 450))],
}
CAT_BOX = (150, 80, 592, 660)  # design-space area that gets sampled


def _in_poly(x, y, pts):
    inside = False
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def _in_ellipse(x, y, e):
    cx, cy, rx, ry = e
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1


def _near_segment(x, y, seg, tol):
    (x1, y1), (x2, y2) = seg
    dx, dy = x2 - x1, y2 - y1
    t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(x - (x1 + t * dx), y - (y1 + t * dy)) <= tol


def cat_layers(scale):
    """Sample the cat onto a braille dot grid; returns {layer: [(x, y), …]} in px."""
    cell_w, cell_h, pitch = 7.5, 14.0, 3.1  # braille cell size and dot spacing
    x0, y0, x1, y1 = CAT_BOX
    layers = {k: [] for k in ("body", "ear_r", "lids", "pupils", "whiskers_l", "whiskers_r")}
    for cy in range(int((y1 - y0) * scale / cell_h) + 1):
        for cx in range(int((x1 - x0) * scale / cell_w) + 1):
            for dc in range(2):
                for dr in range(4):
                    px = cx * cell_w + dc * pitch
                    py = cy * cell_h + dr * pitch
                    x, y = x0 + px / scale, y0 + py / scale
                    eyes = _in_ellipse(x, y, CAT["eye_l"]) or _in_ellipse(x, y, CAT["eye_r"])
                    if _in_ellipse(x, y, CAT["pupil_l"]) or _in_ellipse(x, y, CAT["pupil_r"]):
                        layers["pupils"].append((px, py))
                    if eyes:
                        layers["lids"].append((px, py))
                    elif _in_poly(x, y, CAT["ear_r"]) and y < CAT["head"][0][1] + 4:
                        layers["ear_r"].append((px, py))
                    elif any(_in_poly(x, y, CAT[k]) for k in ("head", "ear_l", "ear_r", "body")):
                        layers["body"].append((px, py))
                    else:
                        for side in ("whiskers_l", "whiskers_r"):
                            if any(_near_segment(x, y, s, 1.6 / scale) for s in CAT[side]):
                                layers[side].append((px, py))
    return layers


def dots_path(points, ox, oy, cls="", extra=""):
    d = "".join(f"M{ox + x:.1f} {oy + y:.1f}h0" for x, y in points)
    c = f' class="{cls}"' if cls else ""
    return f'<path{c} d="{d}"{extra}/>'


def cat_art(cx, cy, scale=0.45):
    """The animated cat centred on (cx, cy). Returns (svg, css)."""
    x0, y0, x1, y1 = CAT_BOX
    ox, oy = cx - (x1 - x0) * scale / 2, cy - (y1 - y0) * scale / 2
    to_px = lambda p: (ox + (p[0] - x0) * scale, oy + (p[1] - y0) * scale)
    L = cat_layers(scale)

    ear_pivot = to_px((470, 222))
    wl_pivot, wr_pivot = to_px((224, 398)), to_px((496, 396))
    svg = (
        f'<g fill="none" stroke="{TEXT}" stroke-width="1.8" stroke-linecap="round">'
        + dots_path(L["body"], ox, oy, extra=' id="catbody"')
        + dots_path(L["ear_r"], ox, oy, "ear")
        + dots_path(L["whiskers_l"], ox, oy, "wl")
        + dots_path(L["whiskers_r"], ox, oy, "wr")
        + dots_path(L["lids"], ox, oy, "lid")
        + f'<g class="pupblink"><g class="glance">{dots_path(L["pupils"], ox, oy, extra=f" stroke=\"{HI}\"")}</g></g>'
        + "</g>"
        # a soft highlight sweeping down the body
        + f'<linearGradient id="sweep" gradientUnits="userSpaceOnUse" x1="0" y1="{oy - 70:.0f}" x2="0" y2="{oy:.0f}">'
        f'<stop offset="0" stop-color="{HI}" stop-opacity="0"/><stop offset=".5" stop-color="{HI}" stop-opacity=".9"/>'
        f'<stop offset="1" stop-color="{HI}" stop-opacity="0"/>'
        f'<animateTransform attributeName="gradientTransform" type="translate" from="0 0" to="0 {(y1 - y0) * scale + 140:.0f}" '
        f'dur="5s" repeatCount="indefinite"/></linearGradient>'
        f'<use href="#catbody" stroke="url(#sweep)" stroke-width="1.8" stroke-linecap="round"/>'
    )
    css = (
        # blink: lids fill the eyes for a moment, pupils vanish
        "@keyframes lid{0%,90%,96%,100%{opacity:0}92%,94%{opacity:1}}.lid{opacity:0;animation:lid 4.8s infinite}"
        "@keyframes pupblink{0%,90%,96%,100%{opacity:1}92%,94%{opacity:0}}.pupblink{animation:pupblink 4.8s infinite}"
        # glance left, then right
        "@keyframes glance{0%,22%{transform:translate(0,0)}27%,48%{transform:translate(-5px,1px)}"
        "53%,74%{transform:translate(4px,0)}79%,100%{transform:translate(0,0)}}.glance{animation:glance 9s ease-in-out infinite}"
        # an occasional ear twitch
        "@keyframes ear{0%,80%,100%{transform:rotate(0)}83%{transform:rotate(-9deg)}86%{transform:rotate(3deg)}"
        "89%{transform:rotate(-6deg)}92%{transform:rotate(0)}}"
        f".ear{{transform-origin:{ear_pivot[0]:.0f}px {ear_pivot[1]:.0f}px;animation:ear 6.5s ease-in-out infinite}}"
        # whiskers sway
        "@keyframes wl{from{transform:rotate(-3deg)}to{transform:rotate(3deg)}}"
        "@keyframes wr{from{transform:rotate(3deg)}to{transform:rotate(-3deg)}}"
        f".wl{{transform-origin:{wl_pivot[0]:.0f}px {wl_pivot[1]:.0f}px;animation:wl 2.6s ease-in-out infinite alternate}}"
        f".wr{{transform-origin:{wr_pivot[0]:.0f}px {wr_pivot[1]:.0f}px;animation:wr 2.6s ease-in-out infinite alternate}}"
    )
    return svg, css


def about():
    split, x0, fs, lh = 292, 318, 13, 21
    chars = int((W - x0 - 24) / (fs * 0.6))
    body = []

    y = BAR_H + 44
    body.append(line(x0, y, [("# ", DIM), (ABOUT["name"], HI, True)], 22)[0])
    y += 28
    body.append(line(x0, y, [(ABOUT["tagline"], MUTED)], fs)[0])
    y += 14
    for text in textwrap.wrap(ABOUT["bio"], chars):
        y += lh
        body.append(line(x0, y, [(text, TEXT)], fs)[0])
    y += 14
    for key, value in ABOUT["list"]:
        y += 24
        body.append(line(x0, y, [("▸ ", HI), (key.ljust(8), MUTED), (value, TEXT)], fs)[0])
    h = int(y + 34)

    # left pane: the animated braille cat
    body.append(f'<line x1="{split}.5" x2="{split}.5" y1="{BAR_H}" y2="{h}" stroke="{FAINT}"/>')
    art, css = cat_art(split / 2, BAR_H + (h - BAR_H) / 2)
    body.append(art)
    label = f"About {ABOUT['name']}: {ABOUT['tagline']}. {ABOUT['bio']} " + " ".join(f"{k}: {v}." for k, v in ABOUT["list"])
    return window(W, h, "~/about.md", "\n".join(body), css, label)


# ── project cards ────────────────────────────────────────────────────────────

CARD_W = 432  # two cards + a 16px gutter = W


def project_layout(p):
    fs = 13
    return textwrap.wrap(p["desc"], int((CARD_W - 48) / (fs * 0.6)))


def project_card(p, h):
    fs, lh = 13, 20
    body = []
    y = BAR_H + 40
    body.append(line(24, y, [(p["name"], HI, True)], 20)[0])
    body.append(line(CARD_W - 24 - 12, y - 2, [("↗", MUTED)], 20)[0])
    y += 24
    body.append(line(24, y, [(p["tagline"], MUTED)], fs)[0])
    y += 12
    for text in project_layout(p):
        y += lh
        body.append(line(24, y, [(text, TEXT)], fs)[0])
    x, ty = 24, y + 34
    for tag in p["tags"]:
        svg, w = pill(x, ty, tag)
        body.append(svg)
        x += w + 8
    body.append(f'<line x1="0" x2="{CARD_W}" y1="{h - 40.5}" y2="{h - 40.5}" stroke="{FAINT}"/>')
    body.append(line(24, h - 15, [("→ ", DIM), (p["url"], MUTED)], 12)[0])
    label = f"{p['name']} — {p['tagline']}. {p['desc']} Built with {', '.join(p['tags'])}. {p['url']}"
    return window(CARD_W, h, f"~/projects/{p['slug']}", "\n".join(body), label=label)


# ── stack card ───────────────────────────────────────────────────────────────

def stack():
    fs, gap, col = 14, 38, 17
    cw = fs * 0.6
    body = []
    y0 = BAR_H + 40
    body.append(line(24, y0, [("~/stack", HI, True)], fs)[0])
    trunk = 24 + cw / 2  # tree connectors drawn as lines, so they join cleanly
    body.append(f'<line x1="{trunk:g}" x2="{trunk:g}" y1="{y0 + 7}" y2="{y0 + gap * len(STACK) - 5}" stroke="{DIM}"/>')
    for i, (folder, tools) in enumerate(STACK):
        y = y0 + gap * (i + 1)
        body.append(f'<line x1="{trunk:g}" x2="{24 + 3.4 * cw:g}" y1="{y - 5}" y2="{y - 5}" stroke="{DIM}"/>')
        body.append(line(24 + 4 * cw, y, [(folder, TEXT, True), ("/", DIM)], fs)[0])
        x = 24 + col * cw
        for tool in tools:
            svg, w = pill(x, y, tool)
            body.append(svg)
            x += w + 8
    n_tools = sum(len(t) for _, t in STACK)
    y = y0 + gap * len(STACK) + 40
    body.append(line(24, y, [(f"{len(STACK)} directories, {n_tools} tools", MUTED)], 13)[0])
    h = int(y + 28)

    # right pane: principles
    split = 612
    body.append(f'<line x1="{split}.5" x2="{split}.5" y1="{BAR_H}" y2="{h}" stroke="{FAINT}"/>')
    py = y0
    body.append(line(split + 28, py, [("# ", DIM), ("principles", HI, True)], fs)[0])
    for p in PRINCIPLES:
        py += 30
        body.append(line(split + 28, py, [("- ", DIM), (p, TEXT)], 13)[0])

    label = "Tech stack: " + "; ".join(f"{f}: {', '.join(t)}" for f, t in STACK) + ". Principles: " + ", ".join(PRINCIPLES)
    return window(W, h, "~/stack — tree", "\n".join(body), label=label)


# ── footer ───────────────────────────────────────────────────────────────────

def footer():
    fs, lh = 14, 22
    y = BAR_H + 32
    rows = [prompt("exit"), [("logout", TEXT)], [("Connection to github.com closed.", MUTED)]]
    body = [line(24, y + i * lh, runs, fs)[0] for i, runs in enumerate(rows)]
    ty = y + len(rows) * lh + 12
    svg, end = line(24, ty, [("✦ ", HI), ("thanks for stopping by", TEXT)], fs)
    body.append(svg + f'<rect class="cur" x="{end + 6:g}" y="{ty - 13}" width="{fs * 0.6:g}" height="17" fill="{HI}"/>')
    return window(W, int(ty + 26), f"{USER}: ~", "\n".join(body), BLINK, "exit — logout. Thanks for stopping by.")


def main():
    out = {
        "terminal.svg": terminal(),
        "about.svg": about(),
        "stack.svg": stack(),
        "footer.svg": footer(),
    }
    for name in LINKS:
        out[f"link-{name}.svg"] = link_button(name)
    for i, (slug, cmd, label) in enumerate(SECTIONS, 1):
        out[f"section-{slug}.svg"] = section_header(i, cmd, label)
    card_h = max(len(project_layout(p)) for p in PROJECTS) * 20 + BAR_H + 40 + 24 + 12 + 34 + 64
    for p in PROJECTS:
        out[f"project-{p['slug']}.svg"] = project_card(p, card_h)
    for name, svg in out.items():
        (ASSETS / name).write_text(svg, encoding="utf-8")
    print(f"wrote {len(out)} files to assets/")


if __name__ == "__main__":
    main()
