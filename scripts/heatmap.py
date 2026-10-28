#!/usr/bin/env python3
"""
Scrape public contribution calendar (no token) and render animated green
heatmap SVGs: assets/heatmap-dark.svg + assets/heatmap-light.svg.
Stdlib only, so CI needs no pip install. Run daily by .github/workflows/update-heatmap.yml.

Local preview with fake data:  python3 scripts/heatmap.py --demo
"""
import datetime
import os
import random
import re
import sys
import urllib.request

USER = os.environ.get("GH_PROFILE_USER", "thejackalsh")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = {t: os.path.join(ROOT, "assets", f"heatmap-{t}.svg") for t in ("dark", "light")}

# github green palette. level 0..4
THEMES = {
    "dark":  {"lv": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
              "lbl": "#7d8590", "total": "#e6edf3", "sub": "#7d8590"},
    "light": {"lv": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
              "lbl": "#57606a", "total": "#1f2328", "sub": "#57606a"},
}
W = 800
LEFT, TOP = 70, 30          # 70 = 40 margin (same as stack.svg) + 30 day labels
CELL, STEP = 10, 13
COL_T, ROW_T = 0.0625, 0.0375  # diagonal wave timing (~3.75s total)
FONT = "Consolas, 'Courier New', monospace"


def css(t):
    th = THEMES[t]
    return (
        f".lbl{{fill:{th['lbl']};font-size:11px;letter-spacing:1.5px}}"
        f".total{{fill:{th['total']};font-size:13px;font-weight:700;letter-spacing:.5px}}"
        f".sub{{fill:{th['sub']};font-size:11px;letter-spacing:1px}}"
        ".c{transform-box:fill-box;transform-origin:center;opacity:0;animation:pop .625s ease-out both}"
        ".g{animation:pop .625s ease-out both,flash 1s ease-out both}"
        ".fade{opacity:0;animation:fade 1s ease-out both}"
        "@keyframes pop{0%{opacity:0;transform:scale(.2)}60%{opacity:1;transform:scale(1.15)}100%{opacity:1;transform:scale(1)}}"
        "@keyframes flash{0%,40%{filter:brightness(2.2)}100%{filter:brightness(1)}}"
        "@keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}"
        + "".join(f".l{i}{{fill:{c}}}" for i, c in enumerate(th["lv"]))
        + "@media (prefers-reduced-motion:reduce){.c,.fade{opacity:1!important;animation:none!important}}"
    )


def fetch_days():
    req = urllib.request.Request(f"https://github.com/users/{USER}/contributions",
                                 headers={"User-Agent": "profile-readme-bot/1.0"})
    page = urllib.request.urlopen(req, timeout=30).read().decode()
    cells = {}
    for td in re.findall(r"<td[^>]*ContributionCalendar-day[^>]*>", page):
        date, cid, lvl = (re.search(rf'{a}="([^"]*)"', td) for a in ("data-date", "id", "data-level"))
        if date and cid:
            cells[cid.group(1)] = {"date": date.group(1), "level": int(lvl.group(1)) if lvl else 0, "count": 0}
    for cid, text in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', page):
        m = re.match(r"(\d[\d,]*)", text)
        if cid in cells and m:
            cells[cid]["count"] = int(m.group(1).replace(",", ""))
    if not cells:
        sys.exit("no calendar cells found -- github markup may have changed")
    return sorted(cells.values(), key=lambda d: d["date"])


def demo_days():
    end = datetime.date.today()
    out = []
    for i in range(364, -1, -1):
        d = end - datetime.timedelta(days=i)
        n = 0 if random.random() < 0.35 else random.choice([1, 2, 3, 5, 8, 13, 21])
        lvl = 0 if n == 0 else 1 if n < 3 else 2 if n < 6 else 3 if n < 12 else 4
        out.append({"date": d.isoformat(), "level": lvl, "count": n})
    return out


def streaks(days):
    cur = best = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        best = max(best, run)
    for d in reversed(days):
        if d["count"]:
            cur += 1
        elif d is days[-1]:
            continue  # today not counted yet -> don't break streak
        else:
            break
    return cur, best


def render(days, theme):
    first = datetime.date.fromisoformat(days[0]["date"])
    cols = [[None] * ((first.weekday() + 1) % 7)]  # sunday = row 0
    for d in days:
        if len(cols[-1]) == 7:
            cols.append([])
        cols[-1].append(d)

    h = TOP + 7 * STEP + 38
    end_t = (len(cols) - 1) * COL_T + 6 * ROW_T + 0.5
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" '
         f'role="img" aria-label="Contribution heatmap for the last year" font-family="{FONT}">',
         "<title>Contributions</title>", f"<style>{css(theme)}</style>"]

    prev = None
    for ci, col in enumerate(cols):
        date = datetime.date.fromisoformat(next(c for c in col if c)["date"])
        if date.month != prev and (prev or date.day <= 7):  # skip partial first month
            p.append(f'<text class="lbl" x="{LEFT + ci*STEP}" y="{TOP - 10}">{date.strftime("%b").upper()}</text>')
        prev = date.month
    for ri, name in [(1, "MON"), (3, "WED"), (5, "FRI")]:
        p.append(f'<text class="lbl" x="40" y="{TOP + ri*STEP + 9}">{name}</text>')

    for ci, col in enumerate(cols):
        for ri, d in enumerate(col):
            if not d:
                continue
            s = "" if d["count"] == 1 else "s"
            cls = f'c g l{d["level"]}' if d["count"] else "c l0"
            p.append(f'<rect class="{cls}" x="{LEFT + ci*STEP}" y="{TOP + ri*STEP}" width="{CELL}" '
                     f'height="{CELL}" rx="2" style="animation-delay:{ci*COL_T + ri*ROW_T:.3f}s">'
                     f'<title>{d["date"]}: {d["count"]} contribution{s}</title></rect>')

    total = sum(d["count"] for d in days)
    cur, best = streaks(days)
    y = h - 8
    tot = f"{total:,} contributions in the last year"
    lx = W - 40 - 38 - 5 * STEP           # legend: LESS [][][][][] MORE, right aligned
    p.append(f'<g class="fade" style="animation-delay:{end_t:.2f}s">'
             f'<text class="total" x="40" y="{y}">{tot}'
             f'<tspan class="sub" font-weight="400" dx="16">STREAK {cur}D · BEST {best}D</tspan></text>'
             f'<text class="lbl" x="{lx - 8}" y="{y}" text-anchor="end">LESS</text>')
    for i in range(5):
        p.append(f'<rect class="l{i}" x="{lx + i*STEP}" y="{y - 9}" width="{CELL}" height="{CELL}" rx="2"/>')
    p.append(f'<text class="lbl" x="{lx + 5*STEP + 5}" y="{y}">MORE</text></g>')
    p.append("</svg>")
    return "".join(p)


if __name__ == "__main__":
    days = demo_days() if "--demo" in sys.argv else fetch_days()
    for t, path in OUT.items():
        with open(path, "w") as f:
            f.write(render(days, t))
    print(f"wrote {len(OUT)} svgs: {len(days)} days, {sum(d['count'] for d in days)} contributions")
