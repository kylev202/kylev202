"""Render a monochrome contribution line graph (last 31 days) as SVG.

    GITHUB_TOKEN=... python scripts/activity_graph.py kylev202 dist/activity-graph.svg --name=Kyle
    python scripts/activity_graph.py kylev202 out.svg --demo     # random data, no network

Run daily by .github/workflows/profile-assets.yml, which publishes the result to the
`output` branch. Replaces the public github-readme-activity-graph instance (now offline).
"""

import datetime as dt
import json
import os
import random
import sys
import urllib.request
from xml.sax.saxutils import escape

DAYS = 31
W, H = 880, 320
PAD_L, PAD_R, PAD_T, PAD_B = 64, 28, 64, 56
BG, BORDER, GRID = "#0D1117", "#30363D", "#21262D"
FG, MUTED, DIM = "#F0F6FC", "#C9D1D9", "#8B949E"
FONT = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"

QUERY = """query($login: String!) { user(login: $login) { contributionsCollection {
  contributionCalendar { weeks { contributionDays { date contributionCount } } } } } }"""


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "activity-graph"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if "errors" in data:
        raise SystemExit(f"GraphQL error: {data['errors']}")
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    return [(dt.date.fromisoformat(d["date"]), d["contributionCount"]) for d in days][-DAYS:]


def demo():
    today = dt.date.today()
    rng = random.Random(3)
    return [(today - dt.timedelta(days=DAYS - 1 - i), rng.choice([0, 0, 0, 1, 2, 3, 5, 8])) for i in range(DAYS)]


def nice_step(top):
    for step in (1, 2, 5, 10, 20, 25, 50, 100, 200, 500):
        if top / step <= 6:
            return step
    return 1000


def render(name, days):
    counts = [c for _, c in days]
    step = nice_step(max(max(counts), 1))
    top = max(step * -(-max(counts) // step), step)
    pw, ph = W - PAD_L - PAD_R, H - PAD_T - PAD_B
    x = lambda i: PAD_L + pw * i / (len(days) - 1)
    y = lambda v: PAD_T + ph * (1 - v / top)

    out = [
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="6" fill="{BG}" stroke="{BORDER}"/>',
        f'<text x="{W / 2}" y="34" text-anchor="middle" font-size="18" font-weight="600" fill="{FG}">'
        f"{escape(name)}'s Contribution Graph</text>",
    ]
    for v in range(0, top + 1, step):  # horizontal grid + y labels
        out.append(f'<line x1="{PAD_L}" x2="{W - PAD_R}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{GRID}"/>')
        out.append(f'<text x="{PAD_L - 10}" y="{y(v) + 4:.1f}" text-anchor="end" font-size="11" fill="{DIM}">{v}</text>')
    for i, (d, _) in enumerate(days):  # x labels: day of month
        out.append(f'<text x="{x(i):.1f}" y="{H - PAD_B + 18}" text-anchor="middle" font-size="10" fill="{DIM}">{d.day}</text>')
    out.append(f'<text x="{W / 2}" y="{H - 12}" text-anchor="middle" font-size="12" fill="{MUTED}">Days</text>')
    out.append(
        f'<text x="20" y="{PAD_T + ph / 2}" text-anchor="middle" font-size="12" fill="{MUTED}" '
        f'transform="rotate(-90 20 {PAD_T + ph / 2})">Contributions</text>'
    )

    line = " ".join(f"{x(i):.1f},{y(c):.1f}" for i, c in enumerate(counts))
    area = f"{x(0):.1f},{y(0):.1f} {line} {x(len(days) - 1):.1f},{y(0):.1f}"
    out.append(f'<polygon points="{area}" fill="{FG}" fill-opacity=".06"/>')
    out.append(f'<polyline points="{line}" fill="none" stroke="{FG}" stroke-width="2" stroke-linejoin="round"/>')
    for i, (d, c) in enumerate(days):
        out.append(
            f'<circle cx="{x(i):.1f}" cy="{y(c):.1f}" r="3.5" fill="{BG}" stroke="{FG}" stroke-width="2">'
            f"<title>{d.isoformat()}: {c}</title></circle>"
        )

    body = "\n  ".join(out)
    return (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="{FONT}" role="img" aria-label="{escape(name)}\'s contributions over the last {DAYS} days">\n'
        f"  {body}\n</svg>\n"
    )


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        raise SystemExit(__doc__)
    login, path = args
    if "--demo" in sys.argv:
        days = demo()
    else:
        token = os.environ.get("GITHUB_TOKEN") or raise_missing()
        days = fetch(login, token)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        name = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--name=")), login)
        f.write(render(name, days))
    print(f"wrote {path} ({sum(c for _, c in days)} contributions in {len(days)} days)")


def raise_missing():
    raise SystemExit("GITHUB_TOKEN is not set (or pass --demo)")


if __name__ == "__main__":
    main()
