"""Render the live stats cards from the GitHub GraphQL API.

    GITHUB_TOKEN=... python scripts/profile_stats.py kylev202 dist
    python scripts/profile_stats.py kylev202 out --demo     # random data, no network

Writes <outdir>/stats.svg (totals, streaks, top languages) and
<outdir>/activity-graph.svg (contributions over the last 31 days), styled by
scripts/theme.py to match the static cards. Run daily by
.github/workflows/profile-assets.yml, which publishes them to the `output` branch.
"""

import datetime as dt
import json
import os
import random
import sys
import urllib.request
from pathlib import Path

from theme import BAR, BAR_H, BORDER, DIM, FAINT, HI, MUTED, TEXT, W, line, text_width, window

GRAPH_DAYS = 31
TOP_LANGS = 5
HIDE_LANGS = {"HTML", "CSS", "SCSS", "Jupyter Notebook"}  # markup/notebooks would swamp the code languages

QUERY = """query($login: String!) { user(login: $login) {
  followers { totalCount }
  pullRequests { totalCount }
  issues { totalCount }
  repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
    totalCount
    nodes { stargazerCount languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
      edges { size node { name } } } }
  }
  contributionsCollection {
    totalCommitContributions
    contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
  }
} }"""


# ── data ─────────────────────────────────────────────────────────────────────

def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-stats"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if "errors" in data:
        raise SystemExit(f"GraphQL error: {data['errors']}")
    u = data["data"]["user"]
    cal = u["contributionsCollection"]["contributionCalendar"]
    langs = {}
    for repo in u["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            langs[edge["node"]["name"]] = langs.get(edge["node"]["name"], 0) + edge["size"]
    return {
        "days": [
            (dt.date.fromisoformat(d["date"]), d["contributionCount"])
            for w in cal["weeks"] for d in w["contributionDays"]
        ],
        "total": cal["totalContributions"],
        "commits": u["contributionsCollection"]["totalCommitContributions"],
        "prs": u["pullRequests"]["totalCount"],
        "issues": u["issues"]["totalCount"],
        "repos": u["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
        "followers": u["followers"]["totalCount"],
        "langs": langs,
    }


def demo():
    rng = random.Random(3)
    today = dt.date.today()
    days = [(today - dt.timedelta(days=364 - i), rng.choice([0, 0, 0, 1, 2, 3, 5, 8])) for i in range(365)]
    return {
        "days": days, "total": sum(c for _, c in days), "commits": 412, "prs": 37, "issues": 12,
        "repos": 15, "stars": 9, "followers": 6,
        "langs": {"TypeScript": 520_000, "Rust": 210_000, "Python": 160_000, "JavaScript": 90_000, "HTML": 900_000},
    }


def streaks(days):
    """(current, current_range, longest, longest_range) — today may still be empty."""
    runs, start = [], None
    for i, (d, c) in enumerate(days):
        if c and start is None:
            start = i
        if not c and start is not None:
            runs.append((start, i - 1))
            start = None
    if start is not None:
        runs.append((start, len(days) - 1))
    longest = max(runs, key=lambda r: r[1] - r[0], default=None)
    last = len(days) - 1 if days[-1][1] else len(days) - 2
    current = next((r for r in runs if r[1] == last), None)
    span = lambda r: (r[1] - r[0] + 1, (days[r[0]][0], days[r[1]][0])) if r else (0, None)
    return (*span(current), *span(longest))


def fmt_range(r):
    if not r:
        return "—"
    a, b = r
    f = lambda d: f"{d:%b} {d.day}"
    return f(a) if a == b else f"{f(a)} – {f(b)}"


# ── stats card ───────────────────────────────────────────────────────────────

def stats_card(s):
    cur, cur_r, best, best_r = streaks(s["days"])
    first = s["days"][0][0]
    tiles = [
        ("contributions", f"{s['total']:,}", "", f"since {first:%b} {first.day}, {first.year}"),
        ("current streak", str(cur), " days" if cur != 1 else " day", fmt_range(cur_r)),
        ("longest streak", str(best), " days" if best != 1 else " day", fmt_range(best_r)),
        ("stars earned", f"{s['stars']:,}", "", f"across {s['repos']} repos"),
    ]
    body = []
    gap, ty, th = 16, BAR_H + 20, 104
    tw = (W - 48 - gap * 3) / 4
    for i, (label, value, unit, sub) in enumerate(tiles):
        x = 24 + i * (tw + gap)
        body.append(f'<rect x="{x:g}" y="{ty}" width="{tw:g}" height="{th}" rx="6" fill="{BAR}" stroke="{BORDER}"/>')
        body.append(line(x + 16, ty + 26, [(label, MUTED)], 11)[0])
        svg, end = line(x + 16, ty + 64, [(value, HI, True)], 30)
        body.append(svg + line(end, ty + 64, [(unit, MUTED)], 13)[0])
        body.append(line(x + 16, ty + 88, [(sub, DIM)], 11)[0])

    fs, lh = 13, 26
    cw = fs * 0.6
    y0 = ty + th + 40

    # left: totals with dotted leaders
    rows = [("commits (1y)", s["commits"]), ("pull requests", s["prs"]), ("issues", s["issues"]),
            ("public repos", s["repos"]), ("followers", s["followers"])]
    cols = int((W / 2 - 24 - 24) / cw)
    body.append(line(24, y0, [("# ", DIM), ("totals", HI, True)], fs)[0])
    for i, (k, v) in enumerate(rows):
        v = f"{v:,}"
        dots = "." * (cols - len(k) - len(v) - 2)
        body.append(line(24, y0 + (i + 1) * lh, [(k, TEXT), (f" {dots} ", DIM), (v, HI, True)], fs)[0])

    # right: top languages as block bars
    langs = {k: v for k, v in s["langs"].items() if k not in HIDE_LANGS}
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:TOP_LANGS]
    rx, bar_n = W / 2 + 24, 18
    body.append(f'<line x1="{W / 2}" x2="{W / 2}" y1="{y0 - 18}" y2="{y0 + len(rows) * lh + 6}" stroke="{FAINT}"/>')
    body.append(line(rx, y0, [("# ", DIM), ("top languages", HI, True)], fs)[0])
    for i, (name, size) in enumerate(top):
        pct = size / total
        filled = max(1, round(pct * bar_n))
        y = y0 + (i + 1) * lh
        body.append(line(rx, y, [(name[:12].ljust(13), TEXT), (" " * bar_n, TEXT), (f"{pct * 100:6.1f}%", MUTED)], fs)[0])
        for j in range(bar_n):  # segmented bar, one cell per character column
            bx = rx + (13 + j) * cw + 1
            body.append(f'<rect x="{bx:g}" y="{y - 10}" width="{cw - 2:g}" height="11" rx="1" fill="{HI if j < filled else FAINT}"/>')

    h = int(y0 + len(rows) * lh + 30)
    label = (f"GitHub stats, last 12 months: {s['total']} contributions, current streak {cur} days, "
             f"longest streak {best} days, {s['stars']} stars. Top languages: "
             + ", ".join(f"{n} {sz / total * 100:.0f}%" for n, sz in top))
    return window(W, h, "~/stats — last 12 months", "\n".join(body), label=label)


# ── activity graph ───────────────────────────────────────────────────────────

def activity_graph(s):
    days = s["days"][-GRAPH_DAYS:]
    counts = [c for _, c in days]
    step = next((st for st in (1, 2, 5, 10, 20, 25, 50, 100, 200, 500) if max(counts) / st <= 5), 1000)
    top = max(step * -(-max(counts) // step), step)
    h = 300
    pl, pr, pt, pb = 56, 28, BAR_H + 44, 40
    pw, ph = W - pl - pr, h - pt - pb
    x = lambda i: pl + pw * i / (len(days) - 1)
    y = lambda v: pt + ph * (1 - v / top)

    body = [line(24, BAR_H + 26, [(f"{sum(counts)}", HI, True), (" contributions in the last 31 days", MUTED)], 12)[0]]
    peak = f"peak {max(counts)}"
    body.append(line(W - pr - text_width(peak, 12), BAR_H + 26, [(peak, MUTED)], 12)[0])
    for v in range(0, top + 1, step):
        body.append(f'<line x1="{pl}" x2="{W - pr}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{FAINT}"/>')
        body.append(f'<text x="{pl - 12}" y="{y(v) + 4:.1f}" text-anchor="end" font-size="10" fill="{DIM}">{v}</text>')
    for i, (d, _) in enumerate(days):
        fill = MUTED if d.day == 1 or i in (0, len(days) - 1) else DIM
        body.append(f'<text x="{x(i):.1f}" y="{h - pb + 20}" text-anchor="middle" font-size="10" fill="{fill}">{d.day}</text>')

    pts = " ".join(f"{x(i):.1f},{y(c):.1f}" for i, c in enumerate(counts))
    body.append(f'<polygon points="{x(0):.1f},{y(0):.1f} {pts} {x(len(days) - 1):.1f},{y(0):.1f}" fill="{HI}" fill-opacity=".06"/>')
    body.append(f'<polyline points="{pts}" fill="none" stroke="{HI}" stroke-width="2" stroke-linejoin="round"/>')
    for i, (d, c) in enumerate(days):
        body.append(f'<circle cx="{x(i):.1f}" cy="{y(c):.1f}" r="3.5" fill="#0D1117" stroke="{HI}" stroke-width="2">'
                    f"<title>{d.isoformat()}: {c}</title></circle>")
    label = f"Contributions over the last {GRAPH_DAYS} days: {sum(counts)} total, peak {max(counts)} in a day"
    return window(W, h, "~/activity — last 31 days", "\n".join(body), label=label)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        raise SystemExit(__doc__)
    login, outdir = args
    if "--demo" in sys.argv:
        s = demo()
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise SystemExit("GITHUB_TOKEN is not set (or pass --demo)")
        s = fetch(login, token)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "stats.svg").write_text(stats_card(s), encoding="utf-8")
    (out / "activity-graph.svg").write_text(activity_graph(s), encoding="utf-8")
    print(f"wrote {out / 'stats.svg'} and {out / 'activity-graph.svg'} ({s['total']} contributions)")


if __name__ == "__main__":
    main()
