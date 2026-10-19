"""Generate the ASCII-art SVGs used in README.md.

    python scripts/build_ascii.py

Every glyph is placed on an explicit character grid (per-character x positions),
so the art stays aligned no matter which monospace font the viewer's system picks.
Edit the art/text below and re-run; outputs land in assets/.
"""

from pathlib import Path
from xml.sax.saxutils import escape

ASSETS = Path(__file__).resolve().parent.parent / "assets"
MONO = "ui-monospace, 'Cascadia Mono', 'SF Mono', Menlo, Consolas, 'DejaVu Sans Mono', 'Liberation Mono', monospace"

THEMES = {
    # bone-on-ink, like an old print
    "dark": {"hi": "#ECE6D6", "mid": "#B3AC99", "dim": "#7A7465", "faint": "#4A463D"},
    "light": {"hi": "#1E1B16", "mid": "#4D483E", "dim": "#8A8475", "faint": "#BFB9A9"},
}

# ── art ──────────────────────────────────────────────────────────────────────

NAME = [  # ANSI Shadow
    "██╗  ██╗██╗   ██╗██╗     ███████╗    ██╗   ██╗██╗   ██╗",
    "██║ ██╔╝╚██╗ ██╔╝██║     ██╔════╝    ██║   ██║██║   ██║",
    "█████╔╝  ╚████╔╝ ██║     █████╗      ██║   ██║██║   ██║",
    "██╔═██╗   ╚██╔╝  ██║     ██╔══╝      ╚██╗ ██╔╝██║   ██║",
    "██║  ██╗   ██║   ███████╗███████╗     ╚████╔╝ ╚██████╔╝",
    "╚═╝  ╚═╝   ╚═╝   ╚══════╝╚══════╝      ╚═══╝   ╚═════╝ ",
]

TREE = [  # a nod to Arbora
    "             .        *       .",
    "       *         .:%%%%%%:.        .",
    "           .:%%%%%%@@%%%%%%%%:.",
    "         :%%%%@@%%%%%%%%%%@@%%%%:   *",
    "   .    %%%%%%%%%%%%%%@@%%%%%%%%%%",
    "       :%%%@@%%%%%%%%%%%%%%%%@@%%%:",
    "        '%%%%%%%%%@@%%%%%%%%%%%%%'",
    "          '%%%%%%\\%%%|%%/%%%%%'    .",
    "             '%%%%\\  | /%%%'",
    "                   \\ |/",
    "                    |||",
    "                    |||",
    "                   /|||\\",
    "        ,.~-~.,___/ ||| \\___,.~-~.,",
]
TREE_TONE = {"@": "hi", "%": "mid"}  # everything else is dim

LACE = "._.-'~'-"


# ── svg helpers ──────────────────────────────────────────────────────────────

class Canvas:
    def __init__(self, cols, rows, cw=8.0, lh=17.0, size=13.3, pad_y=14.0):
        self.cols, self.rows = cols, rows
        self.cw, self.lh, self.size, self.pad_y = cw, lh, size, pad_y
        self.items = []  # (svg string)
        self.taken = set()  # (col, row) cells holding a glyph or reserved

    @property
    def width(self):
        return self.cols * self.cw

    @property
    def height(self):
        return self.rows * self.lh + self.pad_y * 2

    def y(self, row):
        return self.pad_y + row * self.lh + self.lh * 0.8

    def put(self, col, row, text, cls, *, tone=None, mark=True):
        """Place text on the grid. `tone` maps a char to a class override."""
        runs = {}
        for i, ch in enumerate(text):
            if ch == " ":
                continue
            c = tone.get(ch, cls) if tone else cls
            runs.setdefault(c, []).append((col + i, ch))
            if mark:
                self.taken.add((col + i, row))
        for c, glyphs in runs.items():
            self.items.append(self._text(glyphs, self.y(row), c, self.cw, self.size))

    def reserve(self, col0, row0, col1, row1):
        for c in range(col0, col1 + 1):
            for r in range(row0, row1 + 1):
                self.taken.add((c, r))

    @staticmethod
    def _text(glyphs, y, cls, cw, size, x0=0.0, extra=""):
        xs = " ".join(f"{x0 + c * cw + cw / 2:g}" for c, _ in glyphs)
        chars = escape("".join(ch for _, ch in glyphs))
        return f'<text class="{cls}" x="{xs}" y="{y:g}" font-size="{size}"{extra}>{chars}</text>'

    def render(self, theme, label, extra_css=""):
        t = THEMES[theme]
        css = (
            f"text{{font-family:{MONO};text-anchor:middle;white-space:pre}}"
            f".hi{{fill:{t['hi']}}}.mid{{fill:{t['mid']}}}.dim{{fill:{t['dim']}}}.faint{{fill:{t['faint']}}}"
            f".hi-f{{fill:{t['hi']}}}.mid-s{{stroke:{t['mid']}}}"
            + extra_css
        )
        body = "\n  ".join(self.items)
        w, h = self.width, self.height
        return (
            f'<svg width="{w:g}" height="{h:g}" viewBox="0 0 {w:g} {h:g}" '
            f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{escape(label)}">\n'
            f"  <style>{css}</style>\n  {body}\n</svg>\n"
        )


# Double-line box glyphs as polylines in a cell (cx/cy = centre, o = half gap).
BOX = {
    "═": lambda w, h, cx, cy, o: [[(0, cy - o), (w, cy - o)], [(0, cy + o), (w, cy + o)]],
    "║": lambda w, h, cx, cy, o: [[(cx - o, 0), (cx - o, h)], [(cx + o, 0), (cx + o, h)]],
    "╗": lambda w, h, cx, cy, o: [[(0, cy - o), (cx + o, cy - o), (cx + o, h)], [(0, cy + o), (cx - o, cy + o), (cx - o, h)]],
    "╔": lambda w, h, cx, cy, o: [[(w, cy - o), (cx - o, cy - o), (cx - o, h)], [(w, cy + o), (cx + o, cy + o), (cx + o, h)]],
    "╝": lambda w, h, cx, cy, o: [[(0, cy + o), (cx + o, cy + o), (cx + o, 0)], [(0, cy - o), (cx - o, cy - o), (cx - o, 0)]],
    "╚": lambda w, h, cx, cy, o: [[(w, cy + o), (cx - o, cy + o), (cx - o, 0)], [(w, cy - o), (cx + o, cy - o), (cx + o, 0)]],
}


def block_art(lines, x0, y0, cw, lh):
    """Render ANSI-Shadow style art: █ runs become rects, box glyphs become strokes."""
    rects, strokes = [], []
    for r, line in enumerate(lines):
        y = y0 + r * lh
        c = 0
        while c < len(line):
            if line[c] == "█":
                start = c
                while c < len(line) and line[c] == "█":
                    c += 1
                rects.append(f'<rect x="{x0 + start * cw:g}" y="{y:g}" width="{(c - start) * cw:g}" height="{lh:g}"/>')
                continue
            if line[c] in BOX:
                x = x0 + c * cw
                for pts in BOX[line[c]](cw, lh, cw / 2, lh / 2, 2.0):
                    strokes.append("M" + " L".join(f"{x + px:g} {y + py:g}" for px, py in pts))
            c += 1
    return (
        f'<g class="hi-f" shape-rendering="crispEdges">{"".join(rects)}</g>'
        f'<path class="mid-s" fill="none" stroke-width="1.2" d="{" ".join(strokes)}"/>'
    )


def lace(n, offset=0):
    return "".join(LACE[(i + offset) % len(LACE)] for i in range(n))


# ── hero ─────────────────────────────────────────────────────────────────────

def hero(theme):
    cv = Canvas(cols=110, rows=20)
    L, R = 1, 108  # frame columns

    cv.put(0, 0, lace(110), "dim")
    cv.put(L, 1, "+" + "-" * (R - L - 1) + "+", "faint")
    for r in range(2, 18):
        cv.put(L, r, "|", "faint")
        cv.put(R, r, "|", "faint")
    cv.put(L, 18, "+" + "-" * (R - L - 1) + "+", "faint")
    cv.put(0, 19, lace(110, offset=4), "dim")

    # title bar
    cv.put(L + 3, 2, "@kylev202 / README.md", "mid")
    cv.put(R - 14, 2, "[ - ] [ x ]", "dim")
    cv.put(L + 1, 3, "·" * (R - L - 1), "faint")

    # name block, drawn as shapes so the blocks join seamlessly
    cv.items.append(block_art(NAME, x0=4 * cv.cw, y0=cv.pad_y + 4.7 * cv.lh, cw=9.0, lh=16.0))

    # tree on the right; its stars twinkle
    stars = 0
    for i, line in enumerate(TREE):
        for c, ch in enumerate(line):
            if ch == "*":
                cv.put(70 + c, 4 + i, ch, f"dim tw t{stars % 4}")
                stars += 1
        cv.put(70, 4 + i, line.replace("*", " "), "dim", tone=TREE_TONE)

    # captions
    cv.put(5, 12, "...or kyle. i just build things.", "mid")
    cv.put(5, 13, "full-stack engineer  ·  local-first  ·  privacy-first", "dim")
    cv.put(5, 15, "( You continue to build. )", "hi")
    cv.put(5 + 27, 15, "█", "hi cur")

    # a few scattered specks of print texture in the empty space
    for c, r, ch in [(60, 5, "."), (64, 9, "+"), (52, 16, "."), (58, 14, "·"), (3, 16, "."), (40, 17, "'")]:
        cv.put(c, r, ch, "faint")

    t = THEMES[theme]
    css = (
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
        ".cur{animation:blink 1.1s step-end infinite}"
        f"@keyframes tw{{0%,100%{{fill:{t['faint']}}}50%{{fill:{t['mid']}}}}}"
        ".tw{animation:tw 4s ease-in-out infinite}"
        ".t1{animation-delay:1s}.t2{animation-delay:2s}.t3{animation-delay:3s}"
    )
    return cv.render(theme, "Kyle Vu — full-stack engineer building local-first, privacy-first software", css)


# ── divider ──────────────────────────────────────────────────────────────────

DIVIDER = "~*~  ._.-'~'-._.-'~'-._  ( ✦ )  _.-'~'-._.-'~'-._.  ~*~"


def divider(theme):
    cv = Canvas(cols=len(DIVIDER) + 2, rows=1, lh=16, pad_y=2)
    cv.put(1, 0, DIVIDER, "dim", tone={"✦": "hi"})
    return cv.render(theme, "")


def main():
    for theme in THEMES:
        (ASSETS / f"hero-{theme}.svg").write_text(hero(theme), encoding="utf-8")
        (ASSETS / f"divider-{theme}.svg").write_text(divider(theme), encoding="utf-8")
    print("wrote", ", ".join(sorted(p.name for p in ASSETS.glob("*.svg"))))


if __name__ == "__main__":
    main()
